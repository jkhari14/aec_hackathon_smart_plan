# PreFlight: a proposed app structure

One teammate's working proposal for the web app and API, kept in its own folder for now so the
team can react before anything moves to the top level. Everything here reads the shared
`data_pull/` cache and the `checklist/` engine; it changes neither. Companion to the
[plan](../README-Camilo), the [data notes](../docs/data_and_code_notes.md), the
[data sources](../docs/api_data_sources.md) and the [checklist engine](../checklist/README.md).

## One brief, many readers

The API returns one **brief** per site: the site and its touching lots, every public record with its
date, the checklist engine's rows and summary, past failures, and lot and building geometry. The web page, the voice
agent and a Grasshopper script all read that same JSON, so each can be built without waiting on
the others.

- `GET /api/briefs` lists the sites. `GET /api/briefs/<slug>?as_of=YYYY-MM-DD` returns one brief,
  its checklist built from records dated before that day (the engine's `--as-of`).
- `python -m jahleel.api.brief.brief_export` writes every brief to `jahleel/web/public/demo_briefs/`, plus a copy
  for each replay date in `DEMO_AS_OF` (June 1 and November 11). When the API is down, the web
  page reads those files, so the demo never depends on a live server.
- The brief's types are generated from the API (`npm run types`), so a renamed field breaks the
  web build instead of blanking a screen.

## Layout

```
data_pull/             (shared) address in, public records for the site and touching lots out
checklist/             (shared) which Building Code duties apply, and the proof each needs
jahleel/
  api/
    preflight_api.py   the two routes
    brief/
      brief_models.py          the brief's shape (the contract every reader shares)
      brief_build.py           data_pull cache + checklist engine + geometry -> brief
      brief_records.py         each dataset's rows -> {id, date, status today, summary}
      brief_geometry_pull.py   tax-lot polygons and building footprints
      brief_export.py          static copies for the web page, plus api/openapi.json
  data/geometry/       lot polygons and footprints per cached site
  tests/               the brief's tests
  web/src/
    brief/             generated types, loading with the offline fallback, the as-of filter
    features/
      site_search/     site, project type, as-of date
      site_map/        lots, 3D footprints, click a lot to select it
      neighbors/       one card per touching lot
      site_record/     the site's records, newest first, stop-work mentions highlighted
      checklist/       one lane per party (the engine's fixed list); "adjoining owner view" turns proofs into asks
      precedents/      past incidents near the site
      export/          download the brief as JSON, or lots and buildings as GeoJSON
    ui/                the status badges
```

## Rules the screen keeps

- **Proof is never taken from public data** (the engine's rule). A row's proof is "not provided",
  "provided, not verified", or "reported, not read": a lead, a document a public source reports
  that nobody here has read, drawn dashed and linked to the report. A lead never closes a gap.
  Records beside a row are labeled "not proof". An open gap (the duty applies, no proof) gets a red
  edge. The statuses are closed sets in `brief_models.py`, so the API refuses anything else.
- **A failed query is not zero.** A dataset with status `error` shows "couldn't load", never a count.
- **A capped query is a floor.** A dataset that hit the 5,000-row cap shows "at least", and the
  record list says its oldest records are missing (which a replay needs most).
- **Show what the address matched**, not what was typed.
- **As-of means "dated before that day"**, the same rule as the engine. Status is today's, so the
  screen never says a record was open on that date.
- **Text written later shows only once it existed.** A stop-work mention, DOB's resolution of
  a 311 request, or a filing's approval is dated when it was written, which can be weeks after the record's own date.
  The replay shows the record but hides that text until its own date.
- **311 requests and DOB complaints are never added.** The same complaint can be in both and they
  share no key, so the neighbor cards count 311 requests apart and the record list says so.
- **Life-safety rows are tagged** (the engine's flag: the duty protects life safety).
- **No owner, applicant or respondent names.** The question is what was knowable, not who is to
  blame.
- **Past incidents carry a cause only as publicly reported**, or "under investigation" where
  officials say so; never "this would have prevented that" (the second team meeting).

## Run it

From the repo root:

```bash
python3 -m venv .venv && .venv/bin/pip install -r jahleel/api/requirements.txt
.venv/bin/python -m jahleel.api.brief.brief_geometry_pull   # once per new cached site
.venv/bin/python -m jahleel.api.brief.brief_export          # after any brief change
.venv/bin/uvicorn jahleel.api.preflight_api:app --port 8000
cd jahleel/web && npm install && npm run dev                # http://localhost:5173
.venv/bin/python -m unittest discover -s jahleel/tests -t .
```

Try the demo replay: `http://localhost:5173/?site=2625-bedford-ave-brooklyn&as_of=2026-06-01`.

## Where the open work plugs in

| Work | Where it lands | Suggested owner, by expertise in the transcript |
|---|---|---|
| Checklist rules and project inputs | `checklist/`; the brief carries its rows as they are | permitting and DOB data, with the structural engineer |
| Precedent library | fills `precedents` in the brief (causes as publicly reported or under investigation; the meeting found the construction-incidents dataset too vague); a map layer next | the structural engineer |
| Voice | reads `GET /api/briefs/<slug>` | the voice-agent developer |
| Grasshopper, Rhino, Revit | reads the brief or the GeoJSON export | the interoperability and BIM modeling specialist |
| Code and objection angle | wording of rows and the "why it's here" lines | the drawing and code review professional |

## Known gaps

- **Rhino and Revit need local feet.** The brief carries EPSG:4326 only. The
  [data sources](../docs/api_data_sources.md) recommend local feet from an EPSG:2263 origin; add that to
  `brief_geometry_pull.py` (MapPLUTO answers in 2263 with `outSR=2263`).
- **Address search is the demo list.** Free-text search needs the API to call `data_pull` live.
- **Project inputs are not wired.** The engine takes `--inputs` (excavation depth, exposed wall,
  access, underpinning); the API passes none yet, so 8 rows read "needs project input". The
  project-type picker is not wired either.
- **Project types stay open for now.** The second team meeting named alteration as a focus; it is
  noted for later. Until then the picker keeps every type (excavation next to existing, the hero
  site's case, stays the default), and types the demo doesn't need are retired once that's clear.
