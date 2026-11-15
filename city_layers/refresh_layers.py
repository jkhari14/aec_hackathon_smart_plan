"""Refresh the city layers on a schedule, and keep a short log of how each refresh went.

    python3 -m city_layers.refresh_layers             # refresh every layer once
    python3 -m city_layers.refresh_layers --every 6   # then again every 6 hours, until stopped

Or from cron, daily at 5 am:   0 5 * * *  cd <repo> && python3 -m city_layers.refresh_layers

A refresh is build_layers' pull: a layer whose source fails keeps its last good file, so a bad
morning at one source never empties the map. data/layers/refresh_log.json holds the last runs.
It only rewrites files; committing or deploying them is a separate step.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from city_layers import build_layers
from city_layers.layer_file import LAYERS_DIR

LOG = "refresh_log.json"
RUNS_KEPT = 20


def refresh(directory: Path = LAYERS_DIR, now: datetime | None = None) -> dict:
    """Pull every layer and add the run to the log; returns the run's entry."""
    started = now or datetime.now().astimezone()
    outcomes = build_layers.build(list(build_layers.LAYERS), directory, started.date())
    run = {"started": started.isoformat(timespec="seconds"), "outcomes": outcomes,
           "failed": sorted(layer for layer, outcome in outcomes.items() if outcome in ("kept", "error"))}
    path = directory / LOG
    try:
        runs = json.loads(path.read_text(encoding="utf-8"))["runs"]
    except (OSError, ValueError, KeyError, TypeError):
        runs = []
    path.write_text(json.dumps({"runs": [run, *runs][:RUNS_KEPT]}, indent=2) + "\n", encoding="utf-8")
    return run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--every", type=float, metavar="HOURS", help="keep refreshing at this interval")
    args = parser.parse_args()
    if args.every is not None and args.every <= 0:
        parser.error("--every needs a positive number of hours")
    while True:
        run = refresh()
        print(f"refresh {run['started']}: " + (f"failed for {', '.join(run['failed'])}" if run["failed"] else "every layer refreshed"),
              flush=True)
        if args.every is None:
            return 1 if run["failed"] else 0
        time.sleep(args.every * 3600)


if __name__ == "__main__":
    sys.exit(main())
