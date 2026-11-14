"""Offline tests for checklist. Run from the repo root: python3 -m unittest discover -s tests -t ."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from checklist import applicability, complaint_codes, neighbor_context, record_dates, record_evidence, row_proof
from checklist.checklist_rules import PARTIES, RULES
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
        self.assertEqual(neighbor_context.classify("dob_311_requests", {"status": "In Progress"}), "open")
        self.assertEqual(neighbor_context.classify("dob_311_requests", {"status": "Closed"}), "closed")
        self.assertEqual(neighbor_context.classify("dob_311_requests", {"status": "Unspecified"}), "not_stated")

    def test_a_failed_dataset_reports_its_status_not_zero(self):
        counts = neighbor_context.count_statuses("hpd_violations", {"status": "error", "error": "HTTP 503"}, None)
        self.assertEqual(counts["status"], "error")
        self.assertNotIn("open", counts)

    def test_lot_facts_pass_pluto_through_and_leave_blanks_blank(self):
        pluto = {"status": "ok", "records": [{"bbl": "3052110073", "lotarea": "1854", "builtfar": "1.66",
                                              "residfar": "2.43", "histdist": "Example Historic District"}]}
        ctx = neighbor_context.lot_context({"bbl": "3052110073", "datasets": {"pluto": pluto}}, None)
        self.assertEqual((ctx["lot_area_sqft"], ctx["built_far"], ctx["max_far"]["residential"]), ("1854", "1.66", "2.43"))
        self.assertEqual((ctx["historic_district"], ctx["landmark"]), ("Example Historic District", None))

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


class RuleTableTests(unittest.TestCase):
    def test_ids_are_unique_and_parties_come_from_the_fixed_list(self):
        self.assertEqual(len({r.id for r in RULES}), len(RULES))
        self.assertEqual(len({r.section for r in RULES}), len(RULES))
        for rule in RULES:
            self.assertTrue(rule.parties and set(rule.parties) <= set(PARTIES), rule.id)


class LeadTests(unittest.TestCase):
    LEAD = {"reported_by": "a paper", "document": "a letter", "url": "https://example.org/a",
            "document_date": "2026-06-10"}

    def test_bad_leads_are_refused(self):
        for bad in [{"leads": {"9999": [self.LEAD]}},
                    {"leads": {"3309.1.1": [{**self.LEAD, "url": "http://example.org/a"}]}},
                    {"leads": {"3309.1.1": [{**self.LEAD, "verified": True}]}},
                    {"leads": {"3309.1.1": [{"url": "https://example.org/a"}]}}]:
            with self.assertRaises(ValueError):
                row_proof.load_leads(bad, {"3309.1.1"}, None)

    def test_as_of_keeps_only_leads_dated_before_the_cutoff(self):
        raw = {"leads": {"3309.1.1": [self.LEAD, {**self.LEAD, "document_date": "2026-11-12"},
                                      {**self.LEAD, "document_date": None}]}}
        self.assertEqual(len(row_proof.load_leads(raw, {"3309.1.1"}, None)["3309.1.1"]), 3)
        self.assertEqual(len(row_proof.load_leads(raw, {"3309.1.1"}, CUTOFF)["3309.1.1"]), 1)

    def test_a_lead_never_closes_a_gap(self):
        pull = json.loads((REPO / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        result = build(pull, {}, CUTOFF, {"leads": {"3309.4": [self.LEAD]}})
        row = [r for r in result["rows"] if r["id"] == "foundation_protection"][0]
        self.assertEqual((row["proof"]["status"], row["open_gap"]), ("reported_not_read", True))


class ComplaintCodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.imp, cls.meta = complaint_codes.category_key()
        cls.table = {"A3": "FULL STOP WORK ORDER SERVED F"}

    def _lot(self, *records, status="ok"):
        return {"bbl": "3052110073", "datasets": {"dob_complaints": {"status": status, "records": list(records)}}}

    def test_an_imported_meaning_is_its_own_tier_and_never_ok(self):
        lot = self._lot({"complaint_number": "1", "date_entered": "11/01/2026", "complaint_category": "30"})
        category = complaint_codes.lot_complaints(lot, None, self.imp, self.table)["records"][0]["category"]
        self.assertEqual((category["kind"], category["status"]), ("manual_import", "imported_unchecked"))
        self.assertIn("Structural Stability", category["description"])

    def test_a_code_a_key_lacks_is_a_gap_and_keeps_the_raw_code(self):
        lot = self._lot({"complaint_number": "1", "date_entered": "11/01/2026", "complaint_category": "7G",
                         "disposition_code": "AF", "disposition_date": "11/02/2026"})
        record = complaint_codes.lot_complaints(lot, None, self.imp, self.table)["records"][0]
        self.assertEqual((record["category"]["code"], record["category"]["status"]), ("7G", "not_in_key"))
        self.assertIn("may be older than the code", record["category"]["reason"])
        self.assertEqual((record["disposition"]["code"], record["disposition"]["status"]), ("AF", "not_in_table"))
        self.assertIsNone(record["disposition"]["description"])
        missing = complaint_codes.codes_not_found([{"complaints": {"records": [record]}}])
        self.assertEqual(missing, {"dob_complaint_categories": ["7G"], "dob_complaint_dispositions": ["AF"]})

    def test_the_disposition_table_is_public_record_and_its_absence_is_said(self):
        lot = self._lot({"complaint_number": "1", "date_entered": "11/01/2026", "disposition_code": "A3",
                         "disposition_date": "11/02/2026"})
        found = complaint_codes.lot_complaints(lot, None, self.imp, self.table)["records"][0]["disposition"]
        self.assertEqual((found["kind"], found["status"], found["description"]),
                         ("public_record", "ok", "FULL STOP WORK ORDER SERVED F"))
        none = complaint_codes.lot_complaints(lot, None, None, None)["records"][0]
        self.assertEqual((none["category"]["status"], none["disposition"]["status"]), ("not_recorded", "key_unavailable"))
        self.assertEqual(complaint_codes.disposition_key({})[1]["status"], "not_pulled")
        failed = {"reference_tables": {"dob_complaint_dispositions": {"status": "error", "error": "HTTP 503"}}}
        self.assertEqual(complaint_codes.disposition_key(failed), (None, {"kind": "public_record", "status": "error",
                                                                          "reason": "HTTP 503"}))

    def test_as_of_withholds_later_dispositions_and_later_complaints(self):
        lot = self._lot(
            {"complaint_number": "early", "date_entered": "11/01/2026", "disposition_code": "A3", "disposition_date": "11/05/2026"},
            {"complaint_number": "disposed_late", "date_entered": "11/02/2026", "disposition_code": "A3",
             "disposition_date": "11/11/2026"},
            {"complaint_number": "undated", "date_entered": "11/03/2026", "disposition_code": "A3"},
            {"complaint_number": "late", "date_entered": "11/11/2026"})
        records = complaint_codes.lot_complaints(lot, CUTOFF, self.imp, self.table)["records"]
        by_number = {r["complaint_number"]: r["disposition"] for r in records}
        self.assertNotIn("late", by_number)
        self.assertEqual(by_number["early"]["code"], "A3")
        self.assertEqual((by_number["disposed_late"]["code"], by_number["disposed_late"]["status"]), (None, "after_cutoff"))
        self.assertEqual((by_number["undated"]["code"], by_number["undated"]["status"]), (None, "undated"))
        self.assertEqual([r["complaint_number"] for r in records], ["undated", "disposed_late", "early"])

    def test_a_failed_query_or_import_is_reported_not_empty(self):
        self.assertEqual(complaint_codes.lot_complaints(self._lot(status="error"), None, self.imp, self.table)["status"], "error")
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(complaint_codes.category_key(Path(root))[1]["status"], "missing")
            broken = Path(root) / "dob_complaint_categories" / "2026-11-14_broken"
            broken.mkdir(parents=True)
            (broken / "provenance.json").write_text("{}")
            imp, meta = complaint_codes.category_key(Path(root))
            self.assertIsNone(imp)
            self.assertEqual((meta["kind"], meta["status"]), ("manual_import", "error"))
            self.assertIn("broken", meta["reason"])


class CachedHeroCaseTests(unittest.TestCase):
    """Structure only: numbers in the cache change whenever someone re-pulls."""

    @classmethod
    def setUpClass(cls):
        pull = json.loads((REPO / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        cls.result = build(pull, {}, CUTOFF)

    def test_nothing_is_marked_done_from_public_data(self):
        self.assertEqual({r["proof"]["status"] for r in self.result["rows"]}, {"not_provided"})

    def test_excavation_comes_from_the_record_and_1321_flatbush_is_adjacent(self):
        basis = self.result["excavation"]["basis"][0]
        self.assertEqual(basis["kind"], "public_record")
        self.assertTrue(all(r["ref"].startswith("dob_now_filings:") for r in basis["records"]))
        self.assertIn("3052110073", [b["bbl"] for b in self.result["adjacent_buildings"]])

    def test_records_from_the_collapse_day_are_outside_the_before_view(self):
        dates = [m["issue_date"] for m in self.result["site"]["stop_work_mentions"]]
        self.assertTrue(dates)
        self.assertTrue(all(record_dates.parse_record_date(d) < CUTOFF for d in dates))

    def test_complaints_carry_refs_and_no_imported_meaning_reads_as_ok(self):
        keys = self.result["code_keys"]
        self.assertEqual(keys["dob_complaint_categories"]["kind"], "manual_import")
        self.assertNotEqual(keys["dob_complaint_categories"]["status"], "ok")
        records = [r for ctx in [self.result["site"], *self.result["adjacent_buildings"]]
                   for r in ctx["complaints"]["records"]]
        self.assertTrue(records)
        self.assertTrue(all(r["ref"].startswith("dob_complaints:") for r in records))
        self.assertNotIn("ok", {r["category"]["status"] for r in records})

    def test_provided_proof_closes_the_gap_but_stays_unverified(self):
        pull = json.loads((REPO / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        result = build(pull, {"provided_proof": {"3309.4": {"document": "d", "provided_by": "p"}}}, CUTOFF)
        row = [r for r in result["rows"] if r["section"] == "3309.4"][0]
        self.assertEqual((row["proof"]["status"], row["open_gap"]), ("provided_unverified", False))


if __name__ == "__main__":
    unittest.main()
