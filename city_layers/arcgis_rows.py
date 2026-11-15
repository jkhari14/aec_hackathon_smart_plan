"""Read-only queries against an ArcGIS REST layer (FEMA's flood map), standard library only.

The same promises as the Open Data reads: every page or an error, one retry, and a failed query is
a LayerPullError, never an empty answer.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from city_layers.layer_file import LayerPullError

PAGE_FEATURES = 200
MAX_FEATURES = 20_000
_TIMEOUT_SECONDS = 90


def _get(url: str, params: dict[str, str]) -> dict:
    full = f"{url}?{urllib.parse.urlencode(params)}"
    last_error = "no attempt made"
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(full, timeout=_TIMEOUT_SECONDS) as response:
                answer = json.load(response)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            last_error = f"{type(error).__name__}: {error}"
            if attempt == 1:
                time.sleep(2)
            continue
        # ArcGIS reports a failed query inside a 200 answer.
        if not isinstance(answer, dict) or "error" in answer:
            last_error = f"service error: {json.dumps(answer.get('error') if isinstance(answer, dict) else answer)[:200]}"
            break
        return answer
    raise LayerPullError(f"{url}: {last_error}")


def all_features(layer_url: str, where: str, fields: str, simplify_degrees: float, decimals: int,
                 max_features: int = MAX_FEATURES) -> tuple[list[dict], bool]:
    """Every GeoJSON feature matching `where`, a page at a time, in WGS84: (features, capped)."""
    features: list[dict] = []
    while len(features) < max_features:
        answer = _get(f"{layer_url}/query", {
            "where": where, "outFields": fields, "outSR": "4326", "f": "geojson", "orderByFields": "OBJECTID",
            "maxAllowableOffset": str(simplify_degrees), "geometryPrecision": str(decimals),
            "resultOffset": str(len(features)), "resultRecordCount": str(min(PAGE_FEATURES, max_features - len(features))),
        })
        page = answer.get("features")
        if not isinstance(page, list):
            raise LayerPullError(f"{layer_url}: the answer has no feature list")
        features.extend(page)
        more = answer.get("exceededTransferLimit") or (answer.get("properties") or {}).get("exceededTransferLimit")
        if not page or not more:
            return features, False
    return features, True


def attributes_at(layer_url: str, lon: float, lat: float, fields: str) -> list[dict]:
    """The attributes of every feature of the layer that contains the point (WGS84)."""
    answer = _get(f"{layer_url}/query", {
        "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "outFields": fields, "returnGeometry": "false", "f": "json",
    })
    found = answer.get("features")
    if not isinstance(found, list):
        raise LayerPullError(f"{layer_url}: the answer has no feature list")
    return [item.get("attributes") or {} for item in found]
