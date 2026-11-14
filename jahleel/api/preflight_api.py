"""PreFlight's API. Run from the repo root: .venv/bin/uvicorn jahleel.api.preflight_api:app --reload --port 8000"""

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from jahleel.api.brief.brief_build import build_brief, list_slugs
from jahleel.api.brief.brief_models import Brief, BriefListing, ProjectType

app = FastAPI(title="PreFlight", version="0.1.0")
# The Vite dev server; any other reader (Grasshopper, voice) calls from outside a browser.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"])


@app.get("/api/briefs", response_model=list[BriefListing])
def briefs() -> list[BriefListing]:
    out = []
    for slug in list_slugs():
        brief = build_brief(slug)
        out.append(BriefListing(slug=slug, address=brief.matched_label, project_type=brief.project_type))
    return out


@app.get("/api/briefs/{slug}", response_model=Brief)
def brief(
    slug: str,
    project_type: ProjectType = Query("excavation_next_to_existing"),
    as_of: Optional[date] = Query(None, description="Build the checklist from records dated before this day."),
) -> Brief:
    try:
        return build_brief(slug, project_type, as_of)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="No cached brief for that site.")
