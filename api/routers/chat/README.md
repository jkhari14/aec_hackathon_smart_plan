# ForeSite chat

`POST /api/chat`: a question about one site, answered in **parts** that each say where they came
from, plus **actions** for the page to carry out. Ported from the reference in `jahleel/api/chat/`
(its README explains the design at length); this file covers what is different here.

**State: built against stand-in data.** The chat is written and tested against a made-up site shaped
like the shared contracts in `BUILD.md`. It is not wired into the app yet: that needs the contracts
and app skeleton (PR 0) and the site routes and project store (PR 4). No real model call has been made.

## What an answer holds

| Part kind | Rests on | Label for the reader |
|---|---|---|
| `record` | a public record, a dataset count, the site's facts | From the public record |
| `case` | past cases compared with this site | From the case library, as publicly reported |
| `warning` | an early-warning rule's result | An early-warning pattern, not a prediction |
| `action` | an action item from the action rules | An action item, not a determination |
| `lead` | a web search result | From the web, not checked by us |
| `not_found` | looked for and nothing found, with what was searched | Not found |
| `unknown` | a query or a load failed: nothing is known | Unknown. This is not zero |
| `notice` | a fixed line the server writes | (small print) |

The model never chooses a kind: the server derives it from the ids a statement cites, and a
statement citing two kinds of source is held back. Counts, search results, "none found" and
"unknown" are written by the server. A statement is also held back for a number that is not in its
source, a verdict, blame, a cause (except a past case's or a web result's, as reported), a
prediction, or a company name. One correction round, then what still fails is dropped and said.

**Actions** (`ChatAnswer.actions`), each checked before it is returned:
- `toggle_layer`: only a layer id the layer list has.
- `fly_to`: only an item of this view with a place (the site, a neighbor, a record, a case).
- `pin_answer`: only with an open project (`project_id` in the request). `target` is `this` or
  `previous`. The chat writes nothing itself: the page saves the pin, as the person signed in.

**As-of:** a record, past case or warning dated on or after the day is not in the view, the searches
or the model's reading text; neither is text added later or today's status; web search is off.

**No key:** the chat runs in mock mode. A typed question is matched by keyword to a search, a count,
the warnings, the action items or a page action, through the same checks, and is labeled as a mock.
Saved example answers are not written yet (they need the demo sites).

## What it needs from the rest of the app

One function, `(bbl, job_type, stage, as_of) -> SiteContext` (`chat_site_context.py`), passed to
`chat_router_for(...)` when the app mounts the route. A `SiteContext` holds the site profile, the
site's and touching lots' records with each dataset's status, the similar cases, the warnings, the
action items and the layer list. Every piece that can fail to load is a `Loaded` with a status,
because "could not load" must never reach the chat as an empty list.

## Files

```
chat_models.py         request, sources, part kinds, page actions
chat_site_context.py   the seam: what the chat reads about a site
chat_site_view.py      the site on the as-of day; items a statement may cite; the model's reading text
chat_answer_build.py   proposed answer -> checked parts and actions; server-written counts and notices
chat_wording_checks.py the number check and the tone word lists
chat_record_search.py  search the records: the reader's part and the model's tool text
chat_case_search.py    search the past cases, the same way
chat_tools.py          the tools the model may call (search_records, search_similar_cases)
chat_prompt.py         the instructions and the tool the model answers through
chat_model_call.py     the model call with web search and our tools
chat_mock_answers.py   mock mode
chat_service.py        live or mock: one answer
chat_router.py         POST /api/chat, GET /api/chat/setup, 12 live questions a minute
```

Tests: `python -m unittest discover -s tests -t .` (`tests/test_chat_core.py`, `tests/test_chat_service.py`;
offline, a scripted model, no key). Settings: `ANTHROPIC_API_KEY` (server only), `FORESITE_CHAT_LIVE=0`
to force mock mode, `FORESITE_CHAT_MODEL`, `FORESITE_CHAT_EFFORT`.

## Limits

- Stand-in data only so far; field names follow `BUILD.md` and may need small changes when the
  contracts land.
- The word-list checks catch plain phrasings and miss others. A person's name cannot be detected in code.
- The searches match words, not meaning.
- The chat panel and project panel (web) are not built yet: they wait on the design system.
