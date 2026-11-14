"""A row's proof: what the team supplied, and documents a public source reports but nobody read.

Three statuses, and none of them is "verified":
- provided_unverified: the project team listed a document; nobody checked it.
- reported_not_read: a public source (news, a portal link) reports one; nobody here has read it.
- not_provided: neither.
A lead never closes a gap. Leads live in data/leads/<site>.json.
"""

from __future__ import annotations

from datetime import date

from checklist.record_dates import parse_record_date

_LEAD_KEYS = {"reported_by", "url", "reported_on", "document", "document_url", "document_date", "checked"}


def load_leads(raw: dict, sections: set[str], cutoff: date | None) -> dict[str, list[dict]]:
    """Validate a leads file. In an as-of view, keep only leads whose document is dated before the cutoff."""
    by_section = (raw or {}).get("leads") or {}
    kept: dict[str, list[dict]] = {}
    for section, leads in by_section.items():
        if section not in sections:
            raise ValueError(f"lead for an unknown section: {section}")
        for lead in leads:
            if set(lead) - _LEAD_KEYS or not lead.get("reported_by") or not lead.get("document"):
                raise ValueError(f"lead for {section} needs reported_by and document, and only {sorted(_LEAD_KEYS)}")
            for key in ("url", "document_url"):
                if key in lead and not str(lead[key]).startswith("https://"):
                    raise ValueError(f"lead {key} must be an https URL")
            when = parse_record_date(lead.get("document_date"))
            if cutoff is None or (when is not None and when < cutoff):
                kept.setdefault(section, []).append(dict(lead))
    return kept


def row_proof(section: str, inputs: dict, leads: dict[str, list[dict]]) -> dict:
    provided = (inputs.get("provided_proof") or {}).get(section)
    reported = leads.get(section, [])
    if provided:
        return {"status": "provided_unverified", "document": provided.get("document"),
                "provided_by": provided.get("provided_by"), "leads": reported,
                "note": "Supplied by the project team; not verified."}
    if reported:
        return {"status": "reported_not_read", "leads": reported,
                "note": "A public source reports this document; nobody here has read it. A lead, not proof."}
    return {"status": "not_provided", "leads": [],
            "note": "Public data does not hold this document; the responsible party provides it."}
