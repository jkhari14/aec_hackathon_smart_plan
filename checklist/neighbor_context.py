"""What the public record says about one lot: facts and counts, never a risk score.

Counts are of records dated before the cutoff, by each record's status AT PULL TIME. A
dataset that failed to load reports its status instead of a zero.
"""

from __future__ import annotations

import re
from datetime import date

from checklist.record_dates import parse_record_date, split_by_cutoff

# dataset: (status field, open pattern, closed pattern), each checked as a whole word.
_STATUS_RULES = {
    "dob_violations": ("violation_category", r"ACTIVE", r"DISMISSED|RESOLVED"),
    "ecb_violations": ("ecb_violation_status", r"ACTIVE", r"RESOLVE"),
    "dob_safety_violations": ("violation_status", r"ACTIVE", r"DISMISSED"),
    "hpd_violations": ("violationstatus", r"OPEN", r"CLOSE"),
    "dob_complaints": ("status", r"ACTIVE", r"CLOSED"),
}


def classify(dataset_key: str, record: dict) -> str:
    field, open_pattern, closed_pattern = _STATUS_RULES[dataset_key]
    text = str(record.get(field) or "").upper()
    if re.search(rf"\b({open_pattern})\b", text):
        return "open"
    if re.search(rf"\b({closed_pattern})\b", text):
        return "closed"
    return "not_stated"


def count_statuses(dataset_key: str, result: dict, cutoff: date | None) -> dict:
    if result.get("status") != "ok":
        return {"status": result.get("status", "missing"), "reason": result.get("error") or result.get("reason")}
    split = split_by_cutoff(dataset_key, result.get("records", []), cutoff)
    counts = {"open": 0, "closed": 0, "not_stated": 0}
    for record in split["before"]:
        counts[classify(dataset_key, record)] += 1
    return {"status": "ok", **counts, "dated_on_or_after_cutoff": len(split["on_or_after"]),
            "undated": len(split["undated"]), "truncated": bool(result.get("truncated"))}


def _pluto(lot: dict) -> tuple[str, dict]:
    result = lot["datasets"].get("pluto") or {}
    if result.get("status") != "ok":
        return "error", {}
    records = result.get("records") or []
    return ("ok", records[0]) if records else ("no_record", {})


def building_presence(lot: dict) -> dict:
    """Is there a building on the lot? Both sources can lag a demolition or a collapse."""
    footprints = lot.get("footprint_buildings") or {}
    pluto_status, pluto = _pluto(lot)
    if footprints.get("status") == "ok" and footprints.get("count", 0) > 0:
        return {"status": "yes", "basis": f"{footprints['count']} building footprint(s)"}
    try:
        buildings = int(float(pluto.get("numbldgs") or 0))
    except ValueError:
        buildings = 0
    if pluto_status == "ok" and buildings > 0:
        return {"status": "yes", "basis": f"PLUTO lists {buildings} building(s)"}
    if footprints.get("status") == "ok" and pluto_status in ("ok", "no_record"):
        return {"status": "no", "basis": "no footprint and no building in PLUTO"}
    return {"status": "unknown", "basis": "the footprint or PLUTO query failed"}


def lot_context(lot: dict, cutoff: date | None) -> dict:
    pluto_status, pluto = _pluto(lot)
    mentions = [m for m in lot.get("stop_work_mentions", [])
                if cutoff is None or ((d := parse_record_date(m.get("issue_date"))) is not None and d < cutoff)]
    return {
        "bbl": lot["bbl"],
        "role": lot.get("role"),
        "address": pluto.get("address"),
        "pluto_status": pluto_status,
        "year_built": pluto.get("yearbuilt"),
        "floors": pluto.get("numfloors"),
        "residential_units": pluto.get("unitsres"),
        "building_class": pluto.get("bldgclass"),
        "building_presence": building_presence(lot),
        "counts": {key: count_statuses(key, lot["datasets"].get(key) or {}, cutoff) for key in _STATUS_RULES},
        "stop_work_mentions": mentions,
    }
