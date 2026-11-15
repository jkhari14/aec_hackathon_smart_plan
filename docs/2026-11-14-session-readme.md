# Session README: project screen and UI refresh (2026-11-14)

What this working session decided and built on `rishabh/cityweft-3d`, so the team can pick it up.

## Where it started

The team's call left a list of improvements:

- Work type and construction type as inputs.
- Similarity that explains itself.
- Strands between similar buildings.
- A misplaced 2D button and building colours that mean something.
- Lighter cards.
- A project view the whole team shares.

Similarity scoring and the chat are owned by other people, so this session left them alone.

## Built: the project screen

You pick a site, press **Continue to project →**, and get a full-screen view with three steps.

| Step | What happens |
| --- | --- |
| **1 · Setup** | Cards for work type (new construction / modification / demolition) and construction type (wood, masonry, steel, concrete, not sure). Scope chips are pre-ticked from the work type. Then the team: architect, structural engineer, developer, contractor. |
| **2 · Checklist** | Drafted from the action rules for that work type and scope, grouped by owner, life safety first. Status open → in progress → done (or n/a). Filters: Mine / Life safety / Open. |
| **3 · Documents** | Slots shown only when relevant (survey, drawings, geotech report, SOE plan, neighbour survey, demolition plan). Placeholder: attaching records the file name for the team; the file is not uploaded yet. |

- **Sharing:** "Share" copies the link (`?project=<id>&screen=project`).
- **Live:** every open tab checks the project every 4 seconds, so one person's tick shows on everyone's
  screen. The header dot says **Live**, or **Offline: showing the last copy**.

### Backend changes

- Contracts: roles `developer` and `contractor`; projects carry `job_type`, `construction_type`,
  `work_types`; new pin kind `document`.
- `GET /api/sites/{bbl}/actions?job_type=&work_types=a,b` builds the checklist for the chosen job.
- **Breaking for local data:** delete `api/store/data/projects.sqlite` if you made one before this change
  (it refuses the new roles; the API now says so).

### How it was checked

- Python: 391 tests. Web: typecheck and 20 tests (`cd web && npm test`). Build: clean.
- In the browser: two tabs as two roles, live updates, offline state, light/dark, phone width.
- A fresh reviewer read the whole branch. All important findings were fixed with tests.

### Known gaps

- Code-rule items (BC 3309: excavation-support drawings, preconstruction survey) appear for every job,
  even with no digging. They come from `actions/build.py` (Hongyu's) and are proposed as a separate task.
- Documents are names only (no upload).
- Setup is fixed once drafted; changing the job means a new project.

## Decided next: the UI refresh

Design: [`docs/superpowers/specs/2026-11-14-ui-refresh-design.md`](superpowers/specs/2026-11-14-ui-refresh-design.md)

- **Light paper look by default**, from the 4site deck: off-white grid paper, black ink, one blue
  (`#4A6CF0`), Space Grotesk plus a pixel font for small labels. The map goes light too.
- **One strand at a time:** clicking a similar case zooms out to show both buildings, highlighted, joined
  by one strand. A switch shows all.
- **Similarity as a ring** with the number inside, not a bar.
- **Lighter similar-case cards.**
- **Building colours:** site blue, attached neighbours charcoal, the rest pale grey (no more height ramp).
- **The 2D button** moves into the camera controls, and **the Layers button** gets a label.
- **Layers switch on by work type.**

## Files to know

| Path | What |
| --- | --- |
| `web/src/features/project_screen/` | The project screen (see its README) |
| `docs/superpowers/specs/` | Designs for both pieces |
| `docs/superpowers/plans/2026-11-14-project-screen.md` | The project screen's build plan |

## Running it

```bash
.venv/bin/uvicorn api.main:app --port 8000
cd web && npm run dev    # http://localhost:5173
```
