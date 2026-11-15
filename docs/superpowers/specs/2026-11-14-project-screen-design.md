# Project screen: design

Date: 2026-11-14 · Branch: `rishabh/cityweft-3d`

## Intent

The map is the explorer: browse the city, pick a site. Once a team commits to a site, they need a
different, calmer place: say what the job is, get a checklist of the risks that matter for that job,
and work through it together as the project moves. The project screen is that place. Everyone on the
project (architect, structural engineer, developer, contractor) opens the same link and sees the same
checklist, live.

## Goals

- A **Continue** step from a picked site into a full-screen project view.
- **Setup as cards, not text fields:** work type, construction type, optional scope, who is on the project.
- A **checklist drafted from those inputs**, grouped by who owns each item, short lines, detail on demand.
- **Shared and live:** one link; a tick by the contractor shows on the architect's screen within ~4 s.
- **Documents at the right time:** slots for drawings and reports, each shown when the work type makes it relevant.

## Non-goals (this round)

- No changes to the map, similarity, chat, layers or the existing site panel beyond one Continue button.
- No real file upload or storage: documents are placeholders (see Documents).
- No accounts or auth: a tab acts as a role, as the project store already works.
- No AI-written checklist: items come from the existing rule-based actions (`actions/`).

## Anti-goals

- Text-heavy cards. Each item is one line plus status and owner; the "why", code ref and proof needed fold away.
- A checklist that pretends: a sample or failed load is never shown as this site's checklist; "Done" is a person's mark, not proof.
- Owner names, applicants or contractors from public data (AGENTS.md rule).

## Approaches considered

1. **New full screen on the existing project store (chosen).** New `web/src/features/project_screen/` folder;
   the project store and `/api/projects` gain work type, construction type, scope and two roles. Sharing and
   live updates come from the store's ETag polling, already built.
2. Full screen, front-end only (URL + local storage). Fastest, but a share link is a snapshot: ticks never reach anyone else.
3. A panel over the map. Least work, but keeps the project inside the explorer, which is what the team wants to move away from.

Chosen: 1, because shared live state is the point and the plumbing exists.

## How it works

### Entry
- Site panel (`app/slots.tsx`, `SiteSlot`) gets a **Continue to project →** button under the title.
- It opens the screen in setup mode: `?site=<bbl>&screen=project`. After setup the URL becomes
  `?project=<id>&screen=project` (the existing `project_url.ts` key), which is the share link.
- **← Map** returns to the explorer with the site still picked.

### Screen layout
Full-screen, replaces the map (the map stays mounted underneath, hidden, so going back is instant).

```
┌ 4site · 123 Main St, Brooklyn · BBL ─────── ● Live  [Acting as: Architect ▾]  [Share]  [← Map] ┐
│  ① Setup   ›   ② Checklist   ›   ③ Documents                                                    │
│                                                                                                 │
│  (step body)                                                                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### ① Setup (before the project exists; editable later only by re-drafting)
Selectable cards, one choice each unless noted:
- **Work type:** New construction · Modification to existing structure · Demolition
  → maps to the contract `JobType`: `new_building`, `alteration`, `demolition`.
- **Construction type:** Wood frame · Masonry · Steel · Concrete · Not sure.
- **Scope (multi, optional):** Excavation · Foundation · Support of excavation · Underpinning · Structural ·
  Façade · Scaffold / sidewalk shed. Pre-ticked from the work type's defaults
  (`site_profile/work_types.py` `DEFAULT_WORK_TYPES`), user unticks what doesn't apply.
- **Who's on it:** four role cards (Architect, Structural engineer, Developer, Contractor), each with an
  optional name; a role left blank is still added, named by its role, so items can be assigned to it.
  "I am the …" picks this tab's role.
- **Draft checklist →** creates the project, then loads and adds its items.

### ② Checklist
- Items come from `GET /api/sites/{bbl}/actions?job_type=…&work_types=…` (new options, below), added to the
  project with an owner set from the item's discipline: architect → Architect, structural and geotech →
  Structural engineer, contractor → Contractor. Developer owns none by default but can take any.
- Grouped by owner, life-safety first inside each group. Each row: status checkbox-pill
  (open / in progress / done / n/a), title, hazard dot, owner menu. Click the row to unfold why, code ref and proof needed.
- Top strip: progress count (e.g. 4 / 17 done), filter chips "Mine" / "Life safety" / "Open".
- Live: `useProject` polls every 4 s; a header dot shows "Live" while reads succeed and "Offline: showing
  the last copy" when they don't. Changes made in another tab briefly highlight the row.

### ③ Documents
- Slots, each shown only when relevant: Survey (always), Architectural drawings (always), Structural drawings
  (structural, foundation, alteration), Geotechnical report (any earth work), SOE / underpinning plan
  (support of excavation, underpinning), Pre-construction survey of neighbours (attached neighbours or earth
  work, from the profile), Demolition plan (demolition).
- **Placeholder:** "Attach" opens a file picker; the file is not uploaded. Its name, slot and who added it are
  saved on the project as a pin of new kind `document`, so the rest of the team sees it was added. The slot
  says "File stays on your computer: upload is coming".

## Backend changes (small, contract-first)

1. `api/contracts.py`
   - `Role` += `"developer"`, `"contractor"`.
   - `ProjectPin.kind` and `PinCreate.kind` += `"document"`.
   - `Project` and `ProjectCreate` gain optional `job_type: Optional[JobType]`,
     `construction_type: Optional[ConstructionType]`, `work_types: list[WorkType] = []`.
     `ConstructionType = Literal["wood", "masonry", "steel", "concrete", "unknown"]`.
   - Regenerate `api/openapi.json`, `web/src/api_types.ts`, `web/src/contracts.ts` (`contracts.generate`, `npm run contracts`).
2. Store (`api/store/`): three new `projects` columns through `ADDED_COLUMNS`; `create_project` takes and
   checks them; `snapshot` returns them. The CHECK constraints on role/kind are baked into existing SQLite
   files, so a store file made before this change refuses the new roles: the gitignored local
   `projects.sqlite` is deleted, and the store README says so.
3. Actions: `sites_router` `SITE_OPTIONS["actions"]` += `job_type`, `work_types`; `actions_for` builds the profile
   with the job type and, when `work_types` is given, uses that list instead of the inferred one, so the
   checklist follows what the user picked.
4. Tests: extend `test_project_store.py`, `test_projects_router.py`, `test_actions.py` for the new fields, roles,
   pin kind and actions options.

## Constraints

- Every fact keeps its source label; sample data is labelled and never added to a real project (existing rule in `useProject`).
- Design tokens and components from `web/src/design`; works in light and dark theme.
- No new dependencies.

## Left to the builder

- Exact visual styling within the design system; copy wording within the rules above.
- How the "changed by someone else" highlight is drawn.
- Construction type is recorded and shown; no action rule reads it yet (none exists). Adding such rules is out of scope.
