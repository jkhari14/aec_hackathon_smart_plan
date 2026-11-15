"""Pattern model (PR 12): exact explanations, wording, the served artifact and sequence mining. Offline."""

from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.contracts import PatternScore
from api.main import app
from foresight_model import features, score, sequences
from site_profile import build_profile

REPO = Path(__file__).resolve().parent.parent


def bedford_profile(as_of="2026-06-01"):
    pull = json.loads((REPO / "data" / "cache" / "2625-bedford-ave-brooklyn.json").read_text())
    return build_profile.build_profile(pull, as_of=as_of)


def tiny_model() -> dict:
    """One stump on pre1940_attached, so the arithmetic is checkable by hand."""
    i = features.FEATURES.index("pre1940_attached")
    tree = {"feature": [i, -2, -2], "threshold": [0.5, -2.0, -2.0], "left": [1, -1, -1], "right": [2, -1, -1],
            "expected": [0.2, -0.5, 1.0]}
    return {"model_version": "test", "features": features.FEATURES, "init_raw": -1.0, "learning_rate": 0.5,
            "trees": [tree], "calibration": {"method": "platt", "a": 1.0, "b": 0.0},
            "reference_scores": [{"score": s / 10, "similar": s % 2 == 0} for s in range(10)]}


class Explanations(unittest.TestCase):
    def test_contributions_add_up_to_the_raw_score(self):
        model = tiny_model()
        f = features.features_from_profile(bedford_profile())
        raw, bias, contrib = score.explain(model, f)
        self.assertAlmostEqual(raw, bias + sum(contrib.values()))
        self.assertAlmostEqual(bias, -1.0 + 0.5 * 0.2)
        self.assertAlmostEqual(contrib["pre1940_attached"], 0.5 * (1.0 - 0.2))
        self.assertAlmostEqual(score.calibrated(model, raw), 1 / (1 + math.exp(-raw)))

    def test_pattern_score_contract_and_wording(self):
        result = score.pattern_score(bedford_profile(), model=tiny_model())
        PatternScore.model_validate(result)
        self.assertIn("not a prediction", result["calibration_note"])
        self.assertIn("before 1940", result["compared_with"])
        self.assertEqual(result["top_factors"][0]["feature"], "attached neighbors built before 1940")

    def test_features_use_only_records_before_as_of(self):
        early = features.features_from_profile(bedford_profile("2020-01-01"))
        self.assertEqual(early["prior_structural_complaints"], 0)
        later = features.features_from_profile(bedford_profile("2021-06-01"))
        self.assertGreater(later["prior_structural_complaints"], 0)

    def test_feature_list_matches_training_rows(self):
        self.assertEqual(set(features.FEATURES), set(features.features_from_profile(bedford_profile())))


class ServedModel(unittest.TestCase):
    def setUp(self):
        if not score.MODEL_PATH.exists():
            self.skipTest("model not trained")

    def test_artifact_scores_bedford(self):
        result = score.pattern_score(bedford_profile())
        PatternScore.model_validate(result)
        self.assertTrue(0 <= result["score"] <= 1)
        self.assertTrue(result["top_factors"])

    def test_model_card_is_honest(self):
        card = (score.MODEL_PATH.parent / "MODEL_CARD.md").read_text()
        self.assertIn("does not predict", card)
        self.assertIn("Limitations", card)

    def test_route(self):
        response = TestClient(app).get("/api/sites/3052110074/pattern")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.headers.get("X-ForeSite-Fixture"))


class Sequences(unittest.TestCase):
    ROWS = [
        {"filing_date": "2022-01-01", "label": 1, "first_outcome": "2022-05-01", "sequence": [
            {"date": "2022-02-01", "kind": "complaint_03", "where": "touching"},
            {"date": "2022-05-01", "kind": "complaint_30", "where": "touching"}]},
        {"filing_date": "2022-01-01", "label": 0, "first_outcome": None, "sequence": [
            {"date": "2022-03-01", "kind": "complaint_54", "where": "site"}]},
    ]

    def test_outcome_is_never_part_of_its_own_pattern(self):
        tokens = [t for _, t in sequences.tokens(self.ROWS[0])]
        self.assertEqual(tokens, ["filing", "complaint_03@touching"])

    def test_lift(self):
        result = sequences.mine(self.ROWS, min_support=1)
        by = {tuple(p["pattern"]): p for p in result["patterns"]}
        self.assertEqual(by[("filing", "complaint_03@touching")]["lift"], 2.0)
        self.assertEqual(by[("complaint_54@site",)]["outcome_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
