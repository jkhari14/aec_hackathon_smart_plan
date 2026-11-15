# Model card: ForeSite pattern model (foresight-gbm-1)

**What it is.** A gradient-boosted tree model that says how a site's pattern compares with past
earth-work filings across NYC. It is shown as "pattern score compared with similar sites".
**It does not predict that a building will fail**, and a low score does not mean a site is safe.

**Label.** A DOB complaint in category 30, 14, 16 or 5C, or a construction incident other than a worker fall, on the site or a touching lot within 12 months after an earth-work, foundation or support-of-excavation filing. Complaints are reports, not findings, so the label measures "trouble was
reported", not "damage happened".

**Data.** 434 lots sampled by hash of BBL from DOB NOW filings with earth work, foundation or
support of excavation, 2021 to Oct 2025 (built 2026-11-14, 434 sampled,
0 failed to pull). 32 rows (7%) have the label.
Sources: DOB NOW filings, PLUTO, tax lot polygons, building footprints, DOB complaints, construction
incidents (NYC Open Data).

**Features** (only what was knowable on the filing date): job type and work-type flags, touching lots and
attached neighbors, neighbors built before 1940, oldest neighbor year, neighbor floors and height,
pre-1940 walk-up neighbors, structural complaints and incidents in the 3 years before, borough.

## Evaluation (time split)

train: filings before 2024-07-01; test: filings from 2024-07-01 on. Train 335 rows, test 99 rows.

| Metric (test) | Value |
|---|---|
| Base rate | 0.131 |
| ROC AUC | 0.64 |
| Average precision | 0.248 (base rate 0.131) |
| Brier, calibrated | 0.1161 |
| Brier, uncalibrated | 0.1174 |
| Brier, base rate only | 0.1141 |

**Verdict.** The model ranks sites somewhat better than chance (ROC AUC 0.64), but its probabilities are no better than the base rate on the test set (Brier 0.1161 vs 0.1141). Use the score to rank sites and to show which factors stand out, not as a probability.

Baseline rule "any attached neighbor built before 1940": flags 69 test rows, precision
0.159, recall 0.846.

**Calibration** (Platt scaling on out-of-fold scores), test reliability:

| Mean predicted | Observed rate | Rows |
|---|---|---|
| 0.029 | 0.053 | 19 |
| 0.045 | 0.105 | 19 |
| 0.057 | 0.105 | 19 |
| 0.070 | 0.158 | 19 |
| 0.093 | 0.211 | 19 |
| 0.146 | 0.250 | 4 |

## Most important features

| Feature | Importance |
|---|---|
| tallest neighbor (roof height, ft) | 0.304 |
| oldest neighbor (year built) | 0.156 |
| tallest neighbor (floors) | 0.143 |
| pre-1940 residential or mixed-use neighbors | 0.081 |
| new building | 0.077 |
| touching lots | 0.051 |
| touching lots with a building | 0.050 |
| attached neighbors built before 1940 | 0.048 |
| in Brooklyn | 0.030 |
| in Bronx | 0.021 |

## Limitations

- A small sample (434 lots). Treat the score as a conversation starter for the engineer, not evidence.
- Complaints join by BIN from current building footprints. A building's old BIN, or a new one the
  footprints don't list yet, is missed, so some outcomes are undercounted.
- Complaints are reports. Many are closed with no violation. 311 requests are not used, so nothing is
  double counted.
- Touching means touching on the tax map. Public data does not say whether walls are shared.
- No soil, groundwater, excavation depth, contractor practice or monitoring data: the things that matter
  most are not in the model.
- Served model: refit on every row after evaluation; the reported metrics are from the time-split model.
