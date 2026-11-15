"""Every ForeSite route, answered from contracts/fixtures/ until its owner's real router lands.

Each stub response carries the header `X-ForeSite-Fixture: true`, and the web app labels it as sample
data. To replace a stub, include your router before `stubs.router` in api/main.py (the first matching
route wins) and delete the stub here in the same PR.

One stub is left, warnings/checks, until PR 7 lands. The router stays mounted, and the helpers below
are used by routers that still answer from a fixture until their data lands.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Response

from api.contracts import WarningRuleCheck

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"
FIXTURE_HEADER = "X-ForeSite-Fixture"

router = APIRouter(prefix="/api")


@lru_cache(maxsize=None)
def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def sample(response: Response, name: str):
    response.headers[FIXTURE_HEADER] = "true"
    return fixture(name)


@router.get("/sites/{bbl}/warnings/checks", response_model=list[WarningRuleCheck])
def warning_checks(bbl: str, response: Response, as_of: Optional[str] = None):
    return sample(response, "warning_checks")
