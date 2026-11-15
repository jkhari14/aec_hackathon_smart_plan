"""`GET /api/sites/{bbl}/profile` and `GET /api/sites/{bbl}/similar`, made real.

`api/stubs.py` calls these two handlers from the stubs' old place, so the route order, and with it the
generated `api/openapi.json` and `web/src/api_types.ts`, stay exactly as they were. `router` is here
for when Jacob moves them to `app.include_router` with a regeneration.

A saved pull in data/cache/ answers at once; any other BBL is pulled live and kept in memory for this
process. When the case library (PR 3) has not merged, similar cases are ranked over the contract fixture
and the answer carries `X-ForeSite-Fixture: true` so the app labels it as sample data.
"""

from __future__ import annotations

from datetime import date
from threading import Lock
from typing import Optional, get_args

from fastapi import APIRouter, HTTPException, Response

from api.contracts import Hazard, JobType, SiteProfile, SimilarCases, Stage
from site_profile import build_profile as builder
from site_profile import similarity

FIXTURE_HEADER = "X-ForeSite-Fixture"

router = APIRouter(prefix="/api")

HAZARDS, JOB_TYPES, STAGES = set(get_args(Hazard)), set(get_args(JobType)), set(get_args(Stage))

_pulls: dict[str, dict] = {}
_lock = Lock()


def _pull(bbl: str) -> dict:
    try:
        builder.soda_client.validate_bbl(bbl)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    with _lock:
        if bbl in _pulls:
            return _pulls[bbl]
    try:
        pull = builder.load_pull(bbl)
    except builder.PullUnavailable as error:
        raise HTTPException(503, f"Couldn't load the public records for {bbl}. {error}") from error
    with _lock:
        _pulls[bbl] = pull
    return pull


def _choice(name: str, value: Optional[str], allowed: set[str]) -> Optional[str]:
    if value is not None and value not in allowed:
        raise HTTPException(422, f"{name} must be one of: {', '.join(sorted(allowed))}")
    return value


def _as_of(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise HTTPException(422, "as_of must be YYYY-MM-DD") from error


def get_profile(bbl: str, job_type: Optional[str] = None, stage: Optional[str] = None,
                as_of: Optional[str] = None, structural_model: Optional[dict] = None) -> dict:
    if structural_model is None:
        from model_input import store  # a Revit export or drawing uploaded for this site (PR 13)

        structural_model = store.for_site(bbl)
    try:
        return builder.build_profile(_pull(bbl), job_type, stage, _as_of(as_of), structural_model)
    except ValueError as error:
        raise HTTPException(503, f"Couldn't build the profile for {bbl}: {error}") from error


@router.get("/sites/{bbl}/profile", response_model=SiteProfile)
def site_profile(
    bbl: str,
    response: Response,
    job_type: Optional[str] = None,
    stage: Optional[str] = None,
    as_of: Optional[str] = None,
):
    return get_profile(bbl, _choice("job_type", job_type, JOB_TYPES), _choice("stage", stage, STAGES), as_of)


@router.get("/sites/{bbl}/similar", response_model=SimilarCases)
def similar_cases(
    bbl: str,
    response: Response,
    hazard: Optional[str] = None,
    severity_min: Optional[int] = None,
):
    _choice("hazard", hazard, HAZARDS)
    if severity_min is not None and not 0 <= severity_min <= 3:
        raise HTTPException(422, "severity_min must be 0 to 3")
    profile = get_profile(bbl)
    cases, from_fixture = similarity.load_cases()
    if from_fixture:
        response.headers[FIXTURE_HEADER] = "true"
    return similarity.rank(profile, cases + similarity.load_incidents(), hazard, severity_min)
