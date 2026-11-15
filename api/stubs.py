"""Every ForeSite route, answered from contracts/fixtures/ until its owner's real router lands.

Each stub response carries the header `X-ForeSite-Fixture: true`, and the web app labels it as sample
data. To replace a stub, include your router before `stubs.router` in api/main.py (the first matching
route wins) and delete the stub here in the same PR.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Response

from api.contracts import (
    ChatRequest,
    ChatResponse,
)

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"
FIXTURE_HEADER = "X-ForeSite-Fixture"

router = APIRouter(prefix="/api")


@lru_cache(maxsize=None)
def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def sample(response: Response, name: str):
    response.headers[FIXTURE_HEADER] = "true"
    return fixture(name)


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, response: Response):
    return sample(response, "chat_response")
