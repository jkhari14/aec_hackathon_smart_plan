"""A site's public record for the rules: a cached pull in data/cache/ if there is one, else a live pull.

The demo sites are cached (data_pull writes data/cache/<slug>.json), so the demo never waits on the city's
servers. A live pull takes about 5 seconds and is kept in memory for the life of the process.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from data_pull import soda_client
from data_pull.site_brief_pull import CACHE_DIR, pull_site
from early_warning.records import SitePull, from_pull


class SiteUnavailable(Exception):
    """The site's record couldn't be loaded at all."""


@lru_cache(maxsize=1)
def _cache_index(cache_dir: Path, stamp: tuple) -> dict[str, Path]:
    index = {}
    for path in sorted(cache_dir.glob("*.json")):
        try:
            index[json.loads(path.read_text())["site_bbl"]] = path
        except (OSError, ValueError, KeyError):
            continue
    return index


def cached_path(bbl: str, cache_dir: Path = CACHE_DIR) -> Path | None:
    files = sorted(cache_dir.glob("*.json"))
    stamp = tuple((p.name, p.stat().st_mtime_ns) for p in files)
    return _cache_index(cache_dir, stamp).get(bbl)


@lru_cache(maxsize=64)
def _live(bbl: str) -> dict:
    return pull_site(bbl=bbl)


def load_site(bbl: str, cache_dir: Path = CACHE_DIR, live: bool = True) -> SitePull:
    soda_client.validate_bbl(bbl)
    path = cached_path(bbl, cache_dir)
    if path is not None:
        return from_pull(json.loads(path.read_text()))
    if not live:
        raise SiteUnavailable(f"no cached pull for {bbl}")
    try:
        return from_pull(_live(bbl))
    except (soda_client.SodaQueryError, OSError, ValueError, KeyError) as error:
        raise SiteUnavailable(f"the public record for {bbl} couldn't load: {error}") from error
