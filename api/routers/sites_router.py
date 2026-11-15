"""Site routes, and `load_site_part`, the same answer as a Python call (the chat reads a site through it).

Each part answers from its owner's module once that module defines the function named in SITE_SOURCES,
and from the labelled fixture until then, so an owner plugs in without editing this file. The function
takes the BBL and its part's options (SITE_OPTIONS) as keywords, already checked, and returns the
part's contract model or a dict that matches it. It may raise HTTPException for its own errors. If it
takes a `response` (a FastAPI route function), it gets one, and an answer it marks X-ForeSite-Fixture
stays labelled as sample data.
"""

import inspect
from typing import Optional, get_args

from fastapi import APIRouter, HTTPException, Response
from pydantic import TypeAdapter

from api.contracts import (
    ActionItem, EarlyWarning, Hazard, JobType, PatternScore, SimilarCases, SiteOutlook, SiteProfile, Stage, WorkType,
)
from api.routers.router_data import (
    DataUnavailable, LoadedData, owner_function, served, valid_as_of, valid_bbl, valid_choice,
)
from api.stubs import FIXTURE_HEADER, fixture

# part -> (owner module, function it defines, fixture until then)
SITE_SOURCES = {
    "profile": ("site_profile.router", "site_profile", "site_profile"),  # PR 6
    "similar": ("site_profile.router", "similar_cases", "similar_cases"),  # PR 6
    "warnings": ("early_warning", "warnings_for", "warnings"),  # PR 7
    "pattern": ("foresight_model.router", "pattern", "pattern_score"),  # PR 12
    "actions": ("actions", "actions_for", "actions"),  # PR 8
}
SITE_OPTIONS = {
    "profile": ("job_type", "stage", "as_of"),
    "similar": ("hazard", "severity_min"),
    "warnings": ("as_of",),
    "pattern": (),
    "actions": ("stage", "job_type", "work_types", "excavation_depth_ft", "proposed_storeys"),
}
_MODELS = {"profile": TypeAdapter(SiteProfile), "similar": TypeAdapter(SimilarCases),
           "warnings": TypeAdapter(list[EarlyWarning]), "pattern": TypeAdapter(PatternScore),
           "actions": TypeAdapter(list[ActionItem])}

sites_router = APIRouter(prefix="/api/sites/{bbl}")


def _work_types(value) -> Optional[list[str]]:
    """A comma-separated list (the route) or a list (a Python caller), each one a contract WorkType. Empty is None."""
    if value is None:
        return None
    parts = [p.strip() for p in (value.split(",") if isinstance(value, str) else value)]
    parts = [p for p in parts if p]
    for part in parts:
        valid_choice(part, get_args(WorkType), "work_types")
    return list(dict.fromkeys(parts)) or None


def _feet(value, name: str) -> Optional[float]:
    """A number of feet or storeys, 0 or more, or None."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise HTTPException(422, f"{name} must be a number, 0 or more")
    return float(value)


def _checked(job_type, stage, as_of, hazard, severity_min, work_types=None, excavation_depth_ft=None,
             proposed_storeys=None) -> dict:
    if severity_min is not None and (isinstance(severity_min, bool) or not isinstance(severity_min, int)
                                     or not 0 <= severity_min <= 3):
        raise HTTPException(422, "severity_min is 0 to 3")
    return {"job_type": valid_choice(job_type, get_args(JobType), "job_type"),
            "stage": valid_choice(stage, get_args(Stage), "stage"), "as_of": valid_as_of(as_of),
            "hazard": valid_choice(hazard, get_args(Hazard), "hazard"), "severity_min": severity_min,
            "work_types": _work_types(work_types),
            "excavation_depth_ft": _feet(excavation_depth_ft, "excavation_depth_ft"),
            "proposed_storeys": _feet(proposed_storeys, "proposed_storeys")}


def load_site_part(part: str, bbl: str, job_type: Optional[str] = None, stage: Optional[str] = None,
                   as_of: Optional[str] = None, hazard: Optional[str] = None,
                   severity_min: Optional[int] = None, work_types=None, excavation_depth_ft=None,
                   proposed_storeys=None) -> LoadedData:
    """One site part, checked against its contract; `sample` is True while it is the fixture, not this site.

    Pass any of the options: each part gets only its own. Bad input is HTTPException(422), as on the route.
    An owner function that fails or answers off its contract is DataUnavailable, never an empty answer.
    """
    valid_bbl(bbl)
    checked = _checked(job_type, stage, as_of, hazard, severity_min, work_types, excavation_depth_ft, proposed_storeys)
    module_name, function_name, fixture_name = SITE_SOURCES[part]
    where = f"{module_name}.{function_name}"
    build = owner_function(module_name, function_name)
    if build is None:
        return LoadedData(_MODELS[part].validate_python(fixture(fixture_name)), True)
    try:
        params = inspect.signature(build).parameters
        takes_any = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values())
        # An owner gets the options it declares: one written before an option was added keeps working.
        options = {name: checked[name] for name in SITE_OPTIONS[part] if takes_any or name in params}
        response = Response()
        if "response" in params:
            options["response"] = response
        answer = build(bbl, **options)
        return LoadedData(_MODELS[part].validate_python(answer), response.headers.get(FIXTURE_HEADER) == "true")
    except HTTPException as error:
        raise DataUnavailable(f"{where}: {error.detail}", error.status_code) from error
    except Exception as error:  # any failure is reported as a failure, so no caller reads it as "none found"
        raise DataUnavailable(f"{where} could not answer ({type(error).__name__})") from error


@sites_router.get("/profile", response_model=SiteProfile)
def site_profile(bbl: str, response: Response, job_type: Optional[str] = None, stage: Optional[str] = None,
                 as_of: Optional[str] = None):
    return served(response, load_site_part, "profile", bbl, job_type=job_type, stage=stage, as_of=as_of)


@sites_router.get("/similar", response_model=SimilarCases)
def similar_cases(bbl: str, response: Response, hazard: Optional[str] = None, severity_min: Optional[int] = None):
    return served(response, load_site_part, "similar", bbl, hazard=hazard, severity_min=severity_min)


@sites_router.get("/warnings", response_model=list[EarlyWarning])
def warnings(bbl: str, response: Response, as_of: Optional[str] = None):
    return served(response, load_site_part, "warnings", bbl, as_of=as_of)


@sites_router.get("/pattern", response_model=PatternScore)
def pattern(bbl: str, response: Response):
    return served(response, load_site_part, "pattern", bbl)


@sites_router.get("/actions", response_model=list[ActionItem])
def actions(bbl: str, response: Response, stage: Optional[str] = None, job_type: Optional[str] = None,
            work_types: Optional[str] = None, excavation_depth_ft: Optional[float] = None,
            proposed_storeys: Optional[float] = None):
    """`job_type`, `work_types` (comma-separated), `excavation_depth_ft` and `proposed_storeys` are the
    project screen's setup choices."""
    return served(response, load_site_part, "actions", bbl, stage=stage, job_type=job_type, work_types=work_types,
                  excavation_depth_ft=excavation_depth_ft, proposed_storeys=proposed_storeys)


@sites_router.get("/outlook", response_model=SiteOutlook)
def outlook(bbl: str, response: Response):
    """What could go wrong here, for every option: lessons from similar past projects, from this lot's profile."""
    from lessons.outlook import site_outlook

    profile = served(response, load_site_part, "profile", bbl)
    return site_outlook(profile.model_dump() if hasattr(profile, "model_dump") else profile)
