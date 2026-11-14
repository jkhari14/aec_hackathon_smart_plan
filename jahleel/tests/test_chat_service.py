"""Offline tests for one question end to end, against a scripted stand-in for the model."""

import unittest
from datetime import date

from pydantic import ValidationError

from jahleel.api.chat import chat_service
from jahleel.api.chat.chat_models import (
    MAX_EARLIER_EXCHANGES, MAX_HISTORY_CHARS, MAX_QUESTION_CHARS, ChatAnswer, ChatRequest,
)
from jahleel.api.chat.chat_saved_examples import SAVED
from jahleel.tests.chat_test_support import (
    COLLAPSE_DAY_VIOLATION, S3, SITE, SITE_BBL, WEB, ScriptedModel, check, notice_item, says,
)

GOOD = says("Filing B01330433-S3 was filed 2026-02-24.", S3)
UNSOURCED = says("The neighbors were told in June.")


def ask(question="What is on file?", model=None, **fields):
    return chat_service.answer(ChatRequest(slug=SITE, question=question, **fields), model)


def kinds(answer):
    return [part.code if part.kind == "notice" else part.kind for part in answer.parts]


class LiveTests(unittest.TestCase):
    def test_a_sourced_answer_comes_back_typed(self):
        model = ScriptedModel([GOOD, check(SITE_BBL, "hpd_violations")])
        answer = ask(model=model)
        self.assertEqual((answer.mode, answer.web_search), ("live", "not_used"))
        self.assertEqual(kinds(answer), ["record", "not_found"])
        self.assertTrue(answer.plain_text.startswith("From the public record: Filing B01330433-S3"))
        ChatAnswer.model_validate(answer.model_dump())

    def test_the_model_reads_the_same_brief_and_question_and_no_key(self):
        model = ScriptedModel([GOOD])
        ask("Which filings cover earth work?", model=model, history=[{"question": "Hi", "answer": "Hello."}])
        asked = model.opened_with
        self.assertIn("[dob_now_filings:B01330433-S3]", asked["system"][1]["text"])
        self.assertEqual([m["role"] for m in asked["messages"]], ["user", "assistant", "user"])
        self.assertEqual(asked["messages"][-1]["content"], "Which filings cover earth work?")
        self.assertTrue(asked["allow_web"])

    def test_problems_go_back_once_and_the_corrected_answer_is_served(self):
        model = ScriptedModel([GOOD, UNSOURCED], [GOOD])
        answer = ask(model=model)
        self.assertEqual(kinds(answer), ["record"])
        self.assertIsNone(model.problems_seen[0])
        self.assertIn("no source", model.problems_seen[1][0])

    def test_what_still_fails_after_the_retry_is_held_back_and_said(self):
        model = ScriptedModel([GOOD, UNSOURCED], [GOOD, UNSOURCED])
        answer = ask(model=model)
        self.assertEqual(kinds(answer), ["record", "held_back"])
        self.assertNotIn("neighbors were told", answer.model_dump_json())
        self.assertEqual(len(model.problems_seen), 2)  # one retry, not a loop

    def test_nothing_sourced_says_no_answer(self):
        answer = ask(model=ScriptedModel([UNSOURCED], [UNSOURCED]))
        self.assertEqual(kinds(answer), ["held_back", "no_answer"])

    def test_a_web_lead_is_served_as_a_lead(self):
        model = ScriptedModel([says("The city publishes the 2022 construction codes.", WEB.url)], web_results=[WEB], searched=True)
        answer = ask(model=model)
        self.assertEqual((kinds(answer), answer.web_search), (["lead"], "used"))
        self.assertTrue(answer.plain_text.startswith("From the web, not checked by us: "))

    def test_a_verdict_or_a_name_question_gets_the_notice_whatever_the_model_does(self):
        self.assertEqual(kinds(ask("Is it safe to dig here?", model=ScriptedModel([GOOD]))), ["not_a_determination", "record"])
        self.assertEqual(kinds(ask("Who owns the site?", model=ScriptedModel([GOOD]))), ["names_withheld", "record"])
        both = ask("Is it safe?", model=ScriptedModel([notice_item("not_a_determination"), GOOD]))
        self.assertEqual(kinds(both), ["not_a_determination", "record"])  # said once


class AsOfTests(unittest.TestCase):
    def test_a_replay_gets_no_web_search_and_says_so(self):
        model = ScriptedModel([GOOD])
        answer = ask(model=model, as_of=date(2026, 6, 1))
        self.assertFalse(model.opened_with["allow_web"])
        self.assertEqual((answer.as_of, answer.web_search), ("2026-06-01", "off_as_of"))
        self.assertEqual(kinds(answer), ["record", "web_off_as_of"])

    def test_a_replay_does_not_reveal_a_later_record_even_if_the_model_names_it(self):
        later = says('A DOB violation reads "FULL STOP WORK ORDER DUE TO COLLAPSE".', COLLAPSE_DAY_VIOLATION)
        answer = ask(model=ScriptedModel([GOOD, later], [GOOD, later]), as_of=date(2026, 6, 1))
        self.assertEqual(kinds(answer), ["record", "held_back", "web_off_as_of"])
        self.assertNotIn("COLLAPSE", answer.model_dump_json())
        self.assertNotIn("2824347", answer.model_dump_json())


class FallbackTests(unittest.TestCase):
    def test_no_model_gives_a_labeled_mock_answer_not_a_crash(self):
        answer = ask("Anything at all?")
        self.assertEqual((answer.mode, kinds(answer), answer.web_search), ("mock", ["mock_answer", "mock_no_match"], "off"))
        self.assertEqual([e.id for e in answer.examples], [e["id"] for e in SAVED[SITE]])

    def test_a_failed_live_call_gives_the_fallback_and_shows_no_error_text(self):
        with self.assertLogs("preflight.chat", level="WARNING"):
            answer = ask(model=ScriptedModel(fails=RuntimeError("sk-secret-looking-detail")))
        self.assertEqual((answer.mode, kinds(answer)[:2]), ("mock", ["live_failed", "mock_answer"]))
        self.assertNotIn("secret", answer.model_dump_json())

    def test_every_saved_example_is_fully_sourced_as_pulled(self):
        for slug, examples in SAVED.items():
            for example in examples:
                answer = chat_service.answer(ChatRequest(slug=slug, example_id=example["id"]))
                self.assertEqual(answer.mode, "saved")
                self.assertEqual(answer.parts[0].code, "saved_example")
                self.assertNotIn("held_back", kinds(answer), f"{slug}/{example['id']}")
                self.assertNotIn("after_as_of", kinds(answer))
                self.assertEqual(answer.question, example["question"])

    def test_a_saved_example_in_a_replay_drops_what_came_later_and_says_so(self):
        answer = chat_service.answer(ChatRequest(slug=SITE, example_id="stop_work", as_of=date(2026, 6, 1)))
        self.assertIn("after_as_of", kinds(answer))
        self.assertNotIn("held_back", kinds(answer))
        self.assertNotIn("COLLAPSE", answer.model_dump_json())
        for slug, examples in SAVED.items():
            for day in (date(2026, 6, 1), date(2026, 11, 11)):
                for example in examples:
                    replay = chat_service.answer(ChatRequest(slug=slug, example_id=example["id"], as_of=day))
                    dated = [s.date for p in replay.parts if p.kind == "record" for s in p.sources if s.date]
                    self.assertTrue(all(d < str(day) for d in dated), f"{slug}/{example['id']} {day}")

    def test_an_unknown_example_or_site_is_refused(self):
        with self.assertRaises(LookupError):
            chat_service.answer(ChatRequest(slug=SITE, example_id="nope"))
        with self.assertRaises(FileNotFoundError):
            chat_service.answer(ChatRequest(slug="no-such-site", question="x"))
        with self.assertRaises(ValueError):
            chat_service.answer(ChatRequest(slug="../README", question="x"))


class LimitTests(unittest.TestCase):
    def refused(self, **fields):
        with self.assertRaises(ValidationError):
            ChatRequest(slug=SITE, **fields)

    def test_an_oversized_question_is_refused_not_cut(self):
        ChatRequest(slug=SITE, question="x" * MAX_QUESTION_CHARS)
        self.refused(question="x" * (MAX_QUESTION_CHARS + 1))

    def test_an_over_long_conversation_is_refused(self):
        turn = {"question": "q", "answer": "a"}
        ChatRequest(slug=SITE, question="x", history=[turn] * MAX_EARLIER_EXCHANGES)
        self.refused(question="x", history=[turn] * (MAX_EARLIER_EXCHANGES + 1))

    def test_an_oversized_history_is_refused(self):
        big = {"question": "q", "answer": "a" * 3999}
        self.assertGreater(4 * 4000, MAX_HISTORY_CHARS)
        self.refused(question="x", history=[big] * 4)
        self.refused(question="x", history=[{"question": "q", "answer": "a" * 4001}])

    def test_an_empty_question_or_an_unknown_field_is_refused(self):
        self.refused(question="   ")
        self.refused(question="x", api_key="not-a-real-key")
        self.refused(question="x", project_type="demolition")


if __name__ == "__main__":
    unittest.main()
