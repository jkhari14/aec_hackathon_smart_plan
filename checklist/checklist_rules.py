"""The checklist's rows: duties toward adjoining property in the 2022 NYC Building Code.

Paraphrased from the city's text, and every row links to it. The proof each row needs is a
document that public data does not hold, so no row is ever marked done from public data.
"""

from __future__ import annotations

from dataclasses import dataclass

CHAPTER_33 = "https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter33_Con_DemoSafetyWBwm.pdf"
CHAPTER_17 = "https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter17_SpecialInspectionsWBwm.pdf"
EXCAVATION_FLAGS = ("earth_work_work_type_", "foundation_work_type_", "support_of_excavation_work_type_")

# Who acts on a row. The same fixed list as the brief's Party type (api/brief/brief_models.py).
PARTIES = ("owner_developer", "design_professional", "excavation_support_engineer", "geotechnical_engineer",
           "contractor", "special_inspector", "adjoining_owner", "dob")


@dataclass(frozen=True)
class Rule:
    id: str  # stable: the brief, the web page and the voice agent refer to rows by it
    section: str
    title: str
    requirement: str
    parties: tuple[str, ...]
    life_safety: bool
    proof_needed: str
    condition: str  # a condition name in applicability.evaluate
    scope: str = "site"  # or "each_adjacent_building"
    source_url: str = CHAPTER_33
    related_filings: str = ""  # "excavation_flags" or "inspector_status"


RULES = (
    Rule("notice", "3309.1.1", "Notify the adjoining owner",
         "Written notice to the adjoining owner at least 60 days before work: the work, schedule, "
         "inspections or monitoring, protection, and a contact. A second notice if there is no reply.",
         ("owner_developer",), False, "The notice letters and their dates", "adjoining_access"),
    Rule("license", "3309.2", "License to enter the adjoining property",
         "The adjoining owner affords a license to enter; section 3309.4 says who carries the "
         "protection duty if they don't.",
         ("adjoining_owner", "owner_developer"), False, "The license, or the refusal", "adjoining_access"),
    Rule("examination", "3309.3", "Examine the adjoining building",
         "Once access is granted, physically examine the adjoining property before work and at "
         "intervals during it, record the conditions, and make the records available to DOB.",
         ("owner_developer", "contractor"), True, "Dated inspection records", "adjoining_access",
         scope="each_adjacent_building"),
    Rule("foundation_protection", "3309.4", "Protect adjoining footings and foundations",
         "Whenever soil or foundation work occurs, at any depth, protect adjoining structures, "
         "including footings and foundations, at the builder's expense.",
         ("owner_developer", "contractor"), True, "The protection design and records that it was installed",
         "excavation", related_filings="excavation_flags"),
    Rule("survey", "3309.4.3", "Preconstruction survey",
         "No excavation 5 to 10 ft deep within 10 ft of an adjacent building, or over 10 ft deep "
         "anywhere, until a survey documents the existing conditions of all adjacent buildings.",
         ("owner_developer", "design_professional"), True, "The preconstruction survey", "survey_threshold",
         scope="each_adjacent_building"),
    Rule("support_drawings", "3304.4.1", "Excavation-support drawings",
         "Means of supporting the excavation shown on construction documents by a design "
         "professional with retaining or bracing experience; over 20 ft deep, a NY State PE.",
         ("excavation_support_engineer",), True, "Stamped support-of-excavation drawings", "excavation",
         related_filings="excavation_flags"),
    Rule("support_basis", "3304.4.1.2", "Geotechnical basis for the support design",
         "The support drawings rest on site-specific testing, and incorporate the geotechnical "
         "report, the evaluation analysis and the preconstruction survey.",
         ("geotechnical_engineer", "excavation_support_engineer"), True,
         "The geotechnical report, cross-referenced in the drawings", "excavation",
         related_filings="excavation_flags"),
    Rule("underpinning", "3309.5", "Underpin or otherwise support adjoining buildings",
         "Where underpinning or another method of support is required, provide it at the builder's "
         "expense.",
         ("owner_developer", "contractor"), True, "Underpinning drawings, and records that they were followed",
         "underpinning"),
    Rule("underpinning_inspection", "1705.25.4", "Special inspection of underpinning",
         "Underpinning and other methods of supporting adjacent property are subject to special "
         "inspections.",
         ("special_inspector",), True, "Special inspection reports", "underpinning",
         source_url=CHAPTER_17, related_filings="inspector_status"),
    Rule("exposed_wall", "3309.8", "Investigate exposed adjoining walls",
         "Where work exposes or breaches an adjoining wall, a design professional investigates its "
         "stability and condition, and the wall's integrity is maintained.",
         ("design_professional",), True, "The wall investigation report", "exposed_wall"),
    Rule("monitoring", "3309.4.4", "Monitor nearby buildings",
         "During excavation, monitor buildings within the excavation's maximum depth of its edge "
         "(and historic structures within 90 ft), under a plan setting scope, frequency, tolerances "
         "and reporting (3309.16).",
         ("design_professional", "contractor"), True, "The monitoring plan and its readings",
         "monitoring_distance", scope="each_adjacent_building"),
    Rule("hazard_elevations", "3309.4.5", "Hazard monitoring ordered by DOB",
         "Where DOB sees a potential hazard from soil or foundation work, elevations of adjacent "
         "buildings are recorded at intervals of 24 hours or less.",
         ("dob", "design_professional"), True, "Elevation readings at the ordered interval", "dob_decides"),
)
