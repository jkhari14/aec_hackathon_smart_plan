"""The chat's routes. Mount with `app.include_router(chat_router)` in jahleel/api/preflight_api.py."""

import time
from collections import deque

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from jahleel.api.chat import chat_model_call, chat_service
from jahleel.api.chat.chat_models import (
    MAX_EARLIER_EXCHANGES, MAX_HISTORY_CHARS, MAX_QUESTION_CHARS, ChatAnswer, ChatRequest, ExampleQuestion,
)
from jahleel.api.chat.chat_saved_examples import examples_for

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# The key is the team's: one process answers at most this many live questions a minute.
LIVE_QUESTIONS_PER_MINUTE = 12
_recent_live: deque = deque()


class ChatSetup(BaseModel):
    """What a client needs before the first question."""

    live: bool
    examples: list[ExampleQuestion]
    max_question_chars: int = MAX_QUESTION_CHARS
    max_earlier_exchanges: int = MAX_EARLIER_EXCHANGES
    max_history_chars: int = MAX_HISTORY_CHARS


def _live_slot(now: float) -> bool:
    while _recent_live and now - _recent_live[0] > 60:
        _recent_live.popleft()
    if len(_recent_live) >= LIVE_QUESTIONS_PER_MINUTE:
        return False
    _recent_live.append(now)
    return True


@chat_router.get("/setup/{slug}", response_model=ChatSetup)
def chat_setup(slug: str) -> ChatSetup:
    return ChatSetup(live=chat_model_call.default_model() is not None, examples=examples_for(slug))


@chat_router.post("/answer", response_model=ChatAnswer)
def chat_answer(request: ChatRequest) -> ChatAnswer:
    """A question about one site, answered from its brief and web search. See jahleel/api/chat/README.md."""
    model = None if request.example_id else chat_model_call.default_model()
    if model is not None and not _live_slot(time.monotonic()):
        raise HTTPException(status_code=429, detail="Too many live questions this minute. Wait a moment and ask again.")
    try:
        return chat_service.answer(request, model)
    except (FileNotFoundError, ValueError):
        raise HTTPException(status_code=404, detail="No cached brief for that site.")
    except LookupError:
        raise HTTPException(status_code=404, detail="No such saved example for that site.")
