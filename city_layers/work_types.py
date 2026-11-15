"""Which work types to assume for a job type, following how DOB NOW records work.

DOB NOW: Build files each job under a job type, and each filing on the job says yes or no to a
fixed list of work types (dataset w9ak-ipjd). Before a project has filings, ForeSite assumes the
work types that go with its job type: `assumed_work_types`. They are an assumption, so the profile
marks them inferred and the user can untick any of them. Once a site has filings, the work types
they state take over: `stated_work_types`.

The names on the right of every table are `JobType` and `WorkType` in api/contracts.py.
"""

from __future__ import annotations

DATASET = "w9ak-ipjd"
MEASURED_ON = "2026-11-14"
FILINGS_MEASURED = 983_784

# DOB NOW's job type, as the filings dataset prints it -> the contract's job type.
# "No Work" filings state no work type and are not a job type here.
JOB_TYPES = {
    "New Building": "new_building",
    # Filed as an alteration, but its filings carry earth work and foundation as often as a new building's.
    "ALT-CO - New Building with Existing Elements to Remain": "new_building",
    "Alteration": "alteration",
    "Alteration CO": "alteration",
    "Full Demolition": "demolition",
}

# A filing's yes/no column -> the contract's work type.
FILING_COLUMNS = {
    "earth_work_work_type_": "earth_work",
    "foundation_work_type_": "foundation",
    "support_of_excavation_work_type_": "support_of_excavation",
    "structural_work_type_": "structural",
    "full_demolition_work_type_": "demolition",
    "sprinkler_work_type": "sprinkler",
    "plumbing_work_type": "plumbing",
    "mechanical_systems_work_type_": "mechanical",
    "sidewalk_shed_work_type_": "sidewalk_shed",
    "suspended_scaffold_work_type_": "scaffold",
}
# Filing columns with no work type in the contract: general_construction, boiler_equipment,
# protection_mechanical_methods, place_of_assembly, temporary_place_of_assembly, green_roof, solar.

# Work types the contract has and the filings dataset has no column for, so a filing can never state them.
NO_FILING_COLUMN = ("excavation", "underpinning", "facade", "standpipe", "construction_fence")

# The support-of-excavation column reads "No" on every one of the 983,784 filings (checked on
# MEASURED_ON). So a "No" there says nothing about a site, and no filing can state this work type.
NEVER_STATED = ("support_of_excavation",)

# What to assume per job type, most relevant to the neighbors first.
ASSUMED = {
    "new_building": (
        "earth_work", "excavation", "foundation", "support_of_excavation", "structural",
        "plumbing", "mechanical", "sprinkler", "standpipe", "construction_fence", "sidewalk_shed", "scaffold",
    ),
    # The team's alteration walkthrough (session 3) has excavation, foundation, SOE and structural on.
    "alteration": (
        "structural", "earth_work", "excavation", "foundation", "support_of_excavation", "facade",
        "plumbing", "mechanical", "sprinkler", "sidewalk_shed", "scaffold",
    ),
    "demolition": ("demolition", "construction_fence", "sidewalk_shed"),
}
# Underpinning is never assumed: it has no filing column, and whether it is needed depends on the
# adjoining foundations. It stays a question for the structural engineer.

# Percent of filings under each DOB NOW job type that say YES, counted over every filing on MEASURED_ON.
# A job has several filings, so the share of jobs is higher. This is why a work type is on the list.
PERCENT_OF_FILINGS = {
    "New Building": {"earth_work": 24.3, "foundation": 23.8, "structural": 20.0, "plumbing": 17.4,
                     "mechanical": 15.5, "sprinkler": 8.5, "sidewalk_shed": 0.2, "scaffold": 0.1,
                     "support_of_excavation": 0.0, "demolition": 0.0},
    "ALT-CO - New Building with Existing Elements to Remain": {
        "earth_work": 21.8, "foundation": 21.7, "structural": 21.5, "plumbing": 16.2, "mechanical": 16.8,
        "sprinkler": 7.6, "sidewalk_shed": 0.2, "scaffold": 0.0, "support_of_excavation": 0.0, "demolition": 0.0},
    "Alteration": {"earth_work": 1.5, "foundation": 1.2, "structural": 5.9, "plumbing": 24.2,
                   "mechanical": 11.7, "sprinkler": 6.3, "sidewalk_shed": 8.5, "scaffold": 1.8,
                   "support_of_excavation": 0.0, "demolition": 0.0},
    "Alteration CO": {"earth_work": 10.9, "foundation": 10.7, "structural": 15.9, "plumbing": 18.4,
                      "mechanical": 13.9, "sprinkler": 6.4, "sidewalk_shed": 0.1, "scaffold": 0.0,
                      "support_of_excavation": 0.0, "demolition": 0.0},
    "Full Demolition": {"earth_work": 0.0, "foundation": 0.0, "structural": 0.3, "plumbing": 0.0,
                        "mechanical": 0.0, "sprinkler": 0.9, "sidewalk_shed": 0.9, "scaffold": 0.0,
                        "support_of_excavation": 0.0, "demolition": 75.5},
}


def job_type(dob_now_job_type: object) -> str | None:
    """The contract's job type for DOB NOW's, or None for "No Work" and anything unrecognised."""
    return JOB_TYPES.get(str(dob_now_job_type or "").strip())


def assumed_work_types(contract_job_type: str) -> list[str]:
    """The work types to switch on for a job type before any filing exists. Mark them inferred."""
    if contract_job_type not in ASSUMED:
        raise ValueError(f"not a job type: {contract_job_type!r}")
    return list(ASSUMED[contract_job_type])


def stated_work_types(filings: list[dict]) -> list[str]:
    """The work types a site's DOB NOW filings say YES to, in the contract's names.

    Reads whichever work-type columns the rows carry (data_pull requests six of them). An empty
    list means no filing says yes, which is not the same as no such work: see NEVER_STATED and
    NO_FILING_COLUMN.
    """
    stated = []
    for column, work_type in FILING_COLUMNS.items():
        if any(str(filing.get(column) or "").strip().upper() == "YES" for filing in filings):
            stated.append(work_type)
    return stated
