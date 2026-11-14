"""Offline tests for data_pull. Run from the repo root: python3 -m unittest discover -s tests -t ."""

from __future__ import annotations

import unittest
from unittest import mock

from data_pull import lot_neighbors, lot_records, soda_client
from data_pull.stop_work_mentions import find_stop_work_mentions

BBL = "3052110073"


class QuerySafetyTests(unittest.TestCase):
    def test_bbl_validation_rejects_injection_and_bad_shapes(self):
        for bad in ["3052110073' OR '1'='1", "305211007", "6052110073", "", None]:
            with self.assertRaises(ValueError):
                soda_client.validate_bbl(bad)
        self.assertEqual(soda_client.validate_bbl(BBL), BBL)

    def test_in_list_refuses_anything_but_digits(self):
        with self.assertRaises(ValueError):
            soda_client.soql_in(["3120364", "1') OR ('1'='1"])
        with self.assertRaises(ValueError):
            soda_client.soql_in([])
        self.assertEqual(soda_client.soql_in(["3120364"]), "('3120364')")

    def test_polygon_to_wkt_passes_numbers_only(self):
        square = {"type": "Polygon", "coordinates": [[[-73.9, 40.6], [-73.8, 40.6], [-73.9, 40.6]]]}
        self.assertTrue(lot_neighbors.geojson_to_wkt(square).startswith("MULTIPOLYGON(((-73.9 40.6,"))
        for bad_point in [["1); DROP", 40.6], [float("nan"), 40.6]]:
            bad = {"type": "Polygon", "coordinates": [[bad_point, [-73.8, 40.6]]]}
            with self.assertRaises(ValueError):
                lot_neighbors.geojson_to_wkt(bad)


class JoinShapeTests(unittest.TestCase):
    def test_lot_and_block_widths(self):
        self.assertEqual(soda_client.lot_variants("0073"), ["00073", "0073", "73"])
        self.assertEqual(soda_client.block_variants("05211"), ["05211", "5211"])

    def test_placeholder_bins(self):
        self.assertTrue(soda_client.is_placeholder_bin("3000000"))
        self.assertFalse(soda_client.is_placeholder_bin("3120364"))

    def test_record_lot_reads_every_stored_shape(self):
        self.assertEqual(lot_records.record_lot({"bbl": "3052110073.00000000"}), BBL)
        self.assertEqual(lot_records.record_lot({"boro": "3", "block": "05211", "lot": "00073"}), BBL)
        self.assertEqual(lot_records.record_lot({"boro": "3", "block": "5211", "lot": "73"}), BBL)
        self.assertIsNone(lot_records.record_lot({"boro": "B", "block": "5211", "lot": "73"}))
        self.assertIsNone(lot_records.record_lot({"bin": "3120364"}))


def _fake_query(responses):
    calls = []

    def fake(dataset_id, params):
        calls.append((dataset_id, params))
        response = responses.get(dataset_id, [])
        if isinstance(response, Exception):
            raise response
        return response, f"https://example.test/{dataset_id}"

    return fake, calls


class PullLotTests(unittest.TestCase):
    def test_failure_is_an_error_not_zero_and_other_lot_bins_are_not_adopted(self):
        fake, calls = _fake_query({
            "64uk-42ks": [{"bbl": "3052110073.00000000", "address": "1321 FLATBUSH AVENUE"}],
            "w9ak-ipjd": [
                {"bbl": BBL, "bin": "3120364", "job_filing_number": "A-I1"},
                {"bbl": "3052110059", "bin": "3999999", "job_filing_number": "B-I1"},
                {"bin": "3888888", "job_filing_number": "C-I1"},  # states no lot at all
            ],
            "3h2n-5cm9": soda_client.SodaQueryError("3h2n-5cm9: HTTP 503"),
            "6bgk-3dad": [],
        })
        with mock.patch.object(soda_client, "query", side_effect=fake):
            lot = lot_records.pull_lot(BBL, seed_bins=["3000000"])

        datasets = lot["datasets"]
        self.assertEqual(datasets["dob_violations"]["status"], "error")
        self.assertNotIn("count", datasets["dob_violations"])
        self.assertEqual((datasets["ecb_violations"]["status"], datasets["ecb_violations"]["count"]), ("ok", 0))
        # Placeholder dropped; neither another lot's BIN nor an unplaced row's BIN is adopted.
        self.assertEqual(lot["bins"], ["3120364"])
        self.assertEqual(datasets["dob_now_filings"]["count"], 2)
        self.assertEqual(len(datasets["dob_now_filings"]["held_back_other_lot"]), 1)
        complaints_where = [p["where"] for d, p in calls if d == "eabe-havv"][0]
        self.assertIn("'3120364'", complaints_where)

    def test_complaints_are_skipped_without_a_bin(self):
        fake, _ = _fake_query({})
        with mock.patch.object(soda_client, "query", side_effect=fake):
            lot = lot_records.pull_lot(BBL, seed_bins=[])
        self.assertEqual(lot["datasets"]["dob_complaints"]["status"], "skipped")


class StopWorkMentionTests(unittest.TestCase):
    def test_finds_mentions_in_record_text_only(self):
        datasets = {
            "dob_violations": {"records": [
                {"isn_dob_bis_viol": "1", "issue_date": "20261111", "description": "FULL STOP WORK ORDER DUE TO COLLAPSE"},
                {"isn_dob_bis_viol": "2", "issue_date": "20260101", "description": "ELEVATOR INSPECTION OVERDUE"},
            ]},
            "ecb_violations": {"records": [
                {"ecb_violation_number": "9", "issue_date": "20260423",
                 "section_law_description1": "28-207.2.2 UNLAWFULLY CONTINUED WORK WHILE NOTICE OF A"},
            ]},
        }
        mentions = find_stop_work_mentions(datasets)
        self.assertEqual([m["record_id"] for m in mentions], ["1", "9"])


if __name__ == "__main__":
    unittest.main()
