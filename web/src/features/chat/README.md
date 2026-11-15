Docked chat. Owner: Jahleel (PR 4, 9).

Questions about one site, answered in parts that each say where they came from. The server decides
each part's kind from what the part rests on; this folder only shows it.

## Mounting it

```tsx
import { ChatPanel } from "../features/chat/ChatPanel";

<ChatPanel
  bbl={siteBbl}                      // null until a site is picked: the input then says why it is off
  siteLabel="2625 Bedford Avenue"    // optional
  projectId={openProjectId}          // optional: with it, answers can be pinned
  asOf={asOfDay}                     // optional YYYY-MM-DD, when the page replays an earlier date
  jobType={jobType} stage={stage}    // optional
  onFlyTo={(target) => ...}          // { ref?, label?, bbl?, lat?, lon? }: bbl, or lat and lon, is set
  onToggleLayer={(layerId, on) => ...}
  onPin={workspace.pinChatAnswer}    // from useProject (../project); gets { title, question, as_of, offline, answer_parts, text }
/>
```

The panel docks bottom right over the map and collapses to its title bar; pass `className` to place
it elsewhere. The default spot covers the corner where MapLibre puts its attribution, so the shell
should move one of the two.

The handlers are how the chat acts on the page. An answer can carry actions (show or hide a layer, fly
the map, pin an answer); the panel runs them in order through the handlers and says so in the answer
when the page has no handler for one. A source chip under a part opens the source in a new tab, and
"Show on the map" calls `onFlyTo`. `onPin` may return a promise; if it rejects, the panel shows the
error's message next to the answer.

A conversation is about one site on one day: changing `bbl` or `asOf` starts a new one, so answers
from today's view are never sent as context to a question about an earlier date.

## Files

| File | What it holds |
| --- | --- |
| `ChatPanel.tsx` | The dock, the conversation, the question box |
| `ChatAnswerParts.tsx` | One answer: each part under its source label, with its source chips |
| `chat_part_kinds.ts` | The label for each kind of part. Tone classes are placeholders for the design system's source label (PR 1) |
| `chat_client.ts` | `POST /api/chat` and `GET /api/chat/setup` |
| `chat_conversation.ts` | The exchanges kept, and the earlier ones a follow-up sends within the server's caps |
| `chat_page_actions.ts` | Running an answer's actions; where a source chip flies the map |
| `chat_saved_answers.ts`, `chat_saved_answers.json` | Answers saved ahead of time for the sample site |

## When the server has no key, or there is no server

- **No model key on the server:** the server still answers, from the site's data, by matching the
  question to a search, a count, the warnings, the action items or the closest cases. Each such
  answer says no model was called.
- **No server at all:** this chat does not use the shared client's fixture fallback, because a fixed
  answer under a question it was not written for would read as the answer. It says the question was
  not answered and offers the saved answers, which are shown only for the site they were written for
  and never in an as-of view.

`chat_saved_answers.json` is generated: `python -m api.routers.chat.chat_saved_answers_export`. A
test fails when it is out of date.

## Limits

- Not mounted in the app shell yet, so the running app shows no chat.
- Built on the PR 0 placeholder tokens; it has not been moved onto the design system's panel, chip and source label.
- `chat_client.ts` calls `/api/chat` as a relative path. That works in local development (the dev server
  forwards `/api`). A web app deployed on a different host from the API needs `VITE_API_BASE`, which the
  shared client uses and this one does not yet: until then the deployed panel offers the saved answers.
- No model has answered a question yet. The state and the plan for the first live call are in
  `api/routers/chat/README.md` and `api/routers/chat/chat_first_live_call.md`.
- A single record's chip flies to the site, since an answer part does not carry the record's own lot.
- No test runner is set up in `web/` yet, so this folder is covered by the type check and a browser check only.
