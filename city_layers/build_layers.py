"""Pull the city layers and write them to data/layers/.

    python3 -m city_layers.build_layers                       # every layer
    python3 -m city_layers.build_layers sandy_inundation      # only the named ones
    python3 -m city_layers.build_layers --catalog             # no pull: rebuild catalog.json from the files
    python3 -m city_layers.build_layers --list

Each layer is written whole or not at all. When a pull fails:
- a layer with an earlier good file keeps it, with a sentence in its description saying the refresh failed;
- a layer with no earlier file gets an entry with status "error" and no features.
Either way a failed pull is never written as zero records, and the run exits 1.
catalog.json is then rebuilt from every layer file in the folder, including other modules' layers.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from city_layers import (
    construction_incidents, e_designations, fdny_vacates, sandy_inundation, structural_complaints,
    unsafe_facades, vacate_orders,
)
from city_layers.layer_file import (
    LAYERS_DIR, LayerPullError, collection, error_collection, layer_path, read_collection, write_catalog,
    write_collection,
)

# In the order the layer panel lists them.
MODULES = (
    construction_incidents, structural_complaints, vacate_orders, fdny_vacates, unsafe_facades,
    sandy_inundation, e_designations,
)
LAYERS = {module.INFO.layer_id: module for module in MODULES}
_REFRESH_FAILED = " A refresh on "


def _keep_last_good(path: Path, pulled_on: date, directory: Path) -> bool:
    """Mark an earlier good file as not refreshed; False when there is none to keep."""
    if not path.exists():
        return False
    previous = read_collection(path)
    if previous["layer"]["status"] == "error":
        return False
    description = previous["layer"]["description"].split(_REFRESH_FAILED)[0]
    previous["layer"]["description"] = f"{description}{_REFRESH_FAILED}{pulled_on.isoformat()} failed, so this is the earlier pull."
    write_collection(previous, directory)
    return True


def build(layer_ids: list[str], directory: Path = LAYERS_DIR, pulled_on: date | None = None) -> dict[str, str]:
    """Pull and write each named layer; returns layer_id -> "ok", "capped", "kept" or "error"."""
    pulled_on = pulled_on or date.today()
    outcomes: dict[str, str] = {}
    for layer_id in layer_ids:
        module = LAYERS[layer_id]
        try:
            pulled = module.pull(pulled_on)
        except Exception as error:  # noqa: BLE001 - one layer's failure must not stop the others
            reason = str(error) if isinstance(error, LayerPullError) else f"{type(error).__name__}: {error}"
            if _keep_last_good(layer_path(layer_id, directory), pulled_on, directory):
                outcomes[layer_id] = "kept"
                print(f"{layer_id}: pull failed ({reason}); kept the earlier file", file=sys.stderr)
            else:
                write_collection(error_collection(module.INFO, pulled_on), directory)
                outcomes[layer_id] = "error"
                print(f"{layer_id}: pull failed ({reason}); wrote status error", file=sys.stderr)
            continue
        data = collection(module.INFO, pulled, pulled_on)
        path = write_collection(data, directory)
        outcomes[layer_id] = data["layer"]["status"]
        count = data["layer"]["feature_count"]
        size = path.stat().st_size / 1_000_000
        print(f"{layer_id}: {'at least ' if pulled.capped else ''}{count:,} features, {size:.1f} MB, "
              f"source updated {data['layer']['updated_at'] or 'unknown'}")
    write_catalog(directory, first=tuple(LAYERS))
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("layers", nargs="*", help="layer ids; every layer when none is named")
    parser.add_argument("--list", action="store_true", help="print the layer ids and stop")
    parser.add_argument("--catalog", action="store_true", help="rebuild catalog.json from the layer files, without pulling")
    args = parser.parse_args()
    if args.list:
        for layer_id, module in LAYERS.items():
            print(f"{layer_id}: {module.INFO.source_name} ({module.INFO.source_url})")
        return 0
    if args.catalog:
        for entry in write_catalog(LAYERS_DIR, first=tuple(LAYERS)):
            print(f"{entry['layer_id']}: {entry['status']}")
        return 0
    unknown = [name for name in args.layers if name not in LAYERS]
    if unknown:
        print(f"not a layer: {', '.join(unknown)}. Layers: {', '.join(LAYERS)}", file=sys.stderr)
        return 2
    outcomes = build(args.layers or list(LAYERS))
    return 1 if any(outcome in ("kept", "error") for outcome in outcomes.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
