"""Start a manual import from a file a person downloaded in a browser.

    python3 -m manual_imports.new_import dob_complaint_categories ~/Downloads/list.pdf \\
        --url "<the exact URL the file came from>" --by <your role>
    python3 -m manual_imports.new_import precedent_report --no-file --url "<article URL>" --by <role>

It copies the file into data/manual_imports/<source>/<today>_<slug>/raw/ (gitignored), records
its size and sha256, and writes provenance.json and facts.json skeletons. The skeleton does not
validate until you fill in extraction_method, document_date (or the reason it is null) and
the facts; then run: python3 -m manual_imports.load_imports
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from manual_imports.load_imports import FACTS_SCHEMA, IMPORTS_DIR, SCHEMA
from manual_imports.sources import SOURCES, terms_for


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "import"


def start_import(source_key: str, file: Path | None, url: str, by: str, method: str,
                 slug: str | None = None, root: Path = IMPORTS_DIR, approved_by: str | None = None) -> Path:
    src = SOURCES[source_key]
    if file is None and src["raw_required"]:
        raise SystemExit(f"{source_key} is imported from a downloaded file; pass its path")
    fetched_at = datetime.now().astimezone().replace(microsecond=0)
    folder = Path(root) / source_key / f"{fetched_at.date().isoformat()}_{_slug(slug or (file.stem if file else 'page'))}"
    if folder.exists():
        raise SystemExit(f"{folder} already exists; pass --slug to name this import differently")
    meta = None
    if file is not None:
        data = Path(file).read_bytes()
        (folder / "raw").mkdir(parents=True)
        shutil.copy2(file, folder / "raw" / Path(file).name)
        meta = {"name": Path(file).name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    folder.mkdir(parents=True, exist_ok=True)
    known = terms_for(source_key, urlparse(url).hostname)
    terms = dict(known) if known else {"url": "", "clause": "", "read_on": "", "verdict": "b"}
    prov = {"schema": SCHEMA, "source_key": source_key, "fetched_by": by, "fetch_method": method,
            "fetched_at": fetched_at.isoformat(), "source_url": url, "landing_url": src["landing_url"],
            "terms": terms, "file": meta, "document_date": None, "document_date_note": "",
            "extracted_by": by, "extraction_method": "", "checked": None}
    if method == "script_with_approval":
        prov["approved_by"] = approved_by
    (folder / "provenance.json").write_text(json.dumps(prov, indent=1) + "\n", encoding="utf-8")
    example = {name: None for name in src["fields"]}
    facts = {"schema": FACTS_SCHEMA, "source_key": source_key, "facts": [example]}
    (folder / "facts.json").write_text(json.dumps(facts, indent=1) + "\n", encoding="utf-8")
    return folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source_key", choices=sorted(SOURCES))
    parser.add_argument("file", nargs="?", type=Path, help="the file you downloaded")
    parser.add_argument("--no-file", action="store_true", help="nothing was downloaded (read in a browser)")
    parser.add_argument("--url", required=True, help="the exact https URL the file or page came from")
    parser.add_argument("--by", required=True, help="your role label, lowercase (e.g. structural-engineer), never your name")
    parser.add_argument("--method", default="browser_by_person")
    parser.add_argument("--slug", help="a short name for this import (default: the file name)")
    parser.add_argument("--approved-by", help="with --method script_with_approval: who approved the download")
    args = parser.parse_args(argv)
    if (args.file is None) != args.no_file:
        parser.error("pass the downloaded file, or --no-file when nothing was downloaded")
    folder = start_import(args.source_key, args.file, args.url, args.by, args.method, args.slug,
                          approved_by=args.approved_by)
    print(f"started {folder}")
    print("next: re-read the terms at provenance terms.url (update clause and read_on if they changed),")
    print("      fill in extraction_method, document_date or document_date_note, and facts.json,")
    print("      then run: python3 -m manual_imports.load_imports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
