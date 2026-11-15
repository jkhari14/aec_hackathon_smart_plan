"""A pinned chat answer keeps its text: stored as sent, capped, and added to a store file made before the column."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.routers.projects_router import project_store
from api.store import project_store_schema as schema
from api.store.project_store import ProjectStore, ProjectStoreError

BBL = "3052110074"
MEMBERS = [{"name": "Architect", "role": "architect"}]
ANSWER = "Chat answer to: Any warnings?\n\n  Public record: 3 records in DOB ECB Violations.\nNote: no model was called.\n"


class PinBodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "projects.sqlite"
        self.store = ProjectStore(self.path)
        self.project_id = self.store.create_project("Bedford excavation", BBL, "design", MEMBERS)["id"]

    def pin(self, **more):
        return self.store.add_pin(self.project_id, "chat_answer", "chat-1", "Any warnings?", "architect", **more)["pins"]

    def test_a_body_comes_back_exactly_as_sent_and_a_pin_without_one_has_none(self):
        self.assertEqual(self.pin(body=ANSWER)[-1]["body"], ANSWER)  # its line breaks and leading spaces included
        self.assertIsNone(self.pin()[-1]["body"])
        self.assertIsNone(self.pin(body="")[-1]["body"])

    def test_a_body_over_the_cap_is_refused_whole_and_nothing_is_saved(self):
        cap = schema.MAX_TEXT["pin_body"]
        self.assertEqual(self.pin(body="x" * cap)[-1]["body"], "x" * cap)
        before = self.store.version(self.project_id)
        for bad in ("x" * (cap + 1), 7, ["text"]):
            with self.assertRaises(ProjectStoreError):
                self.pin(body=bad)
        self.assertEqual((self.store.version(self.project_id), len(self.store.get_project(self.project_id)["pins"])), (before, 1))

    def test_a_store_file_made_before_the_column_gets_it_and_keeps_its_pins(self):
        self.pin()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("ALTER TABLE pins DROP COLUMN body")  # the file as the first release made it
            db.commit()
        reopened = ProjectStore(self.path)
        pins = reopened.add_pin(self.project_id, "chat_answer", "chat-2", "Second", "architect", ANSWER)["pins"]
        self.assertEqual([pin["body"] for pin in pins], [None, ANSWER])
        ProjectStore(self.path)  # opening again is harmless

    def test_the_route_keeps_the_body_and_refuses_one_over_the_cap(self):
        app.dependency_overrides[project_store] = lambda: self.store
        self.addCleanup(app.dependency_overrides.clear)
        client, path = TestClient(app), f"/api/projects/{self.project_id}/pins"
        pin = {"kind": "chat_answer", "ref_id": "chat-1", "title": "Any warnings?", "by_role": "architect"}
        saved = client.post(path, json={**pin, "body": ANSWER})
        self.assertEqual((saved.status_code, saved.json()["pins"][-1]["body"]), (200, ANSWER))
        self.assertEqual(client.post(path, json=pin).json()["pins"][-1]["body"], None)
        refused = client.post(path, json={**pin, "body": "x" * (schema.MAX_TEXT["pin_body"] + 1)})
        self.assertEqual((refused.status_code, "8000" in refused.json()["detail"]), (422, True))


if __name__ == "__main__":
    unittest.main()
