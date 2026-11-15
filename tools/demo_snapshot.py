"""Save every GET answer the app needs for the demo sites as static files: the deploy's offline fallback.

    .venv/bin/python -m tools.demo_snapshot          # from data/cache/, no network: web/public/snapshot/
    .venv/bin/python -m tools.demo_snapshot --pull   # refresh data/cache/ for the demo addresses first

It asks the API itself (in process), so whatever routers have merged are what gets saved, and a stub's
answer stays labeled as sample data. The web client reads web/public/snapshot/ when the API is down or the
build is static (VITE_STATIC=1), and shows the saved date. Run it again at the freeze.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "public" / "snapshot"
CACHE = ROOT / "data" / "cache"
DEMO_SITES = ROOT / "data" / "demo_sites.json"
DEMO_ADDRESSES = ROOT / "data" / "demo_addresses.json"
SITE_ROUTES = ("profile", "similar", "warnings", "warnings/checks", "pattern", "actions")
AS_OF_ROUTES = ("profile", "warnings", "warnings/checks")


def snapshot_key(url: str) -> str:
    """'/api/search?q=2625 Bedford' -> 'search@q=2625-bedford'. The web client builds the same key."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(parts.path).removeprefix("/api/").strip("/")
    query = sorted(urllib.parse.parse_qsl(parts.query))
    suffix = "&".join(f"{k}={re.sub(r'[^a-z0-9]+', '-', v.lower()).strip('-')}" for k, v in query)
    return f"{path}@{suffix}" if suffix else path


def demo_sites() -> list[dict]:
    """[{bbl, address, as_of}], from Ethnie's data/demo_sites.json when it exists, plus every cached pull."""
    sites: dict[str, dict] = {}
    if DEMO_SITES.exists():
        data = json.loads(DEMO_SITES.read_text())
        for entry in data.get("sites", data) if isinstance(data, dict) else data:
            if isinstance(entry, dict) and entry.get("bbl"):
                sites[str(entry["bbl"])] = {"bbl": str(entry["bbl"]), "address": entry.get("address"),
                                            "as_of": entry.get("as_of")}
    for path in sorted(CACHE.glob("*.json")):
        pull = json.loads(path.read_text())
        bbl = pull.get("site_bbl")
        if bbl and bbl not in sites:
            label = (pull.get("address_lookup") or {}).get("matched_label")
            sites[bbl] = {"bbl": bbl, "address": label, "as_of": None}
    return list(sites.values())


def refresh_cache() -> None:
    from data_pull.site_brief_pull import main as pull_main
    pull_main(["--demo"])


def snapshot(out: Path = OUT, as_of_dates: list[str] | None = None) -> dict:
    from fastapi.testclient import TestClient

    from api.main import app
    from api.stubs import FIXTURE_HEADER

    client = TestClient(app)
    saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    routes: dict[str, dict] = {}
    failed: list[str] = []

    def save(url: str):
        response = client.get(url)
        if response.status_code != 200:
            failed.append(f"{url}: HTTP {response.status_code}")
            return None
        key = snapshot_key(url)
        path = out / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(response.json(), ensure_ascii=False) + "\n")
        routes[key] = {"url": url, "sample": response.headers.get(FIXTURE_HEADER) == "true"}
        return response.json()

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for layer in save("/api/layers") or []:
        save(f"/api/layers/{urllib.parse.quote(layer['layer_id'])}")
    for case in save("/api/cases") or []:
        save(f"/api/cases/{urllib.parse.quote(case['id'])}")
    if DEMO_ADDRESSES.exists():
        for address in json.loads(DEMO_ADDRESSES.read_text()).get("addresses", []):
            save(f"/api/search?{urllib.parse.urlencode({'q': address})}")
    for site in demo_sites():
        bbl = site["bbl"]
        if site.get("address"):
            save(f"/api/search?{urllib.parse.urlencode({'q': site['address']})}")
        for route in SITE_ROUTES:
            save(f"/api/sites/{bbl}/{route}")
        for as_of in sorted({d for d in [site.get("as_of"), *(as_of_dates or [])] if d}):
            for route in AS_OF_ROUTES:
                save(f"/api/sites/{bbl}/{route}?as_of={as_of}")
    manifest = {"saved_at": saved_at, "routes": routes, "failed": failed}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pull", action="store_true", help="refresh data/cache/ for the demo addresses first")
    parser.add_argument("--as-of", action="append", default=[], help="also save as-of answers for this date")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    if args.pull:
        refresh_cache()
    manifest = snapshot(args.out, args.as_of)
    sample = sum(1 for r in manifest["routes"].values() if r["sample"])
    print(f"saved {len(manifest['routes'])} answers ({sample} still sample data) -> {args.out}")
    for failure in manifest["failed"]:
        print(f"  not saved: {failure}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
