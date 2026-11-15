"""The party-wall edge on the map: web/src/features/city_map/party_walls.ts, run with Node's type stripping."""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = (ROOT / "web" / "src" / "features" / "city_map" / "party_walls.ts").as_uri()

# Two 10 m x 10 m lots side by side (sharing x = 10 m), and one lot 5 m away that touches nothing.
DEG_X = 1 / (111320 * 0.7547)  # metres to degrees of longitude near 40.99 N
DEG_Y = 1 / 110540
LAT0, LON0 = 40.99, -73.95


def square(x0: float, y0: float, size: float = 10) -> dict:
    corners = [(x0, y0), (x0 + size, y0), (x0 + size, y0 + size), (x0, y0 + size), (x0, y0)]
    return {"type": "Polygon", "coordinates": [[[LON0 + x * DEG_X, LAT0 + y * DEG_Y] for x, y in corners]]}


SCRIPT = """
import { partyWalls } from %s;
const [site, neighbors] = JSON.parse(process.argv[1]);
console.log(JSON.stringify(partyWalls(site, neighbors)));
"""


def run_party_walls(site: dict, neighbors: list[dict]) -> list[dict]:
    node = shutil.which("node")
    if node is None:
        raise unittest.SkipTest("node is not installed")
    result = subprocess.run(
        [node, "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e",
         SCRIPT % json.dumps(MODULE), json.dumps([site, neighbors])],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0 and "strip-types" in result.stderr:
        raise unittest.SkipTest("this Node cannot run TypeScript directly")
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class PartyWallTest(unittest.TestCase):
    def test_shared_edge_is_found_with_its_length(self):
        walls = run_party_walls(square(0, 0), [{"bbl": "3000000002", "geometry": square(10, 0)}])
        self.assertEqual(len(walls), 1)
        self.assertEqual(walls[0]["properties"]["bbl"], "3000000002")
        self.assertAlmostEqual(walls[0]["properties"]["length_m"], 10, delta=0.2)

    def test_a_lot_that_does_not_touch_has_no_wall(self):
        self.assertEqual(run_party_walls(square(0, 0), [{"bbl": "3000000003", "geometry": square(15, 0)}]), [])

    def test_a_corner_touch_is_not_a_wall(self):
        self.assertEqual(run_party_walls(square(0, 0), [{"bbl": "3000000004", "geometry": square(10, 10)}]), [])


if __name__ == "__main__":
    unittest.main()
