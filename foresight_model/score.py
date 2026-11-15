"""Score a SiteProfile with the exported model (artifacts/model.json), in plain Python.

The result is a `PatternScore`: a calibrated score, where the site falls among similar past filings, and
the features that moved its score most. Every contribution is exact: the bias plus the contributions
equals the model's raw score.
"""

from __future__ import annotations

import json
import math
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path
from typing import Optional

from api.contracts import PatternScore
from foresight_model.features import LABELS, features_from_profile, in_similar_group, similar_group_text

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "model.json"


class ModelUnavailable(Exception):
    """The model has not been trained or its file cannot be read."""


@lru_cache(maxsize=4)
def load_model(path: Path = MODEL_PATH) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ModelUnavailable(f"pattern model not available: {error}") from error


def explain(model: dict, features: dict) -> tuple[float, float, dict[str, float]]:
    """(raw score, bias, contribution per feature), with raw = bias + sum(contributions)."""
    x = [float(features[f]) for f in model["features"]]
    lr = model["learning_rate"]
    bias = model["init_raw"]
    contrib = {f: 0.0 for f in model["features"]}
    for tree in model["trees"]:
        node = 0
        bias += lr * tree["expected"][0]
        while tree["left"][node] != -1:
            f = tree["feature"][node]
            child = tree["left"][node] if x[f] <= tree["threshold"][node] else tree["right"][node]
            contrib[model["features"][f]] += lr * (tree["expected"][child] - tree["expected"][node])
            node = child
    return bias + sum(contrib.values()), bias, contrib


def calibrated(model: dict, raw: float) -> float:
    c = model["calibration"]
    return 1 / (1 + math.exp(-(c["a"] * raw + c["b"])))


def _value(feature: str, value) -> str:
    if feature.startswith(("flag_", "job_", "boro_")):
        return "yes" if value else "no"
    if feature == "oldest_neighbor_year" and not value:
        return "unknown"
    return str(value)


def pattern_score(profile: dict, as_of: Optional[str] = None, model: Optional[dict] = None,
                  top: int = 4) -> dict:
    model = model or load_model()
    features = features_from_profile(profile, as_of)
    raw, _, contrib = explain(model, features)
    score = calibrated(model, raw)
    similar = in_similar_group(features)
    pool = sorted(r["score"] for r in model["reference_scores"] if r["similar"] or not similar)
    percentile = 100.0 * bisect_left(pool, score) / len(pool) if pool else 0.0
    group = similar_group_text() if similar else "past earth-work, foundation or excavation-support filings citywide"
    factors = sorted(((f, c) for f, c in contrib.items() if abs(c) >= 0.005), key=lambda fc: -abs(fc[1]))[:top]
    observed = sum(1 for s in pool if s >= score)
    result = {
        "bbl": profile["bbl"],
        "score": round(score, 3),
        "percentile_vs_similar": round(percentile, 1),
        "compared_with": f"{len(pool)} {group} (2021 to 2025 sample)",
        "top_factors": [{"feature": LABELS[f], "value": _value(f, features[f]), "contribution": round(c, 3)}
                        for f, c in factors],
        "model_version": model["model_version"],
        "calibration_note": (
            f"This site's pattern ranks above {percentile:.0f}% of the compared filings ({observed} of {len(pool)} "
            "scored this high or higher). The model looks for a structural complaint or construction incident on "
            "the site or a touching lot within 12 months of earth work; complaints are reports, not findings. "
            "On held-out filings it ranked sites only somewhat better than chance, so read the score as a ranking "
            "and the factors as what stands out, not as a probability. This compares patterns; it is not a "
            "prediction that this building will fail. See the model card."),
    }
    return PatternScore.model_validate(result).model_dump()
