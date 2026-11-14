"""Records whose own text mentions a stop-work order.

We have not found stop-work orders published as their own dataset, so this transcribes
what violation records and 311 resolutions SAY. It is not a complete list of stop-work orders, and it infers
nothing: every mention carries the record it came from.
"""

from __future__ import annotations

import re

# 28-207.2.x is the Administrative Code section on stop-work orders.
_MENTION = re.compile(r"STOP\s*-?\s*WORK|28-207\.2", re.IGNORECASE)
_TEXT_FIELDS = {
    "dob_violations": ("description", "disposition_comments", "violation_type"),
    "ecb_violations": ("section_law_description1", "violation_description"),
    "dob_safety_violations": ("violation_remarks", "violation_type"),
    "dob_311_requests": ("resolution_description", "descriptor", "descriptor_2"),
}
_ID_FIELDS = {
    "dob_violations": "isn_dob_bis_viol",
    "ecb_violations": "ecb_violation_number",
    "dob_safety_violations": "violation_number",
    "dob_311_requests": "unique_key",
}
# Each dataset names its issue date differently.
_DATE_FIELDS = {"dob_safety_violations": "violation_issue_date", "dob_311_requests": "created_date"}
# A 311 resolution is written when DOB acts, after the request was created: date it by that.
_FIELD_DATES = {("dob_311_requests", "resolution_description"): "resolution_action_updated_date"}
_EXCERPT_CHARS = 240


def find_stop_work_mentions(datasets: dict) -> list[dict]:
    mentions = []
    for key, fields in _TEXT_FIELDS.items():
        result = datasets.get(key) or {}
        for record in result.get("records", []):
            for field in fields:
                text = " ".join(str(record.get(field) or "").split())
                if text and _MENTION.search(text):
                    mentions.append({
                        "dataset": key,
                        "record_id": record.get(_ID_FIELDS[key]),
                        "issue_date": record.get(_FIELD_DATES.get((key, field)) or _DATE_FIELDS.get(key, "issue_date")),
                        "field": field,
                        "text": text[:_EXCERPT_CHARS],
                    })
                    break
    # Dates come as YYYYMMDD or ISO; compare their digits so the two formats sort together.
    return sorted(mentions, key=lambda m: re.sub(r"\D", "", str(m.get("issue_date") or ""))[:8], reverse=True)
