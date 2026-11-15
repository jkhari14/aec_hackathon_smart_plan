# Deferred: the part 3 review's open points

The third team meeting on 2026-11-14 ([transcript](../../planning/transcripts/team_brainstorm_2026-11-14_part_3.md))
left a few fixes to the docs for review. The review was skipped on 2026-11-14. Its open points
are kept here, and the lines they are about are left unchanged for now. Line numbers are as of
commit `7748719`.

## 1. The demo opening

- **What:** [data_and_code_notes.md](../data_and_code_notes.md) line 105 says "The demo hook is
  the Brooklyn collapse." The build doc says the opposite: [BUILD.md](../../BUILD.md) line 465
  ("Do not open with Nov 11") and [foresite_build_plan.md](../../planning/foresite_build_plan.md)
  line 68 ("Do not open with Nov 11. The hero site is decided later.").
- **Meanwhile:** follow the build doc. Line 105 was written before the third meeting.
- **Why put off:** the review was skipped, and the hero site is not confirmed yet.
  [demo_sites.json](../../data/demo_sites.json) ranks 861 Park Avenue first, and
  [demo_seeds.json](../../pitch/demo_seeds.json) says to change the hero there "once the team
  confirms it". In BUILD.md the story-and-demo owner shortlists the sites with the domain lead.
- **Brings it back:** the next edit to the data notes. The rewrite does not have to wait for the
  hero site: line 105 can just say the demo does not open on the collapse and point to
  `demo_sites.json`.

## 2. PreFlight becomes ForeSite in three docs

- **What:** the rename is already decided. Line 271 of the plan says "PreFlight becomes ForeSite
  in the UI and the docs." Five lines in three docs still say PreFlight:
  - [manual_data_imports.md](../manual_data_imports.md) lines 1 and 57
  - [api_data_sources.md](../api_data_sources.md) lines 1 and 70 (the data-sources owner's file)
  - [data_and_code_notes.md](../data_and_code_notes.md) line 1
- **Leave as is:** README.md line 19 and BUILD.md line 215. They name the earlier app and one of
  its files (`api/preflight_api.py`) on purpose.
- **Why put off:** only the edit is left, and it was part of the skipped review.
- **Brings it back:** the next edit to any of the three files. The two lines in
  `api_data_sources.md` go through its owner.

## 3. Hazardous materials in the checklist's "Not covered yet"

- **What:** in the third meeting (transcript line 1409), the list of things to flag early is
  "structural, like, civil and geotechnical, flooding, environmental, fire safety, hazardous
  material." The "Not covered yet" section of [checklist/README.md](../../checklist/README.md)
  (lines 166 to 170) names five hazards from the meetings, and hazardous materials is not one of
  them. The plan has since put it in scope (line 184, "Contamination and hazardous materials").
  [actions/rules.json](../../actions/rules.json) now adds fire, flood, contamination, facade and
  weather rows to the checklist's own, and the section does not point to them. Lines 99 to 101 of
  the data notes make the same claim ("no rows and no data source in the pull yet").
- **Why put off:** it is wording only, and it was part of the skipped review.
- **Brings it back:** the next edit to `checklist/README.md` or the data notes.

## Settled by the build doc, so not kept here

- **"Not exhaustive" on the checklist:** the plan (line 72) labels checklists "not exhaustive" and
  keeps a "What ForeSite doesn't know" panel always visible. BUILD.md line 107 shows the
  limitations on every screen. The checklist's own JSON caveats do not say it, which matters only
  if that file is shown outside the app.
