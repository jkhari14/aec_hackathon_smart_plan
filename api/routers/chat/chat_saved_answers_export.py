"""Writes the answers the web app shows when it cannot reach the API at all.

Each saved answer is built now, from the site's data, through the same checks as any other answer,
and stored in the shared contract's ChatResponse shape. No model is called. Run it again whenever
the sample site's data or the chat's wording changes (a test fails until the file is up to date):

    python -m api.routers.chat.chat_saved_answers_export
"""

import json
from pathlib import Path

from api.routers.chat import chat_service
from api.routers.chat.chat_answer_build import notice, plain_text
from api.routers.chat.chat_contract_map import to_contract
from api.routers.chat.chat_fixture_context import fixture_context
from api.routers.chat.chat_models import ChatRequest
from api.routers.chat.chat_site_context import ContextLoader

SAVED_ANSWERS_FILE = Path(__file__).resolve().parents[3] / "web" / "src" / "features" / "chat" / "chat_saved_answers.json"
SAMPLE_SITE_BBL = "3052110074"  # the site contracts/fixtures/ describes
SAMPLE_SITE_QUESTIONS = (
    "What early warnings are there for this site?",
    "What should the structural engineer do first?",
    "Are there similar past cases?",
    "How many ECB violations are on file?",
    "How many 311 requests are on file?",
)


def saved_answers(load_context: ContextLoader, bbl: str, questions: tuple[str, ...]) -> dict:
    """Raises ValueError for a question no prepared answer matches: a saved answer is never an empty one."""
    answers = []
    for number, question in enumerate(questions, start=1):
        answer = chat_service.answer(ChatRequest(bbl=bbl, question=question), load_context, None)
        if any(part.kind == "notice" and part.code == "mock_no_match" for part in answer.parts):
            raise ValueError(f"no prepared answer matches {question!r}")
        parts = [notice("saved_example") if part.kind == "notice" and part.code == "mock_answer" else part
                 for part in answer.parts]
        saved = answer.model_copy(update={"mode": "saved", "parts": parts, "plain_text": plain_text(parts)})
        answers.append({"id": f"saved-{number}", "question": question, "response": to_contract(saved).model_dump()})
    return {"site_bbl": bbl, "answers": answers}


def saved_answers_text() -> str:
    return json.dumps(saved_answers(fixture_context, SAMPLE_SITE_BBL, SAMPLE_SITE_QUESTIONS), indent=2) + "\n"


if __name__ == "__main__":
    SAVED_ANSWERS_FILE.write_text(saved_answers_text())
    print(f"wrote {SAVED_ANSWERS_FILE}")
