# city_layers

Pulls citywide public sources and writes each one as a map layer in `data/layers/`, every record
tagged with a hazard and a severity. Plain Python 3.9+, no packages, no API keys. It reuses
`data_pull`'s Open Data client, the checklist's date parser and the hand-imported complaint code key.

```bash
python3 -m city_layers.build_layers                    # pull every layer (about 8 minutes)
python3 -m city_layers.build_layers sandy_inundation   # pull only the named layers
python3 -m city_layers.build_layers --catalog          # no pull: rebuild catalog.json from the files
python3 -m city_layers.build_layers --list             # the layer ids and their sources
python3 -m city_layers.refresh_layers --every 6        # refresh now, then every 6 hours
python3 -m city_layers.site_context 40.638718 -73.953869 --bbl 3052110073   # one site, asked of the sources
.venv/bin/python -m unittest tests.test_city_layers tests.test_city_layers_sources   # offline tests
```

Optional: set `SODA_APP_TOKEN` to a free NYC Open Data app token for higher rate limits.

## What it writes

- `data/layers/<layer_id>.geojson`: a GeoJSON FeatureCollection with its catalog entry under
  `layer` (`LayerFeatureCollection` in `api/contracts.py`).
- `data/layers/catalog.json`: every file's `layer` entry in one list (`LayerCatalogEntry`), in the
  order the layer panel shows them.

[data/layers/README.md](../data/layers/README.md) describes the files for the people who read them.

## The layers

| layer_id | Source | Placed by | Hazard | Severity | Date |
|---|---|---|---|---|---|
| `construction_incidents` | DOB Construction-Related Incidents `bf97-mjsy` | the record's coordinates | `geotech` for "Excavation/Soil Work", else `construction_safety` | 3 with a fatality, 2 with an injury, else 1 | incident date |
| `structural_complaints` | DOB Complaints Received `eabe-havv`, categories 03, 14, 16, 30, 54, 2K, 5C, from January 1 two years back | BIN to footprint lot to lot point | `geotech` for 14, else `structural` | 0 | date entered |
| `vacate_orders` | HPD Order to Repair/Vacate `tb8q-a3ar`, reason "Fire Damage" only | the record's coordinates | `fire` | 1 | effective date |
| `fdny_vacates` | FDNY Building Vacate List `n5xc-7jfa` | BBL to lot point | `fire` | 1 | vacate date |
| `unsafe_facades` | DOB NOW: Safety facade filings `xubg-57si`, one per building | BBL to lot point, else BIN to footprint lot | `facade` | 1 for UNSAFE, 0 for SWARMP | the newest filing's date |
| `fema_flood_zones` | FEMA National Flood Hazard Layer, the city's special flood hazard areas | polygons, simplified to about 10 m | `flood` | 0 | none |
| `sandy_inundation` | Sandy Inundation Zone `5xsi-dfpx` | polygons, simplified to about 10 m | `flood` | 0 | 2012-10-29, the storm |
| `flooding_complaints` | 311 requests routed to DEP `erm2-nwe9`: street and highway flooding, sewer backups, water in basements, last twelve months | the record's coordinates | `flood` | 0 | date created |
| `e_designations` | E-Designations `hxm3-23vy`, hazardous materials only | BBL to lot point | `contamination` | 0 | effective date |
| `remediation_sites` | NYS DEC Environmental Remediation Sites `c6ci-rzpg` (data.ny.gov), one per site | the record's coordinates | `contamination` | 0 | none |

A lot point is PLUTO's point for the lot. When PLUTO lacks the lot (it lists a condo under its
billing lot, not the base lot a record names), it is the middle of the lot's polygon on the tax map
(`i38t-6if2`). A record whose lot or building is in neither is left off the map and counted.

Severity follows the team's scale (0 signal, 1 enforcement, 2 incident, 3 catastrophic). These
choices are for the domain lead to confirm:

- A complaint is always 0, whatever its disposition. The disposition is in the summary with its own date.
- A vacate order is 1. A facade filed UNSAFE is 1 (it requires public protection and repair); SWARMP is 0.
- An incident with nobody reported hurt is 1, as in the shared fixture.
- An E-designation, a flood zone and the Sandy zone are 0: context about a lot, not an event on it.
- A 311 flooding report is 0, like a complaint. A state remediation site is 0 whatever its class;
  class 02 ("significant threat") might deserve more.

## Rules the layers keep

- **A failed pull is never zero.** Each layer is written whole or not at all. A layer whose pull
  fails keeps its last good file, with a sentence in its description saying the refresh failed.
  With no earlier file it gets `status: "error"`, `feature_count: null` and no features. The run exits 1.
- **A capped pull is a floor.** A pull that stops at the row cap (200,000) writes `status: "capped"`.
- **Nothing is dropped silently.** Records that cannot be placed, and records left out on purpose,
  are counted in the layer's `description`.
- **No names.** The owner, inspector and registration columns in these sources are never
  requested (a test checks every query's column list).
- **Nothing is guessed.** No join on a placeholder BIN such as `3000000`, or on a BIN whose
  footprints sit on more than one lot. A complaint or disposition code that its key lacks is shown as the code.
- **Housing matters get no hazard.** HPD vacate orders for habitability and illegal occupancy are
  counted and left off the map; they are never filed under fire or structural.
- **`updated_at` is the source's date**, the day Open Data says its rows last changed. The pull date
  is the last sentence of the description.
- **Later facts carry their own date.** A feature's `date` is when the record began. A summary may
  add something recorded later (a rescind date, a disposition), always with its date, so an as-of
  view can tell. Two fields are the status at the pull and have no date: a facade's status, and
  "no rescind date" or "no disposition", which are worded "at the pull".
- **Complaints are never added to 311 requests.** The same complaint can be in both, with no shared key.

## One site, asked of the sources

[site_context.py](site_context.py) asks each source about one point or lot at full detail, for the
site profile. The map layers are simplified, so do not read a lot's answer off them.

```python
from city_layers import site_context
site_context.site_context(lon, lat, bbl)        # flood, soil, e_designation fields plus one sample per source
site_context.fema_zone(lon, lat)                # zone, subtype, special flood hazard area, base flood elevation
site_context.sandy_flooded(lon, lat)            # True or False, from the full-detail polygons
site_context.e_designation(bbl)                 # every designation on the lot: hazardous materials, air, noise
site_context.soil_unit(lon, lat)                # the USDA soil survey map unit
site_context.weather(lon, lat, start, end)      # daily rain and temperatures, heavy-rain and freeze-thaw days
```

Every answer has a `status`: `ok` (a `value` of None means the source has nothing there), `error`
(the query failed, so nothing is known) or `skipped` with a `reason`. Two are skipped for now:

- **Depth to bedrock.** USGS serves it as map tiles only (`DTB_NewYorkCity`, depth in feet, about
  30 m cells). A point lookup needs the raster download and a raster library.
- **Stormwater flood maps.** The city publishes a 34 MB zip of GIS files and map tiles, with no point lookup.

Weather comes from a model grid cell a few km across, not a gauge at the site, and Open-Meteo's
free service is for non-commercial use. A heavy-rain day has more than 25 mm (the PR 7 rule); a
freeze-thaw day went below 0 °C and back above it.

## Scheduled refresh

`python3 -m city_layers.refresh_layers` pulls every layer and logs the run in
`data/layers/refresh_log.json` (the last 20 runs, with each layer's outcome). `--every HOURS` keeps
going; or run it from cron. A layer whose source fails keeps its last good file. The refresh only
rewrites files: committing or deploying them is a separate step.

## Job type to work types

[work_types.py](work_types.py) holds the table the site profile uses before a project has filings.

```python
from city_layers import work_types
work_types.assumed_work_types("new_building")   # what to switch on; mark it inferred
work_types.stated_work_types(filings)           # what a site's DOB NOW filings say YES to
work_types.job_type("Alteration CO")            # DOB NOW's job type -> the contract's
```

- `ASSUMED` lists the work types per job type. `PERCENT_OF_FILINGS` is why each is there: the share
  of DOB NOW filings under that job type that say YES, counted over all 983,784 filings on 2026-11-14.
- The alteration list includes excavation, foundation and support of excavation, as in the team's
  session 3 walkthrough, though only 1.5% of plain "Alteration" filings carry earth work. The user unticks.
- Underpinning is never assumed. It has no filing column, and it depends on the adjoining foundations.
- Five contract work types have no column in the filings dataset, so a filing can never state them:
  excavation, underpinning, facade, standpipe, construction fence.

## Data gate, 2026-11-14

One live query per source in the plan. "Rows" is the whole source that day.

| Source | ID | Rows and dates | Traps |
|---|---|---|---|
| DOB construction incidents | `bf97-mjsy` | 1,511, 2024-01-03 to 2026-11-11 | 16 rows have no coordinates and 84 no BBL. No cause or description column. The Nov 11 collapse is typed "Other Construction Related", with 2 fatalities and 17 injuries as entered |
| HPD vacate orders | `tb8q-a3ar` | 9,002, 2012 on | Reasons: Fire Damage 4,865, Illegal Occupancy 3,495, Habitability 642. 15 orders are dated after the pull: 14 on 2026-11-16 (11 of them fire damage) and one on 2040-08-20 (illegal occupancy). Dates are kept as recorded and flagged |
| FDNY vacate list | `n5xc-7jfa` | 357, 1989-04-05 to 2025-09-17, rows last changed 2026-01-05 | No coordinates, no record number, no reason. Status is "Dismissal", "Rescinded" or blank, and the dataset does not define them. Two buildings repeat on one date |
| Facade filings | `xubg-57si` | 87,702 filings for 16,914 buildings | One row per filing, so the plan's 5,627 UNSAFE and 32,504 SWARMP count rows. By building, 7,153 are UNSAFE or SWARMP on their newest filing (1,530 and 5,607 of the 7,137 placed). No coordinates. Holds owner and inspector names |
| DOB complaints | `eabe-havv` | 3,154,322; the seven codes hold 154,066, of which 18,051 since 2024-01-01 | BIN only, no coordinates. `date_entered` is text (MM/DD/YYYY), so a date range cannot be asked for; years are matched by their ending |
| Sandy Inundation Zone | `5xsi-dfpx` | 492 polygons, last changed 2015-11-09 | **The plan's ID `uyj8-7rv5` is the map view; the API answers it with 492 empty rows.** The data is 91 MB at full detail |
| E-Designations | `hxm3-23vy` | 14,019, 1983 to 2026-10-13 | 10,753 are for hazardous materials; 3,266 are air or noise alone. No coordinates. 1,882 of the 10,753 lots are not in PLUTO: 518 are on the tax map (the ones sampled were condo base lots) and 1,364 are on neither, probably lot numbers retired since |
| DOB NOW job filings | `w9ak-ipjd` | 983,784, to 2026-11-13 | **`support_of_excavation_work_type_` reads "No" on every filing in the city.** A "No" there says nothing about a site. Standpipe, fence and supported scaffold have no column |

Sources for PR 16, each checked with one query:

| Source | ID or endpoint | Result |
|---|---|---|
| NYS DEC remediation sites | `c6ci-rzpg` on data.ny.gov (`jvqh-m7fz` is its map view) | **ID confirmed.** Has coordinates. 49,503 rows for the five counties, many per site. Holds owner and operator names, which we will not request |
| FEMA flood zones | `hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28` | Answers a point query |
| DEP Stormwater Flood Maps | `9i7c-xyvv` | **A 34 MB zip of GIS files, not a queryable dataset.** Needs another route |
| USDA soil (Soil Data Access) | `sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest` | Answers a point query: "Urban land-Flatbush complex, 0 to 3 percent slopes" at 2625 Bedford |
| Open-Meteo archive | `archive-api.open-meteo.com/v1/archive` | Daily rain and temperatures. The answer is for a grid cell about 3 km from the point asked |
| USGS depth to bedrock | `tiledimageservices.arcgis.com/.../DTB_NewYorkCity/ImageServer` | **Tiles only.** `identify` answers "Invalid URL", so there is no point lookup |
| 311 flooding | `erm2-nwe9`, `agency='DEP'` | 15,862 requests in the last twelve months. DEP renamed its types in 2026 ("Street Flooding (SJ)" became "Flooding on Street"), so both names are matched. Highway requests rarely have coordinates |

## Not done

- The DEP stormwater flood maps, as a layer or a lookup, and the depth to bedrock lookup (see above).
- Parquet copies. The plan mentions them; nothing reads them yet, and GeoJSON keeps the pull free of packages.
- Complaints before 2024 and 311 flooding reports older than twelve months. The windows are
  `YEARS_BACK` in `structural_complaints.py` and `DAYS_BACK` in `flooding_complaints.py`.
- FEMA's preliminary flood maps. The layer and the lookup read the effective map only.
