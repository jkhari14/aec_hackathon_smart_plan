"""Offline tests for how a proposed answer becomes typed parts, and what is held back."""

import unittest

from pydantic import ValidationError

from jahleel.api.brief.brief_build import build_brief
from jahleel.api.chat.chat_answer_build import MODEL_NOTICES, NOTICES, build_parts
from jahleel.api.chat.chat_brief_view import BriefView
from jahleel.api.chat.chat_models import BriefSource, LeadPart, RecordPart, WebSource
from jahleel.tests.chat_test_support import (
    NEXT_DOOR_BBL, S3, SITE, SITE_BBL, STOP_WORK_ECB, WEB, check, gap, notice_item, says,
)


def setUpModule():
    global VIEW
    VIEW = BriefView(build_brief(SITE))


def build(*items, web=(), view=None):
    return build_parts(view or VIEW, {"items": list(items)}, list(web), searched=bool(web))


class SourcesTests(unittest.TestCase):
    def test_a_statement_with_no_source_is_held_back(self):
        built = build(says("The site has an approved foundation filing."))
        self.assertEqual(built.parts, [])
        self.assertIn("no source", built.problems[0])

    def test_a_statement_citing_something_outside_the_brief_is_held_back(self):
        built = build(says("A permit was issued.", "dob_now_filings:MADE-UP"))
        self.assertEqual(built.parts, [])
        self.assertIn("not an item of this brief view", built.problems[0])

    def test_a_record_statement_carries_the_briefs_own_source(self):
        [part] = build(says("Filing B01330433-S3 was filed 2026-02-24.", f"[{S3}]")).parts
        self.assertEqual(part.kind, "record")
        self.assertEqual([(s.type, s.ref, s.date) for s in part.sources], [("public_record", S3, "2026-02-24")])
        self.assertTrue(part.sources[0].url.startswith("https://data.cityofnewyork.us/"))

    def test_a_checklist_row_and_lot_facts_are_typed_as_what_they_are(self):
        built = build(says("BC 3309.4 applies on the record.", "row:foundation_protection"),
                      says("PLUTO lists the building as built in 1930.", f"lot:{NEXT_DOOR_BBL}"))
        self.assertEqual([p.sources[0].type for p in built.parts], ["requirement", "lot_facts"])
        self.assertEqual(built.problems, [])


class WebIsNeverARecordTests(unittest.TestCase):
    def test_a_web_statement_is_a_lead(self):
        [part] = build(says("The city publishes the 2022 construction codes online.", WEB.url), web=[WEB]).parts
        self.assertEqual(part.kind, "lead")
        self.assertEqual((part.sources[0].type, part.sources[0].url, part.sources[0].official), ("web_result", WEB.url, True))

    def test_a_statement_mixing_a_web_result_and_a_record_is_held_back(self):
        built = build(says("Filing B01330433-S3 follows the 2022 codes.", S3, WEB.url), web=[WEB])
        self.assertEqual(built.parts, [])
        self.assertIn("Split it", built.problems[0])

    def test_a_url_the_search_did_not_return_is_held_back(self):
        built = build(says("A news site reports on the block.", "https://example.com/story"), web=[WEB])
        self.assertEqual(built.parts, [])
        self.assertIn("not a URL the web search returned", built.problems[0])

    def test_a_record_part_cannot_be_built_from_a_web_source(self):
        web = WebSource(url=WEB.url, title=WEB.title, official=True)
        with self.assertRaises(ValidationError):
            RecordPart(text="x", sources=[web])
        with self.assertRaises(ValidationError):
            RecordPart(text="x", sources=[web.model_dump()])
        with self.assertRaises(ValidationError):
            RecordPart(text="x", sources=[])

    def test_a_lead_part_cannot_be_built_from_a_brief_record(self):
        record = BriefSource(type="public_record", ref=S3, label="DOB NOW filing")
        with self.assertRaises(ValidationError):
            LeadPart(text="x", sources=[record.model_dump()])

    def test_a_web_source_must_be_a_web_address(self):
        for bad in ("javascript:alert(1)", "data:text/html,x", "/api/briefs", ""):
            with self.assertRaises(ValidationError):
                WebSource(url=bad, title="x", official=False)

    def test_a_reported_document_in_the_brief_is_a_lead_and_cannot_mix_with_a_record(self):
        [part] = build(says("A news article reports an adjoining owners notification, dated 2026-06-10.", "lead:notice:1")).parts
        self.assertEqual((part.kind, part.sources[0].type), ("lead", "reported_document"))
        mixed = build(says("The notice row has a reported letter.", "row:notice", "lead:notice:1"))
        self.assertEqual(mixed.parts, [])


class NumbersTests(unittest.TestCase):
    def test_a_number_not_in_the_cited_items_is_held_back(self):
        built = build(says("Filing B01330433-S3 covers a 12 foot excavation.", S3))
        self.assertEqual(built.parts, [])
        self.assertIn("12", built.problems[0])

    def test_a_typed_count_is_held_back_even_in_words(self):
        for text in ("The site has 4 ECB violations.", "The site has three open violations."):
            built = build(says(text, STOP_WORK_ECB))
            self.assertEqual(built.parts, [], text)

    def test_numbers_from_the_cited_record_pass(self):
        built = build(says("An ECB violation dated April 23, 2026 cites section 28-207.2.2.", STOP_WORK_ECB))
        self.assertEqual(built.problems, [])


class WordingTests(unittest.TestCase):
    def held_back(self, text, *refs, web=()):
        built = build(says(text, *refs), web=web)
        self.assertEqual(built.parts, [], text)
        return built.problems[0]

    def test_an_absence_claim_is_held_back(self):
        self.held_back("There are no violations on the site.", f"lot:{SITE_BBL}")
        self.held_back("None were found for this lot.", f"lot:{SITE_BBL}")

    def test_a_verdict_is_held_back(self):
        for text in ("The excavation is not safe.", "The filing complies with the code.", "The site is in compliance."):
            self.assertIn("verdict", self.held_back(text, S3))

    def test_blame_and_prevention_are_held_back(self):
        self.held_back("A survey would have prevented the damage.", "row:survey")
        self.held_back("The builder is at fault here.", S3)

    def test_a_cause_is_held_back_from_the_record_and_allowed_only_as_reported_from_the_web(self):
        self.held_back("The stop-work order was caused by the excavation.", STOP_WORK_ECB)
        self.held_back("The excavation caused the collapse.", WEB.url, web=[WEB])
        reported = build(says("Officials said the cause is under investigation.", WEB.url), web=[WEB])
        self.assertEqual([p.kind for p in reported.parts], ["lead"])

    def test_a_company_name_is_held_back(self):
        self.assertIn("company", self.held_back("The filing was made by Acme Builders LLC.", S3))

    def test_exact_words_quoted_from_the_cited_record_are_the_records(self):
        built = build(says('The violation reads "FULL STOP WORK ORDER DUE TO COLLAPSE".', "dob_violations:2824347"))
        self.assertEqual(built.problems, [])
        invented = build(says('The violation reads "WORK WAS UNSAFE DUE TO NEGLIGENCE".', "dob_violations:2824347"))
        self.assertEqual(invented.parts, [])


class DatasetCheckTests(unittest.TestCase):
    def test_a_count_is_written_by_the_server_with_the_dataset_as_its_source(self):
        [part] = build(check(SITE_BBL, "ecb_violations")).parts
        self.assertEqual(part.kind, "record")
        self.assertTrue(part.text.startswith("4 records in "))
        self.assertEqual(part.sources[0].type, "dataset_count")

    def test_zero_from_an_ok_dataset_is_not_found_with_the_dataset_named(self):
        [part] = build(check(SITE_BBL, "hpd_violations")).parts
        self.assertEqual(part.kind, "not_found")
        self.assertIn("HPD violations", part.text)
        self.assertEqual((part.queried[0].key, part.queried[0].bbl), ("hpd_violations", SITE_BBL))

    def test_a_failed_or_skipped_dataset_is_unknown_never_zero(self):
        for status in ("error", "skipped"):
            brief = build_brief(SITE)
            dataset = next(d for d in brief.site.datasets if d.key == "hpd_violations")
            dataset.status, dataset.count, dataset.reason = status, (0 if status == "error" else None), "no BIN"
            view = BriefView(brief)
            [part] = build(check(SITE_BBL, "hpd_violations"), view=view).parts
            self.assertEqual(part.kind, "unknown", status)
            self.assertIn("This is not zero", part.text)
            self.assertNotIn("None found", part.text)
            self.assertIn(f"hpd_violations: {status} (nothing is known; not zero)", view.digest())

    def test_an_unknown_lot_or_dataset_is_held_back(self):
        self.assertEqual(build(check("9999999999", "ecb_violations")).parts, [])
        self.assertEqual(build(check(SITE_BBL, "stop_work_orders")).parts, [])

    def test_complaints_and_311_requests_together_get_the_overlap_notice(self):
        built = build(check(SITE_BBL, "dob_complaints"), check(SITE_BBL, "dob_311_requests"))
        self.assertEqual(built.parts[-1].code, "complaints_overlap")
        alone = build(check(SITE_BBL, "dob_complaints"))
        self.assertNotIn("notice", [p.kind for p in alone.parts])


class GapAndNoticeTests(unittest.TestCase):
    def test_a_gap_is_worded_by_the_server_and_names_what_was_queried(self):
        [part] = build(gap("the flood zone for this lot")).parts
        self.assertEqual(part.kind, "not_found")
        self.assertEqual(part.text, "Not found in what we queried: the flood zone for this lot.")
        self.assertIn("pluto", [q.key for q in part.queried])

    def test_a_gap_cannot_carry_a_figure_or_a_verdict(self):
        self.assertEqual(build(gap("the 12 foot excavation depth")).parts, [])
        self.assertEqual(build(gap("whether the site is safe")).parts, [])

    def test_the_model_can_ask_only_for_its_own_notices(self):
        [part] = build(notice_item("not_a_determination")).parts
        self.assertEqual((part.kind, part.text), ("notice", NOTICES["not_a_determination"]))
        for code in set(NOTICES) - set(MODEL_NOTICES):
            self.assertEqual(build(notice_item(code)).parts, [], code)

    def test_a_malformed_proposal_is_a_problem_not_a_crash(self):
        for bad in (None, {}, {"items": []}, {"items": [{"kind": "statement"}] * 13}, {"items": [{"kind": "essay"}]}, "text"):
            built = build_parts(VIEW, bad, [])
            self.assertEqual(built.parts, [])
            self.assertTrue(built.problems)


if __name__ == "__main__":
    unittest.main()
