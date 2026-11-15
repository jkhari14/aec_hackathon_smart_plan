"""The one shape every city layer is written in, and the catalog built from those files.

    data/layers/<layer_id>.geojson   a GeoJSON FeatureCollection with its catalog entry under "layer"
                                     (`LayerFeatureCollection` in api/contracts.py)
    data/layers/catalog.json         every file's "layer" entry, in one list (`LayerCatalogEntry`)

Standard library only, so a pull runs before the venv exists. tests/test_city_layers.py checks the
written files against the contracts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from checklist.record_dates import parse_record_date

LAYERS_DIR = Path(__file__).resolve().parent.parent / "data" / "layers"
CATALOG = "catalog.json"

# The same lists as Hazard and Severity in api/contracts.py; a test fails if they drift apart.
HAZARDS = ("structural", "geotech", "fire", "flood", "contamination", "facade", "weather", "construction_safety")
SEVERITIES = (0, 1, 2, 3)

BOROUGHS = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
BOROUGH_CODES = {"MN": "1", "BX": "2", "BK": "3", "QN": "4", "SI": "5",
                 **{name.upper(): code for code, name in BOROUGHS.items()}}
# A box around the five boroughs. A point outside it is a geocoding failure, not a place in the city.
_LON = (-74.30, -73.65)
_LAT = (40.45, 40.95)
_BBL = re.compile(r"^[1-5]\d{9}$")
_SUMMARY_CHARS = 300


class LayerPullError(Exception):
    """A layer's source could not be pulled, so nothing is known about it (never zero records)."""


@dataclass(frozen=True)
class LayerInfo:
    """What the layer panel says about one layer, apart from what a pull finds."""

    layer_id: str
    name: str
    description: str
    hazard: str
    source_name: str
    source_url: str
    default_on: bool


@dataclass
class Pulled:
    """One pull's result. `notes` are sentences on what was left out; they join the description."""

    features: list[dict]
    updated_at: str | None = None
    capped: bool = False
    notes: list[str] = field(default_factory=list)


def iso_date(raw: object) -> str | None:
    """A record's date as YYYY-MM-DD, or None when it cannot be read (never a guess)."""
    when = parse_record_date(raw)
    return when.isoformat() if when else None


def clean_bbl(raw: object) -> str | None:
    """'3052110074', 3052110074 or '3052110074.00000000' -> '3052110074'; anything else -> None."""
    text = str(raw if raw is not None else "").strip().split(".")[0]
    return text if _BBL.match(text) else None


def bbl_from_parts(borough: object, block: object, lot: object) -> str | None:
    """A BBL from a borough name or code, a block and a lot; None when any part is unusable."""
    boro = str(borough or "").strip().upper()
    code = boro if boro in BOROUGHS else BOROUGH_CODES.get(boro)
    block, lot = str(block or "").strip(), str(lot or "").strip()
    if not code or not block.isdigit() or not lot.isdigit() or len(block) > 5 or len(lot) > 4:
        return None
    return clean_bbl(f"{code}{block.zfill(5)}{lot.zfill(4)}")


def point(lon: object, lat: object) -> tuple[float, float] | None:
    """(lon, lat) rounded to about 10 cm, or None when missing or outside the city."""
    try:
        x, y = float(lon), float(lat)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not (_LON[0] <= x <= _LON[1] and _LAT[0] <= y <= _LAT[1]):
        return None
    return round(x, 6), round(y, 6)


def clip(text: object) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= _SUMMARY_CHARS else text[: _SUMMARY_CHARS - 1] + "…"


def count_text(value: object) -> str:
    """'17' for 17, '17.0' or '17'; '?' when the source has no number."""
    try:
        return str(int(float(str(value))))
    except (TypeError, ValueError):
        return "?"


def feature(
    info: LayerInfo,
    key: str,
    geometry: dict,
    *,
    hazard: str,
    severity: int,
    date: str | None,
    title: str,
    summary: str,
    bbl: str | None = None,
    record_id: str | None = None,
) -> dict:
    """One GeoJSON Feature in the contract's shape. `key` is unique inside the layer."""
    if hazard not in HAZARDS:
        raise ValueError(f"{info.layer_id}: {hazard!r} is not a hazard")
    if severity not in SEVERITIES:
        raise ValueError(f"{info.layer_id}: {severity!r} is not a severity")
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "id": f"{info.layer_id}:{key}",
            "layer_id": info.layer_id,
            "hazard": hazard,
            "severity": severity,
            "date": date,
            "title": title,
            "summary": clip(summary),
            "source_name": info.source_name,
            "source_url": info.source_url,
            "bbl": bbl,
            "record_id": record_id,
        },
    }


def point_geometry(lon_lat: tuple[float, float]) -> dict:
    return {"type": "Point", "coordinates": [lon_lat[0], lon_lat[1]]}


def drop_repeats(features: list[dict]) -> tuple[list[dict], int]:
    """Keep the first feature for each id; returns (features, how many repeats were dropped)."""
    seen: set[str] = set()
    kept = []
    for item in features:
        if item["properties"]["id"] not in seen:
            seen.add(item["properties"]["id"])
            kept.append(item)
    return kept, len(features) - len(kept)


def left_out(count: int, total: int, what: str, why: str) -> str | None:
    """'Not on the map: 16 of 1,511 records (no usable coordinates).', or None when nothing was left out."""
    return f"Not on the map: {count:,} of {total:,} {what} ({why})." if count else None


def collection(info: LayerInfo, pulled: Pulled, pulled_on: date) -> dict:
    """A pull's features with their catalog entry. A capped pull's count is a floor ("at least")."""
    features, repeats = drop_repeats(pulled.features)
    notes = [*pulled.notes, left_out(repeats, len(pulled.features), "rows", "each repeats another row's id")]
    description = " ".join([info.description, *[n for n in notes if n], f"Pulled {pulled_on.isoformat()}."])
    return {
        "type": "FeatureCollection",
        "layer": {
            "layer_id": info.layer_id,
            "name": info.name,
            "description": description,
            "hazard": info.hazard,
            "source_name": info.source_name,
            "source_url": info.source_url,
            "updated_at": pulled.updated_at,
            "feature_count": len(features),
            "status": "capped" if pulled.capped else "ok",
            "default_on": info.default_on,
        },
        "features": features,
    }


def error_collection(info: LayerInfo, pulled_on: date) -> dict:
    """What a failed pull writes: status "error", no count and no features. Never read it as zero."""
    return {
        "type": "FeatureCollection",
        "layer": {
            "layer_id": info.layer_id,
            "name": info.name,
            "description": f"{info.description} The pull on {pulled_on.isoformat()} failed, so nothing is known.",
            "hazard": info.hazard,
            "source_name": info.source_name,
            "source_url": info.source_url,
            "updated_at": None,
            "feature_count": None,
            "status": "error",
            "default_on": info.default_on,
        },
        "features": [],
    }


def layer_path(layer_id: str, directory: Path = LAYERS_DIR) -> Path:
    return directory / f"{layer_id}.geojson"


def write_collection(data: dict, directory: Path = LAYERS_DIR) -> Path:
    """Write one layer, a feature per line so a refresh shows up in a diff as changed records."""
    directory.mkdir(parents=True, exist_ok=True)
    path = layer_path(data["layer"]["layer_id"], directory)
    compact = {"ensure_ascii": False, "separators": (",", ":")}
    lines = ",\n".join(json.dumps(item, **compact) for item in data["features"])
    head = json.dumps({"type": data["type"], "layer": data["layer"]}, ensure_ascii=False)[:-1]
    path.write_text(f'{head}, "features": [\n{lines}\n]}}\n', encoding="utf-8")
    return path


def read_collection(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_catalog(directory: Path = LAYERS_DIR, first: tuple[str, ...] = ()) -> list[dict]:
    """Rebuild catalog.json from every layer file in the folder, whoever wrote it.

    Layers named in `first` come in that order; any other file (another module's layer) follows by id.
    """
    entries = {path.stem: read_collection(path)["layer"] for path in sorted(directory.glob("*.geojson"))}
    order = [i for i in first if i in entries] + sorted(i for i in entries if i not in first)
    catalog = [entries[i] for i in order]
    (directory / CATALOG).write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return catalog
