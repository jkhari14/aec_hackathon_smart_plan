Shared project workspace for the architect and structural engineer. Owner: Jahleel (PR 9).

Who is on the project, its action items with an owner and a status each, notes, and pins, including
chat answers pinned from the chat panel. There are no accounts: each browser tab acts as a role, and
the store refuses a note or a pin in a role the project has no member for.

## Mounting it

```tsx
import { ChatPanel } from "../features/chat/ChatPanel";
import { ProjectPanel } from "../features/project/ProjectPanel";
import { useProject } from "../features/project/useProject";

const workspace = useProject(projectId);          // null: no project open

<ProjectPanel
  workspace={workspace}
  siteBbl={siteBbl} siteLabel={address}           // with no project open, one can be started for the site
  onProjectCreated={(id) => ...}                  // put the id in the URL so the other role can open it
  onOpenPin={(pin) => ...}                        // optional: show a pinned record, case, warning or item
/>
<ChatPanel ... projectId={projectId} onPin={workspace.pinChatAnswer} />
```

Call `useProject` once and share the result: it holds the project, the role this tab acts as, and the
writes. It polls every 4 seconds with the project's ETag, so one role's change shows in the other
role's tab; an unchanged project costs a 304 and no body. The panel docks bottom left; pass
`className` to place it elsewhere.

## What it will not do

- **No fixture fallback.** A project is two people's real data. If it cannot be loaded, the panel says
  so and shows nothing rather than a sample or a stale copy passed off as current. While the server
  still answers a project route from sample data, the panel labels it and says changes are not saved.
- **No write is assumed.** Every change waits for the store; a refusal shows the store's reason next
  to the control.
- **No sample action items on a real project.** "Add this site's action items" refuses when only
  sample items could be loaded.
- **No inferred proof.** Status and owner are set by the people on the project. "Done" is a person's
  mark, not a finding that a duty was met.

## Pinned chat answers

A pin of a chat answer carries a `body`: the answer as the reader saw it, each part led by the label of
where it came from, with the question, the as-of day and whether a model was called. It is text, kept
as sent, so a pinned answer is never shown without its source labels. The body needs the optional
`body` field on `PinCreate` and `ProjectPin` and a store that keeps it; where a pin comes back without
one, the panel says the answer's text was not kept. Over 8000 characters an answer is refused, not cut.

## Files

| File | What it holds |
| --- | --- |
| `ProjectPanel.tsx` | The dock: start a project, members and the acting role, notes, pins |
| `ProjectItems.tsx` | The action items: life safety first, owner and status |
| `useProject.ts` | The project's state, the poll, and the writes |
| `project_client.ts` | The calls to `/api/projects` |
| `project_pins.ts` | A chat answer as a pin |
| `project_url.ts` | The open project in the URL (`?project=<id>`) |

## Limits

- It sits in the shell's chat slot as the "Project" tab (`../chat/ChatDock.tsx`), with `embedded`. The open
  project is in the URL (`?project=<id>`, `project_url.ts`), so the link opens the same project for the other role.
- The colours are the design system's, through `../chat/chat_theme.css`; the layout is still this folder's own classes.
- Checked in a browser against the project store and against the sample stubs; no test runner is set up in `web/` yet.
