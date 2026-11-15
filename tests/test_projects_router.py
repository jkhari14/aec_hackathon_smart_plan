"""The projects routes in the real app: two tabs as two roles, ETag polling, contract bodies, 404 and 422."""

import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.contracts import Project
from api.main import app
from api.routers.projects_router import project_store
from api.store.project_store import ProjectStore
from api.stubs import FIXTURE_HEADER

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"
BOTH = [{"name": "Architect", "role": "architect"}, {"name": "Structural engineer", "role": "structural_engineer"}]


def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


class ProjectsRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = ProjectStore(Path(self.tmp.name) / "projects.sqlite")
        app.dependency_overrides[project_store] = lambda: store
        self.architect_tab, self.engineer_tab = TestClient(app), TestClient(app)
        created = self.architect_tab.post("/api/projects", json={"name": "Bedford", "site_bbl": "3052110074",
                                                                  "stage": "design", "members": BOTH})
        self.assertEqual(created.status_code, 200, created.text)
        self.project_id = created.json()["id"]
        self.path = f"/api/projects/{self.project_id}"

    def tearDown(self):
        app.dependency_overrides.pop(project_store, None)
        self.tmp.cleanup()

    def test_two_tabs_as_two_roles_on_one_project(self):
        seen = self.engineer_tab.get(self.path)
        self.assertEqual(self.engineer_tab.get(self.path, headers={"If-None-Match": seen.headers["ETag"]}).status_code, 304)
        self.architect_tab.post(f"{self.path}/items", json=fixture("actions"))
        self.engineer_tab.patch(f"{self.path}/items", json=[{"id": "act-bc-3309-4", "status": "in_progress"}])
        self.engineer_tab.post(f"{self.path}/notes", json={"author_role": "structural_engineer", "text": "Survey Tuesday."})
        polled = self.architect_tab.get(self.path, headers={"If-None-Match": seen.headers["ETag"]})
        self.assertEqual(polled.status_code, 200)
        project = Project.model_validate(polled.json())
        self.assertEqual(project.items[0].status, "in_progress")
        self.assertEqual(project.notes[0].author_role, "structural_engineer")
        self.assertNotEqual(polled.headers["ETag"], seen.headers["ETag"])
        self.assertIsNone(polled.headers.get(FIXTURE_HEADER), "a real project is never labelled sample data")

    def test_a_write_answers_with_the_whole_project_and_its_etag(self):
        answer = self.architect_tab.post(f"{self.path}/pins", json={"kind": "case", "ref_id": "case-714-39th-2018",
                                                                    "title": "A similar excavation", "by_role": "architect"})
        self.assertEqual(answer.status_code, 200, answer.text)
        self.assertEqual(answer.json()["pins"][0]["ref_id"], "case-714-39th-2018")
        self.assertEqual(self.architect_tab.get(self.path, headers={"If-None-Match": answer.headers["ETag"]}).status_code, 304)

    def test_patch_left_out_owner_stays_and_null_unassigns(self):
        self.architect_tab.post(f"{self.path}/items", json=fixture("actions"))
        kept = self.architect_tab.patch(f"{self.path}/items", json=[{"id": "act-bc-3309-4", "status": "done"}]).json()
        self.assertEqual(kept["items"][0]["owner_role"], "structural_engineer")
        cleared = self.architect_tab.patch(f"{self.path}/items", json=[{"id": "act-bc-3309-4", "owner_role": None}]).json()
        self.assertEqual((cleared["items"][0]["status"], cleared["items"][0]["owner_role"]), ("done", None))

    def test_the_structural_model_is_checked_and_kept(self):
        model = fixture("structural_model")
        self.assertEqual(self.architect_tab.post(f"{self.path}/model", json=model).json()["structural_model"], model)
        self.assertEqual(self.architect_tab.post(f"{self.path}/model", json={**model, "confidence": 2}).status_code, 422)

    def test_unknown_projects_and_items_are_404(self):
        for response in (
            self.architect_tab.get("/api/projects/0123456789abcdef"),
            self.architect_tab.get("/api/projects/proj-sample"),
            self.architect_tab.post("/api/projects/0123456789abcdef/notes", json={"author_role": "architect", "text": "x"}),
            self.architect_tab.patch(f"{self.path}/items", json=[{"id": "nope", "status": "done"}]),
        ):
            self.assertEqual(response.status_code, 404, response.text)

    def test_refused_input_is_422(self):
        solo = self.architect_tab.post("/api/projects", json={"name": "Solo", "site_bbl": "3052110074", "stage": "design",
                                                               "members": BOTH[:1]}).json()["id"]
        for response in (
            self.architect_tab.post(f"/api/projects/{solo}/notes", json={"author_role": "structural_engineer", "text": "x"}),
            self.architect_tab.post(f"{self.path}/notes", json={"author_role": "architect", "text": "x", "extra": 1}),
            self.architect_tab.post(f"{self.path}/notes", json={"author_role": "architect", "text": "x" * 5000}),
            self.architect_tab.post("/api/projects", json={"name": "x", "site_bbl": "1", "stage": "design", "members": BOTH}),
            self.architect_tab.patch(f"{self.path}/items", json=[{"id": "act-bc-3309-4", "status": "verified"}]),
        ):
            self.assertEqual(response.status_code, 422, response.text)


if __name__ == "__main__":
    unittest.main()
