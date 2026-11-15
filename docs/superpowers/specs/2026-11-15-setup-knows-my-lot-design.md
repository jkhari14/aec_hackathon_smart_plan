# Setup that already knows the lot

Date: 2026-11-15 · Status: proposed (Rishabh)

## Why

The project setup screen (`web/src/features/project_screen/SetupStep.tsx`) asks for work type, construction,
scope and roles, then drafts the checklist. It feels empty, and it is also missing facts the code turns on:
how deep the dig is, how tall the new building is, and what stage the job is at. Without them the checklist
over-calls (any excavation gets the preconstruction survey) or can't say which neighbors need monitoring.

The feeling we want: **"this is quick, it already knows my lot."** So we show what public records already say,
and ask only for the few facts that records don't hold and that change the checklist.

## Goals

- Show, at the top of setup, what 4site already knows about the lot, each fact with its source and date.
- Add three quick inputs that change the checklist: dig depth, new building height, stage.
- Changing an input visibly changes the drafted checklist (for example, depth 5-10 ft vs 10-20 ft).

## Non-goals

- No per-neighbor distance input: touching lots are at 0 ft, which we already know.
- No long professional form, no new document types.
- No change to the living-checklist rules from documents (`model_rules`, `geotech_rules`).

## Anti-goals

- A fact shown as known that the record doesn't actually say (AGENTS.md: every fact shows source and date;
  sample data is never passed off as real).
- Asking for something public data already answers.

## Approaches considered

- **A. "What we know" card + 3 quick fields (picked).** Shows the app's knowledge and fills the page with real
  facts; each field changes the list. A bit more to build.
- B. Just the 3 fields. Quicker, but reads as a longer form, the opposite of the feeling we want.
- C. Ask nothing; take depth from the uploaded drawing later. Page stays empty and the first checklist stays vague.

## Design

**"What we know" card** (top of setup). Read from the site profile the map already loads
(`/api/sites/{bbl}/profile`): touching neighbors (count, attached, year built range, storeys), lot size, flood
zone, e-designation if any, and the filed job type with its status and date. Each line names its source
(PLUTO, building footprints, FEMA, DOB NOW) and the as-of date. A fact we couldn't load says so ("Flood zone:
couldn't load"), never blank. Corrections are out of scope for this pass (see "Left to the builder").

**Three inputs** (below work type / construction, above scope):

- *How deep will you dig?* Not sure / Under 5 ft / 5-10 ft / 10-20 ft / Over 20 ft. Only shown when scope
  has excavation or foundation. Sent as a number: the band's upper bound (4.9, 10, 20, 21), so a rule with a
  threshold never under-calls. "Not sure" sends nothing, and depth-dependent rows stay "needs input".
- *New building height* (storeys, number). Only for new construction; for alterations the existing height from
  PLUTO is used, as today.
- *Stage*: Design / Filing / Construction. Defaults to Design.

**Checklist** (`actions/build.py`). `build_actions` accepts `excavation_depth_ft`, `proposed_storeys` and the
stage it already takes. The survey and monitoring rows use the existing logic in
`checklist/applicability.py` (`_survey`, `_monitoring`) with each touching lot at 0 ft, instead of the
blanket "excavation" scope. Over 20 ft, the support-drawings row says a NY State PE must seal them (3304.4.1).
The facade-cycle hazard uses `proposed_storeys` when given. A row whose rule needs an input we don't have
shows as "needs input: dig depth", not dropped and not assumed.

**API**: `/api/sites/{bbl}/actions` takes optional `excavation_depth_ft`, `proposed_storeys` (validated as
numbers ≥ 0). The project record stores the three answers with the setup, so other tabs see the same list.

## Left to the builder

- Exact layout of the card (compact list vs small tiles), within the existing project-screen styles.
- Whether a "Correct this" link is worth adding now or later.
- Test cases: depth bands against the survey thresholds (5, 10, 20 ft), attached neighbors at 0 ft, "Not sure".
