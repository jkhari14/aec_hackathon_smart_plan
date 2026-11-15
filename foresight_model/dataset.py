"""Training rows for the pattern model, pulled from NYC Open Data.

    .venv/bin/python -m foresight_model.dataset --sites 600      # writes foresight_model/artifacts/rows.json

One row is one lot with an earth-work, foundation or support-of-excavation filing in DOB NOW (2021 to
late 2025, so each has 12 months of follow-up). For that lot and every lot touching it we pull:
- the touching lots (tax-map polygons), their PLUTO facts and building footprints;
- DOB complaints in the structural categories, by BIN;
- construction incidents (bf97-mjsy) by BBL.

Features use only what was knowable on the filing date (neighbor buildings, prior complaints), never
the site's own PLUTO row, which can already describe the new building.

Label: within 365 days after the filing, a DOB complaint in category 30, 14, 16 or 5C, or a construction
incident other than a worker fall, on the site or a touching lot. Complaints about excavation next door
are often filed at the construction site's address, so the site lot counts too. HPD vacates are not used:
their reasons are fire, illegal occupancy and habitability, never structural.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from checklist.record_dates import parse_record_date
from data_pull import lot_neighbors, soda_client

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
FILINGS = "w9ak-ipjd"
PLUTO = "64uk-42ks"
COMPLAINTS = "eabe-havv"
INCIDENTS = "bf97-mjsy"

LABEL_COMPLAINTS = {"30", "14", "16", "5C"}
EVENT_COMPLAINTS = {"03", "14", "16", "30", "54", "2K", "5C"}
LABEL_INCIDENTS_EXCLUDE = {"Worker Fell"}
OLD_YEAR = 1940
WINDOW_DAYS = 365
PRIOR_DAYS = 3 * 365

FLAG_FIELDS = {
    "earth_work": "earth_work_work_type_",
    "foundation": "foundation_work_type_",
    "soe": "support_of_excavation_work_type_",
}
BOROUGHS = {"1": "manhattan", "2": "bronx", "3": "brooklyn", "4": "queens", "5": "staten_island"}


def candidate_sites(start: str, end: str) -> list[dict]:
    """Lots with a qualifying filing in [start, end): first filing date and which flags any filing had."""
    flags = " OR ".join(f"upper({f})='YES'" for f in FLAG_FIELDS.values())
    rows, _ = soda_client.query(FILINGS, {
        "select": "bbl, min(filing_date) as first_filing, max(job_type) as job_type, "
                  + ", ".join(f"max(upper({f})) as {k}" for k, f in FLAG_FIELDS.items()),
        "where": f"({flags}) AND filing_date >= '{start}T00:00:00' AND filing_date < '{end}T00:00:00' AND bbl IS NOT NULL",
        "group": "bbl",
        "limit": "50000",
    })
    out = []
    for row in rows:
        bbl = str(row.get("bbl") or "").split(".")[0]
        if len(bbl) == 10 and bbl.isdigit() and bbl[0] in BOROUGHS:
            out.append(row | {"bbl": bbl})
    return out


def sample_sites(per_year: int) -> list[dict]:
    """A deterministic sample (by hash of the BBL) of `per_year` lots per filing year, 2021 to 2025."""
    chosen = []
    for year in range(2021, 2026):
        end = f"{year + 1}-01-01" if year < 2025 else "2025-11-01"
        sites = candidate_sites(f"{year}-01-01", end)
        sites.sort(key=lambda s: hashlib.sha1(s["bbl"].encode()).hexdigest())
        chosen += sites[:per_year]
    seen, unique = set(), []
    for site in chosen:
        if site["bbl"] not in seen:
            seen.add(site["bbl"])
            unique.append(site)
    return unique


def _int(value) -> Optional[int]:
    try:
        number = int(float(str(value)))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def pull_site_records(site: dict) -> dict:
    """Touching lots, their PLUTO and footprints, complaints and incidents for one sampled site."""
    bbl = site["bbl"]
    wkt = lot_neighbors.lot_polygon_wkt(bbl)
    touching = lot_neighbors.touching_lots(bbl, wkt) if wkt else []
    lots = [bbl, *touching]
    pluto = {}
    if touching:
        rows, _ = soda_client.query(PLUTO, {
            "select": "bbl,yearbuilt,numfloors,bldgclass,numbldgs",
            "where": f"bbl in ({','.join(touching)})",
        })
        pluto = {str(r.get("bbl", "")).split(".")[0]: r for r in rows}
    rows, _ = soda_client.query(lot_neighbors.BUILDING_FOOTPRINTS, {
        "select": "bin,base_bbl,construction_year,height_roof",
        "where": f"base_bbl in {soda_client.soql_in(lots)}",
    })
    footprints: dict[str, list[dict]] = {}
    for row in rows:
        footprints.setdefault(str(row.get("base_bbl", "")).split(".")[0], []).append(row)
    bin_lot = {}
    for lot, buildings in footprints.items():
        for b in buildings:
            bin_number = str(b.get("bin") or "")
            if len(bin_number) == 7 and bin_number.isdigit() and not soda_client.is_placeholder_bin(bin_number):
                bin_lot[bin_number] = lot
    complaints = []
    if bin_lot:
        rows, _ = soda_client.query(COMPLAINTS, {
            "select": "complaint_number,bin,date_entered,complaint_category",
            # The category codes are our own constants, not user input.
            "where": f"bin in {soda_client.soql_in(sorted(bin_lot))} AND complaint_category in "
                     + "('" + "','".join(sorted(EVENT_COMPLAINTS)) + "')",
        })
        complaints = [r | {"lot": bin_lot.get(str(r.get("bin")))} for r in rows]
    rows, _ = soda_client.query(INCIDENTS, {
        "select": "accident_report_id,address_bbl,incident_date_mm_dd_yyyy,check2_description,fatality,injury",
        "where": f"address_bbl in {soda_client.soql_in(lots)}",
    })
    incidents = [r | {"lot": str(r.get("address_bbl") or "").split(".")[0]} for r in rows]
    return {"site": site, "touching": touching, "pluto": pluto, "footprints": footprints,
            "complaints": complaints, "incidents": incidents}


def events(records: dict) -> list[dict]:
    """Every dated event for the site and its touching lots: {date, kind, lot, where}."""
    site_bbl = records["site"]["bbl"]
    out = []
    for c in records["complaints"]:
        when = parse_record_date(c.get("date_entered"))
        code = str(c.get("complaint_category") or "").upper()
        if when:
            out.append({"date": when, "kind": f"complaint_{code}", "lot": c.get("lot"),
                        "where": "site" if c.get("lot") == site_bbl else "touching"})
    for i in records["incidents"]:
        when = parse_record_date(i.get("incident_date_mm_dd_yyyy"))
        kind = str(i.get("check2_description") or "Other")
        if when:
            out.append({"date": when, "kind": f"incident_{kind}", "lot": i.get("lot"),
                        "where": "site" if i.get("lot") == site_bbl else "touching",
                        "incident": kind, "severe": (_int(i.get("fatality")) or 0) > 0})
    return sorted(out, key=lambda e: e["date"])


def is_outcome(event: dict) -> bool:
    if event["kind"].startswith("complaint_"):
        return event["kind"].split("_", 1)[1] in LABEL_COMPLAINTS
    return event.get("incident") not in LABEL_INCIDENTS_EXCLUDE


def row_for(records: dict) -> Optional[dict]:
    site = records["site"]
    filed = parse_record_date(site.get("first_filing"))
    if filed is None:
        return None
    touching = records["touching"]
    neighbors = []
    for lot in touching:
        p = records["pluto"].get(lot) or {}
        fp = records["footprints"].get(lot) or []
        has_building = bool(fp) or (_int(p.get("numbldgs")) or 0) > 0
        year = _int(p.get("yearbuilt")) or min((y for y in (_int(b.get("construction_year")) for b in fp) if y),
                                                default=None)
        floors = _int(p.get("numfloors"))
        heights = [h for h in (_int(b.get("height_roof")) for b in fp) if h]
        neighbors.append({"has_building": has_building, "year": year, "floors": floors,
                          "height": max(heights) if heights else None, "class": str(p.get("bldgclass") or "")})
    attached = [n for n in neighbors if n["has_building"]]
    old = [n for n in attached if n["year"] and n["year"] < OLD_YEAR]
    years = [n["year"] for n in attached if n["year"]]
    evs = events(records)
    prior = [e for e in evs if filed - timedelta(days=PRIOR_DAYS) <= e["date"] < filed]
    window = [e for e in evs if filed <= e["date"] < filed + timedelta(days=WINDOW_DAYS)]
    outcomes = [e for e in window if is_outcome(e)]
    flags = {k: str(site.get(k) or "").upper() == "YES" for k in FLAG_FIELDS}
    features = {
        "job_new_building": int("new" in str(site.get("job_type") or "").lower()),
        "flag_earth_work": int(flags["earth_work"]),
        "flag_foundation": int(flags["foundation"]),
        "flag_soe": int(flags["soe"]),
        "touching_lots": len(touching),
        "attached_neighbors": len(attached),
        "pre1940_attached": len(old),
        "oldest_neighbor_year": min(years) if years else 0,
        "max_neighbor_floors": max((n["floors"] or 0 for n in attached), default=0),
        "max_neighbor_height_ft": max((n["height"] or 0 for n in attached), default=0),
        "masonry_era_walkups": sum(1 for n in old if n["class"][:1] in {"A", "B", "C", "S"}),
        "prior_structural_complaints": sum(1 for e in prior if e["kind"].startswith("complaint_")),
        "prior_adjacent_complaints": sum(1 for e in prior if e["kind"] == "complaint_03"),
        "prior_incidents": sum(1 for e in prior if e["kind"].startswith("incident_")),
        **{f"boro_{name}": int(site["bbl"][0] == digit) for digit, name in BOROUGHS.items()},
    }
    first_outcome = outcomes[0]["date"] if outcomes else None
    return {
        "bbl": site["bbl"],
        "filing_date": filed.isoformat(),
        "label": int(bool(outcomes)),
        "first_outcome": first_outcome.isoformat() if first_outcome else None,
        "features": features,
        # For sequence mining: what happened from 3 years before the filing up to the first outcome.
        "sequence": [{"date": e["date"].isoformat(), "kind": e["kind"], "where": e["where"]}
                     for e in evs if filed - timedelta(days=PRIOR_DAYS) <= e["date"]
                     and (first_outcome is None or e["date"] <= first_outcome)
                     and e["date"] < filed + timedelta(days=WINDOW_DAYS)],
    }


def build(per_year: int, workers: int = 8) -> dict:
    sites = sample_sites(per_year)
    print(f"{len(sites)} sampled sites", file=sys.stderr)

    def one(site):
        try:
            return row_for(pull_site_records(site)), None
        except (soda_client.SodaQueryError, ValueError) as error:
            return None, f"{site['bbl']}: {error}"

    rows, failures = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, (row, failure) in enumerate(pool.map(one, sites), 1):
            if row:
                rows.append(row)
            if failure:
                failures.append(failure)
            if i % 50 == 0:
                print(f"  {i}/{len(sites)}", file=sys.stderr)
    return {"built_on": date.today().isoformat(), "per_year": per_year, "sites_sampled": len(sites),
            "rows": rows, "failed_sites": failures,
            "sources": {k: f"https://data.cityofnewyork.us/d/{v}" for k, v in
                        {"filings": FILINGS, "pluto": PLUTO, "complaints": COMPLAINTS, "incidents": INCIDENTS,
                         "tax_lots": lot_neighbors.TAX_LOT_POLYGONS,
                         "footprints": lot_neighbors.BUILDING_FOOTPRINTS}.items()}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-year", type=int, default=120)
    parser.add_argument("--out", type=Path, default=ARTIFACTS / "rows.json")
    args = parser.parse_args(argv)
    result = build(args.per_year)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, separators=(",", ":")) + "\n")
    positives = sum(r["label"] for r in result["rows"])
    print(f"{len(result['rows'])} rows, {positives} positive, {len(result['failed_sites'])} failed -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
