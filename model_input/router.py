"""Structural model input for a project.

- `POST /api/projects/{id}/model` (JSON, the Revit reader's output): `api/stubs.py` calls `add_structural_model`
  from the stub's place, so the generated API types do not change.
- `POST /api/projects/{id}/model/drawing` (body: the PDF bytes, `Content-Type: application/pdf`, optional
  `?bbl=`): a drawing read by Claude. Kept out of the OpenAPI schema until Jacob adds it to the contracts.

Either one is saved for the project and its site, so the site profile, similar cases and pattern score
use it from then on (`site_profile.router.get_profile` reads `model_input.store`).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response

from api.contracts import StructuralModel
from model_input import drawing, store
from model_input.revit import ModelInputError, read_revit

FIXTURE_HEADER = "X-ForeSite-Fixture"
PROJECT_FIXTURE = Path(__file__).resolve().parent.parent / "contracts" / "fixtures" / "project.json"

router = APIRouter(prefix="/api")


@lru_cache(maxsize=1)
def _sample_project() -> dict:
    return json.loads(PROJECT_FIXTURE.read_text())


def _project(project_id: str, response: Response) -> dict:
    """The project. Until Jahleel's store (PR 4) lands this is the sample project, labeled as sample data."""
    response.headers[FIXTURE_HEADER] = "true"
    return dict(_sample_project())


def _site_bbl(project: dict, project_id: str, bbl: Optional[str]) -> Optional[str]:
    if bbl:
        return bbl
    return project.get("site_bbl") if project.get("id") == project_id else None


def add_structural_model(project_id: str, body: StructuralModel, response: Response) -> dict:
    payload = body.model_dump()
    try:
        model = read_revit(payload) if payload["source"] == "revit" else StructuralModel.model_validate(payload).model_dump()
    except ModelInputError as error:
        raise HTTPException(422, str(error)) from error
    project = _project(project_id, response)
    store.save(project_id, _site_bbl(project, project_id, None), model)
    return {**project, "structural_model": model}


@router.post("/projects/{project_id}/model/drawing", include_in_schema=False)
async def add_drawing(project_id: str, request: Request, response: Response, bbl: Optional[str] = None):
    pdf = await request.body()
    try:
        model, evidence = drawing.read_drawing(pdf)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except drawing.DrawingUnavailable as error:
        raise HTTPException(503, f"Couldn't read the drawing. {error}") from error
    project = _project(project_id, response)
    store.save(project_id, _site_bbl(project, project_id, bbl), model)
    return {"project": {**project, "structural_model": model}, "evidence": evidence,
            "note": "Read from the drawing by AI: a suggestion for the structural engineer to confirm."}
