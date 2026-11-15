"""Site profile and similarity (PR 6), offline: built from the saved 2625 Bedford pull."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.contracts import SiteProfile, SimilarCases
from api.main import app
from site_profile import build_profile, similarity, work_types

REPO = Path(__file__).resolve().parent.parent
BBL = "3052110074"


def bedford_pull() -> dict:
    return json.loads((REPO / "data" / "cache" / "2625-bedford-ave-brooklyn.json").read_text())


class ProfileFromPull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pull = bedford_pull()
        cls.profile = build_profile.build_profile(cls.pull, as_of="2026-06-01")

    def test_validates_against_the_contract(self):
        SiteProfile.model_validate(self.profile)

    def test_lot_and_neighbors(self):
        self.assertEqual(self.profile["lot"]["year_built"], 1933)
        neighbors = {n["bbl"]: n for n in self.profile["neighbors"]}
        self.assertEqual(neighbors["3052110073"]["year_built"], 1930)
        self.assertTrue(neighbors["3052110073"]["attached"])
        self.assertIsNone(neighbors["3052110073"]["shared_wall_ft"], "shared wall length is not in public data")

    def test_signals_are_dated_before_as_of(self):
        for signal in self.profile["signals"]:
            self.assertIsNotNone(signal["date"])
            self.assertLess(signal["date"], "2026-06-01")
        titles = [s["title"] for s in self.profile["signals"]]
        self.assertIn("Protection for adjacent property not provided", titles)
        self.assertIn("Work continued during a stop-work order", titles)
        self.assertFalse(any("COLLAPSE" in s["explanation"] for s in self.profile["signals"]),
                         "the November collapse record is after the as-of day")

    def test_enforcement_comes_before_complaints(self):
        severities = [s["severity"] for s in self.profile["signals"]]
        self.assertEqual(severities, sorted(severities, reverse=True))

    def test_without_as_of_the_later_records_appear(self):
        profile = build_profile.build_profile(self.pull)
        self.assertTrue(any("collapse" in s["title"].lower() for s in profile["signals"]))

    def test_housing_violations_are_never_signals(self):
        pull = copy.deepcopy(self.pull)
        pull["site"]["datasets"]["hpd_violations"] = {"status": "ok", "count": 1, "records": [
            {"violationid": "1", "inspectiondate": "2026-01-01", "novdescription": "STRUCTURAL COLLAPSE UNSAFE"}]}
        profile = build_profile.build_profile(pull, as_of="2026-06-01")
        self.assertFalse(any(s["source_name"].startswith("HPD") for s in profile["signals"]))

    def test_failed_dataset_is_error_not_zero(self):
        pull = copy.deepcopy(self.pull)
        pull["site"]["datasets"]["dob_complaints"] = {"status": "error", "error": "HTTP 500", "records": []}
        statuses = {d["key"]: d for d in build_profile.build_profile(pull)["datasets"]}
        self.assertEqual(statuses["dob_complaints"]["status"], "error")
        self.assertIsNone(statuses["dob_complaints"]["count"])

    def test_unknown_environment_stays_null(self):
        self.assertIsNone(self.profile["soil"])
        self.assertIsNone(self.profile["flood"]["sandy_inundation"])

    def test_no_names_of_people(self):
        text = json.dumps(self.profile).lower()
        for field in ("owner", "applicant", "permittee", "contractor_name"):
            self.assertNotIn(f'"{field}', text)


class SignalTitles(unittest.TestCase):
    """Real ECB wording from 861 Park Avenue (2026): "UNSAFE" on its own is not a structural condition."""

    def title(self, text):
        from site_profile.signals import violation_signals
        lot = {"datasets": {"ecb_violations": {"status": "ok", "records": [
            {"ecb_violation_number": "1", "issue_date": "20260801", "violation_description": text}]}}}
        return violation_signals(lot, None)[0]["title"]

    def test_scaffold_delivery_is_not_structural(self):
        self.assertEqual(self.title("UNSAFE MATERIAL DELIVERY. SCAFFOLD EQUIPMENT STORED ON TOP OF SIDEWALK SHED"),
                         "Scaffold or material handling cited")

    def test_concrete_washout_is_not_structural(self):
        self.assertEqual(self.title("FAILURE TO PERFORM PROPER CONCRETE WASHOUT. CREATING AN UNSAFE CONDITION"),
                         "Concrete washout not handled properly")

    def test_sidewalk_crack_is_not_structural(self):
        self.assertEqual(self.title("PEDESTRIAN WALKWAY NOT MAINTAINED. 3 INCHES CRACK AND UNEVEN SURFACE"),
                         "Pedestrian walkway not kept safe")

    def test_cracked_wall_is_structural(self):
        self.assertEqual(self.title("OBSERVED CRACKS IN THE REAR BEARING WALL"), "Structural condition cited")


class WorkTypes(unittest.TestCase):
    def test_user_job_type_infers_work_types(self):
        job, types, inferred = work_types.resolve([], "new_building")
        self.assertEqual(job, "new_building")
        self.assertIn("excavation", types)
        self.assertTrue(inferred)

    def test_filing_flags_win_when_no_job_type_given(self):
        filings = [{"job_type": "Alteration", "filing_date": "2026-01-02T00:00:00.000",
                    "foundation_work_type_": "YES", "earth_work_work_type_": "NO"}]
        self.assertEqual(work_types.resolve(filings, None), ("alteration", ["foundation"], False))


class Similarity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = build_profile.build_profile(bedford_pull(), as_of="2026-06-01")
        cls.cases, _ = similarity.load_cases(similarity.CASE_FIXTURE)

    def test_ranked_and_explained(self):
        result = similarity.rank(self.profile, self.cases)
        SimilarCases.model_validate(result)
        self.assertTrue(result["results"])
        scores = [r["score"] for r in result["results"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        for r in result["results"]:
            self.assertTrue(r["matched_on"], "every result says why it matched")
            self.assertLessEqual(r["score"], 1)

    def test_earth_work_next_to_old_neighbor_matches(self):
        case = {"id": "c", "bbl": "1000010001", "hazards": ["structural"], "severity": 2, "job_type": "new_building",
                "work_types": ["excavation"], "conditions": {"neighbor_year_built": 1910, "attached": True}}
        found = similarity.compare(self.profile, case)
        joined = " ".join(found["matched_on"])
        self.assertIn("the neighbor at", joined)
        self.assertIn("1900 to 1937", joined)
        self.assertIn("attached", joined)
        self.assertIn("earth work", joined)
        # The borough is not a structural difference, so it is never listed as one.
        self.assertFalse(any("Manhattan" in d for d in found["differs_on"]))

    def test_near_miss_in_age_is_half_credit_not_a_difference(self):
        here = {"label": "the neighbor", "year_built": 1931, "era": "built 1900 to 1937 (before the 1938 code)",
                "floors": None, "floors_band": None, "wall_system": None, "attached": None}
        there = {**here, "year_built": 1940, "era": "built 1938 to 1967 (1938 code)"}
        found = similarity.compare_buildings(here, there)
        self.assertEqual(found["near"], ["era"])
        self.assertEqual(found["differs"], [])
        self.assertAlmostEqual(found["score"], similarity.WEIGHTS["building_era"] / 2)

    def test_unreported_condition_is_not_a_difference(self):
        case = {"id": "c", "hazards": ["fire"], "severity": 1, "work_types": [], "conditions": {}}
        self.assertEqual(similarity.compare(self.profile, case)["differs_on"], [])

    def test_filters(self):
        result = similarity.rank(self.profile, self.cases, hazard="flood")
        for r in result["results"]:
            self.assertIn("flood", r["case"]["hazards"])
        result = similarity.rank(self.profile, self.cases, severity_min=3)
        for r in result["results"]:
            self.assertGreaterEqual(r["case"]["severity"], 3)

    def test_incident_feature_becomes_a_case_without_a_cause(self):
        feature = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-73.95, 40.64]},
                   "properties": {"id": "inc-1", "layer_id": "construction_incidents", "hazard": "construction_safety",
                                  "severity": 2, "date": "2025-02-01", "title": "Excavation/Soil Work",
                                  "summary": "Worker injured", "source_name": "DOB Construction-Related Incidents",
                                  "source_url": "https://data.cityofnewyork.us/d/bf97-mjsy", "bbl": None,
                                  "record_id": "1"}}
        case = similarity.incident_to_case(feature)
        self.assertEqual(case["cause_status"], "unknown")
        self.assertIsNone(case["cause_as_reported"])
        self.assertIn("excavation", case["work_types"])


class Routes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_profile_route_is_real(self):
        response = self.client.get(f"/api/sites/{BBL}/profile?as_of=2026-06-01&stage=construction")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.headers.get("X-ForeSite-Fixture"))
        self.assertEqual(response.json()["stage"], "construction")

    def test_similar_route(self):
        response = self.client.get(f"/api/sites/{BBL}/similar?severity_min=1")
        self.assertEqual(response.status_code, 200, response.text)
        SimilarCases.model_validate(response.json())

    def test_bad_input(self):
        self.assertEqual(self.client.get("/api/sites/123/profile").status_code, 422)
        self.assertEqual(self.client.get(f"/api/sites/{BBL}/profile?as_of=June").status_code, 422)
        self.assertEqual(self.client.get(f"/api/sites/{BBL}/similar?severity_min=9").status_code, 422)


if __name__ == "__main__":
    unittest.main()
