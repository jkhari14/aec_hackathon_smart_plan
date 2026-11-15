"""HPD's Order to Repair/Vacate Orders (tb8q-a3ar) as a city layer: the fire-damage orders.

HPD gives each order one of three reasons. Only "Fire Damage" names a hazard on ForeSite's list.
Orders for habitability and illegal occupancy are housing matters: they are counted in the layer's
description and left off the map, never filed under another hazard.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from city_layers import source_rows
from city_layers.layer_file import (
    BOROUGHS, BOROUGH_CODES, LayerInfo, Pulled, clean_bbl, count_text, feature, iso_date, left_out, point,
    point_geometry,
)

DATASET = "tb8q-a3ar"
INFO = LayerInfo(
    layer_id="vacate_orders",
    name="Vacate orders (fire damage)",
    description="HPD orders to vacate a building or part of one because of fire damage, 2012 on, "
    "with the rescind date when HPD has recorded one.",
    hazard="fire",
    source_name="HPD Order to Repair/Vacate Orders",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)
SELECT = (
    "vacate_order_number,primary_vacate_reason,vacate_type,vacate_effective_date,actual_rescind_date,"
    "number_of_vacated_units,house_number,street_name,boro_short_name,latitude,longitude,bbl"
)
HAZARD_BY_REASON = {"Fire Damage": "fire"}


def features_from_rows(rows: list[dict], pulled_on: date) -> tuple[list[dict], list[str]]:
    features, unplaced, other_reasons = [], 0, Counter()
    for row in rows:
        reason = str(row.get("primary_vacate_reason") or "").strip()
        if reason not in HAZARD_BY_REASON:
            other_reasons[reason or "no reason recorded"] += 1
            continue
        number = str(row.get("vacate_order_number") or "").split(".")[0]
        lon_lat = point(row.get("longitude"), row.get("latitude"))
        if not number or not lon_lat:
            unplaced += 1
            continue
        effective = iso_date(row.get("vacate_effective_date"))
        rescinded = iso_date(row.get("actual_rescind_date"))
        address = " ".join(str(row.get(k) or "").strip() for k in ("house_number", "street_name")).strip()
        borough = BOROUGHS.get(BOROUGH_CODES.get(str(row.get("boro_short_name") or "").strip().upper(), ""), "")
        scope = str(row.get("vacate_type") or "").strip().lower()
        parts = [
            f"{', '.join(p for p in (address, borough) if p) or 'Address not recorded'}.",
            f"Units vacated: {count_text(row.get('number_of_vacated_units'))}.",
            f"Rescinded {rescinded}." if rescinded else f"No rescind date on record at the pull ({pulled_on.isoformat()}).",
        ]
        if effective and effective > pulled_on.isoformat():
            parts.append("The source dates this order after the pull; the date is shown as recorded.")
        features.append(feature(
            INFO, number, point_geometry(lon_lat),
            hazard=HAZARD_BY_REASON[reason],
            severity=1,
            date=effective,
            title=f"Vacate order: {reason.lower()}" + (f" ({scope})" if scope else ""),
            summary=" ".join(parts),
            bbl=clean_bbl(row.get("bbl")),
            record_id=number,
        ))
    shown = len(rows) - sum(other_reasons.values())
    others = ", ".join(f"{n:,} for {reason.lower()}" for reason, n in other_reasons.most_common())
    notes = [
        left_out(unplaced, shown, "fire-damage orders", "no usable coordinates"),
        f"Not shown: {others}; those are housing matters, not a hazard this map tracks." if others else None,
    ]
    return features, [n for n in notes if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "order": "vacate_order_number"})
    features, notes = features_from_rows(rows, pulled_on or date.today())
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
