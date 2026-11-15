# ForeSite chat

`POST /api/chat`: a question about one site, answered in **parts** that each say where they came
from, plus **actions** for the page to carry out. Ported from the reference in `jahleel/api/chat/`
(its README explains the design at length); this file covers what is different here.

**State: wired in, answering in mock mode.** `POST /api/chat` in `api/main.py` is this chat, and it
returns the shared contract's `ChatResponse`. It reads each site part through the function that
part's route answers from, so it shows real data where an owner's module has landed and the labelled
sample elsewhere. No contract carries a site's list of records, so a record search answers "unknown",
not "none found". The contract's `ai_suggestion` and `user_input` kinds are not produced: every part
here rests on a source or is a fixed server line.

## Status: no model has answered yet

**No request from this chat has ever reached a model**: not in a test, not by hand, not in a deploy.
Every answer it has given is a mock answer (the server matched the question by keyword and answered
from the site's data) or a saved answer (the web panel, with no server). Both say so on the answer.
The web panel is also not mounted in the app shell yet, so the running app shows no chat today.

The plan for the first live call, with what to check and what to do when it fails, is
`chat_first_live_call.md`. The key and any spend are the key holder's call.

**What a mock answer and a live answer share.** These run, and are tested, on every mock answer:
loading the site through the app's own site functions; the as-of view; `build_parts`, which decides
each part's kind from what it cites and writes every count, "none found" and "unknown"; the wording
checks; the page-action checks; the notices added for a question asking for a verdict, a forecast or
a name; the mapping to the contract; the sample-data header.

**What only a live answer uses, and how far each piece has run:**

| Piece | How far it has run |
|---|---|
| The instructions and the site's reading text | Built in tests. Never read by a model |
| One correction round; a web statement shown as a lead; a failed call falling back to a labelled mock | Against a scripted stand-in for the whole model (`tests/chat_test_support.ScriptedModel`) |
| The request loop: a tool call, its result sent back, the answer taken | Once, against a fake SDK client returning canned responses |
| Reading web search results off a response | Never run. The scripted stand-in hands results in directly |
| The stop reasons `refusal`, `max_tokens` and `pause_turn`; the retry without the fallback option after a 400 | Never run. No test |
| The limit of 12 live questions a minute | Never run. No test. It applies only when a model is available |
| The request itself: model id, effort, the web search tool version, the fallback option, three strict tools | Never sent. The pinned SDK accepts the parameter names; whether the API accepts the values is unknown |
| Token and search counts | Counted for each live answer, then dropped: not logged and not in the response |

## Which mode is running

`GET /api/chat/setup` returns `"live": true` only when all three hold: `FORESITE_CHAT_LIVE` is not `0`,
a key is in the server's environment (`ANTHROPIC_API_KEY`), and the `anthropic` package can be
imported. Otherwise it returns `"live": false`, and it does **not** say which of the three is missing.
To tell them apart on the server: read `FORESITE_CHAT_LIVE`, check that the key variable is set
(without printing it), and run `python -c "import anthropic"`.

| What the reader sees | Meaning |
|---|---|
| "· offline answers" in the panel's title bar | `/api/chat/setup` said `live: false`, or could not be reached |
| "Offline answer: no model was called" under an answer, and the mock notice as its first line | A mock answer: `"offline": true` in the response |
| The same, with "The live model call did not complete, so this is a mock answer." first | The server is live, this call failed, and the answer is a mock. The reason is in the server log only |
| "Saved answer: the chat server could not be reached" | No server answered: an answer saved ahead of time, for the sample site only |
| None of these | A model answered: `"offline": false` |

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

**Mock mode:** a typed question is matched by keyword to a search, a count, the warnings, the action
items or a page action, through the same checks, and is labeled as a mock. A question nothing matches
is answered with a line saying so and what the mock can do; it never makes an answer up.

**No server:** the web chat panel shows answers saved ahead of time for the sample site
(`chat_saved_answers_export.py` writes them into `web/src/features/chat/`, built from the site's data
through the same checks and labeled as saved). They are redone for the demo sites once those are picked.

## What it reads

One function, `(bbl, job_type, stage, as_of) -> SiteContext` (`chat_site_context.py`), passed to
`chat_router_for(...)` in `api/main.py`. That function is `app_context` (`chat_app_context.py`): it
reads the profile, similar cases, warnings and action items through `load_site_part` in
`sites_router.py`, the same function each site route answers from, and the layer list through
`load_layer_catalog`. So the chat and the page cannot disagree about what is on record, and an
owner's module that lands is picked up by the chat with no change here.

- A part that is still the labelled sample describes the sample site only. For any other lot it is
  "not available", and a question about it is answered "unknown": sample data is never shown as
  another site's. An answer resting on sample data carries the `X-ForeSite-Fixture` header.
- A part that fails to load is a failure with its reason, never an empty list.
- With no profile for the lot, the chat answers 404 rather than guess.
- **Early-warning rule checks** (`SiteContext.warning_checks`): when a rule could not run, "no warnings"
  is answered "unknown", a count of warnings is "at least", and warnings cited without a count carry a
  line saying some rules were not checked. The chat is ready for this, but `app_context` does not fill
  it yet: the rule-checks contract and route have landed on `main` since, and `load_site_part` has no
  part for them. Until it is wired, an empty warnings list reads "none found".

Every piece that can fail to load is a `Loaded` with a status, because "could not load" must never
reach the chat as an empty list.

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
chat_app_context.py    the site as the app's own site functions serve it (what the app mounts)
chat_fixture_context.py the sample site from contracts/fixtures/ (the saved answers are built from it)
chat_router.py         POST /api/chat, GET /api/chat/setup, 12 live questions a minute
chat_first_live_call.md  the plan for the first live model call (not done)
```

Tests: `python -m unittest discover -s tests -t .` (`tests/test_chat_core.py`, `tests/test_chat_service.py`,
`tests/test_chat_saved_answers.py`, `tests/test_chat_app_context.py`; offline, a scripted model, no key).

Settings, all read from the server's environment: `ANTHROPIC_API_KEY` (the server only; never in the
repo or the web build), `FORESITE_CHAT_LIVE=0` to keep mock mode even with a key, `FORESITE_CHAT_MODEL`
(default `claude-opus-5-5`), `FORESITE_CHAT_EFFORT` (default `medium`).

## Limits

- No contract carries a site's list of records, so the record search and as-of counts answer "unknown"
  until one does. Dataset counts are the site profile's own.
- One source per part on the wire: a part resting on several records names them in `source_name` and
  links the first.
- The word-list checks catch plain phrasings and miss others. A person's name cannot be detected in code.
- The searches match words, not meaning.
- The web chat panel (`web/src/features/chat/`) and project panel (`web/src/features/project/`) are not
  mounted in the app shell yet, and are still on the placeholder tokens, not the design system.
- The web chat panel calls `/api/chat` as a relative path, so a web app deployed on a different host
  from the API cannot reach the chat (it offers the saved answers) until the panel uses `VITE_API_BASE`
  as the shared client does.
