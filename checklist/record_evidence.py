"""Public records RELATED to a row: shown beside it, never counted as its proof.

Two kinds, both transcribed as recorded:
- site filings: excavation work-type flags, or a status that names an inspector;
- violations on the site or a touching lot whose own text cites a code section.
"""

from __future__ import annotations

import re
from datetime import date

from checklist.checklist_rules import EXCAVATION_FLAGS
from checklist.record_dates import parse_record_date, record_date, split_by_cutoff

# "BC 3301.2" or a dotted section like "3309.4" or "1705.25.4". A bare 4-digit number is not a
# citation: house numbers ("1730 Broadway") would match.
_CITATION = re.compile(r"\bBC\s*((?:33|17)\d\d(?:\.\d+)*)|(?<![\d.-])((?:33|17)\d\d(?:\.\d+)+)")
_CITATION_FIELDS = {
    "dob_violations": ("description", "violation_type"),
    "ecb_violations": ("section_law_description1", "violation_description"),
    "dob_safety_violations": ("violation_remarks", "violation_type"),
}
_ID_FIELDS = {"dob_violations": "isn_dob_bis_viol", "ecb_violations": "ecb_violation_number",
              "dob_safety_violations": "violation_number"}


def cited_sections(text: str) -> list[str]:
    return sorted({(m.group(1) or m.group(2)).rstrip(".") for m in _CITATION.finditer(text or "")})


def code_citations(lots: list[dict], cutoff: date | None) -> list[dict]:
    citations = []
    for lot in lots:
        for key, fields in _CITATION_FIELDS.items():
            result = lot["datasets"].get(key) or {}
            for record in split_by_cutoff(key, result.get("records", []), cutoff)["before"]:
                text = " ".join(" ".join(str(record.get(f) or "").split()) for f in fields)
                for section in cited_sections(text):
                    citations.append({"lot_bbl": lot["bbl"], "lot_role": lot.get("role"), "dataset": key,
                                      "record_id": record.get(_ID_FIELDS[key]),
                                      "date": str(record_date(key, record) or ""), "cited": section,
                                      "text": text[:240]})
    return citations


def citations_for_row(section: str, citations: list[dict]) -> list[dict]:
    return [c for c in citations if c["cited"] == section or c["cited"].startswith(section + ".")]


def related_filings(kind: str, site_filings: dict, cutoff: date | None) -> dict:
    if not kind:
        return {"status": "not_applicable", "records": []}
    if site_filings.get("status") != "ok":
        return {"status": "unavailable", "reason": "the DOB NOW filings query failed", "records": []}
    found = []
    for record in split_by_cutoff("dob_now_filings", site_filings.get("records", []), cutoff)["before"]:
        flags = {flag: record.get(flag) for flag in EXCAVATION_FLAGS}
        if kind == "excavation_flags":
            relevant = any(str(v or "").strip().lower() in ("yes", "y", "true") for v in flags.values())
        else:
            relevant = "INSPECTOR" in str(record.get("filing_status") or "").upper()
        if not relevant:
            continue
        status_date = parse_record_date(record.get("current_status_date"))
        found.append({
            "job_filing_number": record.get("job_filing_number"), "filing_date": record.get("filing_date"),
            "filing_status": record.get("filing_status"), "current_status_date": record.get("current_status_date"),
            "status_is_after_cutoff": bool(cutoff and status_date and status_date >= cutoff),
            **flags,
        })
    return {"status": "ok", "records": found}
