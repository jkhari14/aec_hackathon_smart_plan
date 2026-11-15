"""The goal's status script reads BUILD.md correctly and keeps staged files inside their owner's paths."""

from __future__ import annotations

import unittest

from tools.foresite_status import classify, read_plan

TEAM = {"Jacob", "Camilo", "Shandon", "Jahleel", "Lise", "Rishabh", "Hongyu", "Ethnie"}


class ReadsBuildMd(unittest.TestCase):
    def setUp(self):
        self.prs, self.owns = read_plan()

    def test_every_pr_in_the_order_table(self):
        self.assertEqual([p.number for p in self.prs], list(range(20)))
        self.assertEqual({p.owner for p in self.prs}, TEAM)

    def test_dependencies_point_backwards(self):
        for p in self.prs:
            for d in p.depends_on:
                self.assertLess(d, p.number, f"PR {p.number} depends on a later PR {d}")

    def test_everyone_owns_paths(self):
        self.assertEqual(set(self.owns), TEAM)
        for person, paths in self.owns.items():
            self.assertTrue(paths, person)


class StagedFiles(unittest.TestCase):
    owned = ["city_layers/", "data/layers/"]

    def test_own_and_shared_paths_pass(self):
        problems, shared = classify(["city_layers/fema.py", "tests/test_fema.py"], "Lise", self.owned)
        self.assertEqual(problems, [])
        self.assertEqual(shared, ["tests/test_fema.py"])

    def test_other_paths_and_private_files_fail(self):
        paths = [
            "web/src/app/App.tsx",
            "6159-P1 Objections 11-11-2026.pdf",
            "AECtech_Hackathon_Brainstorm_Transcript_Part_3.md",
            "city_layers/.env",
        ]
        problems, _ = classify(paths, "Lise", self.owned)
        self.assertEqual(len(problems), 4)

    def test_prefix_is_not_ownership(self):
        problems, _ = classify(["city_layers_old/x.py"], "Lise", self.owned)
        self.assertEqual(len(problems), 1)


if __name__ == "__main__":
    unittest.main()
