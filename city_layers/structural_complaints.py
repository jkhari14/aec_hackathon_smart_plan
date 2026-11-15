"""DOB complaints in the structural categories (eabe-havv) as a city layer.

A complaint is a signal, not a finding: most end with no violation. The dataset has only a BIN, so
each complaint is placed through its building's footprint, at that lot's point. Category
meanings come from DOB's printed list, imported by hand (manual_imports/); dispositions from DOB's
code table on Open Data. A code either key lacks is shown as the code, never guessed.

Never add these to 311 requests: the same complaint can be in both, with no shared key.
"""

from __future__ import annotations

from datetime import date

from checklist.complaint_codes import category_key
from city_layers import source_rows
from city_layers.layer_file import BOROUGHS, LayerInfo, Pulled, feature, iso_date, left_out, point_geometry
from data_pull import reference_tables
from manual_imports.load_imports import decode

DATASET = "eabe-havv"
# code -> hazard. 14 is excavation undermining a neighbor; the rest are about a structure itself.
CATEGORIES = {"03": "structural", "14": "geotech", "16": "structural", "30": "structural",
              "54": "structural", "2K": "structural", "5C": "structural"}
YEARS_BACK = 2
INFO = LayerInfo(
    layer_id="structural_complaints",
    name="Structural complaints",
    description="DOB complaints in the structural categories: adjacent building not protected (03), "
    "excavation undermining (14), inadequate shoring (16), structural stability (30), retaining wall (54), "
    "structurally compromised (2K), new building stability (5C). A complaint is a report, not a finding; "
    "each shows DOB's disposition with its date when one is recorded.",
    hazard="structural",
    source_name="DOB Complaints Received",
    source_url=f"https://data.cityofnewyork.us/d/{DATASET}",
    default_on=True,
)
SELECT = "complaint_number,date_entered,house_number,house_street,bin,complaint_category,disposition_date,disposition_code"


def first_day(pulled_on: date) -> date:
    """The layer holds complaints entered from January 1, two years before the pull."""
    return date(pulled_on.year - YEARS_BACK, 1, 1)


def where(pulled_on: date) -> str:
    """`date_entered` is text (MM/DD/YYYY), so the years are matched by their ending."""
    codes = ",".join(f"'{code}'" for code in CATEGORIES)
    years = " OR ".join(f"date_entered like '%/{year}'" for year in range(first_day(pulled_on).year, pulled_on.year + 1))
    return f"complaint_category in ({codes}) AND ({years})"


def category_titles() -> tuple[dict[str, str], str]:
    """Code -> the meaning as DOB's list prints it, and a sentence on where the meanings came from."""
    imported, about = category_key()
    if imported is None:
        return {}, "DOB's category list could not be loaded, so categories are shown as codes."
    titles = {}
    for code in CATEGORIES:
        found = decode(code, imported)
        if found.get("description"):
            titles[code] = found["description"]
    checked = "checked against the list" if about.get("status") == "imported_checked" else "not yet checked by a second person"
    return titles, f"Category wording is from DOB's printed list, imported by hand and {checked}."


def disposition_meanings() -> tuple[dict[str, str] | None, str | None]:
    """DOB's disposition code table, kept as printed; (None, a sentence) when it could not be pulled."""
    table = reference_tables.pull_disposition_codes()
    if table.get("status") != "ok":
        return None, "DOB's disposition code table could not be loaded, so dispositions are shown as codes."
    return {str(r.get("code") or "").strip(): str(r.get("disposition") or "").strip() for r in table["records"]}, None


def _disposition(row: dict, meanings: dict[str, str] | None, pulled_on: date) -> str:
    code = str(row.get("disposition_code") or "").strip()
    if not code:
        return f"No disposition on record at the pull ({pulled_on.isoformat()})."
    when = iso_date(row.get("disposition_date"))
    dated = f", dated {when}" if when else ", undated"
    meaning = (meanings or {}).get(code)
    if meaning:
        # The table's wording is quoted as printed, capitals and stray letters included.
        return f"DOB's disposition {code}{dated}: \"{meaning}\"."
    return f"DOB's disposition {code}{dated}" + (" (not in DOB's published code table)." if meanings is not None else ".")


def features_from_rows(
    rows: list[dict],
    bin_lots: dict[str, str],
    points: dict[str, tuple[float, float]],
    titles: dict[str, str],
    meanings: dict[str, str] | None,
    pulled_on: date,
) -> tuple[list[dict], list[str]]:
    features, unplaced, total = [], 0, 0
    since = first_day(pulled_on).isoformat()
    for row in rows:
        code = str(row.get("complaint_category") or "").strip().upper()
        entered = iso_date(row.get("date_entered"))
        number = str(row.get("complaint_number") or "").strip()
        if code not in CATEGORIES or not number or not entered or entered < since:
            continue
        total += 1
        bin_number = source_rows.usable_bin(row.get("bin"))
        bbl = bin_lots.get(bin_number or "")
        if bbl not in points:
            unplaced += 1
            continue
        address = " ".join(str(row.get(k) or "").strip() for k in ("house_number", "house_street")).strip()
        place = ", ".join(p for p in (address, BOROUGHS.get(bin_number[0], "")) if p)  # type: ignore[index]
        features.append(feature(
            INFO, number, point_geometry(points[bbl]),
            hazard=CATEGORIES[code],
            severity=0,
            date=entered,
            title=f"Complaint {code}: {titles[code]}" if code in titles else f"Complaint category {code}",
            summary=f"{place or 'Address not recorded'}. {_disposition(row, meanings, pulled_on)}",
            bbl=bbl,
            record_id=number,
        ))
    note = left_out(unplaced, total, "complaints", "the building has no footprint or lot point, or a placeholder BIN")
    return features, [n for n in [note] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    pulled_on = pulled_on or date.today()
    rows, capped = source_rows.all_rows(DATASET, {"select": SELECT, "where": where(pulled_on), "order": "complaint_number"})
    bin_lots = source_rows.building_lots(b for b in (source_rows.usable_bin(row.get("bin")) for row in rows) if b)
    points = source_rows.lot_points(set(bin_lots.values()))
    titles, titles_note = category_titles()
    meanings, meanings_note = disposition_meanings()
    features, notes = features_from_rows(rows, bin_lots, points, titles, meanings, pulled_on)
    notes = [f"Complaints entered from {first_day(pulled_on).isoformat()} on.", *notes, titles_note, meanings_note,
             "Not added to 311 requests, which can repeat a complaint."]
    return Pulled(features, source_rows.rows_updated_at(DATASET), capped, [n for n in notes if n])
