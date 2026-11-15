"""When each checklist item is due: a phase on the project timeline and a short "when" line.

Where the code states timing (notice 60 days before work, survey before excavation, monitoring during it), the
phase follows the code text in checklist/checklist_rules.py. Hazard rules use the earliest stage they apply in.
Document rules (a confirmed drawing or geotech report) are placed by what they ask for. Anything unknown is Design.
"""

from __future__ import annotations

from typing import Optional

PHASES = ("design", "filing", "notice", "before_excavation", "during_work")

# Code rows (source_rule "checklist:<id>"): from the timing in the code text.
_CODE = {
    "notice": ("notice", "60 days before work"),
    "license": ("notice", "Before work starts"),
    "examination": ("before_excavation", "Before work, then during"),
    "survey": ("before_excavation", "Before excavation"),
    "support_drawings": ("filing", "Before filing"),
    "support_basis": ("filing", "Before filing"),
    "underpinning": ("filing", "Before filing"),
    "monitoring": ("during_work", "During excavation"),
    "foundation_protection": ("during_work", "During work"),
    "exposed_wall": ("during_work", "During work"),
    "underpinning_inspection": ("during_work", "During work"),
    "hazard_elevations": ("during_work", "During work"),
}

# Document rows (source_rule "actions:model:<id>" or "actions:geotech:<id>").
_DOCUMENT = {
    "lot-line-underpin": ("filing", "Before filing"),
    "lot-line-notice": ("notice", "60 days before work"),
    "lot-line-examination": ("before_excavation", "Before work, then during"),
    "support-basis": ("filing", "Before filing"),
    "dewatering": ("filing", "Before filing"),
    "rock": ("filing", "Before filing"),
    "monitoring": ("during_work", "During excavation"),
}

# Hazard rows: the earliest stage the rule applies in.
_STAGE = {
    "pre_acquisition": ("design", "During design"),
    "design": ("design", "During design"),
    "pre_filing": ("filing", "Before filing"),
    "construction": ("during_work", "During work"),
}
_STAGE_ORDER = ("pre_acquisition", "design", "pre_filing", "construction")

_DEFAULT = ("design", "During design")


def phase_for(source_rule: str, stages: Optional[list[str]] = None) -> tuple[str, str]:
    """(phase, when) for an item, from its source rule and, for hazard rules, the stages it applies in."""
    kind, _, rest = source_rule.partition(":")
    if kind == "checklist":
        return _CODE.get(rest, _DEFAULT)
    if kind == "actions":
        sub, _, rule_id = rest.partition(":")
        if sub in ("model", "geotech") and rule_id:
            return _DOCUMENT.get(rule_id, _DEFAULT)
    for stage in _STAGE_ORDER:
        if stages and stage in stages:
            return _STAGE[stage]
    return _DEFAULT
