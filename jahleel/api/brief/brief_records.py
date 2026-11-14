"""data_pull's per-dataset rows -> uniform PublicRecord entries (id, date, status today, summary)."""

import re
from typing import Optional

from jahleel.api.brief.brief_models import PublicRecord
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
        # The approval date is its own field (approved_on), so a replay can't show a later approval.
        lambda r: f"{r.get('job_type', '')} filing. Earth work: {r.get('earth_work_work_type_', '?')}. "
        f"{r.get('job_description', '')}",
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
    # Can repeat a dob_complaints row (no shared key): never add the two counts.
    "dob_311_requests": (
        "unique_key",
        "status",
        lambda r: ". ".join(t for t in (r.get("complaint_type"), r.get("descriptor"), r.get("descriptor_2")) if t),
    ),
}
# Published status values that state nothing.
_NOT_A_STATUS = {"unspecified"}
# Text written when DOB acted, later than the record's own date: (text field, date field).
_LATER_TEXT = {"dob_311_requests": ("resolution_description", "resolution_action_updated_date")}
# Approval date field, per dataset.
_APPROVED = {"dob_now_filings": "approved_date"}


def _first_stop_work_mentions(lot: dict) -> dict[tuple[str, str], Optional[str]]:
    """(dataset, record id) -> ISO date of the earliest dated stop-work mention on it; None if all undated."""
    first: dict[tuple[str, str], Optional[str]] = {}
    for mention in lot.get("stop_work_mentions") or []:
        key = (mention["dataset"], str(mention["record_id"]).strip())
        dates = [d for d in (first.get(key), iso_date(mention.get("issue_date"))) if d]
        first[key] = min(dates) if dates else None
    return first


def _status(row: dict, field: str) -> Optional[str]:
    status = str(row.get(field) or "").strip()
    return status if status and status.lower() not in _NOT_A_STATUS else None


def lot_records(lot: dict, sources: dict) -> list[PublicRecord]:
    """Every counted record on one lot. Rows data_pull held back (another lot's) are left out."""
    stop_work = _first_stop_work_mentions(lot)
    records = []
    for key, (id_field, status_field, summarize) in _FIELDS.items():
        pulled = lot["datasets"].get(key) or {}
        if pulled.get("status") != "ok":
            continue
        text_field, text_date_field = _LATER_TEXT.get(key, (None, None))
        for row in pulled.get("records") or []:
            record_id = str(row.get(id_field) or "").strip()
            if not record_id:
                continue
            when = record_date(key, row)
            later_text = _clip(row.get(text_field) or "") if text_field else ""
            records.append(
                PublicRecord(
                    id=f"{key}:{record_id}",
                    dataset_key=key,
                    dataset_name=sources.get(key, {}).get("name", key),
                    record_id=record_id,
                    bbl=lot["bbl"],
                    date=when.isoformat() if when else None,
                    status_today=_status(row, status_field),
                    summary=_clip(summarize(row)),
                    query_url=pulled.get("query_url"),
                    mentions_stop_work=(key, record_id) in stop_work,
                    stop_work_first_mentioned=stop_work.get((key, record_id)),
                    approved_on=iso_date(row.get(_APPROVED[key])) if key in _APPROVED else None,
                    resolution=later_text or None,
                    resolution_recorded=iso_date(row.get(text_date_field)) if later_text else None,
                )
            )
    return records
