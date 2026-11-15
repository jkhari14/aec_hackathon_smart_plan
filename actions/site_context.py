"""What makes a checklist row about this lot: the neighbouring buildings it concerns, and what the public record
already says that bears on it.

Rows about the adjoining buildings (notice, access, examination, survey, monitoring, protection, underpinning,
exposed walls) list the touching lots by address, attached ones first. Rows the record speaks to carry a line
counting the matching complaints and violations with their date range. Complaints are reports, not findings,
and the line says so.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from typing import Optional

PER_BUILDING = {"notice", "license", "examination", "survey", "monitoring", "foundation_protection", "underpinning",
                "exposed_wall"}

_MOVEMENT = ("Excavation undermining an adjacent building", "Adjacent building not protected",
             "Building shaking or structural stability affected", "Inadequate support or shoring",
             "Structurally compromised building", "Wall or retaining wall bulging or cracked")
_SUPPORT = ("Inadequate support or shoring", "Shoring, bracing or underpinning issue", "Excavation issue",
            "Excavation undermining an adjacent building")

# Code row id -> the signal titles that bear on it.
EVIDENCE = {
    "notice": ("Adjacent building not protected",),
    "license": ("Adjacent building not protected",),
    "examination": _MOVEMENT,
    "survey": _MOVEMENT,
    "monitoring": _MOVEMENT,
    "foundation_protection": _MOVEMENT,
    "underpinning": _SUPPORT,
    "support_drawings": _SUPPORT,
    "support_basis": _SUPPORT,
    "hazard_elevations": ("Work continued during a stop-work order", "Building shaking or structural stability affected"),
}

_SMALL = {"of", "and", "the"}


def _address(text: Optional[str]) -> Optional[str]:
    """'19 MARCUS GARVEY BLVD' -> '19 Marcus Garvey Blvd'."""
    if not text:
        return None
    words = text.strip().split()
    return " ".join(w.lower() if w.lower() in _SMALL and i else w.capitalize() for i, w in enumerate(words))


def _neighbor_label(n: dict) -> str:
    facts = []
    if n.get("year_built"):
        facts.append(f"built {n['year_built']}")
    if n.get("floors"):
        facts.append(f"{n['floors']:g} storeys")
    if n.get("attached"):
        facts.append("attached")
    name = _address(n.get("address")) or "an unnamed lot"
    return f"{name} ({', '.join(facts)})" if facts else name


def applies_to(rule_id: str, profile: dict) -> list[str]:
    """The touching lots a neighbour row concerns, attached first; [] for rows that aren't about them."""
    if rule_id not in PER_BUILDING:
        return []
    neighbors = sorted(profile.get("neighbors") or [], key=lambda n: not n.get("attached"))
    return [_neighbor_label(n) for n in neighbors]


def _month(iso: str) -> Optional[date]:
    try:
        return date.fromisoformat(iso[:10])
    except (TypeError, ValueError):
        return None


def evidence(rule_id: str, profile: dict) -> Optional[str]:
    """'On record here: 2 'X' and 1 'Y' (DOB Complaints Received), Feb 2026–Aug 2026. ...' or None."""
    titles = EVIDENCE.get(rule_id)
    if not titles:
        return None
    matched = []
    for s in profile.get("signals") or []:
        base = re.sub(r" \(touching lot .*\)$", "", s.get("title") or "")
        if base in titles:
            matched.append((base, s))
    if not matched:
        return None
    counts = Counter(base for base, _ in matched)
    parts = [f"{n} '{title}'" for title, n in counts.most_common()]
    sources = sorted({s.get("source_name") for _, s in matched if s.get("source_name")})
    days = sorted(d for d in (_month(s.get("date") or "") for _, s in matched) if d)
    span = ""
    if days:
        first, last = days[0].strftime("%b %Y"), days[-1].strftime("%b %Y")
        span = f", {first}" if first == last else f", {first}–{last}"
    joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return (f"On record here: {joined} ({'; '.join(sources)}){span}. "
            "Complaints are reports, not findings.")
