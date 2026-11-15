"""The 3D model of the blocks around a site, from Cityweft (https://cityweft.com), for the map's close-up.

    GET /api/context3d?lat=40.6&lon=-73.9&radius_m=250

The browser never sees the Cityweft key: this route calls `POST https://api.cityweft.com/v1/context`
with `CITYWEFT_API_KEY` from the environment, merges every building mesh into one, and answers a small
binary file the map draws with deck.gl:

    uint32 LE  header length in bytes
    header     UTF-8 JSON: vertex_count, index_count, building_count, buildings (one [first vertex,
               vertex count, height in metres] per building, for colouring), origin, radius_m,
               attributions, fetched_at, source; padded with spaces to a multiple of 4 bytes
    float32[]  positions, vertex_count * 3: metres east, north and up from (lat, lon)
    uint32[]   triangle indices, index_count

Answers are cached in data/cache/cityweft/ (git-ignored) so a site costs Cityweft area only once.
No key is a 503 and a Cityweft failure is a 502, never an empty model.

Cityweft's docs say local x is east, but checked against the map's own building outlines (2026-11-14,
Empire State Building area) its vertices with `upAxis: "Z"` are (north, east, up): read as-is the model
came out mirrored across the diagonal; swapped, 100% of building corners land on mapped footprints.
So the default reading is "y,x,z" (east = y, north = x, up = z). If Cityweft changes this, set
CITYWEFT_AXES to the right reading, e.g. "x,y,z"; the cache is keyed by it, so nothing stale is served.

Not in the API contract (it isn't JSON): `include_in_schema=False`.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from api.routers.router_data import data_root

CITYWEFT_URL = "https://api.cityweft.com/v1/context"
MEDIA_TYPE = "application/vnd.foresite.mesh"
TIMEOUT_S = 90
DEFAULT_AXES = "y,x,z"  # Cityweft sends (north, east, up); see the module docstring
CACHE_VERSION = "2"  # bump when the packed format changes, so old cached models are fetched again
_AXIS = {"x": 0, "y": 1, "z": 2}

context3d_router = APIRouter(prefix="/api/context3d")


def square_polygon(lat: float, lon: float, radius_m: float) -> list[list[float]]:
    """A closed square of side 2 * radius_m centred on the site, as Cityweft's [lat, lon] pairs."""
    dlat = radius_m / 110_540
    dlon = radius_m / (111_320 * math.cos(math.radians(lat)))
    corners = [(lat - dlat, lon - dlon), (lat - dlat, lon + dlon), (lat + dlat, lon + dlon), (lat + dlat, lon - dlon)]
    ring = [[round(a, 7), round(b, 7)] for a, b in corners]
    return ring + [ring[0]]


def request_body(lat: float, lon: float, radius_m: float) -> dict:
    return {
        "polygon": square_polygon(lat, lon, radius_m),
        "origin": [lat, lon],
        "settings": {"geometry": ["buildings"], "crs": "local", "upAxis": "Z", "indexedMeshes": True},
    }


def parse_axes(text: str) -> list[tuple[int, float]]:
    """"x,y,z" -> which vertex component (and sign) is east, north and up."""
    parts = [p.strip().lower() for p in text.split(",")]
    axes = []
    for p in parts:
        sign = -1.0 if p.startswith("-") else 1.0
        name = p.lstrip("+-")
        if name not in _AXIS:
            raise ValueError(f"CITYWEFT_AXES must be three of x, y, z with optional signs, got {text!r}")
        axes.append((_AXIS[name], sign))
    if len(axes) != 3 or len({a for a, _ in axes}) != 3:
        raise ValueError(f"CITYWEFT_AXES must name x, y and z once each, got {text!r}")
    return axes


def merge_buildings(answer: dict, axes: list[tuple[int, float]]) -> tuple[list[float], list[int], list[list[float]]]:
    """Every building mesh in a Cityweft answer as one indexed mesh in (east, north, up) metres, and each
    building's [first vertex, vertex count, height]: Cityweft's buildingHeight, else its highest vertex."""
    positions: list[float] = []
    indices: list[int] = []
    buildings: list[list[float]] = []
    for group in answer.get("geometry") or []:
        if group.get("type") != "buildings":
            continue
        for mesh in group.get("meshes") or []:
            vertices = mesh.get("vertices") or []
            count = len(vertices) // 3
            if count == 0:
                continue
            base = len(positions) // 3
            for i in range(count):
                v = vertices[3 * i: 3 * i + 3]
                positions.extend(sign * float(v[axis]) for axis, sign in axes)
            mesh_indices = mesh.get("indices")
            # Without indexedMeshes the answer is triangle soup: every three vertices are one triangle.
            local = mesh_indices if mesh_indices else range(count - count % 3)
            indices.extend(base + int(i) for i in local)
            height = (mesh.get("descriptor") or {}).get("buildingHeight")
            if not isinstance(height, (int, float)) or height <= 0:
                height = max(positions[3 * base + 2::3])
            buildings.append([base, count, round(float(height), 1)])
    return positions, indices, buildings


def pack(header: dict, positions: list[float], indices: list[int]) -> bytes:
    text = json.dumps(header, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 4)
    return (
        struct.pack("<I", len(text)) + text
        + struct.pack(f"<{len(positions)}f", *positions)
        + struct.pack(f"<{len(indices)}I", *indices)
    )


def call_cityweft(key: str, body: dict) -> dict:
    request = urllib.request.Request(
        CITYWEFT_URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as reply:
            return json.load(reply)
    except urllib.error.HTTPError as error:
        reasons = {401: "the Cityweft key was refused", 402: "the Cityweft account has no subscription or balance",
                   400: "Cityweft rejected the area", 503: "Cityweft is busy; try again shortly"}
        raise HTTPException(502, f"{reasons.get(error.code, 'Cityweft failed')} (HTTP {error.code})") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(502, f"Cityweft could not be reached: {error}") from error


def cityweft_caller() -> Callable[[str, dict], dict]:
    """The Cityweft call; tests override this dependency."""
    return call_cityweft


@context3d_router.get("", include_in_schema=False)
def context3d(
    lat: float = Query(..., ge=40.4, le=41.0),
    lon: float = Query(..., ge=-74.3, le=-73.6),
    radius_m: int = Query(250, ge=50, le=800),
    root: Path = Depends(data_root),
    call: Callable[[str, dict], dict] = Depends(cityweft_caller),
) -> Response:
    lat, lon = round(lat, 6), round(lon, 6)
    axes_text = os.environ.get("CITYWEFT_AXES", DEFAULT_AXES)
    try:
        axes = parse_axes(axes_text)
    except ValueError as error:
        raise HTTPException(500, str(error)) from error

    name = hashlib.sha1(f"{CACHE_VERSION},{lat},{lon},{radius_m},{axes_text}".encode()).hexdigest()[:16]
    cached = root / "cache" / "cityweft" / f"{name}.mesh"
    if cached.is_file():
        return Response(cached.read_bytes(), media_type=MEDIA_TYPE)

    key: Optional[str] = os.environ.get("CITYWEFT_API_KEY")
    if not key:
        raise HTTPException(503, "the 3D site model needs CITYWEFT_API_KEY in the API's environment")

    answer = call(key, request_body(lat, lon, radius_m))
    positions, indices, buildings = merge_buildings(answer, axes)
    if not buildings:
        raise HTTPException(502, "Cityweft answered with no buildings for this area")
    header = {
        "vertex_count": len(positions) // 3,
        "index_count": len(indices),
        "building_count": len(buildings),
        "buildings": buildings,
        "origin": [lat, lon],
        "radius_m": radius_m,
        "attributions": [str(a.get("name", a)) if isinstance(a, dict) else str(a) for a in answer.get("attributions") or []],
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Cityweft",
    }
    data = pack(header, positions, indices)
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return Response(data, media_type=MEDIA_TYPE)
