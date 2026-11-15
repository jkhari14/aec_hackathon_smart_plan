"""The four building facts behind similarity: era, wall system, height, attachment; and how they score."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from site_profile import build_profile, building_profile as bp, similarity

ROOT = Path(__file__).resolve().parent.parent


class Facts(unittest.TestCase):
    def test_eras_follow_the_building_codes(self):
        self.assertEqual(bp.era(1899), "built before 1900")
        self.assertEqual(bp.era(1930), "built 1900 to 1937 (before the 1938 code)")
        self.assertEqual(bp.era(1938), "built 1938 to 1967 (1938 code)")
        self.assertEqual(bp.era(2007), "built 1968 to 2007 (1968 code)")
        self.assertEqual(bp.era(2008), "built 2008 or later (2008 code)")
        self.assertIsNone(bp.era(None))
        self.assertIsNone(bp.era(0))

    def test_height_bands(self):
        self.assertEqual(bp.floors_band(2.75), "1 to 3 storeys")
        self.assertEqual(bp.floors_band(6), "4 to 6 storeys")
        self.assertEqual(bp.floors_band(12), "7 to 12 storeys")
        self.assertEqual(bp.floors_band(58), "13 storeys or more")
        self.assertIsNone(bp.floors_band(None))
        self.assertIsNone(bp.floors_band(0))

    def test_floors_are_read_from_a_write_up(self):
        self.assertEqual(bp.floors_in_text("three-storey masonry"), 3)
        self.assertEqual(bp.floors_in_text("19-storey residential high-rise"), 19)
        self.assertEqual(bp.floors_in_text("concrete superstructure, 58 storeys"), 58)
        self.assertEqual(bp.floors_in_text("Four Story brick"), 4)
        self.assertIsNone(bp.floors_in_text("masonry"))
        self.assertIsNone(bp.floors_in_text(None))

    def test_wall_system_is_read_from_a_write_up(self):
        for text, system in (
            ("three-storey masonry", bp.MASONRY), ("four-storey brick", bp.MASONRY), ("masonry tenement", bp.MASONRY),
            ("masonry, pre-Civil War row houses", bp.MASONRY), ("steel frame with load-bearing brick piers", bp.FRAME),
            ("concrete superstructure, 58 storeys", bp.FRAME), ("19-storey residential high-rise", bp.FRAME),
            ("closely spaced wood frame", bp.WOOD), ("unreinforced brick masonry", bp.MASONRY),
            ("unreinforced masonry bearing walls", bp.MASONRY), ("reinforced concrete", bp.FRAME),
        ):
            self.assertEqual(bp.wall_system_in_text(text), system, text)

    def test_cladding_and_silence_say_nothing_about_the_structure(self):
        self.assertIsNone(bp.wall_system_in_text("terra cotta clad, 17 storeys"))
        self.assertIsNone(bp.wall_system_in_text("two-storey"))
        self.assertIsNone(bp.wall_system_in_text("cellar-level dwelling unit"))
        self.assertIsNone(bp.wall_system_in_text(None))

    def test_a_guess_from_building_class_is_narrow_and_labeled(self):
        self.assertEqual(bp.wall_system_from_class("S4", 1930), bp.MASONRY)   # mixed-use walk-up, pre-1938
        self.assertEqual(bp.wall_system_from_class("C1", 1931), bp.MASONRY)   # walk-up apartments
        self.assertEqual(bp.wall_system_from_class("D4", 1975), bp.FRAME)     # elevator apartments, 1968 code
        self.assertIsNone(bp.wall_system_from_class("A1", 1925))              # a house: wood or masonry, unknown
        self.assertIsNone(bp.wall_system_from_class("C1", 1950))              # between the eras: no guess
        self.assertIsNone(bp.wall_system_from_class(None, 1930))
        b = bp.building("x", year=1930, floors=3, building_class="S4", attached=True)
        self.assertEqual((b["wall_system"], b["wall_basis"]), (bp.MASONRY, "inferred from building class and year"))
        stated = bp.building("x", year=1930, floors=3, building_class="S4", attached=True, stated_wall=bp.FRAME)
        self.assertEqual((stated["wall_system"], stated["wall_basis"]), (bp.FRAME, "stated"))

    def test_a_revit_model_states_the_sites_wall_system_from_its_material_not_its_floors(self):
        profile = {"bbl": "3052110074", "lot": {"address": "2625 BEDFORD AVENUE", "year_built": 1933, "floors": 1.0, "building_class": "K1"},
                   "neighbors": [], "structural_model": {"material": "unreinforced brick masonry",
                                                         "gravity_system": "wood joists on masonry bearing walls"}}
        site = bp.site_buildings(profile)[0]
        self.assertEqual((site["wall_system"], site["wall_basis"]), (bp.MASONRY, "stated"))
        profile["structural_model"] = {"material": None, "lateral_system": "steel moment frame"}
        self.assertEqual(bp.site_buildings(profile)[0]["wall_system"], bp.FRAME)
        profile["structural_model"] = None
        self.assertEqual(bp.site_buildings(profile)[0]["wall_basis"], "inferred from building class and year")

    def test_describe_names_a_guess_as_one(self):
        b = bp.building("x", year=1930, floors=3, building_class="S4", attached=True)
        self.assertEqual(bp.describe(b), "built 1930 (1900 to 1937), masonry bearing wall (inferred from building class and year), "
                                         "1 to 3 storeys, attached")
        self.assertEqual(bp.describe(bp.building("x", year=None, floors=None, building_class=None, attached=None)), "nothing recorded")


class CaseSide(unittest.TestCase):
    def test_a_case_building_comes_from_its_conditions(self):
        case = {"address": "1321 Flatbush Ave", "conditions": {"construction": "three-storey masonry", "attached": True}}
        b = bp.case_building(case)
        self.assertEqual((b["wall_system"], b["floors_band"], b["attached"], b["era"]), (bp.MASONRY, "1 to 3 storeys", True, None))

    def test_every_library_case_still_reads(self):
        cases = json.loads((ROOT / "data/cases/cases.json").read_text())
        described = [bp.case_building(c) for c in cases]
        with_wall = sum(1 for b in described if b["wall_system"])
        self.assertGreaterEqual(with_wall, 18, "most write-ups that name a construction yield a wall system")
        self.assertTrue(all(b["wall_system"] in (None, bp.MASONRY, bp.WOOD, bp.FRAME) for b in described))


class Scoring(unittest.TestCase):
    HERE = bp.building("the neighbor at 1321", year=1930, floors=3, building_class="S4", attached=True)

    def test_each_fact_scores_only_when_both_sides_report_it(self):
        there = bp.building("case", year=1910, floors=None, building_class=None, attached=True, stated_wall=bp.MASONRY)
        found = similarity.compare_buildings(self.HERE, there)
        self.assertEqual(found["matched"], ["era", "wall_system", "attached"])
        self.assertEqual(found["differs"], [])
        self.assertAlmostEqual(found["score"], 0.18 + 0.18 + 0.10)

    def test_a_different_fact_is_a_difference(self):
        there = bp.building("case", year=1985, floors=20, building_class=None, attached=False, stated_wall=bp.FRAME)
        found = similarity.compare_buildings(self.HERE, there)
        self.assertEqual(found, {"score": 0.0, "matched": [], "differs": ["era", "wall_system", "floors_band", "attached"]})

    def test_the_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(similarity.WEIGHTS.values()), 1.0)


class OnTheDemoSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pull = json.loads((ROOT / "data/cache/2625-bedford-ave-brooklyn.json").read_text())
        cls.profile = build_profile.build_profile(pull, as_of="2026-06-01")
        cls.cases, _ = similarity.load_cases(ROOT / "data/cases/cases.json")

    def test_an_excavation_case_is_compared_with_the_neighbors_not_the_dig_site(self):
        case = {"id": "c", "hazards": ["structural"], "severity": 2, "work_types": ["excavation"],
                "conditions": {"construction": "three-storey masonry", "attached": True}}
        found = similarity.compare(self.profile, case)
        sentence = next(m for m in found["matched_on"] if "is like the building in this case" in m)
        self.assertTrue(sentence.startswith("the neighbor at "), sentence)   # never "the site (...)": 2625 Bedford is the dig
        self.assertTrue(sentence.endswith("masonry bearing wall (inferred from building class and year), 1 to 3 storeys, attached"))
        # Two neighbors tie on the facts; the older one (454 East 25 Street, 1901) is named.
        self.assertIn("454 EAST 25 STREET", sentence)

    def test_an_alteration_compares_the_sites_own_building_too(self):
        altered = {**self.profile, "job_type": "alteration"}
        case = {"id": "c", "hazards": ["structural"], "severity": 2, "work_types": ["excavation"],
                "conditions": {"construction": "one-storey brick", "attached": True}}
        sentence = next(m for m in similarity.compare(altered, case)["matched_on"] if "is like the building" in m)
        self.assertTrue(sentence.startswith("the site (2625 BEDFORD AVENUE)"), sentence)

    def test_a_case_after_the_as_of_date_or_on_a_touching_lot_is_not_offered(self):
        ids = [r["case_id"] for r in similarity.rank(self.profile, self.cases, limit=50)["results"]]
        self.assertNotIn("case-1321-flatbush-2026", ids)   # the neighbor's own event, and after 2026-06-01
        self.assertNotIn("case-235-e-42-2026", ids)         # 2026-07-07, after the as-of date
        self.assertIn("case-347-myrtle-2026", ids)          # 2026-04-18, before it
        self.assertIn("case-211-e-34th-2020", ids)

    def test_results_explain_which_building_matched(self):
        top = similarity.rank(self.profile, self.cases, limit=3)["results"]
        for r in top:
            self.assertTrue(any("is like the building in this case" in m for m in r["matched_on"]), r["case_id"])


if __name__ == "__main__":
    unittest.main()
