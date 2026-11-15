# foresight_model (Rishabh)

The pattern model behind `GET /api/sites/{bbl}/pattern`, shown as "pattern score compared with similar
sites". Read [artifacts/MODEL_CARD.md](artifacts/MODEL_CARD.md) before showing it to anyone.

```bash
.venv/bin/python -m foresight_model.dataset --per-year 120   # pull training rows (about 15 min, live)
.venv/bin/pip install scikit-learn                            # training only
.venv/bin/python -m foresight_model.train                     # model.json, metrics.json, MODEL_CARD.md
.venv/bin/python -m foresight_model.sequences                 # sequences.json: candidate early-warning rules
```

- `dataset.py`: one row per sampled lot with an earth-work, foundation or SOE filing; features from its
  touching lots and prior records; the 12-month label.
- `features.py`: the feature list, shared by training and by scoring a `SiteProfile`.
- `train.py`: gradient boosting, a time-split evaluation, Platt calibration, and the export to plain
  JSON (with each node's expected value, so explanations add up exactly).
- `score.py`: scores a profile with no ML dependency: score, percentile among similar past filings,
  top factors.
- `sequences.py`: which record sequences came before an outcome most often (support, outcome rate, lift).

## Candidate rules for early warnings (for Jacob, PR 7)

From `artifacts/sequences.json` (434 sampled filings, base rate 7%). These are small counts, so treat
them as hypotheses:

| Before an outcome | Filings | Lift |
|---|---|---|
| "Adjacent building not protected" complaint on the site, then the earth-work filing | 7 | 3.9 |
| "Building shaking / structural stability" complaint on a touching lot (any time in the 3 years before) | 24 | 3.4 |
| "Adjacent building not protected" complaint on the site | 11 | 2.5 |
| Structural stability complaint on the site, then the earth-work filing | 14 | 1.9 |
