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
- `building_profile.py`: the four facts that make two buildings alike here: era (the 1938, 1968 and
  2008 code eras), wall system (masonry bearing wall, wood frame, steel or concrete frame), height band
  and attachment. Each comes with its basis. A wall system is stated by the Revit model or a case
  write-up, else guessed from PLUTO's building class and year and labeled as a guess; houses get no
  guess. Attachment is PLUTO's proximity code when it has one.
- `similarity.py`: a weighted, explainable score. Half is the building: the case's hurt building against
  the site's own building and each touching neighbor on the four facts, the best match named in words
  ("the neighbor at 454 East 25 Street is like the building in this case: masonry bearing wall (inferred
  from building class and year), attached"). For an excavation case on a new-building site only the
  neighbors are compared, since the site's building is the one being replaced. The other half is earth
  work, other work types, record signals, soil and flood. A condition a case does not report is not
  counted as a difference. Cases dated after the as-of date, or on the site's own lots, are not offered.
  Style, zoning and risk category are left out on purpose: they describe looks and use, not fragility.

Known gaps: `attached` means the lots touch on the tax map and the neighbor has a building (public data
does not say whether walls are shared, so `shared_wall_ft` is null). Soil, flood and E-designation come from
`city_layers.site_context`; bedrock stays null (no point lookup exists).
