"""Build a `SiteProfile` for one lot from its public-record pull.

    .venv/bin/python -m site_profile.build_profile --bbl 3052110074 --as-of 2026-06-01

The pull comes from `data_pull.site_brief_pull` (the site and every touching lot). A saved pull in
`data/cache/` is used when one exists for the BBL; otherwise the pull runs live.

What it does not do yet (other PRs own the sources): soil, bedrock depth, flood zones and E-designation
come from Lise's `city_layers` (PR 2 and PR 16) and stay null, meaning "not known", until they land.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from api.contracts import SiteProfile
from data_pull import soda_client
from site_profile import signals as signal_rules
from site_profile import work_types

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"

_DATASET_NAMES = {
    "dob_now_filings": "DOB NOW: Build - Job Application Filings",
    "dob_violations": "DOB Violations",
    "ecb_violations": "DOB ECB Violations",
    "dob_safety_violations": "DOB Safety Violations",
    "hpd_violations": "HPD Violations (housing, never scored as structural)",
    "dob_complaints": "DOB Complaints Received",
    "dob_311_requests": "311 requests routed to DOB",
    "pluto": "PLUTO",
}


class PullUnavailable(Exception):
    """No saved pull for the BBL and the live pull failed."""


def find_cached_pull(bbl: str, cache_dir: Path = CACHE_DIR) -> Optional[dict]:
    """The newest saved pull whose site is this BBL."""
    best = None
    for path in sorted(cache_dir.glob("*.json")):
        try:
            pull = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(pull, dict) and pull.get("site_bbl") == bbl and "site" in pull:
            if best is None or str(pull.get("pulled_at")) > str(best.get("pulled_at")):
                best = pull
    return best


def load_pull(bbl: str, cache_dir: Path = CACHE_DIR, live: bool = True) -> dict:
    soda_client.validate_bbl(bbl)
    cached = find_cached_pull(bbl, cache_dir)
    if cached is not None:
        return cached
    if not live:
        raise PullUnavailable(f"no saved pull for {bbl}")
    from data_pull.site_brief_pull import pull_site  # network; imported late so tests stay offline

    try:
        return pull_site(bbl=bbl)
    except (soda_client.SodaQueryError, ValueError, OSError) as error:
        raise PullUnavailable(f"live pull failed for {bbl}: {error}") from error


def _num(value: object) -> Optional[float]:
    try:
        number = float(str(value))
    except (TypeError, ValueError):
        return None
    return number


def _int(value: object) -> Optional[int]:
    number = _num(value)
    return int(number) if number is not None and number > 0 else None


def _pluto(lot: dict) -> dict:
    result = lot["datasets"].get("pluto") or {}
    return (result.get("records") or [{}])[0] if result.get("status") == "ok" else {}


def _footprints(lot: dict) -> list[dict]:
    result = lot.get("footprint_buildings") or {}
    return result.get("records") or [] if result.get("status") == "ok" else []


def _bins(lot: dict) -> list[str]:
    found = set(lot.get("bins") or [])
    for building in _footprints(lot):
        bin_number = str(building.get("bin") or "")
        if len(bin_number) == 7 and bin_number.isdigit() and not soda_client.is_placeholder_bin(bin_number):
            found.add(bin_number)
    return sorted(found)


def _has_building(lot: dict) -> bool:
    return bool(_footprints(lot)) or (_int(_pluto(lot).get("numbldgs")) or 0) > 0


def lot_facts(lot: dict) -> dict:
    pluto = _pluto(lot)
    max_far = [x for x in (_num(pluto.get(k)) for k in ("residfar", "commfar", "facilfar")) if x]
    return {
        "address": pluto.get("address"),
        "zoning": pluto.get("zonedist1"),
        "built_far": _num(pluto.get("builtfar")),
        "max_far": max(max_far) if max_far else None,
        "lot_area_sqft": _int(pluto.get("lotarea")),
        "year_built": _int(pluto.get("yearbuilt")),
        "floors": _num(pluto.get("numfloors")),
        "building_class": pluto.get("bldgclass"),
        "landmark": pluto.get("landmark") or None,
        "historic_district": pluto.get("histdist") or None,
    }


def neighbor(lot: dict) -> dict:
    """A touching lot. `attached` means the lots touch on the tax map and the neighbor lot has a building:
    the public data does not say whether the walls are shared, so shared_wall_ft stays unknown."""
    pluto = _pluto(lot)
    heights = [h for h in (_num(b.get("height_roof")) for b in _footprints(lot)) if h]
    years = [y for y in (_int(b.get("construction_year")) for b in _footprints(lot)) if y]
    return {
        "bbl": lot["bbl"],
        "bins": _bins(lot),
        "address": pluto.get("address"),
        "attached": _has_building(lot),
        "year_built": _int(pluto.get("yearbuilt")) or (min(years) if years else None),
        "floors": _num(pluto.get("numfloors")),
        "building_class": pluto.get("bldgclass"),
        "height_ft": round(max(heights), 2) if heights else None,
        "shared_wall_ft": None,
    }


def dataset_statuses(site: dict) -> list[dict]:
    """How each source answered for the site lot. Skipped and failed are both "error": unknown, never zero."""
    out = []
    for key, result in site["datasets"].items():
        status = result.get("status")
        if status == "ok":
            status = "capped" if result.get("truncated") else "ok"
            count = result.get("count")
        else:
            status, count = "error", None
        dataset_id = (DATASET_IDS.get(key))
        out.append({
            "key": key,
            "name": _DATASET_NAMES.get(key, key),
            "status": status,
            "count": count,
            "source_url": f"https://data.cityofnewyork.us/d/{dataset_id}" if dataset_id else None,
        })
    return out


def _dataset_ids() -> dict[str, str]:
    from data_pull.lot_records import DATASETS

    return {key: spec[0] for key, spec in DATASETS.items()}


DATASET_IDS = _dataset_ids()


def _filings_before(site: dict, cutoff: Optional[date]) -> list[dict]:
    from checklist.record_dates import parse_record_date

    result = site["datasets"].get("dob_now_filings") or {}
    records = result.get("records") or [] if result.get("status") == "ok" else []
    if cutoff is None:
        return records
    return [r for r in records if (d := parse_record_date(r.get("filing_date"))) is not None and d < cutoff]


def build_profile(
    pull: dict,
    job_type: Optional[str] = None,
    stage: Optional[str] = None,
    as_of: Optional[str] = None,
    structural_model: Optional[dict] = None,
) -> dict:
    """A SiteProfile dict (validated against the contract) from a site pull."""
    cutoff = date.fromisoformat(as_of) if as_of else None
    site, touching = pull["site"], pull.get("touching_lots") or []
    lookup = pull.get("address_lookup") or {}
    pluto = _pluto(site)
    lat = lookup.get("latitude") or _num(pluto.get("latitude"))
    lon = lookup.get("longitude") or _num(pluto.get("longitude"))
    if lat is None or lon is None:
        raise ValueError(f"no coordinates for {site['bbl']}")
    resolved_job, resolved_types, inferred = work_types.resolve(_filings_before(site, cutoff), job_type)

    profile = {
        "bbl": site["bbl"],
        "bins": _bins(site),
        "address_matched": lookup.get("matched_label") or pluto.get("address") or site["bbl"],
        "lat": float(lat),
        "lon": float(lon),
        "lot": lot_facts(site),
        "neighbors": [neighbor(lot) for lot in touching],
        "job_type": resolved_job,
        "work_types": resolved_types,
        "work_types_inferred": inferred,
        "stage": stage,
        # Owned by city_layers (Lise, PR 2 and PR 16): null means not known yet, never "none".
        "soil": None,
        "bedrock_depth_ft": None,
        "flood": {"fema_zone": None, "stormwater": None, "sandy_inundation": None},
        "e_designation": None,
        "signals": signal_rules.site_signals(site, touching, cutoff),
        "structural_model": structural_model,
        "datasets": dataset_statuses(site),
        "as_of": as_of,
    }
    return SiteProfile.model_validate(profile).model_dump()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bbl", required=True)
    parser.add_argument("--job-type", choices=["new_building", "alteration", "demolition"])
    parser.add_argument("--stage", choices=["pre_acquisition", "design", "pre_filing", "construction"])
    parser.add_argument("--as-of", help="YYYY-MM-DD: only records dated before this day")
    args = parser.parse_args(argv)
    profile = build_profile(load_pull(args.bbl), args.job_type, args.stage, args.as_of)
    print(json.dumps(profile, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
