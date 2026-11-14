# manual_imports

Facts a person imported by hand from a source a crawler can't or mustn't fetch, each with its
provenance. They load as their own trust tier (`manual_import`), never as a live pull. Which
sources qualify and why: [docs/manual_data_imports.md](../docs/manual_data_imports.md).

```bash
python3 -m manual_imports.new_import <source_key> <downloaded file> --url <exact URL> --by <role>
python3 -m manual_imports.load_imports            # validate every import; exits 1 if any is invalid
python3 -m unittest discover -s tests -t .        # offline tests
```

- `sources.py`: the sources a person may import, their allowed hosts, fetch methods, terms and fact fields.
- `load_imports.py`: the validating loader, plus `decode(code, import)` for code keys.
- `new_import.py`: copies a downloaded file into `raw/` (gitignored), hashes it, writes skeletons.

## Rules

- **The raw file is never committed.** `data/manual_imports/**/raw/` is gitignored; commit
  `provenance.json` and `facts.json` only.
- **People are role labels, never names** (`project-lead`, `structural-engineer`, `claude-agent`).
  Nobody's name goes into a fact either.
- **Statuses:**
  - `imported_unchecked` until a second person compares every fact with the file;
  - then `imported_checked`.
  - Never `ok`.
- **A code missing from a key decodes as `not_in_key`, never as a guess.**
