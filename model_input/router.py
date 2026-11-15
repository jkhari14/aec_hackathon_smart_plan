"""Structural model input for a project.

- `POST /api/projects/{id}/model` (JSON, the Revit reader's output): `api/stubs.py` calls `add_structural_model`
  from the stub's place, so the generated API types do not change.
- `POST /api/projects/{id}/model/drawing` (body: the PDF bytes, `Content-Type: application/pdf`): a drawing
  read by Claude, returned as a suggestion and not saved. Kept out of the OpenAPI schema (a binary body).
- `POST /api/projects/{id}/model/confirm` (`DrawingConfirm`): the reading the uploader confirmed. It becomes
  the project's model, the document is listed, and `actions.from_model` adds or flags checklist items for
  the roles it concerns, each with who added it and why.

A saved model is kept for the project and its site, so the site profile, similar cases and pattern score
use it from then on (`site_profile.router.get_profile` reads `model_input.store`).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from actions.from_model import model_actions
from api.contracts import DrawingConfirm, Project, StructuralModel
from api.routers.projects_router import project_store
from api.store.project_store import NotFound, ProjectStore, ProjectStoreError
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
async def add_drawing(project_id: str, request: Request):
    """Read a drawing and return the reading as a suggestion. Nothing is saved: the uploader checks it and
    sends it to `/model/confirm`, and only then does anyone's checklist change."""
    pdf = await request.body()
    try:
        model, evidence = drawing.read_drawing(pdf)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except drawing.DrawingUnavailable as error:
        raise HTTPException(503, f"Couldn't read the drawing. {error}") from error
    return {"model": model, "evidence": evidence,
            "note": "Read from the drawing by AI: a suggestion to check and confirm. Nothing is saved until you confirm."}


@router.post("/projects/{project_id}/model/confirm", response_model=Project)
def confirm_drawing(project_id: str, body: DrawingConfirm, response: Response,
                    projects: ProjectStore = Depends(project_store)):
    """The uploader confirmed a reading: keep it as the project's model (and the site's, for the profile),
    list the document, and add or flag the checklist items it calls for, each saying who and why."""
    model = StructuralModel.model_validate(body.model.model_dump()).model_dump()
    try:
        items = model_actions(model, body.document, body.by_role)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    try:
        project = projects.get_project(project_id)
        # Items first: the store refuses a role the project has no member for before anything is kept.
        projects.record_items(project_id, items, body.by_role)
        projects.set_structural_model(project_id, model)
        projects.add_pin(project_id, "document", body.slot, body.document, body.by_role, _pin_body(body, items))
    except NotFound as error:
        raise HTTPException(404, str(error)) from None
    except ProjectStoreError as error:
        raise HTTPException(422, str(error)) from None
    store.save(project_id, project["site_bbl"], model)
    snapshot, version = projects.snapshot(project_id)
    response.headers["ETag"] = f'"v{version}"'
    return snapshot


def _pin_body(body: DrawingConfirm, items: list[dict]) -> str:
    lines = [f"AI reading of {body.document}, checked and confirmed on the project. Not a DOB determination."]
    if body.evidence:
        lines.append(f"Reader's note: {body.evidence}")
    lines.append(f"Checklist items added or flagged: {len(items)}.")
    return "\n".join(lines)[:8000]
