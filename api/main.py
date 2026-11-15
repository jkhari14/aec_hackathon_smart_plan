"""The ForeSite API.

    .venv/bin/uvicorn api.main:app --port 8000

Owners add their routers above `stubs.router`; the first matching route wins, so a real route replaces
its stub as soon as it is included. Delete the replaced stub in the same PR.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import stubs
from model_input.router import router as model_input_router

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
    expose_headers=[stubs.FIXTURE_HEADER],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Owners' routers go here, above the stubs.

app.include_router(model_input_router)  # Rishabh, PR 13: drawing upload (not in the schema yet)

app.include_router(stubs.router)
