"""data_pull's cached site record + the checklist engine + optional geometry -> one Brief."""

import json
import pathlib
import re
from datetime import date
from typing import Optional

from jahleel.api.brief.brief_models import Brief, Building, ChecklistRow, ChecklistSummary, DatasetStatus, Lot, LotFacts
from jahleel.api.brief.brief_records import lot_records
from checklist.build_checklist import build as build_checklist

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FOLDER = pathlib.Path(__file__).resolve().parents[2]  # jahleel/
CACHE_DIR = REPO_ROOT / "data" / "cache"  # data_pull's
LEADS_DIR = REPO_ROOT / "data" / "leads"  # the checklist engine's
GEOMETRY_DIR = FOLDER / "data" / "geometry"  # this folder's own
_SLUG = re.compile(r"^[a-z0-9-]{1,80}$", re.ASCII)


def _number(raw, cast):
    try:
        return cast(float(raw)) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _facts(lot: dict) -> Optional[LotFacts]:
    pluto = lot["datasets"].get("pluto") or {}
    rows = pluto.get("records") or []
    if pluto.get("status") != "ok" or not rows:
        return None
    row = rows[0]
    return LotFacts(
        address=row.get("address"),
        year_built=_number(row.get("yearbuilt"), int) or None,  # PLUTO uses 0 for unknown
        floors=_number(row.get("numfloors"), float),
        building_class=row.get("bldgclass"),
        zoning_district=row.get("zonedist1"),
        residential_units=_number(row.get("unitsres"), int),
        lot_front_ft=_number(row.get("lotfront"), float),
        lot_depth_ft=_number(row.get("lotdepth"), float),
        pluto_version=row.get("version"),
    )


def _lot(lot: dict, role: str, sources: dict, geometry: dict, record_ids: list[str]) -> Lot:
    lot_geometry = geometry.get(lot["bbl"], {})
    return Lot(
        bbl=lot["bbl"],
        role=role,
        facts=_facts(lot),
        datasets=[
            DatasetStatus(
                key=key, name=sources.get(key, {}).get("name", key), status=pulled["status"],
                count=pulled.get("count"), reason=pulled.get("reason"), query_url=pulled.get("query_url"),
            )
            for key, pulled in lot["datasets"].items()
        ],
        record_ids=record_ids,
        lot_geometry=lot_geometry.get("lot_geometry"),
        buildings=[Building(**b) for b in lot_geometry.get("buildings", [])],
    )


def list_slugs() -> list[str]:
    """Cached sites, in data/demo_addresses.json order (the excavation site first), then the rest."""
    demo_path = REPO_ROOT / "data" / "demo_addresses.json"
    order = json.loads(demo_path.read_text()).get("addresses", []) if demo_path.exists() else []

    def rank(path: pathlib.Path) -> tuple[int, str]:
        typed = (json.loads(path.read_text()).get("address_lookup") or {}).get("input")
        return (order.index(typed) if typed in order else len(order), path.stem)

    return [p.stem for p in sorted(CACHE_DIR.glob("*.json"), key=rank)]


def build_brief(slug: str, project_type: str = "excavation_next_to_existing", as_of: Optional[date] = None) -> Brief:
    """Raises FileNotFoundError for an unknown slug and ValueError for a malformed one.

    `as_of` is passed to the checklist engine (records dated before that day). The brief's record
    list stays complete; readers filter it with the same rule.
    """
    if not _SLUG.match(slug):
        raise ValueError(f"not a site slug: {slug!r}")
    pulled = json.loads((CACHE_DIR / f"{slug}.json").read_text())
    geometry_path = GEOMETRY_DIR / f"{slug}.json"
    geometry = json.loads(geometry_path.read_text()) if geometry_path.exists() else {}
    sources = pulled.get("sources", {})

    records, lots = [], []
    for lot, role in [(pulled["site"], "site")] + [(t, "touching") for t in pulled["touching_lots"]]:
        lot_recs = lot_records(lot, sources)
        records.extend(lot_recs)
        lots.append(_lot(lot, role, sources, geometry, [r.id for r in lot_recs]))

    leads_path = LEADS_DIR / f"{slug}.json"
    leads = json.loads(leads_path.read_text()) if leads_path.exists() else None
    checklist = build_checklist(pulled, {}, as_of, leads)
    caveats = list(pulled.get("caveats", [])) + [c for c in checklist["caveats"] if c not in pulled.get("caveats", [])]
    if not geometry:
        caveats.append("No lot geometry cached for this site yet: run jahleel.api.brief.brief_geometry_pull.")
    lookup = pulled.get("address_lookup") or {}
    return Brief(
        slug=slug,
        project_type=project_type,
        address_input=lookup.get("input", ""),
        matched_label=lookup.get("matched_label", ""),
        pulled_at=pulled["pulled_at"],
        site=lots[0],
        touching_lots=lots[1:],
        as_of=checklist["as_of"],
        records=sorted(records, key=lambda r: r.date or "", reverse=True),
        checklist=[ChecklistRow(**row) for row in checklist["rows"]],
        checklist_summary=ChecklistSummary(**checklist["summary"]),
        caveats=caveats,
    )
