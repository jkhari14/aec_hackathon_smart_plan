# PreFlight: data and code notes

Written as a companion to the team's first plan, README-Camilo (deleted in 2edb488 and kept in the
repo's history). The current plan is [foresite_build_plan.md](foresite_build_plan.md). This file:

- answers its "⚠️ Verify" data items,
- gives the hero demo case's facts,
- proposes one change to the risk engine.

Every fact here comes from a public source linked below, and every record was pulled on 2026-11-14.

## A proposed change: build the checklist on the Building Code

The plan matches a project against 10 to 20 curated past failures, each tagged with its root cause.
The weak link is that root cause. It is rarely established in public, and for 1321 Flatbush it is
still under investigation. With so few precedents, a new project's matches will be thin.

The proposal:

- **The checklist rows come from Chapter 33 of the Building Code**, the city's written lessons from
  past failures. Each row becomes a code section, a responsible discipline, and the proof that
  the duty was done.
- **The precedent library stays** for the map, the hook and the "why it matters" line under each
  row, with causes labeled "as publicly reported" and nothing said about what could have been
  prevented.

This fits the plan's own rule ("Rules decide the risks; LLM only phrases them"): the rules become
code sections. It also gives the demo a sharper reveal, a duty with no proof.

One more user worth adding: **the adjoining owner**, who grants access to their building without the
technical knowledge to judge the work.

## The checklist spine (2022 NYC Building Code)

The rows live in [checklist/README.md](../checklist/README.md): twelve duties from chapters 33 and
17, each with the parties who act on it, whether it is life safety, and the proof it needs. That
file is the one copy, so the table that used to sit here was removed rather than kept in step.

## The data, verified (NYC Open Data)

This answers the plan's "⚠️ Verify dataset names, API access, and fields" item. All of these are
open, keyless SODA endpoints (`https://data.cityofnewyork.us/resource/<ID>.json`).

| Dataset | ID | Join | Trap |
|---|---|---|---|
| PLUTO (lot data) | `64uk-42ks` | `bbl` | Lags reality: it still lists 2625 Bedford as a 1933 one-story building |
| DOB NOW job filings | `w9ak-ipjd` | `bbl`, `bin`, job number | One row per filing (`-I1`, `-S3`...). Earth work can sit on a later filing |
| DOB violations | `3h2n-5cm9` | `boro` + `block` + `lot`, or `bin` | No `bbl` column. `lot` is stored in several widths (`00073`, `0073`), so query all of them. Status is free text |
| ECB violations | `6bgk-3dad` | `boro` + `block` + `lot` | Carries the section of law and the inspector's note |
| DOB safety violations | `855j-jady` | `bbl`, `bin` | The newer civil-penalty set. It holds 1321 Flatbush's open violation; the two older sets do not |
| HPD violations (housing agency) | `wvxf-dwi5` | `bbl` | Not DOB. "Open" includes items decades old |
| DOB complaints | `eabe-havv` | `bin` only | Categories are 2-character codes, read from DOB's printed list ([imported by hand](manual_data_imports.md)); dispositions are read from Open Data `6v9u-ndjg`. The [checklist](../checklist/README.md#complaint-codes-decoded) decodes both and shows a code either one lacks as a gap |
| 311 requests routed to DOB | `erm2-nwe9` | `bbl`, with `agency='DOB'` | The complaint in words and DOB's resolution. Can repeat a DOB complaint with no shared key, so never add the two. Rows with no `bbl` are missed: 2,004 DOB rows in 2026 so far, all filed by address (queried 2026-11-14). Starts 2020-01-01 |

- **We have not found stop-work orders as their own dataset**, so the plan's data row needs
  adjusting. They surface indirectly: a DOB violation that says so, or an ECB violation for
  continuing work while one was in effect.
- **Adjoining lots:** tax-lot polygons (`i38t-6if2`) and a server-side `intersects()` query,
  which [data_pull](../data_pull/README.md) already does. Consecutive lot numbers are a hint,
  not proof.

## Hero demo case: what the record showed (pulled 2026-11-14)

On November 11, 2026, 1321 Flatbush Ave collapsed into the excavation next door at 2625 Bedford
Ave. Eight people were killed
([NYT](https://www.nytimes.com/live/2026/11/12/nyregion/building-collapse-nyc-brooklyn)). These are
facts only, and nothing here establishes a cause.

- **1321 Flatbush Ave** (BBL 3052110073):
  - Built 1930, three floors, four apartments, 20.5 ft wide.
  - HPD lists 98 open and 31 closed violations. All 98 open ones come from inspections between 1977
    and May 2026. This is the "98 violations" in the news, and they are HPD's, not DOB's.
- **2625 Bedford Ave** (BBL 3052110074, the next lot on the block):
  - DOB NOW job B01330433, a new building. Filing `-S3` covers earth work and foundation; it was
    approved 2026-06-03. Its status now reads "On Hold – Administrative Action", dated
    2026-11-13, like seven other filings on the site. An earlier pull on 2026-11-14 showed "On Hold
    - Pending Withdrawal of Special Inspector".
  - ECB, 2026-03-20: work not as approved, with overhead protection for adjacent properties missing
    during demolition. Resolved.
  - ECB, 2026-04-23: work continued while a stop-work order was in effect. Resolved.
  - ECB, 2026-11-11: failure to safeguard persons and property. Active.
  - [Northeastern](https://news.northeastern.edu/2026/11/12/brooklyn-building-collapse-analysis/)
    links an adjoining-owner notification on DOB NOW and dates the letter June 10. Nobody here has
    read it, and when it was filed is not known (`data/leads/2625-bedford-ave-brooklyn.json`).

The demo can show which duties the public record says apply, and that their proof (the
preconstruction survey and the monitoring readings, for example) is not in public data. The question it answers is
what was knowable, by whom, and when. It does not answer who is to blame.

## Decisions from the team meetings (2026-11-14)

From the two [brainstorm transcripts](../transcripts/), and what they mean for the data and the checklist:

- **Neutral framing.** Public facts only, an ongoing investigation called ongoing, no blame, and no
  claim that a collapse could have been prevented.
- **No roast humor in this project.** The checklist's `life_safety` flag marks rows that protect life
  safety; it no longer sets a tone.
- **No permit-holder, contractor, owner or applicant names.** `data_pull` never requests them.
- **Hazards in scope:** structural collapse, fire, flooding, soil contamination, extreme weather.
  The checklist covers only duties toward adjoining property during excavation and foundation work
  so far. The other four hazards have no rows and no data source in the pull yet.
- **Past violations are not a predictor.** Before the collapse, 1321 Flatbush's open records were
  housing violations, 13 sign violations from 2019, and one missed gas-piping filing. Nothing was
  structural. Counts are shown as context, never as a score.
- **The demo hook is the Brooklyn collapse.** The meeting also discussed an alteration for "just
  the walkthrough right now", and that is noted as a later focus. For now every project type stays
  open. 2625 Bedford is a new-building job.
- **Address facts:** zoning, lot area, floor area ratios, year built, and PLUTO's landmark and
  historic-district fields come with the pull. Flood zone has no source yet.
- **Sources we cannot crawl** (DOB NOW documents, JustFix, BuildNYC, Zillow and others) are being
  checked for a manual import path by a separate session.

## Rules for the build

- **Every row shows its source:** a dataset record or a code section with its link. Otherwise it
  says "not found in public data".
- **Requirement, record and inference look different on screen.** A guess never looks like a fact.
- **No cause is ever inferred.** A news report is a lead, not evidence.

## Open questions

- Which DOB NOW documents are public enough to fill rows? The notice letter is; are the support drawings?
