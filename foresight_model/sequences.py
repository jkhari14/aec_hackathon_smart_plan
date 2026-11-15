"""Which record sequences most often came before an outcome: candidate early-warning rules for Jacob.

    .venv/bin/python -m foresight_model.sequences     # writes artifacts/sequences.json

Each training row's events (from 3 years before the filing up to its first outcome, or the end of its
12-month window) become tokens like "complaint_03@touching". A pattern is one token, or an ordered pair
(A dated before B), with the earth-work filing itself as the token "filing". For each pattern:
- support: how many filings had it before any outcome;
- outcome_rate: the share of those filings that went on to an outcome;
- lift: outcome_rate divided by the overall outcome rate.
Outcome events are left out of the tokens, so a pattern never contains its own outcome.
Small counts: read these as hypotheses for a rule, not as findings.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

from foresight_model.dataset import is_outcome

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
MIN_SUPPORT = 5

NAMES = {
    "filing": "earth-work, foundation or SOE filing on the site",
    "complaint_03": "complaint: adjacent building not protected",
    "complaint_14": "complaint: excavation undermining an adjacent building",
    "complaint_16": "complaint: inadequate support or shoring",
    "complaint_30": "complaint: building shaking or structural stability affected",
    "complaint_54": "complaint: wall or retaining wall bulging or cracked",
    "complaint_2K": "complaint: structurally compromised building",
    "complaint_5C": "complaint: structural stability affected by a new building",
}


def describe(token: str) -> str:
    kind, _, where = token.partition("@")
    name = NAMES.get(kind) or kind.replace("incident_", "construction incident: ").replace("_", " ")
    return f"{name} ({'touching lot' if where == 'touching' else 'site'})" if where else name


def tokens(row: dict) -> list[tuple[str, str]]:
    """(date, token) before the outcome, the filing included, in date order."""
    out = [(row["filing_date"], "filing")]
    for event in row["sequence"]:
        if row["first_outcome"] and event["date"] >= row["first_outcome"]:
            continue
        kind = event["kind"]
        probe = {"kind": kind, "incident": kind.split("_", 1)[1] if kind.startswith("incident_") else None}
        if row["label"] and is_outcome(probe) and event["date"] == row["first_outcome"]:
            continue
        out.append((event["date"], f"{kind}@{event['where']}"))
    return sorted(out)


def patterns(row: dict) -> set[tuple[str, ...]]:
    toks = tokens(row)
    found = {(t,) for _, t in toks if t != "filing"}
    for (d1, a), (d2, b) in combinations(toks, 2):
        if d1 < d2 and a != b:
            found.add((a, b))
    return found


def mine(rows: list[dict], min_support: int = MIN_SUPPORT) -> dict:
    base = sum(r["label"] for r in rows) / len(rows) if rows else 0.0
    counts: dict[tuple, list[int]] = {}
    for row in rows:
        for pattern in patterns(row):
            seen = counts.setdefault(pattern, [0, 0])
            seen[0] += 1
            seen[1] += row["label"]
    results = []
    for pattern, (support, hits) in counts.items():
        if support < min_support or pattern == ("filing",):
            continue
        rate = hits / support
        results.append({
            "pattern": list(pattern),
            "description": " then ".join(describe(t) for t in pattern),
            "support": support,
            "followed_by_outcome": hits,
            "outcome_rate": round(rate, 3),
            "lift": round(rate / base, 2) if base else None,
        })
    results.sort(key=lambda r: (-(r["lift"] or 0), -r["support"]))
    return {"rows": len(rows), "base_rate": round(base, 3), "min_support": min_support,
            "note": "Hypotheses for early-warning rules, from a small sample; not findings.",
            "patterns": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=Path, default=ARTIFACTS / "rows.json")
    parser.add_argument("--min-support", type=int, default=MIN_SUPPORT)
    args = parser.parse_args(argv)
    result = mine(json.loads(args.rows.read_text())["rows"], args.min_support)
    (ARTIFACTS / "sequences.json").write_text(json.dumps(result, indent=1) + "\n")
    for p in result["patterns"][:12]:
        print(f"lift {p['lift']:>5}  n={p['support']:<4} {p['description']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
