"""The four facts that make two buildings alike for this product: era, wall system, height, attachment.

They are the facts that decide how a building takes nearby excavation, fire or a facade failure, and
the only ones public data gives for every lot (PLUTO) and most written-up cases give in words. Style,
zoning and risk category are left out on purpose: they describe looks and use, not fragility.

Every fact comes with where it came from. An inference (a wall system read off a building class and
year) is labeled as one and never worded like a fact.
"""

from __future__ import annotations

import re
from typing import Optional

# Code eras: the 1938, 1968 and 2008 Building Codes. A band is (first year, label).
ERAS = (
    (0, "built before 1900"),
    (1900, "built 1900 to 1937 (before the 1938 code)"),
    (1938, "built 1938 to 1967 (1938 code)"),
    (1968, "built 1968 to 2007 (1968 code)"),
    (2008, "built 2008 or later (2008 code)"),
)
FLOOR_BANDS = ((1, "1 to 3 storeys"), (4, "4 to 6 storeys"), (7, "7 to 12 storeys"), (13, "13 storeys or more"))

MASONRY = "masonry bearing wall"
WOOD = "wood frame"
FRAME = "steel or concrete frame"

# Words a case write-up uses, checked in this order; the first list that matches decides. Whole words,
# so "unreinforced" is not read as "reinforced".
_WOOD_WORDS = ("wood frame", "wood-frame", "timber frame", "frame house", "wooden")
_FRAME_WORDS = ("steel", "concrete", "reinforced", "high-rise", "tower", "skyscraper")
_MASONRY_WORDS = ("masonry", "brick", "brownstone", "stone", "tenement", "row house", "rowhouse", "bearing wall",
                  "bearing pier", "unreinforced")
# "terra cotta clad" and the like describe the skin, not the structure.
_CLADDING_WORDS = ("clad", "cladding", "veneer", "curtain wall")

# PLUTO proxcode: 0 not available, 1 detached, 2 semi-attached, 3 attached.
PROXCODE = {"1": False, "2": True, "3": True}

_NUMBER_WORDS = {w: i for i, w in enumerate(
    "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split(), start=1)}
_STOREYS = re.compile(r"\b(\d{1,3}|" + "|".join(_NUMBER_WORDS) + r")[- ]?stor(?:e|)y", re.IGNORECASE)


def era(year: Optional[int]) -> Optional[str]:
    if not year or year < 1600:
        return None
    return next(label for start, label in reversed(ERAS) if year >= start)


def floors_band(floors: Optional[float]) -> Optional[str]:
    if not floors or floors < 1:
        return None
    return next(label for start, label in reversed(FLOOR_BANDS) if floors >= start)


def floors_in_text(text: Optional[str]) -> Optional[int]:
    """'three-storey masonry' -> 3, '19-storey residential high-rise' -> 19, else None."""
    found = _STOREYS.search(text or "")
    if not found:
        return None
    word = found.group(1).lower()
    return int(word) if word.isdigit() else _NUMBER_WORDS[word]


def wall_system_in_text(text: Optional[str]) -> Optional[str]:
    """The wall system a case write-up states, or None when it only describes the skin or says nothing."""
    words = (text or "").lower()
    if not words:
        return None

    def says(options: tuple[str, ...]) -> bool:
        return any(re.search(rf"\b{re.escape(w)}", words) for w in options)

    if says(_WOOD_WORDS):
        return WOOD
    if says(("unreinforced",)):
        return MASONRY
    if says(_FRAME_WORDS):
        return FRAME
    if says(_CLADDING_WORDS):
        return None
    if says(_MASONRY_WORDS):
        return MASONRY
    return None


def wall_system_from_class(building_class: Optional[str], year: Optional[int]) -> Optional[str]:
    """A guess from PLUTO's building class and year, for buildings nobody has described.

    Walk-ups, mixed-use walk-ups and stores built before the 1938 code are nearly always bearing-wall
    masonry in New York; elevator buildings, offices and towers from 1968 on are framed. One- and
    two-family houses can be either, so they get no guess. Hongyu reviews this table.
    """
    letter = (building_class or "").strip()[:1].upper()
    if not letter or not year:
        return None
    if letter in "CSK" and year < 1938:
        return MASONRY
    if letter in "DORH" and year >= 1968:
        return FRAME
    return None


def building(label: str, *, year: Optional[int], floors: Optional[float], building_class: Optional[str],
             attached: Optional[bool], stated_wall: Optional[str] = None) -> dict:
    """One building's four facts, each with its basis."""
    wall, basis = stated_wall, "stated"
    if not wall:
        wall = wall_system_from_class(building_class, year)
        basis = "inferred from building class and year" if wall else None
    return {
        "label": label,
        "year_built": year,
        "era": era(year),
        "floors": floors,
        "floors_band": floors_band(floors),
        "wall_system": wall,
        "wall_basis": basis if wall else None,
        "attached": attached,
    }


def site_buildings(profile: dict) -> list[dict]:
    """The site's own building and every touching neighbor, as buildings to compare a case against."""
    lot = profile.get("lot") or {}
    neighbors = profile.get("neighbors") or []
    model = profile.get("structural_model") or {}
    found = [building(
        f"the site ({lot.get('address') or profile.get('address_matched') or profile.get('bbl')})",
        year=lot.get("year_built"), floors=lot.get("floors"), building_class=lot.get("building_class"),
        attached=any(n.get("attached") for n in neighbors) if neighbors else None,
        # The model's material names the walls; its lateral system does too. Its gravity system names the
        # floors (wood joists on masonry walls), so it is not read.
        stated_wall=wall_system_in_text(model.get("material")) or wall_system_in_text(model.get("lateral_system")),
    )]
    for n in neighbors:
        found.append(building(
            f"the neighbor at {n.get('address') or n.get('bbl')}",
            year=n.get("year_built"), floors=n.get("floors"), building_class=n.get("building_class"),
            attached=n.get("attached"),
        ))
    return found


def case_building(case: dict) -> dict:
    """The building a case write-up describes: the one that was hurt, in the words the sources used."""
    conditions = case.get("conditions") or {}
    text = conditions.get("construction")
    year = conditions.get("neighbor_year_built") or conditions.get("year_built")
    return building(
        case.get("address") or case.get("id") or "the case",
        year=year, floors=conditions.get("floors") or floors_in_text(text),
        building_class=None, attached=conditions.get("attached"), stated_wall=wall_system_in_text(text),
    )


def describe(b: dict) -> str:
    """'built 1930 (1900 to 1937), masonry bearing wall (inferred ...), 1 to 3 storeys, attached'."""
    parts = []
    if b.get("era"):
        parts.append(f"built {b['year_built']} ({b['era'].split('(')[0].replace('built ', '').strip()})")
    if b.get("wall_system"):
        parts.append(b["wall_system"] + (f" ({b['wall_basis']})" if b.get("wall_basis") != "stated" else ""))
    if b.get("floors_band"):
        parts.append(b["floors_band"])
    if b.get("attached") is not None:
        parts.append("attached" if b["attached"] else "freestanding")
    return ", ".join(parts) or "nothing recorded"
