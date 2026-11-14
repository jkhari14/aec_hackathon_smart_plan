"""Saved example exchanges for the demo sites, so the demo does not depend on a live model call.

Each example is a proposed answer in the same shape the model submits. It is never served as stored
text: every request runs it through the same checks against the brief on screen, so its sources are
always the brief's own, and in an as-of view anything resting on a later record drops out.
They rest on the brief only: a saved web result would be a stale one.
"""

from jahleel.api.chat.chat_models import ExampleQuestion


def _says(text: str, *refs: str) -> dict:
    return {"kind": "statement", "text": text, "refs": list(refs), "bbl": "", "dataset_key": "", "notice": ""}


def _count(bbl: str, dataset_key: str) -> dict:
    return {"kind": "dataset_check", "text": "", "refs": [], "bbl": bbl, "dataset_key": dataset_key, "notice": ""}


def _gap(topic: str) -> dict:
    return {"kind": "gap", "text": topic, "refs": [], "bbl": "", "dataset_key": "", "notice": ""}


def _notice(code: str) -> dict:
    return {"kind": "notice", "text": "", "refs": [], "bbl": "", "dataset_key": "", "notice": code}


_SITE, _NEXT_DOOR = "3052110074", "3052110073"  # 2625 Bedford Ave and 1321 Flatbush Ave
_S3 = "dob_now_filings:B01330433-S3"
_GAP_ROWS = ("row:foundation_protection", "row:support_drawings", "row:support_basis")

SAVED = {
    "2625-bedford-ave-brooklyn": [
        {"id": "excavation", "question": "What does the public record say about excavation on this site?", "items": [
            _says('A DOB NOW New Building filing, B01330433-S3, filed 2026-02-24, lists earth work as "YES" and '
                  "describes foundation plans.", _S3),
            _says('The checklist notes that the same filing answers "No" for support of excavation. PreFlight quotes '
                  "that as recorded and draws nothing further from it.", "row:foundation_protection"),
            _says("From that filing, the checklist treats three duties as applying: protecting adjoining footings and "
                  "foundations (BC 3309.4), excavation-support drawings (BC 3304.4.1) and the geotechnical basis for "
                  "the support design (BC 3304.4.1.2). Proof of each has not been provided to PreFlight.", *_GAP_ROWS),
            _notice("not_a_determination"),
        ]},
        {"id": "stop_work", "question": "Does the record mention a stop-work order on this site?", "items": [
            _says('An ECB violation dated 2026-04-23 reads "UNLAWFULLY CONTINUED WORK WHILE NOTICE OF A STOP WORK ORDER".',
                  "ecb_violations:39553409Z"),
            _says("A 311 request dated 2026-03-18 is about work contrary to or beyond approved plans. DOB's resolution, "
                  "recorded 2026-05-08, says it removed the stop work order.", "dob_311_requests:68381531"),
            _says('A DOB violation dated 2026-11-11 reads "FULL STOP WORK ORDER DUE TO COLLAPSE".', "dob_violations:2824347"),
            _gap("a complete list of stop-work orders (we have not found them published as their own dataset)"),
            _notice("cause_not_established"),
        ]},
        {"id": "neighbors", "question": "What do we know about the buildings touching the site?", "items": [
            _says("PLUTO lists 1321 Flatbush Avenue as built in 1930, with 3 floors and 4 residential units, on a lot "
                  "20.5 feet wide.", f"lot:{_NEXT_DOOR}"),
            _count(_NEXT_DOOR, "hpd_violations"),
            _count(_NEXT_DOOR, "dob_violations"),
            _count(_NEXT_DOOR, "dob_safety_violations"),
            _count("3052110054", "pluto"),
            _says("The checklist judges the examination (BC 3309.3), preconstruction survey (BC 3309.4.3) and monitoring "
                  "(BC 3309.4.4) duties building by building. Each waits on a project input before it can be decided.",
                  "row:examination", "row:survey", "row:monitoring"),
            _notice("status_is_todays"),
        ]},
        {"id": "safe", "question": "Is it safe to excavate here?", "items": [
            _notice("not_a_determination"),
            _says("What the checklist can say: the duties under BC 3309.4, BC 3304.4.1 and BC 3304.4.1.2 apply from the "
                  "public record, and proof of each has not been provided to PreFlight.", *_GAP_ROWS),
            _says("Other rows, such as the preconstruction survey (BC 3309.4.3) and monitoring (BC 3309.4.4), wait on "
                  "project inputs the public record does not hold, such as the excavation depth.",
                  "row:survey", "row:monitoring"),
        ]},
    ],
    "1321-flatbush-ave-brooklyn": [
        {"id": "record", "question": "What does the public record show for this building?", "items": [
            _says("PLUTO lists the building as built in 1930, with 3 floors and 4 residential units.", f"lot:{_NEXT_DOOR}"),
            _count(_NEXT_DOOR, "hpd_violations"),
            _count(_NEXT_DOOR, "dob_violations"),
            _count(_NEXT_DOOR, "ecb_violations"),
            _count(_NEXT_DOOR, "dob_safety_violations"),
            _count(_NEXT_DOOR, "dob_now_filings"),
            _notice("status_is_todays"),
        ]},
        {"id": "next_door", "question": "What is on record for the lot next door at 2625 Bedford Avenue?", "items": [
            _says('A DOB NOW New Building filing on that lot, B01330433-S3, filed 2026-02-24, lists earth work as "YES" '
                  "and describes foundation plans.", _S3),
            _says('An ECB violation on that lot dated 2026-04-23 reads "UNLAWFULLY CONTINUED WORK WHILE NOTICE OF A STOP '
                  'WORK ORDER".', "ecb_violations:39553409Z"),
            _count(_SITE, "dob_now_filings"),
            _count(_SITE, "ecb_violations"),
            _notice("cause_not_established"),
        ]},
    ],
}


def examples_for(slug: str) -> list[ExampleQuestion]:
    return [ExampleQuestion(id=example["id"], question=example["question"]) for example in SAVED.get(slug, [])]


def saved_example(slug: str, example_id: str):
    """The saved example, or None."""
    return next((example for example in SAVED.get(slug, []) if example["id"] == example_id), None)
