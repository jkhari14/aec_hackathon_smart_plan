"""Every ForeSite route, answered from contracts/fixtures/ until its owner's real router lands.

Each stub response carries the header `X-ForeSite-Fixture: true`, and the web app labels it as sample
data. To replace a stub, include your router before `stubs.router` in api/main.py (the first matching
route wins) and delete the stub here in the same PR.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Response

from site_profile import router as site_profile_routes

from api.contracts import (
    ActionItem,
    ActionItemUpdate,
    Case,
    ChatRequest,
    ChatResponse,
    LayerCatalogEntry,
    LayerFeatureCollection,
    NoteCreate,
    PatternScore,
    PinCreate,
    Project,
    ProjectCreate,
    SearchResult,
    SimilarCases,
    SiteProfile,
    StructuralModel,
    EarlyWarning,
)

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"
FIXTURE_HEADER = "X-ForeSite-Fixture"

router = APIRouter(prefix="/api")


@lru_cache(maxsize=None)
def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def sample(response: Response, name: str):
    response.headers[FIXTURE_HEADER] = "true"
    return fixture(name)


@router.get("/layers", response_model=list[LayerCatalogEntry])
def list_layers(response: Response):
    return sample(response, "layer_catalog")


@router.get("/layers/{layer_id}", response_model=LayerFeatureCollection)
def layer_features(layer_id: str, response: Response, bbox: Optional[str] = None, as_of: Optional[str] = None):
    collection = sample(response, "layer_features")
    if collection["layer"]["layer_id"] != layer_id:
        raise HTTPException(404, f"No fixture for layer {layer_id}")
    return collection


@router.get("/search", response_model=list[SearchResult])
def search(q: str, response: Response):
    return sample(response, "search_results")


@router.get("/sites/{bbl}/profile", response_model=SiteProfile)
def site_profile(
    bbl: str,
    response: Response,
    job_type: Optional[str] = None,
    stage: Optional[str] = None,
    as_of: Optional[str] = None,
):
    # Real (Rishabh, PR 6): built from the site's public-record pull, not a fixture.
    return site_profile_routes.site_profile(bbl, response, job_type, stage, as_of)


@router.get("/sites/{bbl}/similar", response_model=SimilarCases)
def similar_cases(bbl: str, response: Response, hazard: Optional[str] = None, severity_min: Optional[int] = None):
    # Real (Rishabh, PR 6): ranked over the case library, or the case fixture until PR 3 merges.
    return site_profile_routes.similar_cases(bbl, response, hazard, severity_min)


@router.get("/sites/{bbl}/warnings", response_model=list[EarlyWarning])
def warnings(bbl: str, response: Response, as_of: Optional[str] = None):
    return sample(response, "warnings")


@router.get("/sites/{bbl}/pattern", response_model=PatternScore)
def pattern(bbl: str, response: Response):
    return sample(response, "pattern_score")


@router.get("/sites/{bbl}/actions", response_model=list[ActionItem])
def actions(bbl: str, response: Response, stage: Optional[str] = None):
    return sample(response, "actions")


@router.get("/cases", response_model=list[Case])
def list_cases(response: Response):
    return sample(response, "cases")


@router.get("/cases/{case_id}", response_model=Case)
def get_case(case_id: str, response: Response):
    for case in sample(response, "cases"):
        if case["id"] == case_id:
            return case
    raise HTTPException(404, f"No case {case_id}")


@router.post("/projects", response_model=Project)
def create_project(body: ProjectCreate, response: Response):
    return {**sample(response, "project"), **body.model_dump(), "items": [], "notes": [], "pins": []}


@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str, response: Response):
    return sample(response, "project")


@router.post("/projects/{project_id}/items", response_model=Project)
def add_items(project_id: str, body: list[ActionItem], response: Response):
    return sample(response, "project")


@router.patch("/projects/{project_id}/items", response_model=Project)
def update_items(project_id: str, body: list[ActionItemUpdate], response: Response):
    return sample(response, "project")


@router.post("/projects/{project_id}/notes", response_model=Project)
def add_note(project_id: str, body: NoteCreate, response: Response):
    return sample(response, "project")


@router.post("/projects/{project_id}/pins", response_model=Project)
def add_pin(project_id: str, body: PinCreate, response: Response):
    return sample(response, "project")


@router.post("/projects/{project_id}/model", response_model=Project)
def add_structural_model(project_id: str, body: StructuralModel, response: Response):
    return {**sample(response, "project"), "structural_model": body.model_dump()}


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, response: Response):
    return sample(response, "chat_response")
