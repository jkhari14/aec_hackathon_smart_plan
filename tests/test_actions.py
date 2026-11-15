import json
import pathlib
import unittest

from actions.build import (DISCIPLINE_ORDER, build_actions, evaluate_condition,
                           group_by_discipline)

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "contracts/fixtures"
DISCIPLINES = {"architect", "structural", "geotech", "contractor"}
HAZARDS = {"structural", "geotech", "fire", "flood", "contamination", "facade",
           "weather", "construction_safety"}


def _profile():
    data = json.loads((FIXTURES / "site_profile.json").read_text(encoding="utf-8"))
    return data[0] if isinstance(data, list) else data


class TestActions(unittest.TestCase):
    def setUp(self):
        self.profile = _profile()
        self.items = build_actions(self.profile)

    def test_items_match_the_contract(self):
        for a in self.items:
            self.assertIn(a["discipline"], DISCIPLINES, a["id"])
            self.assertIn(a["hazard"], HAZARDS, a["id"])
            self.assertEqual(a["status"], "open", a["id"])
            self.assertIsInstance(a["life_safety"], bool, a["id"])
            self.assertTrue(a["title"] and a["why"] and a["source_rule"], a["id"])
            self.assertIn(a.get("owner_role"), (None, "architect", "structural_engineer"), a["id"])

    def test_ids_are_unique(self):
        ids = [a["id"] for a in self.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_nothing_is_ever_pre_completed(self):
        # Public data can never satisfy a proof; a person has to.
        self.assertTrue(all(a["status"] == "open" for a in self.items))

    def test_life_safety_sorts_first_within_a_discipline(self):
        for group in group_by_discipline(self.items).values():
            flags = [a["life_safety"] for a in group]
            self.assertEqual(flags, sorted(flags, reverse=True))

    def test_stage_filter_narrows_the_list(self):
        every = len(build_actions(self.profile))
        acq = len(build_actions(self.profile, stage="pre_acquisition"))
        self.assertLessEqual(acq, every)

    def test_unknown_stage_is_rejected(self):
        with self.assertRaises(ValueError):
            build_actions(self.profile, stage="not_a_stage")

    def test_unknown_condition_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_condition("not_a_condition", self.profile)

    def test_an_undeterminable_condition_keeps_the_item(self):
        # A missing field must not silently drop a life-safety row.
        bare = {"bbl": "3052110073"}
        items = build_actions(bare)
        self.assertTrue(items)
        unresolved = [a for a in items if "could not be determined" in a["why"]]
        self.assertTrue(unresolved)

    def test_router_contract_is_honoured(self):
        """sites_router discovers actions.actions_for(bbl, stage=) and validates list[ActionItem]."""
        from api.contracts import ActionItem
        from api.routers.sites_router import SITE_OPTIONS, SITE_SOURCES
        from pydantic import TypeAdapter

        module_name, func_name, _ = SITE_SOURCES["actions"]
        self.assertEqual(module_name, "actions")
        module = __import__(module_name)
        func = getattr(module, func_name, None)
        self.assertIsNotNone(func, f"{module_name}.{func_name} is missing")

        import inspect
        params = inspect.signature(func).parameters
        for opt in SITE_OPTIONS["actions"]:
            self.assertIn(opt, params, f"actions_for must accept {opt}")

        TypeAdapter(list[ActionItem]).validate_python(func("3052110073"))

    def test_fixture_derived_answers_are_labelled_sample(self):
        """Until PR 6 lands the rules run on the fixture profile, not the real lot."""
        from fastapi.testclient import TestClient

        from api.main import app
        from api.stubs import FIXTURE_HEADER

        r = TestClient(app).get("/api/sites/3052110073/actions")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get(FIXTURE_HEADER), "true")

    def test_every_discipline_bucket_exists(self):
        self.assertEqual(set(group_by_discipline(self.items)), set(DISCIPLINE_ORDER))


if __name__ == "__main__":
    unittest.main()
