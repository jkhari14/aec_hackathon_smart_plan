"""DOB complaint codes, decoded, each meaning labeled with the key it came from and its trust level.

Two keys, never mixed:
- complaint categories: DOB's printed list, imported by hand (manual_imports/). kind "manual_import",
  status "imported_unchecked" or "imported_checked", never "ok".
- dispositions: Open Data 6v9u-ndjg, pulled with the site. kind "public_record", status "ok".
A code a key lacks is a gap with a reason, never a guess. The raw code is always kept.
"""

from __future__ import annotations

from datetime import date

from checklist.record_dates import parse_record_date, split_by_cutoff
from manual_imports.load_imports import IMPORTS_DIR, ManualImport, ManualImportError, decode, load_all
from manual_imports.sources import SOURCES

CATEGORIES = "dob_complaint_categories"
DISPOSITIONS = "dob_complaint_dispositions"


def category_key(root=IMPORTS_DIR) -> tuple[ManualImport | None, dict]:
    """The newest import of DOB's category list, and a description of it for the output."""
    try:
        imports = load_all(root, source_key=CATEGORIES)
    except ManualImportError as error:
        return None, {"kind": "manual_import", "status": "error", "reason": str(error)}
    if not imports:
        return None, {"kind": "manual_import", "status": "missing", "reason": "DOB's category list is not imported"}
    imp, prov = imports[0], imports[0].provenance
    return imp, {"kind": "manual_import", "status": imp.status, "name": SOURCES[CATEGORIES]["name"],
                 "import_id": imp.import_id, "source_url": prov["source_url"], "landing_url": prov.get("landing_url"),
                 "document_date": prov.get("document_date"), "document_date_note": prov.get("document_date_note"),
                 "codes": len(imp.facts)}


def disposition_key(pull: dict) -> tuple[dict[str, str] | None, dict]:
    table = (pull.get("reference_tables") or {}).get(DISPOSITIONS)
    if not table:
        return None, {"kind": "public_record", "status": "not_pulled", "reason": "the pull has no disposition table"}
    if table.get("status") != "ok":
        return None, {"kind": "public_record", "status": table.get("status", "error"), "reason": table.get("error")}
    codes = {str(r.get("code") or "").strip(): r.get("disposition") for r in table.get("records", []) if r.get("code")}
    return codes, {"kind": "public_record", "status": "ok", "name": table.get("name"),
                   "dataset_id": table.get("dataset_id"), "url": f"https://data.cityofnewyork.us/d/{table.get('dataset_id')}",
                   "rows_updated_at": table.get("rows_updated_at"), "codes": len(codes)}


def _category(raw, imp: ManualImport | None) -> dict:
    code = str(raw or "").strip()
    if not code:
        return {"code": None, "status": "not_recorded"}
    if imp is None:
        return {"code": code, "kind": "manual_import", "key": CATEGORIES, "status": "key_unavailable"}
    found = decode(code, imp)
    entry = {"code": code, "kind": "manual_import", "key": CATEGORIES, "status": found["status"],
             "description": found["description"]}
    if found["status"] == "not_in_key":
        return {**entry, "reason": found["reason"]}
    return {**entry, "priority": found.get("priority"), "page": found.get("page")}


def _disposition(record: dict, table: dict[str, str] | None, cutoff: date | None) -> dict:
    code = str(record.get("disposition_code") or "").strip()
    raw_date = record.get("disposition_date")
    if not code:
        return {"code": None, "status": "not_recorded"}
    if cutoff is not None:
        when = parse_record_date(raw_date)
        if when is None:
            return {"code": None, "status": "undated", "note": "withheld: can't tell if it was before the as-of date"}
        if when >= cutoff:
            return {"code": None, "status": "after_cutoff", "note": "disposed on or after the as-of date"}
    entry = {"code": code, "date": raw_date, "kind": "public_record", "key": DISPOSITIONS}
    if table is None:
        return {**entry, "status": "key_unavailable"}
    if code not in table:
        return {**entry, "status": "not_in_table", "description": None,
                "reason": f"code {code!r} is not in Open Data 6v9u-ndjg, which may be older than the code"}
    return {**entry, "status": "ok", "description": table[code]}


def lot_complaints(lot: dict, cutoff: date | None, imp: ManualImport | None, table: dict[str, str] | None) -> dict:
    """The lot's DOB complaints dated before the cutoff, newest first, with both codes decoded."""
    result = lot["datasets"].get("dob_complaints") or {}
    if result.get("status") != "ok":
        return {"status": result.get("status", "missing"), "reason": result.get("error") or result.get("reason"),
                "records": []}
    before = split_by_cutoff("dob_complaints", result.get("records", []), cutoff)["before"]
    before = sorted(before, key=lambda r: parse_record_date(r.get("date_entered")) or date.min, reverse=True)
    return {"status": "ok", "records": [
        {"ref": f"dob_complaints:{r.get('complaint_number')}", "complaint_number": r.get("complaint_number"),
         "date_entered": r.get("date_entered"), "status_at_pull": r.get("status"),
         "category": _category(r.get("complaint_category"), imp), "disposition": _disposition(r, table, cutoff)}
        for r in before]}


def codes_not_found(contexts: list[dict]) -> dict[str, list[str]]:
    """Every code a key lacked, per key, so the gap is visible in one place."""
    missing: dict[str, set[str]] = {CATEGORIES: set(), DISPOSITIONS: set()}
    for ctx in contexts:
        for record in ctx["complaints"]["records"]:
            if record["category"]["status"] == "not_in_key":
                missing[CATEGORIES].add(record["category"]["code"])
            if record["disposition"]["status"] == "not_in_table":
                missing[DISPOSITIONS].add(record["disposition"]["code"])
    return {key: sorted(codes) for key, codes in missing.items()}
