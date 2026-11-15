"""Early-warning rules on the cached 2625 Bedford pull, the warnings API, and the watchlist pipeline (offline)."""

from __future__ import annotations

import copy
import json
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from api.contracts import LayerFeatureCollection
from api.main import app
from api.stubs import FIXTURE_HEADER
from early_warning import geometry, watchlist
from early_warning.records import from_pull
from early_warning.rules import evaluate
from early_warning.site_pulls import SiteUnavailable
from early_warning.weather import Day, Weather, WeatherError

ROOT = Path(__file__).resolve().parent.parent
BEDFORD = "3052110074"
AS_OF = date(2026, 6, 1)


def raw(name: str) -> dict:
    return json.loads((ROOT / "data" / "cache" / f"{name}.json").read_text())


def no_weather(*_args, **_kwargs):
    raise AssertionError("the weather should not be looked up here")


def run(pull: dict, as_of: date | None, weather=no_weather):
    warnings, checks = evaluate(from_pull(pull), as_of, weather)
    return warnings, {c.rule_id: c for c in checks}


def by_rule(warnings, rule_id):
    return [w for w in warnings if w.rule_id == rule_id]


class BedfordAsOfJune(unittest.TestCase):
    """Each rule on 2625 Bedford Ave as of 2026-06-01: what was knowable before that day."""

    @classmethod
    def setUpClass(cls):
        cls.warnings, cls.checks = run(raw("2625-bedford-ave-brooklyn"), AS_OF)

    def test_every_rule_reports_a_check(self):
        self.assertEqual(list(self.checks), ["adjacent_protection_no_follow_up", "stop_work_then_work_continued",
                                             "structural_complaint_near_earth_work", "weather_during_open_excavation"])
        for check in self.checks.values():
            self.assertEqual(check.as_of, "2026-06-01")
            self.assertTrue(check.sources)
            self.assertEqual(check.warnings, len(by_rule(self.warnings, check.rule_id)))

    def test_adjacent_protection_violation_with_no_follow_up(self):
        [warning] = by_rule(self.warnings, "adjacent_protection_no_follow_up")
        self.assertEqual(warning.evidence_record_ids, ["ecb_violations:39552071X"])
        self.assertEqual(warning.first_seen, "2026-04-10")  # 2026-03-20 plus 21 days
        self.assertIn("the next is dated 2026-04-23", warning.explanation)
        self.assertEqual(self.checks["adjacent_protection_no_follow_up"].status, "ok")

    def test_stop_work_then_work_continued(self):
        [warning] = by_rule(self.warnings, "stop_work_then_work_continued")
        self.assertEqual(warning.evidence_record_ids, ["ecb_violations:39553409Z"])
        self.assertEqual(warning.first_seen, "2026-04-23")
        self.assertIn("28-207.2.2", warning.explanation)

    def test_no_structural_complaint_near_earth_work_yet(self):
        # The code-30 complaints on the touching lots were entered on 2026-11-11, after this as-of date.
        self.assertEqual(by_rule(self.warnings, "structural_complaint_near_earth_work"), [])
        self.assertEqual(self.checks["structural_complaint_near_earth_work"].status, "ok")

    def test_no_open_excavation_so_weather_not_applicable(self):
        # The earth-work permit was issued 2026-09-09; the weather is never looked up.
        self.assertEqual(self.checks["weather_during_open_excavation"].status, "not_applicable")

    def test_most_severe_then_newest_first(self):
        self.assertEqual([w.first_seen for w in self.warnings], ["2026-04-23", "2026-04-10"])

    def test_matches_the_contract_fixtures(self):
        fixtures = ROOT / "contracts" / "fixtures"
        self.assertEqual([w.model_dump() for w in self.warnings], json.loads((fixtures / "warnings.json").read_text()))
        self.assertEqual([c.model_dump() for c in self.checks.values()],
                         json.loads((fixtures / "warning_checks.json").read_text()))


class LaterDates(unittest.TestCase):
    def test_structural_complaints_after_the_earth_work_permit(self):
        warnings, checks = run(raw("2625-bedford-ave-brooklyn"), date(2026, 11, 12), weather=lambda *a: Weather([], "u"))
        [warning] = by_rule(warnings, "structural_complaint_near_earth_work")
        self.assertEqual(warning.severity, 0)  # the vacate dispositions are dated 2026-11-12: not yet knowable
        self.assertEqual(sorted(warning.evidence_record_ids), sorted([
            "dob_now_filings:B01330433-S3", "dob_now_filings:B01330433-S4", "dob_complaints:3A88671",
            "dob_complaints:3A88672", "dob_complaints:3A88673", "dob_complaints:3A88676"]))
        self.assertEqual(warning.first_seen, "2026-11-11")

    def test_vacate_dispositions_raise_the_severity_once_knowable(self):
        warnings, _ = run(raw("2625-bedford-ave-brooklyn"), date(2026, 11, 13), weather=lambda *a: Weather([], "u"))
        [warning] = by_rule(warnings, "structural_complaint_near_earth_work")
        self.assertEqual(warning.severity, 1)
        self.assertIn("full vacate order", warning.explanation)

    def test_the_rule_also_runs_from_the_neighbor_side(self):
        warnings, _ = run(raw("1321-flatbush-ave-brooklyn"), date(2026, 11, 12), weather=lambda *a: Weather([], "u"))
        [warning] = by_rule(warnings, "structural_complaint_near_earth_work")
        self.assertIn("dob_complaints:3A88671", warning.evidence_record_ids)
        self.assertIn("2625 Bedford Avenue", warning.explanation)

    def test_heavy_rain_and_freeze_thaw_during_the_open_excavation(self):
        days = [Day(date(2026, 9, 27), 62.0, 20.0, 15.0), Day(date(2026, 10, 1), 3.0, 18.0, 9.0),
                Day(date(2026, 11, 3), 0.0, 6.0, -2.0)]
        seen = {}

        def weather(lat, lon, start, end):
            seen.update(start=start, end=end)
            return Weather(days, "https://archive-api.open-meteo.com/v1/archive?test")
        warnings, checks = run(raw("2625-bedford-ave-brooklyn"), date(2026, 11, 12), weather)
        [warning] = by_rule(warnings, "weather_during_open_excavation")
        self.assertEqual(seen, {"start": date(2026, 9, 9), "end": date(2026, 11, 11)})
        self.assertEqual(warning.title, "Heavy rain and freeze-thaw during an open excavation")
        self.assertIn("open_meteo:2026-09-27", warning.evidence_record_ids)
        self.assertIn("open_meteo:2026-11-03", warning.evidence_record_ids)
        self.assertNotIn("open_meteo:2026-10-01", warning.evidence_record_ids)
        self.assertEqual(checks["weather_during_open_excavation"].status, "ok")

    def test_failed_weather_is_an_error_not_a_clear_day(self):
        def weather(*_args):
            raise WeatherError("offline")
        warnings, checks = run(raw("2625-bedford-ave-brooklyn"), date(2026, 11, 12), weather)
        self.assertEqual(by_rule(warnings, "weather_during_open_excavation"), [])
        self.assertEqual(checks["weather_during_open_excavation"].status, "error")
        self.assertIn("couldn't load", checks["weather_during_open_excavation"].detail)

    def test_days_with_no_weather_data_are_reported(self):
        days = [Day(date(2026, 9, 9), None, None, None), Day(date(2026, 9, 10), 1.0, 20.0, 12.0)]
        _, checks = run(raw("2625-bedford-ave-brooklyn"), date(2026, 11, 12), lambda *a: Weather(days, "u"))
        self.assertEqual(checks["weather_during_open_excavation"].status, "error")
        self.assertIn("1 of 2 days", checks["weather_during_open_excavation"].detail)


class RuleEdges(unittest.TestCase):
    def setUp(self):
        self.pull = copy.deepcopy(raw("2625-bedford-ave-brooklyn"))

    def add(self, dataset: str, record: dict):
        self.pull["site"]["datasets"][dataset]["records"].append(record)

    def test_a_follow_up_within_21_days_clears_the_gap(self):
        self.add("dob_violations", {"isn_dob_bis_viol": "999", "issue_date": "20260402", "description": "RE-INSPECTION"})
        warnings, _ = run(self.pull, AS_OF)
        self.assertEqual(by_rule(warnings, "adjacent_protection_no_follow_up"), [])

    def test_a_new_complaint_is_not_a_follow_up(self):
        self.add("dob_complaints", {"complaint_number": "999", "date_entered": "04/01/2026", "complaint_category": "05"})
        warnings, _ = run(self.pull, AS_OF)
        self.assertEqual(len(by_rule(warnings, "adjacent_protection_no_follow_up")), 1)

    def test_no_gap_before_21_days_have_passed(self):
        warnings, checks = run(self.pull, date(2026, 4, 5))
        self.assertEqual(by_rule(warnings, "adjacent_protection_no_follow_up"), [])
        self.assertEqual(checks["adjacent_protection_no_follow_up"].status, "ok")

    def test_records_on_or_after_the_as_of_day_are_not_knowable(self):
        warnings, _ = run(self.pull, date(2026, 4, 23))
        self.assertEqual(by_rule(warnings, "stop_work_then_work_continued"), [])

    def test_an_earlier_stop_work_record_is_cited_as_evidence(self):
        self.add("dob_violations", {"isn_dob_bis_viol": "777", "issue_date": "20260321",
                                    "description": "FULL STOP WORK ORDER ISSUED"})
        warnings, _ = run(self.pull, AS_OF)
        [warning] = by_rule(warnings, "stop_work_then_work_continued")
        self.assertEqual(warning.evidence_record_ids, ["dob_violations:777", "ecb_violations:39553409Z"])
        self.assertIn("The order appears earlier in DOB violation 777 (2026-03-21)", warning.explanation)

    def test_a_failed_dataset_is_an_error_never_a_clean_check(self):
        self.pull["touching_lots"][0]["datasets"]["ecb_violations"] = {"status": "error", "error": "HTTP 500", "records": []}
        _, checks = run(self.pull, AS_OF)
        check = checks["adjacent_protection_no_follow_up"]
        self.assertEqual(check.status, "error")
        self.assertIn("couldn't load", check.detail)

    def test_housing_violations_are_never_used(self):
        self.pull["site"]["datasets"]["hpd_violations"]["records"].append(
            {"violationid": "1", "inspectiondate": "2026-04-01T00:00:00.000", "novdescription": "ADJACENT BUILDING"})
        warnings, _ = run(self.pull, AS_OF)
        self.assertEqual(len(by_rule(warnings, "adjacent_protection_no_follow_up")), 1)


class WarningsApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_real_route_serves_the_cached_site(self):
        response = self.client.get(f"/api/sites/{BEDFORD}/warnings?as_of=2026-06-01")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.headers.get(FIXTURE_HEADER))
        self.assertEqual([w["rule_id"] for w in response.json()],
                         ["stop_work_then_work_continued", "adjacent_protection_no_follow_up"])

    def test_checks_route(self):
        response = self.client.get(f"/api/sites/{BEDFORD}/warnings/checks?as_of=2026-06-01")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 4)

    def test_bad_input_is_rejected(self):
        self.assertEqual(self.client.get("/api/sites/123/warnings").status_code, 422)
        self.assertEqual(self.client.get(f"/api/sites/{BEDFORD}/warnings?as_of=June").status_code, 422)

    def test_an_unloadable_site_is_503_never_an_empty_list(self):
        with mock.patch("early_warning.api.load_site", side_effect=SiteUnavailable("offline")):
            response = self.client.get("/api/sites/1000010001/warnings")
        self.assertEqual(response.status_code, 503)


def square(x: float, y: float, size: float = 0.0001) -> dict:
    return {"type": "Polygon", "coordinates": [[[x, y], [x + size, y], [x + size, y + size], [x, y + size], [x, y]]]}


class Geometry(unittest.TestCase):
    def test_touching_and_apart(self):
        self.assertTrue(geometry.near(square(-73.95, 40.63), square(-73.9499, 40.63), 0.5))
        self.assertFalse(geometry.near(square(-73.95, 40.63), square(-73.9497, 40.63), 0.5))

    def test_shared_edge_length(self):
        # The shared side is about 11 m; the 1 m tolerance also catches up to 1 m of each corner's other edge.
        shared = geometry.shared_edge_m(square(-73.9499, 40.63), square(-73.95, 40.63), 1.0)
        self.assertTrue(10.5 <= shared <= 13.5, shared)


class Watchlist(unittest.TestCase):
    def fake_query(self, dataset_id, params):
        site, neighbor, far = "3052110074", "3052110073", "3052110010"
        rows = {
            watchlist.FILINGS: [
                {"job_filing_number": "B01330433-S3", "bbl": site, "filing_status": "Permit Entire",
                 "first_permit_date": "2026-09-09T00:00:00.000", "house_no": "2625", "street_name": "BEDFORD   AVENUE",
                 "latitude": "40.6391", "longitude": "-73.9538", "earth_work_work_type_": "YES",
                 "foundation_work_type_": "YES", "support_of_excavation_work_type_": "No"},
                {"job_filing_number": "B000-I1", "bbl": far, "filing_status": "LOC Issued",
                 "first_permit_date": "2026-09-09T00:00:00.000", "latitude": "40.6", "longitude": "-73.9",
                 "earth_work_work_type_": "YES"},
            ],
            watchlist.TAX_LOT_POLYGONS: [
                {"bbl": site, "the_geom": square(-73.9500, 40.6390)},
                {"bbl": neighbor, "the_geom": square(-73.9499, 40.6390)},
                {"bbl": far, "the_geom": square(-73.9490, 40.6390)},
            ],
            watchlist.PLUTO: [{"bbl": f"{neighbor}.00000000", "address": "1321 FLATBUSH AVENUE", "yearbuilt": "1930",
                               "numfloors": "3"}],
            watchlist.BUILDING_FOOTPRINTS: [{"base_bbl": neighbor, "bin": "3120364",
                                             "the_geom": square(-73.9499, 40.6390, 0.00008)}],
        }[dataset_id]
        return rows, "https://example.test"

    def test_build_flags_earth_work_next_to_an_old_attached_building(self):
        with mock.patch("data_pull.soda_client.query", side_effect=self.fake_query):
            result, failures = watchlist.build(date(2026, 11, 14))
        self.assertEqual(failures, [])
        self.assertEqual(result.layer.status, "ok")
        [feature] = result.features
        props = feature.properties
        self.assertEqual((props.bbl, props.record_id, props.severity), ("3052110074", "B01330433-S3", 0))
        self.assertIn("1321 Flatbush Avenue (built 1930, 3 floors)", props.summary)
        self.assertEqual(props.title, "Active earth work at 2625 Bedford Avenue")

    def test_a_failed_filings_query_is_an_error_layer(self):
        from data_pull.soda_client import SodaQueryError
        with mock.patch("data_pull.soda_client.query", side_effect=SodaQueryError("w9ak-ipjd: HTTP 500")):
            result, _ = watchlist.build(date(2026, 11, 14))
        self.assertEqual(result.layer.status, "error")
        self.assertIsNone(result.layer.feature_count)

    def test_the_committed_layer_matches_the_contract_and_names_no_one(self):
        path = ROOT / "data" / "layers" / "watchlist.geojson"
        data = json.loads(path.read_text())
        LayerFeatureCollection.model_validate(data)
        self.assertEqual(data["layer"]["feature_count"], len(data["features"]))
        text = path.read_text().lower()
        for word in ("owner", "applicant", "contractor", "permittee"):
            self.assertNotIn(f'"{word}', text)


if __name__ == "__main__":
    unittest.main()
