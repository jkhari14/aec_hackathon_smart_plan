"""Model input (PR 13): the Revit reader's JSON, a drawing read by Claude (faked here), and the effect on the
site profile and similar cases. Offline: no key and no network."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.contracts import StructuralModel
from api.main import app
from model_input import drawing, store
from model_input.revit import ModelInputError, read_revit

REPO = Path(__file__).resolve().parent.parent
FIXTURE = json.loads((REPO / "contracts" / "fixtures" / "structural_model.json").read_text())
PDF = b"%PDF-1.7\n% test drawing\n"

ANSWER = {"material": "unreinforced brick masonry", "gravity_system": "wood joists on masonry bearing walls",
          "lateral_system": None, "foundation_type": "brick spread footing",
          "bearing_walls_on_lot_line": [{"side": "north", "material": "brick", "length_ft": 90.0}],
          "levels": 3, "confidence": 0.95, "evidence": "S-101 general notes."}


class FakeClient:
    """Stands in for anthropic.Anthropic(): records the request and returns a canned answer."""

    def __init__(self, answer=ANSWER, stop_reason="end_turn"):
        self.requests = []
        text = SimpleNamespace(type="text", text=json.dumps(answer))
        self.response = SimpleNamespace(stop_reason=stop_reason, content=[text])
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **request):
        self.requests.append(request)
        return self.response


class Revit(unittest.TestCase):
    def test_fixture_reads(self):
        model = read_revit(FIXTURE)
        StructuralModel.model_validate(model)
        self.assertEqual(model["bearing_walls_on_lot_line"][0]["side"], "north")

    def test_wrapped_and_short_sides(self):
        model = read_revit({"structural_model": {**FIXTURE, "bearing_walls_on_lot_line": [{"side": "E"}]}})
        self.assertEqual(model["bearing_walls_on_lot_line"][0], {"id": "wall-1", "side": "east", "material": None,
                                                                "length_ft": None})

    def test_bad_input_is_rejected(self):
        with self.assertRaises(ModelInputError):
            read_revit(["not", "an", "object"])
        with self.assertRaises(ModelInputError):
            read_revit({**FIXTURE, "confidence": 3})


class Drawing(unittest.TestCase):
    def test_request_and_answer(self):
        client = FakeClient()
        model, evidence = drawing.read_drawing(PDF, client=client)
        request = client.requests[0]
        self.assertEqual(request["model"], "claude-opus-5-5")
        self.assertEqual(request["messages"][0]["content"][0]["type"], "document")
        self.assertEqual(request["output_config"]["format"]["type"], "json_schema")
        self.assertEqual(model["source"], "drawing")
        self.assertEqual(model["confidence"], drawing.MAX_CONFIDENCE, "AI-read drawings are capped below Revit")
        self.assertEqual(evidence, "S-101 general notes.")

    def test_refusal_is_an_error_not_a_guess(self):
        with self.assertRaises(drawing.DrawingUnavailable):
            drawing.read_drawing(PDF, client=FakeClient(stop_reason="refusal"))

    def test_not_a_pdf(self):
        with self.assertRaises(ValueError):
            drawing.read_drawing(b"hello", client=FakeClient())


class Routes(unittest.TestCase):
    def setUp(self):
        store.clear()
        self.client = TestClient(app)

    def tearDown(self):
        store.clear()

    def test_revit_upload_feeds_profile_and_similarity(self):
        before = self.client.get("/api/sites/3052110074/similar").json()
        response = self.client.post("/api/projects/proj-sample/model", json=FIXTURE)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["structural_model"]["material"], "unreinforced brick masonry")
        profile = self.client.get("/api/sites/3052110074/profile").json()
        self.assertEqual(profile["structural_model"]["source"], "revit")
        after = self.client.get("/api/sites/3052110074/similar").json()
        matched = " ".join(m for r in after["results"] for m in r["matched_on"])
        self.assertIn("construction: masonry", matched)
        self.assertNotIn("construction: masonry", " ".join(m for r in before["results"] for m in r["matched_on"]))

    def test_drawing_without_credentials_says_so(self):
        original = drawing._client
        drawing._client = lambda: (_ for _ in ()).throw(drawing.DrawingUnavailable("no key"))
        try:
            response = self.client.post("/api/projects/proj-sample/model/drawing", content=PDF,
                                        headers={"Content-Type": "application/pdf"})
        finally:
            drawing._client = original
        self.assertEqual(response.status_code, 503)
        self.assertIn("Couldn't read the drawing", response.json()["detail"])

    def test_drawing_route_is_not_in_the_schema(self):
        self.assertNotIn("/api/projects/{project_id}/model/drawing", app.openapi()["paths"])


if __name__ == "__main__":
    unittest.main()
