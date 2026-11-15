"""311 flooding requests routed to DEP (erm2-nwe9) as a city layer: the last twelve months.

Street flooding, sewer backups and water in basements, as the caller reported them. A 311 request
is a report, not a finding, and many repeat the same event. DEP renamed its request types in 2026,
so both sets of names are matched. Never add these to DOB complaints or to each other as "floods".
"""

from __future__ import annotations

from datetime import date, timedelta

from city_layers import source_rows
from city_layers.layer_file import LayerInfo, Pulled, clean_bbl, feature, iso_date, left_out, point, point_geometry

DATASET = "erm2-nwe9"
DAYS_BACK = 365
# descriptor as 311 prints it -> what the feature is called
KINDS = {
    "Street Flooding (SJ)": "street flooding",
    "Flooding on Street": "street flooding",
    "Highway Flooding (SH)": "highway flooding",
    "Flooding on Highway": "highway flooding",
    "Sewer Backup (Use Comments) (SA)": "sewer backup",
    "Backup": "sewer backup",
    "Excessive Water In Basement (WEFB)": "excessive water in basement",
}
INFO = LayerInfo(
    layer_id="flooding_complaints",
    name="311 flooding reports",
    description="311 requests routed to DEP for street or highway flooding, sewer backups and water in "
    "basements, over the last twelve months. A request is a caller's report, not a finding, and one storm "
    "can bring many requests for the same spot.",
    hazard="flood",
    source_name="311 Service Requests from 2020 to Present",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)
SELECT = "unique_key,created_date,complaint_type,descriptor,incident_address,borough,bbl,latitude,longitude"


def first_day(pulled_on: date) -> date:
    return pulled_on - timedelta(days=DAYS_BACK)


def where(pulled_on: date) -> str:
    kinds = ",".join("'" + descriptor.replace("'", "''") + "'" for descriptor in KINDS)
    return f"agency='DEP' AND descriptor in ({kinds}) AND created_date >= '{first_day(pulled_on).isoformat()}T00:00:00'"


def features_from_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    features, unplaced, total = [], 0, 0
    for row in rows:
        kind = KINDS.get(str(row.get("descriptor") or "").strip())
        key = str(row.get("unique_key") or "").strip()
        if not kind or not key:
            continue
        total += 1
        lon_lat = point(row.get("longitude"), row.get("latitude"))
        if not lon_lat:
            unplaced += 1
            continue
        address = str(row.get("incident_address") or "").strip()
        borough = str(row.get("borough") or "").strip().title()
        place = ", ".join(p for p in (address, "" if borough == "Unspecified" else borough) if p)
        features.append(feature(
            INFO, key, point_geometry(lon_lat),
            hazard="flood",
            severity=0,
            date=iso_date(row.get("created_date")),
            title=f"311 report: {kind}",
            summary=f"{place or 'Address not recorded'}. Reported to 311 and routed to DEP.",
            bbl=clean_bbl(row.get("bbl")),
            record_id=key,
        ))
    return features, [n for n in [left_out(unplaced, total, "requests", "no usable coordinates; highway requests rarely have them")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    pulled_on = pulled_on or date.today()
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "where": where(pulled_on), "order": "unique_key"})
    features, notes = features_from_rows(rows)
    notes = [f"Requests created from {first_day(pulled_on).isoformat()} on.", *notes,
             "Not added to DOB complaints, which can repeat a request."]
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
