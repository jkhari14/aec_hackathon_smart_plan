"""FEMA's special flood hazard areas for the city, from the National Flood Hazard Layer.

These are the zones on FEMA's effective flood map whose `SFHA_TF` flag is true (A, AE and VE in
this pull). Outlines are simplified to about 10 m, so the layer is a wash for the map; ask
`site_context.fema_zone` about one lot. A base flood elevation of -9999 is FEMA's "none" and is
never shown as a number.
"""

from __future__ import annotations

from datetime import date

from city_layers import arcgis_rows
from city_layers.layer_file import LayerInfo, Pulled, feature, left_out
from city_layers.sandy_inundation import DECIMALS, SIMPLIFY_DEGREES, simplified

LAYER_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28"
NYC_MAP = "360497"  # FEMA's DFIRM_ID for the City of New York
FIELDS = "FLD_AR_ID,FLD_ZONE,ZONE_SUBTY,STATIC_BFE"
NO_ELEVATION = -9999
INFO = LayerInfo(
    layer_id="fema_flood_zones",
    name="FEMA flood zones",
    description="The special flood hazard areas on FEMA's effective flood map for the city (zones A, AE "
    "and VE). Outlines are simplified to about 10 m for the map, so check a single lot against the source.",
    hazard="flood",
    source_name="FEMA National Flood Hazard Layer",
    source_url=LAYER_URL,
    default_on=False,
)


def elevation_text(raw: object) -> str:
    """' Base flood elevation as recorded: 14 ft.', or '' when FEMA records none."""
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return ""
    return "" if value <= NO_ELEVATION else f" Base flood elevation as recorded: {value:g} ft."


def features_from_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    features, vanished = [], 0
    for row in rows:
        fields = row.get("properties") or {}
        geometry = simplified(row.get("geometry"))
        area_id = str(fields.get("FLD_AR_ID") or "").strip()
        if not geometry or not area_id:
            vanished += 1
            continue
        zone = str(fields.get("FLD_ZONE") or "").strip() or "not recorded"
        subtype = str(fields.get("ZONE_SUBTY") or "").strip()
        features.append(feature(
            INFO, area_id, geometry,
            hazard="flood",
            severity=0,
            date=None,
            title=f"FEMA flood zone {zone}" + (f" ({subtype.lower()})" if subtype else ""),
            summary="A special flood hazard area on FEMA's effective flood map." + elevation_text(fields.get("STATIC_BFE")),
            bbl=None,
            record_id=area_id,
        ))
    return features, [n for n in [left_out(vanished, len(rows), "areas", "too small to draw at this detail, or no id")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = arcgis_rows.all_features(
        LAYER_URL, f"DFIRM_ID='{NYC_MAP}' AND SFHA_TF='T'", FIELDS, SIMPLIFY_DEGREES, DECIMALS)
    features, notes = features_from_rows(rows)
    # FEMA's service gives no "last changed" date for the layer, so the catalog says the date is unknown.
    return Pulled(features, None, capped, notes)
