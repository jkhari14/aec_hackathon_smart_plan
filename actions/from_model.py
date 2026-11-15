"""Turn a confirmed document reading (a structural model, a geotechnical report) into checklist items for the
roles it concerns.

A team member uploads a drawing, checks the AI's reading and confirms it; the project's checklist then
changes for everyone it concerns. Each rule in `rules.json` ("model_rules") has a condition on the
model, an owner role and the item's text. Every item says which document brought it in and who
confirmed it (`added_reason`); the project store adds the time.

Nothing here marks an item done: a drawing shows a condition, never that the work was carried out.
A model the team has not confirmed must not reach this function.
"""

from __future__ import annotations

import json
import pathlib
from typing import Optional

from actions.phases import phase_for

RULES_PATH = pathlib.Path(__file__).with_name("rules.json")

ROLE_WORDS = {"architect": "architect", "structural_engineer": "structural engineer",
              "developer": "developer", "contractor": "contractor"}


def _rules(key: str = "model_rules") -> list[dict]:
    with RULES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)[key]


def _wall(wall: dict) -> str:
    parts = [wall.get("side") if wall.get("side") not in (None, "unknown") else "side not given"]
    if wall.get("material"):
        parts.append(str(wall["material"]))
    if wall.get("length_ft"):
        parts.append(f"{wall['length_ft']:g} ft")
    return ", ".join(parts)


def _blank(value: Optional[str]) -> bool:
    return value is None or not str(value).strip()


def evaluate(condition: str, model: dict) -> Optional[str]:
    """The finding that makes a rule apply, in a few words, or None when it does not apply."""
    walls = model.get("bearing_walls_on_lot_line") or []
    if condition == "bearing_walls_on_lot_line":
        if not walls:
            return None
        noun = "bearing wall" if len(walls) == 1 else f"{len(walls)} bearing walls"
        return f"{noun} on the lot line ({'; '.join(_wall(w) for w in walls)})"
    if condition == "unreinforced_masonry":
        material = str(model.get("material") or "")
        return f"material: {material}" if "unreinforced" in material.lower() else None
    if condition == "lateral_system_not_shown":
        return "no lateral system shown" if _blank(model.get("lateral_system")) else None
    if condition == "foundation_not_shown":
        return "no foundation shown" if _blank(model.get("foundation_type")) else None
    raise ValueError(f"unknown model condition: {condition}")


def document_label(document: str) -> str:
    """'S-101.pdf' -> 'S-101'."""
    name = document.strip().rsplit("/", 1)[-1]
    return name[:-4] if name.lower().endswith(".pdf") else name


def model_actions(model: dict, document: str, by_role: str) -> list[dict]:
    """ActionItem dicts, each with `added_reason` (and `flagged_reason`, for an item the project already has),
    for a model `by_role` confirmed from `document`.

    An item with the id of a checklist row (`item_id`) flags that row when the project already has it;
    the store decides, since only it knows what the project holds.
    """
    return _items(_rules("model_rules"), lambda condition: evaluate(condition, model), document, by_role, "model")


def _ft(value: float) -> str:
    return f"{value:g} ft"


def evaluate_geotech(condition: str, findings: dict) -> Optional[str]:
    """The finding that makes a geotech rule apply, in a few words, or None. A null finding never applies."""
    water, bearing, rock = findings.get("groundwater_depth_ft"), findings.get("allowable_bearing_tsf"), findings.get("rock_depth_ft")
    soil = str(findings.get("soil_description") or "")
    if condition == "report_received":
        return f"soil: {soil}" if soil.strip() else "a site-specific report is now on the project"
    if condition == "groundwater_within_15ft":
        return f"groundwater at {_ft(water)} below grade" if water is not None and water <= 15 else None
    if condition == "bearing_below_3tsf":
        return f"allowable bearing {bearing:g} tsf" if bearing is not None and bearing < 3 else None
    if condition == "fill_or_soft_soil":
        words = ("fill", "organic", "peat", "soft", "loose")
        return f"soil: {soil}" if any(w in soil.lower() for w in words) else None
    if condition == "rock_within_20ft":
        return f"rock at {_ft(rock)} below grade" if rock is not None and rock <= 20 else None
    raise ValueError(f"unknown geotech condition: {condition}")


def geotech_actions(findings: dict, document: str, by_role: str) -> list[dict]:
    """ActionItem dicts for a geotechnical report `by_role` confirmed from `document` (same shape as model_actions)."""
    return _items(_rules("geotech_rules"), lambda condition: evaluate_geotech(condition, findings), document, by_role,
                  "geotech")


def _items(rules: list[dict], finding_for, document: str, by_role: str, kind: str) -> list[dict]:
    if by_role not in ROLE_WORDS:
        raise ValueError(f"unknown role: {by_role}")
    who, doc = ROLE_WORDS[by_role], document_label(document)
    items = []
    for rule in rules:
        finding = finding_for(rule["condition"])
        if finding is None:
            continue
        items.append({
            "id": rule["item_id"] or f"action-{kind}-{rule['id']}",
            "discipline": rule["discipline"],
            "hazard": rule["hazard"],
            "title": rule["title"],
            "why": rule["why"],
            "code_ref": rule["code_ref"],
            "proof_needed": rule["proof_needed"],
            "status": "open",
            "owner_role": rule["owner_role"],
            "source_rule": f"actions:{kind}:{rule['id']}",
            "life_safety": rule["life_safety"],
            **dict(zip(("phase", "when"), phase_for(f"actions:{kind}:{rule['id']}"))),
            "added_reason": f"Added because the {who} uploaded {doc} and confirmed its reading: {finding}.",
            # Used instead when the project already has this item: it was there, the document flags it.
            "flagged_reason": f"Flagged because the {who} uploaded {doc} and confirmed its reading: {finding}.",
        })
    return items
