"""The SQLite project store: two roles on one project, the role fence, closed sets, caps. Temp files only."""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from api.store import project_store_schema as schema
from api.store.project_store import UNCHANGED, NotFound, ProjectStore, ProjectStoreError

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"
BBL = "3052110074"
BOTH = [{"name": "Architect", "role": "architect"}, {"name": "Structural engineer", "role": "structural_engineer"}]


def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


class ProjectStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name) / "projects.sqlite")
        self.project_id = self.store.create_project("Bedford excavation", BBL, "design", BOTH)["id"]
        self.items = fixture("actions")

    def tearDown(self):
        self.tmp.cleanup()


class TwoRolesOnOneProjectTests(ProjectStoreTestCase):
    def test_each_role_sees_the_others_writes_and_the_version_moves(self):
        start = self.store.version(self.project_id)
        self.store.add_items(self.project_id, self.items)
        self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": "in_progress"}])
        self.store.add_note(self.project_id, "structural_engineer", "Survey booked for Tuesday.")
        self.store.add_pin(self.project_id, "case", "case-714-39th-2018", "A similar excavation", "architect")
        project, version = self.store.snapshot(self.project_id)
        self.assertEqual([m["role"] for m in project["members"]], ["architect", "structural_engineer"])
        self.assertEqual([i["id"] for i in project["items"]], [i["id"] for i in self.items])
        self.assertEqual(project["items"][0]["status"], "in_progress")
        self.assertEqual(project["notes"][0]["author_role"], "structural_engineer")
        self.assertEqual(project["pins"][0]["by_role"], "architect")
        self.assertEqual(version, start + 4)

    def test_an_item_added_again_keeps_its_status_and_owner(self):
        self.store.add_items(self.project_id, self.items)
        self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": "done", "owner_role": "architect"}])
        version = self.store.version(self.project_id)
        project = self.store.add_items(self.project_id, self.items)
        self.assertEqual((project["items"][0]["status"], project["items"][0]["owner_role"]), ("done", "architect"))
        self.assertEqual(len(project["items"]), len(self.items))
        self.assertEqual(self.store.version(self.project_id), version, "nothing new, so nothing for the other tab to fetch")

    def test_owner_role_null_unassigns_and_left_out_stays(self):
        self.store.add_items(self.project_id, self.items)
        kept = self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": "done", "owner_role": UNCHANGED}])
        self.assertEqual(kept["items"][0]["owner_role"], "structural_engineer")
        cleared = self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": None, "owner_role": None}])
        self.assertEqual((cleared["items"][0]["status"], cleared["items"][0]["owner_role"]), ("done", None))
        with self.assertRaises(ProjectStoreError):
            self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": None, "owner_role": UNCHANGED}])

    def test_an_update_list_is_all_or_nothing(self):
        self.store.add_items(self.project_id, self.items)
        with self.assertRaises(NotFound):
            self.store.update_items(self.project_id, [{"id": "act-bc-3309-4", "status": "done"},
                                                      {"id": "not-on-this-project", "status": "done"}])
        self.assertEqual(self.store.get_project(self.project_id)["items"][0]["status"], "open")

    def test_the_model_is_kept_and_replaced_whole(self):
        model = fixture("structural_model")
        self.assertEqual(self.store.set_structural_model(self.project_id, model)["structural_model"], model)
        self.assertEqual(self.store.set_structural_model(self.project_id, {**model, "levels": 9})["structural_model"]["levels"], 9)


class RoleFenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name) / "projects.sqlite")
        self.solo = self.store.create_project("Architect only", BBL, "design", BOTH[:1])["id"]

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_role_the_project_has_no_member_for_cannot_write_or_own(self):
        item = {**fixture("actions")[0], "owner_role": None}
        self.store.add_items(self.solo, [item])
        for write in (
            lambda: self.store.add_note(self.solo, "structural_engineer", "not on this project"),
            lambda: self.store.add_pin(self.solo, "case", "c", "t", "structural_engineer"),
            lambda: self.store.update_items(self.solo, [{"id": item["id"], "owner_role": "structural_engineer"}]),
            lambda: self.store.add_items(self.solo, [{**item, "id": "other", "owner_role": "structural_engineer"}]),
        ):
            with self.assertRaises(ProjectStoreError):
                write()

    def test_items_belong_to_their_own_project(self):
        other = self.store.create_project("Other site", "1000010001", "design", BOTH)["id"]
        self.store.add_items(other, fixture("actions"))
        with self.assertRaises(NotFound):
            self.store.update_items(self.solo, [{"id": "act-bc-3309-4", "status": "done"}])

    def test_unknown_or_malformed_project_ids_are_not_found(self):
        for bad in ("", "../etc", "0" * 15, "Z" * 16, None, 7, "0123456789abcdef", "proj-sample"):
            with self.assertRaises(NotFound):
                self.store.get_project(bad)


class ClosedSetTests(ProjectStoreTestCase):
    def test_values_outside_the_contract_sets_are_refused(self):
        item = self.items[0]
        for write in (
            lambda: self.store.create_project("P", BBL, "demolition", BOTH),
            lambda: self.store.create_project("P", BBL, "design", [{"name": "X", "role": "owner"}]),
            lambda: self.store.create_project("P", BBL, "design", []),
            lambda: self.store.create_project("P", "305211007", "design", BOTH),
            lambda: self.store.create_project("P", "6052110074", "design", BOTH),
            lambda: self.store.add_items(self.project_id, [{**item, "status": "verified"}]),
            lambda: self.store.add_items(self.project_id, [{**item, "hazard": "rumor"}]),
            lambda: self.store.add_items(self.project_id, [{**item, "discipline": "owner"}]),
            lambda: self.store.add_items(self.project_id, [{**item, "life_safety": "yes"}]),
            lambda: self.store.add_pin(self.project_id, "verdict", "r", "t", "architect"),
            lambda: self.store.add_note(self.project_id, "contractor", "x"),
        ):
            with self.assertRaises(ProjectStoreError):
                write()

    def test_the_database_itself_refuses_a_value_outside_a_closed_set(self):
        with closing(sqlite3.connect(self.store.db_path)) as db, self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO items (project_id, id, position, discipline, hazard, title, why, status, source_rule,"
                       " life_safety, updated_at) VALUES (?, 'a', 0, 'structural', 'structural', 't', 'w', 'verified',"
                       " 'r', 1, 'x')", (self.project_id,))

    def test_injection_text_is_stored_as_text(self):
        hostile = "x'); DROP TABLE projects; --"
        self.store.add_note(self.project_id, "architect", hostile)
        self.assertEqual(self.store.get_project(self.project_id)["notes"][0]["text"], hostile)


class CapTests(ProjectStoreTestCase):
    def test_over_a_cap_is_refused_not_cut(self):
        with self.assertRaises(ProjectStoreError):
            self.store.add_note(self.project_id, "architect", "x" * (schema.MAX_TEXT["note"] + 1))
        model = {**fixture("structural_model"), "material": "x" * schema.MAX_MODEL_BYTES}
        with self.assertRaises(ProjectStoreError):
            self.store.set_structural_model(self.project_id, model)
        self.assertEqual(self.store.get_project(self.project_id)["notes"], [])

    def test_a_project_stops_at_its_row_limit(self):
        with mock.patch.dict(schema.MAX_ROWS_PER_PROJECT, {"notes": 2, "items": 2}):
            self.store.add_note(self.project_id, "architect", "one")
            self.store.add_note(self.project_id, "architect", "two")
            with self.assertRaises(ProjectStoreError):
                self.store.add_note(self.project_id, "architect", "three")
            with self.assertRaises(ProjectStoreError):
                self.store.add_items(self.project_id, self.items)
            self.assertEqual(self.store.get_project(self.project_id)["items"], [], "a refused batch adds none of it")


ALL_FOUR = BOTH + [{"name": "Developer", "role": "developer"}, {"name": "Contractor", "role": "contractor"}]


class ProjectSetupTests(ProjectStoreTestCase):
    def test_project_keeps_work_type_construction_and_scope(self):
        pid = self.store.create_project("Setup", BBL, "pre_filing", BOTH, job_type="alteration",
                                        construction_type="masonry", work_types=["structural", "facade"])["id"]
        project = self.store.get_project(pid)
        self.assertEqual(project["job_type"], "alteration")
        self.assertEqual(project["construction_type"], "masonry")
        self.assertEqual(project["work_types"], ["structural", "facade"])

    def test_old_projects_read_with_empty_setup(self):
        project = self.store.get_project(self.project_id)
        self.assertIsNone(project["job_type"])
        self.assertIsNone(project["construction_type"])
        self.assertEqual(project["work_types"], [])

    def test_developer_and_contractor_can_be_members_and_own_items(self):
        pid = self.store.create_project("Four", BBL, "design", ALL_FOUR)["id"]
        self.store.add_items(pid, self.items)
        item_id = self.items[0]["id"]
        self.store.update_items(pid, [{"id": item_id, "owner_role": "contractor"}])
        self.store.add_pin(pid, "document", "survey", "survey.pdf", "developer")
        project = self.store.get_project(pid)
        self.assertEqual(next(i for i in project["items"] if i["id"] == item_id)["owner_role"], "contractor")
        self.assertEqual(project["pins"][0]["kind"], "document")
        self.assertEqual(project["pins"][0]["by_role"], "developer")

    def test_unknown_construction_type_and_work_type_are_refused(self):
        with self.assertRaises(ProjectStoreError):
            self.store.create_project("Bad", BBL, "design", BOTH, construction_type="adobe")
        with self.assertRaises(ProjectStoreError):
            self.store.create_project("Bad", BBL, "design", BOTH, work_types=["digging"])


if __name__ == "__main__":
    unittest.main()
