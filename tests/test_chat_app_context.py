"""The chat's site loader over the app's own site functions: real data, the labelled sample, and failures."""

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException

from api.routers.chat import chat_app_context, chat_service
from api.routers.chat.chat_app_context import SAMPLE_OF_ANOTHER_SITE, app_context
from api.routers.chat.chat_fixture_context import fixture_context
from api.routers.chat.chat_models import ChatRequest
from api.routers.chat.chat_site_context import SiteContextUnavailable
from api.routers.router_data import DataUnavailable, LoadedData

FIXTURES = Path(__file__).resolve().parents[1] / "contracts" / "fixtures"
SAMPLE_BBL = "3052110074"
OTHER_BBL = "1000010001"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def site_parts(sample=(), failing=(), bbl=SAMPLE_BBL):
    """A stand-in for load_site_part: every part answers from the fixtures, as real data unless named in `sample`."""
    names = {"profile": "site_profile", "similar": "similar_cases", "warnings": "warnings", "actions": "actions"}

    def load(part, asked_bbl, **options):
        if part in failing:
            raise DataUnavailable(f"{part} module could not answer (RuntimeError)")
        data = fixture(names[part])
        if part == "profile":
            data = {**data, "bbl": bbl if part not in sample else SAMPLE_BBL}
        return LoadedData(data, part in sample)
    return mock.patch.object(chat_app_context, "load_site_part", side_effect=load)


def kinds(answer):
    return [part.code if part.kind == "notice" else part.kind for part in answer.parts][1:]


def ask(question, bbl):
    return chat_service.answer(ChatRequest(bbl=bbl, question=question), app_context, None)


class AppContextTests(unittest.TestCase):
    def test_real_parts_are_read_for_the_lot_asked_about_and_not_marked_sample(self):
        with site_parts(bbl=OTHER_BBL) as load:
            context = app_context(OTHER_BBL, "new_building", "design", "2026-06-01")
        self.assertEqual((context.sample, context.profile.status, context.warnings.status, context.actions.status, context.similar.status),
                         (False, "ok", "ok", "ok", "ok"))
        self.assertEqual({call.args[0]: call.kwargs for call in load.call_args_list}, {
            "profile": {"job_type": "new_building", "stage": "design", "as_of": "2026-06-01"}, "similar": {},
            "warnings": {"as_of": "2026-06-01"}, "actions": {"stage": "design"}})
        self.assertEqual({call.args[1] for call in load.call_args_list}, {OTHER_BBL})
        self.assertEqual(context.similar.value[0].keys(), {"similar", "case"})

    def test_sample_parts_are_used_for_the_sample_site_and_marked(self):
        with site_parts(sample=("profile", "similar", "warnings", "actions")):
            context = app_context(SAMPLE_BBL, None, None, None)
        self.assertEqual((context.sample, context.warnings.status), (True, "ok"))

    def test_sample_data_is_never_shown_as_another_sites(self):
        with site_parts(sample=("profile",)), self.assertRaises(SiteContextUnavailable):
            app_context(OTHER_BBL, None, None, None)
        with site_parts(sample=("warnings", "actions"), bbl=OTHER_BBL):
            context = app_context(OTHER_BBL, None, None, None)
            self.assertEqual((context.sample, context.warnings.status, context.warnings.reason), (False, "not_available", SAMPLE_OF_ANOTHER_SITE))
            self.assertEqual(kinds(ask("Any early warnings?", OTHER_BBL)), ["unknown"])
            self.assertEqual(kinds(ask("What are the action items?", OTHER_BBL)), ["unknown"])
            self.assertIn("case", kinds(ask("Any similar cases?", OTHER_BBL)))

    def test_a_part_that_fails_is_a_failure_never_an_empty_list(self):
        with site_parts(failing=("warnings", "similar"), bbl=OTHER_BBL):
            context = app_context(OTHER_BBL, None, None, None)
            self.assertEqual((context.warnings.status, context.similar.status), ("error", "error"))
            self.assertIn("could not answer", context.warnings.reason)
            self.assertEqual(kinds(ask("Any early warnings?", OTHER_BBL)), ["unknown"])
            self.assertEqual(kinds(ask("Any similar cases?", OTHER_BBL)), ["unknown"])
        with site_parts(failing=("profile",)), self.assertRaises(SiteContextUnavailable):
            app_context(SAMPLE_BBL, None, None, None)

    def test_a_broken_layer_file_is_a_failure_and_a_bad_lot_is_refused(self):
        with site_parts(), mock.patch.object(chat_app_context, "load_layer_catalog", side_effect=DataUnavailable("catalog.json is broken")):
            self.assertEqual(app_context(SAMPLE_BBL, None, None, None).layers.status, "error")
        with self.assertRaises(HTTPException):
            app_context("9000000000", None, None, None)


class FixtureContextTests(unittest.TestCase):
    """The sample-site loader the saved answers are built from."""

    def test_it_describes_the_sample_site_only_and_says_it_is_sample(self):
        context = fixture_context(SAMPLE_BBL, None, None, None)
        self.assertEqual((context.sample, context.profile.status, context.records), (True, "ok", []))
        with self.assertRaises(SiteContextUnavailable):
            fixture_context(OTHER_BBL, None, None, None)


class AppRouteSampleLabelTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from api.main import app
        self.client = TestClient(app)
        patch = mock.patch.dict(os.environ, {"FORESITE_CHAT_LIVE": "0"})
        patch.start()
        self.addCleanup(patch.stop)

    def post(self, bbl):
        return self.client.post("/api/chat", json={"question": "Any early warnings?", "bbl": bbl})

    def test_the_sample_header_follows_the_data_the_answer_rests_on(self):
        with site_parts(sample=("profile", "similar", "warnings", "actions")):
            self.assertEqual(self.post(SAMPLE_BBL).headers.get("X-ForeSite-Fixture"), "true")
        with site_parts(bbl=OTHER_BBL):
            real = self.post(OTHER_BBL)
        self.assertEqual((real.status_code, real.headers.get("X-ForeSite-Fixture")), (200, None))
        self.assertEqual(self.post("9000000000").status_code, 422)


if __name__ == "__main__":
    unittest.main()
