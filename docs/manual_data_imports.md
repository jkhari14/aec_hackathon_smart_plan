# PreFlight: sources a crawler can't use, and how to import them by hand

Follows [api_data_sources.md](api_data_sources.md), which listed what we skipped. For each source
that a script can't or mustn't fetch, this page says whether there is another way in, then sets
out a manual-import path and what a person has to do. All checks were run on **2026-11-14**.

**Verdicts**
- **(a)** automatable after all;
- **(b)** a person downloads or reads it, and we import the file or the facts, within the source's terms;
- **(c)** usable only under a license or with permission;
- **(d)** don't use.

## Top findings

1. **Disposition codes are already open data, so nobody has to type them in.** DOB publishes them as
   [`6v9u-ndjg`](https://data.cityofnewyork.us/d/6v9u-ndjg), a keyless table of 160 codes. In it
   **L3 means "STOP WORK ORDER PARTIALLY RESCINDED"**, not "building leaning" as said in the
   meeting. Y1 is "FULL VACATE ORDER ISSUED", Y3 "PARTIAL VACATE ORDER ISSUED", and A3 "FULL STOP
   WORK ORDER SERVED". The table was last updated 2017-02-08, so two codes in our pull, AF and H8,
   are not in it.
2. **Code 30 is confirmed from DOB's own list:** "Building Shaking/Vibrating/Structural Stability
   Affected", priority A. The list is a PDF that DOB attached to the complaints dataset on Open
   Data. It is now imported as the worked example: 97 codes, footer "Rev. 12/18". In our two cached
   pulls, every code-30 complaint on the hero lots and their neighbors was entered on 2026-11-11.
   Ten codes in the pull are newer than that list (1L, 1X, 2N, 4S, 6S, 6X, 7F, 7G, 7J, 7S). They
   decode as an explicit gap until a person imports DOB's newer list from nyc.gov.
3. **Several "can't crawl" sources are plain downloads or keyless services.** These are FEMA's flood
   layer (queried today: 1321 Flatbush is in Zone X), the USGS bedrock files, the DCP 3D model, and
   the BIS pages. The hero lots are in **Brooklyn Community District 17** (PLUTO `cd` = 317), so the
   3D model file is `nyc_3dmodel_bk17.zip`.
4. **These stay with a person:**
   - the DOB NOW portal and nyc.gov PDFs, both of which answer scripts with HTTP 403;
   - amlegal, whose robots.txt disallows Anthropic's crawlers.

   We do not get around those blocks.
5. **Don't use these:**
   - Who Owns What and BuildNYC, whose terms forbid it;
   - Zillow, whose terms forbid automated access, and listings are not public record anyway;
   - "CityWatch", which we could not identify as any NYC building-data product.

## Verdicts

"Read" means we read the clause ourselves on 2026-11-14. Where
[api_data_sources.md](api_data_sources.md) already records a source's terms (checked the same
day), this table cites it rather than restating it, and we did not open that site again.

| Source | Verdict | Clause behind the verdict | What we checked |
|---|---|---|---|
| DOB complaint **disposition** codes, Open Data [`6v9u-ndjg`](https://data.cityofnewyork.us/d/6v9u-ndjg) | **(a)** | NYC Admin. Code [§ 23-502(d)](https://nycadmincode.readthedocs.io/t23/c05/#section-23-502): public data sets "shall be made available without any registration requirement, license requirement or restrictions on their use" (read, on an unofficial mirror of the Code) | Queried keyless: 160 rows. L3, Y1, Y3, A3 as above. AF and H8 are missing. Last updated 2017-02-08 |
| DOB complaint **category** list (Rev. 12/18), the PDF attached to [`eabe-havv`](https://data.cityofnewyork.us/d/eabe-havv) | **(a)** to fetch, then a one-time import | Same § 23-502(d) | Downloaded with the project lead's OK: `DOBComplaints_complaint_category_list.pdf`, 270,917 bytes. Imported: 97 codes. **Worked example below** |
| DOB's newer category list, [nyc.gov/assets/buildings/pdf/complaint_category.pdf](https://www.nyc.gov/assets/buildings/pdf/complaint_category.pdf) | **(b)** | [nyc.gov terms](https://www.nyc.gov/main/terms-of-use) IV.1: City content is City property, all rights reserved. They have no clause on automated access, but the site answers scripts with 403 (read) | Not opened. A search snippet shows it lists 1X, "Construction Enforcement Work Order (DOB)". A HEAD request got 403 |
| Complaints data dictionary, `DD_DOB_Complaints_Received_2019-08-21.xlsx` (74,051 bytes, on `eabe-havv`) | **(a)** | § 23-502(d) | Size only, not downloaded. It may describe the code columns |
| **DOB NOW public portal** documents: the "Adjoining Owners Notification" PDF on job B01330433, filing S3; support-of-excavation drawings; special and progress inspection documents | **(b)** | nyc.gov terms IV.1 (read). The portal's refusal of a script is already recorded in [api_data_sources.md § 2](api_data_sources.md#2-public-data-we-might-be-missing) and `data/leads/`; its robots.txt also got a 403 today. Note that the Open Data Law's "data" excludes "designs, drawings, maps, photos, or scanned copies of original documents" ([§ 23-501(b)](https://nycadmincode.readthedocs.io/t23/c05/)), so plan scans are not open data | 403 to a script, again today. Whether every document opens for the public is unchecked. Drawings are an architect's or engineer's work, and a letter is its sender's, so **raw files stay local and only facts are committed** |
| **DOB BIS** pages (`a810-bisweb.nyc.gov`) | **(a)** for a few lookups. Prefer Open Data | nyc.gov terms I.A.7 forbid disrupting its servers; there is no clause on scripts (read). BIS has no robots.txt (404) and showed no terms of its own (unchecked) | A property-profile page returned 200 to a script. Most of BIS (complaints, violations, older jobs) is already on Open Data, so don't build on BIS HTML |
| **JustFix**: [Who Owns What](https://whoownswhat.justfix.org/) and its building pages | **(d)** for the site. The data underneath is **(a)** | Recorded in [api_data_sources.md § 2](api_data_sources.md#2-public-data-we-might-be-missing) (its terms 7.2, 7.7 and 7.8); not restated here | Not opened. The code is GPL-3.0, [checked on GitHub](https://github.com/JustFixNYC/who-owns-what); reading it to learn their joins is fine. The same facts come keyless from HPD registrations [`tesw-yqqr`](https://data.cityofnewyork.us/d/tesw-yqqr), contacts [`feu5-w2e2`](https://data.cityofnewyork.us/d/feu5-w2e2), ACRIS, and DOB complaints with `6v9u-ndjg` for dispositions. A link out is fine |
| **BuildNYC** | **(c)**, under its paid data license. **(d)** for this hackathon | Recorded in [api_data_sources.md § 2](api_data_sources.md#2-public-data-we-might-be-missing) (its terms 1.23 and 1.6, and the offer of a data license); not restated here | Not opened. Nothing until someone signs a license |
| **Zillow** listings | **(d)** | [Terms of use](https://www.zillow.com/corporate/terms-of-use/) bar "any robot, spider, scraper or other automated means to access the Services" without written permission. **We saw this clause quoted by third parties and did not open Zillow.** A person should confirm it on the page | Listings are not public record, and their photos and text are copyrighted. The meeting's pre-purchase case needs none of it: a user types any address and PreFlight pulls the public record |
| **CityWatch** | **(d)** until identified | None found | Two searches found no NYC building or permit product by that name. Hits were OnSolve CityWatch (an emergency notification platform) and unrelated research projects. Ask whoever raised it for a URL |
| **News articles and forensic reports** for the precedent library | **(b)**: facts and links only | Copyright, plus each publisher's own terms, which the person records per import | Machine-readable precedents already exist in DOB construction incidents [`bf97-mjsy`](https://data.cityofnewyork.us/d/bf97-mjsy) **(a)**, 2024 onward. Older cases, and anything narrative, a person reads and records |
| **FEMA flood maps** (National Flood Hazard Layer) | **(a)** | A federal service; we found no clause barring scripts, but did not read FEMA's terms in full | [Point query](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28) works keyless: 1321 Flatbush is Zone X, "AREA OF MINIMAL FLOOD HAZARD", not in a special flood hazard area. Which map NYC's code uses (effective or preliminary FIRM) is unchecked |
| NYC flood layers on Open Data: Future Floodplains [`29fz-v4rp`](https://data.cityofnewyork.us/d/29fz-v4rp), Stormwater Flood Maps [`9i7c-xyvv`](https://data.cityofnewyork.us/d/9i7c-xyvv), Hurricane Evacuation Zones [`epne-qv9x`](https://data.cityofnewyork.us/d/epne-qv9x) | **(a)** | § 23-502(d) | Catalog listing only. They cover the flooding and extreme-weather hazards |
| **USGS bedrock** elevation and depth to bedrock ([ScienceBase item](https://www.sciencebase.gov/catalog/item/62154ed5d34e4465d409099f)) | **(a)**, a plain download | CC0 per the USGS page, as recorded in [api_data_sources.md](api_data_sources.md#2-public-data-we-might-be-missing) | File list read through ScienceBase's keyless API: `Depth_to_Bedrock_Raster.zip` 5,802,075 bytes, `Bedrock_Elevation_Raster.zip` 5,955,473, `bedrock_pts.csv` 3,446,740. Not downloaded |
| **DCP NYC 3D model** `.3dm` ([page](https://www.nyc.gov/content/planning/pages/resources/datasets/nyc-3d-model)) | **(a)**, a plain download | DCP's "Use limitations": for information only, no warranty; no clause against reuse (read) | `nyc_3dmodel_bk17.zip` is 138,882,645 bytes (Last-Modified 2024-05-11) on `s-media.nyc.gov`, which answered a HEAD request. Model data is from 2014, released 2018. Not downloaded; too big for the repo |
| **Administrative Code** on amlegal (`codelibrary.amlegal.com`) | **(b)**, by a person in a browser | [robots.txt](https://codelibrary.amlegal.com/robots.txt) gives all agents `search=yes, ai-train=no, use=reference` and `Disallow: /` to ClaudeBot, anthropic-ai and Claude-Web (read) | We opened no amlegal page. An unofficial mirror, `nycadmincode.readthedocs.io`, is a hint: cite amlegal's section, read by a person |
| **Building Code PDFs** on nyc.gov (2022 BC chapters 33 and 17) | **(b)** | nyc.gov terms IV.1; scripted access is blocked on and off (403 today) | DOB's 2022 code overview says the codes were brought up to date with the ICC's 2015 I-Codes. Whether the PDFs carry an ICC copyright notice is unchecked. Keep what the checklist does: section number, paraphrase and link |
| Soil contamination: DCP E-Designations [`hxm3-23vy`](https://data.cityofnewyork.us/d/hxm3-23vy), OER Cleanup Sites [`3279-pp7v`](https://data.cityofnewyork.us/d/3279-pp7v) | **(a)** | § 23-502(d) | Catalog listing only. Added because soil contamination is in scope |
| Geotechnical reports and boring logs | **(b)** where filed on DOB NOW, otherwise not public | As for DOB NOW | Catalog searches for "boring" and "borehole" found no dataset |

## The manual-import path

The code is in [`manual_imports/`](../manual_imports/README.md). It is plain Python 3.9+ with no
packages, like the rest of the repo.

### Folder layout

```
data/manual_imports/<source_key>/<YYYY-MM-DD>_<slug>/
    provenance.json   who fetched it, when, from what URL, under which terms   committed
    facts.json        the facts taken from it, each with a page or locator      committed
    raw/<file>        the downloaded file                                       gitignored, never committed
```

`.gitignore` holds `data/manual_imports/**/raw/`, and a test fails if that rule stops matching.

### Provenance sidecar

The loader refuses an import whose sidecar breaks any of these rules:

- **`fetched_by`, `extracted_by`, `approved_by` and `checked.by`** are role labels (`project-lead`,
  `structural-engineer`, `claude-agent`): lowercase, no spaces, never a person's name.
- **`fetch_method`** is `browser_by_person`, or `script_with_approval` with `approved_by`. A source
  whose site refuses scripts allows only the first.
- **`fetched_at`** is an ISO date-time with its UTC offset, and the folder name starts with its date.
- **`source_url`** must be on the publisher's host. A copy on a third-party site, such as a code
  list on a lookup site, is refused: it is a hint, not the source.
- **`terms`** holds the URL, the clause, the date it was read, and the verdict (a, b or c, never d).
  A file from nyc.gov or DOB NOW must carry verdict b, and one from Open Data verdict a. A (c)
  import must also say who granted the permission.
- **`file`** holds the name, size and sha256. When the raw file is on this machine, the loader
  re-hashes it and refuses a mismatch. When it isn't, the import says so and does not pretend.
- **`document_date`** is the date the document carries, or null with `document_date_note` giving
  the reason. The category list says only "Rev. 12/18", so its date is null.
- **`checked`** is empty until a *second* person compares every fact with the file.

### Trust tier

Every import loads as a `ManualImport` whose `tier` is `"manual_import"`, with one of two statuses:

- **`imported_unchecked`**: someone took the facts from the file, and nobody else has compared them.
- **`imported_checked`**: a second person compared every fact with the file and signed `checked`.

Neither status is `ok`, which belongs to data_pull's live queries, so an import cannot read as a
live public-record pull. A code missing from an imported key decodes to `not_in_key`, with a
reason and a null description. It is never guessed.

### Rules for the public repo

- **Facts only.** Each source's allowed fields are fixed in `manual_imports/sources.py`, and none
  of them is a person's name. A field the source doesn't list is refused.
- **Short quotes.** A `fact` or `quote` over 25 words is refused.
- **What stays local.** Drawings, letters and article text stay in `raw/`.
- **Names.** Owner, contractor and permit-holder names stay out even when a document shows them.
  No validator can catch every name, so the person who extracts the facts and the person who
  checks them both look for names.

### Worked example: DOB's complaint category key

`data/manual_imports/dob_complaint_categories/2026-11-14_category-list-rev-12-18/` holds 97
codes, each with its description, priority and page. Its status is `imported_unchecked`, because
the agent that extracted the codes also looked them over. A teammate's check would make it
`imported_checked`.

```bash
python3 -m manual_imports.load_imports        # validate every import
python3 -m unittest discover -s tests -t .    # includes tests/test_manual_imports.py
```

`decode("30", key)` returns the description, priority and page, plus `tier`, `status`,
`source_url` and `import_id`. `decode("7G", key)` returns `not_in_key`.

## What a person must do, per source

| Source | Steps | What gets committed |
|---|---|---|
| DOB's newer complaint category list | 1. Open [complaint_category.pdf](https://www.nyc.gov/assets/buildings/pdf/complaint_category.pdf) in a browser and save it.<br>2. Run `python3 -m manual_imports.new_import dob_complaint_categories <file> --url <that URL> --by <role>`.<br>3. Type or paste the codes into `facts.json` with page numbers.<br>4. Fill in `extraction_method` and `document_date` (or the reason it is null).<br>5. Run `load_imports`. | Codes, descriptions, pages, provenance. The newer import wins (`load_all` lists newest first) |
| Check the Rev. 12/18 import | A teammate other than the extractor compares `facts.json` with the PDF. They can download it from the `eabe-havv` page, or the agent can re-fetch it with approval. Then they add `"checked": {"by", "on", "how"}` | One provenance edit |
| DOB NOW documents (start with the Adjoining Owners Notification, B01330433-S3) | 1. Open the [portal](https://a810-dobnow.nyc.gov/publish/#!/) in a browser, search the job, go to its Documents tab and download the file.<br>2. Run `new_import dob_now_document <file> --url <the document URL> --by <role>`.<br>3. Record only: job filing, document title, the date on the document, and one short fact per page (for example, which section the letter cites, or the notice date it states). | Facts and provenance. **No names, no addresses of private people, no drawings.** The lead in `data/leads/` stays a lead. Moving it to "read" is the checklist session's call |
| Precedent cases (news, forensic reports) | 1. Read the article or report in a browser.<br>2. Run `new_import precedent_report --no-file --url <article URL> --by <role>`.<br>3. Fill in the publisher's terms URL and clause.<br>4. Record per event: date, address, BBL if known, type, a plain fact, an optional quote of 25 words or fewer, and a paragraph or page locator. | Facts, links and short quotes. No blame and no causes beyond what an official report states |
| Admin Code and Building Code text | Read amlegal and the nyc.gov PDFs in a browser. Keep citing section numbers with a paraphrase and link, as `checklist_rules.py` does | Nothing new |
| Zillow | Confirm the terms clause on [zillow.com/corporate/terms-of-use](https://www.zillow.com/corporate/terms-of-use/) if anyone still wants it. Don't copy listings | Nothing |
| CityWatch | Whoever raised it sends the URL; we check its terms then | Nothing yet |
| BuildNYC | Only if the team wants a license: a person contacts BuildNYC. No access until signed | Nothing yet |
| USGS rasters, DCP 3D model, complaints data dictionary | Say yes to the download, giving the file and size from the table above. They're plain downloads, so a script or a person can fetch them | Extracted values only, such as depth to bedrock at a lot, with provenance. The rasters and the model stay local |

## For the session that owns data_pull and checklist

These are requests. This branch does not touch `data_pull/` or `checklist/`.

1. **Pull `6v9u-ndjg` (disposition codes) as a reference table.** It is keyless and needs no
   manual import. Show a code it lacks (AF, H8 today) as a gap.
2. **Decode `complaint_category` with the import:**
   `manual_imports.load_imports.load_all(source_key="dob_complaint_categories")[0]` and `decode()`.
   Show the meaning with its tier and source, keep the raw code, and show `not_in_key` as a gap.
3. **Add a basis kind `manual_import`** next to `public_record`, `user_input` and `code_text`, and
   carry `status` through. An imported fact must never be counted as a public-record pull.
4. **Leave the leads file alone.** When a DOB NOW document import exists, linking it to the 3309.1.1
   lead is the checklist's decision.

## Where this differed from api_data_sources.md

- That page once named `nyc_3dmodel_bk14.zip` for the hero site. PLUTO puts both hero lots in
  Brooklyn Community District 17 (`cd` = 317, queried 2026-11-14). Its owner has since corrected
  the page to `bk17`, so the two pages now agree.

## Unchecked

- NYC Open Data's own site terms; we relied on the Administrative Code instead.
- FEMA's and USGS's terms in full.
- Whether DOB NOW documents all open for the public.
- Whether the newer nyc.gov category list carries a date, and whether DOB publishes a newer
  disposition list.
- Zillow's terms page itself.
- Whether the NYC code PDFs carry an ICC copyright notice.
- Which flood map NYC's Building Code uses.
