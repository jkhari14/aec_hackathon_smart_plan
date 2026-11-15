"""Site routes, and `load_site_part`, the same answer as a Python call (the chat reads a site through it).

Each part answers from its owner's module once that module defines the function named in SITE_SOURCES,
and from the labelled fixture until then, so an owner plugs in without editing this file. The function
takes the BBL and its part's options (SITE_OPTIONS) as keywords, already checked, and returns the
part's contract model or a dict that matches it. It may raise HTTPException for its own errors. If it
takes a `response` (a FastAPI route function), it gets one, and an answer it marks X-ForeSite-Fixture
stays labelled as sample data.
"""

import importlib
import inspect
from typing import Optional, get_args

from fastapi import APIRouter, HTTPException, Response
from pydantic import TypeAdapter

from api.contracts import ActionItem, EarlyWarning, Hazard, JobType, PatternScore, SimilarCases, SiteProfile, Stage
from api.routers.router_data import DataUnavailable, LoadedData, served, valid_as_of, valid_bbl, valid_choice
from api.stubs import FIXTURE_HEADER, fixture

# part -> (owner module, function it defines, fixture until then)
SITE_SOURCES = {
    "profile": ("site_profile.router", "site_profile", "site_profile"),  # PR 6
    "similar": ("site_profile.router", "similar_cases", "similar_cases"),  # PR 6
    "warnings": ("early_warning", "warnings_for", "warnings"),  # PR 7
    "pattern": ("foresight_model", "pattern_score_for", "pattern_score"),  # PR 12
    "actions": ("actions", "actions_for", "actions"),  # PR 8
}
SITE_OPTIONS = {
    "profile": ("job_type", "stage", "as_of"),
    "similar": ("hazard", "severity_min"),
    "warnings": ("as_of",),
    "pattern": (),
    "actions": ("stage",),
}
_MODELS = {"profile": TypeAdapter(SiteProfile), "similar": TypeAdapter(SimilarCases),
           "warnings": TypeAdapter(list[EarlyWarning]), "pattern": TypeAdapter(PatternScore),
           "actions": TypeAdapter(list[ActionItem])}

sites_router = APIRouter(prefix="/api/sites/{bbl}")


def _checked(job_type, stage, as_of, hazard, severity_min) -> dict:
    if severity_min is not None and (isinstance(severity_min, bool) or not isinstance(severity_min, int)
                                     or not 0 <= severity_min <= 3):
        raise HTTPException(422, "severity_min is 0 to 3")
    return {"job_type": valid_choice(job_type, get_args(JobType), "job_type"),
            "stage": valid_choice(stage, get_args(Stage), "stage"), "as_of": valid_as_of(as_of),
            "hazard": valid_choice(hazard, get_args(Hazard), "hazard"), "severity_min": severity_min}


def _owner_function(module_name: str, function_name: str, where: str):
    """The owner's function, or None while their module or function has not landed. Their module failing
    to import is DataUnavailable: code that is there but broken never falls back to the sample."""
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name == module_name or module_name.startswith(f"{error.name}."):
            return None
        raise DataUnavailable(f"{where} could not be imported ({error.name} is missing)") from error
    except Exception as error:
        raise DataUnavailable(f"{where} could not be imported ({type(error).__name__})") from error
    return getattr(module, function_name, None)


def load_site_part(part: str, bbl: str, job_type: Optional[str] = None, stage: Optional[str] = None,
                   as_of: Optional[str] = None, hazard: Optional[str] = None,
                   severity_min: Optional[int] = None) -> LoadedData:
    """One site part, checked against its contract; `sample` is True while it is the fixture, not this site.

    Pass any of the options: each part gets only its own. Bad input is HTTPException(422), as on the route.
    An owner function that fails or answers off its contract is DataUnavailable, never an empty answer.
    """
    valid_bbl(bbl)
    checked = _checked(job_type, stage, as_of, hazard, severity_min)
    module_name, function_name, fixture_name = SITE_SOURCES[part]
    where = f"{module_name}.{function_name}"
    build = _owner_function(module_name, function_name, where)
    if build is None:
        return LoadedData(_MODELS[part].validate_python(fixture(fixture_name)), True)
    try:
        options = {name: checked[name] for name in SITE_OPTIONS[part]}
        response = Response()
        if "response" in inspect.signature(build).parameters:
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
def actions(bbl: str, response: Response, stage: Optional[str] = None):
    return served(response, load_site_part, "actions", bbl, stage=stage)
