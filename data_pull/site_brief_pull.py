"""Pull the public record for a site and every lot touching it, and save it as JSON.

    python -m data_pull.site_brief_pull "2625 Bedford Ave, Brooklyn"
    python -m data_pull.site_brief_pull --bbl 3052110074
    python -m data_pull.site_brief_pull --demo      # every address in data/demo_addresses.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from data_pull import lot_neighbors, soda_client
from data_pull.address_lookup import AddressLookupError, lookup_address
from data_pull.lot_records import DATASETS, pull_lot
from data_pull.stop_work_mentions import find_stop_work_mentions

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_ADDRESSES = REPO_ROOT / "data" / "demo_addresses.json"
CACHE_DIR = REPO_ROOT / "data" / "cache"

CAVEATS = [
    "Each dataset reports a status: ok (count may be 0, meaning queried and none found), "
    "error (the query failed, so nothing is known: never show it as zero), or skipped.",
    "Records are as of pulled_at. Check the live source before relying on one.",
    "PLUTO and the building footprints can lag a demolition or a collapse.",
    "Touching lots share an edge or a corner on the city's tax map.",
    "stop_work_mentions lists records whose text mentions a stop-work order. It is not a "
    "complete list: we have not found stop-work orders published as their own dataset.",
    "dob_311_requests and dob_complaints can hold the same complaint, and they share no key: "
    "never add their counts. 311 rows with no bbl, and rows before 2020, are missed.",
    "DOB violations filed under a letter borough code (a few thousand of 2.5 million rows) "
    "are found only through a BIN.",
]


def _sources() -> dict:
    sources = {
        key: {"name": name, "dataset_id": dataset_id,
              "url": f"https://data.cityofnewyork.us/d/{dataset_id}"}
        for key, (dataset_id, name, _, _) in DATASETS.items()
    }
    sources["tax_lot_polygons"] = {"name": "Tax lot polygons", "dataset_id": lot_neighbors.TAX_LOT_POLYGONS,
                                   "url": f"https://data.cityofnewyork.us/d/{lot_neighbors.TAX_LOT_POLYGONS}"}
    sources["building_footprints"] = {"name": "Building footprints", "dataset_id": lot_neighbors.BUILDING_FOOTPRINTS,
                                      "url": f"https://data.cityofnewyork.us/d/{lot_neighbors.BUILDING_FOOTPRINTS}"}
    sources["geosearch"] = {"name": "NYC Planning GeoSearch", "url": "https://geosearch.planninglabs.nyc/"}
    return sources


def _pull_one_lot(bbl: str, role: str, extra_bin: str | None) -> dict:
    footprints: dict
    try:
        buildings = lot_neighbors.footprint_buildings(bbl)
        footprints = {"status": "ok", "count": len(buildings), "records": buildings}
    except soda_client.SodaQueryError as error:
        buildings, footprints = [], {"status": "error", "error": str(error), "records": []}
    seed_bins = [str(b.get("bin", "")) for b in buildings if str(b.get("bin", "")).isdigit()]
    seed_bins = [b for b in seed_bins if len(b) == 7]
    if extra_bin:
        seed_bins.append(extra_bin)
    lot = pull_lot(bbl, seed_bins)
    lot["role"] = role
    lot["footprint_buildings"] = footprints
    lot["stop_work_mentions"] = find_stop_work_mentions(lot["datasets"])
    return lot


def pull_site(address: str | None = None, bbl: str | None = None) -> dict:
    pulled_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lookup = lookup_address(address) if address else None
    site_bbl = lookup["bbl"] if lookup else soda_client.validate_bbl(bbl or "")

    neighbors: list[str] = []
    try:
        site_wkt = lot_neighbors.lot_polygon_wkt(site_bbl)
        if site_wkt is None:
            neighbor_status = {"status": "skipped", "reason": "no tax-map polygon for the site lot"}
        else:
            neighbors = lot_neighbors.touching_lots(site_bbl, site_wkt)
            neighbor_status = {"status": "ok", "count": len(neighbors)}
    except soda_client.SodaQueryError as error:
        neighbor_status = {"status": "error", "error": str(error)}

    jobs = [(site_bbl, "site", lookup["bin"] if lookup else None)]
    jobs += [(n, "touching lot", None) for n in neighbors]
    with ThreadPoolExecutor(max_workers=4) as pool:
        lots = list(pool.map(lambda job: _pull_one_lot(*job), jobs))

    return {
        "schema_version": 1,
        "pulled_at": pulled_at,
        "address_lookup": lookup,
        "site_bbl": site_bbl,
        "touching_lots_lookup": neighbor_status,
        "site": lots[0],
        "touching_lots": lots[1:],
        "sources": _sources(),
        "caveats": CAVEATS,
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80] or "site"


def _summary_line(lot: dict) -> str:
    pluto = (lot["datasets"]["pluto"].get("records") or [{}])[0]
    parts = []
    for key, result in lot["datasets"].items():
        if key == "pluto":
            continue
        parts.append(f"{key}={result['count']}" if result["status"] == "ok" else f"{key}={result['status']}")
    return (f"  {lot['role']:<12} {lot['bbl']} {pluto.get('address', '?'):<28} "
            f"built {pluto.get('yearbuilt', '?')} | " + " ".join(parts)
            + f" | stop-work mentions={len(lot['stop_work_mentions'])}")


def save_pull(result: dict, name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_slug(name)}.json"
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("address", nargs="?", help="an NYC street address")
    parser.add_argument("--bbl", help="a 10-digit BBL instead of an address")
    parser.add_argument("--demo", action="store_true", help="pull every demo address")
    parser.add_argument("--out", type=Path, default=CACHE_DIR, help="output folder")
    args = parser.parse_args(argv)

    if args.demo:
        targets = [(a, None) for a in json.loads(DEMO_ADDRESSES.read_text())["addresses"]]
    elif args.address or args.bbl:
        targets = [(args.address, args.bbl)]
    else:
        parser.error("give an address, --bbl, or --demo")

    failed = 0
    for address, bbl in targets:
        try:
            result = pull_site(address=address, bbl=bbl)
        except (AddressLookupError, ValueError) as error:
            print(f"FAILED {address or bbl}: {error}", file=sys.stderr)
            failed += 1
            continue
        path = save_pull(result, address or f"bbl-{bbl}", args.out)
        label = (result["address_lookup"] or {}).get("matched_label") or result["site_bbl"]
        print(f"{label} -> {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}")
        for lot in [result["site"], *result["touching_lots"]]:
            print(_summary_line(lot))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
