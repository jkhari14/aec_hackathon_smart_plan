# PreFlight: data and code notes

A companion to [README-Camilo](../README-Camilo), which is the plan. This file:

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
  roast, with causes labeled "as publicly reported".

This fits the plan's own rule ("Rules decide the risks; LLM only phrases them"): the rules become
code sections. It also gives the demo a sharper reveal, a duty with no proof.

One more user worth adding: **the adjoining owner**, who grants access to their building without the
technical knowledge to judge the work.

## The checklist spine (2022 NYC Building Code)

This is our paraphrase. Read the city's text before relying on any row:
[Chapter 33](https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter33_Con_DemoSafetyWBwm.pdf),
[Chapter 17](https://www.nyc.gov/assets/buildings/codes-pdf/cons_codes_2022/2022BC_Chapter17_SpecialInspectionsWBwm.pdf).

| Section | What it requires | Who | Proof |
|---|---|---|---|
| 3309.1.1 | Written notice to the adjoining owner at least 60 days before work: the work, schedule, monitoring, protection, contact. A second notice if there is no reply | Owner / developer | The letter and its date |
| 3309.2 | The adjoining owner affords a license to enter; 3309.4 says who carries the duty if they don't | Adjoining owner | License, or the refusal |
| 3309.3 | Physical examination of the adjoining property before work and during it, recorded and available to DOB | Whoever causes the work | Inspection records |
| 3309.4.3 | No excavation 5 to 10 ft deep within 10 ft of an adjacent building, or over 10 ft anywhere, until a preconstruction survey documents all adjacent buildings | Owner / design professional | The survey |
| 3304.4.1 | Excavation-support drawings by a design professional with retaining or bracing experience; over 20 ft deep, a NY State PE | Support engineer | Stamped drawings |
| 3304.4.1.2 | Those drawings rest on site-specific testing and incorporate the geotechnical report, the evaluation analysis and the preconstruction survey | Geotech + support engineer | Cross-references |
| 3309.4, 3309.5 | Protect adjoining footings and foundations; underpin at the builder's expense | Developer / contractor | Underpinning drawings, installed as drawn |
| 3309.8 | Where an adjoining wall is exposed, a design professional investigates its stability and condition | Design professional | Investigation report |
| 3309.4.4, 3309.16 | Monitor buildings within the excavation's depth of its edge, under a plan that sets scope, frequency, tolerances and when to report | Design professional / contractor | Plan and readings |
| 1705.25.4 | Underpinning is subject to special inspections | Special inspector | Inspection reports |
| 3309.4.5 | Where DOB sees a potential hazard, elevations are recorded at intervals of 24 hours or less | DOB / design professional | Readings |

## The data, verified (NYC Open Data)

This answers the plan's "⚠️ Verify dataset names, API access, and fields" item. All of these are
open, keyless SODA endpoints (`https://data.cityofnewyork.us/resource/<ID>.json`).

| Dataset | ID | Join | Trap |
|---|---|---|---|
| PLUTO (lot data) | `64uk-42ks` | `bbl` | Lags reality: it still lists 2625 Bedford as a 1933 one-story building |
| DOB NOW job filings | `w9ak-ipjd` | `bbl`, `bin`, job number | One row per filing (`-I1`, `-S3`...). Earth work can sit on a later filing |
| DOB violations | `3h2n-5cm9` | `boro` + `block` + `lot`, or `bin` | No `bbl` column. `lot` is stored in several widths (`00073`, `73`), so query all of them. Status is free text |
| ECB violations | `6bgk-3dad` | `boro` + `block` + `lot` | Carries the section of law and the inspector's note |
| DOB safety violations | `855j-jady` | `bbl`, `bin` | The newer civil-penalty set. It holds 1321 Flatbush's open violation; the two older sets do not |
| HPD violations (housing agency) | `wvxf-dwi5` | `bbl` | Not DOB. "Open" includes items decades old |
| DOB complaints | `eabe-havv` | `bin` only | Categories are 2-character codes; DOB publishes the key separately |

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
    approved 2026-06-03 and now reads "On Hold - Pending Withdrawal of Special Inspector".
  - ECB, 2026-03-20: work not as approved, with overhead protection for adjacent properties missing
    during demolition. Resolved.
  - ECB, 2026-04-23: work continued while a stop-work order was in effect. Resolved.
  - ECB, 2026-11-11: failure to safeguard persons and property. Active.
  - The adjoining-owner notice dated June 10 is posted on DOB NOW
    ([reported by Northeastern](https://news.northeastern.edu/2026/11/12/brooklyn-building-collapse-analysis/)).

The demo can show which checklist rows the public record fills, and which stay "not in public data"
(the preconstruction survey and the monitoring readings, for example). The question it answers is
what was knowable, by whom, and when. It does not answer who is to blame.

## Rules for the build

- **Every row shows its source:** a dataset record or a code section with its link. Otherwise it
  says "not found in public data".
- **Requirement, record and inference look different on screen.** A guess never looks like a fact.
- **No cause is ever inferred.** A news report is a lead, not evidence.

## Open questions

- Which DOB NOW documents are public enough to fill rows? The notice letter is; are the support drawings?
