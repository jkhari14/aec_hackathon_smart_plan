"""Offline tests for what the chat may see on an as-of day."""

import re
import unittest
from datetime import date

from jahleel.api.brief.brief_build import build_brief
from jahleel.api.chat.chat_answer_build import build_parts
from jahleel.api.chat.chat_brief_view import LATER, BriefView, _scrub
from jahleel.tests.chat_test_support import (
    COLLAPSE_DAY_VIOLATION, S3, SITE, SITE_BBL, STOP_WORK_ECB, check, says,
)

JUNE_1 = date(2026, 6, 1)
REQUEST_311 = "dob_311_requests:68381531"  # dated 2026-03-18; DOB's resolution recorded 2026-05-08


def setUpModule():
    global FULL, JUNE, APRIL
    FULL = BriefView(build_brief(SITE))
    JUNE = BriefView(build_brief(SITE, as_of=JUNE_1))
    APRIL = BriefView(build_brief(SITE, as_of=date(2026, 4, 1)))


class AsOfTests(unittest.TestCase):
    def test_a_record_dated_on_or_after_the_day_cannot_be_cited(self):
        self.assertIn(COLLAPSE_DAY_VIOLATION, FULL.items)
        self.assertNotIn(COLLAPSE_DAY_VIOLATION, JUNE.items)
        built = build_parts(JUNE, {"items": [says("A DOB violation mentions a stop work order.", COLLAPSE_DAY_VIOLATION)]}, [])
        self.assertEqual(built.parts, [])
        self.assertEqual(built.after_as_of, 1)

    def test_the_day_itself_is_left_out(self):
        on_the_day = BriefView(build_brief(SITE, as_of=date(2026, 4, 23)))
        self.assertNotIn(STOP_WORK_ECB, on_the_day.items)
        self.assertIn(STOP_WORK_ECB, BriefView(build_brief(SITE, as_of=date(2026, 4, 24))).items)

    def test_the_model_reads_nothing_dated_on_or_after_the_day(self):
        digest = JUNE.digest()
        self.assertNotIn("2824347", digest)
        cited_lines = [line for line in digest.splitlines() if line.startswith(("[", "  "))]  # all but headings and caveats
        self.assertFalse([line for line in cited_lines if "COLLAPSE" in line.upper()])
        later = [d for d in re.findall(r"\d{4}-\d{2}-\d{2}", digest) if d >= "2026-06-01"]
        self.assertEqual(sorted(set(later)), ["2026-06-01", "2026-11-14"])  # the as-of day and the pull date

    def test_an_approval_dated_on_or_after_the_day_is_not_shown(self):
        self.assertIn("Approved 2026-06-03.", FULL.items[S3].source.detail)
        self.assertIn("No approval dated before 2026-06-01.", JUNE.items[S3].source.detail)
        self.assertNotIn("2026-06-03", JUNE.items[S3].evidence)
        self.assertIn("Approved 2026-06-03.", BriefView(build_brief(SITE, as_of=date(2026, 6, 4))).items[S3].source.detail)
        self.assertNotIn("pproved", FULL.items[STOP_WORK_ECB].source.detail)  # only filings carry an approval

    def test_a_later_date_inside_checklist_text_is_masked(self):
        self.assertEqual(_scrub({"note": "seen 2026-05-31, again 2026-06-01"}, "2026-06-01"),
                         {"note": f"seen 2026-05-31, again {LATER}"})
        self.assertEqual(_scrub({"filing_status": "On Hold", "status_is_after_cutoff": True, "id": "x"}, "2026-06-01"),
                         {"status_is_after_cutoff": True, "id": "x"})

    def test_todays_status_is_dropped_in_a_replay(self):
        self.assertIn("Status today: On Hold", FULL.items[S3].source.detail)
        self.assertNotIn("On Hold", JUNE.items[S3].source.detail)
        self.assertNotIn("Pending Withdrawal", JUNE.digest())
        self.assertNotIn("Pending Withdrawal", JUNE.items["row:foundation_protection"].evidence)

    def test_text_written_later_shows_only_once_it_existed(self):
        self.assertIn("removed the stop work order", JUNE.items[REQUEST_311].source.detail)
        self.assertIn(REQUEST_311, APRIL.items)
        self.assertNotIn("removed the stop work order", APRIL.items[REQUEST_311].source.detail)
        self.assertNotIn("mentions a stop-work order", APRIL.items[REQUEST_311].source.detail)

    def test_a_lead_reported_after_the_day_is_not_shown(self):
        self.assertIn("lead:notice:1", FULL.items)
        day_of = BriefView(build_brief(SITE, as_of=date(2026, 11, 11)))  # the letter is dated June 10; the report, Nov 12
        self.assertNotIn("lead:notice:1", day_of.items)
        self.assertNotIn("northeastern", day_of.digest().lower())
        self.assertIn("its report is dated on or after the as-of day", day_of.digest())

    def test_counts_are_of_the_records_dated_before_the_day(self):
        [full] = build_parts(FULL, {"items": [check(SITE_BBL, "ecb_violations")]}, []).parts
        [june] = build_parts(JUNE, {"items": [check(SITE_BBL, "ecb_violations")]}, []).parts
        self.assertTrue(full.text.startswith("4 records"))
        self.assertTrue(june.text.startswith("3 records"))
        self.assertIn("dated before 2026-06-01", june.text)

    def test_a_dataset_with_nothing_before_the_day_is_none_found_for_that_view(self):
        [part] = build_parts(JUNE, {"items": [check(SITE_BBL, "dob_safety_violations")]}, []).parts
        self.assertEqual(part.kind, "not_found")
        self.assertIn("among records dated before 2026-06-01", part.text)


class CappedPullTests(unittest.TestCase):
    """A dataset that hit the pull's row cap: its count is a floor, and an empty view of it is unknown."""

    def _capped(self, as_of=None):
        brief = build_brief(SITE, as_of=as_of)
        for dataset in brief.site.datasets:
            if dataset.key == "ecb_violations":
                dataset.truncated = True
        return BriefView(brief)

    def test_a_capped_count_reads_at_least(self):
        view = self._capped()
        [part] = build_parts(view, {"items": [check(SITE_BBL, "ecb_violations")]}, []).parts
        self.assertTrue(part.text.startswith("At least 4 records"))
        self.assertIn("oldest records are missing", part.text)
        self.assertIn("ecb_violations: at least 4", view.digest())

    def test_an_empty_view_of_a_capped_dataset_is_unknown_not_none(self):
        view = self._capped(as_of=date(2000, 1, 1))
        [part] = build_parts(view, {"items": [check(SITE_BBL, "ecb_violations")]}, []).parts
        self.assertEqual(part.kind, "unknown")
        self.assertIn("This is not zero", part.text)


class DigestTests(unittest.TestCase):
    def test_every_listed_record_can_be_cited_and_long_datasets_say_they_are_cut(self):
        digest = FULL.digest()
        listed = re.findall(r"^\[([a-z_0-9]+:[^\]]+)\] lot ", digest, flags=re.M)
        self.assertTrue(listed)
        self.assertTrue(all(ref in FULL.items for ref in listed))
        self.assertIn("hpd_violations: 129 (5 listed below)", digest)
        self.assertLess(len(digest), 120_000)

    def test_records_the_checklist_points_to_and_stop_work_mentions_are_always_listed(self):
        digest = FULL.digest()
        for ref in (S3, STOP_WORK_ECB, REQUEST_311):
            self.assertIn(f"[{ref}]", digest)

    def test_a_lot_with_no_pluto_record_has_no_lot_facts_to_cite(self):
        self.assertNotIn("lot:3052110054", FULL.items)
        self.assertIn("PLUTO holds no record for it", FULL.digest())


if __name__ == "__main__":
    unittest.main()
