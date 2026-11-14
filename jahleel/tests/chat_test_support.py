"""Shared pieces for the chat tests: a scripted stand-in for the model, and for the Anthropic SDK client.

Nothing here reaches the network. A test that wants the live path passes one of these in; none builds
a real client.
"""

from types import SimpleNamespace

from jahleel.api.chat.chat_answer_build import WebResult
from jahleel.api.chat.chat_model_call import ModelTurn
from jahleel.api.chat.chat_models import ChatUsage

SITE = "2625-bedford-ave-brooklyn"
SITE_BBL = "3052110074"
NEXT_DOOR_BBL = "3052110073"
S3 = "dob_now_filings:B01330433-S3"
STOP_WORK_ECB = "ecb_violations:39553409Z"  # dated 2026-04-23
COLLAPSE_DAY_VIOLATION = "dob_violations:2824347"  # dated 2026-11-11
WEB = WebResult(url="https://www.nyc.gov/site/buildings/codes/2022-construction-codes.page", title="2022 Construction Codes")


def says(text, *refs):
    return {"kind": "statement", "text": text, "refs": list(refs), "bbl": "", "dataset_key": "", "notice": ""}


def check(bbl, dataset_key):
    return {"kind": "dataset_check", "text": "", "refs": [], "bbl": bbl, "dataset_key": dataset_key, "notice": ""}


def gap(topic):
    return {"kind": "gap", "text": topic, "refs": [], "bbl": "", "dataset_key": "", "notice": ""}


def notice_item(code):
    return {"kind": "notice", "text": "", "refs": [], "bbl": "", "dataset_key": "", "notice": code}


class ScriptedModel:
    """Stands in for AnthropicChatModel: returns the given proposals in order and records what it was asked."""

    def __init__(self, *proposals, web_results=(), searched=False, fails=None):
        self.proposals, self.web_results, self.searched, self.fails = list(proposals), list(web_results), searched, fails
        self.opened_with = None
        self.problems_seen = []
        self.usage = ChatUsage(model="scripted")

    def open(self, system, messages, allow_web):
        self.opened_with = {"system": system, "messages": messages, "allow_web": allow_web}
        return self

    def turn(self, problems=None):
        if self.fails:
            raise self.fails
        self.problems_seen.append(problems)
        return ModelTurn(proposal={"items": self.proposals.pop(0)}, web_results=self.web_results, searched=self.searched)


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def search_blocks(*results, error=None):
    """A web search call and its result block, shaped as the SDK returns them."""
    content = SimpleNamespace(type="web_search_tool_result_error", error_code=error) if error else [
        SimpleNamespace(type="web_search_result", url=url, title=title, page_age=None, encrypted_content="x")
        for url, title in results]
    return [SimpleNamespace(type="server_tool_use", id="srv_1", name="web_search", input={"query": "q"}),
            SimpleNamespace(type="web_search_tool_result", tool_use_id="srv_1", content=content)]


def submit_block(items, call_id="call_1"):
    return SimpleNamespace(type="tool_use", id=call_id, name="submit_answer", input={"items": items})


def response(blocks, stop_reason="tool_use", searches=0):
    usage = SimpleNamespace(input_tokens=100, output_tokens=20, cache_read_input_tokens=0, cache_creation_input_tokens=0,
                            server_tool_use=SimpleNamespace(web_search_requests=searches))
    return SimpleNamespace(content=blocks, stop_reason=stop_reason, usage=usage, model="claude-test")


class FakeAnthropicClient:
    """`client.beta.messages.create(**kwargs)` returning scripted responses; keeps every request it was sent."""

    def __init__(self, *responses):
        self.responses, self.requests = list(responses), []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        reply = self.responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply
