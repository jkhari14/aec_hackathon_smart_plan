"""The deploy's demo snapshot: every GET answer for the demo sites, saved under keys the web client rebuilds."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.demo_snapshot import snapshot, snapshot_key

BEDFORD = "3052110074"


class SnapshotKey(unittest.TestCase):
    # web/src/api/client.ts snapshotKey() must give the same answers.
    def test_examples(self):
        self.assertEqual(snapshot_key("/api/layers"), "layers")
        self.assertEqual(snapshot_key("/api/search?q=2625%20Bedford%20Ave,%20Brooklyn"), "search@q=2625-bedford-ave-brooklyn")
        self.assertEqual(snapshot_key(f"/api/sites/{BEDFORD}/warnings/checks?as_of=2026-06-01"),
                         f"sites/{BEDFORD}/warnings/checks@as_of=2026-06-01")
        self.assertEqual(snapshot_key("/api/x?b=2&a=1"), "x@a=1&b=2")


class Snapshot(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "snapshot"
        # Only the cached site, so the test never pulls a lot or its weather live.
        cls.manifest = snapshot(cls.out, ["2026-06-01"], sites=[{"bbl": BEDFORD, "address": "2625 Bedford Ave, Brooklyn"}])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_saves_the_demo_site_and_the_citywide_routes(self):
        routes = self.manifest["routes"]
        for key in ["layers", "cases", f"sites/{BEDFORD}/profile", f"sites/{BEDFORD}/warnings",
                    f"sites/{BEDFORD}/warnings@as_of=2026-06-01", "search@q=2625-bedford-ave-brooklyn"]:
            self.assertIn(key, routes)
        self.assertTrue(self.manifest["saved_at"])

    def test_every_saved_answer_is_json_and_labels_sample_data(self):
        manifest = json.loads((self.out / "manifest.json").read_text())
        self.assertEqual(manifest, self.manifest)
        for key, route in manifest["routes"].items():
            json.loads((self.out / f"{key}.json").read_text())
            self.assertIsInstance(route["sample"], bool)


if __name__ == "__main__":
    unittest.main()
