"""Lessons: past incidents tagged by how they failed, each failure mode tied to what prevents it."""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class LessonData(unittest.TestCase):
    def setUp(self):
        self.lessons = load("data/cases/lessons.json")
        self.cases = {c["id"]: c for c in load("data/cases/cases.json")}
        rules = load("actions/rules.json")
        from checklist.checklist_rules import RULES
        self.items = ({f"checklist:{r.id}" for r in RULES} | {f"actions:{r['id']}" for r in rules["hazard_rules"]}
                      | {f"lesson:{r['id']}" for r in rules["lesson_rules"]})

    def test_every_tagged_case_exists_and_uses_known_modes(self):
        modes = set(self.lessons["failure_modes"])
        for case_id, tag in self.lessons["cases"].items():
            self.assertIn(case_id, self.cases, case_id)
            self.assertTrue(set(tag["modes"]) <= modes, case_id)
            self.assertIn(tag["basis"], ("reported_cause", "event_only"), case_id)

    def test_cases_without_a_reported_cause_are_tagged_by_event_only(self):
        for case_id, tag in self.lessons["cases"].items():
            if self.cases[case_id]["cause_status"] != "reported":
                self.assertEqual(tag["basis"], "event_only", case_id)

    def test_every_mode_says_what_prevents_it_and_where_it_applies(self):
        for mode_id, mode in self.lessons["failure_modes"].items():
            self.assertTrue(mode["prevent_with"], mode_id)
            self.assertTrue(set(mode["prevent_with"]) <= self.items, (mode_id, set(mode["prevent_with"]) - self.items))
            self.assertTrue(set(mode["options"]) <= {"renovate", "demolish_rebuild", "new_build"}, mode_id)
            self.assertTrue(mode["scopes"], mode_id)


if __name__ == "__main__":
    unittest.main()


class Outlook(unittest.TestCase):
    """What could go wrong here, for every option: lessons ranked, each with its incidents and its prevention."""

    @classmethod
    def setUpClass(cls):
        from lessons.outlook import site_outlook
        from site_profile.build_profile import build_profile
        pull = load("data/cache/861-park-ave-brooklyn.json")
        cls.profile = build_profile(pull)
        cls.result = site_outlook(cls.profile)
        cls.by_id = {l["id"]: l for l in cls.result["lessons"]}

    def test_fits_the_contract(self):
        from api.contracts import SiteOutlook
        SiteOutlook.model_validate(self.result)

    def test_every_lesson_has_incidents_and_prevention(self):
        self.assertGreaterEqual(len(self.result["lessons"]), 8)
        for lesson in self.result["lessons"]:
            self.assertTrue(lesson["cases"], lesson["id"])
            self.assertLessEqual(len(lesson["cases"]), 3, lesson["id"])
            self.assertGreaterEqual(lesson["case_count"], len(lesson["cases"]))
            self.assertTrue(all(p["title"] for p in lesson["prevent_with"]), lesson["id"])

    def test_this_lots_own_records_show_where_they_bear(self):
        self.assertIn("related records here", self.by_id["neighbor_undermined"]["here"])
        self.assertIsNone(self.by_id["gas_explosion"]["here"])

    def test_an_incident_with_no_published_cause_is_marked_event_only(self):
        cases = {c["case_id"]: c for l in self.result["lessons"] for c in l["cases"]}
        if "case-1321-flatbush-2026" in cases:
            self.assertEqual(cases["case-1321-flatbush-2026"]["basis"], "event_only")

    def test_ranked_worst_first(self):
        worst = [max(c["severity"] for c in l["cases"]) for l in self.result["lessons"]]
        self.assertEqual(worst, sorted(worst, reverse=True))

    def test_route(self):
        from fastapi.testclient import TestClient

        from api.main import app
        r = TestClient(app).get("/api/sites/3015790010/outlook")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.json()["lessons"])
