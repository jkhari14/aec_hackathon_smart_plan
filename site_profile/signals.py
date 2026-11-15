"""Record signals for a site: what its own records, and its touching lots' structural complaints, say.

A signal is a fact with its record, never a score. Rules:
- Only records dated before the as-of day count; an undated record is left out when there is an as-of.
- Housing (HPD) violations are never turned into signals, and 311 requests are not added to DOB
  complaints (they can be the same complaint).
- Severity follows the shared scale: a complaint is 0 (signal), a violation or stop-work mention is 1
  (enforcement). Severity 2 and 3 come from incident records, not from violation text.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from checklist.record_dates import parse_record_date, record_date

# DOB complaint categories that point at structural or ground movement (from DOB's printed category key).
STRUCTURAL_COMPLAINTS = {
    "03": ("structural", "Adjacent building not protected"),
    "14": ("geotech", "Excavation undermining an adjacent building"),
    "16": ("geotech", "Inadequate support or shoring"),
    "30": ("structural", "Building shaking or structural stability affected"),
    "54": ("structural", "Wall or retaining wall bulging or cracked"),
    "2K": ("structural", "Structurally compromised building"),
    "5C": ("structural", "Structural stability affected by a new building under construction"),
}

# Violation text -> (hazard, title). The first pattern that matches a record wins.
VIOLATION_PATTERNS = [
    (r"COLLAPSE", "structural", "Violation mentions a collapse"),
    (r"ADJ(ACENT|OINING)[^.]{0,60}PROTECT|PROTECT[^.]{0,60}ADJ(ACENT|OINING)",
     "structural", "Protection for adjacent property not provided"),
    (r"UNDERPIN|SHORING|BRAC(E|ING)|SUPPORT OF EXCAVATION|SOE\b", "geotech", "Shoring, bracing or underpinning issue"),
    (r"EXCAVAT", "geotech", "Excavation issue"),
    (r"STRUCTURAL|UNSAFE|CRACK|BULG|LEANING", "structural", "Structural condition cited"),
    (r"CONTINU\w*[^.]{0,40}STOP\s*-?\s*WORK|STOP\s*-?\s*WORK[^.]{0,80}CONTINU|CONTRARY TO[^.]{0,30}STOP",
     "construction_safety", "Work continued during a stop-work order"),
    (r"STOP\s*-?\s*WORK|28-207\.2", "construction_safety", "Stop-work order mentioned"),
    (r"SAFEGUARD|OVERHEAD PROTECTION|SIDEWALK SHED|FENCE", "construction_safety", "Site safeguarding cited"),
    (r"FACADE|PARAPET|FALLING", "facade", "Facade or falling-debris condition cited"),
]
_COMPILED = [(re.compile(p), h, t) for p, h, t in VIOLATION_PATTERNS]

# dataset key: (display name, id field, text fields)
VIOLATION_SETS = {
    "ecb_violations": ("DOB ECB Violations", "ecb_violation_number", ("violation_description", "section_law_description1")),
    "dob_violations": ("DOB Violations", "isn_dob_bis_viol", ("description", "disposition_comments", "violation_type")),
    "dob_safety_violations": ("DOB Safety Violations", "violation_number", ("violation_remarks", "violation_type")),
}

_EXPLAIN_CHARS = 220


def _before(when: Optional[date], cutoff: Optional[date]) -> bool:
    return cutoff is None or (when is not None and when < cutoff)


def _text(record: dict, fields: tuple[str, ...]) -> str:
    return " ".join(" ".join(str(record.get(f) or "").split()) for f in fields).strip()


def violation_signals(lot: dict, cutoff: Optional[date]) -> list[dict]:
    out = []
    for key, (name, id_field, fields) in VIOLATION_SETS.items():
        result = lot["datasets"].get(key) or {}
        if result.get("status") != "ok":
            continue
        for record in result.get("records", []):
            when = record_date(key, record)
            if not _before(when, cutoff):
                continue
            text = _text(record, fields).upper()
            match = next(((h, t) for rx, h, t in _COMPILED if rx.search(text)), None)
            if not match:
                continue
            hazard, title = match
            record_id = str(record.get(id_field) or "")
            excerpt = _text(record, fields)[:_EXPLAIN_CHARS]
            out.append({
                "id": f"sig-{key}-{record_id}",
                "hazard": hazard,
                "severity": 1,
                "title": title,
                "explanation": f"The {name} record says: \"{excerpt}\"",
                "record_ids": [f"{key}:{record_id}"],
                "source_name": name,
                "date": when.isoformat() if when else None,
            })
    return out


def complaint_signals(lot: dict, cutoff: Optional[date], where: str = "") -> list[dict]:
    result = lot["datasets"].get("dob_complaints") or {}
    if result.get("status") != "ok":
        return []
    out = []
    for record in result.get("records", []):
        code = str(record.get("complaint_category") or "").strip().upper()
        if code not in STRUCTURAL_COMPLAINTS:
            continue
        when = parse_record_date(record.get("date_entered"))
        if not _before(when, cutoff):
            continue
        hazard, title = STRUCTURAL_COMPLAINTS[code]
        number = str(record.get("complaint_number") or "")
        status = str(record.get("status") or "not stated").lower()
        out.append({
            "id": f"sig-dob_complaints-{number}",
            "hazard": hazard,
            "severity": 0,
            "title": f"{title}{where}",
            "explanation": (f"DOB complaint {number}, category {code}, entered {record.get('date_entered')}; "
                            f"status {status} when pulled. A complaint is a report, not a finding."),
            "record_ids": [f"dob_complaints:{number}"],
            "source_name": "DOB Complaints Received",
            "date": when.isoformat() if when else None,
        })
    return out


def site_signals(site: dict, touching: list[dict], cutoff: Optional[date]) -> list[dict]:
    """The site's own violation and complaint signals, plus structural complaints on touching lots.
    Life-safety order: highest severity first, then newest."""
    signals = violation_signals(site, cutoff) + complaint_signals(site, cutoff)
    for lot in touching:
        address = ((lot["datasets"].get("pluto") or {}).get("records") or [{}])[0].get("address")
        signals += complaint_signals(lot, cutoff, f" (touching lot {address or lot['bbl']})")
    seen, unique = set(), []
    for signal in signals:
        if signal["id"] not in seen:
            seen.add(signal["id"])
            unique.append(signal)
    unique.sort(key=lambda s: s["date"] or "", reverse=True)
    unique.sort(key=lambda s: s["severity"], reverse=True)
    return unique
