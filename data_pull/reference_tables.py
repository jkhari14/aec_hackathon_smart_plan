"""Code tables DOB publishes on Open Data, pulled once per site so a record's codes can be read.

Rows are kept as printed. Some dispositions end in a stray letter ("FULL STOP WORK ORDER SERVED F");
that is the table's own text, so it is not trimmed here.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from data_pull import soda_client

DISPOSITION_CODES = "6v9u-ndjg"
_VIEWS = "https://data.cityofnewyork.us/api/views"


def _rows_updated_at(dataset_id: str) -> str | None:
    """The date Open Data says the table's rows last changed, or None when that can't be read."""
    try:
        with urllib.request.urlopen(f"{_VIEWS}/{dataset_id}.json", timeout=30) as response:
            stamp = json.load(response).get("rowsUpdatedAt")
        return datetime.fromtimestamp(int(stamp), timezone.utc).date().isoformat()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError):
        return None


def pull_disposition_codes() -> dict:
    try:
        rows, url = soda_client.query(DISPOSITION_CODES, {"select": "code,disposition", "order": "code"})
    except soda_client.SodaQueryError as error:
        return {"status": "error", "dataset_id": DISPOSITION_CODES, "error": str(error), "records": []}
    return {"status": "ok", "dataset_id": DISPOSITION_CODES, "name": "DOB complaint disposition codes",
            "rows_updated_at": _rows_updated_at(DISPOSITION_CODES), "count": len(rows),
            "truncated": len(rows) >= soda_client.ROW_LIMIT, "query_url": url, "records": rows}
