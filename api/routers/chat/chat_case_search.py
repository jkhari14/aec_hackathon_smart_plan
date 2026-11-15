"""Search the past cases compared with this site, as the as-of view allows.

Like the record search, one search with two readers. The reader gets a part the server writes: how
many cases matched with the closest attached, or none found, or unknown when the similar cases could
not be loaded (never "none"). The model, through its tool, gets the matching cases' text so it can
cite them by id. A case dated on or after the as-of day cannot be reached.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from api.routers.chat.chat_models import AnswerPart, CasePart, NotFoundPart, UnknownPart
from api.routers.chat.chat_site_view import PIECES, SiteView

MAX_QUERY_CHARS = 60
MAX_QUERY_WORDS = 6
SOURCES_SHOWN = 3  # cases attached to the reader's part, closest first
CASES_FOR_MODEL = 10
HAZARDS = ("structural", "geotech", "fire", "flood", "contamination", "facade", "weather", "construction_safety")
SEVERITIES = {"0": "a signal", "1": "enforcement", "2": "an incident", "3": "catastrophic"}


@dataclass(frozen=True)
class CaseQuery:
    text: str = ""  # every word must appear in the case's title, summary, address, work types or conditions
    hazard: str = ""  # one of HAZARDS, or empty for all
    severity_min: str = ""  # "0" to "3", or empty for all


@dataclass
class CaseSearch:
    query: CaseQuery
    words: list[str]
    matches: list[dict] = field(default_factory=list)  # {"similar": .., "case": ..}, closest first
    loaded: bool = True


def _plain(text: str) -> str:
    return re.sub(r"[\s\-–_]+", " ", text.lower()).strip()


def query_problem(query: CaseQuery) -> Optional[str]:
    """Why this query cannot run, or None."""
    words = _plain(query.text).split()
    if len(query.text) > MAX_QUERY_CHARS or len(words) > MAX_QUERY_WORDS:
        return f"search words are at most {MAX_QUERY_WORDS} words and {MAX_QUERY_CHARS} characters."
    if '"' in query.text:
        return "search words cannot contain a quotation mark."
    if query.hazard and query.hazard not in HAZARDS:
        return f"'{query.hazard}' is not a hazard. The hazards are: {', '.join(HAZARDS)}."
    if query.severity_min and query.severity_min not in SEVERITIES:
        return "severity_min is 0, 1, 2 or 3, or empty."
    return None


def _case_text(case: dict) -> str:
    fields = [case.get(k) for k in ("id", "title", "address", "summary", "job_type", "work_types", "hazards", "conditions")]
    return _plain(" ".join(str(f) for f in fields if f))


def search(view: SiteView, query: CaseQuery) -> CaseSearch:
    """Run a query that `query_problem` passed."""
    found = CaseSearch(query=query, words=_plain(query.text).split(), loaded=view.piece("similar").status == "ok")
    for entry in view.cases:  # closest first, and already cut at the as-of day
        case = entry["case"]
        if query.hazard and query.hazard not in (case.get("hazards") or []):
            continue
        severity = case.get("severity")
        if query.severity_min and not (isinstance(severity, int) and severity >= int(query.severity_min)):
            continue
        text = _case_text(case)
        if all(word in text for word in found.words):
            found.matches.append(entry)
    return found


def _scope(view: SiteView, found: CaseSearch) -> str:
    query = found.query
    which = f" tagged {query.hazard.replace('_', ' ')}" if query.hazard else ""
    severe = f" of severity {query.severity_min} or higher" if query.severity_min else ""
    words = f' containing "{" ".join(found.words)}"' if found.words else ""
    before = f" dated before {view.as_of}" if view.as_of else ""
    return f"{which}{severe}{words}{before}"


def search_parts(view: SiteView, found: CaseSearch) -> list[AnswerPart]:
    """What the reader sees: the server's count with the closest cases, or none found, or unknown."""
    piece = PIECES["similar"]
    if not found.loaded:
        return [UnknownPart(text="Unknown: the similar past cases could not be loaded, so nothing is known about them. "
                                 "This is not the same as none.", queried=[piece])]
    scope = _scope(view, found)
    if not found.matches:
        return [NotFoundPart(text=f"None found: no past case compared with this site{scope or ' is in the case library'}. "
                                  "The case library is not exhaustive.", queried=[piece])]
    count, shown = len(found.matches), found.matches[:SOURCES_SHOWN]
    text = (f"{count} past case{'' if count == 1 else 's'} compared with this site{scope}"
            f"{' is' if count == 1 else ' are'} in the case library.")
    if count > len(shown):
        text += f" The closest {len(shown)} are listed."
    text += " A match is a likeness to a past case, not a prediction for this site."
    return [CasePart(text=text, sources=[view.items[f"case:{entry['case']['id']}"].source for entry in shown])]


def search_text_for_model(view: SiteView, found: CaseSearch) -> str:
    """What the model's tool returns: matching cases it may cite by id."""
    if not found.loaded:
        return "NOT LOADED: the similar past cases could not be loaded. Nothing is known about them; this is not none."
    shown = found.matches[:CASES_FOR_MODEL]
    lines = [f"{len(found.matches)} past case(s) match{_scope(view, found)}"
             + (f"; the closest {len(shown)} are below." if len(found.matches) > len(shown) else ".")]
    lines += [view.case_line(entry) for entry in shown]
    lines.append("Cite a case by its id in a statement. To tell the reader how many matched, or that none did, add a "
                 "case_search item with the same fields: the server writes that sentence.")
    return "\n".join(lines)
