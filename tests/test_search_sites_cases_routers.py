"""The search, sites and cases routes. GeoSearch is replaced by a fake: no test reaches the network."""

import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from fastapi.testclient import TestClient

import actions as actions_module
from api.main import app
from api.routers.cases_router import load_cases
from api.routers.layers_router import load_layer_catalog
from api.routers.router_data import DataUnavailable, data_root
from api.routers.sites_router import load_site_part
from api.routers.search_router import MAX_RESULTS, geosearch_fetcher
from api.stubs import FIXTURE_HEADER, fixture

BBL = "3052110074"


# Real GeoSearch values (contracts/fixtures/search_results.json); 2625 Bedford's BIN really is the 3000000 placeholder.
def match(label="1321 FLATBUSH AVENUE, Brooklyn, NY, USA", bbl="3052110073", bin_number="3120364",
          coordinates=(-73.953841, 40.638989)):
    return {"geometry": {"type": "Point", "coordinates": list(coordinates)},
            "properties": {"label": label, "addendum": {"pad": {"bbl": bbl, "bin": bin_number}}}}


class SearchRouterTests(unittest.TestCase):
    def setUp(self):
        self.asked, self.answer = [], {"features": []}

        def fake(text):
            self.asked.append(text)
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer

        app.dependency_overrides[geosearch_fetcher] = lambda: fake
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(geosearch_fetcher, None)

    def test_matches_with_a_tax_lot_come_back_as_geosearch_labelled_them(self):
        bedford = match(label="2625 BEDFORD AVENUE, Brooklyn, NY, USA", bbl=BBL, bin_number="3000000",
                        coordinates=(-73.95381, 40.63915))
        self.answer = {"features": [match(), bedford, match(bbl=""),
                                    match(bbl="3052110074\n"), match(coordinates=("x", 40.6)), "not a feature",
                                    *[match(label=f"extra {n}") for n in range(MAX_RESULTS)]]}
        results = self.client.get("/api/search", params={"q": "  2625 bedford  "}).json()
        self.assertEqual(self.asked, ["2625 bedford"])
        self.assertEqual(results[0], {"label": "1321 FLATBUSH AVENUE, Brooklyn, NY, USA", "bbl": "3052110073",
                                      "bin": "3120364", "lat": 40.638989, "lon": -73.953841})
        self.assertEqual((results[1]["bbl"], results[1]["bin"]), (BBL, None), "a placeholder BIN is no building")
        self.assertEqual(len(results), 2, "only the first five matches are read, and only those with a lot and a point")

    def test_a_failed_search_is_an_error_never_an_empty_list(self):
        for failure in (urllib.error.URLError("down"), TimeoutError(), ValueError("not json"), {"error": "x"}, ["x"]):
            self.answer = failure
            self.assertEqual(self.client.get("/api/search?q=bedford").status_code, 502, failure)
        self.answer = {"features": []}
        self.assertEqual(self.client.get("/api/search?q=bedford").json(), [], "GeoSearch answered and found nothing")

    def test_an_empty_or_long_query_is_refused_before_geosearch(self):
        for query in ("", "   ", "x" * 201):
            self.assertEqual(self.client.get("/api/search", params={"q": query}).status_code, 422)
        self.assertEqual(self.asked, [])


class SitesRouterTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_until_an_owner_lands_the_labelled_sample_answers(self):
        for route in ("profile", "similar", "warnings", "pattern", "actions"):
            response = self.client.get(f"/api/sites/{BBL}/{route}")
            self.assertEqual((response.status_code, response.headers.get(FIXTURE_HEADER)), (200, "true"), route)

    def test_an_owner_function_answers_once_it_is_defined(self):
        calls = []

        def actions_for(bbl, stage):
            calls.append((bbl, stage))
            return fixture("actions")[:1]

        with mock.patch.object(actions_module, "actions_for", actions_for, create=True):
            response = self.client.get(f"/api/sites/{BBL}/actions?stage=design")
            self.assertEqual((response.status_code, response.headers.get(FIXTURE_HEADER)), (200, None))
            self.assertEqual(calls, [(BBL, "design")])
        with mock.patch.object(actions_module, "actions_for", lambda bbl, stage: [{"id": "x"}], create=True):
            self.assertEqual(self.client.get(f"/api/sites/{BBL}/actions").status_code, 500, "off-contract is never served")

    def test_bad_bbls_and_options_are_refused(self):
        for path in ("/api/sites/305211007/profile", "/api/sites/6052110074/profile", "/api/sites/3052110074%0A/profile",
                     f"/api/sites/{BBL}/profile?stage=someday", f"/api/sites/{BBL}/profile?as_of=2026-13-01",
                     f"/api/sites/{BBL}/similar?severity_min=4", f"/api/sites/{BBL}/similar?hazard=rumor"):
            self.assertEqual(self.client.get(path).status_code, 422, path)


class CasesRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "data"
        (self.root / "cases").mkdir(parents=True)
        app.dependency_overrides[data_root] = lambda: self.root
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        app.dependency_overrides.pop(data_root, None)
        self.tmp.cleanup()

    def test_the_library_file_is_served_and_the_sample_until_it_lands(self):
        self.assertEqual(self.client.get("/api/cases").headers.get(FIXTURE_HEADER), "true")
        case = {**fixture("cases")[0], "id": "case-from-the-library"}
        (self.root / "cases" / "cases.json").write_text(json.dumps([case]))
        listed = self.client.get("/api/cases")
        self.assertEqual(([c["id"] for c in listed.json()], listed.headers.get(FIXTURE_HEADER)), (["case-from-the-library"], None))
        self.assertEqual(self.client.get("/api/cases/case-from-the-library").json()["id"], "case-from-the-library")
        self.assertEqual(self.client.get(f"/api/cases/{fixture('cases')[0]['id']}").status_code, 404)

    def test_a_case_off_the_contract_breaks_the_file_loudly(self):
        blamed = {**fixture("cases")[0], "cause_status": "blamed"}
        (self.root / "cases" / "cases.json").write_text(json.dumps([blamed]))
        broken = self.client.get("/api/cases")
        self.assertEqual(broken.status_code, 500)
        self.assertIn("cases.json does not match its contract", broken.text)


class PythonLoaderTests(unittest.TestCase):
    """The calls the chat uses: a failure is DataUnavailable, never an empty answer; the sample says it is one."""

    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)

    def patched(self, function):
        return mock.patch.object(actions_module, "actions_for", function, create=True)

    def test_the_sample_says_it_is_the_sample(self):
        loaded = load_site_part("actions", BBL, as_of="2026-06-01")
        self.assertTrue(loaded.sample)
        self.assertEqual(loaded.data[0].id, fixture("actions")[0]["id"])

    def test_an_owner_gets_only_its_own_options_and_an_empty_answer_stays_real(self):
        with self.patched(lambda bbl, stage: []):
            loaded = load_site_part("actions", BBL, job_type="alteration", stage="design", as_of="2026-06-01")
        self.assertEqual((loaded.data, loaded.sample), ([], False))

    def test_a_failing_owner_is_unavailable_never_empty(self):
        def broken(bbl, stage):
            raise RuntimeError("records pull timed out")

        def not_found(bbl, stage):
            raise HTTPException(404, "no such lot")

        for owner, status in ((broken, 500), (not_found, 404), (lambda bbl, stage: [{"id": "x"}], 500)):
            with self.patched(owner):
                with self.assertRaises(DataUnavailable) as failed:
                    load_site_part("actions", BBL)
                self.assertEqual(failed.exception.status_code, status)
                self.assertEqual(self.client.get(f"/api/sites/{BBL}/actions").status_code, status)

    def test_bad_input_is_refused_as_on_the_route(self):
        for call in (lambda: load_site_part("profile", BBL, stage="someday"),
                     lambda: load_site_part("similar", BBL, severity_min=True),
                     lambda: load_site_part("profile", "3052110074\n")):
            with self.assertRaises(HTTPException) as refused:
                call()
            self.assertEqual(refused.exception.status_code, 422)

    def test_layers_and_cases_load_the_same_way(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            (root / "cases").mkdir(parents=True)
            self.assertTrue(load_layer_catalog(root).sample)
            self.assertTrue(load_cases(root).sample)
            (root / "cases" / "cases.json").write_text("[{}]")
            with self.assertRaises(DataUnavailable):
                load_cases(root)


if __name__ == "__main__":
    unittest.main()
