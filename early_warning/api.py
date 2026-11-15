"""The sequence rules over a site's dated records, served two ways.

`warnings_for` is the warnings part of the sites router (api/routers/sites_router.py), which serves
GET /api/sites/{bbl}/warnings and checks the BBL and `as_of` first. `router` serves
GET /api/sites/{bbl}/warnings/checks: one entry per rule, so a rule that could not run is never read as
"no warning".
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Path

from api.contracts import EarlyWarning, WarningRuleCheck
from early_warning.rules import evaluate
from early_warning.site_pulls import SiteUnavailable, load_site

router = APIRouter(prefix="/api")
BBL = Path(pattern=r"^[1-5]\d{9}$", description="10-digit borough-block-lot")


def _run(bbl: str, as_of: Optional[date]):
    try:
        site = load_site(bbl)
    except SiteUnavailable as error:
        raise HTTPException(503, f"Couldn't load the public record for this lot, so no rule was checked: {error}")
    return evaluate(site, as_of)


def warnings_for(bbl: str, as_of: Optional[str] = None) -> list[EarlyWarning]:
    """Warnings from records dated before `as_of` (YYYY-MM-DD; default: everything pulled), most severe first."""
    return _run(bbl, date.fromisoformat(as_of) if as_of else None)[0]


@router.get("/sites/{bbl}/warnings/checks", response_model=list[WarningRuleCheck])
def site_warning_checks(bbl: str = BBL, as_of: Optional[date] = None):
    """One entry per rule: checked, couldn't be checked, or not applicable to this site."""
    return _run(bbl, as_of)[1]
