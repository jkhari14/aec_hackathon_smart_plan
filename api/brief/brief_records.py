"""data_pull's per-dataset rows -> uniform PublicRecord entries (id, date, status today, summary)."""

import re
from typing import Optional

from api.brief.brief_models import PublicRecord

_SUMMARY_CHARS = 300


def iso_date(raw: Optional[str]) -> Optional[str]:
    """'20261111', '2026-06-03T22:32:02.000' and '11/13/2026' -> '2026-11-11'; anything else -> None."""
    if not raw:
        return None
    raw = raw.strip()
    if re.fullmatch(r"\d{8}", raw, re.ASCII):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    if re.match(r"\d{4}-\d{2}-\d{2}", raw, re.ASCII):
        return raw[:10]
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", raw, re.ASCII)
    if match:
        return f"{match[3]}-{match[1]}-{match[2]}"
    return None


def _clip(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1] + "…"


# dataset key -> (record id field, date field, status field, summary builder)
_FIELDS = {
    "dob_now_filings": (
        "job_filing_number",
        "filing_date",
        "filing_status",
        lambda r: f"{r.get('job_type', '')} filing. Earth work: {r.get('earth_work_work_type_', '?')}. "
        f"Approved: {iso_date(r.get('approved_date')) or 'no'}. {r.get('job_description', '')}",
    ),
    "dob_violations": (
        "isn_dob_bis_viol",
        "issue_date",
        "violation_category",
        lambda r: f"{r.get('violation_type', '')} {r.get('description', '')}",
    ),
    "ecb_violations": (
        "ecb_violation_number",
        "issue_date",
        "ecb_violation_status",
        lambda r: f"{r.get('section_law_description1', '')}. {r.get('violation_description', '')}",
    ),
    "dob_safety_violations": (
        "violation_number",
        "violation_issue_date",
        "violation_status",
        lambda r: f"{r.get('violation_type', '')} ({r.get('device_type') or 'no device type'})",
    ),
    "hpd_violations": (
        "violationid",
        "inspectiondate",
        "violationstatus",
        lambda r: f"Class {r.get('class', '?')}. {r.get('novdescription', '')}",
    ),
    "dob_complaints": (
        "complaint_number",
        "date_entered",
        "status",
        lambda r: f"Complaint category code {r.get('complaint_category', '?')} (DOB publishes the key separately).",
    ),
}


def lot_records(lot: dict, sources: dict) -> list[PublicRecord]:
    """Every counted record on one lot. Rows data_pull held back (another lot's) are left out."""
    stop_work = {(m["dataset"], m["record_id"]) for m in lot.get("stop_work_mentions") or []}
    records = []
    for key, (id_field, date_field, status_field, summarize) in _FIELDS.items():
        pulled = lot["datasets"].get(key) or {}
        if pulled.get("status") != "ok":
            continue
        for row in pulled.get("records") or []:
            record_id = str(row.get(id_field) or "").strip()
            if not record_id:
                continue
            records.append(
                PublicRecord(
                    id=f"{key}:{record_id}",
                    dataset_key=key,
                    dataset_name=sources.get(key, {}).get("name", key),
                    record_id=record_id,
                    bbl=lot["bbl"],
                    date=iso_date(row.get(date_field)),
                    status_today=(row.get(status_field) or None),
                    summary=_clip(summarize(row)),
                    query_url=pulled.get("query_url"),
                    mentions_stop_work=(key, record_id) in stop_work,
                )
            )
    return records
