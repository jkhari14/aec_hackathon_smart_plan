"""The Sandy Inundation Zone (5xsi-dfpx) as a city layer: the areas Hurricane Sandy flooded in 2012.

The ID in the plan, uyj8-7rv5, is the dataset's map view, and the API answers it with empty rows;
the polygons are in 5xsi-dfpx. At full detail they are about 90 MB, so the server simplifies each
outline to about 10 m and the coordinates are rounded to about 1 m. That is fine for a wash on the
map; whether a given lot was flooded should be asked of the full-detail source.
"""

from __future__ import annotations

from datetime import date

from city_layers import source_rows
from city_layers.layer_file import LayerInfo, Pulled, feature, left_out

DATASET = "5xsi-dfpx"
MAP_VIEW = "uyj8-7rv5"
# Degrees: 0.0001 is about 10 m here. Coordinates keep 5 decimals, about 1 m.
SIMPLIFY_DEGREES = 0.0001
DECIMALS = 5
# Sandy's surge reached New York City on the night of October 29, 2012.
EVENT_DATE = "2012-10-29"
INFO = LayerInfo(
    layer_id="sandy_inundation",
    name="Sandy inundation zone",
    description="The areas flooded by Hurricane Sandy's storm surge in October 2012, as surveyed "
    "afterwards. Outlines are simplified to about 10 m for the map, so check a single lot against the source.",
    hazard="flood",
    source_name="Sandy Inundation Zone",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)


def _ring(ring: list) -> list | None:
    """A ring rounded to DECIMALS with repeated points dropped; None when it no longer encloses anything."""
    rounded: list[list[float]] = []
    for lon, lat, *_ in ring:
        pair = [round(float(lon), DECIMALS), round(float(lat), DECIMALS)]
        if not rounded or rounded[-1] != pair:
            rounded.append(pair)
    if len(rounded) >= 2 and rounded[0] != rounded[-1]:
        rounded.append(rounded[0])
    return rounded if len(rounded) >= 4 else None


def simplified(geometry: dict | None) -> dict | None:
    """The geometry as a rounded MultiPolygon; None when nothing of it is left at this precision.

    A polygon whose outer ring collapses is dropped with its holes; a hole that collapses is dropped alone.
    """
    if not geometry or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        return None
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    kept = []
    for polygon in polygons:
        outer = _ring(polygon[0]) if polygon else None
        if outer:
            kept.append([outer, *[hole for hole in (_ring(r) for r in polygon[1:]) if hole]])
    return {"type": "MultiPolygon", "coordinates": kept} if kept else None


def features_from_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    features, vanished = [], 0
    for number, row in enumerate(rows, start=1):
        geometry = simplified(row.get("the_geom"))
        if not geometry:
            vanished += 1
            continue
        survey = str(row.get("status") or "").strip()
        features.append(feature(
            INFO, str(number), geometry,
            hazard="flood",
            severity=0,
            date=EVENT_DATE,
            title="Flooded by Hurricane Sandy (2012)",
            summary="Inside the surveyed extent of Hurricane Sandy's storm surge, October 29 to 30, 2012."
            + (f" Survey status as recorded: {survey}." if survey else ""),
            bbl=None,
            record_id=None,
        ))
    return features, [n for n in [left_out(vanished, len(rows), "areas", "too small to draw at this detail")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    select = f"status,simplify_preserve_topology(the_geom,{SIMPLIFY_DEGREES}) as the_geom"
    rows, capped = source_rows.all_rows(DATASET, {"select": select, "order": ":id"})
    features, notes = features_from_rows(rows)
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
