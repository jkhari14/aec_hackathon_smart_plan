"""Offline tests for one question end to end: live with a scripted model, the mock, the model's tools, the route."""

import os
import unittest
from unittest import mock

from fastapi import HTTPException
from pydantic import ValidationError

from api.routers.chat import chat_service, chat_tools
from api.routers.chat.chat_model_call import AnthropicChatModel
from api.routers.chat.chat_models import ChatRequest
from api.routers.chat.chat_site_context import Loaded, SiteContextUnavailable
from api.routers.chat.chat_site_view import SiteView
from tests.chat_test_support import (
    JULY_COMPLAINT, JUNE_1, LATE_CASE, MARCH_WARNING, OLD_CASE, SAFEGUARD, SITE_BBL, STOP_WORK, SURVEY_ACTION, WEB,
    FakeAnthropicClient, ScriptedModel, action, example_context, item, loader, response, says, submit_block, tool_call,
)

GOOD = says("A stop work order was issued on 2026-04-20.", STOP_WORK)
UNSOURCED = says("Everything looks fine here.")


def ask(question="What is on file?", model=None, load=None, **fields):
    return chat_service.answer(ChatRequest(bbl=SITE_BBL, question=question, **fields), load or loader(), model)


def kinds(answer):
    return [part.code if part.kind == "notice" else part.kind for part in answer.parts]


class LiveTests(unittest.TestCase):
    def test_a_sourced_answer_is_shown_with_its_kinds_and_actions(self):
        model = ScriptedModel({"items": [GOOD, says("A past case resembles this site.", OLD_CASE)],
                               "actions": [action("fly_to", ref=OLD_CASE)]})
        answer = ask(model=model)
        self.assertEqual((answer.mode, answer.web_search), ("live", "not_used"))
        self.assertEqual(kinds(answer), ["record", "case", "not_a_prediction", "page_action"])
        self.assertEqual([a.type for a in answer.actions], ["fly_to"])
        self.assertTrue(answer.plain_text.startswith("From the public record: A stop work order"))
        self.assertIn("From the case library, as publicly reported: ", answer.plain_text)

    def test_the_model_reads_the_site_data_and_gets_both_search_tools(self):
        model = ScriptedModel([GOOD])
        ask("Which filings cover earth work?", model=model, history=[{"question": "Hi", "answer": "Hello."}])
        opened = model.opened_with
        self.assertIn(f"[{STOP_WORK}]", opened["system"][1]["text"])
        self.assertEqual(opened["system"][1]["cache_control"], {"type": "ephemeral"})
        self.assertEqual([m["content"] for m in opened["messages"]], ["Hi", "Hello.", "Which filings cover earth work?"])
        self.assertEqual([t.schema["name"] for t in opened["client_tools"]], ["search_records", "search_similar_cases"])
        self.assertTrue(opened["allow_web"])

    def test_one_correction_round_then_what_still_fails_is_dropped_and_said(self):
        fixed = ScriptedModel([GOOD, UNSOURCED], [GOOD])
        self.assertEqual(kinds(ask(model=fixed)), ["record"])
        self.assertIn("no source", fixed.problems_seen[1][0])
        still = ScriptedModel([GOOD, UNSOURCED], [GOOD, UNSOURCED])
        self.assertEqual(kinds(ask(model=still)), ["record", "held_back"])
        self.assertEqual(kinds(ask(model=ScriptedModel([UNSOURCED], [UNSOURCED]))), ["held_back", "no_answer"])

    def test_a_dropped_action_is_said_and_an_action_alone_is_an_answer(self):
        bad = {"items": [GOOD], "actions": [action("toggle_layer", layer_id="made_up")]}
        self.assertEqual(kinds(ask(model=ScriptedModel(bad, bad))), ["record", "action_dropped"])
        only = ScriptedModel({"items": [], "actions": [action("toggle_layer", layer_id="sandy_inundation")]})
        answer = ask("Show the Sandy layer", model=only)
        self.assertEqual((kinds(answer), len(answer.actions)), (["page_action"], 1))

    def test_a_replay_has_no_web_search_and_no_later_material(self):
        model = ScriptedModel([says("A complaint is on file.", JULY_COMPLAINT), says("A later case.", LATE_CASE), GOOD],
                              [GOOD])
        answer = ask(model=model, as_of=JUNE_1)
        self.assertFalse(model.opened_with["allow_web"])
        self.assertEqual((answer.as_of, answer.web_search, kinds(answer)), (JUNE_1, "off_as_of", ["record", "web_off_as_of"]))
        for later in ("C301", "ex-wall-2026", "2026-07-02", "Permit issued"):
            self.assertNotIn(later, model.opened_with["system"][1]["text"] + answer.model_dump_json())

    def test_a_web_statement_is_a_lead_and_never_a_record(self):
        model = ScriptedModel([says("The city publishes the 2022 construction codes.", WEB.url)], web_results=[WEB], searched=True)
        answer = ask(model=model)
        self.assertEqual((kinds(answer), answer.web_search), (["lead"], "used"))
        self.assertTrue(answer.plain_text.startswith("From the web, not checked by us: "))

    def test_questions_asking_for_a_verdict_a_forecast_or_a_name_get_the_notice(self):
        self.assertEqual(kinds(ask("Is it safe to dig here?", model=ScriptedModel([GOOD])))[0], "not_a_determination")
        self.assertEqual(kinds(ask("Will this building collapse?", model=ScriptedModel([GOOD])))[0], "not_a_prediction")
        self.assertEqual(kinds(ask("Who is the contractor?", model=ScriptedModel([GOOD])))[0], "names_withheld")

    def test_a_failed_live_call_falls_back_to_a_labeled_mock(self):
        answer = ask("Search the records for fence", model=ScriptedModel(fails=RuntimeError("boom")))
        self.assertEqual((answer.mode, kinds(answer)[:2]), ("mock", ["live_failed", "mock_answer"]))
        self.assertNotIn("boom", answer.model_dump_json())

    def test_an_unknown_site_and_a_saved_example_are_refused(self):
        def missing(*_):
            raise SiteContextUnavailable("no such lot")
        with self.assertRaises(SiteContextUnavailable):
            ask(load=missing)
        with self.assertRaises(LookupError):
            ask(question="", example_id="x")


class MockTests(unittest.TestCase):
    def body(self, question, **fields):
        answer = ask(question, **fields)
        self.assertEqual((answer.mode, answer.parts[0].code, answer.web_search, answer.usage), ("mock", "mock_answer", "off", None))
        return answer, kinds(answer)[1:]

    def test_searches_counts_warnings_and_action_items_come_from_the_site_data(self):
        self.assertEqual(self.body("Search the records for fence")[1], ["record", "unknown"])
        self.assertEqual(self.body("How many ECB violations are there?")[1], ["record"])
        self.assertEqual(self.body("Any similar cases with underpinning?")[1], ["case", "not_a_prediction"])
        self.assertEqual(self.body("What warnings are there?")[1], ["warning", "warning", "not_a_prediction"])
        answer, got = self.body("What are the action items for the structural engineer?")
        self.assertEqual((got, answer.parts[1].sources[0].ref), (["action"], SURVEY_ACTION))

    def test_life_safety_action_items_come_first(self):
        answer, _ = self.body("What should we do next?")
        self.assertEqual([p.sources[0].life_safety for p in answer.parts[1:]], [True, False])

    def test_page_actions_are_matched_and_checked(self):
        answer, got = self.body("Show the Sandy layer")
        self.assertEqual((got, [(a.type, a.layer_id, a.on) for a in answer.actions]), (["page_action"], [("toggle_layer", "sandy_inundation", True)]))
        answer, _ = self.body("hide the sandy layer")
        self.assertFalse(answer.actions[0].on)
        answer, _ = self.body("Fly to case ex-underpinning-2019")
        self.assertEqual(answer.actions[0].ref, OLD_CASE)
        answer, got = self.body("Pin that", project_id="p1", history=[{"question": "q", "answer": "a"}])
        self.assertEqual((got, answer.actions[0].target), (["page_action"], "previous"))
        self.assertEqual(self.body("Pin that", history=[{"question": "q", "answer": "a"}])[1], ["pin_needs_project"])
        self.assertEqual(self.body("Pin that", project_id="p1")[1], ["pin_needs_answer"])

    def test_nothing_is_made_up_when_no_keyword_matches_or_a_piece_did_not_load(self):
        self.assertEqual(self.body("What's the weather like?")[1], ["mock_no_match"])
        self.assertEqual(self.body("Any similar cases?", load=loader(similar=Loaded.failed("timeout")))[1], ["unknown"])
        self.assertEqual(self.body("What warnings are there?", load=loader(warnings=Loaded.failed("timeout")))[1], ["mock_no_match"])

    def test_a_replay_mock_stays_before_the_day(self):
        answer, got = self.body("What warnings are there?", as_of=JUNE_1)
        self.assertEqual(got, ["warning", "not_a_prediction"])
        self.assertEqual(answer.parts[1].sources[0].ref, MARCH_WARNING)
        self.assertNotIn("C301", ask("search the records for party wall", as_of=JUNE_1).model_dump_json())


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.records, self.cases = chat_tools.tools_for(SiteView(example_context()))

    def test_the_tools_return_ids_the_model_can_cite(self):
        view = SiteView(example_context())
        text = self.records.run({"text": "safeguard", "bbl": "", "dataset_key": "", "date_from": "", "date_to": ""})
        self.assertIn(f"[{SAFEGUARD}]", text)
        self.assertIn("NOT SEARCHED", text)  # the attached lot's violations query failed
        cases = self.cases.run({"text": "", "hazard": "structural", "severity_min": "2"})
        ids = [line[1:line.index("]")] for line in cases.splitlines() if line.startswith("[")]
        self.assertEqual(ids, [LATE_CASE, OLD_CASE])
        self.assertTrue(all(ref in view.items for ref in ids))

    def test_a_tool_says_not_loaded_or_not_run_and_never_raises_on_bad_input(self):
        _, cases = chat_tools.tools_for(SiteView(example_context(similar=Loaded.failed("timeout"))))
        self.assertTrue(cases.run({"text": "", "hazard": "", "severity_min": ""}).startswith("NOT LOADED"))
        self.assertTrue(self.cases.run({"hazard": "earthquake"}).startswith("The search was not run"))
        self.assertTrue(self.records.run({"text": None, "bbl": "nope"}).startswith("The search was not run"))

    def test_a_replay_tool_never_shows_later_material(self):
        records, cases = chat_tools.tools_for(SiteView(example_context(as_of=JUNE_1)))
        self.assertNotIn("C301", records.run({"text": "", "bbl": "", "dataset_key": "dob_complaints", "date_from": "", "date_to": ""}))
        self.assertNotIn("ex-wall-2026", cases.run({"text": "", "hazard": "", "severity_min": ""}))

    def test_the_model_call_runs_a_tool_returns_its_result_and_takes_the_answer_with_actions(self):
        view = SiteView(example_context())
        client = FakeAnthropicClient(
            response([tool_call("search_similar_cases", "c1", text="", hazard="structural", severity_min="")]),
            response([submit_block([says("A past case resembles this site.", OLD_CASE)], [action("fly_to", ref=OLD_CASE)])]))
        chat = AnthropicChatModel(client).open([], [{"role": "user", "content": "q"}], False, tuple(chat_tools.tools_for(view)))
        turn = chat.turn()
        self.assertEqual(turn.proposal["actions"][0]["ref"], OLD_CASE)
        first, second = client.requests
        self.assertEqual([t["name"] for t in first["tools"]], ["search_records", "search_similar_cases", "submit_answer"])
        self.assertTrue(all(t["strict"] for t in first["tools"]))
        [result] = second["messages"][-1]["content"]
        self.assertEqual((result["type"], result["tool_use_id"]), ("tool_result", "c1"))
        self.assertIn(f"[{OLD_CASE}]", result["content"])


class RouteTests(unittest.TestCase):
    """The route functions called directly: the app's own test client needs a package the app does not."""

    def setUp(self):
        from api.routers.chat.chat_router import chat_router_for

        def load(bbl, job_type, stage, as_of):
            if bbl != SITE_BBL:
                raise SiteContextUnavailable(bbl)
            return example_context(as_of=as_of)
        routes = {(route.path, next(iter(route.methods))): route.endpoint for route in chat_router_for(load).routes}
        self.setup, self.answer = routes[("/api/chat/setup", "GET")], routes[("/api/chat", "POST")]
        patcher = mock.patch.dict(os.environ, {"FORESITE_CHAT_LIVE": "0"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_question_is_answered_in_mock_mode_with_no_key(self):
        self.assertFalse(self.setup().live)
        answer = self.answer(ChatRequest(bbl=SITE_BBL, question="Search the records for fence", as_of=JUNE_1))
        self.assertEqual((answer.mode, answer.as_of), ("mock", JUNE_1))

    def test_an_unknown_site_or_saved_example_is_a_404(self):
        for request in (ChatRequest(bbl="3999999999", question="x"), ChatRequest(bbl=SITE_BBL, example_id="nope")):
            with self.assertRaises(HTTPException) as refused:
                self.answer(request)
            self.assertEqual(refused.exception.status_code, 404)

    def test_a_malformed_request_is_refused_not_cut(self):
        long_history = [{"question": "q", "answer": "a" * 4000}] * 4
        for bad in ({"bbl": "123", "question": "x"}, {"bbl": SITE_BBL}, {"bbl": SITE_BBL, "question": "x" * 1001},
                    {"bbl": SITE_BBL, "question": "x", "surprise": 1}, {"bbl": SITE_BBL, "question": "x", "history": long_history},
                    {"bbl": SITE_BBL, "question": "x", "history": [{"question": "q", "answer": "a"}] * 9}):
            with self.assertRaises(ValidationError, msg=bad):
                ChatRequest(**bad)


if __name__ == "__main__":
    unittest.main()
