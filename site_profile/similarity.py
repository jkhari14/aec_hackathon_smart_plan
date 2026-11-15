"""Rank past cases and open-data incidents by how much they resemble a site's profile.

The score is a weighted sum of plain features, each one a sentence a structural engineer can check.
Half of it is the building: a case's write-up describes the building that was hurt, and it is
compared with the site's own building and each touching neighbor on four facts (era, wall system,
height, attachment: see building_profile.py). The best-matching building is named in the explanation.
The other half is the work and the ground. A feature the case does not report counts as no match and
is not listed as a difference, because "not reported" is not "different". The score says how alike
two sites look on paper, nothing about what will happen.

Weights (Hongyu reviews these, see BUILD.md):
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from api.contracts import Case, SimilarCases
from site_profile.building_profile import case_building, describe, site_buildings
from site_profile.work_types import EARTH_WORK

REPO_ROOT = Path(__file__).resolve().parent.parent
CASE_LIBRARY = REPO_ROOT / "data" / "cases" / "cases.json"
CASE_FIXTURE = REPO_ROOT / "contracts" / "fixtures" / "cases.json"
LAYERS_DIR = REPO_ROOT / "data" / "layers"
INCIDENT_LAYERS = ("construction_incidents",)

WEIGHTS = {
    "building_era": 0.18,
    "building_wall_system": 0.18,
    "building_height": 0.10,
    "building_attached": 0.10,
    "earth_work": 0.20,
    "work_types": 0.08,
    "signal_hazards": 0.08,
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


def compare_buildings(here: dict, there: dict) -> dict:
    """{score, matched, differs} for one site building against the case's building, on the four facts."""
    score, matched, differs = 0.0, [], []
    for key, weight in (("era", "building_era"), ("wall_system", "building_wall_system"),
                        ("floors_band", "building_height"), ("attached", "building_attached")):
        a, b = here.get(key), there.get(key)
        if a is None or b is None:
            continue  # not reported on one side: neither a match nor a difference
        if a == b:
            score += WEIGHTS[weight]
            matched.append(key)
        else:
            differs.append(key)
    return {"score": score, "matched": matched, "differs": differs}


def _best_building(profile: dict, case: dict) -> Optional[tuple[dict, dict]]:
    """The site building most like the case's, with its comparison; None when nothing can be compared.

    When the case involved earth work and the site is a new building or a demolition (or its job type
    is unknown and it has earth work), the building that was hurt stood next to the dig, so only the
    site's neighbors are compared; the site's own building is the one being replaced. For an
    alteration the site's building is at risk too.
    Ties go to a building whose wall system is stated over one whose wall system is a guess, then to
    the site's own building, then to the oldest.
    """
    there = case_building(case)
    candidates = site_buildings(profile)
    site_digs = bool(set(profile.get("work_types") or []) & EARTH_WORK)
    replacing = profile.get("job_type") in ("new_building", "demolition") or (profile.get("job_type") is None and site_digs)
    if set(case.get("work_types") or []) & EARTH_WORK and replacing:
        candidates = candidates[1:]
    best = None
    for here in candidates:
        found = compare_buildings(here, there)
        if not (found["matched"] or found["differs"]):
            continue
        key = (found["score"], here.get("wall_basis") == "stated", here is candidates[0] and here["label"].startswith("the site"),
               -(here.get("year_built") or 9999))
        if best is None or key > best[0]:
            best = (key, here, found)
    return (best[1], best[2]) if best else None


_FACT_WORDS = {"era": "era", "wall_system": "wall system", "floors_band": "height", "attached": "attachment"}


def _building_sentences(here: dict, there: dict, found: dict) -> tuple[list[str], list[str]]:
    """One sentence for the facts that match, one per fact that differs."""
    matched, differs = [], []
    if found["matched"]:
        shown = {k: here.get(k) for k in ("year_built", "wall_basis")}
        shown.update({k: here[k] for k in found["matched"]})
        matched.append(f"{here['label']} is like the building in this case: {describe(shown)}")
    for key in found["differs"]:
        a, b = here[key], there[key]
        if key == "attached":
            a, b = ("attached" if a else "freestanding"), ("attached" if b else "freestanding")
        differs.append(f"{_FACT_WORDS[key]}: {here['label']} is {a}, the case's building was {b}")
    return matched, differs


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

    # The building: the case's hurt building against the site's own building and each neighbor.
    best = _best_building(profile, case)
    if best:
        here, found = best
        score += found["score"]
        same, other = _building_sentences(here, case_building(case), found)
        matched.extend(same)
        differs.extend(other)

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

    # Signals: do the site's record signals point at the same hazards the case had?
    site_hazards = {s["hazard"] for s in profile.get("signals", []) if s["severity"] >= 1}
    shared = site_hazards & set(case.get("hazards") or [])
    if shared:
        score += WEIGHTS["signal_hazards"]
        matched.append(f"this site has {_readable(shared)} enforcement records, the hazard in this case")

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
        own_lots = {profile.get("bbl"), *(n.get("bbl") for n in profile.get("neighbors") or [])}
        if case.get("bbl") and case["bbl"] in own_lots:
            continue  # the site's own history, or a neighbor's, is in its signals, not a "similar case"
        when = str(case.get("date") or "")[:10]
        if profile.get("as_of") and when[:4].isdigit() and when > profile["as_of"]:
            continue  # not yet happened as of that day (an undated incident is kept)
        found = compare(profile, case)
        if not found["matched_on"]:
            continue
        results.append({"case_id": case["id"], "case": case, **found})
    results.sort(key=lambda r: (-r["score"], -r["case"]["severity"], r["case_id"]))
    return SimilarCases.model_validate({"bbl": profile["bbl"], "results": results[:limit]}).model_dump()
