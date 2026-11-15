"""Daily weather at a site from the Open-Meteo archive (keyless), cached on disk for the demo.

A day the archive has no value for stays None: it is reported as "no data", never as a dry or mild day.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
SOURCE_NAME = "Open-Meteo historical weather"
CACHE_DIR = Path(__file__).resolve().parent / "weather_cache"
_TIMEOUT_SECONDS = 20


class WeatherError(Exception):
    """The archive could not be reached or answered in an unexpected shape."""


@dataclass(frozen=True)
class Day:
    day: date
    precipitation_mm: float | None
    max_c: float | None
    min_c: float | None


@dataclass(frozen=True)
class Weather:
    days: list[Day]
    url: str


def archive_url(lat: float, lon: float, start: date, end: date) -> str:
    query = urllib.parse.urlencode({
        "latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}",
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "America/New_York",
    })
    return f"{ARCHIVE_URL}?{query}"


def _parse(payload: dict, url: str) -> Weather:
    try:
        daily = payload["daily"]
        rows = zip(daily["time"], daily["precipitation_sum"], daily["temperature_2m_max"], daily["temperature_2m_min"])
        return Weather([Day(date.fromisoformat(t), p, hi, lo) for t, p, hi, lo in rows], url)
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherError(f"unexpected answer from Open-Meteo: {error}") from error


def daily_weather(lat: float, lon: float, start: date, end: date, cache_dir: Path = CACHE_DIR) -> Weather:
    """Every day from start to end, inclusive. Reads the cache first; writes it after a full answer."""
    url = archive_url(lat, lon, start, end)
    cache = cache_dir / f"{lat:.4f}_{lon:.4f}_{start}_{end}.json"
    if cache.exists():
        return _parse(json.loads(cache.read_text()), url)
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise WeatherError(f"Open-Meteo answered HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise WeatherError(f"Open-Meteo couldn't be reached: {error}") from error
    weather = _parse(payload, url)
    if all(d.precipitation_mm is not None for d in weather.days):
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"daily": payload["daily"]}) + "\n")
    return weather
