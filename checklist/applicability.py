"""Does a row apply? Decided only from the public record, the project's own inputs, or the
code's thresholds, and the answer always says which ("basis").

Statuses: applies | does_not_apply | needs_input | set_by_dob | unknown.
A project input never silently overrides the record: when they disagree, both are shown.
"""

from __future__ import annotations

from datetime import date

from checklist.checklist_rules import EXCAVATION_FLAGS
from checklist.record_dates import split_by_cutoff

_BOOL_INPUTS = ("involves_excavation", "requires_adjoining_access", "underpinning_planned",
                "exposes_adjoining_wall")


def validate_inputs(raw: dict) -> dict:
    """Project inputs typed by the team. Keys starting with "_" are notes and are ignored."""
    inputs = {k: v for k, v in (raw or {}).items() if not k.startswith("_")}
    allowed = set(_BOOL_INPUTS) | {"excavation_depth_ft", "distance_to_building_ft", "provided_proof"}
    unknown = set(inputs) - allowed
    if unknown:
        raise ValueError(f"unknown project inputs: {sorted(unknown)}")
    for key in _BOOL_INPUTS:
        if key in inputs and not isinstance(inputs[key], bool):
            raise ValueError(f"{key} must be true or false")
    depth = inputs.get("excavation_depth_ft")
    if depth is not None and (isinstance(depth, bool) or not isinstance(depth, (int, float)) or depth < 0):
        raise ValueError("excavation_depth_ft must be a number of feet, 0 or more")
    for bbl, feet in (inputs.get("distance_to_building_ft") or {}).items():
        if isinstance(feet, bool) or not isinstance(feet, (int, float)) or feet < 0:
            raise ValueError(f"distance_to_building_ft[{bbl}] must be a number of feet, 0 or more")
    return inputs


def _result(status: str, *basis: dict, needs: tuple = (), notes: tuple = ()) -> dict:
    return {"status": status, "basis": list(basis), "needs": list(needs), "notes": list(notes)}


def _user(detail: str) -> dict:
    return {"kind": "user_input", "detail": detail}


def _code(detail: str) -> dict:
    return {"kind": "code_text", "detail": detail}


def _is_yes(value: object) -> bool:
    return str(value or "").strip().lower() in ("yes", "y", "true")


def excavation_status(site_filings: dict, inputs: dict, cutoff: date | None) -> dict:
    said = inputs.get("involves_excavation")
    if site_filings.get("status") != "ok":
        note = "The DOB NOW filings query failed, so the record could not answer."
        if said is None:
            return _result("needs_input", needs=("involves_excavation",), notes=(note,))
        return _result("applies" if said else "does_not_apply", _user(f"involves_excavation: {said}"), notes=(note,))

    filed = []
    for record in split_by_cutoff("dob_now_filings", site_filings.get("records", []), cutoff)["before"]:
        if any(_is_yes(record.get(flag)) for flag in EXCAVATION_FLAGS):
            filed.append({"dataset": "dob_now_filings", "ref": f"dob_now_filings:{record.get('job_filing_number')}",
                          "job_filing_number": record.get("job_filing_number"),
                          "filing_date": record.get("filing_date"),
                          **{flag: record.get(flag) for flag in EXCAVATION_FLAGS}})
    if filed:
        basis = {"kind": "public_record", "records": filed,
                 "detail": f"{len(filed)} DOB NOW filing(s) on this lot list earth work, foundation "
                           "or support-of-excavation work"}
        notes = ("The project input says there is no excavation, but the record lists excavation "
                 "work. Shown as applies; check which is current.",) if said is False else ()
        return _result("applies", basis, notes=notes)
    none_filed = "No DOB NOW filing on this lot lists earth work, foundation or support-of-excavation work."
    if said is None:
        return _result("needs_input", needs=("involves_excavation",), notes=(none_filed,))
    return _result("applies" if said else "does_not_apply", _user(f"involves_excavation: {said}"), notes=(none_filed,))


def _from_bool(inputs: dict, key: str) -> dict:
    if key not in inputs:
        return _result("needs_input", needs=(key,))
    return _result("applies" if inputs[key] else "does_not_apply", _user(f"{key}: {inputs[key]}"))


def _survey(inputs: dict, excavation: dict, bbl: str | None) -> dict:
    if excavation["status"] != "applies":
        return excavation
    depth = inputs.get("excavation_depth_ft")
    if depth is None:
        return _result("needs_input", needs=("excavation_depth_ft",))
    if depth > 10:
        return _result("applies", _user(f"depth {depth} ft"), _code("over 10 ft deep anywhere on the site"))
    if depth < 5:
        return _result("does_not_apply", _user(f"depth {depth} ft"), _code("the survey thresholds start at 5 ft"),
                       notes=("Section 3309.4 still applies at any depth.",))
    distance = (inputs.get("distance_to_building_ft") or {}).get(bbl) if bbl else None
    if distance is None:
        return _result("needs_input", _user(f"depth {depth} ft"), needs=("distance_to_building_ft",))
    status = "applies" if distance <= 10 else "does_not_apply"
    return _result(status, _user(f"depth {depth} ft, building {distance} ft away"),
                   _code("5 to 10 ft deep within 10 ft of an adjacent building"))


def _monitoring(inputs: dict, excavation: dict, bbl: str | None) -> dict:
    if excavation["status"] != "applies":
        return excavation
    historic = "Historic structures within 90 ft also need monitoring; historic status is not checked here."
    depth = inputs.get("excavation_depth_ft")
    if depth is None:
        return _result("needs_input", needs=("excavation_depth_ft",), notes=(historic,))
    if depth <= 5:
        return _result("needs_input", _user(f"depth {depth} ft"), needs=("footing_position",),
                       notes=("At 5 ft or less, monitoring can be exempt depending on distance to footings "
                              "and whether the dig goes below them; a professional must say.", historic))
    distance = (inputs.get("distance_to_building_ft") or {}).get(bbl) if bbl else None
    if distance is None:
        return _result("needs_input", _user(f"depth {depth} ft"), needs=("distance_to_building_ft",), notes=(historic,))
    status = "applies" if distance <= depth else "does_not_apply"
    return _result(status, _user(f"depth {depth} ft, building {distance} ft from the excavation edge"),
                   _code("buildings within the excavation's maximum depth of its edge"), notes=(historic,))


def evaluate(condition: str, inputs: dict, excavation: dict, bbl: str | None = None) -> dict:
    if condition == "excavation":
        return excavation
    if condition == "adjoining_access":
        return _from_bool(inputs, "requires_adjoining_access")
    if condition == "underpinning":
        return _from_bool(inputs, "underpinning_planned")
    if condition == "exposed_wall":
        return _from_bool(inputs, "exposes_adjoining_wall")
    if condition == "survey_threshold":
        return _survey(inputs, excavation, bbl)
    if condition == "monitoring_distance":
        return _monitoring(inputs, excavation, bbl)
    if condition == "dob_decides":
        return _result("set_by_dob", _code("applies when DOB judges that a potential hazard exists"))
    raise ValueError(f"unknown condition: {condition}")
