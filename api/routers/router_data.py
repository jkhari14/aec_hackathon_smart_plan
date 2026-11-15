"""Shared by the routers: where data/ is, a cached and contract-checked read, the input checks, and the
LoadedData / DataUnavailable pair that Python callers (the chat) get instead of an HTTP answer."""

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, Response
from pydantic import TypeAdapter, ValidationError

from api.stubs import FIXTURE_HEADER

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
_BBL = re.compile(r"[1-5][0-9]{9}", re.ASCII)  # fullmatch, so a trailing newline is refused



@dataclass(frozen=True)
class LoadedData:
    """Contract data for a Python caller, and whether it is the labelled sample rather than real data."""

    data: Any
    sample: bool


class DataUnavailable(Exception):
    """The data could not be loaded (a broken file, a failing module): an error, never to be read as empty."""

    def __init__(self, reason: str, status_code: int = 500):
        super().__init__(reason)
        self.status_code = status_code


def served(response: Response, load, *args, **kwargs):
    """Run a loader for an HTTP route: the sample header on a fixture, DataUnavailable as its HTTP error."""
    try:
        loaded = load(*args, **kwargs)
    except DataUnavailable as error:
        raise HTTPException(error.status_code, str(error)) from None
    if loaded.sample:
        response.headers[FIXTURE_HEADER] = "true"
    return loaded.data

def data_root() -> Path:
    """The repo's data/ folder (FORESITE_DATA_DIR overrides it); tests override this dependency."""
    return Path(os.environ.get("FORESITE_DATA_DIR", _DATA_ROOT))


def is_bbl(text) -> bool:
    return isinstance(text, str) and _BBL.fullmatch(text) is not None


def valid_bbl(bbl: str) -> str:
    if not is_bbl(bbl):
        raise HTTPException(422, "a BBL is 10 digits: borough 1 to 5, then block and lot")
    return bbl


def valid_as_of(text: Optional[str]) -> Optional[str]:
    """A replay date, YYYY-MM-DD; anything else is refused rather than read as "today"."""
    if text is None:
        return None
    try:
        if len(text) == 10:
            return date.fromisoformat(text).isoformat()
    except ValueError:
        pass
    raise HTTPException(422, "as_of is a date, YYYY-MM-DD")


def valid_choice(value: Optional[str], allowed: tuple, name: str) -> Optional[str]:
    """A query option from one of the contract's closed sets (checked here so the published API stays the stubs')."""
    if value is not None and value not in allowed:
        raise HTTPException(422, f"{name} must be one of: {', '.join(allowed)}")
    return value


@lru_cache(maxsize=64)
def _read(path: str, mtime_ns: int, size: int, adapter: TypeAdapter):
    return adapter.validate_python(json.loads(Path(path).read_text()))


def read_contract_file(path: Path, adapter: TypeAdapter, root: Path):
    """The file checked against its contract, re-read only when it changes. A broken file is an error, never empty."""
    name = path.relative_to(root.parent).as_posix() if path.is_relative_to(root.parent) else path.name
    try:
        stat = path.stat()
        return _read(str(path), stat.st_mtime_ns, stat.st_size, adapter)
    except ValidationError as error:
        first = ".".join(str(part) for part in error.errors()[0]["loc"])
        raise DataUnavailable(f"{name} does not match its contract ({error.error_count()} errors, first at {first})") from None
    except (OSError, ValueError) as error:
        raise DataUnavailable(f"{name} could not be read: {type(error).__name__}") from None
