"""The layers routes over a temp data/layers/: the catalog, box and as-of filters, the cap, errors never as zero."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from api.main import app
from api.routers import layers_router
from api.routers.router_data import data_root
from api.stubs import FIXTURE_HEADER, fixture

INCIDENTS = fixture("layer_features")  # a dated layer: construction_incidents


def point(feature_id: str, lon: float, lat: float, date, severity: int) -> dict:
    feature = copy.deepcopy(INCIDENTS["features"][0])
    feature["geometry"] = {"type": "Point", "coordinates": [lon, lat]}
    feature["properties"].update(id=feature_id, date=date, severity=severity)
    return feature


def zone_layer() -> dict:
    layer = {**INCIDENTS["layer"], "layer_id": "flood_zone", "name": "Flood zone", "hazard": "flood"}
    feature = copy.deepcopy(INCIDENTS["features"][0])
    feature["geometry"] = {"type": "Polygon", "coordinates": [[[-74.0, 40.6], [-73.9, 40.6], [-73.9, 40.7], [-74.0, 40.6]]]}
    feature["properties"].update(id="zone-1", layer_id="flood_zone", hazard="flood", date=None)
    return {"type": "FeatureCollection", "layer": layer, "features": [feature]}


class LayersRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "data"
        (self.root / "layers").mkdir(parents=True)
        app.dependency_overrides[data_root] = lambda: self.root
        self.client = TestClient(app)
        features = [point("a", -73.95, 40.65, "2026-03-01", 1), point("b", -73.95, 40.65, "2026-07-01", 2),
                    point("c", -73.80, 40.75, "2025-01-01T09:00:00", 0), point("u", -73.95, 40.65, None, 3)]
        self.write("construction_incidents", {**INCIDENTS, "features": features})
        self.write("flood_zone", zone_layer())

    def tearDown(self):
        app.dependency_overrides.pop(data_root, None)
        self.tmp.cleanup()

    def write(self, layer_id: str, collection: dict) -> None:
        (self.root / "layers" / f"{layer_id}.geojson").write_text(json.dumps(collection))

    def ids(self, query: str = "", layer: str = "construction_incidents") -> list[str]:
        response = self.client.get(f"/api/layers/{layer}{query}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.headers.get(FIXTURE_HEADER))
        return sorted(f["properties"]["id"] for f in response.json()["features"])

    def test_the_catalog_comes_from_the_layer_files_or_catalog_json(self):
        listed = self.client.get("/api/layers")
        self.assertEqual(sorted(e["layer_id"] for e in listed.json()), ["construction_incidents", "flood_zone"])
        self.assertIsNone(listed.headers.get(FIXTURE_HEADER))
        (self.root / "layers" / "catalog.json").write_text(json.dumps([zone_layer()["layer"]]))
        self.assertEqual([e["layer_id"] for e in self.client.get("/api/layers").json()], ["flood_zone"])

    def test_box_and_as_of_filters(self):
        self.assertEqual(self.ids(), ["a", "b", "c", "u"])
        self.assertEqual(self.ids("?bbox=-74.0,40.6,-73.9,40.7"), ["a", "b", "u"])
        # dated layer: the undated feature cannot be shown to come before the date, so a replay leaves it out
        self.assertEqual(self.ids("?as_of=2026-06-01"), ["a", "c"])
        self.assertEqual(self.ids("?as_of=2026-06-01", layer="flood_zone"), ["zone-1"], "a zone layer keeps its zones")
        filtered = self.client.get("/api/layers/construction_incidents?as_of=2026-06-01&bbox=-74.0,40.6,-73.9,40.7").json()
        self.assertEqual((filtered["layer"]["feature_count"], [f["properties"]["id"] for f in filtered["features"]]), (1, ["a"]))

    def test_over_the_cap_is_cut_most_severe_first_and_marked_capped(self):
        with mock.patch.object(layers_router, "MAX_FEATURES", 2):
            answer = self.client.get("/api/layers/construction_incidents").json()
        self.assertEqual(answer["layer"]["status"], "capped")
        self.assertEqual(answer["layer"]["feature_count"], 4)
        self.assertEqual([f["properties"]["id"] for f in answer["features"]], ["u", "b"])

    def test_a_listed_layer_with_no_file_is_an_error_not_an_empty_layer(self):
        (self.root / "layers" / "flood_zone.geojson").unlink()
        catalog = [INCIDENTS["layer"], zone_layer()["layer"]]
        (self.root / "layers" / "catalog.json").write_text(json.dumps(catalog))
        layer = self.client.get("/api/layers/flood_zone").json()["layer"]
        self.assertEqual((layer["status"], layer["feature_count"]), ("error", None))

    def test_bad_requests_and_broken_files(self):
        self.assertEqual(self.client.get("/api/layers/Not_A-Layer").status_code, 404)
        self.assertEqual(self.client.get("/api/layers/watchlist").status_code, 404)
        for query in ("?bbox=1,2,3", "?bbox=-73,40,-74,41", "?bbox=nan,40,-73,41", "?as_of=2026-6-1", "?as_of=yesterday"):
            self.assertEqual(self.client.get(f"/api/layers/construction_incidents{query}").status_code, 422, query)
        (self.root / "layers" / "construction_incidents.geojson").write_text('{"type": "FeatureCollection"}')
        broken = TestClient(app, raise_server_exceptions=False).get("/api/layers/construction_incidents")
        self.assertEqual(broken.status_code, 500)
        self.assertIn("construction_incidents.geojson does not match its contract", broken.text)
        self.write("flood_zone", {**zone_layer(), "layer": INCIDENTS["layer"]})
        self.assertEqual(self.client.get("/api/layers/flood_zone").status_code, 500, "a file must hold its own layer")

    def test_with_no_layer_files_the_labelled_sample_answers(self):
        for path in (self.root / "layers").iterdir():
            path.unlink()
        self.assertEqual(self.client.get("/api/layers").headers.get(FIXTURE_HEADER), "true")
        sample = self.client.get("/api/layers/construction_incidents?as_of=2000-01-01")
        self.assertEqual((sample.headers.get(FIXTURE_HEADER), sample.json()["features"]), ("true", []))
        self.assertEqual(self.client.get("/api/layers/flood_zone").status_code, 404)


if __name__ == "__main__":
    unittest.main()
