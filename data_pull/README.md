# data_pull

Takes an NYC address and pulls the public record for that site and every lot touching it.
It's plain Python 3.9+ with no packages to install and no API keys.

```bash
python3 -m data_pull.site_brief_pull "2625 Bedford Ave, Brooklyn"   # writes data/cache/<slug>.json
python3 -m data_pull.site_brief_pull --bbl 3052110074                # skip the address lookup
python3 -m data_pull.site_brief_pull --demo                          # every address in data/demo_addresses.json
python3 -m unittest discover -s tests -t .                           # offline tests
```

A site with five neighbors takes about 5 seconds. Optional: set `SODA_APP_TOKEN` to a free
NYC Open Data app token for higher rate limits.

**For the demo, read `data/cache/` and don't call live APIs.** Two sites are cached, pulled
2026-11-14: `2625-bedford-ave-brooklyn.json` (the excavation site) and
`1321-flatbush-ave-brooklyn.json` (the building that collapsed).

## What it does

1. **Address to lot.** NYC Planning GeoSearch gives the BBL (borough-block-lot ID) and BIN
   (building ID).
2. **Touching lots.** The city's server intersects the site's tax-lot polygon (`i38t-6if2`) with
   every other tax-lot polygon. A shared edge or corner counts as touching.
3. **BINs per lot.** These come from building footprints (`5zhs-2jue`), the address lookup, and
   DOB NOW filings that state this lot.
4. **Eight datasets per lot:** PLUTO, DOB NOW filings, DOB violations, ECB violations, DOB
   safety violations, HPD violations, DOB complaints, and 311 requests routed to DOB. The
   [data notes](../docs/data_and_code_notes.md) list their IDs and traps.
5. **Stop-work mentions.** These are violation records and 311 resolutions whose own text
   mentions a stop-work order. A 311 resolution is dated by when DOB recorded it.
6. **DOB's disposition code table** (`6v9u-ndjg`), once per pull, kept as printed with the date
   Open Data says its rows last changed. That date is 2017-02-08, and two codes in these pulls
   (AF and H8) are missing from it, probably because they are newer. The checklist decodes
   complaints with it.

## Output shape

```
{
  "pulled_at", "address_lookup": {matched_label, bbl, bin, ...}, "site_bbl",
  "touching_lots_lookup": {status, count},
  "site":          LOT,
  "touching_lots": [LOT, ...],
  "reference_tables": {"dob_complaint_dispositions":
                       {status, dataset_id, rows_updated_at, count, query_url, records: [{code, disposition}]}},
  "sources": {key: {name, dataset_id, url}}, "caveats": [...]
}
LOT = {
  "bbl", "role", "bins", "footprint_buildings": {status, records},
  "datasets": {pluto | dob_now_filings | dob_violations | ecb_violations | dob_safety_violations |
               hpd_violations | dob_complaints | dob_311_requests:
               {status, count, truncated, query_url, records, held_back_other_lot}},
  "stop_work_mentions": [{dataset, record_id, issue_date, field, text}]
}
```

## Rules the UI must keep

- **`status` is one of three things:**
  - `ok` means it was queried, and a `count` of 0 means none were found.
  - `error` means the query failed and nothing is known. Never show an error as zero.
  - `skipped` comes with a `reason`.
- **Show `address_lookup.matched_label`.** GeoSearch matches loosely, so show what was found, not
  what was typed.
- **Every record has a source:** `query_url` reproduces the query exactly.
- **Never add `dob_complaints` and `dob_311_requests`.** The same complaint can be in both, and
  they share no key to match on.
- **`held_back_other_lot` rows are not counted.** They were reached through a BIN, but the record
  itself names a different lot.
- **`stop_work_mentions` is not a list of stop-work orders.** We have not found them published as
  their own dataset.
- **PLUTO and footprints can lag.**
  - PLUTO still shows the old one-story building at 2625 Bedford.
  - The footprints still list 1321 Flatbush as "Constructed".
  - Lot 3052110054 is on the tax map but has no PLUTO record.

## Not included, on purpose

Owner, applicant, respondent, permit-holder and contractor names. The data is public, but the
demo is about what was knowable, not about who is to blame (the team settled this on 2026-11-14).
