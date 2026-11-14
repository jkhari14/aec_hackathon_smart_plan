"""Load files a person imported by hand, and refuse any that cannot say where they came from.

    python3 -m manual_imports.load_imports                  # check every import under data/manual_imports
    python3 -m manual_imports.load_imports <import folder>  # check one

One folder per import:

    data/manual_imports/<source_key>/<YYYY-MM-DD>_<slug>/
        provenance.json   who fetched it, when, from what URL, under which terms   (committed)
        facts.json        the facts taken from it, each with its page or locator    (committed)
        raw/<file>        the downloaded file itself                                (gitignored)

Every import loads as a ManualImport whose tier is "manual_import", with one of two statuses:
- imported_unchecked: someone took the facts from the file; nobody else has compared them with it.
- imported_checked: a second person compared every fact with the file and signed provenance "checked".
Neither is "ok", which belongs to data_pull's live queries, so an import never reads as a live pull.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

from manual_imports.sources import HOST_TERMS, MAX_QUOTE_WORDS, SOURCES

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPORTS_DIR = REPO_ROOT / "data" / "manual_imports"

TIER = "manual_import"
STATUSES = ("imported_unchecked", "imported_checked")
SCHEMA = "manual_import/1"
FACTS_SCHEMA = "manual_import_facts/1"

_HANDLE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,39}$")
_IMPORT_ID = re.compile(r"^(\d{4}-\d{2}-\d{2})_[a-z0-9][a-z0-9-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_BBL = re.compile(r"^[1-5]\d{9}$")
_PROVENANCE_KEYS = {"schema", "source_key", "fetched_by", "fetch_method", "fetched_at", "source_url",
                    "landing_url", "terms", "file", "document_date", "document_date_note",
                    "extracted_by", "extraction_method", "checked", "approved_by", "notes"}
_REQUIRED = {"schema", "source_key", "fetched_by", "fetch_method", "fetched_at", "source_url",
             "terms", "extracted_by", "extraction_method", "document_date"}
_TERMS_KEYS = {"url", "clause", "read_on", "verdict", "note", "permission"}
_FILE_KEYS = {"name", "bytes", "sha256", "media_type"}
_CHECKED_KEYS = {"by", "on", "how"}
_DATE_FIELDS = {"document_date", "event_date"}
_WORD_LIMITED = {"fact", "quote"}


class ManualImportError(ValueError):
    def __init__(self, where: str, problems: list[str]):
        self.problems = list(problems)
        super().__init__(f"{where}: " + "; ".join(self.problems))


@dataclass(frozen=True)
class ManualImport:
    import_id: str
    source_key: str
    status: str
    provenance: dict
    facts: tuple
    raw: dict
    tier: str = TIER

    def as_dict(self) -> dict:
        return {"tier": self.tier, "status": self.status, "source_key": self.source_key,
                "import_id": self.import_id, "provenance": self.provenance,
                "facts": [dict(f) for f in self.facts], "raw": self.raw}


def _https_host(url) -> str | None:
    if not isinstance(url, str):
        return None
    parsed = urlparse(url)
    return parsed.hostname if parsed.scheme == "https" and parsed.hostname else None


def _iso_date(value) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _aware_datetime(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def _handle_problem(label: str, value) -> str | None:
    if isinstance(value, str) and _HANDLE.match(value):
        return None
    return f"{label} must be a role label such as 'project-lead' or 'claude-agent' (lowercase, no spaces), never a person's name"


def validate_provenance(prov, source_key: str, import_id: str) -> list[str]:
    if not isinstance(prov, dict):
        return ["provenance.json must be a JSON object"]
    problems = []
    if set(prov) - _PROVENANCE_KEYS:
        problems.append(f"unknown provenance keys {sorted(set(prov) - _PROVENANCE_KEYS)}")
    if _REQUIRED - set(prov):
        problems.append(f"missing provenance keys {sorted(_REQUIRED - set(prov))}")
    if prov.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA!r}")
    if prov.get("source_key") != source_key:
        problems.append(f"source_key must match the folder name {source_key!r}")
    src = SOURCES.get(source_key)
    if src is None:
        return problems + [f"{source_key!r} is not a source listed in manual_imports/sources.py"]

    for label in ("fetched_by", "extracted_by"):
        if (problem := _handle_problem(label, prov.get(label))):
            problems.append(problem)
    if prov.get("fetch_method") not in src["fetch_methods"]:
        problems.append(f"fetch_method for {source_key} must be one of {sorted(src['fetch_methods'])}")
    elif prov["fetch_method"] == "script_with_approval":
        if (problem := _handle_problem("approved_by (the person who approved the download)", prov.get("approved_by"))):
            problems.append(problem)
    fetched = _aware_datetime(prov.get("fetched_at"))
    if fetched is None:
        problems.append("fetched_at must be an ISO date-time with a UTC offset")
    else:
        if fetched > datetime.now(timezone.utc) + timedelta(days=1):
            problems.append("fetched_at is in the future")
        if fetched.date().isoformat() != import_id[:10]:
            problems.append("the folder name must start with the fetched_at date")
    host = _https_host(prov.get("source_url"))
    if host is None:
        problems.append("source_url must be an https URL")
    elif src["hosts"] is not None and host not in src["hosts"]:
        problems.append(f"source_url host {host!r} is not the publisher's ({sorted(src['hosts'])}); "
                        "a copy on another site is a hint, not the source")
    if prov.get("landing_url") is not None and _https_host(prov.get("landing_url")) is None:
        problems.append("landing_url must be an https URL")
    if not isinstance(prov.get("extraction_method"), str) or not prov.get("extraction_method", "").strip():
        problems.append("extraction_method must say how the facts were taken from the file")

    problems += _terms_problems(prov.get("terms"), src)
    host_terms = HOST_TERMS.get(host or "")
    if host_terms and isinstance(prov.get("terms"), dict) and prov["terms"].get("verdict") != host_terms["verdict"]:
        problems.append(f"a file from {host} carries verdict {host_terms['verdict']!r} ({host_terms['url']})")
    problems += _file_problems(prov.get("file"), src)

    if prov.get("document_date") is None:
        if not str(prov.get("document_date_note") or "").strip():
            problems.append("document_date is null, so document_date_note must give the reason")
    elif _iso_date(prov.get("document_date")) is None:
        problems.append("document_date must be YYYY-MM-DD or null")

    checked = prov.get("checked")
    if checked is not None:
        if not isinstance(checked, dict) or set(checked) != _CHECKED_KEYS:
            problems.append(f"checked must have exactly {sorted(_CHECKED_KEYS)}")
        else:
            if (problem := _handle_problem("checked.by", checked["by"])):
                problems.append(problem)
            elif checked["by"] == prov.get("extracted_by"):
                problems.append("checked.by must be a second person, not the one who extracted the facts")
            if _iso_date(checked["on"]) is None:
                problems.append("checked.on must be YYYY-MM-DD")
            if not str(checked["how"]).strip():
                problems.append("checked.how must say what was compared")
    return problems


def _terms_problems(terms, src) -> list[str]:
    if not isinstance(terms, dict):
        return ["terms must be an object with url, clause, read_on and verdict"]
    problems = []
    if set(terms) - _TERMS_KEYS:
        problems.append(f"unknown terms keys {sorted(set(terms) - _TERMS_KEYS)}")
    if _https_host(terms.get("url")) is None:
        problems.append("terms.url must be an https URL")
    if not str(terms.get("clause") or "").strip():
        problems.append("terms.clause must quote or name the clause behind the verdict")
    read_on = _iso_date(terms.get("read_on"))
    if read_on is None or read_on > date.today():
        problems.append("terms.read_on must be the YYYY-MM-DD date the terms were read")
    verdict = terms.get("verdict")
    if verdict not in ("a", "b", "c"):
        problems.append("terms.verdict must be a, b or c; a source marked d is never imported")
    elif verdict not in src["verdicts"]:
        problems.append(f"terms.verdict {verdict!r} is not one this source allows ({sorted(src['verdicts'])})")
    if verdict == "c" and not str(terms.get("permission") or "").strip():
        problems.append("a licensed source needs terms.permission: who granted it, when, for what")
    return problems


def _file_problems(meta, src) -> list[str]:
    if meta is None:
        return ["file is required: this source is imported from a downloaded file"] if src["raw_required"] else []
    if not isinstance(meta, dict) or set(meta) - _FILE_KEYS or {"name", "bytes", "sha256"} - set(meta):
        return [f"file must have name, bytes and sha256 (and optionally media_type), nothing else"]
    problems = []
    if not isinstance(meta["name"], str) or not meta["name"] or "/" in meta["name"] or meta["name"].startswith("."):
        problems.append("file.name must be a plain file name")
    if not isinstance(meta["bytes"], int) or meta["bytes"] <= 0:
        problems.append("file.bytes must be the file's size in bytes")
    if not isinstance(meta["sha256"], str) or not _SHA256.match(meta["sha256"]):
        problems.append("file.sha256 must be 64 lowercase hex characters")
    return problems


def validate_facts(doc, source_key: str) -> list[str]:
    if not isinstance(doc, dict):
        return ["facts.json must be a JSON object"]
    problems = []
    if doc.get("schema") != FACTS_SCHEMA:
        problems.append(f"facts schema must be {FACTS_SCHEMA!r}")
    if doc.get("source_key") != source_key:
        problems.append(f"facts source_key must be {source_key!r}")
    if set(doc) - {"schema", "source_key", "facts"}:
        problems.append(f"unknown keys in facts.json {sorted(set(doc) - {'schema', 'source_key', 'facts'})}")
    facts = doc.get("facts")
    if not isinstance(facts, list) or not facts:
        return problems + ["facts must be a non-empty list"]
    src = SOURCES[source_key]
    fields, unique, seen = src["fields"], src["unique"], set()
    for i, fact in enumerate(facts):
        where = f"fact {i + 1}"
        if not isinstance(fact, dict):
            problems.append(f"{where} must be an object")
            continue
        if set(fact) - set(fields):
            problems.append(f"{where} has fields this source does not allow: {sorted(set(fact) - set(fields))}")
        for name, required in fields.items():
            value = fact.get(name)
            if value is None or (isinstance(value, str) and not value.strip()):
                if required and name not in _DATE_FIELDS:
                    problems.append(f"{where} needs {name}")
                elif required:
                    problems.append(f"{where} needs {name} (YYYY-MM-DD)")
                continue
            if name == "page" and (not isinstance(value, int) or value < 1):
                problems.append(f"{where}: page must be a page number from 1")
            elif name in _DATE_FIELDS and _iso_date(value) is None:
                problems.append(f"{where}: {name} must be YYYY-MM-DD")
            elif name == "bbl" and not _BBL.match(str(value)):
                problems.append(f"{where}: bbl must be 10 digits")
            elif name in _WORD_LIMITED and len(str(value).split()) > MAX_QUOTE_WORDS:
                problems.append(f"{where}: {name} is over {MAX_QUOTE_WORDS} words; the repository is public, "
                                "so keep a short quote or a plain fact and link the source")
            elif name not in ("page",) and not isinstance(value, str):
                problems.append(f"{where}: {name} must be text")
        if unique and isinstance(fact.get(unique), str):
            if fact[unique] in seen:
                problems.append(f"{where}: {unique} {fact[unique]!r} appears twice")
            seen.add(fact[unique])
    return problems


def check_raw(directory: Path, meta: dict | None) -> tuple[dict, list[str]]:
    """Compare the local raw file with provenance. A missing raw file is normal: it is never committed."""
    if meta is None:
        return {"present": False, "verified": None, "note": "nothing was downloaded for this import"}, []
    path = directory / "raw" / meta["name"]
    if not path.is_file():
        return {"present": False, "verified": None,
                "note": "the raw file is not on this machine (it is never committed); size and hash not re-checked"}, []
    data = path.read_bytes()
    problems = []
    if len(data) != meta["bytes"]:
        problems.append(f"raw file is {len(data)} bytes, provenance says {meta['bytes']}")
    if hashlib.sha256(data).hexdigest() != meta["sha256"]:
        problems.append("raw file's sha256 differs from provenance: it is not the file that was imported")
    return {"present": True, "verified": not problems, "note": "size and sha256 match provenance.json"
            if not problems else "raw file does not match provenance.json"}, problems


def _read_json(path: Path, problems: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append(f"{path.name} is missing")
    except json.JSONDecodeError as exc:
        problems.append(f"{path.name} is not valid JSON ({exc})")
    return None


def load_import(directory: Path) -> ManualImport:
    directory = Path(directory)
    import_id, source_key = directory.name, directory.parent.name
    problems: list[str] = []
    if not _IMPORT_ID.match(import_id):
        problems.append("the folder name must be YYYY-MM-DD_<slug> (lowercase slug)")
    prov = _read_json(directory / "provenance.json", problems)
    facts = _read_json(directory / "facts.json", problems)
    if prov is not None:
        problems += validate_provenance(prov, source_key, import_id)
    if facts is not None and source_key in SOURCES:
        problems += validate_facts(facts, source_key)
    raw = {"present": False, "verified": None, "note": "not checked"}
    if not problems:
        raw, raw_problems = check_raw(directory, prov.get("file"))
        problems += raw_problems
    if problems:
        raise ManualImportError(f"{source_key}/{import_id}", problems)
    status = "imported_checked" if prov.get("checked") else "imported_unchecked"
    return ManualImport(import_id=import_id, source_key=source_key, status=status, provenance=prov,
                        facts=tuple(dict(f) for f in facts["facts"]), raw=raw)


def import_folders(root: Path = IMPORTS_DIR) -> list[Path]:
    if not Path(root).is_dir():
        return []
    return sorted(d for src in Path(root).iterdir() if src.is_dir() and not src.name.startswith(".")
                  for d in src.iterdir() if d.is_dir() and not d.name.startswith("."))


def load_all(root: Path = IMPORTS_DIR, source_key: str | None = None) -> list[ManualImport]:
    """Every import under root (or one source's), newest first. Raises on the first invalid import."""
    found = [load_import(d) for d in import_folders(root) if source_key in (None, d.parent.name)]
    return sorted(found, key=lambda imp: imp.import_id, reverse=True)


def code_key(imp: ManualImport) -> dict[str, dict]:
    field = SOURCES[imp.source_key]["unique"]
    if not field:
        raise ValueError(f"{imp.source_key} is not a code key")
    return {fact[field]: fact for fact in imp.facts}


def decode(code, imp: ManualImport) -> dict:
    """What a code means in an imported key, or an explicit gap. Never guesses a meaning."""
    code = str(code).strip() if code is not None else ""
    base = {"code": code, "tier": TIER, "source_key": imp.source_key, "import_id": imp.import_id,
            "source_url": imp.provenance["source_url"], "document_date": imp.provenance.get("document_date")}
    entry = code_key(imp).get(code)
    if entry is None:
        return {**base, "status": "not_in_key", "description": None,
                "reason": f"code {code!r} is not in {SOURCES[imp.source_key]['name']} as imported "
                          f"({imp.import_id}); the key may be older than the code"}
    extra = {k: v for k, v in entry.items() if k not in ("code", "description")}
    return {**base, "status": imp.status, "description": entry["description"], **extra}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("folders", nargs="*", type=Path, help="import folders (default: all)")
    args = parser.parse_args(argv)
    folders = args.folders or import_folders()
    if not folders:
        print(f"no imports under {IMPORTS_DIR}")
        return 0
    failed = 0
    for folder in folders:
        try:
            imp = load_import(folder)
        except ManualImportError as exc:
            failed += 1
            print(f"INVALID  {exc}")
            continue
        print(f"{imp.status:<19} {imp.source_key}/{imp.import_id}  {len(imp.facts)} facts  raw: {imp.raw['note']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
