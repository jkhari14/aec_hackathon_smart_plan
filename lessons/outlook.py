"""What could go wrong here, for every option.

Each failure mode in data/cases/lessons.json becomes a lesson for the site: the past incidents in that mode,
closest to this site first (site_profile.similarity), what prevents it (checklist items), and what this lot's
own records already show. Lessons are ranked worst incident first, then by how many incidents. No blame: a
lesson says what happened on similar projects, with causes only as reported.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from actions.site_context import _MOVEMENT, _SUPPORT, records_line
from checklist.checklist_rules import RULES as CODE_RULES
from site_profile.similarity import compare, load_cases

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "data" / "cases" / "lessons.json"
RULES = ROOT / "actions" / "rules.json"
SHOWN = 3

# This lot's own record signals that bear on a failure mode.
HERE = {
    "neighbor_undermined": _MOVEMENT,
    "excavation_support_failed": _SUPPORT,
    "deteriorated_building": ("Structural condition cited", "Structurally compromised building",
                              "Wall or retaining wall bulging or cracked", "Violation mentions a collapse"),
    "bearing_element_removed": ("Structural condition cited", "Shoring, bracing or underpinning issue"),
    "facade_falling": ("Facade or falling-debris condition cited", "Site safeguarding cited"),
    "site_safety_lapse": ("Scaffold or material handling cited", "Site safeguarding cited", "Pedestrian walkway not kept safe",
                          "Unsafe site condition cited"),
}


@lru_cache(maxsize=1)
def _data() -> tuple[dict, dict]:
    lessons = json.loads(LESSONS.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    items = {f"checklist:{r.id}": (r.title, f"2022 NYC BC {r.section}") for r in CODE_RULES}
    items.update({f"actions:{r['id']}": (r["title"], r.get("code_ref")) for r in rules["hazard_rules"]})
    items.update({f"lesson:{r['id']}": (r["title"], r.get("code_ref")) for r in rules["lesson_rules"]})
    return lessons, items


def site_outlook(profile: dict, cases: Optional[list[dict]] = None) -> dict:
    lessons, items = _data()
    cases = cases if cases is not None else load_cases()[0]
    by_id = {c["id"]: c for c in cases}
    out = []
    for mode_id, mode in lessons["failure_modes"].items():
        tagged = [(by_id[cid], tag["basis"]) for cid, tag in lessons["cases"].items()
                  if mode_id in tag["modes"] and cid in by_id]
        if not tagged:
            continue
        ranked = sorted(tagged, key=lambda cb: (-compare(profile, cb[0])["score"], -cb[0]["severity"], cb[0]["id"]))
        out.append({
            "id": mode_id,
            "label": mode["label"],
            "hazard": mode["hazard"],
            "options": mode["options"],
            "scopes": mode["scopes"],
            "case_count": len(tagged),
            "cases": [{"case_id": c["id"], "title": c["title"], "address": c["address"], "date": c["date"],
                       "severity": c["severity"], "basis": basis} for c, basis in ranked[:SHOWN]],
            "prevent_with": [{"source_rule": rid, "title": items[rid][0], "code_ref": items[rid][1]}
                             for rid in mode["prevent_with"]],
            "here": records_line(HERE.get(mode_id, ()), profile),
        })
    out.sort(key=lambda l: (-max(c["severity"] for c in l["cases"]), l["here"] is None, -l["case_count"], l["id"]))
    return {"bbl": profile["bbl"], "lessons": out}
