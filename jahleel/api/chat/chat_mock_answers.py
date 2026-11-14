"""A stand-in for the model while the server has no key: a typed question gets a prepared answer.

No model runs. The question is matched by keyword to dataset counts, checklist rows or a saved
example, and the result is a proposed answer in the same shape a model submits, so it goes through
the same checks and every part still rests on the brief on screen. A question nothing matches gets
None: the mock never makes an answer up, and it never stands in for a web search.
"""

import re
from typing import Optional

from jahleel.api.chat.chat_answer_build import MAX_ITEMS
from jahleel.api.chat.chat_brief_view import BriefView
from jahleel.api.chat.chat_saved_examples import SAVED

_STOP = set("a about an and any are at by can could do dob does for has have here how i in is it its lot me of on or public "
            "record records say says show shows site tell that the there this to under was we what which with you".split())
_COUNT_CUE = re.compile(r"\bhow many\b|\bcount\b|\bnumber of\b|\bhow much\b", re.I)
_NEIGHBOR_CUE = re.compile(r"\bneighbou?r\w*|\badjacent\b|\badjoining\b|\bnext door\b|\btouching\b", re.I)
_CHECKLIST_CUE = re.compile(r"\bdut(?:y|ies)\b|\bchecklist\b|\brequire\w*|\bobligation\w*|\bappl(?:y|ies)\b|\bgaps?\b|"
                            r"\bproof\b|\bmissing\b", re.I)
_GAP_CUE = re.compile(r"\bgaps?\b|\bproof\b|\bmissing\b|\boutstanding\b", re.I)
# Words in a question -> the datasets they mean, most specific first.
_DATASET_WORDS = [
    (r"\becb\b|\boath\b", ["ecb_violations"]),
    (r"\bhpd\b|\bhousing\b", ["hpd_violations"]),
    (r"\b311\b", ["dob_311_requests"]),
    (r"\bsafety violations?\b|\bcivil penalt\w*", ["dob_safety_violations"]),
    (r"\bcomplaints?\b", ["dob_complaints", "dob_311_requests"]),
    (r"\bfilings?\b|\bjobs?\b|\bpermits?\b|\bapplications?\b", ["dob_now_filings"]),
    (r"\bviolations?\b", ["dob_violations", "ecb_violations", "dob_safety_violations", "hpd_violations"]),
]
# Extra words that point to a saved example, by its id.
_EXAMPLE_WORDS = {
    "excavation": "excavate dig digging earth foundation filing work",
    "stop_work": "stop work order swo halted stopped",
    "neighbors": "neighbor neighbors adjacent adjoining next door touching buildings lots",
    "safe": "safe safety unsafe risk danger compliant compliance legal dig excavate proceed",
    "record": "history building violations",
    "next_door": "neighbor adjacent adjoining bedford",
}
_APPLIES = {
    "applies": "applies from the public record",
    "needs_input": "waits on a project input before it can be decided",
    "set_by_dob": "is set by DOB, not by the project",
    "unknown": "cannot be decided from what was queried",
    "does_not_apply": "does not apply on the public record",
}
_PROOF = {
    "not_provided": "proof has not been provided to PreFlight",
    "provided_unverified": "proof was provided and is not verified",
    "reported_not_read": "a public source reports a document, which nobody here has read",
}


def _tokens(text: str) -> set[str]:
    """Lower-case words, short forms: 'excavation' and 'excavate' meet, as do a word and its plural."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:5] if len(w) > 5 else w.rstrip("s") or w for w in words if w not in _STOP}


def _says(text: str, *refs: str) -> dict:
    return {"kind": "statement", "text": text, "refs": list(refs), "bbl": "", "dataset_key": "", "notice": ""}


def _check(bbl: str, dataset_key: str) -> dict:
    return {"kind": "dataset_check", "text": "", "refs": [], "bbl": bbl, "dataset_key": dataset_key, "notice": ""}


def _lots_asked_about(view: BriefView, question: str) -> list[str]:
    """A lot named by its house number and street, else every touching lot, else the site."""
    asked = set(re.findall(r"[a-z0-9]+", question.lower()))
    named = []
    for lot in view.lots:
        address = (lot.facts.address if lot.facts and lot.facts.address else "").lower().split()
        if len(address) >= 2 and address[0] in asked and address[1] in asked:
            named.append(lot.bbl)
    if named:
        return named
    if _NEIGHBOR_CUE.search(question):
        return [lot.bbl for lot in view.lots if lot.role == "touching"]
    return [view.brief.site.bbl]


def _datasets_asked_about(question: str) -> list[str]:
    for pattern, keys in _DATASET_WORDS:
        if re.search(pattern, question, re.I):
            return keys
    return []


def _counts(view: BriefView, question: str, keys: list[str]) -> list[dict]:
    lots = _lots_asked_about(view, question)
    keys = keys or [key for (bbl, key) in view.datasets if bbl == lots[0] and key != "pluto"]
    keys = keys[:max(1, MAX_ITEMS // len(lots))]
    return [_check(bbl, key) for bbl in lots for key in keys if (bbl, key) in view.datasets][:MAX_ITEMS]


def _rows(view: BriefView, question: str) -> list[dict]:
    asked = _tokens(question)
    overlap = {row.id: len(asked & _tokens(row.title)) for row in view.brief.checklist}
    best = max(overlap.values(), default=0)
    rows = [row for row in view.brief.checklist if best and overlap[row.id] == best]  # the closest titles only
    if not rows and _GAP_CUE.search(question):
        rows = [row for row in view.brief.checklist if row.open_gap]
    if not rows and _CHECKLIST_CUE.search(question):
        rows = [row for row in view.brief.checklist if row.applies.status == "applies"]
    items = []
    for row in rows[:5]:
        applies = _APPLIES.get(row.applies.status, "has a status this mock does not word")
        items.append(_says(f'Checklist row "{row.title}" (BC {row.section}): it {applies}; '
                           f"{_PROOF.get(row.proof.status, 'its proof has a status this mock does not word')}.", f"row:{row.id}"))
        if f"lead:{row.id}:1" in view.items:
            items.append(_says("A public source reports a document for that row. Nobody here has read it, so it is "
                               "a lead and not proof.", f"lead:{row.id}:1"))
    return items


def _saved(slug: str, question: str, at_least: int) -> Optional[list[dict]]:
    asked, best, best_score = _tokens(question), None, 0
    for example in SAVED.get(slug, []):
        score = len(asked & _tokens(example["question"] + " " + _EXAMPLE_WORDS.get(example["id"], "")))
        if score > best_score:
            best, best_score = example, score
    return list(best["items"]) if best is not None and best_score >= at_least else None


def propose(view: BriefView, slug: str, question: str) -> Optional[list[dict]]:
    """Proposed items for the question, or None when nothing prepared matches it."""
    keys = _datasets_asked_about(question)
    if _COUNT_CUE.search(question):
        return _counts(view, question, keys) or None
    asks_checklist = bool(_CHECKLIST_CUE.search(question))
    return (_saved(slug, question, at_least=2)
            or (_rows(view, question) if asks_checklist else None)
            or (_counts(view, question, keys) if keys else None)
            or _rows(view, question)
            or _saved(slug, question, at_least=1)
            or None)
