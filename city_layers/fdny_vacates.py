"""The Fire Department's Building Vacate List (n5xc-7jfa) as a city layer.

The list has no coordinates, no record number and no reason for the order. Each building is placed
at its lot's point (PLUTO, else the tax map). Its status ("Dismissal", "Rescinded" or blank) is quoted as recorded:
the dataset does not define the words.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from city_layers import source_rows
from city_layers.layer_file import (
    BOROUGHS, BOROUGH_CODES, LayerInfo, Pulled, clean_bbl, feature, iso_date, left_out, point_geometry,
)

DATASET = "n5xc-7jfa"
INFO = LayerInfo(
    layer_id="fdny_vacates",
    name="FDNY vacate orders",
    description="Buildings the Fire Department ordered vacated (Fire Operations or the Bureau of Fire "
    "Prevention). The list gives no reason for an order; its status is quoted as recorded.",
    hazard="fire",
    source_name="NYC Fire Department Building Vacate List",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)
SELECT = "description,vac_date,bor,aka_address,bin,bbl,status_change_date,ocpcy_desc"


def _first_address(raw: object) -> str:
    """'120B ELIZABETH STREET, MN ;120 ELIZABETH STREET, MN' -> '120B ELIZABETH STREET, Manhattan'."""
    first = str(raw or "").split(";")[0].strip()
    street, _, boro = first.rpartition(",")
    name = BOROUGHS.get(BOROUGH_CODES.get(boro.strip().upper(), ""), "")
    return f"{street.strip()}, {name}" if street and name else first


def features_from_rows(rows: list[dict], points: dict[str, tuple[float, float]]) -> tuple[list[dict], list[str]]:
    features, unplaced, seen = [], 0, Counter()
    for row in rows:
        bbl = clean_bbl(row.get("bbl"))
        when = iso_date(row.get("vac_date"))
        if not bbl or bbl not in points:
            unplaced += 1
            continue
        # The list has no record number, so a building and a date identify an order; a repeat gets a suffix.
        key = f"{bbl}-{when or 'undated'}"
        seen[key] += 1
        if seen[key] > 1:
            key = f"{key}-{seen[key]}"
        status = str(row.get("description") or "").strip()
        changed = iso_date(row.get("status_change_date"))
        use = str(row.get("ocpcy_desc") or "").strip().lower()
        parts = [f"{_first_address(row.get('aka_address')) or 'Address not recorded'}."]
        if status:
            parts.append(f'Status as recorded: "{status}"' + (f", changed {changed}." if changed else "."))
        else:
            parts.append("No status recorded.")
        features.append(feature(
            INFO, key, point_geometry(points[bbl]),
            hazard="fire",
            severity=1,
            date=when,
            title="FDNY vacate order" + (f": {use} building" if use and use != "unknown" else ""),
            summary=" ".join(parts),
            bbl=bbl,
            record_id=None,
        ))
    return features, [n for n in [left_out(unplaced, len(rows), "orders", "the lot is in neither PLUTO nor the tax map")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "order": "vac_date,bin,:id"})
    points = source_rows.lot_points(b for b in (clean_bbl(row.get("bbl")) for row in rows) if b)
    features, notes = features_from_rows(rows, points)
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
