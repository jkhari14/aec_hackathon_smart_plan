"""The Cityweft site model route: request shape, axis reading, binary packing, cache and errors."""

from __future__ import annotations

import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.main import app
from api.routers import context3d_router as c3d
from api.routers.router_data import data_root

LAT, LON = 40.6339, -73.9476

# One 10 m cube-ish building as an indexed mesh: two triangles of its roof are enough to check order.
ANSWER = {
    "origin": [LAT, LON],
    "geometry": [
        {"type": "surface", "geometryType": "meshes", "meshes": [{"vertices": [0, 0, 0] * 3}]},
        {"type": "buildings", "geometryType": "meshes", "meshes": [
            {"vertices": [0, 0, 12, 10, 0, 12, 10, 10, 12, 0, 10, 12], "indices": [0, 1, 2, 0, 2, 3],
             "descriptor": {"type": "building", "buildingHeight": 14.0}},
            {"vertices": [20, 0, 0, 21, 0, 0, 21, 1, 5]},  # triangle soup, no indices
        ]},
    ],
    "attributions": [{"name": "OpenStreetMap contributors"}],
}


def unpack(data: bytes) -> tuple[dict, list[float], list[int]]:
    (length,) = struct.unpack_from("<I", data, 0)
    header = json.loads(data[4:4 + length])
    offset = 4 + length
    positions = list(struct.unpack_from(f"<{header['vertex_count'] * 3}f", data, offset))
    offset += 12 * header["vertex_count"]
    indices = list(struct.unpack_from(f"<{header['index_count']}I", data, offset))
    return header, positions, indices


class SquarePolygonTest(unittest.TestCase):
    def test_closed_square_about_500_m_across(self):
        ring = c3d.square_polygon(LAT, LON, 250)
        self.assertEqual(len(ring), 5)
        self.assertEqual(ring[0], ring[-1])
        lats = [p[0] for p in ring]
        self.assertAlmostEqual((max(lats) - min(lats)) * 110_540, 500, delta=1)


class AxesTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(c3d.parse_axes("x,-z,y"), [(0, 1.0), (2, -1.0), (1, 1.0)])
        for bad in ("x,y", "x,x,z", "a,b,c"):
            with self.assertRaises(ValueError):
                c3d.parse_axes(bad)

    def test_merge_reads_east_north_up_and_offsets_indices(self):
        positions, indices, buildings = c3d.merge_buildings(ANSWER, c3d.parse_axes("x,y,z"))
        # Cityweft's height when it gives one, else the highest vertex.
        self.assertEqual(buildings, [[0, 4, 14.0], [4, 3, 5.0]])
        self.assertEqual(positions[:3], [0.0, 0.0, 12.0])
        self.assertEqual(indices, [0, 1, 2, 0, 2, 3, 4, 5, 6])

    def test_default_reads_cityweft_as_north_east_up(self):
        self.assertEqual(c3d.parse_axes(c3d.DEFAULT_AXES), [(1, 1.0), (0, 1.0), (2, 1.0)])

    def test_merge_with_y_up(self):
        positions, _, _ = c3d.merge_buildings(ANSWER, c3d.parse_axes("x,-z,y"))
        self.assertEqual(positions[3:6], [10.0, -12.0, 0.0])


class RouteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.calls: list[dict] = []

        def fake(key, body):
            self.calls.append(body)
            return ANSWER

        app.dependency_overrides[data_root] = lambda: Path(self.tmp.name)
        app.dependency_overrides[c3d.cityweft_caller] = lambda: fake
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.pop(data_root, None)
        app.dependency_overrides.pop(c3d.cityweft_caller, None)
        self.tmp.cleanup()

    def get(self):
        return self.client.get("/api/context3d", params={"lat": LAT, "lon": LON})

    def test_no_key_is_503(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            reply = self.get()
        self.assertEqual(reply.status_code, 503)
        self.assertIn("CITYWEFT_API_KEY", reply.json()["detail"])
        self.assertEqual(self.calls, [])

    def test_model_then_cache(self):
        with mock.patch.dict(os.environ, {"CITYWEFT_API_KEY": "cw_test"}, clear=True):
            first = self.get()
            second = self.get()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content, second.content)
        self.assertEqual(len(self.calls), 1, "the second request comes from the cache")
        body = self.calls[0]
        self.assertEqual(body["origin"], [LAT, LON])
        self.assertEqual(body["settings"]["geometry"], ["buildings"])
        header, positions, indices = unpack(first.content)
        self.assertEqual(header["building_count"], 2)
        self.assertEqual(header["buildings"], [[0, 4, 14.0], [4, 3, 5.0]])
        self.assertEqual(header["attributions"], ["OpenStreetMap contributors"])
        self.assertEqual(len(positions), 21)
        self.assertEqual(indices[-3:], [4, 5, 6])

    def test_cityweft_failure_is_502(self):
        def broken(key, body):
            raise HTTPException(502, "the Cityweft key was refused (HTTP 401)")

        app.dependency_overrides[c3d.cityweft_caller] = lambda: broken
        with mock.patch.dict(os.environ, {"CITYWEFT_API_KEY": "cw_test"}, clear=True):
            reply = self.get()
        self.assertEqual(reply.status_code, 502)

    def test_outside_nyc_is_422(self):
        reply = self.client.get("/api/context3d", params={"lat": 51.5, "lon": -0.1})
        self.assertEqual(reply.status_code, 422)

    def test_not_in_the_contract(self):
        self.assertNotIn("/api/context3d", app.openapi()["paths"])


if __name__ == "__main__":
    unittest.main()
