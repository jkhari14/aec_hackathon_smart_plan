"""Which lots touch a lot, and which buildings stand on it.

Adjacency is computed by the city's server: the site's tax-lot polygon goes into an
`intersects()` query against every tax-lot polygon. A shared edge or a shared corner both
count as touching.
"""

from __future__ import annotations

import math

from data_pull import soda_client

TAX_LOT_POLYGONS = "i38t-6if2"
BUILDING_FOOTPRINTS = "5zhs-2jue"


def _coordinate_text(point: list) -> str:
    x, y = float(point[0]), float(point[1])
    if not (math.isfinite(x) and math.isfinite(y)):
        raise ValueError("non-finite coordinate in a lot polygon")
    return f"{x!r} {y!r}"


def geojson_to_wkt(geometry: dict) -> str:
    """Polygon or MultiPolygon GeoJSON -> MULTIPOLYGON WKT. Numbers only reach the query."""
    if geometry.get("type") == "Polygon":
        polygons = [geometry["coordinates"]]
    elif geometry.get("type") == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        raise ValueError(f"unsupported geometry type: {geometry.get('type')!r}")
    polygon_texts = []
    for polygon in polygons:
        rings = ["(" + ",".join(_coordinate_text(p) for p in ring) + ")" for ring in polygon]
        polygon_texts.append("(" + ",".join(rings) + ")")
    return "MULTIPOLYGON(" + ",".join(polygon_texts) + ")"


def lot_polygon_wkt(bbl: str) -> str | None:
    """The lot's tax-map polygon as WKT, or None when the tax map has no polygon for it."""
    soda_client.validate_bbl(bbl)
    rows, _ = soda_client.query(TAX_LOT_POLYGONS, {"where": f"bbl='{bbl}'", "select": "the_geom"})
    geometries = [row["the_geom"] for row in rows if isinstance(row.get("the_geom"), dict)]
    if not geometries:
        return None
    if len(geometries) == 1:
        return geojson_to_wkt(geometries[0])
    merged = {"type": "MultiPolygon", "coordinates": []}
    for geometry in geometries:
        part = geometry["coordinates"]
        merged["coordinates"].extend([part] if geometry.get("type") == "Polygon" else part)
    return geojson_to_wkt(merged)


def touching_lots(bbl: str, site_wkt: str) -> list[str]:
    """BBLs of the lots whose polygons touch the site's, excluding the site itself."""
    rows, _ = soda_client.query(
        TAX_LOT_POLYGONS,
        {"select": "bbl", "where": f"intersects(the_geom,'{site_wkt}') AND bbl!='{bbl}'"},
    )
    found = set()
    for row in rows:
        try:
            found.add(soda_client.validate_bbl(str(row.get("bbl", "")).split(".")[0]))
        except ValueError:
            continue
    return sorted(found)


def footprint_buildings(bbl: str) -> list[dict]:
    """Buildings the footprint dataset places on this lot. It can lag a demolition or collapse."""
    soda_client.validate_bbl(bbl)
    rows, _ = soda_client.query(
        BUILDING_FOOTPRINTS,
        {
            "select": "bin,construction_year,height_roof,last_status_type,last_edited_date",
            "where": f"base_bbl='{bbl}'",
        },
    )
    return rows
