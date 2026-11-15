"""Projects: create one, read it (ETag = version, for polling), add or update items, notes, pins, the model.

There are no accounts: each tab acts as a role, and the store refuses a note, pin or owner in a role the
project has no member for. Bodies are the contract models; the store checks caps, so this file only
maps its errors to HTTP and returns the whole project.
"""

import os
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.contracts import ActionItem, ActionItemUpdate, NoteCreate, PinCreate, Project, ProjectCreate, StructuralModel
from api.store.project_store import UNCHANGED, NotFound, ProjectStore, ProjectStoreError

_DEFAULT_DB = Path(__file__).resolve().parents[1] / "store" / "data" / "projects.sqlite"  # gitignored

projects_router = APIRouter(prefix="/api/projects")


@lru_cache(maxsize=1)
def project_store() -> ProjectStore:
    return ProjectStore(os.environ.get("FORESITE_PROJECTS_DB", _DEFAULT_DB))


def _run(action, *args):
    try:
        return action(*args)
    except NotFound as error:
        raise HTTPException(404, str(error)) from None
    except ProjectStoreError as error:
        raise HTTPException(422, str(error)) from None


def _etag(version: int) -> str:
    return f'"v{version}"'


def _answer(response: Response, store: ProjectStore, project_id: str) -> dict:
    """The whole project, with the ETag of the very version it shows."""
    project, version = _run(store.snapshot, project_id)
    response.headers["ETag"] = _etag(version)
    return project


@projects_router.post("", response_model=Project)
def create_project(body: ProjectCreate, response: Response, store: ProjectStore = Depends(project_store)):
    members = [member.model_dump() for member in body.members]
    project = _run(store.create_project, body.name, body.site_bbl, body.stage, members)
    return _answer(response, store, project["id"])


@projects_router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, request: Request, response: Response, store: ProjectStore = Depends(project_store)):
    # A tab polls with If-None-Match; while nothing has changed it gets 304 and no body. Read from the
    # request rather than declared, so the published API stays the stubs'.
    etag = _etag(_run(store.version, project_id))
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return _answer(response, store, project_id)


@projects_router.post("/{project_id}/items", response_model=Project)
def add_items(project_id: str, body: list[ActionItem], response: Response, store: ProjectStore = Depends(project_store)):
    # Adds the site's action items; one already on the project keeps its status and owner.
    _run(store.add_items, project_id, [item.model_dump() for item in body])
    return _answer(response, store, project_id)


@projects_router.patch("/{project_id}/items", response_model=Project)
def update_items(project_id: str, body: list[ActionItemUpdate], response: Response,
                 store: ProjectStore = Depends(project_store)):
    # All or nothing. owner_role sent as null unassigns the item; left out, it stays as it is.
    updates = [{"id": update.id, "status": update.status,
                "owner_role": update.owner_role if "owner_role" in update.model_fields_set else UNCHANGED}
               for update in body]
    _run(store.update_items, project_id, updates)
    return _answer(response, store, project_id)


@projects_router.post("/{project_id}/notes", response_model=Project)
def add_note(project_id: str, body: NoteCreate, response: Response, store: ProjectStore = Depends(project_store)):
    _run(store.add_note, project_id, body.author_role, body.text)
    return _answer(response, store, project_id)


@projects_router.post("/{project_id}/pins", response_model=Project)
def add_pin(project_id: str, body: PinCreate, response: Response, store: ProjectStore = Depends(project_store)):
    _run(store.add_pin, project_id, body.kind, body.ref_id, body.title, body.by_role, body.body)
    return _answer(response, store, project_id)


@projects_router.post("/{project_id}/model", response_model=Project)
def add_structural_model(project_id: str, body: StructuralModel, response: Response,
                         store: ProjectStore = Depends(project_store)):
    # The Revit reader's model, checked against the StructuralModel contract, kept on the project.
    _run(store.set_structural_model, project_id, body.model_dump())
    return _answer(response, store, project_id)
