# checklist

Takes a `data_pull` file and lists the Building Code duties toward adjoining property:
which ones apply to this site, what document proves each one, and what the public record
shows beside each. Plain Python 3.9+, no packages, no network.

```bash
python3 -m checklist.build_checklist data/cache/2625-bedford-ave-brooklyn.json                     # as of the pull
python3 -m checklist.build_checklist data/cache/2625-bedford-ave-brooklyn.json --as-of 2026-11-11  # what was knowable before Nov 11
python3 -m checklist.build_checklist <pull.json> --inputs data/project_inputs/example_inputs.json  # with project inputs
python3 -m unittest discover -s tests -t .                                                         # offline tests
```

Each run writes `data/checklists/<pull>[-as-of-DATE][-<inputs>].json` and prints a summary.
If `data/leads/<pull file name>.json` exists, its leads are read too (`--no-leads` skips them).

## The rows

Twelve rows from the 2022 Building Code, chapter 33 (safeguards during construction) and
chapter 17 (special inspections). Each row is paraphrased and links to the city's PDF, so read the
code text before relying on a row. The rows are in `checklist_rules.py`.

Each row has a stable `id` that the brief, the web page and the voice agent use. It also has
`parties`, drawn from one fixed list shared with the brief: owner_developer, design_professional,
excavation_support_engineer, geotechnical_engineer, contractor, special_inspector, adjoining_owner
and dob. `life_safety` marks rows where the serious tone comes first.

| id | Section | Duty | Scope | Life safety |
|---|---|---|---|---|
| notice | 3309.1.1 | Notify the adjoining owner 60 days ahead | site | no |
| license | 3309.2 | License to enter the adjoining property | site | no |
| examination | 3309.3 | Examine the adjoining building before and during work | each adjacent building | yes |
| foundation_protection | 3309.4 | Protect adjoining footings and foundations | site | yes |
| survey | 3309.4.3 | Preconstruction survey | each adjacent building | yes |
| support_drawings | 3304.4.1 | Excavation-support drawings | site | yes |
| support_basis | 3304.4.1.2 | Geotechnical basis for the support design | site | yes |
| underpinning | 3309.5 | Underpin or otherwise support adjoining buildings | site | yes |
| underpinning_inspection | 1705.25.4 | Special inspection of underpinning | site | yes |
| exposed_wall | 3309.8 | Investigate exposed adjoining walls | site | yes |
| monitoring | 3309.4.4 | Monitor nearby buildings (plan per 3309.16) | each adjacent building | yes |
| hazard_elevations | 3309.4.5 | Hazard monitoring ordered by DOB | site | yes |

## What decides a row

`applies.status` is one of:

- `applies` or `does_not_apply`, decided from the record, a project input, or a code threshold;
- `needs_input`, with `needs` naming the missing input;
- `set_by_dob`, for a duty that starts only when DOB orders it;
- `unknown`, when the query the answer depends on failed.

Every answer carries a `basis`, and each basis has a `kind`:

- `public_record`: the records it came from;
- `user_input`: a value the project team typed;
- `code_text`: the threshold it applied.

**Excavation is read from the record first.** If a DOB NOW filing on the lot says yes to earth
work, foundation, or support of excavation, the excavation rows apply. A project input that says
otherwise is shown in `notes` and is not obeyed. If the filings query failed, the answer is
`needs_input`, never "no excavation".

**Per-building rows** (3309.3, 3309.4.3, 3309.4.4) are judged for each touching lot that has a
building. A lot counts as having a building when a footprint or PLUTO says so. The row's own
status rolls up in the order applies > needs_input > unknown > set_by_dob > does_not_apply.

## Proof is never taken from public data

The public record does not hold notice letters, surveys, support drawings or inspection
reports, so no row is ever marked done from it. `proof.status` is one of three, and none of them
means verified:

- `provided_unverified`: the project team listed a document under `provided_proof`, and nobody
  checked it.
- `reported_not_read`: a public source, such as a news article linking a portal document, reports
  one. Nobody here has read it. The leads are in `proof.leads` and come from `data/leads/`.
- `not_provided`: neither of the above.

`open_gap` is true when a row applies and the team has provided nothing. **A lead never closes a
gap.** In an as-of view, a lead counts only if its document is dated before the cutoff.

Every record a row points to carries a `ref` in the brief's id format,
`<dataset_key>:<record_id>`.

`related_records` sit beside a row and are not its proof:

- `filings`: site filings with excavation flags, or a status that names an inspector;
- `citations`: violations on the site or a touching lot whose own text cites that section, or a
  more specific part of it.

## The as-of view

`--as-of DATE` keeps only records dated before DATE. **Counts still use each record's status at
pull time**, because the datasets keep only the current status. A violation that was open on
Nov 10 and closed on Nov 12 counts as closed. A filing whose current status is dated on or after
the cutoff is marked `status_is_after_cutoff`. Records with no usable date are counted under
`undated`.

## Project inputs

```json
{"involves_excavation": true, "requires_adjoining_access": true, "underpinning_planned": true,
 "exposes_adjoining_wall": true, "excavation_depth_ft": 12,
 "distance_to_building_ft": {"<adjacent bbl>": 0},
 "provided_proof": {"3309.1.1": {"document": "...", "provided_by": "..."}}}
```

Unknown keys and wrong types are refused. Keys starting with `_` are notes.
`data/project_inputs/example_inputs.json` is **hypothetical**: it is there to show the per-building
logic, and it says nothing about what was planned at 2625 Bedford. Don't commit its output next to
the real-site checklists.

## The demo: 2625 Bedford Ave, as of 2026-11-11

`data/checklists/2625-bedford-ave-brooklyn-as-of-2026-11-11.json`, public record only:

- **Excavation applies.** Filing B01330433-S3 (filed 2026-02-24) says yes to earth work and
  foundation work and "No" to support of excavation.
- **3 open gaps:** 3309.4 (protect adjoining foundations), 3304.4.1 (support drawings) and
  3304.4.1.2 (geotechnical basis). These apply from the record alone, and no proof was provided.
- **8 rows need input**, from four facts the record does not hold: depth, adjoining access,
  underpinning and an exposed wall. **1 row is set by DOB.**
- **A lead on the notice row (3309.1.1).** A Northeastern article links an "Adjoining Owners
  Notification" on DOB NOW for filing S3 and dates the letter June 10. Nobody has read it, and it
  is not known when it was filed.
- **Five touching lots have buildings**, including 1321 Flatbush (built 1930). Lot 3052110054
  has a footprint but no PLUTO record.
- **S3 and S4's current status**, "On Hold - Pending Withdrawal of Special Inspector", is dated
  on or after the cutoff and is flagged as such.
- **One stop-work mention** before the cutoff, on the site: ECB, 2026-04-23, worked while a
  stop-work order was in force. The DOB violation issued on the day of the collapse (a full
  stop-work order) falls on the cutoff, so it is left out.

## Not checked

- Historic status, for the 90 ft monitoring rule.
- Footing positions, for digs of 5 ft or less.
- Whether any document exists.

## For the team's reviewers

These twelve sections are the only ones reviewed for this list. Other parts of sections 3304
and 3309, the rest of chapter 33, and the Administrative Code were not read for it. The brief's
first draft combined 3309.4 with 3309.5, and 3309.4.4 with 3309.16. Here 3309.4 and 3309.5 are
separate rows, and 3309.16 is cited inside the monitoring row.

What we need from each area of expertise:

- **Code consultant or expediter.**
  - Are the paraphrases faithful to the 2022 text?
  - Which other sections belong here?
  - Is the right party on each row?
  - Are the two rows marked not life-safety (notice and license) right?
- **Structural or excavation-support engineer.**
  - Check the thresholds in the per-building rows. The survey applies over 10 ft deep anywhere,
    or 5 to 10 ft deep within 10 ft of a building. Monitoring applies to buildings within the
    excavation's depth of its edge. Digs of 5 ft or less can be exempt.
  - Should 3309.4 and 3309.5 be one row?
  - What project facts would decide underpinning and exposed walls?
- **Geotechnical engineer.**
  - What must the report behind 3304.4.1.2 contain?
  - Could public data, such as borings or groundwater, tell us more before a project starts?
- **Special inspector.**
  - Which DOB NOW filing statuses mean an inspector withdrew or was never assigned?
  - Is "the status names an inspector" a fair way to pick the filings shown beside 1705.25.4?

Nothing here establishes the cause of any incident.
