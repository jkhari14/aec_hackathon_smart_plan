# Project screen

The place a team goes once it has committed to a site: **Setup → Checklist → Documents**, full screen over
the map. Everyone on the project (architect, structural engineer, developer, contractor) opens the same
link (`?project=<id>&screen=project`) and sees the same checklist, live.

## How it works

- **Entry:** "Continue to project →" in the site panel sets `?screen=project`. "← Map" goes back with the
  site still picked; the map stays mounted underneath.
- **Setup** (`SetupStep.tsx`): cards for work type (→ `JobType`) and construction type, scope chips
  pre-ticked from the work type, and the four roles. "Draft checklist" runs `draft.ts`: create the project
  with the choices, load `GET /api/sites/{bbl}/actions?job_type=&work_types=`, add the items with an owner
  from their discipline. Sample items are never added to a real project.
- **Checklist** (`ChecklistStep.tsx`): grouped by owner, life safety first. Status cycles
  open → in progress → done; "not applicable" is in the unfolded row. Rows another tab changed flash briefly.
- **Live:** `useProject` polls the project store every 4 s with its ETag; the header dot says Live or Offline.
- **Documents** (`DocumentsStep.tsx`): slots shown only when the work makes them relevant (`DOC_SLOTS`).
  A placeholder: attaching records the file's name as a `document` pin; the file is not uploaded.

## Files

| File | What it holds |
| --- | --- |
| `model.ts` | Card options, default scope, the work types sent to the checklist, owners, grouping, document slots |
| `draft.ts` | "Draft checklist": create, load, add; its calls are passed in so it is testable |
| `ProjectScreen.tsx` | The frame: header, live dot, acting-as role, share, steps |
| `SetupStep.tsx`, `ChecklistStep.tsx`, `DocumentsStep.tsx` | The three steps |

Tests: `npm test` (Node's built-in runner, `web/tests/`).
