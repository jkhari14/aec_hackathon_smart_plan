"""Read-only queries against NYC Open Data (Socrata SODA), standard library only.

Every value placed in a SoQL `$where` passes a digits-only check first, so an address or a
record from another system can never inject query text.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

SODA_BASE = "https://data.cityofnewyork.us/resource"
ROW_LIMIT = 5000
_TIMEOUT_SECONDS = 30
_RETRY_STATUSES = {429, 500, 502, 503, 504}
_BBL = re.compile(r"^[1-5]\d{9}$")
_BIN = re.compile(r"^[1-5]\d{6}$")
_DIGITS = re.compile(r"^\d+$")


class SodaQueryError(Exception):
    """A dataset query failed (network, HTTP status, or an unexpected response shape)."""


def validate_bbl(bbl: str) -> str:
    if not isinstance(bbl, str) or not _BBL.match(bbl):
        raise ValueError(f"not a 10-digit BBL: {bbl!r}")
    return bbl


def validate_bin(bin_number: str) -> str:
    if not isinstance(bin_number, str) or not _BIN.match(bin_number):
        raise ValueError(f"not a 7-digit BIN: {bin_number!r}")
    return bin_number


def is_placeholder_bin(bin_number: str) -> bool:
    """BINs like 3000000 are NYC's "no building" placeholder, shared by thousands of lots."""
    return bin_number[1:] == "000000"


def split_bbl(bbl: str) -> tuple[str, str, str]:
    """BBL -> (borough digit, 5-digit block, 4-digit lot)."""
    validate_bbl(bbl)
    return bbl[0], bbl[1:6], bbl[6:]


def block_variants(block: str) -> list[str]:
    """Blocks are stored both zero-padded ("05211") and bare ("5211")."""
    return sorted({block.zfill(5), block.lstrip("0") or "0"})


def lot_variants(lot: str) -> list[str]:
    """DOB violations store lots in three widths ("00073", "0073", "73"); query all of them."""
    return sorted({lot.zfill(5), lot.zfill(4), lot.lstrip("0") or "0"})


def soql_in(values: list[str]) -> str:
    """('a','b') for a SoQL IN clause. Digits only, so nothing can break out of the quotes."""
    if not values:
        raise ValueError("an IN list needs at least one value")
    for value in values:
        if not _DIGITS.match(value):
            raise ValueError(f"refusing non-digit value in a query: {value!r}")
    return "(" + ",".join(f"'{value}'" for value in values) + ")"


def build_url(dataset_id: str, params: dict[str, str]) -> str:
    query = urllib.parse.urlencode({f"${key}": value for key, value in params.items()})
    return f"{SODA_BASE}/{dataset_id}.json?{query}"


def query(dataset_id: str, params: dict[str, str]) -> tuple[list[dict], str]:
    """Run one query; returns (rows, url). One retry on throttling, 5xx or a network error."""
    params = {"limit": str(ROW_LIMIT), **params}
    url = build_url(dataset_id, params)
    headers = {"Accept": "application/json"}
    token = os.environ.get("SODA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token
    last_error = "no attempt made"
    for attempt in (1, 2):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                rows = json.load(response)
        except urllib.error.HTTPError as error:
            last_error = f"HTTP {error.code}"
            if error.code in _RETRY_STATUSES and attempt == 1:
                time.sleep(2)
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = f"network error: {error}"
            if attempt == 1:
                time.sleep(2)
                continue
            break
        except json.JSONDecodeError:
            last_error = "response was not JSON"
            break
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            last_error = "response was not a list of records"
            break
        return rows, url
    raise SodaQueryError(f"{dataset_id}: {last_error}")
