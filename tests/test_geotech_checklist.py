"""A confirmed geotechnical report reading turns into checklist items for the roles it concerns
(model_input/geotech.py, actions/from_model.geotech_actions, /geotech and /geotech/confirm). Offline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from actions.from_model import evaluate_geotech, geotech_actions
from api.contracts import ActionItem
from api.main import app
from api.routers.projects_router import project_store
from api.store.project_store import ProjectStore
from model_input import drawing, geotech

BBL = "3052110074"
WET = {"groundwater_depth_ft": 11.0, "soil_description": "6 ft of fill over medium dense fine sand",
       "allowable_bearing_tsf": 2.5, "rock_depth_ft": None, "boring_count": 3, "max_boring_depth_ft": 40.0,
       "confidence": 0.7}
DRY = {**WET, "groundwater_depth_ft": 32.0, "soil_description": "dense sand and gravel", "allowable_bearing_tsf": 4.0}
TEAM = [{"name": "A", "role": "architect"}, {"name": "S", "role": "structural_engineer"},
        {"name": "C", "role": "contractor"}, {"name": "D", "role": "developer"}]


class FakeClient:
    def __init__(self, answer):
        text = SimpleNamespace(type="text", text=json.dumps(answer))
        self.response = SimpleNamespace(stop_reason="end_turn", content=[text])
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **request: self.response))


class GeotechRules(unittest.TestCase):
    def test_shallow_groundwater_reaches_contractor_and_architect(self):
        items = {i["id"]: i for i in geotech_actions(WET, "G-1 Geotech Report.pdf", "developer")}
        self.assertEqual(items["action-geotech-dewatering"]["owner_role"], "contractor")
        self.assertEqual(items["action-geotech-waterproofing"]["owner_role"], "architect")
        self.assertEqual(items["action-code-monitoring"]["owner_role"], "contractor")
        self.assertIn("groundwater at 11 ft below grade", items["action-geotech-dewatering"]["added_reason"])
        self.assertTrue(items["action-geotech-dewatering"]["added_reason"].startswith("Added because the developer uploaded"))

    def test_weak_soil_and_fill_reach_the_engineer(self):
        items = {i["id"]: i for i in geotech_actions(WET, "G-1.pdf", "developer")}
        self.assertEqual(items["action-geotech-bearing"]["owner_role"], "structural_engineer")
        self.assertEqual(items["action-geotech-fill"]["owner_role"], "structural_engineer")
        self.assertEqual(items["action-code-support_basis"]["owner_role"], "structural_engineer")

    def test_good_ground_only_flags_the_support_basis(self):
        ids = {i["id"] for i in geotech_actions(DRY, "G-1.pdf", "developer")}
        self.assertEqual(ids, {"action-code-support_basis"})

    def test_null_findings_never_apply(self):
        blank = {k: None for k in WET} | {"confidence": 0.5}
        self.assertEqual({i["id"] for i in geotech_actions(blank, "G.pdf", "architect")}, {"action-code-support_basis"})

    def test_shallow_rock(self):
        self.assertIsNotNone(evaluate_geotech("rock_within_20ft", {**DRY, "rock_depth_ft": 18}))
        self.assertIsNone(evaluate_geotech("rock_within_20ft", {**DRY, "rock_depth_ft": 30}))

    def test_items_fit_the_contract_and_are_open(self):
        for item in geotech_actions(WET, "G-1.pdf", "developer"):
            self.assertEqual(item["status"], "open")
            ActionItem.model_validate({k: v for k, v in item.items() if k != "flagged_reason"})

    def test_unknown_condition(self):
        with self.assertRaises(ValueError):
            evaluate_geotech("nope", WET)


class Reader(unittest.TestCase):
    def test_answer_is_capped_and_checked(self):
        findings, evidence = geotech.read_geotech(b"%PDF-1.7", client=FakeClient({**WET, "confidence": 0.95,
                                                                                  "evidence": "Table 1, B-1 to B-3."}))
        self.assertEqual(findings["confidence"], 0.7)
        self.assertEqual(findings["groundwater_depth_ft"], 11.0)
        self.assertEqual(evidence, "Table 1, B-1 to B-3.")

    def test_not_a_pdf(self):
        with self.assertRaises(ValueError):
            geotech.read_geotech(b"hello", client=FakeClient(WET))


class Routes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.projects = ProjectStore(Path(self.tmp.name) / "projects.sqlite")
        app.dependency_overrides[project_store] = lambda: self.projects
        self.client = TestClient(app)
        self.pid = self.client.post("/api/projects", json={"name": "T", "site_bbl": BBL, "stage": "pre_filing",
                                                            "members": TEAM}).json()["id"]

    def tearDown(self):
        app.dependency_overrides.pop(project_store, None)
        self.tmp.cleanup()

    def test_confirm_updates_other_roles(self):
        response = self.client.post(f"/api/projects/{self.pid}/geotech/confirm",
                                    json={"findings": WET, "by_role": "developer", "document": "G-1 Geotech Report.pdf"})
        self.assertEqual(response.status_code, 200, response.text)
        project = self.client.get(f"/api/projects/{self.pid}").json()
        contractor = {i["title"] for i in project["items"] if i["owner_role"] == "contractor"}
        self.assertEqual(contractor, {"Plan dewatering for the excavation", "Monitor nearby buildings"})
        pin = project["pins"][0]
        self.assertEqual((pin["ref_id"], pin["by_role"]), ("geotech", "developer"))
        self.assertIn("Groundwater: 11 ft", pin["body"])
        self.assertIsNone(project["structural_model"], "a report is not a structural model")

    def test_read_saves_nothing_and_says_when_unavailable(self):
        original = geotech.read_geotech
        geotech.read_geotech = lambda pdf: (WET, "note")
        try:
            ok = self.client.post(f"/api/projects/{self.pid}/geotech", content=b"%PDF-1.7",
                                  headers={"Content-Type": "application/pdf"})
            geotech.read_geotech = lambda pdf: (_ for _ in ()).throw(drawing.DrawingUnavailable("no key"))
            down = self.client.post(f"/api/projects/{self.pid}/geotech", content=b"%PDF-1.7",
                                    headers={"Content-Type": "application/pdf"})
        finally:
            geotech.read_geotech = original
        self.assertEqual(ok.json()["findings"]["groundwater_depth_ft"], 11.0)
        self.assertEqual(self.client.get(f"/api/projects/{self.pid}").json()["items"], [])
        self.assertEqual(down.status_code, 503)
        self.assertIn("Couldn't read the report", down.json()["detail"])


if __name__ == "__main__":
    unittest.main()
