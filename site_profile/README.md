# site_profile (Rishabh)

Builds a `SiteProfile` for a lot and ranks similar cases. Serves `GET /api/sites/{bbl}/profile` and
`GET /api/sites/{bbl}/similar` (`router.py`).

```bash
.venv/bin/python -m site_profile.build_profile --bbl 3052110074 --as-of 2026-06-01
```

- `build_profile.py`: the profile from a `data_pull.site_brief_pull` result. A saved pull in
  `data/cache/` is used when one exists for the BBL; otherwise it pulls live.
- `signals.py`: record signals. Violations whose text cites adjacent protection, shoring,
  excavation, a collapse, stop-work or safeguarding (severity 1), and DOB complaints in the
  structural categories 03, 14, 16, 30, 54, 2K and 5C on the site and its touching lots (severity 0).
  HPD violations are never signals. With an as-of date, only records dated before it count.
- `work_types.py`: job type and work types from the DOB NOW filings, or inferred from the job type
  (a stand-in table until `city_layers/work_types.py` lands).
- `similarity.py`: a weighted, explainable score over neighbor age and attachment, earth work, other
  work types, construction, signal hazards, job type, soil and flood. Each result lists
  `matched_on` and `differs_on`; a condition a case does not report is not counted as a difference.

Known gaps: `attached` means the lots touch on the tax map and the neighbor has a building (public data
does not say whether walls are shared, so `shared_wall_ft` is null). Soil, bedrock, flood and
E-designation stay null until `city_layers` (PR 2, PR 16) provides them.
