"""Pull tax-lot polygons and building footprints for every lot in a cached site, for the map and Rhino/Revit.

python -m api.brief.brief_geometry_pull            # every cached site
Writes data/cache/geometry/<slug>.json: {bbl: {lot_geometry, buildings: [...]}}. Uses data_pull's SODA client.
"""

import json
import sys

from api.brief.brief_build import CACHE_DIR, GEOMETRY_DIR, list_slugs
from data_pull.soda_client import query, soql_in, validate_bbl

TAX_LOT_POLYGONS = "i38t-6if2"
BUILDING_FOOTPRINTS = "5zhs-2jue"


def _float(raw):
    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def pull_site_geometry(slug: str) -> dict:
    pulled = json.loads((CACHE_DIR / f"{slug}.json").read_text())
    bbls = [validate_bbl(lot["bbl"]) for lot in [pulled["site"], *pulled["touching_lots"]]]
    lots, _ = query(TAX_LOT_POLYGONS, {"select": "bbl,the_geom", "where": f"bbl in {soql_in(bbls)}"})
    footprints, _ = query(BUILDING_FOOTPRINTS, {"where": f"base_bbl in {soql_in(bbls)}"})
    out = {bbl: {"lot_geometry": None, "buildings": []} for bbl in bbls}
    for row in lots:
        if row.get("bbl") in out:
            out[row["bbl"]]["lot_geometry"] = row.get("the_geom")
    for row in footprints:
        if row.get("base_bbl") in out:
            out[row["base_bbl"]]["buildings"].append({
                "bin": row.get("bin"),
                "construction_year": int(_float(row.get("construction_year")) or 0) or None,
                "height_roof_ft": _float(row.get("height_roof")),
                "ground_elevation_ft": _float(row.get("ground_elevation")),
                "status": row.get("last_status_type"),
                "geometry": row.get("the_geom"),
            })
    return out


def main() -> int:
    GEOMETRY_DIR.mkdir(parents=True, exist_ok=True)
    for slug in list_slugs():
        geometry = pull_site_geometry(slug)
        (GEOMETRY_DIR / f"{slug}.json").write_text(json.dumps(geometry, indent=1))
        missing = [bbl for bbl, g in geometry.items() if not g["lot_geometry"]]
        print(f"{slug}: {len(geometry)} lots, {sum(len(g['buildings']) for g in geometry.values())} footprints"
              + (f", no lot polygon for {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
