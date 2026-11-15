"""The pattern model's features: one list for training (from `dataset.row_for`) and for scoring a
`SiteProfile`, so the two never drift apart."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

OLD_YEAR = 1940
PRIOR_DAYS = 3 * 365
BOROUGHS = {"1": "manhattan", "2": "bronx", "3": "brooklyn", "4": "queens", "5": "staten_island"}

LABELS = {
    "job_new_building": "new building",
    "flag_earth_work": "earth work filed",
    "flag_foundation": "foundation work filed",
    "flag_soe": "support of excavation filed",
    "touching_lots": "touching lots",
    "attached_neighbors": "touching lots with a building",
    "pre1940_attached": "attached neighbors built before 1940",
    "oldest_neighbor_year": "oldest neighbor (year built)",
    "max_neighbor_floors": "tallest neighbor (floors)",
    "max_neighbor_height_ft": "tallest neighbor (roof height, ft)",
    "masonry_era_walkups": "pre-1940 residential or mixed-use neighbors",
    "prior_structural_complaints": "structural complaints in the 3 years before",
    "prior_adjacent_complaints": "'adjacent building not protected' complaints in the 3 years before",
    "prior_incidents": "construction incidents in the 3 years before",
    **{f"boro_{name}": f"in {name.replace('_', ' ').title()}" for name in BOROUGHS.values()},
}
FEATURES = list(LABELS)

EARTH = {"earth_work", "excavation"}


def in_similar_group(features: dict) -> bool:
    """The comparison group: earth work, foundation or SOE next to an attached building built before 1940."""
    return bool(features["pre1940_attached"]) and bool(
        features["flag_earth_work"] or features["flag_foundation"] or features["flag_soe"])


def similar_group_text() -> str:
    return "past earth-work, foundation or excavation-support filings next to an attached building built before 1940"


def features_from_profile(profile: dict, as_of: Optional[str] = None) -> dict:
    """The model's features for a SiteProfile, as of a day (default: the profile's as-of, else today).
    Construction incidents are not in the profile yet, so prior_incidents is 0 (noted in the model card)."""
    ref = date.fromisoformat(as_of or profile.get("as_of") or date.today().isoformat())
    work = set(profile.get("work_types") or [])
    attached = [n for n in profile.get("neighbors", []) if n.get("attached")]
    old = [n for n in attached if n.get("year_built") and n["year_built"] < OLD_YEAR]
    years = [n["year_built"] for n in attached if n.get("year_built")]
    prior = [s for s in profile.get("signals", [])
             if s["id"].startswith("sig-dob_complaints-") and s.get("date")
             and ref - timedelta(days=PRIOR_DAYS) <= date.fromisoformat(s["date"]) < ref]
    return {
        "job_new_building": int(profile.get("job_type") == "new_building"),
        "flag_earth_work": int(bool(work & EARTH)),
        "flag_foundation": int("foundation" in work),
        "flag_soe": int("support_of_excavation" in work),
        "touching_lots": len(profile.get("neighbors", [])),
        "attached_neighbors": len(attached),
        "pre1940_attached": len(old),
        "oldest_neighbor_year": min(years) if years else 0,
        "max_neighbor_floors": int(max((n.get("floors") or 0 for n in attached), default=0)),
        "max_neighbor_height_ft": int(max((n.get("height_ft") or 0 for n in attached), default=0)),
        "masonry_era_walkups": sum(1 for n in old if str(n.get("building_class") or "")[:1] in {"A", "B", "C", "S"}),
        "prior_structural_complaints": len(prior),
        "prior_adjacent_complaints": sum(1 for s in prior if s["title"].startswith("Adjacent building not protected")),
        "prior_incidents": 0,
        **{f"boro_{name}": int(str(profile.get("bbl", ""))[:1] == digit) for digit, name in BOROUGHS.items()},
    }
