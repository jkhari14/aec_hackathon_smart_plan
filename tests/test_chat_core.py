"""Offline tests for the chat's core: what a view may see, what a proposed answer becomes, the two searches, page actions."""

import unittest

from api.routers.chat import chat_case_search, chat_record_search
from api.routers.chat.chat_answer_build import build_parts
from api.routers.chat.chat_case_search import CaseQuery
from api.routers.chat.chat_record_search import RecordQuery
from api.routers.chat.chat_site_context import Loaded
from api.routers.chat.chat_site_view import SiteView
from tests.chat_test_support import (
    ATTACHED_BBL, FACADE_CASE, FILING, JULY_COMPLAINT, JULY_WARNING, JUNE_1, LATE_CASE, MARCH_WARNING, OLD_CASE, OTHER_BBL,
    SAFEGUARD, SITE_BBL, STOP_WORK, SURVEY_ACTION, WEB, action, check, example_context, item, says,
)


def setUpModule():
    global FULL, JUNE
    FULL, JUNE = SiteView(example_context()), SiteView(example_context(as_of=JUNE_1))


def build(view, *items, actions=(), **more):
    return build_parts(view, {"items": list(items), "actions": list(actions)}, more.pop("web", []), **more)


def one(view, proposed, **more):
    built = build(view, proposed, **more)
    assert not built.problems, built.problems
    return built.parts[0]


class AsOfViewTests(unittest.TestCase):
    def test_nothing_dated_on_or_after_the_day_is_in_the_view(self):
        for ref in (JULY_COMPLAINT, LATE_CASE, JULY_WARNING):
            self.assertIn(ref, FULL.items)
            self.assertNotIn(ref, JUNE.items)
        digest = JUNE.digest()
        for later in ("C301", "2026-07-02", "ex-wall-2026", "w2", "Party wall failure"):
            self.assertNotIn(later, digest)

    def test_a_record_dated_on_the_day_itself_is_left_out(self):
        self.assertNotIn(STOP_WORK, SiteView(example_context(as_of="2026-04-20")).items)  # dated 2026-04-20
        self.assertIn(STOP_WORK, SiteView(example_context(as_of="2026-04-21")).items)

    def test_a_case_dated_only_by_year_is_before_the_day_only_if_the_whole_year_is(self):
        def cases(year):
            entry = {"similar": {"case_id": "c", "score": 0.5}, "case": {"id": "c", "title": "t", "date": year}}
            return SiteView(example_context(as_of=JUNE_1, similar=Loaded.ok([entry]))).cases
        self.assertEqual(len(cases("2025")), 1)
        self.assertEqual(cases("2026"), [])
        self.assertEqual(cases(None), [])

    def test_a_warning_resting_on_a_record_the_view_cannot_see_is_left_out(self):
        april = SiteView(example_context(as_of="2026-04-01", warnings=Loaded.ok([
            {"id": "w9", "rule_id": "r", "title": "t", "first_seen": "2026-03-30", "evidence_record_ids": [STOP_WORK]}])))
        self.assertNotIn("warning:w9", april.items)  # its record is dated 2026-04-20

    def test_text_added_later_and_todays_status_are_left_out(self):
        april = SiteView(example_context(as_of="2026-05-01"))
        self.assertIn("rescinded", FULL.items[STOP_WORK].source.detail)
        self.assertNotIn("rescinded", april.items[STOP_WORK].source.detail)
        self.assertIn("Permit issued", FULL.items[FILING].source.detail)
        self.assertNotIn("Permit issued", JUNE.items[FILING].source.detail)
        self.assertNotIn("Permit issued", JUNE.digest())

    def test_a_piece_that_did_not_load_reads_as_not_loaded_never_as_none(self):
        view = SiteView(example_context(similar=Loaded.failed("timeout"), warnings=Loaded.not_available("not built"),
                                        profile=Loaded.failed("timeout")))
        digest = view.digest()
        self.assertEqual(digest.count("nothing is known, which is not the same as none"), 3)
        self.assertNotIn("none in this view", digest)
        self.assertEqual(SiteView(example_context(warnings=Loaded.ok([]))).digest().count("none in this view"), 1)


class StatementTests(unittest.TestCase):
    def test_the_kind_of_a_part_comes_from_what_it_cites(self):
        cited = {"record": STOP_WORK, "case": OLD_CASE, "warning": MARCH_WARNING, "action": SURVEY_ACTION}
        for kind, ref in cited.items():
            part = one(FULL, says("This is on file for the site.", ref))
            self.assertEqual((part.kind, [s.ref for s in part.sources]), (kind, [ref]))
        lead = one(FULL, says("The city publishes its construction codes.", WEB.url), web=[WEB])
        self.assertEqual((lead.kind, lead.sources[0].official), ("lead", True))

    def test_a_statement_citing_two_kinds_of_source_is_held_back(self):
        for refs in ((STOP_WORK, OLD_CASE), (MARCH_WARNING, SAFEGUARD), (SURVEY_ACTION, WEB.url), (OLD_CASE, WEB.url)):
            built = build(FULL, says("These go together.", *refs), web=[WEB])
            self.assertEqual((built.parts, len(built.problems)), ([], 1), refs)
            self.assertIn("Split it", built.problems[0])

    def test_no_source_an_unknown_id_or_an_unreturned_url_is_held_back(self):
        for refs in ((), ("dob_violations:NOPE",), ("https://example.org/not-returned",)):
            built = build(FULL, says("Something is on file.", *refs))
            self.assertEqual((built.parts, len(built.problems)), ([], 1), refs)

    def test_a_ref_hidden_by_the_as_of_day_is_refused_and_counted(self):
        built = build(JUNE, says("A complaint about the party wall is on file.", JULY_COMPLAINT), says("A later case.", LATE_CASE))
        self.assertEqual((built.parts, len(built.problems), built.after_as_of), ([], 2, 1))

    def test_numbers_must_be_in_the_cited_item(self):
        self.assertEqual(one(FULL, says("The attached building was built in 1925.", f"neighbor:{ATTACHED_BBL}")).kind, "record")
        self.assertTrue(build(FULL, says("The attached building was built in 1931.", f"neighbor:{ATTACHED_BBL}")).problems)

    def test_a_cause_is_relayed_only_for_a_past_case_and_only_as_reported(self):
        reported = "The cause, as publicly reported, was undermining of the adjoining foundation."
        self.assertEqual(one(FULL, says(reported, OLD_CASE)).kind, "case")
        self.assertTrue(build(FULL, says("It was caused by undermining of the adjoining foundation.", OLD_CASE)).problems)
        self.assertTrue(build(FULL, says("The stop work order was caused by the excavation, as reported.", STOP_WORK)).problems)

    def test_a_prediction_a_verdict_blame_or_a_count_is_held_back(self):
        for text, ref in (("This site is likely to collapse.", OLD_CASE), ("The wall will fail.", MARCH_WARNING),
                          ("The excavation is unsafe.", STOP_WORK), ("The contractor was negligent.", STOP_WORK),
                          ("There are 2 violations on the site.", STOP_WORK), ("There are no complaints on file.", STOP_WORK)):
            self.assertTrue(build(FULL, says(text, ref)).problems, text)

    def test_a_case_or_warning_part_brings_the_not_a_prediction_notice(self):
        for ref in (OLD_CASE, MARCH_WARNING):
            self.assertEqual([p.kind for p in build(FULL, says("This is in the data.", ref)).parts][-1], "notice")
        self.assertEqual([p.kind for p in build(FULL, says("This is in the data.", STOP_WORK)).parts], ["record"])

    def test_a_warnings_own_words_can_be_quoted_even_where_they_say_something_is_absent(self):
        words = FULL.items[MARCH_WARNING].source.explanation
        self.assertEqual(one(FULL, says(f'The rule says: "{words}"', MARCH_WARNING)).kind, "warning")


class CountAndSearchTests(unittest.TestCase):
    def test_the_server_writes_counts_none_unknown_and_at_least(self):
        texts = {(bbl, key): one(FULL, check(bbl, key)) for bbl, key in (
            (SITE_BBL, "ecb_violations"), (SITE_BBL, "dob_complaints"), (ATTACHED_BBL, "dob_violations"), (OTHER_BBL, "dob_complaints"))}
        self.assertEqual([p.kind for p in texts.values()], ["record", "not_found", "unknown", "record"])
        self.assertTrue(texts[(SITE_BBL, "ecb_violations")].text.startswith("1 record in ECB violations"))
        self.assertIn("the query failed, so nothing is known. This is not zero", texts[(ATTACHED_BBL, "dob_violations")].text)
        self.assertTrue(texts[(OTHER_BBL, "dob_complaints")].text.startswith("At least 1 record"))
        self.assertTrue(build(FULL, check(SITE_BBL, "nope")).problems)

    def test_an_as_of_count_covers_only_records_before_the_day(self):
        self.assertTrue(one(FULL, check(ATTACHED_BBL, "dob_complaints")).text.startswith("2 records"))
        june = one(JUNE, check(ATTACHED_BBL, "dob_complaints"))
        self.assertTrue(june.text.startswith("1 record"))
        self.assertIn("among records dated before 2026-06-01", june.text)

    def test_a_record_search_gives_a_count_none_found_and_unknown_for_a_failed_dataset(self):
        parts = build(FULL, item("record_search", text="fence")).parts
        self.assertEqual([p.kind for p in parts], ["record", "unknown"])
        self.assertTrue(parts[0].text.startswith('At least 2 records for the site and the lots touching it contain "fence"'))
        self.assertIn("This is not zero", parts[1].text)
        [none] = build(FULL, item("record_search", text="zebra", bbl=SITE_BBL)).parts
        self.assertEqual(none.kind, "not_found")
        [failed] = build(FULL, item("record_search", text="zebra", bbl=ATTACHED_BBL, dataset_key="dob_violations")).parts
        self.assertEqual(failed.kind, "unknown")

    def test_a_record_search_cannot_reach_later_records_later_text_or_todays_status(self):
        search = lambda view, text: [r.id for r in chat_record_search.search(view, RecordQuery(text=text)).matches]
        self.assertEqual(search(FULL, "party wall"), [JULY_COMPLAINT])
        self.assertEqual(search(JUNE, "party wall"), [])
        self.assertEqual(search(FULL, "rescinded"), [STOP_WORK])
        self.assertEqual(search(SiteView(example_context(as_of="2026-05-01")), "rescinded"), [])
        self.assertEqual(search(FULL, "permit issued"), [FILING])
        self.assertEqual(search(JUNE, "permit issued"), [])

    def test_a_case_search_gives_a_count_with_the_closest_cases_and_filters(self):
        [part, note] = build(FULL, item("case_search")).parts
        self.assertEqual((part.kind, note.code), ("case", "not_a_prediction"))
        self.assertTrue(part.text.startswith("3 past cases compared with this site are in the case library."))
        self.assertEqual([s.ref for s in part.sources], [LATE_CASE, OLD_CASE, FACADE_CASE])  # closest first
        ids = lambda **q: [e["case"]["id"] for e in chat_case_search.search(FULL, CaseQuery(**q)).matches]
        self.assertEqual(ids(hazard="facade"), ["ex-facade-2022"])
        self.assertEqual(ids(severity_min="3"), ["ex-wall-2026", "ex-facade-2022"])
        self.assertEqual(ids(text="underpinning collapse"), ["ex-underpinning-2019"])
        self.assertTrue(build(FULL, item("case_search", hazard="earthquake")).problems)

    def test_a_case_search_says_none_found_only_when_the_cases_loaded(self):
        [none] = build(FULL, item("case_search", text="zebra")).parts
        self.assertEqual(none.kind, "not_found")
        self.assertIn("not exhaustive", none.text)
        [unknown] = build(SiteView(example_context(similar=Loaded.failed("timeout"))), item("case_search", text="zebra")).parts
        self.assertEqual(unknown.kind, "unknown")
        self.assertIn("not the same as none", unknown.text)

    def test_a_case_search_in_a_replay_leaves_out_later_cases(self):
        [part, _] = build(JUNE, item("case_search", hazard="structural")).parts
        self.assertEqual([s.ref for s in part.sources], [OLD_CASE])
        self.assertIn("dated before 2026-06-01", part.text)

    def test_a_gap_names_only_what_could_be_read_and_is_unknown_when_nothing_could(self):
        view = SiteView(example_context(similar=Loaded.failed("timeout")))
        [gap] = build(view, item("gap", text="the depth of the neighboring foundation")).parts
        self.assertEqual(gap.kind, "not_found")
        self.assertNotIn("case_library", [q.key for q in gap.queried])
        nothing = SiteView(example_context(similar=Loaded.failed("x"), warnings=Loaded.failed("x"), actions=Loaded.failed("x"), datasets=[]))
        self.assertEqual(build(nothing, item("gap", text="anything about the foundation")).parts[0].kind, "unknown")


class ListCheckTests(unittest.TestCase):
    """The site's early warnings and action items counted by the server, with the as-of view applied."""

    def test_a_loaded_list_is_counted_under_its_own_kind_and_cut_at_the_as_of_day(self):
        warnings = one(FULL, check("", "early_warnings"))
        self.assertEqual((warnings.kind, warnings.text, len(warnings.sources)), ("warning", "2 early-warning rule results for this site.", 2))
        actions = one(FULL, check("", "action_items"))
        self.assertEqual((actions.kind, actions.text), ("action", "2 action items for this site."))
        early = SiteView(example_context(as_of="2020-01-01"))
        self.assertEqual(one(early, check("", "early_warnings")).kind, "not_found")
        self.assertIn("dated before 2020-01-01", one(early, check("", "early_warnings")).text)

    def test_a_list_that_did_not_load_is_unknown(self):
        for key, piece in (("early_warnings", "warnings"), ("action_items", "actions")):
            part = one(SiteView(example_context(**{piece: Loaded.failed("timeout")})), check("", key))
            self.assertEqual((part.kind, "This is not the same as none" in part.text), ("unknown", True))


class RuleCheckTests(unittest.TestCase):
    """An early-warning rule that could not run: the warnings shown may then not be all of them."""

    CHECKS = Loaded.ok([{"rule_id": "r1", "title": "Stop-work order, then more work", "status": "ok"},
                        {"rule_id": "r2", "title": "Heavy rain on an open excavation", "status": "error"},
                        {"rule_id": "r3", "title": "A rule for towers", "status": "not_applicable"}])

    def test_a_count_becomes_a_floor_and_none_becomes_unknown(self):
        view = SiteView(example_context(warning_checks=self.CHECKS))
        self.assertEqual(view.rules_not_checked, ["Heavy rain on an open excavation"])
        counted = one(view, check("", "early_warnings"))
        self.assertEqual(counted.kind, "warning")
        self.assertTrue(counted.text.startswith("At least 2 early-warning rule results for this site."))
        self.assertIn("1 early-warning rule was not checked (Heavy rain on an open excavation), so this is a floor", counted.text)
        none = one(SiteView(example_context(warning_checks=self.CHECKS, warnings=Loaded.ok([]))), check("", "early_warnings"))
        self.assertEqual((none.kind, "This is not the same as none" in none.text), ("unknown", True))
        # Action items are not the rules' results: they are counted as before.
        self.assertEqual(one(view, check("", "action_items")).text, "2 action items for this site.")

    def test_checks_that_all_ran_or_did_not_load_change_nothing(self):
        ran = Loaded.ok([{"rule_id": "r1", "title": "t", "status": "ok"}, {"rule_id": "r3", "title": "t", "status": "not_applicable"}])
        for checks in (ran, Loaded.failed("timeout"), Loaded.not_available("not built")):
            view = SiteView(example_context(warning_checks=checks))
            self.assertEqual((view.rules_not_checked, one(view, check("", "early_warnings")).text),
                             ([], "2 early-warning rule results for this site."))

    def test_a_warning_cited_without_the_count_still_says_a_rule_was_not_checked(self):
        view = SiteView(example_context(warning_checks=self.CHECKS))
        cited = build(view, says("A rule found a pattern.", MARCH_WARNING))
        self.assertEqual([p.code for p in cited.parts if p.kind == "notice"], ["not_a_prediction", "warning_rules_unchecked"])
        both = build(view, says("A rule found a pattern.", MARCH_WARNING), check("", "early_warnings"))
        self.assertEqual([p.code for p in both.parts if p.kind == "notice"], ["not_a_prediction"])
        self.assertIn("RULES THAT COULD NOT BE CHECKED: Heavy rain on an open excavation", view.digest())
        self.assertNotIn("RULES THAT COULD NOT BE CHECKED", FULL.digest())


class PageActionTests(unittest.TestCase):
    def test_a_layer_is_toggled_only_if_the_page_has_it(self):
        built = build(FULL, actions=[action("toggle_layer", layer_id="sandy_inundation", on=False)])
        [done] = built.actions
        self.assertEqual((done.type, done.layer_id, done.name, done.on), ("toggle_layer", "sandy_inundation", "Sandy Inundation Zone", False))
        self.assertIn("hide the map layer", built.parts[0].text)
        bad = build(FULL, actions=[action("toggle_layer", layer_id="made_up")])
        self.assertEqual((bad.actions, bad.actions_dropped, len(bad.problems)), ([], 1, 1))
        unloaded = build(SiteView(example_context(layers=Loaded.failed("timeout"))), actions=[action("toggle_layer", layer_id="sandy_inundation")])
        self.assertEqual(unloaded.actions, [])

    def test_the_map_moves_only_to_an_item_of_the_view_with_a_place(self):
        targets = {r: build(FULL, actions=[action("fly_to", ref=r)]).actions for r in (f"site:{SITE_BBL}", STOP_WORK, OLD_CASE)}
        self.assertEqual([t[0].bbl for t in targets.values()], [SITE_BBL, SITE_BBL, "3000020001"])
        self.assertEqual((targets[OLD_CASE][0].lat, targets[OLD_CASE][0].lon), (40.7, -73.9))
        for ref in (MARCH_WARNING, SURVEY_ACTION, "case:made-up", ""):
            self.assertEqual(build(FULL, actions=[action("fly_to", ref=ref)]).actions, [], ref)
        self.assertEqual(build(JUNE, actions=[action("fly_to", ref=LATE_CASE)]).actions, [])

    def test_pinning_needs_an_open_project_and_an_answer(self):
        pin = [action("pin_answer", ref="this")]
        with_project = build(FULL, says("A stop work order was issued.", STOP_WORK), actions=pin, project_id="p1")
        self.assertEqual([(a.type, a.project_id, a.target) for a in with_project.actions], [("pin_answer", "p1", "this")])
        no_project = build(FULL, says("A stop work order was issued.", STOP_WORK), actions=pin)
        self.assertEqual((no_project.actions, no_project.parts[-1].code), ([], "pin_needs_project"))
        self.assertEqual(build(FULL, actions=pin, project_id="p1").actions, [])  # nothing in the answer to pin
        previous = [action("pin_answer", ref="previous")]
        self.assertEqual(build(FULL, actions=previous, project_id="p1", has_history=True).actions[0].target, "previous")
        alone = build(FULL, actions=previous, project_id="p1")
        self.assertEqual((alone.actions, alone.parts[-1].code), ([], "pin_needs_answer"))

    def test_an_answer_needs_an_item_or_an_action_and_respects_the_caps(self):
        self.assertTrue(build(FULL).problems)
        self.assertTrue(build(FULL, actions=[action("fly_to", ref=STOP_WORK)] * 5).problems)
        self.assertTrue(build_parts(FULL, {"items": [{"kind": "statement"}], "extra": 1}, []).problems)


if __name__ == "__main__":
    unittest.main()
