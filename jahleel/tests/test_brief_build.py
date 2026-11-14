"""Offline tests for the brief: built from the cached demo sites, no network."""

import copy
import unittest
from datetime import date

from jahleel.api.brief import brief_build, brief_records
from jahleel.api.brief.brief_build import build_brief
from jahleel.api.brief.brief_models import Brief


class BriefFromCacheTests(unittest.TestCase):
    def test_demo_site_builds_and_validates(self):
        brief = build_brief("2625-bedford-ave-brooklyn")
        Brief.model_validate(brief.model_dump())
        self.assertEqual(brief.site.bbl, "3052110074")
        self.assertIn("3052110073", [lot.bbl for lot in brief.touching_lots])

    def test_checklist_rows_carry_no_roast(self):
        rows = build_brief("2625-bedford-ave-brooklyn").model_dump()["checklist"]
        self.assertTrue(rows)
        self.assertFalse([row["id"] for row in rows if "roast" in row])

    def test_stop_work_mention_is_flagged_on_its_record(self):
        brief = build_brief("2625-bedford-ave-brooklyn")
        flagged = {r.id for r in brief.records if r.mentions_stop_work}
        self.assertIn("ecb_violations:39553409Z", flagged)

    def test_311_resolution_and_its_stop_work_mention_carry_the_day_dob_acted(self):
        records = {r.id: r for r in build_brief("2625-bedford-ave-brooklyn").records}
        request = records["dob_311_requests:68381531"]
        self.assertEqual(request.date, "2026-03-18")
        self.assertIn("removed the stop work order", request.resolution)
        self.assertEqual(request.resolution_recorded, "2026-05-08")
        self.assertTrue(request.mentions_stop_work)
        self.assertEqual(request.stop_work_first_mentioned, "2026-05-08")

    def test_checklist_comes_from_the_engine_and_never_claims_proof(self):
        brief = build_brief("2625-bedford-ave-brooklyn")
        self.assertEqual(len(brief.checklist), brief.checklist_summary.rows)
        self.assertTrue(all(row.proof.status != "provided_unverified" for row in brief.checklist))
        self.assertIn("3309.4", {row.section for row in brief.checklist if row.open_gap})

    def test_reported_letter_is_a_lead_and_drops_out_before_its_date(self):
        notice = {r.id: r for r in build_brief("2625-bedford-ave-brooklyn").checklist}["notice"]
        self.assertEqual(notice.proof.status, "reported_not_read")
        replay = {r.id: r for r in build_brief("2625-bedford-ave-brooklyn", as_of=date(2026, 6, 1)).checklist}
        self.assertEqual(replay["notice"].proof.status, "not_provided")

    def test_as_of_reaches_the_engine_and_keeps_every_record(self):
        full = build_brief("2625-bedford-ave-brooklyn")
        replay = build_brief("2625-bedford-ave-brooklyn", as_of=date(2026, 6, 1))
        self.assertEqual(replay.as_of, "2026-06-01")
        self.assertEqual(len(replay.records), len(full.records))

    def test_unknown_or_malformed_slug_is_refused(self):
        with self.assertRaises(FileNotFoundError):
            build_brief("no-such-site")
        for bad in ("../README", "a/b", "", "x" * 81):
            with self.assertRaises(ValueError):
                build_brief(bad)


class LotFactsTests(unittest.TestCase):
    def test_landmark_and_historic_district_are_blank_when_pluto_lists_none(self):
        def lot(extra):
            return {"datasets": {"pluto": {"status": "ok", "records": [{"address": "1 MAIN ST", **extra}]}}}
        listed = brief_build._facts(lot({"landmark": "OLD MILL", "histdist": "Park Slope Historic District"}))
        self.assertEqual((listed.landmark, listed.historic_district), ("OLD MILL", "Park Slope Historic District"))
        blank = brief_build._facts(lot({"landmark": "  "}))
        self.assertEqual((blank.landmark, blank.historic_district), (None, None))


class RecordTests(unittest.TestCase):
    def test_dates_normalize_from_each_dataset_format(self):
        self.assertEqual(brief_records.iso_date("20261111"), "2026-11-11")
        self.assertEqual(brief_records.iso_date("2026-06-03T22:32:02.000"), "2026-06-03")
        self.assertEqual(brief_records.iso_date("11/13/2026"), "2026-11-13")
        self.assertIsNone(brief_records.iso_date("soon"))
        self.assertIsNone(brief_records.iso_date(None))

    def test_failed_dataset_contributes_no_records(self):
        lot = {"bbl": "3052110074", "datasets": {"ecb_violations": {"status": "error", "records": [
            {"ecb_violation_number": "1", "issue_date": "20260101"}]}}}
        self.assertEqual(brief_records.lot_records(copy.deepcopy(lot), {}), [])

    def test_311_row_unstated_status_undated_resolution_and_earliest_mention(self):
        lot = {"bbl": "3052110054", "datasets": {"dob_311_requests": {"status": "ok", "records": [
            {"unique_key": "7", "created_date": "2021-01-20T09:00:00.000", "status": "Unspecified",
             "complaint_type": "General Construction/Plumbing", "descriptor": "Working Contrary To Stop Work Order",
             "resolution_description": "DOB inspected."}]}},
            "stop_work_mentions": [
                {"dataset": "dob_311_requests", "record_id": "7", "issue_date": "2021-03-02T00:00:00.000"},
                {"dataset": "dob_311_requests", "record_id": "7", "issue_date": "2021-01-20T09:00:00.000"},
                {"dataset": "dob_311_requests", "record_id": "7", "issue_date": None}]}
        [record] = brief_records.lot_records(lot, {})
        self.assertEqual(record.summary, "General Construction/Plumbing. Working Contrary To Stop Work Order")
        self.assertIsNone(record.status_today)
        self.assertEqual(record.resolution, "DOB inspected.")
        self.assertIsNone(record.resolution_recorded)
        self.assertEqual(record.stop_work_first_mentioned, "2021-01-20")


if __name__ == "__main__":
    unittest.main()
