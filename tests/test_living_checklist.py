"""The living checklist: a confirmed drawing reading turns into checklist items for the roles it concerns,
each saying who added it and why (actions/from_model.py, ProjectStore.record_items, /model/confirm)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from actions.from_model import document_label, evaluate, model_actions
from api.contracts import ActionItem, Project
from api.main import app
from api.routers.projects_router import project_store
from api.store.project_store import ProjectStore, ProjectStoreError
from model_input import store as model_store

BBL = "3052110074"
WALLED = {"source": "drawing", "material": "unreinforced brick masonry", "gravity_system": "wood joists",
          "lateral_system": None, "foundation_type": "brick spread footing",
          "bearing_walls_on_lot_line": [{"id": "drawing-wall-1", "side": "north", "material": "brick", "length_ft": 90.0}],
          "levels": 3, "confidence": 0.7}
PLAIN = {**WALLED, "material": "steel frame", "lateral_system": "braced frames",
         "bearing_walls_on_lot_line": []}
TEAM = [{"name": "A", "role": "architect"}, {"name": "S", "role": "structural_engineer"}]


def _ids(items):
    return {i["id"] for i in items}


class ModelRules(unittest.TestCase):
    def test_lot_line_walls_reach_the_engineer_and_the_architect(self):
        items = {i["id"]: i for i in model_actions(WALLED, "S-101.pdf", "structural_engineer")}
        self.assertEqual(items["action-code-underpinning"]["owner_role"], "structural_engineer")
        self.assertEqual(items["action-code-underpinning"]["title"], "Underpin or support the adjoining buildings")
        self.assertEqual(items["action-code-notice"]["owner_role"], "architect")
        self.assertEqual(items["action-code-notice"]["title"], "Notify the adjoining owner")
        self.assertIn("action-model-lot-line-walls", items)

    def test_every_item_says_who_and_why(self):
        for item in model_actions(WALLED, "S-101.pdf", "structural_engineer"):
            self.assertTrue(item["added_reason"].startswith("Added because the structural engineer uploaded S-101"), item)
            self.assertEqual(item["status"], "open", "a drawing never marks work done")
            ActionItem.model_validate({k: v for k, v in item.items() if k != "flagged_reason"})
            self.assertTrue(item["flagged_reason"].startswith("Flagged because the structural engineer"))

    def test_reason_names_the_finding(self):
        notice = next(i for i in model_actions(WALLED, "S-101.pdf", "architect") if i["id"] == "action-code-notice")
        self.assertIn("bearing wall on the lot line (north, brick, 90 ft)", notice["added_reason"])
        self.assertIn("the architect uploaded", notice["added_reason"])

    def test_unknowns_become_items_to_establish(self):
        ids = _ids(model_actions({**PLAIN, "lateral_system": None, "foundation_type": " "}, "S-1.pdf", "architect"))
        self.assertEqual(ids, {"action-model-lateral-unknown", "action-model-foundation-unknown"})

    def test_a_model_with_nothing_to_flag_adds_nothing(self):
        self.assertEqual(model_actions(PLAIN, "S-1.pdf", "structural_engineer"), [])

    def test_unreinforced_masonry(self):
        self.assertIsNotNone(evaluate("unreinforced_masonry", WALLED))
        self.assertIsNone(evaluate("unreinforced_masonry", {**WALLED, "material": "reinforced concrete"}))

    def test_unknown_condition_and_role_are_refused(self):
        with self.assertRaises(ValueError):
            evaluate("nope", WALLED)
        with self.assertRaises(ValueError):
            model_actions(WALLED, "S-101.pdf", "inspector")

    def test_document_label(self):
        self.assertEqual(document_label("S-101.PDF"), "S-101")
        self.assertEqual(document_label("plans/A-1"), "A-1")


class StoreProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name) / "p.sqlite")
        self.pid = self.store.create_project("T", BBL, "pre_filing", TEAM)["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def item(self, id_, owner="structural_engineer", **extra):
        return {"id": id_, "discipline": "structural", "hazard": "structural", "title": "t", "why": "w",
                "status": "open", "owner_role": owner, "source_rule": "r", "life_safety": False, **extra}

    def test_drafted_items_carry_no_provenance(self):
        sent = self.item("a", added_by_role="architect", added_reason="sneaky", added_at="2020-01-01")
        project = self.store.add_items(self.pid, [sent])
        item = project["items"][0]
        self.assertEqual((item["added_by_role"], item["added_reason"], item["added_at"]), (None, None, None))
        Project.model_validate(project)

    def test_new_items_record_who_why_and_when(self):
        project = self.store.record_items(self.pid, [self.item("b", added_reason="Added because X")], "structural_engineer")
        item = project["items"][0]
        self.assertEqual(item["added_by_role"], "structural_engineer")
        self.assertEqual(item["added_reason"], "Added because X")
        self.assertRegex(item["added_at"], r"^\d{4}-\d\d-\d\dT")
        Project.model_validate(project)

    def test_an_existing_item_keeps_status_and_owner_but_is_flagged(self):
        self.store.add_items(self.pid, [self.item("c", owner="architect")])
        self.store.update_items(self.pid, [{"id": "c", "status": "done"}])
        project = self.store.record_items(self.pid, [self.item("c", added_reason="Added", flagged_reason="Flagged")],
                                          "structural_engineer")
        self.assertEqual(len(project["items"]), 1)
        item = project["items"][0]
        self.assertEqual((item["status"], item["owner_role"], item["added_reason"]), ("done", "architect", "Flagged"))
        self.assertNotIn("flagged_reason", item)

    def test_an_unassigned_existing_item_takes_the_rule_owner(self):
        self.store.add_items(self.pid, [self.item("d", owner=None)])
        project = self.store.record_items(self.pid, [self.item("d", added_reason="r")], "architect")
        self.assertEqual(project["items"][0]["owner_role"], "structural_engineer")

    def test_owner_without_a_member_is_left_unassigned(self):
        project = self.store.record_items(self.pid, [self.item("e", owner="contractor", added_reason="r")], "architect")
        self.assertIsNone(project["items"][0]["owner_role"])

    def test_refuses_a_role_off_the_project_and_a_missing_reason(self):
        with self.assertRaises(ProjectStoreError):
            self.store.record_items(self.pid, [self.item("f", added_reason="r")], "contractor")
        with self.assertRaises(ProjectStoreError):
            self.store.record_items(self.pid, [self.item("f")], "architect")
        self.assertEqual(self.store.get_project(self.pid)["items"], [])

    def test_bumps_the_version_once(self):
        before = self.store.version(self.pid)
        self.store.record_items(self.pid, [self.item("g", added_reason="r"), self.item("h", added_reason="r")], "architect")
        self.assertEqual(self.store.version(self.pid), before + 1)

    def test_an_older_store_file_gets_the_columns(self):
        import sqlite3
        path = Path(self.tmp.name) / "old.sqlite"
        with sqlite3.connect(path) as db:
            db.executescript("CREATE TABLE items (project_id TEXT, id TEXT, position INTEGER, discipline TEXT, hazard TEXT,"
                             " title TEXT, why TEXT, code_ref TEXT, proof_needed TEXT, status TEXT, owner_role TEXT,"
                             " source_rule TEXT, life_safety INTEGER, updated_at TEXT);")
        ProjectStore(path)
        with sqlite3.connect(path) as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(items)")}
        self.assertTrue({"added_by_role", "added_reason", "added_at"} <= columns)


class ConfirmRoute(unittest.TestCase):
    def setUp(self):
        model_store.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.projects = ProjectStore(Path(self.tmp.name) / "projects.sqlite")
        app.dependency_overrides[project_store] = lambda: self.projects
        self.client = TestClient(app)
        self.pid = self.client.post("/api/projects", json={"name": "T", "site_bbl": BBL, "stage": "pre_filing",
                                                            "members": TEAM}).json()["id"]

    def tearDown(self):
        model_store.clear()
        app.dependency_overrides.pop(project_store, None)
        self.tmp.cleanup()

    def confirm(self, **body):
        payload = {"model": WALLED, "by_role": "structural_engineer", "document": "S-101.pdf", **body}
        return self.client.post(f"/api/projects/{self.pid}/model/confirm", json=payload)

    def test_confirm_updates_the_other_roles_checklist(self):
        response = self.confirm(evidence="S-101 notes")
        self.assertEqual(response.status_code, 200, response.text)
        # What the architect's tab gets on its next poll.
        project = self.client.get(f"/api/projects/{self.pid}").json()
        mine = [i for i in project["items"] if i["owner_role"] == "architect"]
        self.assertEqual([i["title"] for i in mine], ["Notify the adjoining owner"])
        self.assertIn("structural engineer uploaded S-101", mine[0]["added_reason"])
        self.assertEqual(mine[0]["added_by_role"], "structural_engineer")
        self.assertEqual(project["structural_model"]["material"], "unreinforced brick masonry")
        pin = next(p for p in project["pins"] if p["kind"] == "document")
        self.assertEqual((pin["ref_id"], pin["title"], pin["by_role"]), ("structural", "S-101.pdf", "structural_engineer"))
        self.assertIsNotNone(model_store.for_site(BBL))

    def test_an_item_the_project_had_says_flagged(self):
        notice = {"id": "action-code-notice", "discipline": "architect", "hazard": "structural", "title": "Notify",
                  "why": "w", "status": "open", "owner_role": "architect", "source_rule": "checklist:notice", "life_safety": False}
        self.client.post(f"/api/projects/{self.pid}/items", json=[notice])
        items = {i["id"]: i for i in self.confirm().json()["items"]}
        self.assertTrue(items["action-code-notice"]["added_reason"].startswith("Flagged because the structural engineer"))
        self.assertEqual(items["action-code-notice"]["title"], "Notify", "a flag keeps the team's item as it was")
        self.assertTrue(items["action-model-lot-line-walls"]["added_reason"].startswith("Added because"))

    def test_contractor_item_without_a_contractor_is_unassigned(self):
        project = self.confirm().json()
        exam = next(i for i in project["items"] if i["id"] == "action-code-examination")
        self.assertIsNone(exam["owner_role"])

    def test_a_role_off_the_project_cannot_confirm(self):
        response = self.confirm(by_role="developer")
        self.assertEqual(response.status_code, 422)
        project = self.client.get(f"/api/projects/{self.pid}").json()
        self.assertEqual((project["items"], project["structural_model"], project["pins"]), ([], None, []))

    def test_unknown_project(self):
        response = self.client.post("/api/projects/0123456789abcdef/model/confirm",
                                    json={"model": WALLED, "by_role": "architect", "document": "S.pdf"})
        self.assertEqual(response.status_code, 404)

    def test_the_drawing_route_saves_nothing(self):
        from model_input import drawing
        original = drawing.read_drawing
        drawing.read_drawing = lambda pdf: (WALLED, "S-101 notes")
        try:
            response = self.client.post(f"/api/projects/{self.pid}/model/drawing", content=b"%PDF-1.7",
                                        headers={"Content-Type": "application/pdf"})
        finally:
            drawing.read_drawing = original
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["model"]["material"], "unreinforced brick masonry")
        self.assertIsNone(model_store.for_project(self.pid))
        self.assertEqual(self.client.get(f"/api/projects/{self.pid}").json()["items"], [])

    def test_confirm_is_in_the_published_api(self):
        self.assertIn("/api/projects/{project_id}/model/confirm", json.loads(json.dumps(app.openapi()))["paths"])


if __name__ == "__main__":
    unittest.main()
