"""`GET /api/sites/{bbl}/pattern`, made real. `api/stubs.py` calls `pattern` from the stub's place so
the generated API types do not change."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Response

from foresight_model import score
from site_profile import router as site_profile_routes


def pattern(bbl: str, response: Response, as_of: Optional[str] = None) -> dict:
    profile = site_profile_routes.get_profile(bbl, as_of=as_of)
    try:
        return score.pattern_score(profile)
    except score.ModelUnavailable as error:
        raise HTTPException(503, f"Couldn't load the pattern model. {error}") from error
