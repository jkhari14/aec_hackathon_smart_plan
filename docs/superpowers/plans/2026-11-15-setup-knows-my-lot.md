# Setup That Already Knows the Lot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The project setup screen shows what public records already say about the lot, and asks three quick questions (dig depth, new building height, stage) that change the drafted checklist.

**Architecture:** The checklist API (`actions_for` → `build_actions`) gains two optional inputs, `excavation_depth_ft` and `proposed_storeys`; the survey and monitoring rows reuse the depth thresholds already in `checklist/applicability.py` with touching lots at 0 ft. The project record stores the answers. The setup screen adds a "What we know" card built from the site profile and the three inputs.

**Tech Stack:** FastAPI + pydantic (Python 3.11, unittest), React + TypeScript (node:test), Vite.

**Spec:** `docs/superpowers/specs/2026-11-15-setup-knows-my-lot-design.md`

## Global Constraints

- Every fact shown as known names its source and date; a fact that couldn't load says so, never blank (AGENTS.md).
- Depth bands send their upper bound: Under 5 ft → 4.9, 5-10 ft → 10, 10-20 ft → 20, Over 20 ft → 21; "Not sure" sends nothing.
- A row whose rule needs an input we don't have is kept with "needs input: dig depth" in its why, never dropped or assumed.
- Stage values: Design → `design`, Filing → `pre_filing`, Construction → `construction`; default `design`.
- No per-neighbor distance input; touching lots count as 0 ft.
- Run Python tests with `.venv/bin/python -m unittest ...`; web tests with `npm test` in `web/`.

## Review Focus

- Depth exactly on a threshold (5 ft band upper bound 4.9 vs 10 ft): survey must not apply under 5 ft, must apply at 10.
- A site with no touching neighbors: survey/monitoring fall back to "needs input" (no bbl to measure), not "applies".
- Old projects saved without the new fields still load and redraw (fields optional, default null).
- Alteration jobs: height field hidden; facade cycle keeps using existing PLUTO floors.
- Profile load failure on the setup screen: the card says "couldn't load" and setup still works.

---

### Task 1: Checklist takes dig depth and new building height

**Files:**
- Modify: `actions/build.py` (`code_actions`, `evaluate_condition` "facade_cycle_applies")
- Modify: `actions/__init__.py` (`actions_for`)
- Modify: `api/routers/sites_router.py` (`SITE_OPTIONS["actions"]`, `_checked`, `actions` route)
- Test: `tests/test_actions.py`

**Interfaces:**
- Produces: `actions_for(bbl, stage=None, job_type=None, work_types=None, excavation_depth_ft: float | None = None, proposed_storeys: float | None = None, response=None)`; the profile passed to `build_actions` carries `excavation_depth_ft` and `proposed_storeys` keys. `GET /api/sites/{bbl}/actions?excavation_depth_ft=20&proposed_storeys=9` (both optional, numbers ≥ 0, else 422).

- [ ] **Step 1: Write the failing tests** in `tests/test_actions.py`, class `DepthAndHeight`, using a profile with `work_types=["excavation","foundation"]` and one attached neighbor `{"bbl": "3000000002", "attached": True, ...}`:

```python
def rows(profile): return {a["id"]: a for a in build_actions(profile)}
def test_survey_not_required_under_5ft(self):     assert "action-code-survey" not in rows({**P, "excavation_depth_ft": 4.9})
def test_survey_required_at_10ft_next_door(self): assert "action-code-survey" in rows({**P, "excavation_depth_ft": 10})
def test_no_depth_keeps_row_as_needs_input(self): assert "needs input: dig depth" in rows(P)["action-code-survey"]["why"]
def test_monitoring_applies_over_5ft(self):       assert "action-code-monitoring" in rows({**P, "excavation_depth_ft": 10})
def test_over_20ft_support_drawings_need_state_pe(self):
    assert "NY State PE" in rows({**P, "excavation_depth_ft": 21})["action-code-support_drawings"]["why"]
def test_proposed_storeys_drive_facade_cycle(self):
    assert "action-facade-inspection-cycle" in rows({**P, "job_type": "new_building", "proposed_storeys": 9})
def test_no_neighbors_is_needs_input_not_applies(self):
    assert "needs input" in rows({**P, "neighbors": [], "excavation_depth_ft": 8})["action-code-survey"]["why"]
```

Also a route test: `GET /api/sites/{bbl}/actions?excavation_depth_ft=-1` → 422.

- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_actions -v` — expect the new tests to FAIL.

- [ ] **Step 3: Implement.** In `code_actions`, for rules whose condition is `survey_threshold` or `monitoring_distance`, once the scope check says excavation applies, call `checklist.applicability._survey` / `_monitoring` with `inputs={"excavation_depth_ft": profile.get("excavation_depth_ft"), "distance_to_building_ft": {n["bbl"]: 0 for n in neighbors if n["attached"]}}`, `excavation={"status": "applies"}`, and the first attached neighbor's bbl (None if none). `does_not_apply` drops the row; `needs_input` keeps it and appends `" Needs input: dig depth."` when `excavation_depth_ft` is in `needs`, else the first note. For `support_drawings` with depth > 20, append `" Over 20 ft deep, a NY State PE must seal the support drawings."`. In `evaluate_condition("facade_cycle_applies")`, use `profile.get("proposed_storeys")` when set, else lot floors. `actions_for` copies the two values into the profile; `sites_router` adds them to `SITE_OPTIONS["actions"]`, validates as numbers ≥ 0 in `_checked`, and adds them to the route signature.

- [ ] **Step 4: Run** `.venv/bin/python -m unittest tests.test_actions tests.test_site_profile -v` — PASS.

- [ ] **Step 5: Commit** `git commit -m "Checklist: dig depth and new building height drive survey, monitoring, PE and facade rows"`

### Task 2: Project record keeps the answers

**Files:**
- Modify: `api/contracts.py` (`ProjectCreate`, `Project`)
- Regenerate: `contracts/schemas/*`, `api/openapi.json`, `web/src/api_types.ts`
- Modify: `contracts/fixtures/project.json` (add the two fields as `null`)
- Test: `tests/test_projects_router.py`, `tests/test_contracts.py`

**Interfaces:**
- Produces: `ProjectCreate.excavation_depth_ft: Optional[float] = Field(None, ge=0)`, `ProjectCreate.proposed_storeys: Optional[float] = Field(None, ge=0)`, the same two on `Project`; TS `Project["excavation_depth_ft"]`, `Project["proposed_storeys"]`.

- [ ] **Step 1: Failing test** `test_project_keeps_depth_and_storeys`: POST a project with `excavation_depth_ft=20, proposed_storeys=9, stage="design"`, GET it back, assert both values and stage round-trip; and an old body without them still creates (both `None`).
- [ ] **Step 2: Run** `.venv/bin/python -m unittest tests.test_projects_router -v` — FAIL.
- [ ] **Step 3: Add the fields**, then `.venv/bin/python -m contracts.generate` and `npm run contracts` in `web/`; add the fields to the fixture.
- [ ] **Step 4: Run** `.venv/bin/python -m unittest tests.test_projects_router tests.test_contracts -v` — PASS.
- [ ] **Step 5: Commit** `git commit -m "Project: store dig depth and new building height from setup"`

### Task 3: Setup asks depth, height and stage, and the draft uses them

**Files:**
- Modify: `web/src/features/project_screen/model.ts` (depth bands, stage options)
- Modify: `web/src/features/project_screen/draft.ts` (`DraftInput`, `DraftDeps.actions`, `draftProject`, `addProjectItems`)
- Modify: `web/src/api/client.ts` (`api.actions` opts)
- Modify: `web/src/features/project_screen/SetupStep.tsx`, `project_screen.css`
- Test: `web/tests/project_screen_model.test.ts`, `web/tests/project_screen_draft.test.ts`

**Interfaces:**
- Consumes: Task 1 query params; Task 2 project fields.
- Produces: `DEPTH_BANDS: { value: DepthBand; label: string; feet: number | null }[]` with `DepthBand = "unsure" | "under5" | "5to10" | "10to20" | "over20"`; `STAGE_OPTIONS: { value: Stage; label: string }[]`; `DraftInput` gains `depthFt: number | null`, `proposedStoreys: number | null`, `stage: Stage`; `api.actions(bbl, { jobType, workTypes, depthFt?, proposedStoreys?, stage? })`.

- [ ] **Step 1: Failing tests.** Model: `DEPTH_BANDS.map(b => b.feet)` equals `[null, 4.9, 10, 20, 21]`; `STAGE_OPTIONS.map(s => s.value)` equals `["design", "pre_filing", "construction"]`. Draft: with a fake `deps.actions` spy, `draftProject` passes `depthFt: 20, proposedStoreys: 9, stage: "design"` through to `actions` and to `create` (as `excavation_depth_ft`, `proposed_storeys`, `stage`); `addProjectItems` passes a saved project's values; `depthFt: null` is omitted from the actions call.
- [ ] **Step 2: Run** `npm test` in `web/` — FAIL.
- [ ] **Step 3: Implement.** Setup shows "How deep will you dig?" (segmented, default "Not sure") only when scope includes excavation or foundation; "New building height" (number input, storeys, min 1) only when job type is `new_building`; "Stage" segmented, default Design. `draftProject` stops hard-coding `stage: "pre_filing"`.
- [ ] **Step 4: Run** `npm test` and `npx tsc --noEmit -p .` in `web/` — PASS, no type errors.
- [ ] **Step 5: Commit** `git commit -m "Setup: ask dig depth, new building height and stage; the draft uses them"`

### Task 4: "What we know" card

**Files:**
- Create: `web/src/features/project_screen/known_facts.ts`, `web/src/features/project_screen/KnownFacts.tsx`
- Modify: `SetupStep.tsx` (render the card above Work type), `project_screen.css`
- Test: `web/tests/project_screen_known_facts.test.ts`

**Interfaces:**
- Consumes: `api.siteProfile(bbl)` → `{ data: SiteProfile; sample: boolean }`.
- Produces: `knownFacts(profile: SiteProfile | null): KnownFact[]` with `KnownFact = { label: string; value: string | null; source: string }`; `value: null` renders "couldn't load".

- [ ] **Step 1: Failing tests** for `knownFacts`, from a profile with 5 attached neighbors built 1910–1931, 2–3 floors, `lot_area_sqft: 8000`, `flood.fema_zone: "X"`, `e_designation: null`, `job_type: "new_building"`:
  - neighbors line value `"5 attached, built 1910–1931, 2–3 storeys"`, source `"PLUTO and building footprints"`
  - flood line value `"Zone X"`, source `"FEMA flood maps"`
  - e-designation line only when set
  - filed job line value `"New building"` with source `"DOB NOW filings"` when `work_types_inferred` is true
  - `knownFacts(null)` returns each line with `value: null`
- [ ] **Step 2: Run** `npm test` — FAIL.
- [ ] **Step 3: Implement** `knownFacts` and `KnownFacts.tsx`: a compact list titled "What we already know about this lot", each row value plus source, and the profile's `as_of` (or "pulled from public records") as the date line; a sample profile shows the existing Sample badge, never as fact.
- [ ] **Step 4: Run** `npm test` and `npx tsc --noEmit -p .` — PASS.
- [ ] **Step 5: Commit** `git commit -m "Setup: show what public records already say about the lot"`

### Task 5: Check it in the app

- [ ] Restart the API (from the worktree, with `.env`), open `http://localhost:5174/?screen=project&site=3015790010`, pick New construction / Concrete / Excavation+Foundation+Structural, depth 5-10 ft, Draft: the survey and monitoring rows appear. Go back, change depth to Under 5 ft: the survey row is gone. Screenshot the setup screen with the card.
