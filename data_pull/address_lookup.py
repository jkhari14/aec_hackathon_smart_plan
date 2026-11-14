"""Address -> BBL and BIN through NYC Planning's GeoSearch (keyless, public)."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from data_pull.soda_client import is_placeholder_bin, validate_bbl, validate_bin

GEOSEARCH_URL = "https://geosearch.planninglabs.nyc/v2/search"
_TIMEOUT_SECONDS = 20


class AddressLookupError(Exception):
    """GeoSearch found no usable match for the address."""


def lookup_address(address: str) -> dict:
    """Top GeoSearch match for an address. Keep `matched_label`: GeoSearch matches fuzzily,
    so the UI should show what was actually found, not what was typed."""
    url = f"{GEOSEARCH_URL}?{urllib.parse.urlencode({'text': address, 'size': '1'})}"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise AddressLookupError(f"GeoSearch request failed: {error}") from error

    features = payload.get("features") if isinstance(payload, dict) else None
    if not isinstance(features, list) or not features:
        raise AddressLookupError(f"no GeoSearch match for {address!r}")
    feature = features[0]
    properties = feature.get("properties") or {}
    pad = (properties.get("addendum") or {}).get("pad") or {}
    coordinates = (feature.get("geometry") or {}).get("coordinates") or [None, None]

    try:
        bbl = validate_bbl(str(pad.get("bbl", "")))
    except ValueError as error:
        raise AddressLookupError(f"GeoSearch match has no valid BBL: {error}") from error
    bin_number = str(pad.get("bin", ""))
    try:
        validate_bin(bin_number)
        if is_placeholder_bin(bin_number):
            bin_number = None
    except ValueError:
        bin_number = None

    return {
        "input": address,
        "matched_label": properties.get("label"),
        "bbl": bbl,
        "bin": bin_number,
        "longitude": coordinates[0],
        "latitude": coordinates[1],
        "source": "NYC Planning GeoSearch",
        "pad_version": pad.get("version"),
    }
