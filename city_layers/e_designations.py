"""E-Designations (hxm3-23vy) as a city layer: the lots designated for hazardous materials.

An E-designation is a requirement on a lot (testing or remediation before work), not a violation.
The dataset also holds designations for air quality and noise alone; those are not contamination,
so they are counted in the layer's description and left off this map. The dataset has no
coordinates; a lot is placed at its point in PLUTO, or the middle of its tax-map polygon.
"""

from __future__ import annotations

from datetime import date

from city_layers import source_rows
from city_layers.layer_file import LayerInfo, Pulled, clean_bbl, feature, iso_date, left_out, point_geometry

DATASET = "hxm3-23vy"
INFO = LayerInfo(
    layer_id="e_designations",
    name="E-designations (hazardous materials)",
    description="Lots with an environmental (E) designation for hazardous materials; each shows the "
    "requirement as the record states it. A requirement on the lot, not a violation.",
    hazard="contamination",
    source_name="E-Designations",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)
SELECT = "enumber,effective_date,hazmat_code,air_code,noise_code,description,bbl"


def _also(row: dict) -> str:
    others = [name for name, key in (("air quality", "air_code"), ("noise", "noise_code")) if row.get(key) is True]
    return f" Also designated for {' and '.join(others)}." if others else ""


def features_from_rows(rows: list[dict], points: dict[str, tuple[float, float]]) -> tuple[list[dict], list[str]]:
    features, unplaced, hazmat = [], 0, 0
    for row in rows:
        if row.get("hazmat_code") is not True:
            continue
        hazmat += 1
        bbl = clean_bbl(row.get("bbl"))
        number = str(row.get("enumber") or "").strip()
        if not number or not bbl or bbl not in points:
            unplaced += 1
            continue
        recorded = str(row.get("description") or "").strip()
        features.append(feature(
            INFO, f"{number}:{bbl}", point_geometry(points[bbl]),
            hazard="contamination",
            severity=0,
            date=iso_date(row.get("effective_date")),
            title="E-designation: hazardous materials",
            summary=f"{number} on this lot.{_also(row)}" + (f" As recorded: {recorded}" if recorded else ""),
            bbl=bbl,
            record_id=number,
        ))
    others = len(rows) - hazmat
    notes = [
        left_out(unplaced, hazmat, "designated lots", "the lot is in neither PLUTO nor the tax map"),
        f"Not shown: {others:,} designations for air quality or noise alone." if others else None,
    ]
    return features, [n for n in notes if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "order": "enumber,bbl,:id"})
    lots = {clean_bbl(row.get("bbl")) for row in rows if row.get("hazmat_code") is True} - {None}
    features, notes = features_from_rows(rows, source_rows.lot_points(lots))
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, notes)
