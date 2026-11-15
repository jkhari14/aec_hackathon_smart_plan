"""Tools the model may call while it works on one question, besides web search and its answer tool.

A tool is a schema plus a function over the site view on screen. New tools plug in here: add the
schema and the function, and list it in `tools_for`. What a tool returns is text for the model
only; nothing reaches the reader except through the checked answer. Things the page does (showing
a layer, moving the map, pinning an answer) are not tools: they are actions on the answer, checked
in chat_answer_build.
"""

from dataclasses import dataclass
from typing import Callable

from api.routers.chat import chat_case_search, chat_record_search
from api.routers.chat.chat_case_search import HAZARDS, CaseQuery
from api.routers.chat.chat_record_search import RecordQuery
from api.routers.chat.chat_site_view import SiteView

MAX_TOOL_RUNS = 4  # per question


@dataclass(frozen=True)
class ClientTool:
    schema: dict
    run: Callable[[dict], str]


_TEXT = {"type": "string"}


def _strict(name: str, description: str, properties: dict) -> dict:
    return {"name": name, "description": description, "strict": True,
            "input_schema": {"type": "object", "properties": properties, "required": list(properties),
                             "additionalProperties": False}}


SEARCH_RECORDS_TOOL = _strict(
    "search_records",
    "Search the public records of the site and the lots touching it, in the view on screen. The SITE DATA lists only "
    "the newest records of each dataset; this reaches the rest. Returns matching records with their ids, which you "
    "may cite in statements. Use an empty string for any field you do not need.",
    {"text": {**_TEXT, "description": "Words that must all appear in the record's text or id, e.g. 'stop work' or "
              "'fence'. Up to 6 words. Empty to match every record in the other filters."},
     "bbl": {**_TEXT, "description": "One lot's BBL, or empty for the site and every touching lot."},
     "dataset_key": {**_TEXT, "description": "One dataset key as the SITE DATA names it, or empty for all."},
     "date_from": {**_TEXT, "description": "Earliest record date, YYYY-MM-DD, or empty."},
     "date_to": {**_TEXT, "description": "Latest record date, YYYY-MM-DD, or empty."}})

SEARCH_CASES_TOOL = _strict(
    "search_similar_cases",
    "Search the past cases compared with this site. The SITE DATA lists only the closest; this reaches the rest. "
    "Returns matching cases with their ids, which you may cite in statements. Use an empty string for any field "
    "you do not need.",
    {"text": {**_TEXT, "description": "Words that must all appear in the case's title, summary, address, work types "
              "or conditions, e.g. 'underpinning'. Up to 6 words, or empty."},
     "hazard": {**_TEXT, "description": "One hazard, or empty for all: " + ", ".join(HAZARDS) + "."},
     "severity_min": {**_TEXT, "description": "Lowest severity to include: 0 signal, 1 enforcement, 2 incident, "
                      "3 catastrophic. Empty for all."}})


def _fields(given: dict, names: tuple[str, ...]) -> dict:
    return {name: str(given.get(name) or "").strip() for name in names}


def _search_records(view: SiteView, given: dict) -> str:
    query = RecordQuery(**_fields(given, ("text", "bbl", "dataset_key", "date_from", "date_to")))
    problem = chat_record_search.query_problem(view, query)
    if problem:
        return f"The search was not run: {problem}"
    return chat_record_search.search_text_for_model(view, chat_record_search.search(view, query))


def _search_cases(view: SiteView, given: dict) -> str:
    query = CaseQuery(**_fields(given, ("text", "hazard", "severity_min")))
    problem = chat_case_search.query_problem(query)
    if problem:
        return f"The search was not run: {problem}"
    return chat_case_search.search_text_for_model(view, chat_case_search.search(view, query))


def tools_for(view: SiteView) -> list[ClientTool]:
    return [ClientTool(schema=SEARCH_RECORDS_TOOL, run=lambda given: _search_records(view, given)),
            ClientTool(schema=SEARCH_CASES_TOOL, run=lambda given: _search_cases(view, given))]
