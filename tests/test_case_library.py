"""The case library the app serves (data/cases/cases.json): every case sourced and dated, and no cause
stated unless it was publicly reported."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from api.contracts import Case

CASES = Path(__file__).resolve().parent.parent / "data" / "cases" / "cases.json"


class CaseLibrary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text())

    def test_every_case_matches_the_contract_and_ids_are_unique(self):
        for case in self.cases:
            Case.model_validate(case)
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_source_has_a_date(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertTrue(case["sources"])
                for source in case["sources"]:
                    self.assertTrue(source.get("date"), source["url"])

    def test_a_cause_is_stated_only_when_publicly_reported(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                if case["cause_status"] != "reported":
                    self.assertIsNone(case["cause_as_reported"])


if __name__ == "__main__":
    unittest.main()
