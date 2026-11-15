"""The contracts every module builds against: fixtures, schemas and the stub API agree."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from api import contracts
from api.main import app
from api.stubs import FIXTURE_HEADER
from contracts.generate import schema_files

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "contracts" / "fixtures"
SCHEMAS = ROOT / "contracts" / "schemas"


def load(path: Path):
    return json.loads(path.read_text())


class FixturesMatchContracts(unittest.TestCase):
    def test_every_contract_has_a_fixture_and_a_schema(self):
        for name in contracts.FIXTURES:
            self.assertTrue((FIXTURES / f"{name}.json").exists(), name)
            self.assertTrue((SCHEMAS / f"{name}.schema.json").exists(), name)

    def test_fixtures_validate_against_the_models(self):
        for name, (model, is_list) in contracts.FIXTURES.items():
            data = load(FIXTURES / f"{name}.json")
            with self.subTest(name=name):
                if is_list:
                    self.assertIsInstance(data, list)
                    self.assertTrue(data, f"{name} fixture is empty")
                    for item in data:
                        model.model_validate(item)
                else:
                    model.model_validate(data)

    def test_fixtures_validate_against_the_json_schemas(self):
        for name in contracts.FIXTURES:
            schema = load(SCHEMAS / f"{name}.schema.json")
            errors = list(Draft202012Validator(schema).iter_errors(load(FIXTURES / f"{name}.json")))
            self.assertEqual(errors, [], name)

    def test_generated_files_are_up_to_date(self):
        for path, expected in schema_files().items():
            with self.subTest(path=path.name):
                self.assertEqual(path.read_text(), expected, "run: .venv/bin/python -m contracts.generate")

    def test_cases_carry_sources_and_never_blame_without_a_report(self):
        for case in load(FIXTURES / "cases.json"):
            self.assertTrue(case["sources"])
            if case["cause_status"] != "reported":
                self.assertIsNone(case["cause_as_reported"], case["id"])


class StubApiServesEveryRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def assert_sample(self, response):
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers.get(FIXTURE_HEADER), "true")

    def test_get_routes(self):
        bbl = "3052110074"
        for path in [
            "/api/layers",
            "/api/layers/construction_incidents",
            "/api/search?q=2625%20Bedford",
            f"/api/sites/{bbl}/warnings",
            f"/api/sites/{bbl}/pattern",
            f"/api/sites/{bbl}/actions",
            "/api/cases",
            "/api/cases/case-714-39th-2018",
            "/api/projects/proj-sample",
        ]:
            with self.subTest(path=path):
                self.assert_sample(self.client.get(path))

    def test_unknown_layer_and_case_are_404(self):
        self.assertEqual(self.client.get("/api/layers/nope").status_code, 404)
        self.assertEqual(self.client.get("/api/cases/nope").status_code, 404)

    def test_write_routes(self):
        project = {"name": "Test", "site_bbl": "3052110074", "stage": "design", "members": [{"name": "A", "role": "architect"}]}
        created = self.client.post("/api/projects", json=project)
        self.assert_sample(created)
        self.assertEqual(created.json()["name"], "Test")
        pid = "proj-sample"
        self.assert_sample(self.client.post(f"/api/projects/{pid}/notes", json={"author_role": "architect", "text": "hi"}))
        self.assert_sample(self.client.post(f"/api/projects/{pid}/pins", json={"kind": "case", "ref_id": "c", "title": "t", "by_role": "architect"}))
        self.assert_sample(self.client.patch(f"/api/projects/{pid}/items", json=[{"id": "act-bc-3309-4", "status": "done"}]))
        self.assert_sample(self.client.post(f"/api/projects/{pid}/model", json=load(FIXTURES / "structural_model.json")))
        self.assert_sample(self.client.post("/api/chat", json={"question": "What should I check?", "bbl": "3052110074"}))

    def test_bad_input_is_rejected(self):
        response = self.client.post("/api/projects", json={"name": "x", "site_bbl": "1", "stage": "someday", "members": []})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
