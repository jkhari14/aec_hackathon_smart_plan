FastAPI routers that replace the stubs in api/stubs.py. Owner: Jahleel (PR 4, 9).

| Router | Reads | Until its data lands |
| --- | --- | --- |
| `layers_router.py` | `data/layers/<layer_id>.geojson` (a `LayerFeatureCollection`), and `data/layers/catalog.json` when there is one | the labelled fixture |
| `cases_router.py` | `data/cases/cases.json` (a list of `Case`) | the labelled fixture |
| `search_router.py` | NYC Planning GeoSearch, live, top 5 matches with a tax lot | a GeoSearch failure is a 502, never `[]` |
| `sites_router.py` | the owner modules below | the labelled fixture |
| `projects_router.py` | the SQLite store in `api/store/` | none: projects are always real |

A data file that does not match its contract is a 500 that names the file, never an empty answer.
A layer listed in the catalog without its file comes back with `status: "error"` and no count.

**Layer filters.** `bbox=west,south,east,north` keeps features whose box meets it. `as_of=YYYY-MM-DD`
keeps features dated on or before it; an undated feature is kept only on a layer with no dates at all
(a zone, not an event). Over 5000 features the answer is cut, most severe and most recent first, with
`status: "capped"` and `feature_count` the number that matched.

**Plugging a site module in.** Define the function named here; nothing in this folder changes:

| Route | Module | Function |
| --- | --- | --- |
| `/api/sites/{bbl}/profile` | `site_profile` | `site_profile_for(bbl, job_type, stage, as_of)` |
| `/api/sites/{bbl}/similar` | `site_profile` | `similar_cases_for(bbl, hazard, severity_min)` |
| `/api/sites/{bbl}/warnings` | `early_warning` | `warnings_for(bbl, as_of)` |
| `/api/sites/{bbl}/pattern` | `foresight_model` | `pattern_score_for(bbl)` |
| `/api/sites/{bbl}/actions` | `actions` | `actions_for(bbl, stage)` |

Arguments come as keywords, already checked (the BBL, the closed sets, the date). Return the route's
contract model or a dict that matches it; an off-contract answer is a 500, never served. Raise
`HTTPException` for your own errors. To rename a function, edit `SITE_SOURCES` in `sites_router.py`.

**Python calls (for the chat).** The same answers without HTTP, each a `LoadedData(data, sample)`:
`load_site_part(part, bbl, job_type=, stage=, as_of=, hazard=, severity_min=)` in `sites_router.py`
(pass any options; each part gets only its own), `load_layer_catalog(root)` and `load_layer(...)` in
`layers_router.py`, `load_cases(root)` in `cases_router.py`, with `root = data_root()`. `sample` is True
while the answer is the fixture, not that site's data, so never present it as the site's. A load that
fails raises `DataUnavailable` (with the HTTP status the route would send), never an empty answer; bad
input raises `HTTPException(422)` as the route does.
