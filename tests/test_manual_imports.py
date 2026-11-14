"""Offline tests for manual_imports. Run from the repo root: python3 -m unittest discover -s tests -t ."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from manual_imports import load_imports as li
from manual_imports.new_import import start_import

REPO = Path(__file__).resolve().parent.parent
RAW = b"%PDF-1.4 a stand-in for DOB's category list\n"

PROVENANCE = {
    "schema": li.SCHEMA, "source_key": "dob_complaint_categories", "fetched_by": "project-lead",
    "fetch_method": "script_with_approval", "fetched_at": "2026-11-14T17:00:00-05:00",
    "source_url": "https://data.cityofnewyork.us/api/views/eabe-havv/files/x?download=true",
    "landing_url": "https://data.cityofnewyork.us/d/eabe-havv",
    "terms": {"url": "https://nycadmincode.readthedocs.io/t23/c05/", "clause": "23-502(d)",
              "read_on": "2026-11-14", "verdict": "a"},
    "file": {"name": "list.pdf", "bytes": len(RAW), "sha256": hashlib.sha256(RAW).hexdigest()},
    "document_date": None, "document_date_note": "The list carries no date.",
    "extracted_by": "claude-agent", "extraction_method": "pdftotext -layout", "checked": None,
    "approved_by": "project-lead",
}
FACTS = {"schema": li.FACTS_SCHEMA, "source_key": "dob_complaint_categories",
         "facts": [{"code": "30", "description": "A stand-in description", "priority": "A", "page": 1}]}


class ManualImportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, prov=None, facts=None, raw=RAW, source="dob_complaint_categories",
              folder="2026-11-14_category-list"):
        d = self.root / source / folder
        d.mkdir(parents=True)
        (d / "provenance.json").write_text(json.dumps(PROVENANCE if prov is None else prov))
        (d / "facts.json").write_text(json.dumps(FACTS if facts is None else facts))
        if raw is not None:
            (d / "raw").mkdir()
            (d / "raw" / "list.pdf").write_bytes(raw)
        return d

    def refused(self, prov=None, facts=None, **kw) -> str:
        with self.assertRaises(li.ManualImportError) as ctx:
            li.load_import(self.write(prov, facts, **kw))
        return str(ctx.exception)

    def changed(self, **changes) -> dict:
        prov = copy.deepcopy(PROVENANCE)
        prov.update(changes)
        return prov

    def test_a_valid_import_is_its_own_tier_and_never_ok(self):
        imp = li.load_import(self.write())
        self.assertEqual((imp.tier, imp.status), ("manual_import", "imported_unchecked"))
        self.assertNotIn("ok", li.STATUSES)
        self.assertEqual(imp.raw["verified"], True)

    def test_raw_file_absent_is_said_not_assumed(self):
        imp = li.load_import(self.write(raw=None))
        self.assertFalse(imp.raw["present"])
        self.assertIsNone(imp.raw["verified"])

    def test_a_different_file_is_refused(self):
        self.assertIn("sha256", self.refused(raw=RAW.replace(b"stand", b"STAND")))

    def test_checked_needs_a_second_person(self):
        same = {"by": "claude-agent", "on": "2026-11-14", "how": "compared every row"}
        self.assertIn("second person", self.refused(self.changed(checked=same)))
        shutil.rmtree(self.root / "dob_complaint_categories")
        other = dict(same, by="structural-engineer")
        self.assertEqual(li.load_import(self.write(self.changed(checked=other))).status, "imported_checked")

    def test_refusals(self):
        cases = [
            (self.changed(fetched_by="Jane Doe"), "never a person's name"),
            (self.changed(source_url="https://buildingviolation.com/x.html"), "is not the publisher's"),
            (self.changed(terms=dict(PROVENANCE["terms"], verdict="d")), "never imported"),
            (self.changed(document_date_note=""), "document_date_note"),
            (self.changed(extraction_method=" "), "extraction_method"),
            (self.changed(fetched_at="2026-11-13T09:00:00-05:00"), "fetched_at date"),
            (self.changed(fetched_at="2026-11-14T17:00:00"), "UTC offset"),
            (self.changed(approved_by=None), "approved_by"),
            (self.changed(source_url="https://www.nyc.gov/assets/buildings/pdf/complaint_category.pdf"),
             "carries verdict 'b'"),
        ]
        for prov, expected in cases:
            with self.subTest(expected):
                shutil.rmtree(self.root / "dob_complaint_categories", ignore_errors=True)
                self.assertIn(expected, self.refused(prov))

    def test_dob_now_documents_come_from_a_person_in_a_browser(self):
        prov = self.changed(source_key="dob_now_document", source_url="https://a810-dobnow.nyc.gov/x.pdf",
                            terms=dict(PROVENANCE["terms"], verdict="b"))
        facts = {"schema": li.FACTS_SCHEMA, "source_key": "dob_now_document",
                 "facts": [{"job_filing_number": "B00000000-S3", "document_title": "A letter", "page": 1,
                            "fact": " ".join(["word"] * 30)}]}
        message = self.refused(prov, facts, source="dob_now_document")
        self.assertIn("fetch_method for dob_now_document", message)
        self.assertIn("over 25 words", message)

    def test_fact_rules(self):
        fact = FACTS["facts"][0]
        cases = [
            ([dict(fact, owner_name="someone")], "does not allow"),
            ([{k: v for k, v in fact.items() if k != "page"}], "needs page"),
            ([fact, fact], "appears twice"),
            ([dict(fact, page=0)], "page must be"),
        ]
        for facts, expected in cases:
            with self.subTest(expected):
                shutil.rmtree(self.root / "dob_complaint_categories", ignore_errors=True)
                self.assertIn(expected, self.refused(facts=dict(FACTS, facts=facts)))

    def test_decode_gives_a_gap_for_an_unknown_code(self):
        imp = li.load_import(self.write())
        self.assertEqual(li.decode("30", imp)["status"], "imported_unchecked")
        gap = li.decode("L3", imp)
        self.assertEqual((gap["status"], gap["description"], gap["tier"]), ("not_in_key", None, "manual_import"))

    def test_new_import_skeleton_does_not_validate_until_filled(self):
        src_file = self.root / "downloaded.pdf"
        src_file.write_bytes(RAW)
        folder = start_import("dob_complaint_categories", src_file, "https://data.cityofnewyork.us/x",
                              "project-lead", "browser_by_person", root=self.root / "imports")
        self.assertTrue((folder / "raw" / "downloaded.pdf").is_file())
        with self.assertRaises(li.ManualImportError):
            li.load_import(folder)

    def test_raw_files_are_gitignored(self):
        probe = "data/manual_imports/dob_now_document/2026-11-14_x/raw/letter.pdf"
        result = subprocess.run(["git", "check-ignore", "-q", probe], cwd=REPO)
        self.assertEqual(result.returncode, 0, "raw/ under data/manual_imports must be gitignored")

    def test_committed_imports_all_validate(self):
        for imp in li.load_all():
            self.assertEqual(imp.tier, "manual_import")


if __name__ == "__main__":
    unittest.main()
