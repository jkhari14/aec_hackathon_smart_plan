"""The interface copy (web/src/copy/index.ts) and the demo sites keep the team's wording rules."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from typing import get_args

from api import contracts

ROOT = Path(__file__).resolve().parent.parent
COPY = (ROOT / "web" / "src" / "copy" / "index.ts").as_uri()
DEMO_SITES = ROOT / "data" / "demo_sites.json"

# From jahleel/api/chat/chat_wording_checks.py: blame or "would have", and verdicts on safety or compliance.
BLAME = re.compile(
    r"\b(?:would|could|might|should|may)(?:\s+not)?\s+have\s+(?:been\s+)?(?:prevent|avoid|stopp|caught|known|done|acted)\w*"
    r"|\b(?:at fault|to blame|blamed?|negligen\w+|reckless\w*|liable|failed to (?:prevent|protect|act))\b", re.I)
VERDICT = re.compile(
    r"\b(?:is|are|was|were|appears?|seems?|looks?)\s+(?:\w+\s+)?(?:code[- ])?(?:compliant|non-?compliant|safe|unsafe|"
    r"sound|adequate|inadequate|legal|illegal|dangerous)\b|\bstructurally sound\b|\bsafe to (?:dig|build|excavate|proceed)\b", re.I)
# The pattern score and similar cases are comparisons, never a forecast for a building.
PREDICTION = re.compile(r"\b(?:predict\w*|will (?:fail|collapse)|likelihood of (?:failure|collapse)|guarantee\w*)\b", re.I)
COMPANY = re.compile(r"\b(?:LLC|Inc\.?|Corp\.?|Ltd\.?|LLP|PLLC|Realty)(?=\W|$)")


def strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in strings(v)]
    return []


def load_copy() -> dict:
    node = shutil.which("node")
    if node is None:
        raise unittest.SkipTest("node is not installed")
    script = f"import {{ copy }} from {json.dumps(COPY)}; console.log(JSON.stringify(copy));"
    result = subprocess.run([node, "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e", script],
                            capture_output=True, text=True, timeout=30)
    if result.returncode != 0 and "strip-types" in result.stderr:
        raise unittest.SkipTest("this Node cannot run TypeScript directly")
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def labels(literal) -> set[str]:
    return {str(v) for v in get_args(literal)}


class WordingTest(unittest.TestCase):
    def check(self, texts: list[str], where: str) -> None:
        for text in texts:
            for name, pattern in (("blame", BLAME), ("verdict", VERDICT), ("prediction", PREDICTION), ("company", COMPANY)):
                match = pattern.search(text)
                self.assertIsNone(match, f"{where}: {name} wording {match.group() if match else ''!r} in {text!r}")

    def test_copy_wording(self):
        self.check(strings(load_copy()), "web/src/copy")

    def test_demo_site_wording(self):
        # The "rules" list quotes the banned phrases on purpose; only the sites themselves are checked.
        self.check(strings(json.loads(DEMO_SITES.read_text(encoding="utf-8"))["sites"]), "data/demo_sites.json")


class CoverageTest(unittest.TestCase):
    def test_every_hazard_and_stage_has_a_label(self):
        copy = load_copy()
        self.assertEqual(set(copy["hazards"]), labels(contracts.Hazard))
        self.assertEqual(set(copy["stages"]), labels(contracts.Stage))
        self.assertEqual(set(copy["roles"]), labels(contracts.Role))
        self.assertEqual(set(copy["disciplines"]), labels(contracts.Discipline))
        self.assertEqual(set(copy["jobTypes"]), labels(contracts.JobType))
        self.assertEqual(set(copy["queryStatus"]), labels(contracts.QueryStatus))
        self.assertEqual(set(copy["severity"]), labels(contracts.Severity))
        self.assertEqual(set(copy["sourceLabels"]), labels(contracts.ChatAnswerPart.model_fields["kind"].annotation))

    def test_demo_sites_are_well_formed(self):
        data = json.loads(DEMO_SITES.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["sites"]), 2)
        for site in data["sites"]:
            self.assertRegex(site["bbl"], r"^\d{10}$")
            self.assertTrue(site["why_it_works"] and site["sources"], site["id"])
            self.assertTrue(all(s["url"] and s["date"] for s in site["sources"]), site["id"])
        # The pitch never opens on Nov 11: the top-ranked site is not 1321 Flatbush or its excavation lot.
        hero = min(data["sites"], key=lambda s: s["rank"])
        self.assertNotIn(hero["bbl"], {"3052110073", "3052110074"})


class DemoSeedsTest(unittest.TestCase):
    def test_seeds_point_at_real_sites_and_layers(self):
        seeds = json.loads((ROOT / "pitch" / "demo_seeds.json").read_text(encoding="utf-8"))
        site_ids = {s["id"] for s in json.loads(DEMO_SITES.read_text(encoding="utf-8"))["sites"]}
        for key in ("hero_site_id", "backup_site_id", "offline_site_id"):
            self.assertIn(seeds[key], site_ids, key)
        catalog = json.loads((ROOT / "contracts" / "fixtures" / "layer_catalog.json").read_text(encoding="utf-8"))
        self.assertLessEqual(set(seeds["layers_on"]), {layer["layer_id"] for layer in catalog})
        self.assertEqual({m["role"] for m in seeds["project"]["members"]}, labels(contracts.Role))


if __name__ == "__main__":
    unittest.main()
