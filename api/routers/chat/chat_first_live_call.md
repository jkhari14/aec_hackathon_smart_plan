# The chat's first live model call: a plan

Nothing here has been done. No request from this chat has ever reached a model (see "Status" in
`README.md`). This file is the list to work through when a model key exists, so the first live answer
is checked on purpose and not discovered in front of an audience.

The key and any spend belong to the person who holds the key. Nobody else makes a live call, and no
step below is a reason to ask for a key sooner.

## Before the call

| Needed | State on `main` | How to check |
|---|---|---|
| The SDK installed on the server | Listed: `anthropic==2.8.0` in `api/requirements.txt` | `python -c "import anthropic; print(anthropic.__version__)"` in the server's environment |
| A model key in the server's environment (`ANTHROPIC_API_KEY`) | Not set anywhere | `GET /api/chat/setup` returns `"live": true` once the key and the SDK are both there |
| The key kept out of the repo, the web build and the logs | Holds today: the SDK reads it from the environment, no code reads or prints it, and no `VITE_` variable carries it | Search the built `web/dist/` for the key's first characters after a build: nothing should match |
| The model and effort settings | Defaults `claude-opus-5-5` and `medium`; override with `FORESITE_CHAT_MODEL` and `FORESITE_CHAT_EFFORT` | Read them back from the server's environment |
| A way to see server logs | The chat logs to the `foresite.chat` logger; warnings reach stderr with no setup, info lines do not | Run the API in a terminal, or open the host's log view |
| A site whose data is loaded | Any lot with a cached pull; the sample lot works but its answers carry the sample label | `GET /api/sites/<bbl>/profile` answers without the `X-ForeSite-Fixture` header |

Two more things are needed before the chat can be asked from the app itself. Neither blocks the first
call, which is made straight at the API:

- **The panel is not mounted in the app shell.** The mount snippet is in `web/src/features/chat/README.md`.
- **The panel calls `/api/chat` as a relative path.** That works in local development, where the dev
  server forwards `/api` to the API. A deployed web app on a different host from the API reaches it
  through `VITE_API_BASE`, which the shared client uses and the chat's client does not yet. Until it
  does, the deployed panel cannot reach the chat and offers the saved answers.

## What a live request sends that has never been sent

The pinned SDK accepts every parameter name below (checked by reading the method's signature in
`anthropic` 2.8.0; no request was sent). Whether the API accepts the **values** is not known. The first
call is what shows it.

| Sent | Where | If the API rejects it |
|---|---|---|
| Model id `claude-opus-5-5` | `chat_model_call.MODEL` | Every question falls back to a mock answer with the "live call did not complete" line. Set `FORESITE_CHAT_MODEL` to an id the key can use |
| `output_config={"effort": "medium"}` | `_Session._request` | Same fallback. Try `FORESITE_CHAT_EFFORT` set to another level, then remove the setting in code |
| The fallback option: beta `server-side-fallback-2026-07-01` with `fallbacks="default"` | `_Session._request` | On a 400 the code asks once more without it, **silently**: nothing is logged. See "Reading the result" for how to tell |
| The web search tool, type `web_search_20250305`, at most 3 searches, two blocked sites, an approximate location | `WEB_SEARCH_TOOL` | Same fallback to mock. The SDK also knows two newer tool versions; the older one was chosen because each result comes back as its own block that a cited URL can be checked against. A newer version may need the reading code in `_request` changed |
| Three strict tools: `search_records`, `search_similar_cases`, `submit_answer` | `chat_tools.py`, `chat_prompt.py` | A schema the API will not compile as strict is a 400 on the first request: same fallback |
| A cache marker on the site-data block of the instructions | `chat_prompt.system_blocks` | Not expected to fail; whether it saves anything shows in the usage numbers |

## The first call

One question, on one site whose data is loaded, with no as-of day (so web search is allowed), asked
straight at the API so the app is not part of what is being tested:

```bash
curl -s -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d '{"bbl": "<a lot with loaded data>", "question": "What early warnings are there for this site, and what are they based on?"}'
```

A question about the site's own data comes first, because every statement in the answer can be checked
against what the site routes return. A question that needs the web comes second, and a question in an
as-of view third (web search must be off and nothing dated on or after the day may appear).

## Reading the result

Check these in order. Each line names where to look.

1. **A model answered.** The response has `"offline": false`. If it is `true` and the first part is the
   "live model call did not complete" notice, the call failed: go to "If the call fails".
2. **The answer went through the checks.** Every part that is not a notice has a `source_name`, and a
   part of kind `public_record`, `case`, `warning` or `action` has a `record_id`. For a case, a warning
   or an action item that id is one the matching site route also returns (`/similar`, `/warnings`,
   `/actions`): look each one up. A "held back" notice means the model wrote something the server would not show; that
   is the checks working, and it is worth reading the server log to see what was held back (an info
   line, so the log level must be info).
3. **Counts and absences are the server's.** "None found" and "unknown" parts read exactly as they do in
   a mock answer for the same site.
4. **Web results are leads.** A part of kind `web` has a `source_url` that is one of the URLs the search
   returned, and its text never appears under a record label. This is the first time the code that
   reads search results off a response runs at all.
5. **Which model answered, and what it cost.** The chat counts tokens and searches for each answer but
   neither logs nor returns them today, so read the usage for the call on the provider's console. If
   the fallback option was accepted, the model named there can differ from the one configured. A log
   line for usage is a small change worth making before the second call.
6. **Whether the fallback option was accepted.** The code retries silently without it after a 400. The
   provider's console shows one failed request followed by one accepted request when that happened.
7. **Time.** One question may take up to 8 requests, each with a 120-second timeout and one retry.
   Measure how long the first answer takes; the panel shows "Looking this up…" for all of it and has no
   timeout of its own.
8. **The limit.** With a key, the server answers at most 12 live questions a minute per process and
   refuses the next with HTTP 429 and a plain sentence, which the panel shows as the reason. This has no
   test; ask 13 short questions in a minute once and confirm the thirteenth is refused, knowing each of
   the first twelve is a paid call.

## If the call fails

A failed live call never reaches the reader as an error. The server logs one warning,
`live chat call failed: ChatModelError: <reason>`, and answers in mock mode with the notice "The live
model call did not complete, so this is a mock answer." A line with any other error name in place of
`ChatModelError` is a fault in the chat's own code, not in the call. The reason is one of:

| In the log | Meaning | First thing to try |
|---|---|---|
| `AuthenticationError`, `PermissionDeniedError` | The key is wrong, revoked, or not allowed this model | The key holder checks the key and the model access |
| `BadRequestError` | The API rejected the request's shape or a value, even after the retry without the fallback option | Send the same request with web search off (ask in an as-of view), then with another model id, to find which value is rejected |
| `NotFoundError` | The model id is not one the key can use | Set `FORESITE_CHAT_MODEL` |
| `RateLimitError`, `OverloadedError`, `InternalServerError` | The provider's limit or an outage | Wait and ask again |
| `APITimeoutError`, `APIConnectionError` | No answer within 120 seconds, or no route out from the host | Check the host can reach the provider; ask a shorter question |
| `the model declined the request` | A refusal stop reason | Read the question; the fallback option exists for this case |
| `the answer ran past the token limit` | 8000 output tokens were not enough | Ask a narrower question; raise `MAX_TOKENS` if it recurs |
| `no answer was submitted within the request limit` | 8 requests passed without the model calling `submit_answer` | Read the server log for tool rounds; this is a prompt problem |

The stop reasons `refusal`, `max_tokens` and `pause_turn`, and the retry after a 400, have no test: the
first time one happens will be the first time that branch runs.

## After the first live answer

- Replace "No request from this chat has ever reached a model" in `README.md` with the date of the
  call, the model that answered, the SDK version, and which of the values in the table above were accepted.
- Record what failed and what was changed to make it pass, in this file.
- Add tests for whatever the first call showed to be wrong, and for the untested branches named above.
- Add the usage log line, if it was not added before the call.
- Rerun `python -m api.routers.chat.chat_saved_answers_export` only if the chat's wording or checks
  changed. The saved answers are built from the site's data with no model, so a live call by itself
  does not change them.
- Decide, with the key holder, whether the demo runs live or stays on mock answers: `FORESITE_CHAT_LIVE=0`
  keeps a server with a key in mock mode.

## What stays the key holder's call

Getting a key, putting it on a host, the first call and every call after it, and any limit on spend.
The chat spends nothing while it is in mock mode.
