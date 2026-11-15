# ForeSite: build doc

How the 8 of us build ForeSite in parallel, each with our own coding agent, and merge it in the right
order. The product plan is [planning/foresite_build_plan.md](planning/foresite_build_plan.md); this
file is who builds what, in which order, and with which prompt.

Deadline: **Sun Nov 15, 12:00 PM**. Feature freeze at **11:00 AM**.

## Start your goal

Your agent runs your whole part as one long-running goal: it pulls `main`, builds your PRs in the
order below, opens each one on GitHub, and keeps them rebased and green. It does the git work for you
and explains each step. The steps live in one skill, `.claude/skills/foresite-goal/SKILL.md`, which
Cursor and Claude Code both load; `tools/foresite_status.py` tells the agent where you stand.

**Once, on your laptop** (ask your agent to help with any step):

1. Install the GitHub CLI (`brew install gh`) and run `gh auth login` (GitHub.com, HTTPS, browser).
2. `gh repo clone jkhari14/aec_hackathon_smart_plan` and open that folder in Cursor, or `cd` into it
   and run `claude`.
3. Check where you stand: `python3 tools/foresite_status.py <your name>`.

**Start the goal.** In **Cursor** (Agent chat, a new chat):

```text
/goal I'm <your name> on the ForeSite team. Follow the foresite-goal skill: build every PR in my section
of BUILD.md in order until each one is open on GitHub with green CI.
```

If `/goal` is not in your Cursor yet, send the same text without `/goal`, or run `/foresite-goal <your name>`.

In **Claude Code** (in the repo folder):

```text
/foresite-goal <your name>
```

**After Jacob posts a merge in Slack,** run the same command again in a new chat. The agent rebases your
open PRs, fixes review comments and CI, and moves on to your next PR.

Until PR 0 has merged, `contracts/`, `api/` and `web/` do not exist yet; the goal tells you to do the
"Before PR 0" prep in your section (research, data checks, sketches) instead.

## Who builds what

| Person | Role | PRs |
|---|---|---|
| Jacob | Lead, integrator, merge captain; early warnings | 0, 7, 19 |
| Camilo | UX/UI lead: design system, shell, panels, polish | 1, 10, 15 |
| Shandon | Map and 3D | 5, 14 |
| Jahleel | API, project workspace, chat | 4, 9 |
| Lise | Data sources | 2, 16 |
| Rishabh | Intelligence: profile, similarity, ML, model input | 6, 12, 13 |
| Hongyu | Domain lead (structural): case library, action rules, review | 3, 8, 17 |
| Ethnie | Story and demo: copy, demo sites, pitch | 11, 18 |

## PR order

A PR can be **built** at any time against fixtures. It **merges** only after the PRs in its "depends
on" column have merged. Jacob merges, in this order, and posts each merge in Slack.

| PR | Wave | Owner | What | Depends on | Target |
|---|---|---|---|---|---|
| 0 | 0 | Jacob | Contracts, fixtures, API stubs, app skeletons, CI, ForeSite rename | | Sat 7:30 PM |
| 1 | 1 | Camilo | Design system and app shell on fixtures | 0 | Sat 11 PM |
| 2 | 1 | Lise | `city_layers` v1: citywide layers as GeoJSON with hazard and severity | 0 | Sat 11 PM |
| 3 | 1 | Hongyu | Case library v1 (20+ cases) | 0 | Sat 11 PM |
| 4 | 1 | Jahleel | API routers on real files, SQLite project store | 0 | Sat 11 PM |
| 5 | 2 | Shandon | Map home: citywide map, clustering, fly-to, layer panel | 1, 4 | Sun 4 AM |
| 6 | 2 | Rishabh | Site profile and explainable similarity | 2, 3, 4 | Sun 4 AM |
| 7 | 2 | Jacob | Early-warning rules, citywide watchlist, warnings panel | 1, 2, 4 | Sun 4 AM |
| 8 | 2 | Hongyu | Action rules by discipline | 4 | Sun 4 AM |
| 9 | 2 | Jahleel | Chat tools, chat panel, project panel | 1, 4 | Sun 4 AM |
| 10 | 2 | Camilo | Site panel, similar-case panel, actions panel | 1, 4 | Sun 4 AM |
| 11 | 2 | Ethnie | Copy strings, limitations wording, candidate demo sites | 1 | Sun 4 AM |
| 12 | 3 | Rishabh | Pattern model and sequence mining | 6, 7 | Sun 8 AM |
| 13 | 3 | Rishabh | Model input: Revit `structural_model.json` and drawing vision | 6, 9 | Sun 8 AM |
| 14 | 3 | Shandon | 3D tiles, party-wall edge, similar-case arcs | 5, 6 | Sun 8 AM |
| 15 | 3 | Camilo | UX polish pass after the usability test | 5, 10 | Sun 9 AM |
| 16 | 3 | Lise | Remaining sources and the scheduled refresh | 2 | Sun 8 AM |
| 17 | 3 | Hongyu | Case library v2 (40+) and review fixes | 3, 6 | Sun 8 AM |
| 18 | 4 | Ethnie | Pitch materials and final demo seeds | 11 | Sun 10:30 AM |
| 19 | 4 | Jacob | Deploy, cache demo data, freeze | all | Sun 11 AM |

## Rules every agent follows

- **Your paths only.** Each section lists the paths you own. Do not edit anyone else's. A change to
  `contracts/` is its own small PR to Jacob, made before the PR that needs it.
- **Branch and title.** Branch `<name>/pr<n>-<short-topic>` from the latest `main` (or from your own
  open PR when the new one builds on it; the status script says which). PR title
  `[W<wave>/PR<n>] <what it does>`. One PR per row above; keep it small.
- **Before opening:** rebase on `main`, run `python -m unittest discover -s tests -t .` and
  `cd web && npm run build`, and fill in the PR template (what, how tested, screenshots for UI).
- **Fixtures first.** Build against `contracts/fixtures/` so nobody waits. Switch to real data only
  once the upstream PR has merged.
- **`jahleel/` is a read-only reference.** Copy or port what fits into your own paths; never edit it.
- **Product rules** (from the team's meetings):
  - No names of owners, applicants, permit holders or contractors.
  - Every fact shows its source and date. A failed query shows "couldn't load", never zero. A capped
    query is "at least".
  - Proof is never inferred from public data. Housing violations are shown but never scored as
    structural risk.
  - As-of means "dated before that day".
  - Past cases carry a cause only "as publicly reported", or "under investigation". No blame, no
    "would have prevented".
  - The pattern score is "compared with similar sites", never a prediction that a building will fail.
  - Limitations are visible on every screen: ForeSite is not exhaustive and not engineering advice.
- **UX bar** (plan section "UX and UI: the differentiator"): dark-first, calm, nothing cluttered, blank
  or unexplained; every element answers "why am I seeing this?". Fewer features done beautifully beat
  more features done roughly.
- **Secrets** stay in the environment (`ANTHROPIC_API_KEY`, `VITE_GOOGLE_MAPS_KEY`,
  `SOCRATA_APP_TOKEN`), never in code or commits.
- **Do not commit** the unredacted transcripts or PDFs in the repo root; the redacted transcripts are
  in `planning/transcripts/`.

## Shared contracts (built in PR 0)

Everyone builds against these. The pydantic models in `api/contracts.py` are the source of truth;
`.venv/bin/python -m contracts.generate` writes the JSON Schemas in `contracts/schemas/` and
`api/openapi.json`, and `npm run contracts` in `web/` turns that into `web/src/api_types.ts`, with
friendly names in `web/src/contracts.ts`. One fixture per schema lives in `contracts/fixtures/` (real
2625 Bedford records and real reported cases). `tests/test_contracts.py` fails if a fixture stops
matching or the generated files are stale. To change a contract, edit `api/contracts.py`, regenerate,
update the fixture, and send it as its own small PR before the PR that needs it.

- **Hazards:** `structural`, `geotech`, `fire`, `flood`, `contamination`, `facade`, `weather`,
  `construction_safety`.
- **Severity:** `0` signal (complaint), `1` enforcement (violation, stop-work, vacate), `2` incident
  (injury, partial collapse), `3` catastrophic (fatality, full collapse).
- **Stages:** `pre_acquisition`, `design`, `pre_filing`, `construction`. **Roles:** `architect`,
  `structural_engineer`.
- **`LayerCatalogEntry`:** `layer_id`, `name`, `description`, `hazard`, `source_name`, `source_url`,
  `updated_at`, `feature_count`, `status` (`ok`, `error`, `capped`), `default_on`.
- **`LayerFeatureCollection`:** `layer` (its catalog entry) and `features[]`, each a GeoJSON Feature
  whose `properties` are `id`, `layer_id`, `hazard`, `severity`, `date`, `title`, `summary`,
  `source_name`, `source_url`, `bbl` (nullable), `record_id`.
- **`SearchResult`:** `label`, `bbl`, `bin`, `lat`, `lon`.
- **`Case`:** `id`, `title`, `address`, `bbl`, `lat`, `lon`, `date`, `hazards[]`, `severity`,
  `job_type`, `work_types[]`, `conditions` (`neighbor_year_built`, `attached`, `construction`, `soil`,
  `flood_zone`, `excavation_depth_ft`, and any other reported condition), `summary`,
  `cause_as_reported` (null unless `cause_status` is `reported`), `cause_status` (`reported`,
  `under_investigation`, `unknown`), `sources[]` (`name`, `url`, `date`; at least one).
- **`SiteProfile`:** `bbl`, `bins[]`, `address_matched`, `lat`, `lon`, `lot` (`zoning`, `built_far`,
  `max_far`, `lot_area_sqft`, `year_built`, `floors`, `building_class`, `landmark`,
  `historic_district`), `neighbors[]` (`bbl`, `bins[]`, `address`, `attached`, `year_built`, `floors`,
  `building_class`, `height_ft`, `shared_wall_ft`), `job_type`, `work_types[]`, `work_types_inferred`,
  `stage`, `soil`, `bedrock_depth_ft`, `flood` (`fema_zone`, `stormwater`, `sandy_inundation`),
  `e_designation`, `signals[]` (`id`, `hazard`, `severity`, `title`, `explanation`, `record_ids[]`,
  `source_name`, `date`), `structural_model` (nullable), `datasets[]` (`key`, `name`, `status`,
  `count`, `source_url`: an error is never shown as zero), `as_of`.
- **`SimilarCases`:** `bbl` and `results[]`, each `case_id`, `case` (the full `Case`), `score` (0 to 1),
  `matched_on[]`, `differs_on[]`.
- **`EarlyWarning`:** `id`, `rule_id`, `hazard`, `severity`, `title`, `explanation`,
  `evidence_record_ids[]`, `first_seen`, `as_of`.
- **`WarningRuleCheck`:** `rule_id`, `title`, `status` (`ok`, `error`, `not_applicable`), `detail`,
  `warnings` (how many it raised), `sources[]`, `as_of`. One per rule, so a rule that could not run is
  shown as "couldn't check", never as "no warning".
- **`PatternScore`:** `bbl`, `score`, `percentile_vs_similar`, `compared_with`, `top_factors[]`
  (`feature`, `value`, `contribution`), `model_version`, `calibration_note`.
- **`ActionItem`:** `id`, `discipline` (`architect`, `structural`, `geotech`, `contractor`), `hazard`,
  `title`, `why`, `code_ref`, `proof_needed`, `status` (`open`, `in_progress`, `done`,
  `not_applicable`), `owner_role`, `source_rule`, `life_safety`.
- **`Project`:** `id`, `name`, `site_bbl`, `stage`, `members[]` (`name`, `role`), `items[]`
  (`ActionItem`), `notes[]`, `pins[]`, `structural_model`, `created_at`.
- **`StructuralModel`:** `source` (`revit`, `drawing`), `material`, `gravity_system`,
  `lateral_system`, `foundation_type`, `bearing_walls_on_lot_line[]` (`id`, `side`, `material`,
  `length_ft`), `levels`, `confidence`.
- **`ChatRequest` / `ChatResponse`:** `question`, `bbl`, `project_id`, `as_of` in; `answer_parts[]`
  (`kind`: `public_record`, `case`, `ai_suggestion`, `web`, `user_input`; `text`, source fields),
  `actions[]` (`fly_to`, `toggle_layer`, `pin`), `offline` out.

**API** (stubs serving fixtures in PR 0, made real by the owners):
`GET /api/layers`, `GET /api/layers/{layer_id}?bbox=&as_of=`, `GET /api/search?q=`,
`GET /api/sites/{bbl}/profile?job_type=&stage=&as_of=`, `GET /api/sites/{bbl}/similar?hazard=&severity_min=`,
`GET /api/sites/{bbl}/warnings?as_of=`, `GET /api/sites/{bbl}/warnings/checks?as_of=`, `GET /api/sites/{bbl}/pattern`,
`GET /api/sites/{bbl}/actions?stage=`, `GET /api/cases`, `GET /api/cases/{id}`,
`POST /api/projects`, `GET /api/projects/{id}`, `POST|PATCH /api/projects/{id}/items`,
`POST /api/projects/{id}/notes`, `POST /api/projects/{id}/pins`, `POST /api/projects/{id}/model`,
`POST /api/chat`.

Stub answers carry the header `X-ForeSite-Fixture: true`, and the web client (`web/src/api/client.ts`)
also falls back to the fixtures when the API is down; either way the UI shows "Sample data". To make a
route real, include your router above `stubs.router` in `api/main.py` (the first matching route wins)
and delete the stub from `api/stubs.py` in the same PR.

## Repo layout after PR 0

```
contracts/        schemas and fixtures (Jacob)
api/              ForeSite FastAPI app: main.py, contracts.py, stubs.py (Jacob), routers/ and store/ (Jahleel)
web/              ForeSite app: Vite, React, MapLibre, deck.gl (see feature owners below)
city_layers/      citywide source pulls (Lise)
site_profile/     site profile and similarity (Rishabh)
foresight_model/  pattern model and sequence mining (Rishabh)
model_input/      Revit and drawing input (Rishabh)
early_warning/    sequence rules and watchlist (Jacob)
actions/          action rules by discipline (Hongyu)
data/cases/       case library (Hongyu)
data/layers/      generated layer files (Lise)
data/demo_sites.json   demo sites (Ethnie)
pitch/            deck, video script, persona wrap-up (Ethnie)
data_pull/, checklist/, manual_imports/   existing shared modules: reuse, extend with care
jahleel/          read-only reference
planning/         plan and transcripts
```

---

## Jacob: lead, integrator, merge captain

**Owns:** `contracts/`, `api/main.py`, `api/contracts.py`, `api/stubs.py`, `web/src/contracts.ts`, `early_warning/`,
`web/src/features/early_warnings/`, `data/layers/watchlist.geojson`, `.github/`, `.claude/`, `tools/`, `.gitignore`, `deploy/`, `AGENTS.md`, `BUILD.md`.
Also merges every PR in order and runs the end-to-end check after each wave.

**References in `jahleel/`:** `api/brief/brief_models.py` (closed status sets), `api/preflight_api.py`
(app wiring), `api/brief/brief_export.py` (static fallback), `web/src/brief/brief_as_of.ts`,
`web/package.json` (stack versions).

**PR 0 (wave 0): contracts and skeleton.** JSON Schemas and one fixture each for every contract above;
pydantic models and TS types; `api/main.py` with every route stubbed to return fixtures; a `web/`
Vite + React 19 + Tailwind 4 + MapLibre + deck.gl skeleton that renders a placeholder map and reads
`/api/layers` (falls back to fixtures when the API is down); empty owner folders with a README line
each; `.github/pull_request_template.md`; CI running unittest and `npm run build`; ForeSite name.
Done when `uvicorn api.main:app` serves every route, `npm run build` passes, and CI is green.

**PR 7 (wave 2): early warnings.** Rules over a site's dated records with as-of (each rule a small
function with an id, hazard, severity and explanation):
- an adjacent-protection violation (complaint 03, ECB text) with no follow-up record in 21 days
- a stop-work mention followed by a "work continued" violation
- complaint 30, 14, 16 or 5C within 90 days of an earth-work filing on a touching lot
- heavy rain (Open-Meteo, over 25 mm a day) or a freeze-thaw day during an open excavation
Also the citywide watchlist (active earth-work, foundation or SOE filings next to attached pre-1940
lots) written to `data/layers/watchlist.geojson`, `GET /api/sites/{bbl}/warnings`, and the warnings
panel in Camilo's design system. Test each rule on 2625 Bedford as of 2026-06-01.

**PR 19 (wave 4): deploy.** Web and API deployed, demo sites cached, static fallback on, freeze at 11.

**Role prompt:**
```text
I'm Jacob, lead and integrator for ForeSite. Read AGENTS.md, BUILD.md and planning/foresite_build_plan.md.
Build PR 0 from my section of BUILD.md: every contract in "Shared contracts" as a JSON Schema with one
fixture, pydantic models in api/contracts.py, TS types in web/src/contracts.ts, api/main.py with every
route stubbed to serve fixtures, a web/ skeleton (Vite, React 19, Tailwind 4, MapLibre, deck.gl) with a
fixture fallback, owner folders, a PR template and CI. Use jahleel/ only as a reference. Keep it small
and green; others branch from it.
```

---

## Camilo: UX/UI lead

**Owns:** `web/src/design/` (tokens, components), `web/src/app/` (shell, layout, routing, command bar),
`web/src/features/site_panel/`, `web/src/features/similar_cases/`, `web/src/features/actions/`,
`web/src/features/limitations/`. Runs the design review after each wave and the usability test with
Hongyu (structural engineer) and an architect.

**References in `jahleel/`:** `web/src/app.css`, `web/src/ui/evidence_badge.tsx` (source labels),
`web/src/features/checklist/checklist_lanes.tsx` (lanes by party).

**Before PR 0:** sketch the key screens (city view, site view, a similar case, an early warning, the
layer panel, the chat) and pick the tokens.

**PR 1 (wave 1): design system and shell.** Dark-first tokens (color, type with tabular numbers,
8-point spacing, hazard and severity colors, AA contrast), core components (panel, card, chip, source
label, badge, skeleton, empty and error states, toggle, tabs), the shell (full-bleed map slot, floating
panels that slide over the map, command bar on `/` and Cmd-K, keyboard shortcuts, shareable URLs), the
always-visible limitations panel, reduced-motion support. All on fixtures.

**PR 10 (wave 2): site, similar-case and action panels.** The site panel opens with the top 3 signals
(life safety first) and tucks lot facts into a section; similar cases as cards with "matches on" and
"differs on", filters for hazard, severity and date; actions grouped by discipline with owner, status
and proof needed. Hover and click explain every item and its source.

**PR 15 (wave 3): polish.** Motion (150 to 300 ms), loading skeletons everywhere, empty and error
states, copy pass with Ethnie, fixes from the usability test.

**Role prompt:**
```text
I'm Camilo, UX/UI lead for ForeSite. Read AGENTS.md, BUILD.md (my section and the shared rules) and the
"UX and UI: the differentiator" section of planning/foresite_build_plan.md. Build my next unmerged PR.
UX is our differentiator: dark-first, calm, fast, beautiful, never cluttered or unexplained. Stay in my
paths, use the contracts and fixtures, check the jahleel/ references in my section, and include
screenshots in the PR.
```

---

## Shandon: map and 3D

**Owns:** `web/src/features/city_map/`, `web/src/features/layer_panel/`.

**References in `jahleel/`:** `web/src/features/site_map/site_map_view.tsx` (MapLibre, 3D footprints,
click to select), `web/src/features/export/brief_geojson.ts`, `data/geometry/*.json`.

**Before PR 0:** prototype MapLibre with a deck.gl overlay and check a Google Maps key with the Map
Tiles API (photorealistic 3D tiles) if the team has one.

**PR 5 (wave 2): map home.** Full-bleed citywide map (dark style), deck.gl layers for every entry in
`/api/layers` with clustering and fade by zoom (the city must never look on fire), search and click to
pick a site, a cinematic fly-to, the site and touching neighbors highlighted, extruded footprints, the
layer panel (every source with toggle, status, count, source link, updated date).

**PR 14 (wave 3): 3D and storytelling.** Google Photorealistic 3D Tiles when `VITE_GOOGLE_MAPS_KEY` is
set, styled extrusions with soft lighting otherwise; the shared party wall as a glowing edge; similar
cases arcing in from across the city; camera keeps the site in view as panels open.

**Role prompt:**
```text
I'm Shandon, map and 3D for ForeSite. Read AGENTS.md, BUILD.md (my section and the shared rules) and the
UX section of planning/foresite_build_plan.md. Build my next unmerged PR: the map is the home of the app
and the centerpiece of the demo. Use MapLibre with a deck.gl overlay, the layer contracts and fixtures,
Camilo's design tokens, and the jahleel/ map as a reference. Keep it fast (city map paints under 2
seconds) and calm (cluster and fade by zoom). Include a screen recording in the PR.
```

---

## Jahleel: API, project workspace, chat

**Owns:** `api/routers/`, `api/store/`, `web/src/features/chat/`, `web/src/features/project/`.

**References in `jahleel/`:** `api/chat/` (answers typed by source, wording checks, saved offline
answers, the Anthropic call), `api/brief/brief_records.py`, `api/brief/brief_build.py`,
`web/src/features/chat/`, `web/src/brief/brief_load.ts` (offline fallback). It is your own earlier
work: port what fits.

**PR 4 (wave 1): routers and project store.** Replace the stubs with real routers: layers (reads
`data/layers/`), search (GeoSearch), sites (calls `data_pull` and the modules as they land, fixtures
until then), cases (reads `data/cases/`), projects (SQLite: projects, members with roles architect and
structural engineer, items, assignments, notes, pins, uploads). Two browser tabs must work as two
roles on one project.

**PR 9 (wave 2): chat and project panel.** `POST /api/chat` answering from the site's profile,
records, similar cases, warnings and actions, plus web search, each answer part labeled by source;
tools to toggle layers, fly to a record and pin an answer to the project; the docked, collapsible
chat panel with source chips that fly the map; the project panel (members, assigned items, notes,
pins). Offline saved answers when there is no key.

**Role prompt:**
```text
I'm Jahleel, API, project workspace and chat for ForeSite. Read AGENTS.md, BUILD.md (my section and the
shared rules) and planning/foresite_build_plan.md. Build my next unmerged PR in api/routers, api/store,
web/src/features/chat and web/src/features/project. Port what fits from my jahleel/ code, follow the
contracts exactly, keep keys in the environment, and keep the offline fallback working.
```

---

## Lise: data sources

**Owns:** `city_layers/`, `data/layers/`. Extends `data_pull/` with care where a site-level pull is
needed (shared module: small, tested changes).

**References in `jahleel/`:** `api/brief/brief_records.py` (dataset rows to dated summaries),
`api/brief/brief_geometry_pull.py`. Also read `docs/api_data_sources.md`, `docs/data_and_code_notes.md`
and `data_pull/lot_records.py`.

**Before PR 0:** the hour-1 data gate: one live query per source in the plan's "Data sources" list;
confirm the NYS DEC remediation dataset ID; note row counts, date ranges and traps.

**PR 2 (wave 1): `city_layers` v1.** One module per source writing `data/layers/<layer_id>.geojson`
plus a catalog entry, every feature tagged with hazard and severity: construction incidents
`bf97-mjsy`, HPD vacate orders `tb8q-a3ar`, FDNY vacates `n5xc-7jfa`, facade filings `xubg-57si`
(UNSAFE and SWARMP), DOB complaints in the structural codes (03, 14, 16, 30, 54, 2K, 5C), Sandy
Inundation `uyj8-7rv5`, E-Designations `hxm3-23vy`. Also the job type to work types table (DOB NOW
structure) in `city_layers/work_types.py`. Failed pulls write `status: error`, capped pulls
`status: capped`.

**PR 16 (wave 3): remaining sources and refresh.** FEMA flood zones, DEP Stormwater Flood Maps
`9i7c-xyvv`, 311 flooding complaints, NYS DEC remediation sites, site-level samplers for USGS depth to
bedrock, USDA soil (Soil Data Access) and Open-Meteo weather; a scheduled refresh script.

**Role prompt:**
```text
I'm Lise, data sources for ForeSite. Read AGENTS.md, BUILD.md (my section and the shared rules),
docs/api_data_sources.md and the "Data sources" section of planning/foresite_build_plan.md. Build my
next unmerged PR in city_layers/ and data/layers/. Every feature carries hazard, severity, date, source
name and URL; failed queries are errors, never zero; no owner or applicant names. Reuse data_pull/ and
the jahleel/ references where they fit.
```

---

## Rishabh: intelligence

**Owns:** `site_profile/`, `foresight_model/`, `model_input/`.

**References in `jahleel/`:** `api/brief/brief_build.py`, `api/chat/chat_model_call.py` (model call
pattern). Also `checklist/neighbor_context.py` and `data_pull/lot_neighbors.py`.

**Before PR 0:** design the feature vector and the label; check how many touching-lot pairs with an
earth-work filing the open data gives.

**PR 6 (wave 2): profile and similarity.** `site_profile/` builds a `SiteProfile` from `data_pull`, PLUTO,
footprints, `city_layers` and the work-type table; `GET /api/sites/{bbl}/similar` ranks cases and
open-data incidents by a weighted, explainable similarity (neighbor age and attachment, construction,
work types, soil, flood, signals) with `matched_on` and `differs_on`.

**PR 12 (wave 3): pattern model and sequence mining.** Label: a severe signal or incident on a lot
within 12 months of an earth-work filing on a touching lot (codes 30, 14, 16, 5C, vacates,
`bf97-mjsy`). Gradient boosting with feature attributions, a time-split evaluation and calibration,
saved with a model card. `GET /api/sites/{bbl}/pattern` returns a `PatternScore` shown as "compared
with similar sites". Mine the event sequences that most often came before incidents and hand them to
Jacob as candidate rules.

**PR 13 (wave 3): model input.** `POST /api/projects/{id}/model` accepts the Revit reader's
`structural_model.json` (stand-in fixture until the reader's output arrives); a drawing PDF goes to a
vision model that classifies the structural system. Either updates the profile, similar cases and
actions.

**Role prompt:**
```text
I'm Rishabh, intelligence for ForeSite. Read AGENTS.md, BUILD.md (my section and the shared rules) and
the "Main build: Foresight" section of planning/foresite_build_plan.md. Build my next unmerged PR in
site_profile/, foresight_model/ or model_input/. Every score must explain itself; the model is "compared with
similar sites", never a failure prediction; report the evaluation honestly in a model card.
```

---

## Hongyu: domain lead (structural)

**Owns:** `data/cases/`, `actions/`. Reviews the similarity features (PR 6), the model label (PR 12)
and the wording of warnings and actions. Is the structural engineer in the usability test.

**References in `jahleel/`:** `web/src/features/precedents/precedent_list.tsx`,
`web/src/features/checklist/checklist_lanes.tsx`. Also `checklist/checklist_rules.py` (the BC 3309
duties) and the case list in the plan.

**Before PR 0:** list the cases to cover across hazards and severity (start with the plan's seed list:
211 E 34th, 714 39th, 656 Myrtle, 102-02 Liberty, 97 Quincy, 1915 Billingsley, 57 Ann, 235 E 42nd,
161 Maiden Lane, 1321 Flatbush; add gas explosions, facade deaths, crane incidents, Ida basement
flooding, fire vacates).

**PR 3 (wave 1): case library v1.** 20+ cases in `data/cases/cases.json` following the `Case`
contract, each with sources and a cause only as publicly reported or under investigation, tagged with
hazards, severity, job type, work types and conditions.

**PR 8 (wave 2): action rules.** `actions/rules.json` plus a small builder that combines the
`checklist/` engine's BC 3309 rows with hazard rules (flood, fire, contamination, facade, weather),
grouped for architect, structural engineer, geotech and contractor; each with why, code reference,
proof needed and a life-safety flag; `GET /api/sites/{bbl}/actions`.

**PR 17 (wave 3): case library v2 and review fixes.** 40+ cases, fixes from the reviews.

**Role prompt:**
```text
I'm Hongyu, the structural engineer and domain lead for ForeSite. Read AGENTS.md, BUILD.md (my section
and the shared rules) and planning/foresite_build_plan.md. Help me build my next unmerged PR in
data/cases/ or actions/. Every case needs real sources; state a cause only as publicly reported or under
investigation; never blame. Ask me to confirm any engineering judgment before you write it.
```

---

## Ethnie: story and demo

**Owns:** `web/src/copy/` (all user-facing strings, which the components import), `data/demo_sites.json`,
`pitch/`.

**References in `jahleel/`:** its README's "Rules the screen keeps" (wording), `api/chat/chat_wording_checks.py`.

**Before PR 0:** the pitch story (5 minutes: about 1 minute slides, 1 minute video, 1 to 2 minutes
live demo, persona wrap-up for the architect and the structural engineer); shortlist demo sites with
Hongyu. Do not open with Nov 11.

**PR 11 (wave 2): copy and demo sites.** All UI strings in `web/src/copy/`, the limitations wording,
empty and error state copy; 2 to 3 candidate hero sites in `data/demo_sites.json` with why each works.

**PR 18 (wave 4): pitch.** Deck outline and slides in `pitch/`, the 1-minute video script and shot
list, the persona wrap-up, final demo seeds.

**Role prompt:**
```text
I'm Ethnie, story and demo for ForeSite. Read AGENTS.md, BUILD.md (my section and the shared rules) and
planning/foresite_build_plan.md. Help me build my next unmerged PR in web/src/copy/, data/demo_sites.json
or pitch/. Tone: calm, factual, no blame, no "would have prevented"; the product is for architects and
structural engineers working together.
```
