"""The city layers: each source's tagging rules, the paging and lookups, the build, and the written files.

Offline. Rows are shaped like the live datasets' (checked 2026-11-14); nothing here calls the network.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import get_args
from unittest import mock

from api import contracts
from city_layers import (
    build_layers, construction_incidents, e_designations, fdny_vacates, layer_file, sandy_inundation,
    source_rows, structural_complaints, unsafe_facades, vacate_orders, work_types,
)
from city_layers.layer_file import LayerInfo, LayerPullError, Pulled
from data_pull import soda_client

PULLED_ON = date(2026, 11, 14)
SITE = "3052110074"
NEXT_DOOR = "3052110073"
POINTS = {SITE: (-73.953811, 40.639146), NEXT_DOOR: (-73.953786, 40.638984)}
INFO = LayerInfo("test_layer", "Test layer", "A layer for tests.", "structural", "Test source",
                 "https://example.org/source", True)


def props(features: list[dict]) -> list[dict]:
    return [f["properties"] for f in features]


def a_feature(key: str = "1", **overrides) -> dict:
    fields = {"hazard": "structural", "severity": 0, "date": "2026-01-02", "title": "t", "summary": "s"}
    return layer_file.feature(INFO, key, layer_file.point_geometry(POINTS[SITE]), **{**fields, **overrides})


class LayerFileShape(unittest.TestCase):
    def test_hazards_and_severities_are_the_contracts(self):
        self.assertEqual(layer_file.HAZARDS, get_args(contracts.Hazard))
        self.assertEqual(layer_file.SEVERITIES, get_args(contracts.Severity))

    def test_a_feature_refuses_a_hazard_or_severity_off_the_list(self):
        with self.assertRaises(ValueError):
            a_feature(hazard="housing")
        with self.assertRaises(ValueError):
            a_feature(severity=4)

    def test_bbl_reading(self):
        self.assertEqual(layer_file.clean_bbl("3052110074.00000000"), SITE)
        self.assertEqual(layer_file.clean_bbl(3052110074), SITE)
        for bad in (None, "", "305211007", "9052110074", "30521100744", "abc"):
            self.assertIsNone(layer_file.clean_bbl(bad), bad)
        self.assertEqual(layer_file.bbl_from_parts("Brooklyn", "5211", "74"), SITE)
        self.assertEqual(layer_file.bbl_from_parts("BK", "05211", "0074"), SITE)
        self.assertEqual(layer_file.bbl_from_parts("3", "5211", "74"), SITE)
        for parts in (("Brooklyn", "5211", ""), ("Narnia", "5211", "74"), ("Brooklyn", "52x1", "74"), (None, None, None)):
            self.assertIsNone(layer_file.bbl_from_parts(*parts), parts)

    def test_a_point_outside_the_city_is_no_point(self):
        self.assertEqual(layer_file.point("-73.953869", "40.638718"), (-73.953869, 40.638718))
        for lon, lat in ((0, 0), (None, 40.6), ("", ""), (-73.95, 42.0), (-80.0, 40.6), ("x", "y")):
            self.assertIsNone(layer_file.point(lon, lat), (lon, lat))

    def test_dates_are_read_or_left_undated(self):
        self.assertEqual(layer_file.iso_date("2026-11-11T00:00:00.000"), "2026-11-11")
        self.assertEqual(layer_file.iso_date("11/12/2026"), "2026-11-12")
        self.assertIsNone(layer_file.iso_date("sometime"))
        self.assertIsNone(layer_file.iso_date(None))

    def test_a_long_summary_is_clipped(self):
        summary = a_feature(summary="word " * 200)["properties"]["summary"]
        self.assertLessEqual(len(summary), 300)
        self.assertTrue(summary.endswith("…"))

    def test_collection_counts_features_and_says_what_was_left_out(self):
        pulled = Pulled([a_feature("1"), a_feature("2"), a_feature("2")], "2026-11-13", notes=["A note."])
        data = layer_file.collection(INFO, pulled, PULLED_ON)
        self.assertEqual(data["layer"]["feature_count"], 2)
        self.assertEqual(data["layer"]["status"], "ok")
        self.assertEqual(data["layer"]["updated_at"], "2026-11-13")
        self.assertEqual(
            data["layer"]["description"],
            "A layer for tests. A note. Not on the map: 1 of 3 rows (each repeats another row's id). Pulled 2026-11-14.",
        )
        contracts.LayerFeatureCollection.model_validate(data)

    def test_a_capped_pull_is_marked_capped(self):
        data = layer_file.collection(INFO, Pulled([a_feature()], capped=True), PULLED_ON)
        self.assertEqual(data["layer"]["status"], "capped")
        contracts.LayerFeatureCollection.model_validate(data)

    def test_a_failed_pull_is_an_error_with_no_count(self):
        data = layer_file.error_collection(INFO, PULLED_ON)
        self.assertEqual(data["layer"]["status"], "error")
        self.assertIsNone(data["layer"]["feature_count"])
        self.assertEqual(data["features"], [])
        contracts.LayerFeatureCollection.model_validate(data)

    def test_written_files_read_back_the_same_and_build_the_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for layer_id in ("zebra", "alpha", "watchlist"):
                info = LayerInfo(layer_id, layer_id, "d", "flood", "s", "https://example.org", False)
                data = layer_file.collection(info, Pulled([layer_file.feature(
                    info, "1", layer_file.point_geometry(POINTS[SITE]), hazard="flood", severity=0, date=None,
                    title="Ünïcode", summary="s")]), PULLED_ON)
                path = layer_file.write_collection(data, directory)
                self.assertEqual(layer_file.read_collection(path), data)
            # One feature per line, so a refresh shows as changed records in a diff.
            self.assertEqual(len((directory / "alpha.geojson").read_text().splitlines()), 3)
            catalog = layer_file.write_catalog(directory, first=("zebra",))
            self.assertEqual([entry["layer_id"] for entry in catalog], ["zebra", "alpha", "watchlist"])
            self.assertEqual(json.loads((directory / "catalog.json").read_text()), catalog)

    def test_an_empty_layer_still_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = layer_file.write_collection(layer_file.error_collection(INFO, PULLED_ON), Path(folder))
            self.assertEqual(layer_file.read_collection(path)["features"], [])


class ConstructionIncidents(unittest.TestCase):
    ROWS = [
        {"accident_report_id": "46672", "incident_date_mm_dd_yyyy": "2026-11-11T00:00:00.000",
         "record_type_description": "Accident", "check2_description": "Other Construction Related",
         "fatality": "2", "injury": "17", "addressnumber": "1321", "street": "FLATBUSH AVENUE", "boro": "Brooklyn",
         "address_latitude": "40.638718", "address_longitude": "-73.953869", "address_bbl": NEXT_DOOR},
        {"accident_report_id": "46639", "incident_date_mm_dd_yyyy": "2026-11-02T00:00:00.000",
         "record_type_description": "Accident", "check2_description": "Excavation/Soil Work",
         "fatality": "0", "injury": "1", "addressnumber": "48-05", "street": "46 STREET", "boro": "Queens",
         "address_latitude": "40.739029", "address_longitude": "-73.919515", "address_bbl": "4022900015"},
        {"accident_report_id": "46571", "incident_date_mm_dd_yyyy": "2026-10-15T00:00:00.000",
         "record_type_description": "Incident", "check2_description": "Scaffold/Shoring Installations",
         "fatality": "0", "injury": "0", "addressnumber": "809", "street": "MADISON AVENUE", "boro": "Manhattan",
         "address_latitude": "40.769077", "address_longitude": "-73.9674"},
        {"accident_report_id": "46000", "record_type_description": "Accident", "check2_description": "Worker Fell",
         "fatality": "0", "injury": "1", "boro": "Bronx"},
    ]

    def test_severity_follows_fatalities_then_injuries(self):
        features, _ = construction_incidents.features_from_rows(self.ROWS)
        self.assertEqual([p["severity"] for p in props(features)], [3, 2, 1])

    def test_only_excavation_is_geotech(self):
        features, _ = construction_incidents.features_from_rows(self.ROWS)
        self.assertEqual([p["hazard"] for p in props(features)], ["construction_safety", "geotech", "construction_safety"])

    def test_wording_matches_the_shared_fixture(self):
        features, _ = construction_incidents.features_from_rows(self.ROWS)
        fixture = json.loads((Path(contracts.__file__).parent.parent / "contracts/fixtures/layer_features.json").read_text())
        expected = next(f for f in fixture["features"] if f["properties"]["record_id"] == "46639")
        self.assertEqual(features[1]["properties"], {**expected["properties"], "source_name": features[1]["properties"]["source_name"]})
        self.assertEqual(features[1]["geometry"], expected["geometry"])

    def test_a_record_with_no_coordinates_is_counted_not_placed(self):
        features, notes = construction_incidents.features_from_rows(self.ROWS)
        self.assertEqual(len(features), 3)
        self.assertEqual(notes, ["Not on the map: 1 of 4 records (no usable coordinates)."])
        self.assertIsNone(features[2]["properties"]["bbl"])

    def test_the_summary_states_counts_and_no_cause(self):
        summary = props(construction_incidents.features_from_rows(self.ROWS)[0])[0]["summary"]
        self.assertEqual(summary, "1321 FLATBUSH AVENUE, Brooklyn. Injuries: 17. Fatalities: 2.")


class VacateOrders(unittest.TestCase):
    ROWS = [
        {"vacate_order_number": "261351", "primary_vacate_reason": "Fire Damage", "vacate_type": "Entire Building",
         "vacate_effective_date": "2026-11-10T00:00:00.000", "number_of_vacated_units": "4", "house_number": "70",
         "street_name": "EAST 95 STREET", "boro_short_name": "BK", "latitude": "40.66386", "longitude": "-73.926065",
         "bbl": "3045970036"},
        {"vacate_order_number": "91563", "primary_vacate_reason": "Fire Damage", "vacate_type": "Partial",
         "vacate_effective_date": "2012-01-06T00:00:00.000", "actual_rescind_date": "2016-05-13T00:00:00.000",
         "number_of_vacated_units": "1", "house_number": "482", "street_name": "OCEAN PARKWAY",
         "boro_short_name": "BK", "latitude": "40.636836", "longitude": "-73.97288", "bbl": "3053890041"},
        {"vacate_order_number": "2327", "primary_vacate_reason": "Fire Damage", "vacate_type": "Partial",
         "vacate_effective_date": "2040-08-20T00:00:00.000", "number_of_vacated_units": "2", "house_number": "70-17",
         "street_name": "37 AVENUE", "boro_short_name": "QN", "latitude": "40.748622", "longitude": "-73.895109"},
        {"vacate_order_number": "5", "primary_vacate_reason": "Illegal Occupancy", "latitude": "40.7", "longitude": "-73.9"},
        {"vacate_order_number": "6", "primary_vacate_reason": "Illegal Occupancy", "latitude": "40.7", "longitude": "-73.9"},
        {"vacate_order_number": "7", "primary_vacate_reason": "Habitability", "latitude": "40.7", "longitude": "-73.9"},
        {"vacate_order_number": "8", "primary_vacate_reason": "Fire Damage"},
    ]

    def test_only_fire_damage_orders_are_features_and_the_rest_are_counted(self):
        features, notes = vacate_orders.features_from_rows(self.ROWS, PULLED_ON)
        self.assertEqual([p["record_id"] for p in props(features)], ["261351", "91563", "2327"])
        self.assertTrue(all(p["hazard"] == "fire" and p["severity"] == 1 for p in props(features)))
        self.assertEqual(notes, [
            "Not on the map: 1 of 4 fire-damage orders (no usable coordinates).",
            "Not shown: 2 for illegal occupancy, 1 for habitability; those are housing matters, not a hazard this map tracks.",
        ])

    def test_housing_reasons_never_get_a_hazard(self):
        self.assertEqual(vacate_orders.HAZARD_BY_REASON, {"Fire Damage": "fire"})

    def test_the_summary_dates_the_rescind_or_says_none_at_the_pull(self):
        features, _ = vacate_orders.features_from_rows(self.ROWS, PULLED_ON)
        self.assertEqual(features[0]["properties"]["title"], "Vacate order: fire damage (entire building)")
        self.assertEqual(features[0]["properties"]["summary"],
                         "70 EAST 95 STREET, Brooklyn. Units vacated: 4. No rescind date on record at the pull (2026-11-14).")
        self.assertEqual(features[1]["properties"]["summary"], "482 OCEAN PARKWAY, Brooklyn. Units vacated: 1. Rescinded 2016-05-13.")

    def test_a_date_after_the_pull_is_kept_as_recorded_and_flagged(self):
        future = vacate_orders.features_from_rows(self.ROWS, PULLED_ON)[0][2]["properties"]
        self.assertEqual(future["date"], "2040-08-20")
        self.assertIn("after the pull", future["summary"])


class FdnyVacates(unittest.TestCase):
    ROWS = [
        {"vac_date": "2025-09-17T00:00:00.000", "bor": "BK", "aka_address": "120B ELIZABETH STREET, BK ;120 ELIZABETH STREET, BK",
         "bin": "3120364", "bbl": NEXT_DOOR, "status_change_date": "2025-12-19T00:00:00.000", "ocpcy_desc": "Residential"},
        {"description": "Rescinded", "vac_date": "2025-09-17T00:00:00.000", "aka_address": "1321 FLATBUSH AVENUE, BK",
         "bin": "3120364", "bbl": NEXT_DOOR, "status_change_date": "2025-10-29T00:00:00.000", "ocpcy_desc": "Unknown"},
        {"description": "Dismissal", "vac_date": "2012-07-23T00:00:00.000", "aka_address": "5 NOWHERE ROAD, SI",
         "bin": "5000001", "bbl": "5000010001", "ocpcy_desc": "Storage"},
    ]

    def test_orders_are_placed_by_lot_and_the_unplaced_are_counted(self):
        features, notes = fdny_vacates.features_from_rows(self.ROWS, POINTS)
        self.assertEqual(len(features), 2)
        self.assertEqual(features[0]["geometry"]["coordinates"], list(POINTS[NEXT_DOOR]))
        self.assertEqual(notes, ["Not on the map: 1 of 3 orders (the lot is in neither PLUTO nor the tax map)."])

    def test_a_second_order_on_the_same_building_and_day_keeps_its_own_id(self):
        ids = [p["id"] for p in props(fdny_vacates.features_from_rows(self.ROWS, POINTS)[0])]
        self.assertEqual(ids, [f"fdny_vacates:{NEXT_DOOR}-2025-09-17", f"fdny_vacates:{NEXT_DOOR}-2025-09-17-2"])

    def test_the_status_is_quoted_and_no_reason_is_invented(self):
        first, second = props(fdny_vacates.features_from_rows(self.ROWS, POINTS)[0])
        self.assertEqual(first["title"], "FDNY vacate order: residential building")
        self.assertEqual(first["summary"], "120B ELIZABETH STREET, Brooklyn. No status recorded.")
        self.assertEqual(second["title"], "FDNY vacate order")
        self.assertEqual(second["summary"], '1321 FLATBUSH AVENUE, Brooklyn. Status as recorded: "Rescinded", changed 2025-10-29.')
        self.assertIsNone(first["record_id"])
        self.assertEqual((first["hazard"], first["severity"]), ("fire", 1))


class UnsafeFacades(unittest.TestCase):
    @staticmethod
    def filing(tr6: str, cycle: str, current: str, filed: str | None = None, **extra) -> dict:
        row = {"tr6_no": tr6, "cycle": cycle, "current_status": current, "filing_status": current, "bin": "3120364",
               "house_no": "1321", "street_name": "FLATBUSH AVENUE", "borough": "Brooklyn", "block": "5211", "lot": "73"}
        if filed:
            row["filing_date"] = f"{filed}T00:00:00.000"
        return {**row, **extra}

    def test_a_building_appears_once_with_its_newest_cycle(self):
        rows = [self.filing("TR6-1-9A-I1", "9", "UNSAFE", "2022-08-16"), self.filing("TR6-1-10A-I1", "10", "SAFE", "2025-03-01")]
        newest, unidentified = unsafe_facades.newest_filings(rows)
        self.assertEqual([r["tr6_no"] for r in newest], ["TR6-1-10A-I1"])  # cycle 10 is after cycle 9
        self.assertEqual(unidentified, 0)
        self.assertEqual(unsafe_facades.features_from_rows(newest, POINTS, {})[0], [])  # now SAFE: no mark

    def test_within_a_cycle_the_latest_dated_filing_wins_over_an_undated_one(self):
        rows = [self.filing("TR6-1-9A-I1", "9", "UNSAFE", "2022-08-16"), self.filing("TR6-1-9A-A1", "9", "SWARMP", "2023-07-19"),
                self.filing("TR6-1-9A-N1", "9", "UNSAFE")]
        newest, _ = unsafe_facades.newest_filings(rows)
        self.assertEqual([r["tr6_no"] for r in newest], ["TR6-1-9A-A1"])

    def test_unsafe_is_enforcement_level_and_swarmp_a_signal(self):
        rows = [self.filing("TR6-1-9A-I1", "9", "UNSAFE", "2025-02-20", filing_status="UNSAFE",
                            exterior_wall_type_s_="MASONRY LOAD-BEARING WALL", exterior_wall_material_s_="MASONRY; TERRA COTTA"),
                self.filing("TR6-2-9A-I1", "9", "SWARMP", "2024-01-05", bin="3328271", lot="74", filing_status="UNSAFE")]
        features, notes = unsafe_facades.features_from_rows(*[unsafe_facades.newest_filings(rows)[0]], POINTS, {})
        unsafe, swarmp = props(features)
        self.assertEqual((unsafe["severity"], unsafe["title"]), (1, "Facade status: unsafe"))
        self.assertEqual(unsafe["summary"], "1321 FLATBUSH AVENUE, Brooklyn. Inspection cycle 9, filing TR6-1-9A-I1. "
                                            "Exterior wall: masonry load-bearing wall; masonry; terra cotta.")
        self.assertEqual(swarmp["severity"], 0)
        self.assertIn("filed as UNSAFE.", swarmp["summary"])
        self.assertEqual((unsafe["bbl"], swarmp["bbl"], unsafe["date"]), (NEXT_DOOR, SITE, "2025-02-20"))
        self.assertEqual(notes, [])

    def test_a_condo_unit_lot_falls_back_to_the_buildings_footprint_lot(self):
        rows = [self.filing("TR6-3-9A-I1", "9", "UNSAFE", "2025-02-20", lot="1001")]
        newest, _ = unsafe_facades.newest_filings(rows)
        self.assertEqual(unsafe_facades.features_from_rows(newest, POINTS, {})[1],
                         ["Not on the map: 1 of 1 buildings (the lot is in neither PLUTO nor the tax map)."])
        placed = unsafe_facades.features_from_rows(newest, POINTS, {"3120364": NEXT_DOOR})[0]
        self.assertEqual(placed[0]["properties"]["bbl"], NEXT_DOOR)

    def test_a_filing_naming_no_building_is_counted(self):
        rows = [self.filing("TR6-4-9A-I1", "9", "UNSAFE", bin="3000000", block="", lot="")]
        self.assertEqual(unsafe_facades.newest_filings(rows), ([], 1))


class StructuralComplaints(unittest.TestCase):
    BIN_LOTS = {"3120364": NEXT_DOOR, "3328271": SITE}
    TITLES = {"30": "Building Shaking/Vibrating/Structural Stability Affected", "14": "Excavation - Undermining Adjacent Building"}
    MEANINGS = {"I2": "NO VIOLATION WARRANTED FOR COMPLAINT AT TIME OF INSPECTION", "A3": "FULL STOP WORK ORDER SERVED F"}

    @staticmethod
    def complaint(number: str, code: str, entered: str, bin_number: str = "3120364", **extra) -> dict:
        return {"complaint_number": number, "complaint_category": code, "date_entered": entered, "bin": bin_number,
                "house_number": "1321", "house_street": "FLATBUSH AVENUE", **extra}

    def build(self, rows, meanings="default", titles=None):
        meanings = self.MEANINGS if meanings == "default" else meanings
        return structural_complaints.features_from_rows(rows, self.BIN_LOTS, POINTS, self.TITLES if titles is None else titles,
                                                        meanings, PULLED_ON)

    def test_the_query_names_the_seven_codes_and_the_years_in_the_window(self):
        where = structural_complaints.where(PULLED_ON)
        self.assertEqual(where, "complaint_category in ('03','14','16','30','54','2K','5C') AND "
                                "(date_entered like '%/2024' OR date_entered like '%/2025' OR date_entered like '%/2026')")
        self.assertEqual(structural_complaints.first_day(PULLED_ON), date(2024, 1, 1))

    def test_a_complaint_is_a_signal_with_its_category_as_printed(self):
        features, notes = self.build([self.complaint("3963382", "30", "11/11/2026", disposition_code="I2", disposition_date="11/12/2026")])
        feature = features[0]["properties"]
        self.assertEqual((feature["severity"], feature["hazard"], feature["date"]), (0, "structural", "2026-11-11"))
        self.assertEqual(feature["title"], "Complaint 30: Building Shaking/Vibrating/Structural Stability Affected")
        self.assertEqual(feature["summary"], "1321 FLATBUSH AVENUE, Brooklyn. DOB's disposition I2, dated 2026-11-12: "
                                             '"NO VIOLATION WARRANTED FOR COMPLAINT AT TIME OF INSPECTION".')
        self.assertEqual((feature["bbl"], feature["record_id"]), (NEXT_DOOR, "3963382"))
        self.assertEqual(notes, [])

    def test_excavation_undermining_is_geotech(self):
        self.assertEqual(self.build([self.complaint("1", "14", "03/18/2026")])[0][0]["properties"]["hazard"], "geotech")
        self.assertEqual(set(structural_complaints.CATEGORIES.values()), {"structural", "geotech"})

    def test_a_code_missing_from_a_key_is_shown_as_the_code_never_guessed(self):
        rows = [self.complaint("1", "5C", "03/18/2026", disposition_code="AF", disposition_date="03/20/2026")]
        feature = self.build(rows)[0][0]["properties"]
        self.assertEqual(feature["title"], "Complaint category 5C")
        self.assertTrue(feature["summary"].endswith("DOB's disposition AF, dated 2026-03-20 (not in DOB's published code table)."))
        no_table = self.build(rows, meanings=None)[0][0]["properties"]
        self.assertTrue(no_table["summary"].endswith("DOB's disposition AF, dated 2026-03-20."))

    def test_no_disposition_says_so_with_the_pull_date(self):
        summary = self.build([self.complaint("1", "30", "11/12/2026")])[0][0]["properties"]["summary"]
        self.assertEqual(summary, "1321 FLATBUSH AVENUE, Brooklyn. No disposition on record at the pull (2026-11-14).")

    def test_complaints_before_the_window_or_in_other_categories_are_not_counted(self):
        rows = [self.complaint("1", "30", "12/31/2023"), self.complaint("2", "85", "03/18/2026"), self.complaint("3", "30", "not a date")]
        self.assertEqual(self.build(rows), ([], []))

    def test_a_placeholder_bin_or_an_unknown_building_is_counted_not_placed(self):
        rows = [self.complaint("1", "30", "03/18/2026", bin_number="3000000"), self.complaint("2", "30", "03/18/2026", bin_number="3999999"),
                self.complaint("3", "30", "03/18/2026")]
        features, notes = self.build(rows)
        self.assertEqual(len(features), 1)
        self.assertEqual(notes, ["Not on the map: 2 of 3 complaints (the building has no footprint or lot point, or a placeholder BIN)."])

    def test_category_wording_comes_from_the_hand_imported_list(self):
        titles, note = structural_complaints.category_titles()
        self.assertEqual(set(titles), set(structural_complaints.CATEGORIES))
        self.assertEqual(titles["03"], "Adjacent Buildings - Not Protected")
        self.assertIn("imported by hand", note)


class SandyInundation(unittest.TestCase):
    SQUARE = [[-73.951234567, 40.601234567], [-73.950234567, 40.601234567], [-73.950234567, 40.602234567],
              [-73.951234567, 40.602234567], [-73.951234567, 40.601234567]]
    SPECK = [[-73.9500001, 40.6000001], [-73.9500002, 40.6000001], [-73.9500002, 40.6000002], [-73.9500001, 40.6000001]]

    def test_coordinates_are_rounded_and_a_polygon_becomes_a_multipolygon(self):
        geometry = sandy_inundation.simplified({"type": "Polygon", "coordinates": [self.SQUARE]})
        self.assertEqual(geometry, {"type": "MultiPolygon", "coordinates": [[[
            [-73.95123, 40.60123], [-73.95023, 40.60123], [-73.95023, 40.60223], [-73.95123, 40.60223], [-73.95123, 40.60123]]]]})
        contracts.Geometry.model_validate(geometry)

    def test_a_ring_that_collapses_is_dropped(self):
        both = {"type": "MultiPolygon", "coordinates": [[self.SQUARE, self.SPECK], [self.SPECK]]}
        geometry = sandy_inundation.simplified(both)
        self.assertEqual(len(geometry["coordinates"]), 1)        # the speck polygon is gone
        self.assertEqual(len(geometry["coordinates"][0]), 1)     # and so is the speck hole
        self.assertIsNone(sandy_inundation.simplified({"type": "Polygon", "coordinates": [self.SPECK]}))
        self.assertIsNone(sandy_inundation.simplified(None))

    def test_features_are_flood_context_dated_to_the_storm(self):
        rows = [{"status": "Final Field-Verified High Resolution", "the_geom": {"type": "Polygon", "coordinates": [self.SQUARE]}},
                {"the_geom": {"type": "Polygon", "coordinates": [self.SPECK]}}, {}]
        features, notes = sandy_inundation.features_from_rows(rows)
        only = features[0]["properties"]
        self.assertEqual((only["hazard"], only["severity"], only["date"], only["id"]), ("flood", 0, "2012-10-29", "sandy_inundation:1"))
        self.assertIn("Survey status as recorded: Final Field-Verified High Resolution.", only["summary"])
        self.assertEqual(notes, ["Not on the map: 2 of 3 areas (too small to draw at this detail)."])

    def test_it_reads_the_dataset_not_the_empty_map_view(self):
        self.assertEqual((sandy_inundation.DATASET, sandy_inundation.MAP_VIEW), ("5xsi-dfpx", "uyj8-7rv5"))
        self.assertIn("5xsi-dfpx", sandy_inundation.INFO.source_url)


class EDesignations(unittest.TestCase):
    ROWS = [
        {"enumber": "E-905", "effective_date": "2026-10-13T00:00:00.000", "hazmat_code": True, "air_code": True, "noise_code": True,
         "description": "Air Quality - HVAC electricity only;Hazardous Materials* Phase I and Phase II Testing Protocol", "bbl": SITE},
        {"enumber": "E-12", "effective_date": "1999-01-01T00:00:00.000", "hazmat_code": True, "air_code": False, "noise_code": False,
         "bbl": "3052110073.00000000"},
        {"enumber": "E-77", "hazmat_code": False, "air_code": False, "noise_code": True, "bbl": SITE},
        {"enumber": "E-78", "hazmat_code": True, "bbl": "1000010001"},
    ]

    def test_only_hazardous_materials_designations_are_features(self):
        features, notes = e_designations.features_from_rows(self.ROWS, POINTS)
        self.assertEqual([p["id"] for p in props(features)], [f"e_designations:E-905:{SITE}", f"e_designations:E-12:{NEXT_DOOR}"])
        self.assertTrue(all((p["hazard"], p["severity"]) == ("contamination", 0) for p in props(features)))
        self.assertEqual(notes, ["Not on the map: 1 of 3 designated lots (the lot is in neither PLUTO nor the tax map).",
                                 "Not shown: 1 designations for air quality or noise alone."])

    def test_the_requirement_is_quoted_from_the_record(self):
        first, second = props(e_designations.features_from_rows(self.ROWS, POINTS)[0])
        self.assertEqual(first["summary"], "E-905 on this lot. Also designated for air quality and noise. As recorded: "
                                           "Air Quality - HVAC electricity only;Hazardous Materials* Phase I and Phase II Testing Protocol")
        self.assertEqual((first["date"], first["record_id"]), ("2026-10-13", "E-905"))
        self.assertEqual(second["summary"], "E-12 on this lot.")


class NoNamesAreRequested(unittest.TestCase):
    def test_no_layer_asks_a_source_for_a_name(self):
        allowed = {"street_name", "boro_short_name"}
        for module in build_layers.MODULES:
            if not hasattr(module, "SELECT"):
                continue
            for column in module.SELECT.split(","):
                with self.subTest(layer=module.INFO.layer_id, column=column):
                    self.assertFalse(any(word in column for word in ("owner", "qewi", "applicant", "contractor", "registration", "comments")))
                    self.assertTrue(not column.endswith("name") or column in allowed)


class SourceRows(unittest.TestCase):
    def test_all_rows_pages_until_a_short_page(self):
        pages = [[{"n": i} for i in range(3)], [{"n": i} for i in range(3)], [{"n": 0}]]
        calls = []

        def query(dataset_id, params):
            calls.append(params)
            return pages[len(calls) - 1], "url"

        with mock.patch.object(source_rows, "PAGE_ROWS", 3), mock.patch.object(soda_client, "query", query):
            rows, capped = source_rows.all_rows("abcd-1234", {"select": "n"})
        self.assertEqual((len(rows), capped), (7, False))
        self.assertEqual([c["offset"] for c in calls], ["0", "3", "6"])
        self.assertTrue(all(c["order"] == ":id" and c["limit"] == "3" for c in calls))

    def test_all_rows_stops_at_the_cap_and_says_so(self):
        with mock.patch.object(source_rows, "PAGE_ROWS", 3), \
                mock.patch.object(soda_client, "query", lambda d, p: ([{"n": 1}] * int(p["limit"]), "url")):
            rows, capped = source_rows.all_rows("abcd-1234", {}, max_rows=5)
        self.assertEqual((len(rows), capped), (5, True))

    def test_one_failed_page_fails_the_whole_read(self):
        def query(dataset_id, params):
            if params["offset"] != "0":
                raise soda_client.SodaQueryError("abcd-1234: HTTP 500")
            return [{"n": 1}] * 3, "url"

        with mock.patch.object(source_rows, "PAGE_ROWS", 3), mock.patch.object(soda_client, "query", query):
            with self.assertRaises(LayerPullError):
                source_rows.all_rows("abcd-1234", {})

    def test_lot_points_asks_pluto_in_batches_then_the_tax_map_for_the_lots_it_lacks(self):
        asked = []
        square = {"type": "MultiPolygon", "coordinates": [[[[-73.9540, 40.6390], [-73.9538, 40.6390], [-73.9538, 40.6392],
                                                            [-73.9540, 40.6392], [-73.9540, 40.6390]]]]}

        def query(dataset_id, params):
            asked.append((dataset_id, params["where"]))
            if dataset_id == source_rows.PLUTO:
                return [{"bbl": "3052110074.00000000", "latitude": "40.6391463", "longitude": "-73.9538111"},
                        {"bbl": "3052110073.00000000", "latitude": "0", "longitude": "0"}], "url"
            return [{"bbl": NEXT_DOOR, "the_geom": square}], "url"

        with mock.patch.object(source_rows, "LOOKUP_BATCH", 2), mock.patch.object(soda_client, "query", query):
            points = source_rows.lot_points([SITE, NEXT_DOOR, "3052110054", SITE])
        # The site is PLUTO's point; next door (no usable PLUTO point) is the middle of its tax-map polygon;
        # lot 54 is in neither, so it is absent.
        self.assertEqual(points, {SITE: (-73.953811, 40.639146), NEXT_DOOR: (-73.9539, 40.6391)})
        self.assertEqual(asked, [
            ("64uk-42ks", "bbl in (3052110054,3052110073)"), ("64uk-42ks", "bbl in (3052110074)"),
            ("i38t-6if2", "bbl in ('3052110054','3052110073')"),
        ])
        with self.assertRaises(ValueError):
            source_rows.lot_points(["3052110074) OR 1=1 --"])

    def test_the_middle_of_a_polygon(self):
        l_shape = [[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2], [0, 0]]
        moved = [[-73.96 + x / 1000, 40.60 + y / 1000] for x, y in l_shape]
        lon, lat = source_rows.polygon_middle({"type": "Polygon", "coordinates": [moved]})
        self.assertAlmostEqual(lon, -73.96 + (5 / 6) / 1000, places=6)   # an L's centroid, not its corner average
        self.assertAlmostEqual(lat, 40.60 + (5 / 6) / 1000, places=6)
        speck = [[-73.9, 40.7], [-73.9, 40.7], [-73.9, 40.7], [-73.9, 40.7]]
        both = {"type": "MultiPolygon", "coordinates": [[speck], [moved]]}
        self.assertEqual(source_rows.polygon_middle(both), (lon, lat))  # the largest part decides
        for nothing in (None, {}, {"type": "Point", "coordinates": [0, 0]}, {"type": "Polygon", "coordinates": [speck]}):
            self.assertIsNone(source_rows.polygon_middle(nothing))

    def test_building_lots_never_joins_on_a_placeholder_or_an_ambiguous_bin(self):
        rows = [{"bin": "3120364", "mappluto_bbl": NEXT_DOOR, "base_bbl": NEXT_DOOR},
                {"bin": "3999999", "mappluto_bbl": "3036590015"}, {"bin": "3999999", "mappluto_bbl": "3051710071"},
                {"bin": "3111111", "base_bbl": SITE}]
        asked = []

        def query(dataset_id, params):
            asked.append(params["where"])
            return rows, "url"

        with mock.patch.object(soda_client, "query", query):
            lots = source_rows.building_lots(["3120364", "3000000", "3999999", "3111111", "not a bin", None])
        self.assertEqual(lots, {"3120364": NEXT_DOOR, "3111111": SITE})
        self.assertEqual(asked, ["bin in (3111111,3120364,3999999)"])

    def test_a_failed_lookup_is_an_error_not_an_empty_answer(self):
        def query(dataset_id, params):
            raise soda_client.SodaQueryError("64uk-42ks: HTTP 429")

        with mock.patch.object(soda_client, "query", query):
            with self.assertRaises(LayerPullError):
                source_rows.lot_points([SITE])
            with self.assertRaises(LayerPullError):
                source_rows.building_lots(["3120364"])
            with self.assertRaises(LayerPullError):
                source_rows.count_rows("abcd-1234")


class Build(unittest.TestCase):
    def run_build(self, directory: Path, pull):
        module = mock.Mock(INFO=LayerInfo("construction_incidents", "Construction incidents", "About.", "construction_safety",
                                          "DOB", "https://example.org", True), pull=pull)
        with mock.patch.dict(build_layers.LAYERS, {"construction_incidents": module}), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            return build_layers.build(["construction_incidents"], directory, PULLED_ON)

    @staticmethod
    def good(pulled_on):
        info = build_layers.LAYERS["construction_incidents"].INFO
        return Pulled([layer_file.feature(info, "1", layer_file.point_geometry(POINTS[SITE]), hazard="geotech", severity=2,
                                          date="2026-11-02", title="t", summary="s")], "2026-11-14")

    @staticmethod
    def failing(pulled_on):
        raise LayerPullError("bf97-mjsy: HTTP 503")

    def test_a_good_pull_writes_the_layer_and_the_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertEqual(self.run_build(directory, self.good), {"construction_incidents": "ok"})
            catalog = json.loads((directory / "catalog.json").read_text())
            self.assertEqual([(e["layer_id"], e["status"], e["feature_count"]) for e in catalog], [("construction_incidents", "ok", 1)])

    def test_a_failed_first_pull_writes_an_error_never_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertEqual(self.run_build(directory, self.failing), {"construction_incidents": "error"})
            entry = json.loads((directory / "catalog.json").read_text())[0]
            self.assertEqual((entry["status"], entry["feature_count"]), ("error", None))
            contracts.LayerCatalogEntry.model_validate(entry)

    def test_a_failed_refresh_keeps_the_last_good_file_and_says_so(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.run_build(directory, self.good)
            for _ in range(2):  # a second failure must not stack a second sentence
                self.assertEqual(self.run_build(directory, self.failing), {"construction_incidents": "kept"})
            kept = layer_file.read_collection(directory / "construction_incidents.geojson")
            self.assertEqual((kept["layer"]["status"], len(kept["features"])), ("ok", 1))
            self.assertEqual(kept["layer"]["description"],
                             "About. Pulled 2026-11-14. A refresh on 2026-11-14 failed, so this is the earlier pull.")

    def test_a_bug_in_one_layer_is_a_failed_pull_not_a_crash(self):
        def broken(pulled_on):
            raise KeyError("the_geom")

        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.run_build(Path(folder), broken), {"construction_incidents": "error"})

    def test_every_layer_has_its_own_id_and_a_pull(self):
        self.assertEqual(len(build_layers.LAYERS), len(build_layers.MODULES))
        for module in build_layers.MODULES:
            self.assertIn(module.INFO.hazard, layer_file.HAZARDS)
            self.assertTrue(callable(module.pull))


class WrittenLayerFiles(unittest.TestCase):
    """data/layers/ as committed: whatever module wrote a file, it must match the contracts."""

    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(layer_file.LAYERS_DIR.glob("*.geojson"))
        cls.collections = {path.stem: layer_file.read_collection(path) for path in cls.paths}

    def test_every_city_layer_has_a_file(self):
        self.assertTrue(set(build_layers.LAYERS) <= set(self.collections), sorted(set(build_layers.LAYERS) - set(self.collections)))

    def test_every_file_matches_the_contract(self):
        for layer_id, data in self.collections.items():
            with self.subTest(layer=layer_id):
                contracts.LayerFeatureCollection.model_validate(data)
                self.assertEqual(data["layer"]["layer_id"], layer_id)

    def test_features_belong_to_their_layer_with_unique_ids_inside_the_city(self):
        for layer_id, data in self.collections.items():
            ids = [f["properties"]["id"] for f in data["features"]]
            with self.subTest(layer=layer_id):
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(all(i.startswith(f"{layer_id}:") for i in ids))
                self.assertTrue(all(f["properties"]["layer_id"] == layer_id for f in data["features"]))
                for f in data["features"]:
                    if f["geometry"]["type"] == "Point":
                        self.assertIsNotNone(layer_file.point(*f["geometry"]["coordinates"]), f["properties"]["id"])

    def test_counts_are_honest(self):
        for layer_id, data in self.collections.items():
            layer = data["layer"]
            with self.subTest(layer=layer_id):
                if layer["status"] == "error":
                    self.assertEqual((layer["feature_count"], data["features"]), (None, []))
                else:
                    self.assertEqual(layer["feature_count"], len(data["features"]))

    def test_the_catalog_lists_every_file(self):
        catalog = json.loads((layer_file.LAYERS_DIR / layer_file.CATALOG).read_text())
        for entry in catalog:
            contracts.LayerCatalogEntry.model_validate(entry)
        self.assertEqual({e["layer_id"]: e for e in catalog}, {i: d["layer"] for i, d in self.collections.items()})


class WorkTypes(unittest.TestCase):
    JOB_TYPES = set(get_args(contracts.JobType))
    WORK_TYPES = set(get_args(contracts.WorkType))

    def test_every_name_is_the_contracts(self):
        self.assertEqual(set(work_types.ASSUMED), self.JOB_TYPES)
        self.assertTrue(set(work_types.JOB_TYPES.values()) <= self.JOB_TYPES)
        for assumed in work_types.ASSUMED.values():
            self.assertTrue(set(assumed) <= self.WORK_TYPES)
            self.assertEqual(len(assumed), len(set(assumed)))
        self.assertTrue(set(work_types.FILING_COLUMNS.values()) <= self.WORK_TYPES)

    def test_every_contract_work_type_is_either_a_filing_column_or_listed_as_having_none(self):
        self.assertEqual(set(work_types.FILING_COLUMNS.values()) | set(work_types.NO_FILING_COLUMN), self.WORK_TYPES)
        self.assertFalse(set(work_types.FILING_COLUMNS.values()) & set(work_types.NO_FILING_COLUMN))

    def test_dob_now_job_types_map_to_the_contract(self):
        self.assertEqual(work_types.job_type("New Building"), "new_building")
        self.assertEqual(work_types.job_type(" Alteration CO "), "alteration")
        self.assertEqual(work_types.job_type("Full Demolition"), "demolition")
        self.assertIsNone(work_types.job_type("No Work"))
        self.assertIsNone(work_types.job_type(None))
        self.assertEqual(set(work_types.PERCENT_OF_FILINGS), set(work_types.JOB_TYPES))

    def test_assumed_work_types(self):
        new_building = work_types.assumed_work_types("new_building")
        self.assertEqual(new_building[:4], ["earth_work", "excavation", "foundation", "support_of_excavation"])
        self.assertEqual(work_types.assumed_work_types("demolition")[0], "demolition")
        self.assertIn("structural", work_types.assumed_work_types("alteration"))
        new_building.append("x")  # a caller's edit must not change the table
        self.assertNotIn("x", work_types.assumed_work_types("new_building"))
        with self.assertRaises(ValueError):
            work_types.assumed_work_types("No Work")

    def test_underpinning_is_never_assumed(self):
        self.assertTrue(all("underpinning" not in assumed for assumed in work_types.ASSUMED.values()))

    def test_stated_work_types_reads_the_filings_yes_flags(self):
        filings = [{"earth_work_work_type_": "YES", "foundation_work_type_": "Yes", "support_of_excavation_work_type_": "No"},
                   {"structural_work_type_": "NO", "sprinkler_work_type": "yes"}]
        self.assertEqual(work_types.stated_work_types(filings), ["earth_work", "foundation", "sprinkler"])
        self.assertEqual(work_types.stated_work_types([]), [])

    def test_the_cached_demo_site_states_earth_work_and_foundation(self):
        pull = json.loads((Path(contracts.__file__).parent.parent / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        stated = work_types.stated_work_types(pull["site"]["datasets"]["dob_now_filings"]["records"])
        self.assertIn("earth_work", stated)
        self.assertIn("foundation", stated)
        self.assertNotIn("support_of_excavation", stated)  # "No" on every filing in the city: see NEVER_STATED


if __name__ == "__main__":
    unittest.main()
