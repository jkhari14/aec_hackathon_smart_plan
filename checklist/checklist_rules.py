"""The checklist's rows: duties toward adjoining property in the 2022 NYC Building Code.

Paraphrased from the city's text, and every row links to it. The proof each row needs is a
document that public data does not hold, so no row is ever marked done from public data.
"""

from __future__ import annotations

from dataclasses import dataclass

CHAPTER_33 = "https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter33_Con_DemoSafetyWBwm.pdf"
CHAPTER_17 = "https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter17_SpecialInspectionsWBwm.pdf"
EXCAVATION_FLAGS = ("earth_work_work_type_", "foundation_work_type_", "support_of_excavation_work_type_")


@dataclass(frozen=True)
class Rule:
    section: str
    title: str
    requirement: str
    responsible: str
    proof_needed: str
    condition: str  # a key in applicability.CONDITIONS
    scope: str = "site"  # or "each_adjacent_building"
    source_url: str = CHAPTER_33
    related_filings: str = ""  # "excavation_flags" or "inspector_status"


RULES = (
    Rule("3309.1.1", "Notify the adjoining owner",
         "Written notice to the adjoining owner at least 60 days before work: the work, schedule, "
         "inspections or monitoring, protection, and a contact. A second notice if there is no reply.",
         "Owner / developer", "The notice letters and their dates", "adjoining_access"),
    Rule("3309.2", "License to enter the adjoining property",
         "The adjoining owner affords a license to enter; section 3309.4 says who carries the "
         "protection duty if they don't.",
         "Adjoining owner", "The license, or the refusal", "adjoining_access"),
    Rule("3309.3", "Examine the adjoining building",
         "Once access is granted, physically examine the adjoining property before work and at "
         "intervals during it, record the conditions, and make the records available to DOB.",
         "Whoever causes the work", "Dated inspection records", "adjoining_access",
         scope="each_adjacent_building"),
    Rule("3309.4", "Protect adjoining footings and foundations",
         "Whenever soil or foundation work occurs, at any depth, protect adjoining structures, "
         "including footings and foundations, at the builder's expense.",
         "Developer / contractor", "The protection design and records that it was installed",
         "excavation", related_filings="excavation_flags"),
    Rule("3309.4.3", "Preconstruction survey",
         "No excavation 5 to 10 ft deep within 10 ft of an adjacent building, or over 10 ft deep "
         "anywhere, until a survey documents the existing conditions of all adjacent buildings.",
         "Owner / design professional", "The preconstruction survey", "survey_threshold",
         scope="each_adjacent_building"),
    Rule("3304.4.1", "Excavation-support drawings",
         "Means of supporting the excavation shown on construction documents by a design "
         "professional with retaining or bracing experience; over 20 ft deep, a NY State PE.",
         "Support-of-excavation engineer", "Stamped support-of-excavation drawings", "excavation",
         related_filings="excavation_flags"),
    Rule("3304.4.1.2", "Geotechnical basis for the support design",
         "The support drawings rest on site-specific testing, and incorporate the geotechnical "
         "report, the evaluation analysis and the preconstruction survey.",
         "Geotechnical + support engineer", "The geotechnical report, cross-referenced in the drawings",
         "excavation", related_filings="excavation_flags"),
    Rule("3309.5", "Underpin or otherwise support adjoining buildings",
         "Where underpinning or another method of support is required, provide it at the builder's "
         "expense.",
         "Developer / contractor", "Underpinning drawings, and records that they were followed",
         "underpinning"),
    Rule("1705.25.4", "Special inspection of underpinning",
         "Underpinning and other methods of supporting adjacent property are subject to special "
         "inspections.",
         "Special inspector", "Special inspection reports", "underpinning",
         source_url=CHAPTER_17, related_filings="inspector_status"),
    Rule("3309.8", "Investigate exposed adjoining walls",
         "Where work exposes or breaches an adjoining wall, a design professional investigates its "
         "stability and condition, and the wall's integrity is maintained.",
         "Design professional", "The wall investigation report", "exposed_wall"),
    Rule("3309.4.4", "Monitor nearby buildings",
         "During excavation, monitor buildings within the excavation's maximum depth of its edge "
         "(and historic structures within 90 ft), under a plan setting scope, frequency, tolerances "
         "and reporting (3309.16).",
         "Design professional / contractor", "The monitoring plan and its readings",
         "monitoring_distance", scope="each_adjacent_building"),
    Rule("3309.4.5", "Hazard monitoring ordered by DOB",
         "Where DOB sees a potential hazard from soil or foundation work, elevations of adjacent "
         "buildings are recorded at intervals of 24 hours or less.",
         "DOB / design professional", "Elevation readings at the ordered interval", "dob_decides"),
)
