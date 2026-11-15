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
