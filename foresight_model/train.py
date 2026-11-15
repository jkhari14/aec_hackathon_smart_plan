"""Train the pattern model, evaluate it on a time split, calibrate it and export it as plain JSON.

    .venv/bin/pip install scikit-learn        # training only; the API scores the JSON with no dependencies
    .venv/bin/python -m foresight_model.train

Reads foresight_model/artifacts/rows.json (from `foresight_model.dataset`) and writes model.json,
metrics.json and MODEL_CARD.md beside it.

Evaluation: train on filings before the split date, test on filings after it (the model never sees the
future). The served model is then refit on every row, and its calibration is fit on out-of-fold scores.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

from foresight_model.features import FEATURES, LABELS, in_similar_group

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
SPLIT_DATE = "2024-07-01"
PARAMS = {"n_estimators": 150, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.8,
          "min_samples_leaf": 10, "random_state": 0}
MODEL_VERSION = "foresight-gbm-1"


def _matrix(rows):
    return [[row["features"][f] for f in FEATURES] for row in rows], [row["label"] for row in rows]


def export_tree(tree) -> dict:
    """One regression tree as lists, with each node's expected leaf value (sample-weighted), so the
    per-feature contributions along a path add up exactly to the leaf value."""
    t = tree.tree_
    left, right = t.children_left.tolist(), t.children_right.tolist()
    weight = t.weighted_n_node_samples.tolist()
    value = [float(v) for v in t.value[:, 0, 0]]
    expected = list(value)

    def fill(node: int) -> float:
        if left[node] == -1:
            return expected[node]
        a, b = fill(left[node]), fill(right[node])
        expected[node] = (a * weight[left[node]] + b * weight[right[node]]) / weight[node]
        return expected[node]

    fill(0)
    return {"feature": t.feature.tolist(), "threshold": [float(x) for x in t.threshold],
            "left": left, "right": right, "expected": [round(x, 6) for x in expected]}


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def reliability(probs, labels, bins: int = 5) -> list[dict]:
    pairs = sorted(zip(probs, labels))
    out, size = [], max(1, len(pairs) // bins)
    for i in range(0, len(pairs), size):
        chunk = pairs[i:i + size]
        out.append({"mean_predicted": round(sum(p for p, _ in chunk) / len(chunk), 3),
                    "observed_rate": round(sum(y for _, y in chunk) / len(chunk), 3), "n": len(chunk)})
    return out


def train(rows: list[dict]) -> tuple[dict, dict]:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    rows = sorted(rows, key=lambda r: r["filing_date"])
    train_rows = [r for r in rows if r["filing_date"] < SPLIT_DATE]
    test_rows = [r for r in rows if r["filing_date"] >= SPLIT_DATE]
    X_train, y_train = _matrix(train_rows)
    X_test, y_test = _matrix(test_rows)
    X_all, y_all = _matrix(rows)

    # 1. Time-split evaluation.
    model = GradientBoostingClassifier(**PARAMS).fit(X_train, y_train)
    oof = cross_val_predict(GradientBoostingClassifier(**PARAMS), X_train, y_train,
                            cv=StratifiedKFold(5, shuffle=True, random_state=0), method="decision_function")
    platt = LogisticRegression().fit([[x] for x in oof], y_train)
    raw_test = model.decision_function(X_test)
    p_raw = [_sigmoid(x) for x in raw_test]
    p_cal = platt.predict_proba([[x] for x in raw_test])[:, 1].tolist()
    base_rate = sum(y_test) / len(y_test)
    rule = [int(r["features"]["pre1940_attached"] > 0) for r in test_rows]
    rule_hits = sum(1 for a, y in zip(rule, y_test) if a and y)
    metrics = {
        "rows": len(rows), "positives": sum(y_all), "train_rows": len(train_rows), "test_rows": len(test_rows),
        "split": f"train: filings before {SPLIT_DATE}; test: filings from {SPLIT_DATE} on",
        "test_base_rate": round(base_rate, 3),
        "test_roc_auc": round(roc_auc_score(y_test, p_cal), 3),
        "test_average_precision": round(average_precision_score(y_test, p_cal), 3),
        "test_brier_uncalibrated": round(brier_score_loss(y_test, p_raw), 4),
        "test_brier_calibrated": round(brier_score_loss(y_test, p_cal), 4),
        "test_brier_base_rate_only": round(brier_score_loss(y_test, [base_rate] * len(y_test)), 4),
        "test_reliability_calibrated": reliability(p_cal, y_test),
        "baseline_rule_pre1940_attached": {
            "flagged": sum(rule),
            "precision": round(rule_hits / sum(rule), 3) if sum(rule) else None,
            "recall": round(rule_hits / sum(y_test), 3) if sum(y_test) else None,
        },
    }

    # 2. The served model: refit on every row, calibrated on out-of-fold scores.
    final = GradientBoostingClassifier(**PARAMS).fit(X_all, y_all)
    oof_all = cross_val_predict(GradientBoostingClassifier(**PARAMS), X_all, y_all,
                                cv=StratifiedKFold(5, shuffle=True, random_state=0), method="decision_function")
    platt_all = LogisticRegression().fit([[x] for x in oof_all], y_all)
    a, b = float(platt_all.coef_[0][0]), float(platt_all.intercept_[0])
    prior = sum(y_all) / len(y_all)
    trees = [export_tree(est[0]) for est in final.estimators_]
    raw_all = final.decision_function(X_all)
    reference = [{"score": round(_sigmoid(a * raw + b), 4), "similar": in_similar_group(row["features"])}
                 for raw, row in zip(raw_all, rows)]
    importances = sorted(zip(FEATURES, final.feature_importances_.tolist()), key=lambda x: -x[1])
    metrics["feature_importance"] = [{"feature": f, "label": LABELS[f], "importance": round(v, 3)}
                                     for f, v in importances]
    exported = {
        "model_version": MODEL_VERSION,
        "trained_on": date.today().isoformat(),
        "features": FEATURES,
        "init_raw": math.log(prior / (1 - prior)),
        "learning_rate": PARAMS["learning_rate"],
        "trees": trees,
        "calibration": {"method": "platt", "a": a, "b": b},
        "reference_scores": reference,
        "label_definition": LABEL_TEXT,
    }
    return exported, metrics


LABEL_TEXT = ("A DOB complaint in category 30, 14, 16 or 5C, or a construction incident other than a worker "
              "fall, on the site or a touching lot within 12 months after an earth-work, foundation or "
              "support-of-excavation filing.")


def verdict(m: dict) -> str:
    """One honest sentence on whether the model earns its place, from the test numbers."""
    ranks = m["test_roc_auc"] >= 0.6 and m["test_average_precision"] > m["test_base_rate"]
    calibrated = m["test_brier_calibrated"] < m["test_brier_base_rate_only"]
    if ranks and calibrated:
        return "The model ranks sites better than chance and its probabilities beat the base rate on the test set."
    if ranks:
        return ("The model ranks sites somewhat better than chance (ROC AUC "
                f"{m['test_roc_auc']}), but its probabilities are no better than the base rate on the test set "
                f"(Brier {m['test_brier_calibrated']} vs {m['test_brier_base_rate_only']}). Use the score to rank "
                "sites and to show which factors stand out, not as a probability.")
    return "The model does not beat chance on the test set; show its factors only, not its score."


def model_card(metrics: dict, built: dict) -> str:
    m = metrics
    rel = "\n".join(f"| {b['mean_predicted']:.3f} | {b['observed_rate']:.3f} | {b['n']} |"
                    for b in m["test_reliability_calibrated"])
    imp = "\n".join(f"| {f['label']} | {f['importance']:.3f} |" for f in m["feature_importance"][:10])
    rule = m["baseline_rule_pre1940_attached"]
    return f"""# Model card: ForeSite pattern model ({MODEL_VERSION})

**What it is.** A gradient-boosted tree model that says how a site's pattern compares with past
earth-work filings across NYC. It is shown as "pattern score compared with similar sites".
**It does not predict that a building will fail**, and a low score does not mean a site is safe.

**Label.** {LABEL_TEXT} Complaints are reports, not findings, so the label measures "trouble was
reported", not "damage happened".

**Data.** {m['rows']} lots sampled by hash of BBL from DOB NOW filings with earth work, foundation or
support of excavation, 2021 to Oct 2025 (built {built['built_on']}, {built['sites_sampled']} sampled,
{len(built['failed_sites'])} failed to pull). {m['positives']} rows ({m['positives'] / m['rows']:.0%}) have the label.
Sources: DOB NOW filings, PLUTO, tax lot polygons, building footprints, DOB complaints, construction
incidents (NYC Open Data).

**Features** (only what was knowable on the filing date): job type and work-type flags, touching lots and
attached neighbors, neighbors built before 1940, oldest neighbor year, neighbor floors and height,
pre-1940 walk-up neighbors, structural complaints and incidents in the 3 years before, borough.

## Evaluation (time split)

{m['split']}. Train {m['train_rows']} rows, test {m['test_rows']} rows.

| Metric (test) | Value |
|---|---|
| Base rate | {m['test_base_rate']} |
| ROC AUC | {m['test_roc_auc']} |
| Average precision | {m['test_average_precision']} (base rate {m['test_base_rate']}) |
| Brier, calibrated | {m['test_brier_calibrated']} |
| Brier, uncalibrated | {m['test_brier_uncalibrated']} |
| Brier, base rate only | {m['test_brier_base_rate_only']} |

**Verdict.** {verdict(m)}

Baseline rule "any attached neighbor built before 1940": flags {rule['flagged']} test rows, precision
{rule['precision']}, recall {rule['recall']}.

**Calibration** (Platt scaling on out-of-fold scores), test reliability:

| Mean predicted | Observed rate | Rows |
|---|---|---|
{rel}

## Most important features

| Feature | Importance |
|---|---|
{imp}

## Limitations

- A small sample ({m['rows']} lots). Treat the score as a conversation starter for the engineer, not evidence.
- Complaints join by BIN from current building footprints. A building's old BIN, or a new one the
  footprints don't list yet, is missed, so some outcomes are undercounted.
- Complaints are reports. Many are closed with no violation. 311 requests are not used, so nothing is
  double counted.
- Touching means touching on the tax map. Public data does not say whether walls are shared.
- No soil, groundwater, excavation depth, contractor practice or monitoring data: the things that matter
  most are not in the model.
- Served model: refit on every row after evaluation; the reported metrics are from the time-split model.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=Path, default=ARTIFACTS / "rows.json")
    args = parser.parse_args(argv)
    built = json.loads(args.rows.read_text())
    exported, metrics = train(built["rows"])
    (ARTIFACTS / "model.json").write_text(json.dumps(exported, separators=(",", ":")) + "\n")
    (ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=1) + "\n")
    (ARTIFACTS / "MODEL_CARD.md").write_text(model_card(metrics, built))
    print(json.dumps({k: v for k, v in metrics.items() if not isinstance(v, list)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
