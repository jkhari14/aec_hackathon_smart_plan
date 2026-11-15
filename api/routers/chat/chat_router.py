"""The chat's routes. `chat_router_for(load_context)` returns the router to mount in the app:
`POST /api/chat` (a question about one site) and `GET /api/chat/setup` (what a client needs first).
"""

import time
from collections import deque

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.routers.chat import chat_model_call, chat_service
from api.routers.chat.chat_models import (
    MAX_EARLIER_EXCHANGES, MAX_HISTORY_CHARS, MAX_QUESTION_CHARS, ChatAnswer, ChatRequest, ExampleQuestion,
)
from api.routers.chat.chat_site_context import ContextLoader, SiteContextUnavailable

# The key is the team's: one process answers at most this many live questions a minute.
LIVE_QUESTIONS_PER_MINUTE = 12


class ChatSetup(BaseModel):
    """What a client needs before the first question."""

    live: bool
    examples: list[ExampleQuestion] = []
    max_question_chars: int = MAX_QUESTION_CHARS
    max_earlier_exchanges: int = MAX_EARLIER_EXCHANGES
    max_history_chars: int = MAX_HISTORY_CHARS


def chat_router_for(load_context: ContextLoader) -> APIRouter:
    router = APIRouter(prefix="/api/chat", tags=["chat"])
    recent_live: deque = deque()

    def live_slot(now: float) -> bool:
        while recent_live and now - recent_live[0] > 60:
            recent_live.popleft()
        if len(recent_live) >= LIVE_QUESTIONS_PER_MINUTE:
            return False
        recent_live.append(now)
        return True

    @router.get("/setup", response_model=ChatSetup)
    def chat_setup() -> ChatSetup:
        return ChatSetup(live=chat_model_call.default_model() is not None)

    @router.post("", response_model=ChatAnswer)
    def chat_answer(request: ChatRequest) -> ChatAnswer:
        """A question about one site, answered in parts that each say where they came from."""
        model = None if request.example_id else chat_model_call.default_model()
        if model is not None and not live_slot(time.monotonic()):
            raise HTTPException(status_code=429, detail="Too many live questions this minute. Wait a moment and ask again.")
        try:
            return chat_service.answer(request, load_context, model)
        except SiteContextUnavailable:
            raise HTTPException(status_code=404, detail="No data could be loaded for that site.")
        except LookupError:
            raise HTTPException(status_code=404, detail="No such saved example for that site.")

    return router
