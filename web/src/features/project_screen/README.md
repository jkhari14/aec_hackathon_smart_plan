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
  A PDF in the structural slot goes to the drawing reader (`DrawingReader.tsx`, `POST /model/drawing`) while
  `DrawingScan.tsx` plays (scan → 3D → read; the plan drawn is a labelled illustration). The reading is a
  suggestion: the uploader corrects and confirms it (`POST /model/confirm`), and only then do
  `actions/from_model.py`'s rules add or flag checklist items for the roles they concern. Any other file
  records its name as a `document` pin; the file is not uploaded.
- **Living checklist:** an item a document added or flagged shows why, who and when (`added_reason`,
  `added_by_role`, `added_at`). "New for you" (`newForRole`, `seen.ts`) counts items another role's document
  added to your role's list since this browser last left the checklist as that role (or pressed "Got it");
  the Checklist step shows the count and the checklist a banner and a tag per row.

## Files

| File | What it holds |
| --- | --- |
| `model.ts` | Card options, default scope, the work types sent to the checklist, owners, grouping, document slots |
| `draft.ts` | "Draft checklist": create, load, add; its calls are passed in so it is testable |
| `ProjectScreen.tsx` | The frame: header, live dot, acting-as role, share, steps |
| `SetupStep.tsx`, `ChecklistStep.tsx`, `DocumentsStep.tsx` | The three steps |
| `DrawingReader.tsx`, `DrawingScan.tsx` | Read a drawing, check and confirm it; the loading animation |
| `seen.ts` | When this browser last looked at the checklist as a role (localStorage) |

Tests: `npm test` (Node's built-in runner, `web/tests/`).
