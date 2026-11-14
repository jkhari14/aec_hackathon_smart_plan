"""Dates on records, for the "what was knowable before X" view.

Each dataset stores its date differently (YYYYMMDD, ISO, MM/DD/YYYY). A record whose date
cannot be read is "undated": it is never silently placed before or after a cutoff.
"""

from __future__ import annotations

from datetime import date

DATE_FIELDS = {
    "dob_now_filings": "filing_date",
    "dob_violations": "issue_date",
    "ecb_violations": "issue_date",
    "dob_safety_violations": "violation_issue_date",
    "hpd_violations": "inspectiondate",
    "dob_complaints": "date_entered",
    "dob_311_requests": "created_date",
}


def parse_record_date(raw: object) -> date | None:
    text = str(raw or "").strip()
    try:
        if len(text) == 8 and text.isdigit():
            return date(int(text[:4]), int(text[4:6]), int(text[6:]))
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return date.fromisoformat(text[:10])
        if len(text) == 10 and text[2] == "/" and text[5] == "/":
            return date(int(text[6:]), int(text[:2]), int(text[3:5]))
    except ValueError:
        return None
    return None


def record_date(dataset_key: str, record: dict) -> date | None:
    field = DATE_FIELDS.get(dataset_key)
    return parse_record_date(record.get(field)) if field else None


def split_by_cutoff(dataset_key: str, records: list[dict], cutoff: date | None) -> dict:
    """{"before": [...], "on_or_after": [...], "undated": [...]}. No cutoff: all count as before."""
    if cutoff is None:
        return {"before": list(records), "on_or_after": [], "undated": []}
    split: dict[str, list[dict]] = {"before": [], "on_or_after": [], "undated": []}
    for record in records:
        when = record_date(dataset_key, record)
        if when is None:
            split["undated"].append(record)
        elif when < cutoff:
            split["before"].append(record)
        else:
            split["on_or_after"].append(record)
    return split
