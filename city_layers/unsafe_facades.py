"""DOB NOW: Safety facade filings (xubg-57si) as a city layer: buildings now UNSAFE or SWARMP.

The dataset holds one row per filing, several per building and inspection cycle, so counting rows
overstates buildings. Here each building appears once, with the status on its newest filing. The
dataset has no coordinates; a building is placed at its lot's point (PLUTO, else the tax map).

Owner and inspector names and the free-text comments are in the dataset and are never requested.
"""

from __future__ import annotations

from datetime import date

from city_layers import source_rows
from city_layers.layer_file import (
    LayerInfo, Pulled, bbl_from_parts, feature, iso_date, left_out, point_geometry,
)

DATASET = "xubg-57si"
INFO = LayerInfo(
    layer_id="unsafe_facades",
    name="Unsafe facades",
    description="Buildings whose newest facade inspection filing has the status UNSAFE, or SWARMP "
    "(safe with a repair and maintenance program). One mark per building; the status is the one on "
    "record at the pull and the date is that filing's. The inspection program covers buildings taller than "
    "six stories, so a building with no mark was not necessarily inspected.",
    hazard="facade",
    source_name="DOB NOW: Safety - Facades Compliance Filings",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=False,
)
SELECT = (
    "tr6_no,filing_type,cycle,bin,house_no,street_name,borough,block,lot,submitted_on,filing_date,"
    "current_status,filing_status,exterior_wall_type_s_,exterior_wall_material_s_"
)
# status -> (severity, title). UNSAFE requires public protection and repair; SWARMP is a watch item.
SHOWN = {
    "UNSAFE": (1, "Facade status: unsafe"),
    "SWARMP": (0, "Facade status: safe with a repair and maintenance program (SWARMP)"),
}


def _filed(row: dict) -> str:
    return iso_date(row.get("filing_date")) or iso_date(row.get("submitted_on")) or ""


def _cycle(row: dict) -> int:
    text = str(row.get("cycle") or "").strip()
    return int(text) if text.isdigit() else -1


def newest_filings(rows: list[dict]) -> tuple[list[dict], int]:
    """One row per building: its newest cycle's newest filing. Returns (rows, rows with no building id).

    A building is its BIN, or its lot when the BIN is missing or a placeholder.
    """
    newest: dict[str, dict] = {}
    unidentified = 0
    for row in rows:
        building = source_rows.usable_bin(row.get("bin")) or bbl_from_parts(row.get("borough"), row.get("block"), row.get("lot"))
        if not building:
            unidentified += 1
            continue
        rank = (_cycle(row), _filed(row), str(row.get("tr6_no") or ""))
        if building not in newest or rank > newest[building]["_rank"]:
            newest[building] = {**row, "_rank": rank}
    return list(newest.values()), unidentified


def features_from_rows(rows: list[dict], points: dict[str, tuple[float, float]], bin_lots: dict[str, str]) -> tuple[list[dict], list[str]]:
    """`rows` are newest_filings(); `points` is BBL -> point; `bin_lots` is BIN -> BBL for the lots PLUTO lacked."""
    features, unplaced, shown = [], 0, 0
    for row in rows:
        status = str(row.get("current_status") or "").strip().upper()
        if status not in SHOWN:
            continue
        shown += 1
        bbl = bbl_from_parts(row.get("borough"), row.get("block"), row.get("lot"))
        if bbl not in points:
            bbl = bin_lots.get(source_rows.usable_bin(row.get("bin")) or "", bbl)
        number = str(row.get("tr6_no") or "").strip()
        if not number or bbl not in points:
            unplaced += 1
            continue
        level, title = SHOWN[status]
        address = " ".join(str(row.get(k) or "").strip() for k in ("house_no", "street_name")).strip()
        place = ", ".join(p for p in (address, str(row.get("borough") or "").strip()) if p)
        filed_as = str(row.get("filing_status") or "").strip()
        wall = "; ".join(str(row.get(k) or "").strip().lower() for k in ("exterior_wall_type_s_", "exterior_wall_material_s_") if row.get(k))
        parts = [
            f"{place or 'Address not recorded'}.",
            f"Inspection cycle {str(row.get('cycle') or '?').strip()}, filing {number}"
            + (f", filed as {filed_as}." if filed_as and filed_as.upper() != status else "."),
            f"Exterior wall: {wall}." if wall else "",
        ]
        features.append(feature(
            INFO, number, point_geometry(points[bbl]),
            hazard="facade",
            severity=level,
            date=_filed(row) or None,
            title=title,
            summary=" ".join(p for p in parts if p),
            bbl=bbl,
            record_id=number,
        ))
    return features, [n for n in [left_out(unplaced, shown, "buildings", "the lot is in neither PLUTO nor the tax map")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "order": "tr6_no,:id"})
    newest, unidentified = newest_filings(rows)
    marked = [row for row in newest if str(row.get("current_status") or "").strip().upper() in SHOWN]
    lots = {bbl_from_parts(row.get("borough"), row.get("block"), row.get("lot")) for row in marked} - {None}
    points = source_rows.lot_points(lots)
    # A filing can name a condo unit lot, which PLUTO does not list; the building's footprint names its lot.
    missed = {b for b in (source_rows.usable_bin(row.get("bin")) for row in marked
                          if bbl_from_parts(row.get("borough"), row.get("block"), row.get("lot")) not in points) if b}
    bin_lots = source_rows.building_lots(missed)
    points.update(source_rows.lot_points(set(bin_lots.values()) - set(points)))
    features, notes = features_from_rows(newest, points, bin_lots)
    notes.append(left_out(unidentified, len(rows), "filings", "no usable building number or lot"))
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, [n for n in notes if n])
