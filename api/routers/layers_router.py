"""Map layers from data/layers/: the catalog, and one layer's features in a box, as of a date.

Each `<layer_id>.geojson` is a LayerFeatureCollection (its `layer` is its catalog entry). The catalog
is `catalog.json` when there is one, else the entries of the layer files. With no layer files at all,
the labelled fixtures answer, as the stubs did.
"""

import math
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import TypeAdapter

from api.contracts import LayerCatalogEntry, LayerFeature, LayerFeatureCollection
from api.routers.router_data import DataUnavailable, LoadedData, data_root, read_contract_file, served, valid_as_of
from api.stubs import fixture

MAX_FEATURES = 5000  # beyond this the answer is cut, most severe and most recent first, and marked capped
_LAYER_ID = re.compile(r"[a-z0-9_]{1,64}", re.ASCII)
_CATALOG = TypeAdapter(list[LayerCatalogEntry])
_COLLECTION = TypeAdapter(LayerFeatureCollection)

layers_router = APIRouter(prefix="/api/layers")


def _catalog(root: Path) -> Optional[list[LayerCatalogEntry]]:
    folder = root / "layers"
    if (folder / "catalog.json").is_file():
        return read_contract_file(folder / "catalog.json", _CATALOG, root)
    files = sorted(folder.glob("*.geojson"))
    return [read_contract_file(path, _COLLECTION, root).layer for path in files] or None


def _bbox(text: Optional[str]) -> Optional[tuple[float, float, float, float]]:
    if text is None:
        return None
    try:
        west, south, east, north = (float(part) for part in text.split(","))
    except ValueError:
        raise HTTPException(422, "bbox is west,south,east,north in degrees") from None
    if not all(map(math.isfinite, (west, south, east, north))) or not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise HTTPException(422, "bbox is west,south,east,north in degrees, west <= east and south <= north")
    return west, south, east, north


def _bounds(coordinates) -> Optional[tuple[float, float, float, float]]:
    """The box around a geometry's positions (a position is a list starting with two numbers)."""
    xs, ys = [], []
    stack = [coordinates]
    while stack:
        part = stack.pop()
        if not isinstance(part, list) or not part:
            continue
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in part[:2]) and len(part) >= 2:
            xs.append(part[0])
            ys.append(part[1])
        else:
            stack.extend(part)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _in_box(feature: LayerFeature, box) -> bool:
    bounds = _bounds(feature.geometry.coordinates)
    return bounds is not None and bounds[0] <= box[2] and bounds[2] >= box[0] and bounds[1] <= box[3] and bounds[3] >= box[1]


def _filtered(collection: LayerFeatureCollection, box, day: Optional[str]) -> LayerFeatureCollection:
    features = collection.features
    if day is not None:
        # An undated feature is kept only on a layer with no dates at all (a zone, not an event): on a dated
        # layer it cannot be shown to come before the as-of date.
        static = all(f.properties.date is None for f in features)
        features = [f for f in features if (f.properties.date is None and static)
                    or (f.properties.date is not None and f.properties.date[:10] <= day)]
    if box is not None:
        features = [f for f in features if _in_box(f, box)]
    if day is None and box is None and len(features) <= MAX_FEATURES:
        return collection
    status, count = collection.layer.status, len(features)
    if count > MAX_FEATURES:
        features = sorted(features, key=lambda f: (f.properties.severity, f.properties.date or ""), reverse=True)[:MAX_FEATURES]
        status = "error" if status == "error" else "capped"
    layer = collection.layer.model_copy(update={"status": status, "feature_count": count})
    return LayerFeatureCollection(type="FeatureCollection", layer=layer, features=features)


def load_layer_catalog(root: Path) -> LoadedData:
    """The catalog for a Python caller (the chat); a broken layer file is DataUnavailable."""
    catalog = _catalog(root)
    return LoadedData(_CATALOG.validate_python(fixture("layer_catalog")), True) if catalog is None else LoadedData(catalog, False)


def load_layer(layer_id: str, root: Path, bbox: Optional[str] = None, as_of: Optional[str] = None) -> LoadedData:
    """One layer, filtered. Bad input or an unknown layer is HTTPException (422, 404); a broken file is DataUnavailable."""
    if not _LAYER_ID.fullmatch(layer_id):
        raise HTTPException(404, f"no layer {layer_id!r}")
    box, day = _bbox(bbox), valid_as_of(as_of)
    path = root / "layers" / f"{layer_id}.geojson"
    if path.is_file():
        collection = read_contract_file(path, _COLLECTION, root)
        if collection.layer.layer_id != layer_id:
            raise DataUnavailable(f"data/layers/{layer_id}.geojson holds layer {collection.layer.layer_id!r}")
        return LoadedData(_filtered(collection, box, day), False)
    catalog = _catalog(root)
    if catalog is not None:
        entry = next((e for e in catalog if e.layer_id == layer_id), None)
        if entry is None:
            raise HTTPException(404, f"no layer {layer_id!r}")
        # Listed but its file is missing: an error with no count, never an empty layer that reads as zero.
        return LoadedData(LayerFeatureCollection(type="FeatureCollection", features=[], layer=entry.model_copy(
            update={"status": "error", "feature_count": None})), False)
    collection = _COLLECTION.validate_python(fixture("layer_features"))
    if collection.layer.layer_id != layer_id:
        raise HTTPException(404, f"no sample for layer {layer_id!r}")
    return LoadedData(_filtered(collection, box, day), True)


@layers_router.get("", response_model=list[LayerCatalogEntry])
def list_layers(response: Response, root: Path = Depends(data_root)):
    return served(response, load_layer_catalog, root)


@layers_router.get("/{layer_id}", response_model=LayerFeatureCollection)
def layer_features(layer_id: str, response: Response, bbox: Optional[str] = None, as_of: Optional[str] = None,
                   root: Path = Depends(data_root)):
    return served(response, load_layer, layer_id, root, bbox, as_of)
