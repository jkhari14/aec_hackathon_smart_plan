# ForeSite chat

`POST /api/chat`: a question about one site, answered in **parts** that each say where they came
from, plus **actions** for the page to carry out. Ported from the reference in `jahleel/api/chat/`
(its README explains the design at length); this file covers what is different here.

**State: wired in, on sample data.** `POST /api/chat` in `api/main.py` is this chat, replacing the
stub, and it returns the shared contract's `ChatResponse`. Until the site routes are real (PR 4) it
reads the one sample site in `contracts/fixtures/` and marks every answer with the fixture header,
as the stubs do. The fixtures hold no list of the site's records, so a record search there answers
"unknown", not "none found". No real model call has been made.

This PR sits on a small contract change (its own PR): `ChatAnswerPart.kind` gains `warning`,
`action`, `not_found`, `unknown` and `notice`, and `ChatRequest` gains optional `job_type`, `stage`
and `history`. The contract's `ai_suggestion` and `user_input` kinds are not produced: every part
here rests on a source or is a fixed server line.

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

On the wire these are the contract's kinds (`record` is `public_record`, `lead` is `web`), with a
part's first source in `source_name`, `source_url` and `record_id` (`chat_contract_map.py`).

The model never chooses a kind: the server derives it from the ids a statement cites, and a
statement citing two kinds of source is held back. Counts, search results, "none found" and
"unknown" are written by the server, for a dataset and for the site's early warnings and action
items alike: a list that did not load is unknown, never none. A statement is also held back for a number that is not in its
source, a verdict, blame, a cause (except a past case's or a web result's, as reported), a
prediction, or a company name. One correction round, then what still fails is dropped and said.

**Actions** (`ChatAnswer.actions`), each checked before it is returned:
- `toggle_layer`: only a layer id the layer list has.
- `fly_to`: only an item of this view with a place (the site, a neighbor, a record, a case).
- `pin_answer` (`pin` on the wire): only with an open project (`project_id` in the request). `target`
  is `this` or `previous`. The chat writes nothing itself: the page saves the pin, as the person signed in.

**As-of:** a record, past case or warning dated on or after the day is not in the view, the searches
or the model's reading text; neither is text added later or today's status; web search is off.

**No key:** the chat runs in mock mode. A typed question is matched by keyword to a search, a count,
the warnings, the action items or a page action, through the same checks, and is labeled as a mock.

**No server:** the web chat panel shows answers saved ahead of time for the sample site
(`chat_saved_answers_export.py` writes them into `web/src/features/chat/`, built from the site's data
through the same checks and labeled as saved). They are redone for the demo sites once those are picked.

## What it needs from the rest of the app

One function, `(bbl, job_type, stage, as_of) -> SiteContext` (`chat_site_context.py`), passed to
`chat_router_for(...)` in `api/main.py`. Today that is `fixture_context`; the real one replaces it
when the site routes land. A `SiteContext` holds the site profile, the
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
chat_saved_answers_export.py  writes the web app's saved answers for the sample site
chat_service.py        live or mock: one answer
chat_contract_map.py   the chat's answer as the contract's ChatResponse; the contract's request as the chat's
chat_fixture_context.py the sample site from contracts/fixtures/, until the site routes are real
chat_router.py         POST /api/chat, GET /api/chat/setup, 12 live questions a minute
```

Tests: `python -m unittest discover -s tests -t .` (`tests/test_chat_core.py`, `tests/test_chat_service.py`,
`tests/test_chat_saved_answers.py`; offline, a scripted model, no key). Settings: `ANTHROPIC_API_KEY` (server only), `FORESITE_CHAT_LIVE=0`
to force mock mode, `FORESITE_CHAT_MODEL`, `FORESITE_CHAT_EFFORT`.

## Limits

- Sample data only so far: one site, no record list. The record search and as-of counts need the real
  site data.
- One source per part on the wire: a part resting on several records names them in `source_name` and
  links the first.
- The word-list checks catch plain phrasings and miss others. A person's name cannot be detected in code.
- The searches match words, not meaning.
- The web chat panel (`web/src/features/chat/`) and project panel (`web/src/features/project/`) are built on
  the placeholder tokens and are not mounted in the app shell yet.
