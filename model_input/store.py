"""Which structural model belongs to which project and site, for this API process.

Jahleel's project store (PR 4) persists projects. Until it does, the latest model per project and per site
lives here in memory, and the site profile, similar cases and pattern score read it from here.
"""

from __future__ import annotations

from threading import Lock
from typing import Optional

_by_project: dict[str, dict] = {}
_by_site: dict[str, dict] = {}
_lock = Lock()


def save(project_id: str, site_bbl: Optional[str], model: dict) -> None:
    with _lock:
        _by_project[project_id] = model
        if site_bbl:
            _by_site[site_bbl] = model


def for_project(project_id: str) -> Optional[dict]:
    with _lock:
        return _by_project.get(project_id)


def for_site(bbl: str) -> Optional[dict]:
    with _lock:
        return _by_site.get(bbl)


def clear() -> None:
    with _lock:
        _by_project.clear()
        _by_site.clear()
