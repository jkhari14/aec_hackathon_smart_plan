"""Address search through NYC Planning's GeoSearch (keyless, public): the top matches that have a tax lot.

A GeoSearch failure is a 502, never an empty list: an empty list means GeoSearch answered and nothing
it found has a BBL. The label is GeoSearch's, so the UI shows what was matched, not what was typed.
"""

import http.client
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException

from api.contracts import SearchResult
from api.routers.router_data import is_bbl
from data_pull.address_lookup import GEOSEARCH_URL
from data_pull.soda_client import is_placeholder_bin

MAX_RESULTS = 5
MAX_QUERY = 200
_TIMEOUT_SECONDS = 10

search_router = APIRouter(prefix="/api/search")


def _geosearch(text: str) -> dict:
    url = f"{GEOSEARCH_URL}?{urllib.parse.urlencode({'text': text, 'size': str(MAX_RESULTS)})}"
    with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as answer:
        return json.load(answer)


def geosearch_fetcher() -> Callable[[str], dict]:
    """The live call; tests override this dependency so no test reaches GeoSearch."""
    return _geosearch


def _dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _result(feature) -> Optional[SearchResult]:
    """One GeoSearch match, or None when it has no tax lot, label or point (never a made-up one)."""
    properties = _dict(_dict(feature).get("properties"))
    pad = _dict(_dict(properties.get("addendum")).get("pad"))
    coordinates = _dict(_dict(feature).get("geometry")).get("coordinates")
    bbl, bin_number, label = str(pad.get("bbl", "")), str(pad.get("bin", "")), properties.get("label")
    if not is_bbl(bbl) or not isinstance(label, str) or not label.strip():
        return None
    if not (isinstance(coordinates, list) and len(coordinates) >= 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in coordinates[:2])):
        return None
    real_bin = len(bin_number) == 7 and bin_number.isascii() and bin_number.isdigit() and bin_number[0] in "12345" \
        and not is_placeholder_bin(bin_number)
    return SearchResult(label=label.strip(), bbl=bbl, bin=bin_number if real_bin else None,
                        lon=coordinates[0], lat=coordinates[1])


@search_router.get("", response_model=list[SearchResult])
def search(q: str, fetch: Callable[[str], dict] = Depends(geosearch_fetcher)):
    if not q.strip() or len(q) > MAX_QUERY:
        raise HTTPException(422, f"type an address, up to {MAX_QUERY} characters")
    try:
        payload = fetch(q.strip())
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError, ValueError):
        raise HTTPException(502, "NYC Planning GeoSearch did not answer; the search was not run") from None
    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list):
        raise HTTPException(502, "NYC Planning GeoSearch answered in a shape this search does not read")
    return [result for result in map(_result, features[:MAX_RESULTS]) if result is not None]
