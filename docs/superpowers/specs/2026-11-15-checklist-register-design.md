# Checklist as a compliance register, with a milestone timeline

Date: 2026-11-15 · Status: approved (Rishabh, from the two mockups in the session)

## Why

The project checklist reads like an app to-do list. Engineers and architects should see something that looks
like a sign-off sheet: numbered items, the code section and the proof in their own columns, when each is due,
and a clear "done" sign-off. A project plan also needs time: a line of milestones showing where the job is.

## Goals

- **Register rows:** number (A1, S1, C1… by owner group), title with a one-line "Proof:", code section column,
  "When" column, status checkbox, owner select. Life safety as a red left edge, not a pill. Why / added-because
  stay one click away.
- **Done sign-off:** green check, faint green row, and "Marked done by <role> · <date> · not checked against
  records". No strikethrough.
- **Milestone timeline** above the register: Design → DOB filing → Neighbors notified → Survey done →
  Excavation, evenly spaced on a line; current stage filled; a red ring where a checkpoint has life-safety
  items; a checkpoint is filled when all its items are done; under each, a count. Clicking one filters the list;
  clicking again clears.

## Non-goals

- Calendar dates or a Gantt chart (no planned start date is collected).
- Changing which items appear (rules unchanged).

## Anti-goals

- Implying 4site verified a "done" (it is a person's mark; say so on the row).
- A "When" the code doesn't support. Where the code states timing, use it; otherwise use the rule's stage.

## Approaches

- **A. Compliance register + milestone line (picked).** Looks like a sign-off sheet; uses data already present.
- B. Polish the current list. Cheaper, still reads as a to-do list.

## Design

**Phases** (backend, `actions/phases.py`): `phase_for(source_rule) -> (phase, when)` where phase is one of
`design | filing | notice | before_excavation | during_work`. Code rules by id: notice → notice "60 days before
work"; license → notice "Before work starts"; survey → before_excavation "Before excavation"; examination →
before_excavation "Before work, then during"; support_drawings, support_basis, underpinning → filing "Before
filing"; monitoring → during_work "During excavation"; foundation_protection, exposed_wall, underpinning_inspection,
hazard_elevations → during_work "During work". Hazard rules: earliest of their `stages` (pre_acquisition/design →
design, pre_filing → filing, construction → during_work). Document rules (`actions:model:*`, `actions:geotech:*`):
by id (underpin, support-basis, dewatering → filing; notice → notice; examination → before_excavation;
monitoring → during_work; the rest → design). Unknown → design.

**Contract:** `ActionItem` gains optional `phase`, `when`, `done_by_role`, `done_at`. `ActionItemUpdate` gains
optional `by_role`. The store keeps the four new item fields; setting status to done records `by_role` and now;
any other status clears them. Items saved before this read back with phase/when empty; the UI places them in
Design.

**UI:** `ChecklistStep.tsx` renders the timeline and the register; numbering and milestone grouping live in
`model.ts` as pure, tested functions. The acting role is sent as `by_role` with every status change.
