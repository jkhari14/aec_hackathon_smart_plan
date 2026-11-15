# Project Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A full-screen project view (Setup → Checklist → Documents) that a site's whole team shares live through one link.

**Architecture:** Backend: extend the contracts and the SQLite project store with work type, construction type, scope, two roles and a `document` pin kind; let `/actions` take the job type and scope. Frontend: a new `web/src/features/project_screen/` folder reusing `useProject` (4 s ETag polling) for live state; the shell mounts it when `?screen=project`.

**Tech Stack:** FastAPI + Pydantic + SQLite (unittest), React 19 + TypeScript + Vite, design system in `web/src/design`.

**Spec:** `docs/superpowers/specs/2026-11-14-project-screen-design.md`

## Global Constraints

- No new dependencies (Python or npm).
- Contract change first; then `.venv/bin/python -m contracts.generate && (cd web && npm run contracts)`; `tests/test_contracts.py` must pass.
- Sample or failed loads are never added to a real project; "Done" is a person's mark, never proof.
- No owner/applicant/contractor names from public data.
- Use `web/src/design` components and tokens; works in light and dark themes.
- Do not edit map, similarity, chat or layer code. Only touch `app/App.tsx`, `app/slots.tsx`, `app/url_state.ts`, `app/shell.css` in the shell.
- Role labels: Architect, Structural engineer, Developer, Contractor.
- Work type cards → JobType: New construction → `new_building`; Modification to existing structure → `alteration`; Demolition → `demolition`.
- Construction type: `wood`, `masonry`, `steel`, `concrete`, `unknown` (labels: Wood frame, Masonry, Steel, Concrete, Not sure).
- Discipline → owner role: `architect`→`architect`, `structural`→`structural_engineer`, `geotech`→`structural_engineer`, `contractor`→`contractor`.

## Review Focus

1. API unreachable or answering sample data when "Draft checklist" is pressed → no half-made project is opened; the setup shows the reason and stays editable. (Task 4)
2. A local `projects.sqlite` made before this change refuses the new roles → store README tells the developer to delete it; the screen shows the store's refusal text, not a blank page. (Task 1, Task 4)
3. The site's actions list comes back empty → the checklist says "No items for this work type" instead of an empty page. (Task 5)
4. A shared link opened in a fresh tab → it opens the checklist step with a role picker visible, defaulting to Architect. (Task 5)
5. Unknown `work_types` value in the `/actions` query → 422 with the allowed values, never silently ignored. (Task 2)

---

### Task 1: Contracts and project store

**Files:**
- Modify: `api/contracts.py` (Role, ConstructionType, ProjectPin/PinCreate kind, Project, ProjectCreate)
- Modify: `api/store/project_store_schema.py` (ADDED_COLUMNS), `api/store/project_store.py` (`create_project`, `snapshot`)
- Modify: `api/routers/projects_router.py` (`create_project` passes new fields)
- Modify: `api/store/README.md` (delete old local DB note)
- Regenerate: `contracts/schemas/*`, `api/openapi.json`, `web/src/api_types.ts`
- Test: `tests/test_project_store.py`, `tests/test_projects_router.py`

**Interfaces:**
- Produces: `Role = Literal["architect","structural_engineer","developer","contractor"]`; `ConstructionType = Literal["wood","masonry","steel","concrete","unknown"]`; pin kind `"document"`; `Project` and `ProjectCreate` optional fields `job_type: Optional[JobType] = None`, `construction_type: Optional[ConstructionType] = None`, `work_types: list[WorkType] = []`.
- Produces: `ProjectStore.create_project(name, site_bbl, stage, members, job_type=None, construction_type=None, work_types=None) -> dict`.

- [ ] **Step 1: Write failing tests** in `tests/test_project_store.py`:
  - `test_project_keeps_work_type_construction_and_scope`: create with `job_type="alteration"`, `construction_type="masonry"`, `work_types=["structural","facade"]`; `get_project` returns exactly those.
  - `test_old_projects_read_with_empty_setup`: create without them → `job_type is None`, `construction_type is None`, `work_types == []`.
  - `test_developer_and_contractor_can_be_members_and_own_items`: create with all four roles; `update_items` sets `owner_role="contractor"` on a fixture item; `add_pin(..., "document", "survey", "survey.pdf", "developer")` succeeds.
  - `test_unknown_construction_type_and_work_type_are_refused`: `construction_type="adobe"` and `work_types=["digging"]` each raise `ProjectStoreError`.
  - In `tests/test_projects_router.py`: `test_create_round_trips_setup_fields` posts the three fields and reads them back.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_project_store tests.test_projects_router` → new tests FAIL.
- [ ] **Step 3: Implement.** Contracts as in Interfaces. Store: `ADDED_COLUMNS` += `("projects","job_type","TEXT")`, `("projects","construction_type","TEXT")`, `("projects","work_types_json","TEXT")`; validate with `_choice` against `get_args` of the contract literals (add `JOB_TYPES`, `CONSTRUCTION_TYPES`, `WORK_TYPES` to the schema file); `work_types` stored as JSON, deduplicated, order kept; `snapshot` returns the three keys. Router passes `body.job_type`, `body.construction_type`, `body.work_types`. README: one paragraph that a store file made before 2026-11-14 must be deleted (CHECK constraints on role/kind are baked in).
- [ ] **Step 4: Regenerate** `.venv/bin/python -m contracts.generate && (cd web && npm run contracts)`.
- [ ] **Step 5: Run all tests** `.venv/bin/python -m unittest discover -s tests -t .` → OK. `cd web && npm run typecheck` → passes (fix `ROLE_LABELS` in `web/src/features/project/project_client.ts` by adding `developer: "Developer", contractor: "Contractor"`, and `StartProject`'s members initial state in `ProjectPanel.tsx` to include the two new keys with `""`).
- [ ] **Step 6: Commit** `feat(projects): work type, construction type, scope, developer and contractor roles, document pins`.

### Task 2: Actions follow the chosen job type and scope

**Files:**
- Modify: `api/routers/sites_router.py` (`SITE_OPTIONS["actions"]`, `_checked`, `load_site_part`, `/actions` route)
- Modify: `actions/__init__.py` (`actions_for`)
- Test: `tests/test_actions.py`

**Interfaces:**
- Produces: `GET /api/sites/{bbl}/actions?stage=&job_type=&work_types=a,b` (comma-separated); `actions_for(bbl, stage=None, job_type=None, work_types=None, response=None) -> list[dict]`; `load_site_part(..., work_types: Optional[list[str]] = None)`.

- [ ] **Step 1: Write failing tests** in `tests/test_actions.py`:
  - `test_chosen_work_types_replace_inferred_ones`: patch `actions._profile_for` to return the fixture profile with `work_types=[]`; `actions_for(bbl, work_types=["excavation"])` contains an item whose rule needs excavation and `actions_for(bbl, work_types=["facade"])` does not.
  - `test_chosen_job_type_reaches_the_rules`: `job_type="alteration"` includes the `alteration_with_occupancy` item; `job_type="new_building"` does not.
  - `test_router_rejects_unknown_work_type`: TestClient GET `/api/sites/3052110074/actions?work_types=digging` → 422 and the body names allowed values.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_actions` → FAIL.
- [ ] **Step 3: Implement.** Route takes `job_type: Optional[str]`, `work_types: Optional[str]`; split on commas, strip, drop empties; each checked with `valid_choice` against `get_args(WorkType)`; empty after split → `None` (meaning "inferred"). `actions_for` gets the profile via `load_site_part("profile", bbl, job_type=job_type)` path (extend `_profile_for(bbl, job_type)`), then if `work_types` is not None sets `profile["work_types"] = work_types` before `build_actions`.
- [ ] **Step 4: Run all tests** → OK. Regenerate contracts (openapi changes) and run `tests.test_contracts`.
- [ ] **Step 5: Commit** `feat(actions): checklist follows the chosen job type and scope`.

### Task 3: Project screen model (pure functions) and API client

**Files:**
- Create: `web/src/features/project_screen/model.ts`
- Modify: `web/src/api/client.ts` (`actions` takes options), `web/src/contracts.ts` (export `ConstructionType`, `JobType`, `WorkType`, `Role` aliases if missing)
- Modify: `web/src/app/url_state.ts` (`screen: "map" | "project"`, `?screen=project`)

**Interfaces:**
- Produces (in `model.ts`):
  - `WORK_TYPE_CARDS: { value: JobType; label: string; hint: string }[]`
  - `CONSTRUCTION_CARDS: { value: ConstructionType; label: string }[]`
  - `SCOPE_OPTIONS: { value: WorkType; label: string }[]` for excavation, foundation, support_of_excavation, underpinning, structural, facade, scaffold (label "Scaffold / sidewalk shed" maps to both `scaffold` and `sidewalk_shed` → store as `scaffold` and add `sidewalk_shed` when ticked).
  - `defaultScope(job: JobType): WorkType[]` (from DEFAULT_WORK_TYPES in `site_profile/work_types.py`, filtered to SCOPE_OPTIONS values)
  - `ROLES: Role[]` in order architect, structural_engineer, developer, contractor; `ROLE_LABELS` re-exported from `project_client.ts`
  - `ownerFor(discipline: Discipline): Role`
  - `withOwners(items: ActionItem[]): ActionItem[]` (sets `owner_role` only where null)
  - `DOC_SLOTS: { id: string; label: string; relevant: (job: JobType | null, scope: WorkType[]) => boolean }[]`: survey (always), architectural (always), structural (scope has structural or foundation, or job alteration), geotech (scope ∩ earth work: earth_work, excavation, foundation, support_of_excavation, underpinning), soe (support_of_excavation or underpinning), neighbor_survey (any earth work), demolition (job demolition)
  - `groupByOwner(items: ActionItem[]): { role: Role | null; items: ActionItem[] }[]` (ROLES order, then unassigned; life_safety first within a group)
- Produces: `api.actions(bbl, opts?: { jobType?: JobType; workTypes?: WorkType[] })`.
- Produces: `ViewState.screen`; `setView({ screen })`.

- [ ] **Step 1:** Implement the above. No web test runner exists; correctness is pinned by typecheck plus Task 6 browser checks.
- [ ] **Step 2: Run** `cd web && npm run typecheck` → passes.
- [ ] **Step 3: Commit** `feat(project-screen): setup model, owners, document slots, actions options`.

### Task 4: Screen frame and Setup step

**Files:**
- Create: `web/src/features/project_screen/ProjectScreen.tsx`, `SetupStep.tsx`, `project_screen.css`, `README.md`

**Interfaces:**
- Consumes: Task 3 model, `useProject` / `ProjectWorkspace`, `projectWrites`, `setProjectInUrl` from `features/project/project_url.ts`.
- Produces: `ProjectScreen(props: { bbl: string | null; siteLabel?: string; projectId: string | null; workspace: ProjectWorkspace; onProjectCreated: (id: string) => void; onBack: () => void })`.

- [ ] **Step 1:** `ProjectScreen`: full-viewport surface over the map (`position: fixed; inset: 0; background: var(--fs-bg…)` token), header with address + BBL, live dot ("Live" when `workspace.state.status === "ok"` and not sample; "Offline: showing the last copy" or "Sample: not saved" otherwise), acting-as role select, Share button (copies `window.location.href`, shows "Link copied"), "← Map". Stepper of three steps; Checklist and Documents disabled until a project exists. With `projectId` → open on Checklist; without → Setup.
- [ ] **Step 2:** `SetupStep`: card groups (radio-style buttons with `aria-pressed`) for work type, construction type; scope as multi-select chips pre-filled from `defaultScope` whenever work type changes; four role cards with optional name input and an "I am this" radio; "Draft checklist →" disabled until work type and construction type are chosen. On submit: `workspace.create({ name: `Project: ${siteLabel ?? bbl}`, site_bbl: bbl, stage: "pre_filing", members, job_type, construction_type, work_types })` → `onProjectCreated(id)`; then load `api.actions(bbl, { jobType, workTypes })`; if `sample`, show "Only sample checklist items could be loaded, so none were added." and still open the checklist (empty); else `projectWrites.addItems(id, withOwners(items))`. Any thrown error shows its message under the button and keeps the form.
- [ ] **Step 3: Run** `cd web && npm run typecheck` → passes.
- [ ] **Step 4: Commit** `feat(project-screen): full-screen frame and setup cards`.

### Task 5: Checklist and Documents steps

**Files:**
- Create: `web/src/features/project_screen/ChecklistStep.tsx`, `DocumentsStep.tsx`

**Interfaces:**
- Consumes: `groupByOwner`, `DOC_SLOTS`, `ROLE_LABELS`, `workspace.updateItem`, `projectWrites.addPin`.

- [ ] **Step 1:** `ChecklistStep`: progress "N / M done" (n/a counts as done), chips Mine (owner = acting role) / Life safety / Open; groups from `groupByOwner` with a heading per role; each row: status pill cycling open → in_progress → done (with a menu entry for n/a), title, hazard dot (`--fs-hz-<hazard>`), owner select (members' roles + Unassigned); row click unfolds `why`, `code_ref`, `proof_needed` via `Explain`. Rows whose status/owner changed since the previous poll get a 2 s highlight class. Empty → `EmptyState` "No items for this work type". Write errors show inline on the row.
- [ ] **Step 2:** `DocumentsStep`: slots filtered by `relevant(project.job_type, project.work_types)`; each lists `document` pins with `ref_id === slot.id` (file name, role label, date); "Attach" = hidden `<input type="file">`; on choose → `addPin({ kind: "document", ref_id: slot.id, title: file.name, by_role: role })`. Note under the list: "Files stay on your computer for now: only the name is shared."
- [ ] **Step 3: Run** typecheck → passes.
- [ ] **Step 4: Commit** `feat(project-screen): live checklist by owner and document slots`.

### Task 6: Entry point, mounting, browser verification

**Files:**
- Modify: `web/src/app/slots.tsx` (`SiteSlot` gets `onContinue` prop → button "Continue to project →" under the panel subtitle, via `Panel`'s `actions` prop)
- Modify: `web/src/app/App.tsx` (call `useProject(projectId)` once; render `<ProjectScreen>` when `view.screen === "project"`; Escape closes it)

- [ ] **Step 1:** Wire it. `projectId` comes from `features/project/project_url.ts`. Continue → `setView({ screen: "project" })`. `onBack` → `setView({ screen: "map" })`.
- [ ] **Step 2: Run** `.venv/bin/python -m unittest discover -s tests -t .` → OK; `cd web && npm run build` → OK.
- [ ] **Step 3: Browser check** (preview `api` + `web`): pick a site → Continue → choose New construction / Masonry → Draft checklist → items appear grouped; open the share link in a second tab as Contractor, mark an item done → first tab shows it within ~5 s; Documents shows Geotechnical report for new construction; attach a file → name appears in the other tab; ← Map returns with site still picked; check dark and light theme; stop the API and confirm the live dot says offline.
- [ ] **Step 4: Commit** `feat(project-screen): continue from a site into the project screen`.
