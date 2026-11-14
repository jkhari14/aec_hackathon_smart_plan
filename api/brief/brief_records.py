"""data_pull's per-dataset rows -> uniform PublicRecord entries (id, date, status today, summary)."""

import re
from typing import Optional

from api.brief.brief_models import PublicRecord
from checklist.record_dates import parse_record_date, record_date

_SUMMARY_CHARS = 300


def iso_date(raw: Optional[str]) -> Optional[str]:
    """The checklist engine's parser, as an ISO string; None when undated (never a guess)."""
    when = parse_record_date(raw)
    return when.isoformat() if when else None


def _clip(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1] + "…"


# dataset key -> (record id field, status field, summary builder). Date fields: checklist/record_dates.py.
_FIELDS = {
    "dob_now_filings": (
        "job_filing_number",
        "filing_status",
        lambda r: f"{r.get('job_type', '')} filing. Earth work: {r.get('earth_work_work_type_', '?')}. "
        f"Approved: {iso_date(r.get('approved_date')) or 'no'}. {r.get('job_description', '')}",
    ),
    "dob_violations": (
        "isn_dob_bis_viol",
        "violation_category",
        lambda r: f"{r.get('violation_type', '')} {r.get('description', '')}",
    ),
    "ecb_violations": (
        "ecb_violation_number",
        "ecb_violation_status",
        lambda r: f"{r.get('section_law_description1', '')}. {r.get('violation_description', '')}",
    ),
    "dob_safety_violations": (
        "violation_number",
        "violation_status",
        lambda r: f"{r.get('violation_type', '')} ({r.get('device_type') or 'no device type'})",
    ),
    "hpd_violations": (
        "violationid",
        "violationstatus",
        lambda r: f"Class {r.get('class', '?')}. {r.get('novdescription', '')}",
    ),
    "dob_complaints": (
        "complaint_number",
        "status",
        lambda r: f"Complaint category code {r.get('complaint_category', '?')} (DOB publishes the key separately).",
    ),
}


def lot_records(lot: dict, sources: dict) -> list[PublicRecord]:
    """Every counted record on one lot. Rows data_pull held back (another lot's) are left out."""
    stop_work = {(m["dataset"], m["record_id"]) for m in lot.get("stop_work_mentions") or []}
    records = []
    for key, (id_field, status_field, summarize) in _FIELDS.items():
        pulled = lot["datasets"].get(key) or {}
        if pulled.get("status") != "ok":
            continue
        for row in pulled.get("records") or []:
            record_id = str(row.get(id_field) or "").strip()
            if not record_id:
                continue
            when = record_date(key, row)
            records.append(
                PublicRecord(
                    id=f"{key}:{record_id}",
                    dataset_key=key,
                    dataset_name=sources.get(key, {}).get("name", key),
                    record_id=record_id,
                    bbl=lot["bbl"],
                    date=when.isoformat() if when else None,
                    status_today=(row.get(status_field) or None),
                    summary=_clip(summarize(row)),
                    query_url=pulled.get("query_url"),
                    mentions_stop_work=(key, record_id) in stop_work,
                )
            )
    return records
