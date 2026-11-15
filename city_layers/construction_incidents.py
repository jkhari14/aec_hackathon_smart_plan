"""DOB's Construction-Related Incidents (bf97-mjsy) as a city layer.

The dataset has a record type, a broad incident type, and injury and fatality counts; it has no
description or cause column, so a feature states none. Counts are DOB's at the time of entry.
"""

from __future__ import annotations

from datetime import date

from city_layers import source_rows
from city_layers.layer_file import (
    LayerInfo, Pulled, clean_bbl, count_text, feature, iso_date, left_out, point, point_geometry,
)

DATASET = "bf97-mjsy"
INFO = LayerInfo(
    layer_id="construction_incidents",
    name="Construction incidents",
    description="Accidents, incidents and notifications DOB records at construction sites, 2024 on. "
    "Injury and fatality counts are DOB's at the time of entry, and the source gives no cause.",
    hazard="construction_safety",
    source_name="DOB Construction-Related Incidents",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=True,
)
SELECT = (
    "accident_report_id,incident_date_mm_dd_yyyy,record_type_description,check2_description,fatality,"
    "injury,addressnumber,street,boro,address_latitude,address_longitude,address_bbl"
)
# The source's incident types that are not general construction safety.
HAZARD_BY_TYPE = {"Excavation/Soil Work": "geotech"}


def _number(value: object) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return 0


def severity(row: dict) -> int:
    """3 with a fatality, 2 with an injury, otherwise 1: a recorded event with no one reported hurt."""
    if _number(row.get("fatality")) > 0:
        return 3
    return 2 if _number(row.get("injury")) > 0 else 1


def features_from_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    features, unplaced = [], 0
    for row in rows:
        report_id = str(row.get("accident_report_id") or "").split(".")[0]
        lon_lat = point(row.get("address_longitude"), row.get("address_latitude"))
        if not report_id or not lon_lat:
            unplaced += 1
            continue
        kind = str(row.get("check2_description") or "").strip()
        record_type = str(row.get("record_type_description") or "Record").strip()
        address = " ".join(str(row.get(k) or "").strip() for k in ("addressnumber", "street")).strip()
        place = ", ".join(part for part in (address, str(row.get("boro") or "").strip()) if part)
        features.append(feature(
            INFO, report_id, point_geometry(lon_lat),
            hazard=HAZARD_BY_TYPE.get(kind, INFO.hazard),
            severity=severity(row),
            date=iso_date(row.get("incident_date_mm_dd_yyyy")),
            title=f"{record_type}: {kind.lower().replace('/', ' or ') or 'type not recorded'}",
            summary=f"{place or 'Address not recorded'}. Injuries: {count_text(row.get('injury'))}. "
            f"Fatalities: {count_text(row.get('fatality'))}.",
            bbl=clean_bbl(row.get("address_bbl")),
            record_id=report_id,
        ))
    return features, [n for n in [left_out(unplaced, len(rows), "records", "no usable coordinates")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "order": "accident_report_id"})
    features, notes = features_from_rows(rows)
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
