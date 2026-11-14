"""Offline tests for checklist. Run from the repo root: python3 -m unittest discover -s tests -t ."""

from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from checklist import applicability, neighbor_context, record_dates, record_evidence
from checklist.build_checklist import build

REPO = Path(__file__).resolve().parent.parent
CUTOFF = date(2026, 11, 11)


def _filings(*records, status="ok"):
    return {"status": status, "records": list(records)}


S3 = {"job_filing_number": "X-S3", "filing_date": "2026-02-24T00:00:00.000",
      "earth_work_work_type_": "YES", "foundation_work_type_": "YES", "support_of_excavation_work_type_": "No"}
LATE = {**S3, "job_filing_number": "X-S9", "filing_date": "2026-11-12T00:00:00.000"}


class DateTests(unittest.TestCase):
    def test_every_stored_format_and_undated(self):
        self.assertEqual(record_dates.parse_record_date("20260423"), date(2026, 4, 23))
        self.assertEqual(record_dates.parse_record_date("2026-04-23T00:00:00.000"), date(2026, 4, 23))
        self.assertEqual(record_dates.parse_record_date("04/23/2026"), date(2026, 4, 23))
        self.assertIsNone(record_dates.parse_record_date("20261341"))
        split = record_dates.split_by_cutoff("ecb_violations", [{"issue_date": "20260423"},
                                                                {"issue_date": "20261111"}, {}], CUTOFF)
        self.assertEqual([len(split[k]) for k in ("before", "on_or_after", "undated")], [1, 1, 1])


class InputTests(unittest.TestCase):
    def test_bad_inputs_are_refused(self):
        for bad in [{"depth": 3}, {"underpinning_planned": "yes"}, {"excavation_depth_ft": -1},
                    {"excavation_depth_ft": True}, {"distance_to_building_ft": {"3052110073": "near"}}]:
            with self.assertRaises(ValueError):
                applicability.validate_inputs(bad)
        self.assertEqual(applicability.validate_inputs({"_note": "x", "excavation_depth_ft": 12}),
                         {"excavation_depth_ft": 12})


class ExcavationTests(unittest.TestCase):
    def test_record_decides_and_a_contrary_input_is_shown_not_obeyed(self):
        result = applicability.excavation_status(_filings(S3), {"involves_excavation": False}, None)
        self.assertEqual(result["status"], "applies")
        self.assertEqual(result["basis"][0]["kind"], "public_record")
        self.assertTrue(result["notes"])

    def test_cutoff_hides_later_filings(self):
        result = applicability.excavation_status(_filings(LATE), {}, CUTOFF)
        self.assertEqual(result["status"], "needs_input")

    def test_failed_query_is_not_read_as_no_excavation(self):
        result = applicability.excavation_status(_filings(status="error"), {}, None)
        self.assertEqual((result["status"], result["needs"]), ("needs_input", ["involves_excavation"]))


class ThresholdTests(unittest.TestCase):
    EXCAVATING = {"status": "applies", "basis": [], "needs": [], "notes": []}

    def _survey(self, **inputs):
        return applicability.evaluate("survey_threshold", inputs, self.EXCAVATING, "3052110073")["status"]

    def test_preconstruction_survey_thresholds(self):
        self.assertEqual(self._survey(excavation_depth_ft=12), "applies")
        self.assertEqual(self._survey(excavation_depth_ft=3), "does_not_apply")
        self.assertEqual(self._survey(excavation_depth_ft=7, distance_to_building_ft={"3052110073": 5}), "applies")
        self.assertEqual(self._survey(excavation_depth_ft=7, distance_to_building_ft={"3052110073": 15}), "does_not_apply")
        self.assertEqual(self._survey(excavation_depth_ft=7), "needs_input")
        self.assertEqual(self._survey(), "needs_input")

    def test_monitoring_follows_depth_and_distance(self):
        def status(**inputs):
            return applicability.evaluate("monitoring_distance", inputs, self.EXCAVATING, "3052110073")["status"]
        self.assertEqual(status(excavation_depth_ft=12, distance_to_building_ft={"3052110073": 0}), "applies")
        self.assertEqual(status(excavation_depth_ft=12, distance_to_building_ft={"3052110073": 30}), "does_not_apply")
        self.assertEqual(status(excavation_depth_ft=4, distance_to_building_ft={"3052110073": 0}), "needs_input")


class ContextTests(unittest.TestCase):
    def test_status_words_match_whole_words_only(self):
        self.assertEqual(neighbor_context.classify("dob_violations", {"violation_category": "V-DOB VIOLATION - ACTIVE"}), "open")
        inactive = {"violation_category": "V-DOB VIOLATION - INACTIVE"}  # contains "ACTIVE"
        self.assertEqual(neighbor_context.classify("dob_violations", inactive), "not_stated")
        self.assertEqual(neighbor_context.classify("hpd_violations", {"violationstatus": "Close"}), "closed")

    def test_a_failed_dataset_reports_its_status_not_zero(self):
        counts = neighbor_context.count_statuses("hpd_violations", {"status": "error", "error": "HTTP 503"}, None)
        self.assertEqual(counts["status"], "error")
        self.assertNotIn("open", counts)

    def test_building_presence(self):
        def lot(footprints, pluto):
            return {"footprint_buildings": footprints, "datasets": {"pluto": pluto}}
        ok_none = {"status": "ok", "count": 0, "records": []}
        self.assertEqual(neighbor_context.building_presence(lot({"status": "ok", "count": 1}, ok_none))["status"], "yes")
        self.assertEqual(neighbor_context.building_presence(lot(ok_none, ok_none))["status"], "no")
        self.assertEqual(neighbor_context.building_presence(lot({"status": "error"}, ok_none))["status"], "unknown")


class CitationTests(unittest.TestCase):
    def test_citations_need_a_bc_prefix_or_a_dotted_section(self):
        self.assertEqual(record_evidence.cited_sections("BC 3301.2,27-1009(A) FAIL TO SAFEGUARD"), ["3301.2"])
        self.assertEqual(record_evidence.cited_sections("SIGN AT 1730 BROADWAY"), [])
        self.assertEqual(record_evidence.cited_sections("NO 3309.4.3 PRECONSTRUCTION SURVEY"), ["3309.4.3"])

    def test_a_citation_attaches_to_its_row_and_broader_rows_only(self):
        citations = [{"cited": "3309.4.3"}]
        self.assertTrue(record_evidence.citations_for_row("3309.4", citations))
        self.assertFalse(record_evidence.citations_for_row("3304.4.1", [{"cited": "3304.4"}]))


class CachedHeroCaseTests(unittest.TestCase):
    """Structure only: numbers in the cache change whenever someone re-pulls."""

    @classmethod
    def setUpClass(cls):
        pull = json.loads((REPO / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        cls.result = build(pull, {}, CUTOFF)

    def test_nothing_is_marked_done_from_public_data(self):
        self.assertEqual({r["proof"]["status"] for r in self.result["rows"]}, {"not_provided"})

    def test_excavation_comes_from_the_record_and_1321_flatbush_is_adjacent(self):
        self.assertEqual(self.result["excavation"]["basis"][0]["kind"], "public_record")
        self.assertIn("3052110073", [b["bbl"] for b in self.result["adjacent_buildings"]])

    def test_records_from_the_collapse_day_are_outside_the_before_view(self):
        dates = [m["issue_date"] for m in self.result["site"]["stop_work_mentions"]]
        self.assertTrue(dates)
        self.assertTrue(all(record_dates.parse_record_date(d) < CUTOFF for d in dates))

    def test_provided_proof_closes_the_gap_but_stays_unverified(self):
        pull = json.loads((REPO / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        result = build(pull, {"provided_proof": {"3309.4": {"document": "d", "provided_by": "p"}}}, CUTOFF)
        row = [r for r in result["rows"] if r["section"] == "3309.4"][0]
        self.assertEqual((row["proof"]["status"], row["open_gap"]), ("provided_unverified", False))


if __name__ == "__main__":
    unittest.main()
