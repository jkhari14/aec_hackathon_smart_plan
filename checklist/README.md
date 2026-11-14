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

## The rows

Twelve rows from the 2022 Building Code, chapter 33 (safeguards during construction) and
chapter 17 (special inspections). Each row is paraphrased and links to the city's PDF, so read the
code text before relying on a row. The rows are in `checklist_rules.py`.

| Section | Duty | Scope |
|---|---|---|
| 3309.1.1 | Notify the adjoining owner 60 days ahead | site |
| 3309.2 | License to enter the adjoining property | site |
| 3309.3 | Examine the adjoining building before and during work | each adjacent building |
| 3309.4 | Protect adjoining footings and foundations | site |
| 3309.4.3 | Preconstruction survey | each adjacent building |
| 3304.4.1 | Excavation-support drawings | site |
| 3304.4.1.2 | Geotechnical basis for the support design | site |
| 3309.5 | Underpin or otherwise support adjoining buildings | site |
| 1705.25.4 | Special inspection of underpinning | site |
| 3309.8 | Investigate exposed adjoining walls | site |
| 3309.4.4 | Monitor nearby buildings | each adjacent building |
| 3309.4.5 | Hazard monitoring ordered by DOB | site |

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

`proof.status` is `not_provided` or `provided_unverified`. The public record does not hold
notice letters, surveys, support drawings or inspection reports, so no row is ever marked done
from it. `provided_unverified` means the project team listed a document under `provided_proof`,
and nobody checked it. `open_gap` is true when a row applies and no proof was provided.

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

Nothing here establishes the cause of any incident.
