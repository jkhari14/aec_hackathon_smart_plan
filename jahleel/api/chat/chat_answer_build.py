"""A proposed answer (what the model submits) -> typed parts, plus the reasons anything was held back.

The model writes sentences and names what each one rests on. It never picks a part's kind, words a
count, or says something is absent: the kind comes from the items cited, and counts, "none found"
and "unknown" are written here from each dataset's status.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from jahleel.api.chat import chat_wording_checks
from jahleel.api.chat.chat_brief_view import BriefView
from jahleel.api.chat.chat_models import (
    AnswerPart, BriefSource, LeadPart, NotFoundPart, NoticePart, QueriedDataset, RecordPart, UnknownPart, WebSource,
)

MAX_ITEMS = 12
MAX_STATEMENT_CHARS = 700
MAX_GAP_CHARS = 140

NOTICES = {
    "not_a_determination": "PreFlight is a coordination aid. It does not determine code compliance, structural "
    "adequacy or safety: the licensed professionals on the project and the Department of Buildings do.",
    "names_withheld": "PreFlight leaves out the names of owners, applicants, contractors and permit holders.",
    "cause_not_established": "Nothing in the public record here establishes the cause of any incident. Where "
    "officials say a cause is under investigation, that is the state.",
    "out_of_scope": "That is outside what PreFlight covers: the public record for this site and the lots "
    "touching it, and the checklist of Building Code duties toward adjoining property.",
    "status_is_todays": "A record's status is the one published at the pull, not its status on an earlier date: "
    "the datasets keep only the current status.",
    "complaints_overlap": "311 requests and DOB complaints can be the same complaint and share no key, so their "
    "counts are never added.",
    "web_off_as_of": "Web search is off in an as-of view: the web holds what is known today, not what was "
    "knowable on that day.",
    "held_back": "Part of the draft answer was held back because it could not be tied to a source.",
    "after_as_of": "Some of this prepared answer is not shown: it rests on records dated on or after the as-of day.",
    "no_answer": "No answer could be drawn from the brief or the web for this question.",
    "saved_example": "A saved example, written ahead of time and checked against this brief. It is not a live answer, "
    "and it uses no web search.",
    "mock_answer": "A mock answer: no model was called. The question was matched by keyword to a prepared answer, "
    "which was checked against this brief. It uses no web search.",
    "mock_no_match": "No prepared answer matches this question, and the mock does not make one up. It can count "
    "records in a dataset, report checklist rows, and open the saved examples.",
    "live_failed": "The live model call did not complete, so this is a mock answer.",
}
# The codes a model may ask for. The rest are the server's own.
MODEL_NOTICES = ("not_a_determination", "names_withheld", "cause_not_established", "out_of_scope", "status_is_todays")


class ProposedItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["statement", "dataset_check", "gap", "notice"]
    text: str = ""
    refs: list[str] = Field(default_factory=list)
    bbl: str = ""
    dataset_key: str = ""
    notice: str = ""


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ProposedItem] = Field(min_length=1, max_length=MAX_ITEMS)


@dataclass(frozen=True)
class WebResult:
    url: str
    title: str
    page_age: Optional[str] = None


@dataclass
class Built:
    parts: list[AnswerPart] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)  # what to tell the model on its one retry
    after_as_of: int = 0  # items resting on records the as-of view leaves out


def _same_page(url: str) -> str:
    parts = urlsplit(url.strip())
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path.rstrip('/')}?{parts.query}"


def _is_official(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host.endswith(".gov") or host == "cityofnewyork.us" or host.endswith(".cityofnewyork.us")


def _statement(view: BriefView, item: ProposedItem, web: dict[str, WebResult], built: Built, where: str) -> None:
    text = item.text.strip()
    refs = list(dict.fromkeys(ref.strip().strip("[]") for ref in item.refs if ref.strip()))
    if not text or len(text) > MAX_STATEMENT_CHARS:
        built.problems.append(f"{where}: a statement needs text of at most {MAX_STATEMENT_CHARS} characters.")
        return
    if not refs:
        built.problems.append(f"{where}: no source. Every statement cites the brief items or the search result URLs it rests on.")
        return
    brief_sources, lead_sources, evidence, from_the_web = [], [], [view.shared_evidence], False
    for ref in refs:
        if ref.lower().startswith(("http://", "https://")):
            result = web.get(_same_page(ref))
            if result is None:
                built.problems.append(f"{where}: {ref} is not a URL the web search returned in this conversation.")
                return
            lead_sources.append(WebSource(url=result.url, title=result.title, page_age=result.page_age,
                                          official=_is_official(result.url)))
            from_the_web = True
        elif ref in view.items:
            cited = view.items[ref]
            (brief_sources if cited.trust == "brief" else lead_sources).append(cited.source)
            evidence.append(cited.evidence)
        else:
            built.after_as_of += ref in view.after_as_of
            built.problems.append(f"{where}: {ref} is not an item of this brief view.")
            return
    if brief_sources and lead_sources:
        built.problems.append(f"{where}: it cites both the brief and a lead (a web result or a reported document). "
                              "Split it: the reader sees the two under different labels.")
        return
    reasons = chat_wording_checks.statement_problems(text, None if from_the_web else " ".join(evidence),
                                                     is_lead=bool(lead_sources))
    if reasons:
        built.problems += [f"{where}: {reason}" for reason in reasons]
        return
    built.parts.append(RecordPart(text=text, sources=brief_sources) if brief_sources
                       else LeadPart(text=text, sources=lead_sources))


def _dataset_check(view: BriefView, item: ProposedItem, built: Built, where: str) -> None:
    dataset = view.datasets.get((item.bbl.strip(), item.dataset_key.strip()))
    if dataset is None:
        built.problems.append(f"{where}: the brief has no dataset '{item.dataset_key}' for lot '{item.bbl}'.")
        return
    queried, lot = [dataset.queried()], dataset.lot_label
    before = f" among records dated before {view.as_of}" if view.as_of and dataset.key != "pluto" else ""
    if dataset.status != "ok":
        why = "the query failed" if dataset.status == "error" else f"it was not queried ({dataset.reason or 'no reason given'})"
        built.parts.append(UnknownPart(text=f"Unknown: {dataset.name} for {lot}: {why}, so nothing is known. This is not zero.",
                                       queried=queried))
    elif not dataset.count and dataset.capped:
        # A capped pull lost its oldest records, so an empty as-of view cannot say "none".
        built.parts.append(UnknownPart(
            text=f"Unknown: {dataset.name} for {lot}{before}: the pull hit its row cap and its oldest records are "
                 "missing, so nothing is known for this view. This is not zero.", queried=queried))
    elif not dataset.count:
        built.parts.append(NotFoundPart(text=f"None found in {dataset.name} for {lot}{before}.", queried=queried))
    else:
        noun = "record" if dataset.count == 1 else "records"
        floor = "At least " if dataset.capped else ""
        cap = " The pull hit its row cap, so the oldest records are missing." if dataset.capped else ""
        built.parts.append(RecordPart(
            text=f"{floor}{dataset.count} {noun} in {dataset.name} for {lot}{before}.{cap}",
            sources=[BriefSource(type="dataset_count", ref=f"dataset:{dataset.bbl}:{dataset.key}", label=dataset.name,
                                 bbl=dataset.bbl, url=dataset.url)]))


def _gap(view: BriefView, item: ProposedItem, searched: bool, built: Built, where: str) -> None:
    topic = item.text.strip().rstrip(".")
    reasons = chat_wording_checks.statement_problems(topic, "", is_lead=False) if topic else ["a gap needs a topic."]
    if len(topic) > MAX_GAP_CHARS:
        reasons.append(f"a gap's topic is at most {MAX_GAP_CHARS} characters.")
    if reasons:
        built.problems += [f"{where}: {reason}" for reason in reasons]
        return
    names = {d.key: d.name for d in view.datasets.values()}
    scope = "the brief or the web results read for this answer" if searched else "what we queried"
    built.parts.append(NotFoundPart(text=f"Not found in {scope}: {topic}.",
                                    queried=[QueriedDataset(key=key, name=name) for key, name in names.items()]))


def notice(code: str) -> NoticePart:
    return NoticePart(code=code, text=NOTICES[code])


def build_parts(view: BriefView, proposed: object, web_results: list[WebResult], searched: bool = False) -> Built:
    built = Built()
    try:
        proposal = Proposal.model_validate(proposed)
    except ValidationError as error:
        built.problems.append(f"the answer did not fit the tool's shape ({error.error_count()} problems): "
                              f"1 to {MAX_ITEMS} items, each with every field.")
        return built
    web = {_same_page(result.url): result for result in web_results}
    for number, item in enumerate(proposal.items, start=1):
        where = f"item {number}"
        if item.kind == "statement":
            _statement(view, item, web, built, where)
        elif item.kind == "dataset_check":
            _dataset_check(view, item, built, where)
        elif item.kind == "gap":
            _gap(view, item, searched, built, where)
        elif item.notice in MODEL_NOTICES:
            built.parts.append(notice(item.notice))
        else:
            built.problems.append(f"{where}: '{item.notice}' is not a notice. Use one of: {', '.join(MODEL_NOTICES)}.")
    checked = {source.ref.rsplit(":", 1)[-1] for part in built.parts if part.kind == "record"
               for source in part.sources if source.type == "dataset_count"}
    checked |= {q.key for part in built.parts if part.kind in ("not_found", "unknown") for q in part.queried if q.bbl}
    if {"dob_complaints", "dob_311_requests"} <= checked:
        built.parts.append(notice("complaints_overlap"))
    return built


def without_repeats(parts: list[AnswerPart]) -> list[AnswerPart]:
    """Each notice once, in the order first seen."""
    seen, kept = set(), []
    for part in parts:
        if part.kind == "notice":
            if part.code in seen:
                continue
            seen.add(part.code)
        kept.append(part)
    return kept


def plain_text(parts: list[AnswerPart]) -> str:
    """One text for a voice client: each part says where it came from, and links are left out."""
    lines = []
    for part in parts:
        if part.kind == "record":
            lines.append(f"From the public record: {part.text}")
        elif part.kind == "lead":
            web = any(source.type == "web_result" for source in part.sources)
            lines.append(("From the web, not checked by us: " if web else "Reported by a public source, not read by us: ") + part.text)
        else:
            lines.append(part.text)
    return "\n".join(lines)
