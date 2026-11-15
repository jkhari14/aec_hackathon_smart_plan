import json
import pathlib
import sys
import unittest
from unittest import mock

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

    def test_code_duties_follow_the_scope(self):
        def ids(work_types):
            return {a["id"] for a in build_actions({**self.profile, "work_types": work_types})}
        facade_only = ids(["facade", "scaffold"])
        self.assertIn("action-code-notice", facade_only, "notice applies to any work on an attached site")
        for dig in ("action-code-foundation_protection", "action-code-support_drawings", "action-code-survey",
                    "action-code-monitoring", "action-code-underpinning"):
            self.assertNotIn(dig, facade_only)
        digging = ids(["excavation", "foundation"])
        self.assertIn("action-code-support_drawings", digging)
        self.assertNotIn("action-code-underpinning", digging, "no underpinning picked, no underpinning duty")
        self.assertIn("action-code-underpinning", ids(["excavation", "underpinning"]))

    def test_unknown_scope_keeps_code_duties_with_a_note(self):
        items = {a["id"]: a for a in build_actions({**self.profile, "work_types": None})}
        self.assertIn("could not be determined", items["action-code-underpinning"]["why"])

    def test_every_code_row_has_a_scope_condition(self):
        from actions.build import CODE_SCOPE
        from checklist.checklist_rules import RULES
        self.assertEqual({r.condition for r in RULES} - set(CODE_SCOPE), set())

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

        with mock.patch.dict(sys.modules, {"site_profile.router": None}):  # PR 6 not landed
            r = TestClient(app).get("/api/sites/3052110073/actions")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get(FIXTURE_HEADER), "true")

    def test_every_discipline_bucket_exists(self):
        self.assertEqual(set(group_by_discipline(self.items)), set(DISCIPLINE_ORDER))


class TestActionsFollowTheChosenJob(unittest.TestCase):
    """The project screen's setup picks a job type and scope; the checklist must follow them."""

    def _fake_profile_for(self, bbl, job_type=None):
        profile = dict(_profile(), work_types=[])
        if job_type is not None:
            profile["job_type"] = job_type
        return profile, False

    def _rules(self, **options):
        import actions
        with mock.patch.object(actions, "_profile_for", side_effect=self._fake_profile_for):
            return {a["source_rule"] for a in actions.actions_for("3052110073", **options)}

    def test_chosen_work_types_replace_inferred_ones(self):
        self.assertIn("actions:weather-open-excavation-rain", self._rules(work_types=["excavation"]))
        self.assertNotIn("actions:weather-open-excavation-rain", self._rules(work_types=["facade"]))

    def test_chosen_job_type_reaches_the_rules(self):
        self.assertIn("actions:fire-egress-during-construction", self._rules(job_type="alteration"))
        self.assertNotIn("actions:fire-egress-during-construction", self._rules(job_type="new_building"))

    def test_router_rejects_unknown_work_type(self):
        from fastapi.testclient import TestClient

        from api.main import app

        r = TestClient(app).get("/api/sites/3052110073/actions", params={"work_types": "excavation,digging"})
        self.assertEqual(r.status_code, 422, r.text)
        self.assertIn("support_of_excavation", r.text)


class TestDepthAndHeight(unittest.TestCase):
    """Setup's dig depth and new building height decide the survey, monitoring, PE and facade rows."""

    def setUp(self):
        neighbor = {"bbl": "3000000002", "bins": [], "attached": True, "year_built": 1925, "floors": 3}
        self.p = dict(_profile(), work_types=["excavation", "foundation"], neighbors=[neighbor])

    def rows(self, **extra):
        return {a["id"]: a for a in build_actions({**self.p, **extra})}

    def test_survey_not_required_under_5ft(self):
        self.assertNotIn("action-code-survey", self.rows(excavation_depth_ft=4.9))

    def test_survey_required_at_10ft_next_door(self):
        self.assertIn("action-code-survey", self.rows(excavation_depth_ft=10))

    def test_no_depth_keeps_row_as_needs_input(self):
        self.assertIn("needs input: dig depth", self.rows()["action-code-survey"]["why"].lower())

    def test_monitoring_applies_over_5ft(self):
        row = self.rows(excavation_depth_ft=10)["action-code-monitoring"]
        self.assertNotIn("needs input", row["why"].lower())

    def test_over_20ft_support_drawings_need_state_pe(self):
        self.assertIn("NY State PE", self.rows(excavation_depth_ft=21)["action-code-support_drawings"]["why"])

    def test_proposed_storeys_drive_facade_cycle(self):
        low = dict(self.p["lot"], floors=2)
        self.assertNotIn("action-facade-inspection-cycle", self.rows(lot=low))
        self.assertIn("action-facade-inspection-cycle", self.rows(lot=low, proposed_storeys=9))

    def test_no_neighbors_is_needs_input_not_applies(self):
        self.assertIn("needs input", self.rows(neighbors=[], excavation_depth_ft=8)["action-code-survey"]["why"].lower())

    def test_router_rejects_negative_depth(self):
        from fastapi.testclient import TestClient

        from api.main import app

        r = TestClient(app).get("/api/sites/3052110073/actions", params={"excavation_depth_ft": "-1"})
        self.assertEqual(r.status_code, 422, r.text)


if __name__ == "__main__":
    unittest.main()


class TestPhases(unittest.TestCase):
    """Each item says when it's due: from the code text where it states timing, else the rule's stage."""

    def test_code_rows_use_the_codes_own_timing(self):
        from actions.phases import phase_for
        self.assertEqual(phase_for("checklist:notice"), ("notice", "60 days before work"))
        self.assertEqual(phase_for("checklist:survey")[0], "before_excavation")
        self.assertEqual(phase_for("checklist:monitoring"), ("during_work", "During excavation"))

    def test_hazard_rows_use_their_earliest_stage(self):
        from actions.phases import phase_for
        self.assertEqual(phase_for("actions:x", ["pre_filing", "construction"]), ("filing", "Before filing"))
        self.assertEqual(phase_for("actions:y", ["construction"]), ("during_work", "During work"))

    def test_document_rows_and_unknowns(self):
        from actions.phases import phase_for
        self.assertEqual(phase_for("actions:geotech:dewatering")[0], "filing")
        self.assertEqual(phase_for("actions:model:lot-line-notice")[0], "notice")
        self.assertEqual(phase_for("something-else")[0], "design")

    def test_every_built_item_has_a_phase(self):
        phases = {"design", "filing", "notice", "before_excavation", "during_work"}
        for a in build_actions(_profile()):
            self.assertIn(a.get("phase"), phases, a["id"])
            self.assertTrue(a.get("when"), a["id"])


class TestSiteContext(unittest.TestCase):
    """Rows about the neighbors name them; rows the records speak to say what the records show."""

    def setUp(self):
        n = lambda addr, year, floors, attached=True: {"bbl": addr, "bins": [], "address": addr, "attached": attached,  # noqa: E731
                                                       "year_built": year, "floors": floors}
        sig = lambda title, date: {"id": title + date, "hazard": "structural", "severity": 0, "title": title,  # noqa: E731
                                   "explanation": "", "record_ids": [], "source_name": "DOB Complaints Received",
                                   "date": date}
        self.p = dict(_profile(), work_types=["excavation", "foundation"], excavation_depth_ft=10,
                      neighbors=[n("19 MARCUS GARVEY BLVD", 1931, 3.0), n("296 ELLERY STREET", 1931, 3.0),
                                 n(None, 0, None)],
                      signals=[sig("Excavation undermining an adjacent building", "2026-02-11"),
                               sig("Excavation undermining an adjacent building (touching lot 17 MARCUS GARVEY BLVD)", "2026-08-21"),
                               sig("Adjacent building not protected", "2026-05-15"),
                               sig("Scaffold or material handling cited", "2026-10-08")])

    def rows(self):
        return {a["id"]: a for a in build_actions(self.p)}

    def test_neighbor_rows_name_the_buildings(self):
        applies = self.rows()["action-code-survey"]["applies_to"]
        self.assertEqual(applies[0], "19 Marcus Garvey Blvd (built 1931, 3 storeys, attached)")
        self.assertIn("296 Ellery Street (built 1931, 3 storeys, attached)", applies)
        self.assertIn("an unnamed lot (attached)", applies)

    def test_rows_not_about_neighbors_name_none(self):
        self.assertEqual(self.rows()["action-code-support_drawings"].get("applies_to"), [])

    def test_matching_records_are_counted_with_their_dates(self):
        ev = self.rows()["action-code-monitoring"]["evidence"]
        self.assertIn("2 'Excavation undermining an adjacent building'", ev)
        self.assertIn("1 'Adjacent building not protected'", ev)
        self.assertIn("Feb 2026–Aug 2026", ev)
        self.assertIn("reports, not findings", ev)
        self.assertNotIn("Scaffold", ev)

    def test_no_matching_records_means_no_evidence(self):
        self.p["signals"] = []
        self.assertIsNone(self.rows()["action-code-monitoring"]["evidence"])
