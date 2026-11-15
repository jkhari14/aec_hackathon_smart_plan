"""The ForeSite API.

    .venv/bin/uvicorn api.main:app --port 8000

Owners add their routers above `stubs.router`; the first matching route wins, so a real route replaces
its stub as soon as it is included. Delete the replaced stub in the same PR.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import stubs
from api.routers.cases_router import cases_router
from api.routers.chat.chat_app_context import app_context
from api.routers.chat.chat_router import chat_router_for
from api.routers.layers_router import layers_router
from api.routers.projects_router import projects_router
from api.routers.search_router import search_router
from api.routers.sites_router import sites_router
from early_warning import api as early_warning_api

app = FastAPI(
    title="ForeSite API",
    version="0.1.0",
    description="Public records, similar cases and early warnings for NYC sites. Not a DOB determination or engineering advice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[stubs.FIXTURE_HEADER, "ETag"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Owners' routers go here, above the stubs.
app.include_router(early_warning_api.router)

for owner_router in (layers_router, search_router, sites_router, cases_router, projects_router):
    app.include_router(owner_router)
# The chat reads each site part through the same function its route uses.
app.include_router(chat_router_for(app_context))
app.include_router(stubs.router)
