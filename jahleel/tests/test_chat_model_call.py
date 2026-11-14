"""Offline tests for the live model call, against a stand-in for the Anthropic SDK client, and for the routes."""

import os
import unittest
from unittest import mock

from fastapi import HTTPException

from jahleel.api.chat import chat_model_call, chat_router
from jahleel.api.chat.chat_model_call import AnthropicChatModel, ChatModelError, default_model
from jahleel.api.chat.chat_models import ChatRequest
from jahleel.tests.chat_test_support import (
    S3, SITE, FakeAnthropicClient, ScriptedModel, response, says, search_blocks, submit_block, text_block,
)

ITEMS = [says("Filing B01330433-S3 was filed 2026-02-24.", S3)]
NYC = ("https://www.nyc.gov/site/buildings/index.page", "Buildings")


def session(*responses, allow_web=True):
    client = FakeAnthropicClient(*responses)
    return client, AnthropicChatModel(client).open([{"type": "text", "text": "sys"}], [{"role": "user", "content": "q"}], allow_web)


class ModelCallTests(unittest.TestCase):
    def test_the_submitted_answer_and_the_search_results_come_back(self):
        client, chat = session(response(search_blocks(NYC) + [submit_block(ITEMS)], searches=1))
        turn = chat.turn()
        self.assertEqual(turn.proposal, {"items": ITEMS})
        self.assertEqual([(r.url, r.title) for r in turn.web_results], [NYC])
        self.assertTrue(turn.searched)
        self.assertEqual((chat.usage.web_searches, chat.usage.input_tokens, chat.usage.model), (1, 100, "claude-test"))

    def test_the_request_carries_the_model_the_tools_and_no_forced_tool_choice(self):
        client, chat = session(response([submit_block(ITEMS)]))
        chat.turn()
        [sent] = client.requests
        self.assertEqual(sent["model"], "claude-opus-5-5")
        self.assertEqual([t["name"] for t in sent["tools"]], ["web_search", "submit_answer"])
        self.assertTrue(sent["tools"][1]["strict"])
        self.assertNotIn("tool_choice", sent)
        self.assertNotIn("thinking", sent)
        self.assertNotIn("temperature", sent)
        self.assertNotIn("api_key", str(sent))

    def test_no_web_tool_is_sent_when_web_is_not_allowed(self):
        client, chat = session(response([submit_block(ITEMS)]), allow_web=False)
        chat.turn()
        self.assertEqual([t["name"] for t in client.requests[0]["tools"]], ["submit_answer"])

    def test_a_paused_search_turn_is_sent_back_unchanged_and_resumed(self):
        paused = response(search_blocks(NYC), stop_reason="pause_turn")
        client, chat = session(paused, response([submit_block(ITEMS)]))
        turn = chat.turn()
        self.assertEqual(len(client.requests), 2)
        self.assertEqual(client.requests[1]["messages"][-1], {"role": "assistant", "content": paused.content})
        self.assertEqual(len(turn.web_results), 1)

    def test_a_failed_search_yields_no_results_and_no_crash(self):
        client, chat = session(response(search_blocks(error="too_many_requests") + [submit_block(ITEMS)]))
        turn = chat.turn()
        self.assertEqual(turn.web_results, [])
        self.assertTrue(turn.searched)

    def test_problems_go_back_as_an_error_result_for_the_pending_call(self):
        client, chat = session(response([submit_block(ITEMS, "call_1")]), response([submit_block(ITEMS, "call_2")]))
        chat.turn()
        chat.turn(["item 1: no source."])
        [result] = client.requests[1]["messages"][-1]["content"]
        self.assertEqual((result["type"], result["tool_use_id"], result["is_error"]), ("tool_result", "call_1", True))
        self.assertIn("item 1: no source.", result["content"])

    def test_text_without_the_tool_is_nudged_then_given_up_on(self):
        client, chat = session(response([text_block("Here is my answer.")], stop_reason="end_turn"),
                               response([submit_block(ITEMS)]))
        self.assertEqual(chat.turn().proposal, {"items": ITEMS})
        self.assertIn("submit_answer", client.requests[1]["messages"][-1]["content"])
        never = [response([text_block("...")], stop_reason="end_turn") for _ in range(chat_model_call.MAX_REQUESTS)]
        _, stuck = session(*never)
        with self.assertRaises(ChatModelError):
            stuck.turn()

    def test_a_refusal_or_a_cut_off_answer_is_an_error(self):
        for stop in ("refusal", "max_tokens"):
            _, chat = session(response([text_block("")], stop_reason=stop))
            with self.assertRaises(ChatModelError):
                chat.turn()

    def test_an_sdk_error_becomes_a_short_reason(self):
        class Boom(Exception):
            pass

        client = FakeAnthropicClient()
        client.beta.messages.create = mock.Mock(side_effect=Boom("request body with secrets"))
        chat = AnthropicChatModel(client, errors=(Boom,)).open([], [{"role": "user", "content": "q"}], True)
        with self.assertRaises(ChatModelError) as caught:
            chat.turn()
        self.assertEqual(str(caught.exception), "Boom")

    def test_a_rejected_fallback_option_is_dropped_and_the_question_asked_once_more(self):
        class Rejected(Exception):
            status_code = 400

        client = FakeAnthropicClient(Rejected("unknown beta"), response([submit_block([says("x", S3)])]),
                                     response([submit_block([says("y", S3)])]))
        chat = AnthropicChatModel(client, errors=(Rejected,)).open([], [{"role": "user", "content": "q"}], True)
        chat.turn()
        chat.turn(problems=["item 1: no source"])
        first, second, third = client.requests
        self.assertEqual((first["betas"], first["fallbacks"]), (["server-side-fallback-2026-07-01"], "default"))
        for later in (second, third):  # the same request without the option, and it stays off
            self.assertNotIn("betas", later)
            self.assertNotIn("fallbacks", later)
        self.assertEqual(second["tools"], first["tools"])

    def test_any_other_api_error_is_not_retried(self):
        class Overloaded(Exception):
            status_code = 529

        client = FakeAnthropicClient(Overloaded("busy"))
        chat = AnthropicChatModel(client, errors=(Overloaded,)).open([], [{"role": "user", "content": "q"}], True)
        with self.assertRaises(ChatModelError):
            chat.turn()
        self.assertEqual(len(client.requests), 1)


class DefaultModelTests(unittest.TestCase):
    def test_no_key_means_no_live_model(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(default_model())

    def test_the_off_switch_wins_over_a_key(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-not-real", "PREFLIGHT_CHAT_LIVE": "0"}, clear=True):
            self.assertIsNone(default_model())


class RouteTests(unittest.TestCase):
    """The handlers, called directly. `default_model` is always replaced, so no test can reach the API."""

    def setUp(self):
        chat_router._recent_live.clear()

    def post(self, model=None, **fields):
        with mock.patch.object(chat_model_call, "default_model", return_value=model):
            return chat_router.chat_answer(ChatRequest(slug=fields.pop("slug", SITE), **fields))

    def test_with_no_key_the_route_serves_a_mock_answer(self):
        answer = self.post(question="How many ECB violations?")
        self.assertEqual((answer.mode, answer.parts[0].code, answer.usage), ("mock", "mock_answer", None))

    def test_a_saved_example_never_touches_the_model(self):
        with mock.patch.object(chat_model_call, "default_model", side_effect=AssertionError("not for a saved example")):
            answer = chat_router.chat_answer(ChatRequest(slug=SITE, example_id="safe"))
        self.assertEqual(answer.mode, "saved")

    def test_an_unknown_site_or_example_is_a_404(self):
        for fields in ({"slug": "no-such-site", "question": "x"}, {"slug": "../etc", "question": "x"}, {"example_id": "nope"}):
            with self.assertRaises(HTTPException) as caught:
                self.post(**fields)
            self.assertEqual(caught.exception.status_code, 404)

    def test_live_questions_are_capped_per_minute(self):
        for _ in range(chat_router.LIVE_QUESTIONS_PER_MINUTE):
            self.post(model=ScriptedModel(ITEMS), question="x")
        with self.assertRaises(HTTPException) as caught:
            self.post(model=ScriptedModel(ITEMS), question="x")
        self.assertEqual(caught.exception.status_code, 429)
        self.assertEqual(self.post(question="x").mode, "mock")  # a mock answer is never capped

    def test_setup_says_whether_live_answers_are_on_and_lists_the_examples(self):
        with mock.patch.object(chat_model_call, "default_model", return_value=None):
            setup = chat_router.chat_setup(SITE)
        self.assertFalse(setup.live)
        self.assertEqual([e.id for e in setup.examples], ["excavation", "stop_work", "neighbors", "safe"])
        with mock.patch.object(chat_model_call, "default_model", return_value=None):
            self.assertEqual(chat_router.chat_setup("no-such-site").examples, [])


if __name__ == "__main__":
    unittest.main()
