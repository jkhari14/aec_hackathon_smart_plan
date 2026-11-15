"""The citywide watchlist: active earth work next to a pre-1940 building built to the shared lot line.

    python -m early_warning.watchlist            # writes data/layers/watchlist.geojson
    python -m early_warning.watchlist --limit 50 # a quick sample

1. DOB NOW filings (w9ak-ipjd) with an earth-work, foundation or SOE work type, a first permit in the last
   12 months, and no sign-off, letter of completion, CO or withdrawal.
2. The lots touching each one, from the tax-lot polygons (i38t-6if2) of its block: lots across a street are
   on another block, so a block holds every touching lot.
3. PLUTO (64uk-42ks) for each touching lot's year built, and the building footprints (5zhs-2jue) for
   whether its building reaches the shared lot line (within 1 m, for at least 3 m). PLUTO's attachment code
   is not used: it marks some row houses as detached.

A feature is a prompt to look, never a finding. Owner, applicant and contractor names are never selected.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from api.contracts import LayerCatalogEntry, LayerFeatureCollection
from data_pull import soda_client
from data_pull.lot_neighbors import BUILDING_FOOTPRINTS, TAX_LOT_POLYGONS
from early_warning import geometry

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "layers" / "watchlist.geojson"
FILINGS = "w9ak-ipjd"
PLUTO = "64uk-42ks"
LAYER_ID = "watchlist"
OLD_BEFORE = 1940
TOUCH_M = 0.5
WALL_M = 1.0
MIN_WALL_M = 3.0
BATCH = 40
CLOSED = ("LOC ISSUED", "CO ISSUED", "WITHDRAWN", "SIGNED-OFF", "SIGNED OFF", "DISAPPROVED")
WORK = {"earth_work_work_type_": "earth work", "foundation_work_type_": "foundation",
        "support_of_excavation_work_type_": "support of excavation"}


def dataset_url(dataset_id: str) -> str:
    return f"https://data.cityofnewyork.us/d/{dataset_id}"


@dataclass
class Candidate:
    bbl: str
    lat: float
    lon: float
    address: str
    filings: list[dict] = field(default_factory=list)
    work: list[str] = field(default_factory=list)
    neighbors: list[dict] = field(default_factory=list)


class Partial(Exception):
    """Some batches failed: the layer is "at least" what was found."""


def all_rows(dataset_id: str, params: dict[str, str], cap: int = 50_000) -> list[dict]:
    rows, offset = [], 0
    while offset < cap:
        page, _ = soda_client.query(dataset_id, {**params, "offset": str(offset), "order": ":id"})
        rows += page
        if len(page) < soda_client.ROW_LIMIT:
            return rows
        offset += soda_client.ROW_LIMIT
    raise Partial(f"{dataset_id}: more than {cap} rows")


def active_filings(today: date) -> list[dict]:
    flags = " OR ".join(f"upper({f})='YES'" for f in WORK)
    since = (today - timedelta(days=365)).isoformat()
    rows = all_rows(FILINGS, {
        "select": "job_filing_number,job_type,filing_status,first_permit_date,signoff_date,bbl,house_no,street_name,"
                  "borough,latitude,longitude," + ",".join(WORK),
        "where": f"({flags}) AND first_permit_date > '{since}' AND signoff_date IS NULL",
    })
    return [r for r in rows if not any(word in str(r.get("filing_status") or "").upper() for word in CLOSED)]


def candidates(filings: list[dict]) -> dict[str, Candidate]:
    found: dict[str, Candidate] = {}
    for row in filings:
        bbl = str(row.get("bbl") or "").split(".")[0]
        try:
            soda_client.validate_bbl(bbl)
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (ValueError, KeyError, TypeError):
            continue
        address = " ".join(" ".join(str(row.get(k) or "").split()) for k in ("house_no", "street_name")).strip().title()
        cand = found.setdefault(bbl, Candidate(bbl, lat, lon, address))
        cand.filings.append(row)
        cand.work += [name for key, name in WORK.items()
                      if str(row.get(key) or "").upper() == "YES" and name not in cand.work]
    return found


def _batches(items: list[str], size: int = BATCH) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def _parallel(fn, batches: list, failures: list[str]) -> list:
    def run(batch):
        try:
            return fn(batch)
        except (soda_client.SodaQueryError, Partial) as error:
            failures.append(str(error))
            return []
    with ThreadPoolExecutor(max_workers=6) as pool:
        return [row for rows in pool.map(run, batches) for row in rows]


def block_polygons(blocks: list[str], failures: list[str]) -> dict[str, dict]:
    """bbl -> tax-lot polygon for every lot on these blocks ("<boro><5-digit block>")."""
    def fetch(batch: list[str]) -> list[dict]:
        by_boro: dict[str, list[str]] = {}
        for b in batch:
            by_boro.setdefault(b[0], []).extend(soda_client.block_variants(b[1:]))
        where = " OR ".join(f"(boro='{boro}' AND block in {soda_client.soql_in(sorted(set(v)))})"
                            for boro, v in by_boro.items())
        return all_rows(TAX_LOT_POLYGONS, {"select": "bbl,the_geom", "where": where})
    polygons: dict[str, dict] = {}
    for row in _parallel(fetch, _batches(blocks, 15), failures):
        bbl = str(row.get("bbl") or "").split(".")[0]
        if isinstance(row.get("the_geom"), dict) and len(bbl) == 10:
            polygons[bbl] = row["the_geom"]
    return polygons


def pluto_rows(bbls: list[str], failures: list[str]) -> dict[str, dict]:
    def fetch(batch):
        return all_rows(PLUTO, {"select": "bbl,address,yearbuilt,numfloors,bldgclass",
                                "where": f"bbl in ({','.join(batch)})"})
    return {str(r.get("bbl", "")).split(".")[0]: r for r in _parallel(fetch, _batches(bbls, 150), failures)}


def footprints(bbls: list[str], failures: list[str]) -> dict[str, list[dict]]:
    def fetch(batch):
        return all_rows(BUILDING_FOOTPRINTS, {"select": "base_bbl,bin,construction_year,height_roof,the_geom",
                                              "where": f"base_bbl in {soda_client.soql_in(batch)}"})
    out: dict[str, list[dict]] = {}
    for row in _parallel(fetch, _batches(bbls, 60), failures):
        if isinstance(row.get("the_geom"), dict):
            out.setdefault(str(row.get("base_bbl", "")).split(".")[0], []).append(row)
    return out


def _year(row: dict) -> int | None:
    try:
        year = int(float(row.get("yearbuilt") or 0))
    except ValueError:
        return None
    return year if year > 0 else None


def build(today: date, limit: int | None = None) -> tuple[LayerFeatureCollection, list[str]]:
    failures: list[str] = []
    try:
        filings = active_filings(today)
    except (soda_client.SodaQueryError, Partial) as error:
        return collection([], "error", today, f"the DOB NOW filings query failed: {error}"), [str(error)]
    cands = candidates(filings)
    if limit:
        cands = dict(list(cands.items())[:limit])
    polygons = block_polygons(sorted({bbl[:6] for bbl in cands}), failures)

    by_block: dict[str, list[str]] = {}
    for other in polygons:
        by_block.setdefault(other[:6], []).append(other)
    touching: dict[str, list[str]] = {}
    for bbl in cands:
        site = polygons.get(bbl)
        if site is None:
            continue
        touching[bbl] = [other for other in by_block.get(bbl[:6], [])
                         if other != bbl and geometry.near(site, polygons[other], TOUCH_M)]
    neighbor_bbls = sorted({n for ns in touching.values() for n in ns})
    pluto = pluto_rows(neighbor_bbls, failures)
    old = [n for n in neighbor_bbls if (y := _year(pluto.get(n, {}))) and y < OLD_BEFORE]
    prints = footprints(old, failures)

    for bbl, neighbors in touching.items():
        for n in neighbors:
            year = _year(pluto.get(n, {}))
            if not year or year >= OLD_BEFORE:
                continue
            wall = max((geometry.shared_edge_m(fp["the_geom"], polygons[bbl], WALL_M) for fp in prints.get(n, [])),
                       default=0.0)
            if wall >= MIN_WALL_M:
                row = pluto[n]
                cands[bbl].neighbors.append({"bbl": n, "address": str(row.get("address") or "").title() or None,
                                             "year_built": year, "floors": row.get("numfloors"), "wall_m": wall})
    flagged = [c for c in cands.values() if c.neighbors]
    status = "capped" if failures else "ok"
    return collection(flagged, status, today, "; ".join(failures[:3]) if failures else None), failures


def _feature(c: Candidate) -> dict:
    permits = sorted(str(f.get("first_permit_date") or "")[:10] for f in c.filings)
    jobs = sorted({str(f.get("job_filing_number")) for f in c.filings})
    c.neighbors.sort(key=lambda n: n["year_built"])
    first = c.neighbors[0]
    others = len(c.neighbors) - 1
    next_door = (f"{first['address'] or 'lot ' + first['bbl']} (built {first['year_built']}"
                 + (f", {float(first['floors']):g} floors" if first.get("floors") else "") + ")"
                 + (f" and {others} more" if others else ""))
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [c.lon, c.lat]},
        "properties": {
            "id": f"{LAYER_ID}:{c.bbl}",
            "layer_id": LAYER_ID,
            "hazard": "geotech",
            "severity": 0,
            "date": permits[-1] or None,
            "title": f"Active earth work at {c.address or c.bbl}",
            "summary": (f"Permit for {' and '.join(c.work)} (filing{'s' if len(jobs) > 1 else ''} "
                        f"{', '.join(jobs[:3])}{' and more' if len(jobs) > 3 else ''}), first issued {permits[0]}, "
                        f"no sign-off yet. Next door: {next_door}, built to the shared lot line on the city's maps. "
                        f"A prompt to look, not a finding."),
            "source_name": "DOB NOW job filings, with tax lots, PLUTO and building footprints",
            "source_url": dataset_url(FILINGS),
            "bbl": c.bbl,
            "record_id": jobs[0],
        },
    }


def collection(flagged: list[Candidate], status: str, today: date, problem: str | None) -> LayerFeatureCollection:
    description = (f"Active DOB NOW earth-work, foundation or SOE permits from the 12 months before {today}, on "
                   f"lots next to a building from before {OLD_BEFORE} that reaches the shared lot line. Year built is "
                   f"PLUTO's, which is often an estimate. A prompt to look, not a finding.")
    if problem:
        description += f" Not complete: {problem}."
    layer = LayerCatalogEntry(
        layer_id=LAYER_ID, name="Excavation watchlist", description=description, hazard="geotech",
        source_name="DOB NOW job filings (w9ak-ipjd), tax lots (i38t-6if2), PLUTO (64uk-42ks), footprints (5zhs-2jue)",
        source_url=dataset_url(FILINGS),
        updated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        feature_count=len(flagged) if status != "error" else None, status=status, default_on=True,
    )
    features = sorted((_feature(c) for c in flagged), key=lambda f: f["properties"]["id"])
    return LayerFeatureCollection(type="FeatureCollection", layer=layer, features=features)


def to_text(result: LayerFeatureCollection) -> str:
    """One feature per line, so a refresh diffs by site."""
    data = result.model_dump()
    features = ",\n".join(json.dumps(f, ensure_ascii=False) for f in data["features"])
    return (f'{{"type": "FeatureCollection",\n"layer": {json.dumps(data["layer"], ensure_ascii=False)},\n'
            f'"features": [\n{features}\n]}}\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, help="only the first N candidate lots, for a quick check")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    result, failures = build(date.today(), args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(to_text(result))
    print(f"{result.layer.status}: {len(result.features)} sites -> {args.out}")
    if args.out.parent == OUT.parent:
        from city_layers.build_layers import LAYERS
        from city_layers.layer_file import write_catalog

        write_catalog(OUT.parent, first=tuple(LAYERS))  # the layers router serves catalog.json, not the folder
    for failure in failures:
        print(f"  failed: {failure}", file=sys.stderr)
    return 1 if result.layer.status == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
