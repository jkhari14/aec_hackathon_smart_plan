"""Search the public records of the site and the lots touching it, as the as-of view allows.

One search, two readers. The reader of an answer gets a part the server writes: how many records
matched, or none found, or unknown where a dataset's query failed (never zero). The model, through
its search tool, gets the matching records' text so it can cite them by id. Both run over the same
view, so a search cannot reach a record dated on or after the as-of day or text written later.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from api.routers.chat.chat_site_context import SiteRecord
from api.routers.chat.chat_site_view import DatasetView, SiteView
from api.routers.chat.chat_models import AnswerPart, NotFoundPart, RecordPart, UnknownPart

MAX_QUERY_CHARS = 60
MAX_QUERY_WORDS = 6
SOURCES_SHOWN = 5  # records attached to the reader's part, newest first
RECORDS_FOR_MODEL = 20
_ISO_DAY = re.compile(r"\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class RecordQuery:
    text: str = ""  # every word must appear in the record's id or text; empty matches all
    bbl: str = ""  # one lot, or empty for the site and every touching lot
    dataset_key: str = ""  # one dataset, or empty for all
    date_from: str = ""  # ISO day, inclusive
    date_to: str = ""  # ISO day, inclusive


@dataclass
class RecordSearch:
    query: RecordQuery
    words: list[str]
    matches: list[SiteRecord] = field(default_factory=list)  # newest first
    searched: list[DatasetView] = field(default_factory=list)  # datasets whose records could be searched
    not_searched: list[DatasetView] = field(default_factory=list)  # query failed or skipped: nothing is known
    capped: list[DatasetView] = field(default_factory=list)  # hit the pull's row cap: oldest records missing


def _plain(text: str) -> str:
    """Lower case, with hyphens and odd spacing flattened, so 'stop-work' and 'STOP WORK' meet."""
    return re.sub(r"[\s\-–]+", " ", text.lower()).strip()


def query_problem(view: SiteView, query: RecordQuery) -> Optional[str]:
    """Why this query cannot run, or None."""
    words = _plain(query.text).split()
    if len(query.text) > MAX_QUERY_CHARS or len(words) > MAX_QUERY_WORDS:
        return f"search words are at most {MAX_QUERY_WORDS} words and {MAX_QUERY_CHARS} characters."
    if '"' in query.text:
        return "search words cannot contain a quotation mark."
    if query.bbl and query.bbl not in view.lot_labels:
        return f"this site has no lot '{query.bbl}'."
    keys = {key for (_, key) in view.datasets}
    if query.dataset_key and query.dataset_key not in keys:
        return f"this site has no record dataset '{query.dataset_key}'. The keys are: {', '.join(sorted(keys))}."
    for day in (query.date_from, query.date_to):
        if day and not _ISO_DAY.match(day):
            return f"'{day}' is not a date written YYYY-MM-DD."
    if not (words or query.dataset_key or query.date_from or query.date_to):
        return "a search needs words, a dataset or a date range."
    return None


def search(view: SiteView, query: RecordQuery) -> RecordSearch:
    """Run a query that `query_problem` passed."""
    found = RecordSearch(query=query, words=_plain(query.text).split())
    for (bbl, key), dataset in view.datasets.items():
        if (query.bbl and bbl != query.bbl) or (query.dataset_key and key != query.dataset_key):
            continue
        (found.searched if dataset.status == "ok" else found.not_searched).append(dataset)
        if dataset.capped:
            found.capped.append(dataset)
    in_scope = {(d.bbl, d.key) for d in found.searched}
    for record in view.records:  # newest first, and already cut at the as-of day
        if (record.bbl, record.dataset_key) not in in_scope:
            continue
        if (query.date_from and (record.date or "") < query.date_from) or (query.date_to and (record.date or "9") > query.date_to):
            continue
        text = _plain(f"{record.id} {view.record_text(record)}")
        if all(word in text for word in found.words):
            found.matches.append(record)
    return found


def _scope(view: SiteView, found: RecordSearch) -> str:
    query = found.query
    where = view.lot_labels[query.bbl] if query.bbl else "the site and the lots touching it"
    names = {d.name for d in found.searched + found.not_searched}
    which = f" in {next(iter(names))}" if query.dataset_key and names else ""
    dates = (f" dated {query.date_from} to {query.date_to}" if query.date_from and query.date_to
             else f" dated {query.date_from} or later" if query.date_from
             else f" dated {query.date_to} or earlier" if query.date_to else "")
    before = f" among records dated before {view.as_of}" if view.as_of else ""
    return f"for {where}{which}{dates}{before}"


def _names(datasets: list[DatasetView]) -> str:
    return "; ".join(f"{d.name} for {d.lot_label}" for d in datasets)


def search_parts(view: SiteView, found: RecordSearch) -> list[AnswerPart]:
    """What the reader sees: the server's count with the newest matches, or none found, plus unknowns."""
    quoted = f' "{" ".join(found.words)}"' if found.words else ""
    scope = _scope(view, found)
    cap = (f" {_names(found.capped)} hit the pull's row cap, so the oldest records could not be searched."
           if found.capped else "")
    parts: list[AnswerPart] = []
    if found.matches:
        count = len(found.matches)
        shown = found.matches[:SOURCES_SHOWN]
        verb = ("contains" if count == 1 else "contain") if found.words else ("matches" if count == 1 else "match")
        text = f"{'At least ' if found.capped else ''}{count} record{'' if count == 1 else 's'} {scope} {verb}{quoted}."
        if count > len(shown):
            text += f" The newest {len(shown)} are listed."
        parts.append(RecordPart(text=text + cap, sources=[view.items[r.id].source for r in shown]))
    elif found.searched:
        parts.append(NotFoundPart(text=f"None found: no record {scope} {'contains' if found.words else 'matches'}{quoted}.{cap}",
                                  queried=[d.queried() for d in found.searched]))
    if found.not_searched:
        parts.append(UnknownPart(
            text=f"Unknown: {_names(found.not_searched)} could not be searched because the query for it failed or was "
                 "skipped, so nothing is known there. This is not zero.",
            queried=[d.queried() for d in found.not_searched]))
    return parts


def search_text_for_model(view: SiteView, found: RecordSearch) -> str:
    """What the model's search tool returns: matching records it may cite by id."""
    shown = found.matches[:RECORDS_FOR_MODEL]
    lines = [f"{len(found.matches)} record(s) match {_scope(view, found)}"
             + (f"; the newest {len(shown)} are below." if len(found.matches) > len(shown) else ".")]
    lines += [f"[{r.id}] lot {r.bbl} | {r.date or 'undated'} | {view.items[r.id].source.detail}" for r in shown]
    if found.not_searched:
        lines.append(f"NOT SEARCHED (the query failed or was skipped; nothing is known, not zero): {_names(found.not_searched)}")
    if found.capped:
        lines.append(f"CAPPED (oldest records missing, so any count is a floor): {_names(found.capped)}")
    lines.append("Cite a record by its id in a statement. To tell the reader how many matched, or that none did, "
                 "add a record_search item with the same fields: the server writes that sentence.")
    return "\n".join(lines)
