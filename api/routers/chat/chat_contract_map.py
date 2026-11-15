"""The chat's answer as the shared contract's ChatResponse, and the contract's request as the chat's own.

The chat works with richer shapes inside (every source of a part, the datasets a search covered).
The contract carries one source per part, so a part's first source goes in its fields and any
others are named in `source_name`.
"""

from typing import Optional

from api import contracts
from api.routers.chat.chat_models import AnswerPart, ChatAnswer, ChatRequest, PageAction

_KIND = {"record": "public_record", "case": "case", "warning": "warning", "action": "action", "lead": "web",
         "not_found": "not_found", "unknown": "unknown", "notice": "notice"}


def _strip(ref: str, prefix: str) -> str:
    return ref[len(prefix):] if ref.startswith(prefix) else ref


def _named(names: list[str]) -> Optional[str]:
    names = list(dict.fromkeys(name for name in names if name))
    return "; ".join(names[:3]) + (f"; and {len(names) - 3} more" if len(names) > 3 else "") if names else None


def _part(part: AnswerPart) -> contracts.ChatAnswerPart:
    name: Optional[str] = None
    url: Optional[str] = None
    record_id: Optional[str] = None
    if part.kind == "record":
        first = part.sources[0]
        name, url, record_id = _named([s.label for s in part.sources]), first.url, first.ref
    elif part.kind == "case":
        first = part.sources[0]
        reports = _named([report.name for report in first.reports])
        name = _named([s.title for s in part.sources]) + (f" (as publicly reported: {reports})" if reports else "")
        url, record_id = next((r.url for r in first.reports if r.url), None), _strip(first.ref, "case:")
    elif part.kind == "warning":
        first = part.sources[0]
        name, record_id = f"Early-warning rule: {first.title}", _strip(first.ref, "warning:")
    elif part.kind == "action":
        first = part.sources[0]
        name, record_id = _named([s.code_ref or "Action rules" for s in part.sources]), _strip(first.ref, "action:")
    elif part.kind == "lead":
        first = part.sources[0]
        name, url = _named([s.title or s.url for s in part.sources]), first.url
    elif part.kind in ("not_found", "unknown"):
        name, url = _named([q.name for q in part.queried]), None
    return contracts.ChatAnswerPart(kind=_KIND[part.kind], text=part.text, source_name=name, source_url=url, record_id=record_id)


def _action(action: PageAction, question: str) -> contracts.ChatAction:
    if action.type == "toggle_layer":
        return contracts.ChatAction(type="toggle_layer", payload={"layer_id": action.layer_id, "on": action.on, "name": action.name})
    if action.type == "fly_to":
        return contracts.ChatAction(type="fly_to", payload=action.model_dump(exclude={"type"}, exclude_none=True))
    # The page saves the pin (POST /api/projects/{id}/pins), as the person signed in: it adds ref_id and by_role.
    return contracts.ChatAction(type="pin", payload={"kind": "chat_answer", "project_id": action.project_id,
                                                     "target": action.target, "title": question[:120]})


def to_contract(answer: ChatAnswer) -> contracts.ChatResponse:
    """`offline` is true whenever no live model answered (mock mode, or a saved example)."""
    return contracts.ChatResponse(answer_parts=[_part(part) for part in answer.parts],
                                  actions=[_action(action, answer.question) for action in answer.actions],
                                  offline=answer.mode != "live")


def from_contract(body: contracts.ChatRequest) -> ChatRequest:
    """Raises pydantic.ValidationError when the request is over a cap or has no site: refused, never cut."""
    return ChatRequest.model_validate({
        "bbl": body.bbl or "", "question": body.question, "project_id": body.project_id, "as_of": body.as_of,
        "job_type": body.job_type, "stage": body.stage,
        "history": [{"question": turn.question, "answer": turn.answer} for turn in body.history]})
