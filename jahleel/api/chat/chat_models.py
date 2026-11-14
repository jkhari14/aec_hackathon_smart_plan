"""The chat's request and answer shapes.

An answer is a list of parts, and a part's kind says where it came from. The kinds are separate
types on purpose: a `record` part can only hold items of the brief, and a `lead` part can only hold
a web result or a document a public source reports, so a web page can never be shown as a record.
"""

from datetime import date
from typing import Annotated, Literal, Optional, Union
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from jahleel.api.brief.brief_models import ProjectType

MAX_QUESTION_CHARS = 1000
MAX_EARLIER_EXCHANGES = 8
MAX_EARLIER_ANSWER_CHARS = 4000
MAX_HISTORY_CHARS = 12000


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- the request ----


class Exchange(_Closed):
    """One earlier question and the text of the answer the reader saw."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    answer: str = Field(max_length=MAX_EARLIER_ANSWER_CHARS)


class ChatRequest(_Closed):
    """Over any limit the request is refused (HTTP 422), never cut to fit."""

    slug: str = Field(max_length=80)
    project_type: ProjectType = "excavation_next_to_existing"
    as_of: Optional[date] = Field(None, description="The page's as-of day: nothing dated on or after it is used.")
    history: list[Exchange] = Field(default_factory=list, max_length=MAX_EARLIER_EXCHANGES)
    question: str = Field("", max_length=MAX_QUESTION_CHARS)
    example_id: Optional[str] = Field(None, max_length=60, description="Ask for a saved example instead of a live answer.")

    @model_validator(mode="after")
    def _has_a_question_and_fits(self) -> "ChatRequest":
        if not self.question.strip() and not self.example_id:
            raise ValueError("a question or an example_id is required")
        size = sum(len(turn.question) + len(turn.answer) for turn in self.history)
        if size > MAX_HISTORY_CHARS:
            raise ValueError(f"the conversation is over {MAX_HISTORY_CHARS} characters: start a new chat")
        return self


# ---- sources ----


class BriefSource(_Closed):
    """An item of the brief. Its link is the brief's own, never one the model wrote."""

    type: Literal["public_record", "requirement", "lot_facts", "dataset_count"]
    ref: str
    label: str
    detail: Optional[str] = None
    date: Optional[str] = None
    bbl: Optional[str] = None
    url: Optional[str] = None


class ReportedSource(_Closed):
    """A document a public source reports and nobody here has read (a lead already in the brief)."""

    type: Literal["reported_document"] = "reported_document"
    ref: str
    reported_by: str
    document: str
    url: Optional[str] = None
    reported_on: Optional[str] = None
    document_date: Optional[str] = None


class WebSource(_Closed):
    """A web search result the model received in this call."""

    type: Literal["web_result"] = "web_result"
    url: str
    title: str
    page_age: Optional[str] = None
    official: bool = Field(description="The host is a city, state or federal government site. A hint about the host only.")

    @field_validator("url")
    @classmethod
    def _is_a_web_address(cls, url: str) -> str:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ValueError("not a web address")
        return url


class QueriedDataset(_Closed):
    key: str
    name: str
    bbl: Optional[str] = None
    url: Optional[str] = None


# ---- answer parts ----


class RecordPart(_Closed):
    """Rests on the brief: public records, checklist rows, PLUTO lot facts or a dataset count."""

    kind: Literal["record"] = "record"
    text: str
    sources: list[BriefSource] = Field(min_length=1)


class LeadPart(_Closed):
    """From the web or a reported document. Not checked by us; never evidence."""

    kind: Literal["lead"] = "lead"
    text: str
    sources: list[Annotated[Union[WebSource, ReportedSource], Field(discriminator="type")]] = Field(min_length=1)


class NotFoundPart(_Closed):
    """Queried and nothing found, with what was queried named."""

    kind: Literal["not_found"] = "not_found"
    text: str
    queried: list[QueriedDataset] = Field(min_length=1)


class UnknownPart(_Closed):
    """A query failed or was skipped: nothing is known. Never zero."""

    kind: Literal["unknown"] = "unknown"
    text: str
    queried: list[QueriedDataset] = Field(min_length=1)


NoticeCode = Literal[
    "not_a_determination", "names_withheld", "cause_not_established", "out_of_scope", "status_is_todays",
    "complaints_overlap", "web_off_as_of", "held_back", "after_as_of", "no_answer", "saved_example",
    "mock_answer", "mock_no_match", "live_failed",
]


class NoticePart(_Closed):
    """A status line the server wrote. The model can ask for one by code; it cannot word one."""

    kind: Literal["notice"] = "notice"
    code: NoticeCode
    text: str


AnswerPart = Annotated[Union[RecordPart, LeadPart, NotFoundPart, UnknownPart, NoticePart], Field(discriminator="kind")]


class ExampleQuestion(_Closed):
    id: str
    question: str


class ChatUsage(_Closed):
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    web_searches: int = 0


class ChatAnswer(_Closed):
    mode: Literal["live", "saved", "mock"] = Field(
        description="live: a model answered now. saved: an example written ahead of time, checked against this "
        "brief. mock: no model was called (no key on the server, or the call failed); the question was matched by "
        "keyword to a prepared answer, and `examples` lists what else can be opened when nothing matched.")
    question: str
    parts: list[AnswerPart]
    plain_text: str = Field(description="The parts as one text, each prefixed by where it came from. For a voice client.")
    as_of: Optional[str] = None
    web_search: Literal["used", "not_used", "off_as_of", "off"]
    examples: list[ExampleQuestion] = Field(default_factory=list)
    usage: Optional[ChatUsage] = None
