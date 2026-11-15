"""Action rules by discipline (architect, structural, geotech, contractor). Owner: Hongyu (PR 8, 17).

`actions_for` is the function `api/routers/sites_router.py` looks for (SITE_SOURCES["actions"]),
so GET /api/sites/{bbl}/actions serves this module without that file being edited.
"""

from __future__ import annotations

import json
import pathlib
from typing import Optional

from actions.build import build_actions, group_by_discipline  # noqa: F401  (re-exported)

__all__ = ["actions_for", "build_actions", "group_by_discipline"]

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "contracts/fixtures/site_profile.json"


def _profile_for(bbl: str) -> tuple[Optional[dict], bool]:
    """The site's profile from PR 6 once it lands, else the PR 0 fixture.

    Returns (profile, is_sample). A missing site_profile module is 'not landed yet'; a module that
    is present but raises is a real failure and is allowed to propagate, so broken code is never
    shown as sample data.
    """
    try:
        from site_profile.router import site_profile  # type: ignore
    except ModuleNotFoundError:
        pass
    else:
        profile = site_profile(bbl)
        return (profile if isinstance(profile, dict) else profile.model_dump()), False

    if not _FIXTURE.exists():
        return None, False
    with _FIXTURE.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return (data[0] if isinstance(data, list) else data), True


def actions_for(bbl: str, stage: Optional[str] = None, response=None) -> list[dict]:
    """Action items for a site, grouped by discipline and life-safety first.

    Called by sites_router with the BBL, the checked `stage` and a Response. Until PR 6 lands the
    rules run against the fixture profile, not this site, so the answer is labelled sample data:
    without that header the UI would present fixture-derived actions as findings about the lot.
    """
    profile, is_sample = _profile_for(bbl)
    if profile is None:
        return []
    if is_sample and response is not None:
        from api.stubs import FIXTURE_HEADER
        response.headers[FIXTURE_HEADER] = "true"
    return build_actions(profile, stage)
