# Lessons first: what could go wrong here, for every option

Date: 2026-11-15 · Status: approved direction (Rishabh, in session) · Branch: `rishabh/lessons-first` (local only)

## Why

4site started as an address lookup: a lot's own red flags. The idea is preventive: before you even decide what to
do with a plot, see what went wrong on similar past projects (collapse, fire, flood, falls) and what prevents it,
then narrow by what you'll actually do. Not a wiki of projects: every lesson ends in an action.

## Flow

1. Enter an address. The site panel leads with **What could go wrong here**: lessons for every option, grouped
   by hazard.
2. Narrow with option chips: All · Renovate · Demolish and rebuild · New build (vacant lot).
3. Narrow with scope chips (Excavation, Underpinning, Structural, Facade, Scaffold, Demolition, Gas).
4. **Start a project with this option**: the project setup opens pre-filled with the option and scope.

## A lesson

- A **failure mode** (about 12): e.g. "Excavation undermined a neighbor's footings", "Load-bearing element
  removed without shoring", "Fire during demolition or hot work", "Water entered below-grade space".
- The **past incidents** in that mode from the case library, closest to this site first (existing similarity),
  each with title, year and whether the tag comes from a reported cause or only from what happened (cases under
  investigation are tagged by event only, never a cause).
- **What prevents it**: the checklist items, existing code rows and hazard rows plus a few new lesson items
  (temporary shoring for structural alterations, existing-condition assessment, hot-work and demolition fire
  watch, crane and hoist rigging plan, scaffold and guardrails). A code section only where certain.
- **Already reported here**: if this lot's own records bear on the mode (e.g. undermining complaints), one line.
- Which options and scopes it applies to.

## Data

`data/cases/lessons.json`: failure modes (label, hazard, options, scopes, preventive item ids) and each case's
modes with their basis (`reported_cause` or `event_only`), tagged by reading each case's reported cause. New
preventive items live in `actions/rules.json` under `lesson_rules`.

## API

`GET /api/sites/{bbl}/outlook` → `{ bbl, options, lessons: [{ id, label, hazard, options, scopes, cases,
prevent_with, here }] }`. Lessons with no case are left out. Ranked by severity of their worst case, then count.

## Non-goals / anti-goals

- No blame and no "would have prevented": lessons say "similar past projects", causes only as reported.
- No change to the project checklist rules beyond adding the lesson items to the draft when their scope applies.
- Not merged or pushed; reviewed on its own ports (web 5175, API 8002).
