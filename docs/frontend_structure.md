# PreFlight: app structure

How the web app and API are laid out, and where each person's work plugs in. Companion to the
[plan](../README-Camilo), the [data notes](data_and_code_notes.md), the
[data sources](api_data_sources.md) and the [checklist engine](../checklist/README.md).

## One brief, many readers

The API returns one **brief** per site: the site and its touching lots, every public record with its
date, the checklist engine's rows and summary, past failures, and lot and building geometry. The web page, the voice
agent and a Grasshopper script all read that same JSON, so each can be built without waiting on
the others.

- `GET /api/briefs` lists the sites. `GET /api/briefs/<slug>?as_of=YYYY-MM-DD` returns one brief,
  its checklist built from records dated before that day (the engine's `--as-of`).
- `python -m api.brief.brief_export` writes every brief to `web/public/demo_briefs/`, plus a copy
  for each replay date in `DEMO_AS_OF` (June 1 and November 11). When the API is down, the web
  page reads those files, so the demo never depends on a live server.
- The brief's types are generated from the API (`npm run types`), so a renamed field breaks the
  web build instead of blanking a screen.

## Layout

```
data_pull/           address in, public records for the site and touching lots out
checklist/           which Building Code duties apply, and the proof each needs
api/
  preflight_api.py   the two routes
  brief/
    brief_models.py          the brief's shape (the contract every reader shares)
    brief_build.py           data_pull cache + checklist engine + geometry -> brief
    brief_records.py         each dataset's rows -> {id, date, status today, summary}
    brief_geometry_pull.py   tax-lot polygons and building footprints
    brief_export.py          static copies for the web page, plus api/openapi.json
web/src/
  brief/             generated types, loading with the offline fallback, the as-of filter
  features/
    site_search/     site, project type, as-of date
    site_map/        lots, 3D footprints, click a lot to select it
    neighbors/       one card per touching lot
    site_record/     the site's records, newest first, stop-work mentions highlighted
    checklist/       one lane per party (the engine's fixed list); "adjoining owner view" turns proofs into asks
    roast/           the intensity dial and the roast line under each row
    precedents/      past failures near the site
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
- **Show what the address matched**, not what was typed.
- **As-of means "dated before that day"**, the same rule as the engine. Status is today's, so the
  screen never says a record was open on that date.
- **On life-safety rows (the engine's flag) the serious line comes first**, with the roast under it.
- **No owner, applicant or respondent names.** The question is what was knowable, not who is to
  blame.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r api/requirements.txt
.venv/bin/python -m api.brief.brief_geometry_pull      # once per new cached site
.venv/bin/python -m api.brief.brief_export             # after any brief change
.venv/bin/uvicorn api.preflight_api:app --port 8000
cd web && npm install && npm run dev                   # http://localhost:5173
.venv/bin/python -m unittest discover -s tests -t .
```

Try the demo replay: `http://localhost:5173/?site=2625-bedford-ave-brooklyn&as_of=2026-06-01`.

## Where the open work plugs in

| Work | Where it lands | Suggested owner, by expertise in the transcript |
|---|---|---|
| Checklist rules and project inputs | `checklist/`; the brief carries its rows as they are | permitting and DOB data, with the structural engineer |
| Precedent library | fills `precedents` in the brief; a map layer next | the structural engineer |
| Roast lines and the character | fills `roast` on each row; `roast/` renders it | the design technologist (computation and BIM) |
| Voice | reads `GET /api/briefs/<slug>` | the voice-agent developer |
| Grasshopper, Rhino, Revit | reads the brief or the GeoJSON export | the interoperability and BIM modeling specialist |
| Code and objection angle | wording of rows and the "why it's here" lines | the drawing and code review professional |

## Known gaps

- **Rhino and Revit need local feet.** The brief carries EPSG:4326 only. The
  [data sources](api_data_sources.md) recommend local feet from an EPSG:2263 origin; add that to
  `brief_geometry_pull.py` (MapPLUTO answers in 2263 with `outSR=2263`).
- **Address search is the demo list.** Free-text search needs the API to call `data_pull` live.
- **Project inputs are not wired.** The engine takes `--inputs` (excavation depth, exposed wall,
  access, underpinning); the API passes none yet, so 8 rows read "needs project input". The
  project-type picker is not wired either.
- **A filing's summary can name a later date** (for example "Approved: 2026-06-03" on a June 1
  replay), because a filing is one row with its current status.
