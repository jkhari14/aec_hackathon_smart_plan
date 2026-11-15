"""Whole-dataset reads from NYC Open Data for the city layers, on data_pull's SODA client.

data_pull asks about one lot at a time. A city layer needs every row of a query, so this pages
through it, and it turns the ids a source does carry (BBL, BIN) into a point on the map for the
sources that publish no coordinates.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterable
from datetime import datetime, timezone

from city_layers.layer_file import LayerPullError, clean_bbl, point
from data_pull import soda_client

PAGE_ROWS = 10_000
MAX_ROWS = 200_000
LOOKUP_BATCH = 300
PLUTO = "64uk-42ks"
BUILDING_FOOTPRINTS = "5zhs-2jue"
TAX_LOT_POLYGONS = "i38t-6if2"
_VIEWS = "https://data.cityofnewyork.us/api/views"


def all_rows(dataset_id: str, params: dict[str, str], max_rows: int = MAX_ROWS) -> tuple[list[dict], bool]:
    """Every row of one query, a page at a time: (rows, capped).

    `capped` is True when `max_rows` were read and the source may hold more, so the count is a floor.
    A failed page fails the whole read: part of a dataset is never passed off as all of it.
    """
    params = {"order": ":id", **params}
    rows: list[dict] = []
    while len(rows) < max_rows:
        size = min(PAGE_ROWS, max_rows - len(rows))
        try:
            page, _ = soda_client.query(dataset_id, {**params, "limit": str(size), "offset": str(len(rows))})
        except soda_client.SodaQueryError as error:
            raise LayerPullError(str(error)) from error
        rows.extend(page)
        if len(page) < size:
            return rows, False
    return rows, True


def count_rows(dataset_id: str, where: str | None = None) -> int:
    params = {"select": "count(*) as n", **({"where": where} if where else {})}
    try:
        rows, _ = soda_client.query(dataset_id, params)
        return int(rows[0]["n"])
    except (soda_client.SodaQueryError, LookupError, TypeError, ValueError) as error:
        raise LayerPullError(f"{dataset_id}: could not count rows ({error})") from error


def rows_updated_at(dataset_id: str) -> str | None:
    """The date Open Data says the dataset's rows last changed; None when that cannot be read."""
    try:
        with urllib.request.urlopen(f"{_VIEWS}/{dataset_id}.json", timeout=30) as response:
            stamp = json.load(response).get("rowsUpdatedAt")
        return datetime.fromtimestamp(int(stamp), timezone.utc).date().isoformat()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, TypeError, AttributeError):
        return None


def _batches(values: Iterable[str]) -> Iterable[list[str]]:
    unique = sorted(set(values))
    for start in range(0, len(unique), LOOKUP_BATCH):
        yield unique[start : start + LOOKUP_BATCH]


def _number_list(values: list[str]) -> str:
    """(1,2,3) for a SoQL IN on a number column. Digits only, so nothing else reaches the query."""
    for value in values:
        if not value.isdigit():
            raise ValueError(f"refusing non-digit value in a query: {value!r}")
    return "(" + ",".join(values) + ")"


def usable_bin(raw: object) -> str | None:
    """A 7-digit BIN as text, or None for a missing, malformed or placeholder one (never join on those)."""
    text = str(raw or "").strip().split(".")[0]
    try:
        return None if soda_client.is_placeholder_bin(soda_client.validate_bin(text)) else text
    except ValueError:
        return None


def _pluto_points(bbls: list[str]) -> dict[str, tuple[float, float]]:
    found: dict[str, tuple[float, float]] = {}
    for batch in _batches(bbls):
        try:
            rows, _ = soda_client.query(
                PLUTO, {"select": "bbl,latitude,longitude", "where": f"bbl in {_number_list(batch)}"}
            )
        except soda_client.SodaQueryError as error:
            raise LayerPullError(str(error)) from error
        for row in rows:
            bbl, lon_lat = clean_bbl(row.get("bbl")), point(row.get("longitude"), row.get("latitude"))
            if bbl and lon_lat:
                found[bbl] = lon_lat
    return found


def polygon_middle(geometry: dict | None) -> tuple[float, float] | None:
    """The centroid of a Polygon's or MultiPolygon's largest outer ring, as a point in the city."""
    if not geometry or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        return None
    polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
    best: tuple[float, float, float] | None = None
    for polygon in polygons:
        ring = polygon[0] if polygon else []
        if len(ring) < 4:
            continue
        # Measured from the first corner, so the sums stay small and exact enough in degrees.
        x0, y0 = float(ring[0][0]), float(ring[0][1])
        area = cx = cy = 0.0
        for (xa, ya, *_), (xb, yb, *_) in zip(ring, ring[1:]):
            xa, ya, xb, yb = float(xa) - x0, float(ya) - y0, float(xb) - x0, float(yb) - y0
            cross = xa * yb - xb * ya
            area += cross
            cx += (xa + xb) * cross
            cy += (ya + yb) * cross
        if area and (best is None or abs(area) > best[0]):
            best = (abs(area), x0 + cx / (3 * area), y0 + cy / (3 * area))
    return point(best[1], best[2]) if best else None


def _tax_map_points(bbls: list[str]) -> dict[str, tuple[float, float]]:
    found: dict[str, tuple[float, float]] = {}
    for batch in _batches(bbls):
        try:
            rows, _ = soda_client.query(
                TAX_LOT_POLYGONS, {"select": "bbl,the_geom", "where": f"bbl in {soda_client.soql_in(batch)}"}
            )
        except soda_client.SodaQueryError as error:
            raise LayerPullError(str(error)) from error
        for row in rows:
            bbl, lon_lat = clean_bbl(row.get("bbl")), polygon_middle(row.get("the_geom"))
            if bbl and lon_lat:
                found.setdefault(bbl, lon_lat)
    return found


def lot_points(bbls: Iterable[str]) -> dict[str, tuple[float, float]]:
    """BBL -> (lon, lat): PLUTO's point for the lot, else the middle of its polygon on the tax map.

    PLUTO lists a condo under its billing lot, so the lot a record names (the condo's base lot) can
    be on the tax map and not in PLUTO. A lot in neither is absent from the answer, not guessed.
    """
    wanted = sorted({soda_client.validate_bbl(b) for b in bbls})
    found = _pluto_points(wanted)
    found.update(_tax_map_points([b for b in wanted if b not in found]))
    return found


def building_lots(bins: Iterable[str]) -> dict[str, str]:
    """BIN -> BBL from Building Footprints.

    Left out, never guessed: placeholder BINs ("3000000", shared by thousands of lots), BINs with no
    footprint, and BINs whose footprints sit on more than one lot.
    """
    wanted = [b for b in (usable_bin(raw) for raw in bins) if b]
    lots: dict[str, set[str]] = {}
    for batch in _batches(wanted):
        try:
            rows, _ = soda_client.query(
                BUILDING_FOOTPRINTS,
                {"select": "bin,mappluto_bbl,base_bbl", "where": f"bin in {_number_list(batch)}"},
            )
        except soda_client.SodaQueryError as error:
            raise LayerPullError(str(error)) from error
        for row in rows:
            bin_number = str(row.get("bin") or "").split(".")[0]
            bbl = clean_bbl(row.get("mappluto_bbl")) or clean_bbl(row.get("base_bbl"))
            if bin_number and bbl:
                lots.setdefault(bin_number, set()).add(bbl)
    return {bin_number: next(iter(found)) for bin_number, found in lots.items() if len(found) == 1}
