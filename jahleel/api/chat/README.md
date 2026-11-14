# PreFlight chat: questions about one site, answered with sources

A chat panel beside the brief, and the endpoint behind it. It answers from two things only: the
**brief** the page already shows (the public records, the lots, the checklist rows) and **web
search**. There is no stored document library behind it: no code text, bulletins or filings are
indexed here. Part of the same proposal as [the app structure](../../README.md); it reads the brief
and changes nothing in `data_pull/`, `checklist/` or the brief itself.

PreFlight is a coordination aid. The chat does not decide code compliance, structural adequacy or
safety, and it says so when asked.

## What an answer is

`POST /api/chat/answer` returns a list of **parts**. Each part has a kind, and the kind says where
it came from:

| Kind | What it rests on | How the page draws it |
|---|---|---|
| `record` | items of the brief: a public record (by its id), a checklist row, a lot's PLUTO facts, or a dataset count | solid green edge, "From the public record", each source opens to its text and the query that returned it |
| `lead` | a web search result (by its URL), or a document the brief lists as reported but unread | dashed amber, "A lead · not checked by us", linked to the page |
| `not_found` | a dataset that was queried and returned nothing, or a topic neither the brief nor the search answered | grey, with the datasets queried |
| `unknown` | a dataset whose query failed or was skipped, or a capped dataset with nothing in view | dashed red, "This is not zero" |
| `notice` | a fixed line the server writes (not a determination, names withheld, web search off in a replay, and so on) | small italic line |

**The model never chooses a part's kind.** It proposes statements with the ids or URLs each rests
on, and the server decides the kind from those. A web result cannot be shown as a record because
nothing the model writes can make it one; the two are different types in `chat_models.py`, and a
`record` part cannot hold a web source.

## What the server checks before anything is shown

All in `chat_answer_build.py` and `chat_wording_checks.py`, with a test for each in `jahleel/tests/test_chat_*.py`.

- **No source, no statement.** A statement that cites nothing is held back.
- **A source must exist.** A brief id must be an item of the brief view; a URL must be one the web
  search returned during this question.
- **One kind of source per statement.** A statement citing both the brief and a lead is held back, so
  the reader never sees a web claim under the public-record label.
- **Numbers must be in the source.** Every run of digits in a `record` statement (a date, an id, a
  section number) has to appear in the items it cites.
- **The model cannot count or say "none".** Counts, "none found" and "unknown" are written by the
  server from each dataset's status. A dataset with status `error` reads "Unknown ... the query
  failed ... This is not zero"; a capped dataset reads "At least N".
- **Tone rules** (word lists, see the limits below): no verdict on compliance or safety, no blame, nothing
  about what would have changed an outcome, no cause from the public record (a lead may relay one
  "as reported"), no company names.
- **One correction round.** Held-back statements go back to the model once with the reasons. What
  still fails is dropped, and the answer says part of it was held back.

## The as-of view

When the page is on an as-of day, the chat uses the same rule as the checklist engine: dated before
that day.

- Records dated on or after the day are not in what the model reads and cannot be cited.
- Text written later (a stop-work mention, DOB's resolution of a 311 request, a filing's approval)
  appears only once its own date is before the day. Later dates inside checklist text are masked.
- Today's statuses are left out, since the datasets keep only the current status.
- Counts are of the records dated before the day, and say so.
- A lead whose report is dated on or after the day is not shown.
- **Web search is off**, because the web is today's knowledge. The answer says so.

## What it will not do

- Decide whether a project is compliant, safe, adequate or legal.
- Assign blame, state a cause, or say what would have prevented an incident.
- Name owners, applicants, contractors or companies (the prompt forbids it; company suffixes are also refused in code).
- Mark a checklist row done, or treat a web page or news report as proof.
- Answer from memory when neither the brief nor a search result supports a point: that becomes "not found".
- Read documents. It sees web search results, not the pages behind them, and no drawings or filings.

## Run it

The routes mount in the API with one line (see "Wiring"). With them mounted:

```bash
export ANTHROPIC_API_KEY=...        # the server only; never in the web app, never committed
.venv/bin/pip install anthropic     # without it, or without a key, the chat serves saved examples
.venv/bin/uvicorn jahleel.api.preflight_api:app --port 8000
.venv/bin/python -m unittest discover -s jahleel/tests -t .       # offline: a scripted model, no key
.venv/bin/python -m jahleel.api.chat.chat_saved_export            # after a brief change: the panel's offline copies
```

- `PREFLIGHT_CHAT_LIVE=0` turns live answers off even with a key.
- `PREFLIGHT_CHAT_MODEL` (default `claude-opus-5-5`) and `PREFLIGHT_CHAT_EFFORT` (default `medium`) change the model call.
- With the API down, the panel still opens the saved examples from `web/src/features/chat/saved/`.

**Cost, estimated and not measured:** roughly $0.10 to $0.25 a live question (the brief as input, the
answer, up to three searches). Follow-up questions on the same site within a few minutes reuse a
cached copy of the brief and cost less. Saved examples cost nothing.

## Calling it from somewhere else (voice, a script)

```
GET  /api/chat/setup/<slug>     -> {live, examples[{id, question}], max_question_chars, max_earlier_exchanges, max_history_chars}
POST /api/chat/answer
     {"slug": "2625-bedford-ave-brooklyn", "project_type": "excavation_next_to_existing",
      "as_of": null, "history": [{"question": "...", "answer": "..."}], "question": "..."}
     -> {mode, question, parts[], plain_text, as_of, web_search, examples[], usage}
```

- `plain_text` is the answer as lines to read aloud, each starting with where it came from ("From the
  public record:", "From the web, not checked by us:").
- `history` is the earlier questions and the answers as they were shown. Send `example_id` instead of
  `question` to get a saved example.
- `mode` is `live`, `saved`, or `unavailable` (no key, or the call failed; the parts say which).
- HTTP 422 means the question or history is over a cap, 429 that the per-minute limit was reached.

## Wiring

Three edits in files this folder does not own:

1. `jahleel/api/preflight_api.py`: `from jahleel.api.chat.chat_router import chat_router` and
   `app.include_router(chat_router)`. A browser client on another origin also needs `POST` and the
   `content-type` header allowed in the CORS line; the page itself goes through the Vite proxy.
2. `jahleel/web/src/app/preflight_app.tsx`:
   `<ChatPanel brief={brief} projectType={projectType} asOf={asOf} offline={offline} />`.
3. `jahleel/api/requirements.txt`: the `anthropic` package.

After the first, `brief_export` and `npm run types` add the chat's shapes to the generated types;
until then the panel uses hand-written ones in `chat_types.ts`.

## Files

```
jahleel/api/chat/
  chat_models.py          request, sources, the five part kinds, the caps
  chat_brief_view.py      the brief as the chat may use it on the as-of day; the model's reading text
  chat_answer_build.py    proposed items -> checked parts; server-written counts and notices
  chat_wording_checks.py  the number check and the tone word lists
  chat_prompt.py          the instructions and the one tool the model answers through
  chat_model_call.py      the model call with web search; pauses, refusals, one correction round
  chat_saved_examples.py  saved example answers for the two demo sites
  chat_saved_export.py    writes the panel's offline copies
  chat_service.py         saved, live or unavailable: one answer
  chat_router.py          the two routes and the per-minute limit
jahleel/web/src/features/chat/
  chat_panel.tsx, chat_answer_parts.tsx, chat_api.ts, chat_types.ts, saved/
```

## Limits

- **No live question has been run against a real model yet.** The tests use a scripted model, and the
  request was run through the real SDK against a local stand-in. Answer quality is not measured.
- **No stored conversations.** The conversation lives in the browser tab and is sent with each
  question; the server keeps nothing.
- **Hard caps, refused and never cut:** 8 earlier exchanges, 1,000 characters a question, 12,000 for
  the history.
- **12 live questions a minute** for one server process; the count resets on restart.
- **No streaming.** One response; the panel shows a waiting line.
- **Search results, not pages.** The chat does not open the pages a search returns, and a result's
  text is unreadable to the server, so only a lead's URL is verified. That is why every lead reads
  "not checked by us".
- **Code text is not quoted.** A checklist row's paraphrase links to the city's published section;
  anything more about a section is a web lead.
- **The number check can pass a coincidence.** A small number in a statement passes if the same digits
  appear anywhere in the cited item. A separate check refuses "N violations" style counts.
- **The tone checks are word lists.** They catch plain phrasings and miss others; the prompt carries
  the rule, the lists back it up. A person's name cannot be detected in code at all.
- **The model reads the newest 25 records per lot and dataset** (5 for housing violations), plus every
  record a checklist row points to or that mentions a stop-work order. Counts still cover all of them.
- **Saved examples rest on the brief only**, and exist for the two demo sites.

## Open questions, by area of expertise

- **Permitting and DOB data:** are the dataset names and "record" wording right for a reader who files
  with DOB? Should the chat decode complaint category codes now that the key can be imported by hand?
- **The structural engineer:** which questions should get only "not a determination" and nothing else?
  Is a checklist row's paraphrase acceptable to read out, or should the chat only point to the section?
- **The voice-agent developer:** is `plain_text` with a spoken source label per line the right shape,
  and is a wait of several seconds per answer workable, or does voice need a faster brief-only mode?
- **The interoperability and BIM modeling specialist:** every brief source carries its lot's BBL. Is
  that enough for a model view to highlight what an answer is about?
- **The drawing and code review professional:** should statements about what a code section requires
  be limited to official sites only? Today official sites are preferred and flagged, not required.
