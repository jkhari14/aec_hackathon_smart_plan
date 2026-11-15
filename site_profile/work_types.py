"""Job type and work types for a site, read from its DOB NOW filings or inferred from the job type.

Lise's `city_layers/work_types.py` (PR 2) will hold the full DOB NOW job type to work types table. Until it
merges, the small table below stands in, and `infer_work_types` prefers hers when it can be imported.
"""

from __future__ import annotations

from typing import Iterable, Optional

from checklist.record_dates import parse_record_date

# DOB NOW job type text -> contract JobType.
JOB_TYPES = {
    "new building": "new_building",
    "alteration": "alteration",
    "alteration co": "alteration",
    "alteration type 1": "alteration",
    "full demolition": "demolition",
    "demolition": "demolition",
}

# Stand-in for the DOB NOW structure: the work types a job type usually carries. Everything is on by
# default and the user unticks what does not apply.
DEFAULT_WORK_TYPES = {
    "new_building": [
        "earth_work", "excavation", "foundation", "support_of_excavation", "structural",
        "plumbing", "mechanical", "sprinkler", "standpipe", "sidewalk_shed", "construction_fence",
    ],
    "alteration": ["structural", "plumbing", "mechanical", "sprinkler", "sidewalk_shed", "scaffold"],
    "demolition": ["demolition", "sidewalk_shed", "construction_fence", "scaffold"],
}

# DOB NOW filing flag column -> work types it stands for.
FILING_FLAGS = {
    "earth_work_work_type_": ["earth_work", "excavation"],
    "foundation_work_type_": ["foundation"],
    "support_of_excavation_work_type_": ["support_of_excavation"],
    "structural_work_type_": ["structural"],
    "sprinkler_work_type": ["sprinkler"],
    "full_demolition_work_type_": ["demolition"],
}

EARTH_WORK = {"earth_work", "excavation", "foundation", "support_of_excavation", "underpinning"}

_ORDER = [
    "earth_work", "excavation", "foundation", "support_of_excavation", "underpinning", "structural",
    "facade", "demolition", "sprinkler", "standpipe", "plumbing", "mechanical", "sidewalk_shed",
    "scaffold", "construction_fence",
]


def ordered(work_types: Iterable[str]) -> list[str]:
    wanted = set(work_types)
    return [w for w in _ORDER if w in wanted]


def job_type_from_text(text: object) -> Optional[str]:
    return JOB_TYPES.get(str(text or "").strip().lower())


def infer_work_types(job_type: Optional[str]) -> list[str]:
    if not job_type:
        return []
    try:  # Lise's full table, once PR 2 has merged.
        from city_layers.work_types import work_types_for_job_type  # type: ignore

        return ordered(work_types_for_job_type(job_type))
    except Exception:
        return list(DEFAULT_WORK_TYPES.get(job_type, []))


def _flag_on(value: object) -> bool:
    return str(value or "").strip().upper() in {"YES", "Y", "TRUE", "1"}


def from_filings(filings: list[dict]) -> tuple[Optional[str], list[str]]:
    """(job type of the newest filing, work types any filing flags). Filings with no date sort last."""
    dated = sorted(filings, key=lambda f: parse_record_date(f.get("filing_date")) or parse_record_date("19000101"),
                   reverse=True)
    job_type = next((jt for f in dated if (jt := job_type_from_text(f.get("job_type")))), None)
    flagged: set[str] = set()
    for filing in filings:
        for column, types in FILING_FLAGS.items():
            if _flag_on(filing.get(column)):
                flagged.update(types)
    return job_type, ordered(flagged)


def resolve(filings: list[dict], job_type: Optional[str]) -> tuple[Optional[str], list[str], bool]:
    """(job type, work types, inferred). A job type passed by the user wins and its work types are inferred.
    Otherwise the filings say what was filed; when they flag nothing, the work types are inferred."""
    filed_job_type, flagged = from_filings(filings)
    if job_type:
        return job_type, infer_work_types(job_type), True
    if flagged:
        return filed_job_type, flagged, False
    return filed_job_type, infer_work_types(filed_job_type), True
