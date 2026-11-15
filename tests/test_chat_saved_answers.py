"""The answers the web app shows when it cannot reach the API: built from the site's data, labeled, and kept up to date."""

import json
import unittest

from api import contracts
from api.routers.chat.chat_saved_answers_export import (
    SAMPLE_SITE_BBL, SAMPLE_SITE_QUESTIONS, SAVED_ANSWERS_FILE, saved_answers, saved_answers_text,
)
from api.routers.chat.chat_site_context import Loaded
from tests.chat_test_support import SITE_BBL, loader


class SavedAnswerTests(unittest.TestCase):
    def test_the_file_the_web_app_ships_is_up_to_date(self):
        self.assertEqual(SAVED_ANSWERS_FILE.read_text(), saved_answers_text(),
                         "run: python -m api.routers.chat.chat_saved_answers_export")

    def test_every_saved_answer_fits_the_contract_and_says_it_is_saved(self):
        saved = json.loads(SAVED_ANSWERS_FILE.read_text())
        self.assertEqual((saved["site_bbl"], [a["question"] for a in saved["answers"]]), (SAMPLE_SITE_BBL, list(SAMPLE_SITE_QUESTIONS)))
        for entry in saved["answers"]:
            response = contracts.ChatResponse.model_validate(entry["response"])
            first = response.answer_parts[0]
            self.assertEqual((first.kind, first.text.startswith("A saved example answer"), response.offline), ("notice", True, True))
            self.assertFalse(any("mock answer" in part.text.lower() for part in response.answer_parts))
            self.assertTrue(any(part.kind != "notice" for part in response.answer_parts), entry["question"])
            self.assertEqual(response.actions, [])  # a saved answer never moves the page

    def test_a_failed_load_is_saved_as_unknown_and_a_question_nothing_matches_is_refused(self):
        failed = saved_answers(loader(warnings=Loaded.failed("timeout")), SITE_BBL, ("What early warnings are there?",))
        self.assertEqual([part["kind"] for part in failed["answers"][0]["response"]["answer_parts"]], ["notice", "unknown"])
        with self.assertRaises(ValueError):
            saved_answers(loader(), SITE_BBL, ("What's the weather like?",))


if __name__ == "__main__":
    unittest.main()
