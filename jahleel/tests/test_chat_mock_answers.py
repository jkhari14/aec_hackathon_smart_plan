"""Offline tests for the mock: what a typed question gets while the server has no model key."""

import unittest
from datetime import date

from jahleel.api.brief.brief_build import build_brief
from jahleel.api.chat import chat_mock_answers, chat_service
from jahleel.api.chat.chat_answer_build import build_parts
from jahleel.api.chat.chat_brief_view import BriefView
from jahleel.api.chat.chat_models import ChatRequest
from jahleel.tests.chat_test_support import COLLAPSE_DAY_VIOLATION, NEXT_DOOR_BBL, SITE, SITE_BBL

JUNE_1 = date(2026, 6, 1)


def ask(question, **fields):
    return chat_service.answer(ChatRequest(slug=SITE, question=question, **fields))


def kinds(answer):
    return [part.code if part.kind == "notice" else part.kind for part in answer.parts]


def sourced(answer):
    return [part for part in answer.parts if part.kind != "notice"]


class MockTests(unittest.TestCase):
    def test_every_mock_answer_says_it_is_one_and_uses_no_web(self):
        for question in ("How many ECB violations?", "Which duties apply?", "What is the weather?"):
            answer = ask(question)
            self.assertEqual((answer.mode, answer.web_search, answer.usage), ("mock", "off", None))
            self.assertEqual(answer.parts[0].code, "mock_answer")
            self.assertIn("no model was called", answer.plain_text)

    def test_a_count_question_gets_the_servers_count_for_the_site(self):
        [part] = sourced(ask("How many ECB violations are on the site?"))
        self.assertEqual(part.kind, "record")
        self.assertTrue(part.text.startswith("4 records in ECB violations"))
        self.assertEqual(part.sources[0].bbl, SITE_BBL)

    def test_a_lot_named_by_its_address_is_the_lot_counted(self):
        parts = sourced(ask("How many complaints at 1321 Flatbush Avenue?"))
        self.assertEqual([p.kind for p in parts], ["record", "not_found"])
        self.assertEqual(parts[1].queried[0].bbl, NEXT_DOOR_BBL)
        self.assertIn("complaints_overlap", kinds(ask("How many complaints at 1321 Flatbush Avenue?")))

    def test_a_neighbor_question_counts_each_touching_lot_and_stays_within_the_item_limit(self):
        parts = sourced(ask("What violations do the neighbors have?"))
        self.assertLessEqual(len(parts), 12)
        lots = {(p.sources[0].bbl if p.kind == "record" else p.queried[0].bbl) for p in parts}
        self.assertEqual(len(lots), 5)
        self.assertNotIn(SITE_BBL, lots)

    def test_a_failed_query_is_unknown_in_a_mock_answer_too(self):
        brief = build_brief(SITE)
        for dataset in brief.site.datasets:
            if dataset.key == "ecb_violations":
                dataset.status, dataset.count = "error", None
        view = BriefView(brief)
        items = chat_mock_answers.propose(view, SITE, "How many ECB violations?")
        [part] = build_parts(view, {"items": items}, []).parts
        self.assertEqual(part.kind, "unknown")
        self.assertIn("This is not zero", part.text)

    def test_a_checklist_question_reports_rows_with_their_status_and_cites_them(self):
        parts = sourced(ask("What are the open gaps?"))
        self.assertEqual([p.sources[0].ref for p in parts],
                         ["row:foundation_protection", "row:support_drawings", "row:support_basis"])
        self.assertTrue(all("proof has not been provided to PreFlight" in p.text for p in parts))

    def test_a_reported_document_is_shown_as_a_lead_never_as_a_record(self):
        parts = sourced(ask("Was the adjoining owner notified?"))
        self.assertEqual([p.kind for p in parts], ["record", "lead"])
        self.assertEqual(parts[1].sources[0].type, "reported_document")
        self.assertEqual([p.kind for p in sourced(ask("Was the adjoining owner notified?", as_of=JUNE_1))], ["record"])

    def test_a_question_close_to_a_saved_example_gets_that_example(self):
        answer = ask("Does the record mention a stop-work order?")
        self.assertIn("cause_not_established", kinds(answer))
        self.assertTrue(any(COLLAPSE_DAY_VIOLATION in [s.ref for s in p.sources] for p in sourced(answer) if p.kind == "record"))

    def test_a_replay_does_not_reveal_a_later_record_and_counts_only_earlier_ones(self):
        answer = ask("Does the record mention a stop-work order?", as_of=JUNE_1)
        self.assertNotIn("2824347", answer.model_dump_json())
        self.assertNotIn("COLLAPSE", answer.model_dump_json().upper())
        self.assertIn("after_as_of", kinds(answer))
        [part] = sourced(ask("How many ECB violations are on the site?", as_of=JUNE_1))
        self.assertTrue(part.text.startswith("3 records"))

    def test_a_verdict_or_a_name_question_gets_the_notice(self):
        self.assertEqual(kinds(ask("Is it safe to dig here?"))[:2], ["mock_answer", "not_a_determination"])
        self.assertEqual(kinds(ask("Who is the contractor?")), ["mock_answer", "names_withheld", "mock_no_match"])

    def test_nothing_is_made_up_for_a_question_nothing_matches(self):
        for question in ("What is the weather?", "What happened here?", "x"):
            answer = ask(question)
            self.assertEqual(sourced(answer), [])
            self.assertEqual(kinds(answer)[-1], "mock_no_match")
            self.assertTrue(answer.examples)

    def test_every_part_of_every_mock_answer_has_a_source(self):
        questions = ["How many records are there?", "Any filings?", "Which duties apply?", "Tell me about underpinning",
                     "What do we know about the buildings touching the site?", "Is it safe to excavate here?"]
        for as_of in (None, JUNE_1):
            for question in questions:
                answer = ask(question, as_of=as_of)
                self.assertNotIn("held_back", kinds(answer), (question, as_of))
                for part in sourced(answer):
                    self.assertTrue(getattr(part, "sources", None) or getattr(part, "queried", None), (question, part))


if __name__ == "__main__":
    unittest.main()
