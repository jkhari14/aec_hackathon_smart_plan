"""One question in, one typed answer out.

The brief is built the same way the page builds it (same site, project type and as-of day, from the
cache: no second pull), so the chat and the screen cannot disagree about what is on record.
"""

import logging
import re
from typing import Optional

from jahleel.api.brief.brief_build import build_brief
from jahleel.api.chat import chat_mock_answers
from jahleel.api.chat.chat_answer_build import build_parts, notice, plain_text, without_repeats
from jahleel.api.chat.chat_brief_view import BriefView
from jahleel.api.chat.chat_models import AnswerPart, ChatAnswer, ChatRequest, ChatUsage
from jahleel.api.chat.chat_prompt import conversation, system_blocks
from jahleel.api.chat.chat_saved_examples import examples_for, saved_example

log = logging.getLogger("preflight.chat")

# A question that asks for a verdict or a name gets the matching notice whatever the model does.
_ASKS_VERDICT = re.compile(r"\b(?:safe|unsafe|safely|compliant|comply|complies|compliance|legal|illegal|fault|blame|"
                           r"negligen\w*|liable)\b", re.I)
_ASKS_NAME = re.compile(r"\bwho\b|\b(?:owner|contractor|applicant|engineer|architect|developer|landlord)'?s?\s+name\b|"
                        r"\bname of\b", re.I)


def answer(request: ChatRequest, model=None) -> ChatAnswer:
    """`model` is a chat_model_call.AnthropicChatModel, or None when live answers cannot run: the
    question then gets a mock answer (chat_mock_answers), labeled as one.

    Raises FileNotFoundError or ValueError for an unknown or malformed site, LookupError for an
    unknown saved example.
    """
    view = BriefView(build_brief(request.slug, request.project_type, request.as_of))
    if request.example_id:
        return _saved(request, view)
    if model is None:
        return _mock(request, view, [])
    try:
        return _live(request, view, model)
    except Exception as error:  # the demo must not crash on a failed call; the reason is logged, never shown
        log.warning("live chat call failed: %s: %s", type(error).__name__, error)
        return _mock(request, view, [notice("live_failed")])


def _live(request: ChatRequest, view: BriefView, model) -> ChatAnswer:
    question = request.question.strip()
    session = model.open(system_blocks(view), conversation(request.history, question), allow_web=view.as_of is None)
    turn = session.turn()
    built = build_parts(view, turn.proposal, turn.web_results, turn.searched)
    if built.problems:  # one correction round, with the reasons
        turn = session.turn(built.problems)
        built = build_parts(view, turn.proposal, turn.web_results, turn.searched)
    parts = _question_notices(question) + built.parts
    if built.problems:
        log.info("chat held back %d item(s): %s", len(built.problems), built.problems)
        parts.append(notice("held_back"))
    if all(part.kind == "notice" for part in built.parts):
        parts.append(notice("no_answer"))
    if view.as_of:
        parts.append(notice("web_off_as_of"))
    web = "off_as_of" if view.as_of else ("used" if turn.searched else "not_used")
    return _finish(request, view, "live", parts, web, session.usage)


def _question_notices(question: str) -> list[AnswerPart]:
    parts: list[AnswerPart] = []
    if _ASKS_VERDICT.search(question):
        parts.append(notice("not_a_determination"))
    if _ASKS_NAME.search(question):
        parts.append(notice("names_withheld"))
    return parts


def _mock(request: ChatRequest, view: BriefView, first: list[AnswerPart]) -> ChatAnswer:
    """No model: a prepared answer matched by keyword, through the same checks as a live one."""
    question = request.question.strip()
    parts = first + [notice("mock_answer")] + _question_notices(question)
    items = chat_mock_answers.propose(view, request.slug, question)
    if not items:
        return _finish(request, view, "mock", parts + [notice("mock_no_match")], "off", with_examples=True)
    built = build_parts(view, {"items": items}, [])
    parts += built.parts
    if built.after_as_of:
        parts.append(notice("after_as_of"))
    if len(built.problems) > built.after_as_of:
        log.warning("mock answer for %s out of step with the brief: %s", request.slug, built.problems)
        parts.append(notice("held_back"))
    return _finish(request, view, "mock", parts, "off")


def _saved(request: ChatRequest, view: BriefView) -> ChatAnswer:
    example = saved_example(request.slug, request.example_id or "")
    if example is None:
        raise LookupError(f"no saved example {request.example_id!r} for {request.slug!r}")
    built = build_parts(view, {"items": example["items"]}, [])
    parts = [notice("saved_example")] + built.parts
    if built.after_as_of:
        parts.append(notice("after_as_of"))
    if len(built.problems) > built.after_as_of:  # a saved example out of step with the brief: say so, and log it
        log.warning("saved example %s/%s no longer matches the brief: %s", request.slug, example["id"], built.problems)
        parts.append(notice("held_back"))
    return _finish(request, view, "saved", parts, "off", question=example["question"])


def _finish(request: ChatRequest, view: BriefView, mode: str, parts: list[AnswerPart], web: str,
            usage: Optional[ChatUsage] = None, question: Optional[str] = None, with_examples: bool = False) -> ChatAnswer:
    parts = without_repeats(parts)
    return ChatAnswer(mode=mode, question=question or request.question.strip(), parts=parts, plain_text=plain_text(parts),
                      as_of=view.as_of, web_search=web, usage=usage,
                      examples=examples_for(request.slug) if with_examples else [])
