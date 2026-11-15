# Checklist Register Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** The project checklist becomes a numbered compliance register with code, proof, when and a done sign-off, under a milestone timeline.

**Architecture:** The backend tags each action item with a phase and a "when" (`actions/phases.py`) and records who marked it done and when. The web checklist renders a milestone line and register rows from those fields.

**Tech Stack:** FastAPI + pydantic + SQLite (unittest), React + TypeScript (node:test).

**Spec:** `docs/superpowers/specs/2026-11-15-checklist-register-design.md`

## Global Constraints

- Phases: `design`, `filing`, `notice`, `before_excavation`, `during_work`, in that order; unknown → `design`.
- "Done" always shows "not checked against records".
- Run `.venv/bin/python -m unittest discover -s tests -t .` and `npm --prefix web test`.

## Review Focus

- Items saved before this change (no phase, no done_by) render in Design without errors.
- Unmarking done (done → open) clears the sign-off.
- A status change sent without `by_role` still saves; the sign-off then says "Marked done" without a role.
- Clicking a milestone with no items shows the empty-filter state, not a blank page.
- Numbering stays stable while filters are on (numbers come from the full list, not the filtered one).

---

### Task 1: Phase and when on every item

**Files:** Create `actions/phases.py`; modify `actions/build.py` (`code_actions`, `hazard_actions`), `actions/from_model.py`; test `tests/test_actions.py`.

**Interfaces:** Produces `phase_for(source_rule: str, stages: list[str] | None = None) -> tuple[str, str]`; every item dict from `build_actions` and from the document rules has `phase` and `when`.

- [ ] Failing tests: `phase_for("checklist:notice") == ("notice", "60 days before work")`; `phase_for("checklist:survey")[0] == "before_excavation"`; `phase_for("actions:x", ["pre_filing","construction"]) == ("filing", "Before filing")`; `phase_for("unknown") [0] == "design"`; every item from `build_actions(fixture profile)` has a phase in the five values.
- [ ] Implement; run tests; commit "Checklist items say when they're due".

### Task 2: Contract and store keep phase, when and the done sign-off

**Files:** `api/contracts.py` (`ActionItem`, `ActionItemUpdate`), `api/store/project_store.py`, `api/store/project_store_schema.py`, regenerate contracts, fixtures; test `tests/test_projects_router.py`.

**Interfaces:** `ActionItem.phase/when/done_by_role/done_at: Optional`; `ActionItemUpdate.by_role: Optional[Role]`.

- [ ] Failing tests: an added item keeps `phase`/`when`; PATCH status done with `by_role: "structural_engineer"` sets `done_by_role` and a `done_at`; PATCH back to open clears both; PATCH done without `by_role` sets `done_at`, `done_by_role` None.
- [ ] Implement (ADDED_COLUMNS for the four item columns); regenerate; run full suite; commit "Items keep when they're due and who marked them done".

### Task 3: Register rows and milestone timeline

**Files:** `web/src/features/project_screen/model.ts` (`itemNumbers`, `MILESTONES`, `milestoneSummary`), `ChecklistStep.tsx`, `project_screen.css`, `web/src/features/project/useProject.ts` (send `by_role`); test `web/tests/project_screen_model.test.ts`.

**Interfaces:** `itemNumbers(groups: {role: Role | null; items: ActionItem[]}[]): Map<string, string>` (A1… by role letter A/S/D/C, U for unassigned); `MILESTONES: {phase; label; sub}[]`; `milestoneSummary(items) -> {phase, total, done, lifeSafety}[]`; `phaseOf(item) -> phase` (missing → design); stage → current milestone: design→design, pre_filing→filing, construction→during_work, pre_acquisition→design.

- [ ] Failing tests for the four functions (numbering by group order, missing phase → design, done counts, life-safety flag).
- [ ] Implement UI: timeline (line, dots, current stage filled, red ring for life safety, filled when all done, click filters), register header row and rows per spec, done sign-off line; send `by_role: workspace.role` on status changes.
- [ ] Run tests, `npx tsc --noEmit -p .`; commit "Checklist: compliance register with a milestone timeline".

### Task 4: Check it in the app

- [ ] Restart the API, draft 861 Park, mark an item done as Structural engineer: green sign-off with role and date; click "Survey done": list filters; screenshot.
