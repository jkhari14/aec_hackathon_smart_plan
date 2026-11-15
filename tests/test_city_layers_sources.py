"""PR 16's sources: FEMA, 311 flooding and state remediation layers, the site lookups and the refresh.

Offline. Rows are shaped like the live sources' answers (checked 2026-11-14); nothing calls the network.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock

from city_layers import (
    arcgis_rows, build_layers, fema_flood_zones, flooding_complaints, refresh_layers, remediation_sites,
    site_context, source_rows,
)
from city_layers.layer_file import LayerPullError
from data_pull import soda_client

PULLED_ON = date(2026, 11, 14)
HERO = (-73.953869, 40.638718)
SQUARE = [[-73.98, 40.57], [-73.97, 40.57], [-73.97, 40.58], [-73.98, 40.58], [-73.98, 40.57]]


def props(features: list[dict]) -> list[dict]:
    return [f["properties"] for f in features]


class AnotherPortal(unittest.TestCase):
    def test_the_client_can_read_another_socrata_portal(self):
        self.assertTrue(soda_client.build_url("abcd-1234", {"limit": "1"}).startswith("https://data.cityofnewyork.us/resource/abcd-1234.json?"))
        url = soda_client.build_url("c6ci-rzpg", {"limit": "1"}, "https://data.ny.gov/resource")
        self.assertEqual(url, "https://data.ny.gov/resource/c6ci-rzpg.json?%24limit=1")

    def test_the_city_token_is_sent_to_the_city_portal_only(self):
        sent = []

        class Answer:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args): return b"[]"

        def urlopen(request, timeout):
            sent.append(dict(request.header_items()))
            return Answer()

        with mock.patch.dict(os.environ, {"SODA_APP_TOKEN": "secret"}), mock.patch("urllib.request.urlopen", urlopen):
            soda_client.query("abcd-1234", {})
            soda_client.query("c6ci-rzpg", {}, "https://data.ny.gov/resource")
        self.assertEqual(sent[0].get("X-app-token"), "secret")
        self.assertNotIn("X-app-token", sent[1])

    def test_paging_passes_the_portal_through(self):
        calls = []

        def query(dataset_id, params, base=None):
            calls.append(base)
            return [], "url"

        with mock.patch.object(soda_client, "query", query):
            source_rows.all_rows("c6ci-rzpg", {}, portal="data.ny.gov")
        self.assertEqual(calls, ["https://data.ny.gov/resource"])


class ArcgisRows(unittest.TestCase):
    def test_features_are_read_a_page_at_a_time(self):
        pages = [{"features": [{"n": 1}, {"n": 2}], "exceededTransferLimit": True},
                 {"features": [{"n": 3}], "properties": {"exceededTransferLimit": True}}, {"features": [{"n": 4}]}]
        asked = []

        def get(url, params):
            asked.append(params["resultOffset"])
            return pages[len(asked) - 1]

        with mock.patch.object(arcgis_rows, "_get", get):
            features, capped = arcgis_rows.all_features("https://example.org/L/28", "1=1", "A", 0.0001, 5)
        self.assertEqual((len(features), capped, asked), (4, False, ["0", "2", "3"]))

    def test_reading_stops_at_the_cap_and_says_so(self):
        with mock.patch.object(arcgis_rows, "_get", lambda url, params: {"features": [{}] * int(params["resultRecordCount"]), "exceededTransferLimit": True}):
            features, capped = arcgis_rows.all_features("https://example.org/L/28", "1=1", "A", 0.0001, 5, max_features=250)
        self.assertEqual((len(features), capped), (250, True))

    def test_an_error_inside_a_200_answer_is_a_failed_pull(self):
        class Answer:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args): return b'{"error": {"code": 400, "message": "Invalid URL"}}'

        with mock.patch("urllib.request.urlopen", lambda url, timeout: Answer()):
            with self.assertRaises(LayerPullError):
                arcgis_rows.all_features("https://example.org/L/28", "1=1", "A", 0.0001, 5)
            with self.assertRaises(LayerPullError):
                arcgis_rows.attributes_at("https://example.org/L/28", *HERO, "A")


class FemaFloodZones(unittest.TestCase):
    ROWS = [
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [SQUARE]},
         "properties": {"FLD_AR_ID": "360497_5", "FLD_ZONE": "AE", "ZONE_SUBTY": None, "STATIC_BFE": 14}},
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [SQUARE]},
         "properties": {"FLD_AR_ID": "360497_9", "FLD_ZONE": "AE", "ZONE_SUBTY": "FLOODWAY", "STATIC_BFE": -9999}},
        {"type": "Feature", "geometry": None, "properties": {"FLD_AR_ID": "360497_10", "FLD_ZONE": "VE"}},
    ]

    def test_zones_are_flood_context_with_no_date(self):
        features, notes = fema_flood_zones.features_from_rows(self.ROWS)
        first, floodway = props(features)
        self.assertEqual((first["hazard"], first["severity"], first["date"], first["record_id"]), ("flood", 0, None, "360497_5"))
        self.assertEqual(first["title"], "FEMA flood zone AE")
        self.assertEqual(first["summary"], "A special flood hazard area on FEMA's effective flood map. Base flood elevation as recorded: 14 ft.")
        self.assertEqual(floodway["title"], "FEMA flood zone AE (floodway)")
        self.assertEqual(features[0]["geometry"]["type"], "MultiPolygon")
        self.assertEqual(notes, ["Not on the map: 1 of 3 areas (too small to draw at this detail, or no id)."])

    def test_femas_none_elevation_is_never_shown_as_a_number(self):
        self.assertNotIn("9999", props(fema_flood_zones.features_from_rows(self.ROWS)[0])[1]["summary"])
        self.assertEqual(fema_flood_zones.elevation_text(-9999.0), "")
        self.assertEqual(fema_flood_zones.elevation_text(None), "")
        self.assertEqual(fema_flood_zones.elevation_text(10.5), " Base flood elevation as recorded: 10.5 ft.")


class FloodingComplaints(unittest.TestCase):
    ROWS = [
        {"unique_key": "69878533", "created_date": "2026-07-28T21:45:00.000", "descriptor": "Street Flooding (SJ)",
         "incident_address": "1425 KINGS HIGHWAY", "borough": "BROOKLYN", "bbl": "3067770029",
         "latitude": "40.608508194435615", "longitude": "-73.9588815646739"},
        {"unique_key": "70000001", "created_date": "2026-09-01T08:00:00.000", "descriptor": "Backup", "borough": "Unspecified",
         "latitude": "40.82", "longitude": "-73.89"},
        {"unique_key": "70000002", "created_date": "2026-09-01T08:00:00.000", "descriptor": "Flooding on Highway", "borough": "QUEENS"},
        {"unique_key": "70000003", "descriptor": "Catch Basin Clogged/Flooding (Use Comments) (SC)", "latitude": "40.7", "longitude": "-73.9"},
    ]

    def test_the_query_covers_the_last_twelve_months_and_both_sets_of_names(self):
        where = flooding_complaints.where(PULLED_ON)
        self.assertTrue(where.startswith("agency='DEP' AND descriptor in ('Street Flooding (SJ)','Flooding on Street',"))
        self.assertTrue(where.endswith("AND created_date >= '2025-11-14T00:00:00'"))

    def test_reports_are_signals_named_by_kind(self):
        features, notes = flooding_complaints.features_from_rows(self.ROWS)
        street, backup = props(features)
        self.assertEqual((street["title"], street["severity"], street["hazard"], street["date"]),
                         ("311 report: street flooding", 0, "flood", "2026-07-28"))
        self.assertEqual(street["summary"], "1425 KINGS HIGHWAY, Brooklyn. Reported to 311 and routed to DEP.")
        self.assertEqual((street["bbl"], street["record_id"]), ("3067770029", "69878533"))
        self.assertEqual((backup["title"], backup["summary"]), ("311 report: sewer backup", "Address not recorded. Reported to 311 and routed to DEP."))
        # The highway request has no coordinates; the clogged catch basin is not a flooding kind at all.
        self.assertEqual(notes, ["Not on the map: 1 of 3 requests (no usable coordinates; highway requests rarely have them)."])


class RemediationSites(unittest.TestCase):
    ROWS = [
        {"program_number": "224142", "program_type": "HW", "siteclass": "P", "address1": "Ingraham Street", "county": "Kings",
         "latitude": "40.707155254", "longitude": "-73.930085330", "contaminants": "trichloroethene (TCE)"},
        {"program_number": "224142", "program_type": "HW", "siteclass": "P", "address1": "Ingraham Street", "county": "Kings",
         "latitude": "40.707155254", "longitude": "-73.930085330", "contaminants": "lead"},
        {"program_number": "C224999", "program_type": "ZZ", "siteclass": "77", "county": "Queens",
         "latitude": "40.72", "longitude": "-73.85"},
        {"program_number": "203002", "program_type": "BCP", "siteclass": "N", "county": "Bronx"},
    ] + [{"program_number": "231000", "program_type": "VCP", "siteclass": "C", "address1": "1 Main Street", "county": "New York",
          "latitude": "40.71", "longitude": "-74.0", "contaminants": f"substance {n}"} for n in range(9)]

    def test_a_site_appears_once_with_its_contaminants(self):
        features, notes = remediation_sites.features_from_rows(self.ROWS)
        self.assertEqual([p["record_id"] for p in props(features)], ["224142", "C224999", "231000"])
        site = props(features)[0]
        self.assertEqual(site["title"], "Remediation site: State Superfund Program")
        self.assertEqual(site["summary"], "Ingraham Street, Brooklyn. DEC site 224142, class P: preliminary information indicates "
                                          "the site may have contamination. Contaminants listed: lead; trichloroethene (TCE).")
        self.assertEqual((site["hazard"], site["severity"], site["date"], site["bbl"]), ("contamination", 0, None, None))
        self.assertEqual(notes, ["Not on the map: 1 of 4 sites (no usable coordinates)."])

    def test_a_code_the_dataset_does_not_define_is_shown_as_the_code(self):
        unknown = props(remediation_sites.features_from_rows(self.ROWS)[0])[1]
        self.assertEqual(unknown["title"], "Remediation site: program ZZ")
        self.assertEqual(unknown["summary"], "Queens. DEC site C224999, class 77. No contaminants listed.")

    def test_a_long_contaminant_list_is_cut_with_a_count(self):
        summary = props(remediation_sites.features_from_rows(self.ROWS)[0])[2]["summary"]
        self.assertIn("substance 5; and 3 more.", summary)

    def test_it_reads_the_five_counties_from_the_state_portal_without_names(self):
        self.assertEqual(remediation_sites.where(), "county in ('New York','Bronx','Kings','Queens','Richmond')")
        self.assertEqual(remediation_sites.PORTAL, "data.ny.gov")
        self.assertFalse(any(word in remediation_sites.SELECT for word in ("owner", "operator", "disposal", "facility")))


class SiteContext(unittest.TestCase):
    def test_a_point_outside_the_city_is_refused(self):
        with self.assertRaises(ValueError):
            site_context.fema_zone(0, 0)
        with self.assertRaises(ValueError):
            site_context.soil_unit(-73.95, 45.0)

    def test_fema_zone_and_its_none_elevation(self):
        zone = [{"FLD_ZONE": "X", "ZONE_SUBTY": "AREA OF MINIMAL FLOOD HAZARD", "SFHA_TF": "F", "STATIC_BFE": -9999.0}]
        with mock.patch.object(arcgis_rows, "attributes_at", lambda *a: zone):
            answer = site_context.fema_zone(*HERO)
        self.assertEqual((answer["status"], answer["value"]), ("ok", "X"))
        self.assertEqual(answer["detail"], {"subtype": "AREA OF MINIMAL FLOOD HAZARD", "special_flood_hazard_area": False,
                                            "base_flood_elevation_ft": None})
        coastal = [{"FLD_ZONE": "AE", "ZONE_SUBTY": None, "SFHA_TF": "T", "STATIC_BFE": 10.0}]
        with mock.patch.object(arcgis_rows, "attributes_at", lambda *a: coastal):
            self.assertEqual(site_context.fema_zone(*HERO)["detail"]["base_flood_elevation_ft"], 10.0)
        with mock.patch.object(arcgis_rows, "attributes_at", lambda *a: []):
            self.assertEqual((site_context.fema_zone(*HERO)["status"], site_context.fema_zone(*HERO)["value"]), ("ok", None))

    def test_a_failed_lookup_is_an_error_not_a_no(self):
        def fail(*args, **kwargs):
            raise LayerPullError("service down")

        def soda_fail(*args, **kwargs):
            raise soda_client.SodaQueryError("5xsi-dfpx: HTTP 503")

        with mock.patch.object(arcgis_rows, "attributes_at", fail), mock.patch.object(soda_client, "query", soda_fail), \
                mock.patch.object(site_context, "_get_json", fail):
            answers = [site_context.fema_zone(*HERO), site_context.sandy_flooded(*HERO), site_context.soil_unit(*HERO),
                       site_context.e_designation("3052110073"), site_context.weather(*HERO, PULLED_ON, PULLED_ON)]
            profile = site_context.site_context(*HERO, "3052110073")
        self.assertEqual([a["status"] for a in answers], ["error"] * 5)
        self.assertTrue(all(a["value"] is None and a["reason"] for a in answers))
        self.assertEqual(profile["flood"], {"fema_zone": None, "stormwater": None, "sandy_inundation": None})  # unknown, not False
        self.assertEqual([s["status"] for s in profile["samples"]], ["error", "error", "skipped", "error", "skipped", "error"])

    def test_sandy_is_asked_of_the_full_detail_polygons(self):
        asked = []

        def query(dataset_id, params):
            asked.append((dataset_id, params["where"]))
            return [{"n": "1"}], "url"

        with mock.patch.object(soda_client, "query", query):
            self.assertIs(site_context.sandy_flooded(*HERO)["value"], True)
        self.assertEqual(asked, [("5xsi-dfpx", "intersects(the_geom, 'POINT (-73.953869 40.638718)')")])
        with mock.patch.object(soda_client, "query", lambda d, p: ([{"n": "0"}], "url")):
            self.assertIs(site_context.sandy_flooded(*HERO)["value"], False)

    def test_e_designation_lists_every_kind_on_the_lot(self):
        rows = [{"enumber": "E-905", "effective_date": "2026-10-13T00:00:00.000", "hazmat_code": True, "air_code": True,
                 "noise_code": False, "description": "as recorded"}, {"enumber": "E-12", "noise_code": True}]
        with mock.patch.object(soda_client, "query", lambda d, p: (rows, "url")):
            answer = site_context.e_designation("3024030001")
        self.assertEqual(answer["value"], "E-905: hazardous materials, air quality; E-12: noise")
        self.assertEqual(answer["detail"]["designations"][0]["effective"], "2026-10-13")
        with mock.patch.object(soda_client, "query", lambda d, p: ([], "url")):
            self.assertEqual((site_context.e_designation("3024030001")["status"], site_context.e_designation("3024030001")["value"]), ("ok", None))
        with self.assertRaises(ValueError):
            site_context.e_designation("3024030001 OR 1=1")

    def test_soil_unit(self):
        table = {"Table": [["mukey", "musym", "muname"], ["2518852", "UoA", "Urban land, outwash substratum, 0 to 3 percent slopes"]]}
        with mock.patch.object(site_context, "_get_json", lambda url, body=None: table):
            answer = site_context.soil_unit(*HERO)
        self.assertEqual(answer["value"], "Urban land, outwash substratum, 0 to 3 percent slopes")
        self.assertEqual(answer["detail"], {"map_unit_key": "2518852", "symbol": "UoA"})
        with mock.patch.object(site_context, "_get_json", lambda url, body=None: {}):
            self.assertEqual((site_context.soil_unit(*HERO)["status"], site_context.soil_unit(*HERO)["value"]), ("ok", None))

    def test_weather_picks_out_heavy_rain_and_freeze_thaw_days(self):
        answer = {"latitude": 40.667835, "longitude": -73.93768, "daily": {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "precipitation_sum": [25.0, 25.1, None, 0.0],
            "temperature_2m_max": [5.0, 2.0, -1.0, 0.0], "temperature_2m_min": [1.0, -3.0, -6.0, -4.0]}}
        with mock.patch.object(site_context, "_get_json", lambda url, body=None: answer):
            found = site_context.weather(*HERO, date(2026, 1, 1), date(2026, 1, 4))
        self.assertEqual(found["detail"]["heavy_rain_days"], ["2026-01-02"])      # more than 25 mm, not 25 exactly
        self.assertEqual(found["detail"]["freeze_thaw_days"], ["2026-01-02"])     # below freezing and back above it
        self.assertEqual(found["detail"]["grid_cell"], {"lat": 40.667835, "lon": -73.93768})
        self.assertEqual(len(found["value"]), 4)

    def test_what_is_not_read_yet_says_so(self):
        for answer in (site_context.bedrock_depth(*HERO), site_context.stormwater_flood(*HERO)):
            self.assertEqual((answer["status"], answer["value"]), ("skipped", None))
            self.assertTrue(answer["reason"])


class Refresh(unittest.TestCase):
    def test_a_refresh_logs_its_outcomes_and_keeps_the_last_runs(self):
        outcomes = iter([{"a": "ok", "b": "kept"}, {"a": "ok", "b": "ok"}])
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(build_layers, "build", lambda ids, d, day: next(outcomes)), \
                mock.patch.object(refresh_layers, "RUNS_KEPT", 2):
            directory = Path(folder)
            first = refresh_layers.refresh(directory, datetime(2026, 11, 15, 5, 0).astimezone())
            self.assertEqual(first["failed"], ["b"])
            second = refresh_layers.refresh(directory, datetime(2026, 11, 15, 11, 0).astimezone())
            self.assertEqual(second["failed"], [])
            (directory / refresh_layers.LOG).write_text(json.dumps({"runs": [second, first, first]}))
            outcomes = iter([{"a": "ok"}])
            refresh_layers.refresh(directory, datetime(2026, 11, 15, 17, 0).astimezone())
            runs = json.loads((directory / refresh_layers.LOG).read_text())["runs"]
        self.assertEqual(len(runs), 2)
        self.assertTrue(runs[0]["started"].startswith("2026-11-15T17:00:00"))

    def test_a_broken_log_does_not_stop_a_refresh(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(build_layers, "build", lambda ids, d, day: {"a": "ok"}):
            (Path(folder) / refresh_layers.LOG).write_text("not json")
            refresh_layers.refresh(Path(folder))
            self.assertEqual(len(json.loads((Path(folder) / refresh_layers.LOG).read_text())["runs"]), 1)


if __name__ == "__main__":
    unittest.main()
