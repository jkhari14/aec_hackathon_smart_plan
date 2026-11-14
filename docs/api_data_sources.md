# PreFlight: data sources, APIs and the Revit/Rhino/Grasshopper path

Extends [data_and_code_notes.md](data_and_code_notes.md) (the datasets it lists) and the
[data_pull](../data_pull/README.md) pipeline. It does not repeat them. Every live check was run on
**2026-11-14** against the sources linked in each row; "unchecked" means we did not verify it today.
Hero site: 2625 Bedford Ave (BBL 3052110074) and 1321 Flatbush Ave (BBL 3052110073).
Updated the same day to follow the team meetings' decisions (see "Decisions applied" in section 5).

## Top findings

1. **A DOB dataset of construction incidents exists, but it is a thin base for the precedent map.**
   [`bf97-mjsy`](https://data.cityofnewyork.us/d/bf97-mjsy) has 1,511 rows from 2024-01-03 to
   2026-11-11, each with a BBL, coordinates, a type, and fatality and injury counts, and it holds the
   collapse (2 fatalities and 17 injuries on the entry, a figure at the time of entry, not the final
   toll). The team called it "very vague" and recent-only in its second meeting, and the data bears
   that out: a handful of categories, no cause or description column, and nothing before 2024. The
   precedent map should rest on the curated precedent library, with causes "as publicly reported";
   this dataset is at most a dated cross-check.
2. **The pipeline now holds the newer violations set and 311.** `855j-jady` (DOB Safety Violations,
   joined on `bbl` or `bin`) holds 1321 Flatbush's open gas-piping violation, which the older
   `3h2n-5cm9` and ECB `6bgk-3dad` do not. 311 requests routed to DOB (`erm2-nwe9`, 2020 on) add the
   complaint in words: two rows on 2625 Bedford (2026-03-18 and 2026-11-11), none on 1321 Flatbush.
   Both are in `data_pull` (checked against its `DATASETS`).
3. **No building outline exists today for the dig site.** Building Footprints (`5zhs-2jue`) holds
   no row for either BIN at 2625 Bedford (the old building `3328271`, the new one `3430674`), and the
   address search returns the dummy BIN `3000000`. The brief must carry "no footprint" as a state.
4. **Of the three sites named, only one rests on an API we may use.** Who Owns What and BuildNYC
   forbid bots and scraping in their terms; ZRD1.com is a blog with no data. The open data under
   Who Owns What (HPD registrations, ACRIS) is keyless. The team ruled out showing owner, applicant
   and contractor names, so we use it only for dated facts, such as a registration that had lapsed.
5. **For Rhino, one JSON file in local feet is enough.** NYC geometry ships in EPSG:2263
   (feet), and Grasshopper in Rhino 8 runs Python 3 scripts, which should be able to read a URL (not tested). The DCP's own NYC 3D model
   is also published as `.3dm` (a 2014 survey, so it lacks new buildings).

## 1. Sources we already use, extended

Base URL for all SODA rows: `https://data.cityofnewyork.us/resource/<ID>.json` (`.geojson` also works
on datasets with geometry). **Key:** none. **Rate limits:** without an app token, requests share a
per-IP pool and a 429 means you were throttled; with a free
[app token](https://dev.socrata.com/docs/app-tokens.html) (header `X-App-Token`) the docs say there is
no throttling unless abusive. Checked 2026-11-14. Responses omit null fields per row, and numbers
arrive as strings (`"yearbuilt":"1930"`).

| Source | ID or endpoint | Join key | Fields the brief takes | Traps (verified 2026-11-14 unless marked) |
|---|---|---|---|---|
| Address search (**use this, keyless**) | [`geosearch.planninglabs.nyc/v2/search?text=`](https://geosearch.planninglabs.nyc/v2/search?text=2625%20Bedford%20Ave%2C%20Brooklyn&size=1) | text to BBL, BIN | `label`, `geometry` (lon, lat), `addendum.pad.bbl`, `addendum.pad.bin`, `addendum.pad.version` | Returned BIN `3000000` for 2625 Bedford: a dummy, never join on it. Matches loosely, so show `label`. CORS is open (`*`). No rate limit stated; unchecked |
| Address search (needs a key) | Geoclient ([portal](https://api-portal.nyc.gov/), [docs](https://mlipper.github.io/geoclient/docs/current/user-guide/)) | house number, street, borough | `bbl`, `buildingIdentificationNumber`, `latitude`, `longitude` | Not run today (needs a subscription key from the portal). Skip: GeoSearch covers it without a key |
| PLUTO | [`64uk-42ks`](https://data.cityofnewyork.us/d/64uk-42ks) (updated 2026-08-24, version `26v2`) | `bbl` (comes as `"3052110074.00000000"`) | `address`, `yearbuilt`, `numfloors`, `bldgclass`, `landuse`, `lotarea`, `lotfront`, `lotdepth`, `bldgfront`, `bldgdepth`, `zonedist1`, `histdist`, `landmark`, `xcoord`, `ycoord` (EPSG:2263), `latitude`, `longitude`, `cd` | Stale on purpose: still `K1`, 1 floor, built 1933 for 2625 Bedford. `landmark` is only present on landmarked lots. `ownername` exists in the dataset but is left out, per the names decision |
| MapPLUTO lot polygons | [ArcGIS `MAPPLUTO/FeatureServer/0`](https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0) (DCP). Query: `where=BBL=3052110074&outSR=2263&f=geojson` | `BBL` (a number here) | lot polygon in **EPSG:2263 feet** when you ask for `outSR=2263`; `YearBuilt`, `NumFloors`, `BldgClass`, `ZoneDist1`, `LotArea` | Max 2,000 records per call. Data last edited 2026-09-09. `outSR=4326` also works. The ring for 2625 Bedford matches the tax-lot polygon below (checked) |
| Tax-lot polygons | [`i38t-6if2`](https://data.cityofnewyork.us/d/i38t-6if2) (used by `data_pull`) | `bbl` text | `the_geom` (**EPSG:4326 only**), `condo_flag`, `air_lot_flag`, `easement_flag` | Has `air_lot_flag` and `condo_flag` columns; check them before treating a polygon as a ground parcel. Use MapPLUTO when you need feet |
| Building Footprints | [`5zhs-2jue`](https://data.cityofnewyork.us/d/5zhs-2jue) (updated 2026-11-08) | `base_bbl`, `mappluto_bbl` (text), `bin` (a **number**) | `the_geom` (4326), `height_roof` (ft above ground), `ground_elevation` (ft, NAVD88 when modern), `construction_year`, `last_status_type`, `feature_code` | 1321 Flatbush: height 32.15 ft, built 1930, still "Constructed". **No row for 2625 Bedford.** Height `0` or null means unknown. Dummy BINs `1000000`, `2000000`... exist, and `3000000` is on two other lots. Photogrammetric accuracy about +/-2 ft ([metadata](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md)) |
| DOB NOW job filings | [`w9ak-ipjd`](https://data.cityofnewyork.us/d/w9ak-ipjd) (updated 2026-11-13) | `bbl`, `bin`, `job_filing_number` | `job_type`, `filing_status`, `earth_work_work_type_`, `foundation_work_type_`, `support_of_excavation_work_type_`, `sidewalk_shed_work_type_`, `full_demolition_work_type_`, `proposed_height`, `proposed_no_of_stories`, `existing_height`, `specialinspectionrequirement`, `progressinspectionrequirement`, `filing_date`, `approved_date`, `first_permit_date`, `job_description` | The columns the checklist needs are here: for 2625 Bedford, `-S3` has earth work and foundation = `YES`, special inspection "Excavations - Sheeting, Shoring, and Bracing". **`support_of_excavation_work_type_` is "No" on every one of its filings.** Quote it as recorded, draw no conclusion. The BIN changed from `3328271` (demolished) to `3430674` (new). The same row also carries applicant, owner and filing-representative names, which we do not take |
| DOB Violations (older) | [`3h2n-5cm9`](https://data.cityofnewyork.us/d/3h2n-5cm9) | `boro`+`block`+`lot`, or `bin`. No `bbl` | `violation_category` (free text), `violation_type`, dates as `YYYYMMDD` | Hero lots: 4 rows (3 on lot 74, 1 on lot 73), all `V-DOB VIOLATION - ACTIVE`. Our query matched only 5-digit lots (`00073`, `00074`); other widths were not tested, so `data_pull`'s lot variants are right to try several |
| **DOB Safety Violations (newer)** | [`855j-jady`](https://data.cityofnewyork.us/d/855j-jady) (updated 2026-11-13) | `bbl` or `bin` | `violation_number`, `violation_type`, `violation_status` (Active, Dismissed), `violation_issue_date`, `violation_remarks`, `device_type` | In `data_pull` as `dob_safety_violations`. 1321 Flatbush: one Active gas-piping (LL152) violation, issued 2025-01-31. Some violations also appear in `3h2n-5cm9`, so dedupe on the number |
| DOB ECB Violations | [`6bgk-3dad`](https://data.cityofnewyork.us/d/6bgk-3dad) (updated 2026-11-14) | `boro`+`block`+`lot` (block 5 digits, lot **4 digits**: `05211`, `0074`), or `bin` | `ecb_violation_status` (`ACTIVE`, `RESOLVE`), `issue_date` (`YYYYMMDD`), `severity`, `section_law_description1..10`, `violation_description`, `hearing_status` | Confirms the three 2625 Bedford rows in the notes. A query on `bin = '3000000'` returns other lots' rows, because the dummy BIN is shared |
| DOB complaints | [`eabe-havv`](https://data.cityofnewyork.us/d/eabe-havv) | `bin` only | `status`, `date_entered` (`MM/DD/YYYY`), `complaint_category` (code), `disposition_code` | Two complaints were entered on 2026-11-13, after the collapse, on `3120364` and `3430674`. Do not count them as "before" |
| 311 requests routed to DOB | [`erm2-nwe9`](https://data.cityofnewyork.us/d/erm2-nwe9) ("311 Service Requests from 2020 to Present", 679,002 DOB rows, 2020-01-01 to 2026-11-12) | `bbl`, filter `agency='DOB'`. Rows filed by street or intersection may have no `bbl` (not counted) | `unique_key`, `created_date`, `closed_date`, `complaint_type`, `descriptor`, `status`, `resolution_description`, `incident_address` | In `data_pull` as `dob_311_requests`. 2625 Bedford: two rows, 2026-03-18 (closed) and 2026-11-11 (assigned), both "General Construction/Plumbing / Cons - Contrary/Beyond Approved Plans/Permits". 1321 Flatbush: none. The row has a `unique_key` and no DOB complaint number, so it cannot be matched to `eabe-havv`: never add the two counts. The dataset page links a note on recent changes to the dataset, which we did not read |
| DOB construction incidents | [`bf97-mjsy`](https://data.cityofnewyork.us/d/bf97-mjsy) (updated 2026-11-13) | `address_bbl`, `bin`, `address_latitude`, `address_longitude` | `incident_date_mm_dd_yyyy`, `record_type_description` (Accident 1,095, Incident 360, Notification 49, Not DOB Jurisdiction 7), `check2_description` (type), `fatality`, `injury`, `addressnumber`, `street`, `boro` | **Not used for precedents** (the team called it "very vague"). 2024 onward only. The hero event is filed as "Other Construction Related", so **a filter by type will miss it**, and its lot is `address_bbl`, not `bbl`. Excavation/Soil Work: 49 rows citywide (23 Brooklyn), 2 fatalities. Some rows lack a BBL. No cause or description column. The dataset description only says it records incidents in DOB's Incident Database; we found no statement that it is limited to worker safety (a teammate's claim, unconfirmed) |
| DOB NOW approved permits | [`rbx6-tga4`](https://data.cityofnewyork.us/d/rbx6-tga4) (updated 2026-11-13) | `bbl`, `bin`, job number (columns unchecked) | permit dates and status per job | Only the name and freshness were checked |
| DOB permits (older BIS) | [`ipu4-2q9a`](https://data.cityofnewyork.us/d/ipu4-2q9a), jobs [`ic3t-wcy2`](https://data.cityofnewyork.us/d/ic3t-wcy2) | `bin`, borough+block+lot | pre-2018 jobs for neighbors built before DOB NOW | Name and freshness only. Useful for old neighbors' alteration history |
| HPD violations | all [`wvxf-dwi5`](https://data.cityofnewyork.us/d/wvxf-dwi5) (has `bbl`, `bin`), open-only view [`csn4-vhvf`](https://data.cityofnewyork.us/d/csn4-vhvf) (**no `bbl`**: use `boroid`+`block`+`lot`) | as noted | `class` (A, B, C), `novdescription`, `currentstatus`, `novissueddate` | 1321 Flatbush: 129 rows in the all-view, 98 in the open view. Matches the notes. Housing, not construction |

**Drop-in query for a neighbor's age and height:**
`5zhs-2jue.json?$where=mappluto_bbl in ('...') OR base_bbl in ('...')&$select=bin,height_roof,construction_year,the_geom`

## 2. Public data we might be missing

### The three named

| Source | What it offers | API or open data underneath | Terms (read 2026-11-14) | Helps PreFlight? |
|---|---|---|---|---|
| [Who Owns What](https://whoownswhat.justfix.org/) (JustFix) | Landlord portfolios by building: other buildings of the same owner, evictions, rent-stabilised unit estimates | Rests on HPD registration data plus ACRIS, PLUTO, DOB filings ([methodology](https://whoownswhat.justfix.org/en/how-it-works)). The code is public, GPL-3.0 ([repo](https://github.com/JustFixNYC/who-owns-what)). Its API routes (`/address`, `/address/buildinginfo`...) are in the repo, but a request to `whoownswhat.justfix.org/api/address` returned the web page, not JSON, so we found no documented public endpoint | [Terms](https://whoownswhat.justfix.org/en/terms-of-use) section 7.7 and 7.8 forbid scraping and bots, and 7.2 limits use to personal, non-commercial. **Do not call it.** The tool's robots.txt carries `ai-train=no` | Low. It profiles residential landlords; an excavation neighbor's owner is better read from the open data below. A link out ("check this owner on Who Owns What") is fine |
| [BuildNYC](https://buildnyc.ai/) | Search over DOB filings, plans, owners, architects, contractors, violations, with paid plan viewing | A paid, closed index of DOB records and plans. No public API; "ask us for a data license" | [Terms](https://buildnyc.ai/terms) 1.23: no robots, scripts, browser automation or AI agents; no bulk extraction; 1.6: no AI training. **Do not touch.** We read only its home page and terms page, once each | None for the build. Its owner/geotech-engineer directory shows the market has the data, which the open data below partly covers |
| [ZRD1.com](https://www.zrd1.com/) | A blog analysing past Zoning Resolution Determination (ZRD1) requests, mostly zoning-text topics, marked pre-"City of Yes" | No data, no API, a Wix site; states it is not affiliated with the City. The real ZRD1 is a [DOB form](https://www.nyc.gov/assets/buildings/pdf/zrd1.pdf) ($1,000 request) | Not read in full; no scraping needed | None. Zoning determinations are not an excavation topic. Skip |

### Other public sources that serve the question

| Source | ID or URL | Join | What it gives | Checked 2026-11-14 | Use |
|---|---|---|---|---|---|
| HPD registrations | [`tesw-yqqr`](https://data.cityofnewyork.us/d/tesw-yqqr) | `boroid`+`block`+`lot` (bare numbers), `bin` | `registrationid`, `lastregistrationdate`, `registrationenddate` | 1321 Flatbush: a registration ending 2024-09-30, so it had lapsed by the collapse. Residential multiple dwellings and non-owner-occupied small ones only ([methodology](https://whoownswhat.justfix.org/en/how-it-works)) | Demo |
| HPD registration contacts | [`feu5-w2e2`](https://data.cityofnewyork.us/d/feu5-w2e2) | `registrationid` | `type` (owner, agent, head officer), `corporationname`, name, business address | Columns verified; no person looked up. Public record, but the team decided on 2026-11-14 to show no owner, applicant or contractor names, and `data_pull` leaves them out | **Skip.** The adjoining-owner row says what the Building Code requires and what proof is missing, with no named party |
| ACRIS (deeds) | legals [`8h5j-fqxa`](https://data.cityofnewyork.us/d/8h5j-fqxa), master [`bnx9-e6tj`](https://data.cityofnewyork.us/d/bnx9-e6tj), parties [`636b-3b5g`](https://data.cityofnewyork.us/d/636b-3b5g) | legals by `borough`, `block`, `lot` (**plain numbers**), then `document_id` | `doc_type`, `document_date`, `document_amt`, `air_rights`, `subterranean_rights` (party `name` is in the parties table; leave it out, per the names decision) | 2625 Bedford has recent documents (2024-06, 2026-02). Three-table join | Nice to have: dated transfers and rights, with no party names |
| Facade inspections (FISP) | [`xubg-57si`](https://data.cityofnewyork.us/d/xubg-57si) (87,702 rows) | `bin`, `block`, `lot` | `filing_status`, `cycle`, `exterior_wall_type_s_`, `exterior_wall_material_s_` | No row for the three hero BINs. The program covers taller buildings only (the rule is from DOB's program, unchecked today) | Nice to have: neighbor construction type for tall neighbors |
| Landmarks | PLUTO `landmark`, `histdist`; LPC permits [`dpm2-m9mq`](https://data.cityofnewyork.us/d/dpm2-m9mq); LPC violations [`wycc-5aqt`](https://data.cityofnewyork.us/d/wycc-5aqt) | `bbl`, block+lot | landmark status flag | The PLUTO column is present on landmarked lots only | Demo: one flag in the brief, and a row "needs LPC review" |
| DOB NOW public portal | [portal](https://a810-dobnow.nyc.gov/publish/#/), [manual](https://www.nyc.gov/assets/buildings/pdf/DOB_NOW_public_portal_manual.pdf) | job number | The Documents tab lists name, status and created date per job (the manual's example shows "Site Survey: Initial", "Plot Diagram", "Landmark Approval") | Manual read; **no API found**, no bulk download. Whether each file opens for the public is not confirmed by the manual. Note: the notice dated June 10 is reported by Northeastern, not verified by us | Do not scrape the portal. Show a link to the job and say "document list is on the DOB portal" |
| Registered demolition and construction firms | [`cspg-yi7g`](https://data.cityofnewyork.us/d/cspg-yi7g) | `account_name`, `bic_number` | company, license dates | Columns only | Skip |
| Soil and bedrock | USGS [bedrock elevation and overburden maps, five boroughs](https://www.usgs.gov/data/geospatial-data-bedrock-elevation-and-overburden-thickness-maps-five-boroughs-new-york-city) (2023, CC0) and [mapper](https://ny.water.usgs.gov/maps/nycbedrock/) | spatial | shapefiles and rasters of bedrock elevation and depth to bedrock | Page read; **raster not downloaded or sampled**. Not a boring log for a given lot; site borings are in the geotechnical report, which is not public | Roadmap: one "depth to bedrock" figure |
| NYC 3D model | [DCP page](https://www.nyc.gov/content/planning/pages/resources/datasets/nyc-3d-model) | by community district, `.3dm` (Rhino) | massing of every building present in 2014. The hero lots are in Brooklyn Community District 17 (PLUTO `cd` = 317 for both), so the file is `nyc_3dmodel_bk17.zip`, which the page links | Page links re-read 2026-11-14; file not downloaded (a script request to nyc.gov returned 403 today). Model date is 2014 (released 2018). An earlier version of this row named `bk14`, which was wrong | Roadmap: context mesh for Rhino |
| Stop-work orders | none found | n/a | The catalog search for "stop work order" returns only the complaints dataset | Re-checked: no standalone dataset. They appear in ECB `section_law_description` ("28-207.2.2 ... NOTICE OF A STOP WORK ORDER") | Keep the `stop_work_mentions` approach |

## 3. Revit, Rhino and Grasshopper

**Coordinates.** DCP publishes footprints and lots in New York State Plane, Long Island East Zone,
NAD83, US foot (EPSG:2263), and republishes GeoJSON in EPSG:4326 and shapefiles in 3857
([metadata](https://github.com/CityOfNewYork/nyc-geo-metadata/blob/main/Metadata/Metadata_BuildingFootprints.md)).
PLUTO's `xcoord`/`ycoord` are 2263 too (997076, 172079 for 1321 Flatbush). So: SODA GeoJSON gives
degrees, and MapPLUTO's ArcGIS service gives feet if you ask.

**The trap that moves a site by 2 ft.** A US survey foot is 0.3048006096 m and an international foot
0.3048 m. At x = 997,076 the difference is **1.99 ft** (our calculation). Revit works in feet internally and Rhino in whatever
units the file sets, so absolute state-plane coordinates look fine and land about 2 ft off if one
tool reads them as the other kind of foot. So the brief must not ship absolute coordinates for modelling.

**What the JSON must carry** (a sketch, not a spec):

```json
{
  "crs": {"epsg": 2263, "unit": "US survey foot", "geometry_unit": "foot",
          "origin_epsg2263": [997076.0, 172079.0], "origin_wgs84": [-73.95379, 40.63898]},
  "site":      {"bbl": "3052110074", "lot_ring_local": [[x, y], "..."], "footprint": null,
                "footprint_status": "none_in_dataset"},
  "neighbors": [{"bbl": "3052110073", "bins": ["3120364"], "ring_local": [], "z_base_ft": 29.0,
                 "height_ft": 32.15, "year_built": 1930, "height_source": "5zhs-2jue"}],
  "rows":      [{"section": "3309.1.1", "party": "owner", "status": "not_found",
                 "source_url": null}],
  "precedents":[{"lon": 0, "lat": 0, "label": "...", "date": "2026-02-26",
                 "cause_as_reported": null, "source_url": null}]
}
```

- **Local coordinates in feet, relative to `origin_epsg2263`**, plus the origin. A Grasshopper or
  Revit user moves the origin to the project base point; nothing is lost and no absolute number is
  trusted.
- **`z_base_ft` and `height_ft` kept apart.** `ground_elevation` is feet above sea level (NAVD88 when
  modern); `height_roof` is feet above that ground, not above sea level. Never add them silently.
- **Unknowns stay `null` with a status**, never `0` (the footprints use `0` or null for "unknown").
- **Every lot carries both BBL and BIN lists** and says which footprint is for which BIN.
- Keep the original WGS84 ring too, for the map.

| Option | Work in under 24 h | Status |
|---|---|---|
| Plain JSON or GeoJSON endpoint read by a Grasshopper script component | Low. [Rhino 8 offers Python 3 in Grasshopper](https://developer.rhino3d.com/guides/scripting/scripting-gh-python/), so `urllib.request` and `json` should suffice (we did not run it; this needs Rhino 8, and a Rhino 7 setup is unchecked). The script extrudes `ring_local` by `height_ft` and draws the lots | **Hackathon pick** |
| Rhino.Inside.Revit | Medium. It runs Grasshopper inside Revit, so the same definition can create Revit elements; install and Revit version match are the risk. [Forum comparison with Speckle](https://discourse.mcneel.com/t/speckle-vs-rhino-inside/166895) | Stretch for the demo |
| Speckle | Medium to high. Connectors for Rhino, Grasshopper and Revit; the Rhino and Grasshopper connectors install together ([Speckle](https://speckle.systems/tutorials/convert-rhino-blocks-to-revit-families-with-speckle/)). Free plan: 1 project, 3 users, 30-day history ([pricing](https://speckle.systems/pricing)). A forum post notes V2 to V3 [lost simple send/receive flows](https://speckle.community/tag/grasshopper?match_all_tags=true&page=1&tags%5B%5D=grasshopper) | **Roadmap pick**: model the brief as Speckle objects with the checklist as properties |
| Heron (GIS into Grasshopper) | [Food4Rhino](https://www.food4rhino.com/en/app/heron): imports GIS data placed around an Earth Anchor Point; about 50 MB of libraries | Skip for 24 h; alternative later |
| IFC export | Not checked; more work than the JSON | Roadmap |
| Revit only, no Rhino | Needs a custom add-in or Dynamo; unchecked | Skip |

## 4. Recommendation

### Use in the demo

| Item | Why |
|---|---|
| GeoSearch for the address | Keyless; gives BBL and BIN; fails to a dummy BIN, so check `3000000` |
| Footprints, PLUTO, MapPLUTO polygons (2263) | Neighbor age, height, lot shape. State "no footprint" for 2625 Bedford |
| DOB NOW job filings | The excavation flags, special-inspection lists and job status that fill the checklist rows |
| DOB Safety Violations `855j-jady`, ECB, and 311 requests routed to DOB `erm2-nwe9` (all in `data_pull`) | The record of unresolved safety and stop-work text, and the complaint in words |
| HPD registration (dates only) | The lapsed 1321 registration is a dated fact on screen; no contact names |
| One JSON brief in local feet plus a Grasshopper script | The one tool-side path we can finish |

### Nice to have

ACRIS deeds (dated transfers, no party names), FISP (neighbor facade type), PLUTO `landmark` flag
with LPC permits, construction incidents `bf97-mjsy` as a dated cross-check on the curated
precedents, Rhino.Inside.Revit running the same definition, the DCP `.3dm` model of the community
district as context (2014).

### Skip

Who Owns What and BuildNYC (terms forbid it, and the open data covers the need), ZRD1.com (no
data), Geoclient (a key, no gain over GeoSearch), the DOB NOW portal scrape, registered-firm lists,
Speckle for the 24-hour build.

## 5. Corrections and open items

- **For the notes:** the open HPD view `csn4-vhvf` has no `bbl` column; the all-violations set
  `wvxf-dwi5` does. The notes' 98 open count matches the open view.
- **For `data_pull`:** build on it, no second client. `855j-jady` and `erm2-nwe9` are already in
  `DATASETS` in `data_pull/lot_records.py`. Nothing is needed for the precedent map from
  `bf97-mjsy`; if it is ever used as a cross-check, its lot column is `address_bbl`, not `bbl`, so
  `record_lot` would return None and the row would stay unplaced until it is mapped.
- **The 2625 Bedford filings** show `support_of_excavation_work_type_` = "No" next to a special
  inspection for "Excavations - Sheeting, Shoring, and Bracing". Report both as recorded; whether
  they conflict is for a licensed professional.
- **Unchecked today:** rate limits of GeoSearch, NYC Open Data terms of use, `rbx6-tga4` columns,
  the DOB portal's file access, USGS raster contents, Rhino 7 behaviour, Revit's coordinate-system
  list, Speckle connector versions for Rhino 8 and Revit 2026.
- **Decisions applied (team meetings, 2026-11-14):**
  - Names are out: no permit-holder, contractor, owner or applicant names. This removes HPD
    registration contacts and ACRIS party names from the plan.
  - Precedents are shown with causes "as publicly reported" or "under investigation", with no blame
    and no claim that something would have been prevented. This moves the precedent map off
    `bf97-mjsy`, which the team called "very vague", onto the curated library.
  - Sources we cannot crawl (DOB NOW documents, Who Owns What, BuildNYC) are being sorted for manual
    import in a separate document, `manual_data_imports.md`, which was not on `main` when this was
    written. The terms findings above are the ones it should cite.
