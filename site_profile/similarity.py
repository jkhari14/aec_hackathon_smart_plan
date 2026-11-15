"""Rank past cases and open-data incidents by how much they resemble a site's profile.

The score is a weighted sum of plain features, each one a sentence a structural engineer can check:
"matches on: excavation next to an attached building built before 1940". A feature the case does not
report counts as no match and is not listed as a difference, because "not reported" is not "different".
The score says how alike two sites look on paper, nothing about what will happen.

Weights (Hongyu reviews these, see BUILD.md):
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from api.contracts import Case, SimilarCases
from site_profile.work_types import EARTH_WORK

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_LIBRARY = REPO_ROOT / "data" / "cases" / "cases.json"
CASE_FIXTURE = REPO_ROOT / "contracts" / "fixtures" / "cases.json"
LAYERS_DIR = REPO_ROOT / "data" / "layers"
INCIDENT_LAYERS = ("construction_incidents",)

OLD_NEIGHBOR_YEAR = 1940  # pre-war masonry era; the plan's "attached pre-1940" watch rule

WEIGHTS = {
    "old_attached_neighbor": 0.25,
    "earth_work": 0.25,
    "attached": 0.10,
    "work_types": 0.10,
    "signal_hazards": 0.10,
    "construction": 0.08,
    "job_type": 0.04,
    "soil": 0.04,
    "flood": 0.04,
}
__doc__ += "\n".join(f"    {k}: {v}" for k, v in WEIGHTS.items())

BOROUGHS = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}

# Construction-incident type text (bf97-mjsy) -> work types, for open-data incidents with no case write-up.
INCIDENT_WORK_TYPES = {
    "excavation": ["excavation", "earth_work"],
    "soil": ["earth_work"],
    "shoring": ["support_of_excavation"],
    "scaffold": ["scaffold"],
    "demolition": ["demolition"],
    "facade": ["facade"],
    "crane": ["structural"],
    "structural": ["structural"],
}


# Loading cases


def load_cases(path: Optional[Path] = None) -> tuple[list[dict], bool]:
    """(cases, from_fixture). Hongyu's library once PR 3 has merged, else the contract fixture."""
    if path is None:
        path = CASE_LIBRARY if CASE_LIBRARY.exists() else CASE_FIXTURE
    cases = json.loads(path.read_text(encoding="utf-8"))
    return [Case.model_validate(c).model_dump() for c in cases], path == CASE_FIXTURE


def incident_to_case(feature: dict) -> Optional[dict]:
    """An open-data incident feature (LayerFeature) as a Case: no cause is ever attached to it."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    if (feature.get("geometry") or {}).get("type") != "Point" or len(coords) < 2:
        return None
    text = f"{props.get('title', '')} {props.get('summary', '')}".lower()
    types: set[str] = set()
    for word, mapped in INCIDENT_WORK_TYPES.items():
        if word in text:
            types.update(mapped)
    case = {
        "id": f"incident-{props.get('id')}",
        "title": props.get("title") or "Construction incident",
        "address": props.get("summary") or "",
        "bbl": props.get("bbl"),
        "lat": float(coords[1]),
        "lon": float(coords[0]),
        "date": props.get("date") or "unknown",
        "hazards": [props.get("hazard") or "construction_safety"],
        "severity": props.get("severity", 2),
        "job_type": None,
        "work_types": sorted(types),
        "conditions": {},
        "summary": props.get("summary") or "",
        "cause_as_reported": None,
        "cause_status": "unknown",
        "sources": [{"name": props.get("source_name") or "NYC Open Data", "url": props.get("source_url"),
                     "date": props.get("date")}],
    }
    try:
        return Case.model_validate(case).model_dump()
    except Exception:
        return None


def load_incidents(layers_dir: Path = LAYERS_DIR) -> list[dict]:
    """Open-data incidents from Lise's layer files (PR 2). Empty until they exist."""
    out = []
    for layer_id in INCIDENT_LAYERS:
        path = layers_dir / f"{layer_id}.geojson"
        if not path.exists():
            continue
        try:
            collection = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for feature in collection.get("features") or []:
            if (case := incident_to_case(feature)) is not None:
                out.append(case)
    return out


# Profile features


def _old_attached(profile: dict) -> Optional[dict]:
    """The oldest attached neighbor built before 1940, if any."""
    old = [n for n in profile.get("neighbors", []) if n.get("attached") and n.get("year_built")
           and n["year_built"] < OLD_NEIGHBOR_YEAR]
    return min(old, key=lambda n: n["year_built"]) if old else None


def _construction(profile: dict) -> Optional[str]:
    model = profile.get("structural_model") or {}
    return (model.get("material") or "").lower() or None


def _borough(bbl: Optional[str]) -> Optional[str]:
    return BOROUGHS.get(str(bbl or "")[:1])


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def _readable(items: Iterable[str]) -> str:
    return ", ".join(i.replace("_", " ") for i in sorted(items))


def compare(profile: dict, case: dict) -> dict:
    """{score, matched_on, differs_on} for one case."""
    conditions = case.get("conditions") or {}
    matched: list[str] = []
    differs: list[str] = []
    score = 0.0

    site_types = set(profile.get("work_types") or [])
    case_types = set(case.get("work_types") or [])
    site_earth, case_earth = bool(site_types & EARTH_WORK), bool(case_types & EARTH_WORK)

    # Old attached neighbor.
    old = _old_attached(profile)
    case_year = conditions.get("neighbor_year_built")
    case_attached = conditions.get("attached")
    if case_year is not None:
        if old and case_year < OLD_NEIGHBOR_YEAR:
            score += WEIGHTS["old_attached_neighbor"]
            matched.append(f"attached neighbor built before {OLD_NEIGHBOR_YEAR} "
                           f"(here {old['year_built']}, there {case_year})")
        elif old or case_year < OLD_NEIGHBOR_YEAR:
            here = f"built {old['year_built']}" if old else f"no attached neighbor before {OLD_NEIGHBOR_YEAR}"
            differs.append(f"neighbor age: here {here}, there built {case_year}")

    # Attached at all.
    site_attached = any(n.get("attached") for n in profile.get("neighbors", []))
    if case_attached is not None:
        if case_attached == site_attached:
            score += WEIGHTS["attached"]
            matched.append("attached to a neighboring building" if site_attached else "freestanding")
        else:
            differs.append("attached here, freestanding there" if site_attached else "freestanding here, attached there")

    # Earth work next door, the core pattern.
    if site_earth and case_earth:
        score += WEIGHTS["earth_work"]
        matched.append(f"earth work: {_readable((site_types & case_types & EARTH_WORK) or (case_types & EARTH_WORK))}")
    elif case_types and site_earth != case_earth:
        differs.append("earth work here, none reported there" if site_earth else "no earth work here, earth work there")

    # Other work types.
    other_site, other_case = site_types - EARTH_WORK, case_types - EARTH_WORK
    if other_site and other_case:
        overlap = _jaccard(other_site, other_case)
        if overlap > 0:
            score += WEIGHTS["work_types"] * overlap
            matched.append(f"same work: {_readable(other_site & other_case)}")

    # Construction (needs the Revit or drawing input here, and a reported construction there).
    here, there = _construction(profile), (conditions.get("construction") or "").lower() or None
    if here and there:
        if "masonry" in here and "masonry" in there or here == there:
            score += WEIGHTS["construction"]
            matched.append(f"construction: {there}")
        else:
            differs.append(f"construction: here {here}, there {there}")

    # Signals: do the site's record signals point at the same hazards the case had?
    site_hazards = {s["hazard"] for s in profile.get("signals", []) if s["severity"] >= 1}
    shared = site_hazards & set(case.get("hazards") or [])
    if shared:
        score += WEIGHTS["signal_hazards"]
        matched.append(f"this site has {_readable(shared)} enforcement records, the hazard in this case")

    if profile.get("job_type") and case.get("job_type"):
        if profile["job_type"] == case["job_type"]:
            score += WEIGHTS["job_type"]
            matched.append(f"job type: {profile['job_type'].replace('_', ' ')}")
        else:
            differs.append(f"job type: here {profile['job_type'].replace('_', ' ')}, "
                           f"there {case['job_type'].replace('_', ' ')}")

    if profile.get("soil") and conditions.get("soil"):
        if profile["soil"].split(",")[0].lower() == conditions["soil"].split(",")[0].lower():
            score += WEIGHTS["soil"]
            matched.append(f"same soil: {conditions['soil'].split(',')[0]}")
        else:
            differs.append(f"soil: here {profile['soil'].split(',')[0]}, there {conditions['soil'].split(',')[0]}")

    site_zone = (profile.get("flood") or {}).get("fema_zone")
    if site_zone and conditions.get("flood_zone"):
        if site_zone[:1] == conditions["flood_zone"][:1]:
            score += WEIGHTS["flood"]
            matched.append(f"flood zone {conditions['flood_zone']}")
        else:
            differs.append(f"flood zone: here {site_zone}, there {conditions['flood_zone']}")

    here_boro, there_boro = _borough(profile.get("bbl")), _borough(case.get("bbl"))
    if here_boro and there_boro and here_boro != there_boro:
        differs.append(f"{there_boro}, not {here_boro}")

    return {"score": round(min(score, 1.0), 3), "matched_on": matched, "differs_on": differs}


def rank(
    profile: dict,
    cases: list[dict],
    hazard: Optional[str] = None,
    severity_min: Optional[int] = None,
    limit: int = 12,
) -> dict:
    """SimilarCases for a profile: best first, cases with nothing in common left out."""
    results = []
    for case in cases:
        if hazard and hazard not in case.get("hazards", []):
            continue
        if severity_min is not None and case.get("severity", 0) < severity_min:
            continue
        if case.get("bbl") and case["bbl"] == profile.get("bbl"):
            continue  # the site's own history is in its signals, not a "similar case"
        found = compare(profile, case)
        if not found["matched_on"]:
            continue
        results.append({"case_id": case["id"], "case": case, **found})
    results.sort(key=lambda r: (-r["score"], -r["case"]["severity"], r["case_id"]))
    return SimilarCases.model_validate({"bbl": profile["bbl"], "results": results[:limit]}).model_dump()
