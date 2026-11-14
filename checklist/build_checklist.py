"""Build the adjoining-property checklist from a data_pull file.

    python3 -m checklist.build_checklist data/cache/2625-bedford-ave-brooklyn.json
    python3 -m checklist.build_checklist data/cache/2625-bedford-ave-brooklyn.json --as-of 2026-11-11
    python3 -m checklist.build_checklist <pull.json> --inputs data/project_inputs/example_inputs.json

Leads in data/leads/<pull file name>.json are read when the file exists (--no-leads skips them).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from checklist.applicability import evaluate, excavation_status, validate_inputs
from checklist.checklist_rules import RULES
from checklist.neighbor_context import lot_context
from checklist.record_evidence import citations_for_row, code_citations, related_filings
from checklist.row_proof import load_leads, row_proof

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "checklists"
LEADS_DIR = REPO_ROOT / "data" / "leads"
_ROLLUP_ORDER = ("applies", "needs_input", "unknown", "set_by_dob", "does_not_apply")

CAVEATS = [
    "A row is never marked done from public data: its proof is a document the public record "
    "does not hold. 'provided_unverified' means the project team supplied it; nobody checked it. "
    "'reported_not_read' means a public source reports it; nobody here has read it.",
    "related_records sit beside a row; they are not its proof.",
    "Counts use each record's status at pull time, not on the as-of date.",
    "dob_311_requests and dob_complaints can count the same complaint twice: never add them.",
    "Requirements are paraphrased; read the linked code text before relying on a row.",
    "Nothing here establishes the cause of any incident.",
]


def _rollup(statuses: list[str]) -> str:
    return next((s for s in _ROLLUP_ORDER if s in statuses), "unknown")


def _gap(applies: dict, proof: dict) -> bool:
    return applies["status"] == "applies" and proof["status"] != "provided_unverified"


def _row(rule, inputs, leads, excavation, adjacent, neighbors_known, site_filings, citations, cutoff) -> dict:
    proof = row_proof(rule.section, inputs, leads)
    row = {"id": rule.id, "section": rule.section, "title": rule.title, "requirement": rule.requirement,
           "parties": list(rule.parties), "life_safety": rule.life_safety, "proof_needed": rule.proof_needed,
           "source_url": rule.source_url, "scope": rule.scope, "proof": proof,
           "related_records": {"filings": related_filings(rule.related_filings, site_filings, cutoff),
                               "citations": citations_for_row(rule.section, citations)}}
    if rule.scope == "site":
        row["applies"] = evaluate(rule.condition, inputs, excavation)
        row["open_gap"] = _gap(row["applies"], proof)
        return row
    per_building = []
    for ctx in adjacent:
        applies = evaluate(rule.condition, inputs, excavation, ctx["bbl"])
        per_building.append({"bbl": ctx["bbl"], "address": ctx["address"],
                             "building_presence": ctx["building_presence"]["status"], "applies": applies,
                             "open_gap": _gap(applies, proof)})
    row["per_building"] = per_building
    if not neighbors_known:
        row["applies"] = {"status": "unknown", "basis": [], "needs": [], "notes": ["the touching-lots lookup failed"]}
    elif not per_building:
        row["applies"] = {"status": "does_not_apply", "needs": [], "notes": [],
                          "basis": [{"kind": "public_record", "detail": "no adjacent building found"}]}
    else:
        row["applies"] = {"status": _rollup([p["applies"]["status"] for p in per_building]), "basis": [],
                          "needs": sorted({n for p in per_building for n in p["applies"]["needs"]}),
                          "notes": [f"rolled up from {len(per_building)} adjacent building(s)"]}
    row["open_gap"] = any(p["open_gap"] for p in per_building)
    return row


def build(pull: dict, raw_inputs: dict, cutoff: date | None, raw_leads: dict | None = None) -> dict:
    inputs = validate_inputs(raw_inputs)
    leads = load_leads(raw_leads or {}, {rule.section for rule in RULES}, cutoff)
    site, touching = pull["site"], pull["touching_lots"]
    site_filings = site["datasets"].get("dob_now_filings") or {}
    excavation = excavation_status(site_filings, inputs, cutoff)
    contexts = {lot["bbl"]: lot_context(lot, cutoff) for lot in [site, *touching]}
    adjacent = [contexts[lot["bbl"]] for lot in touching if contexts[lot["bbl"]]["building_presence"]["status"] != "no"]
    neighbors_known = (pull.get("touching_lots_lookup") or {}).get("status") == "ok"
    citations = code_citations([site, *touching], cutoff)
    rows = [_row(rule, inputs, leads, excavation, adjacent, neighbors_known, site_filings, citations, cutoff)
            for rule in RULES]
    statuses = [r["applies"]["status"] for r in rows]
    return {
        "schema_version": 1,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pull": {"pulled_at": pull.get("pulled_at"), "site_bbl": pull.get("site_bbl"),
                 "matched_label": (pull.get("address_lookup") or {}).get("matched_label")},
        "as_of": cutoff.isoformat() if cutoff else None,
        "inputs": inputs, "inputs_note": (raw_inputs or {}).get("_note"), "leads_note": (raw_leads or {}).get("_note"),
        "excavation": excavation,
        "site": contexts[site["bbl"]],
        "adjacent_buildings": adjacent,
        "rows": rows,
        "site_signals": {"code_citations": citations},
        "summary": {"rows": len(rows), **{s: statuses.count(s) for s in _ROLLUP_ORDER},
                    "open_gaps": sum(r["open_gap"] for r in rows),
                    "inputs_needed": sorted({n for r in rows for n in r["applies"]["needs"]})},
        "caveats": CAVEATS,
    }


def _print_summary(result: dict) -> None:
    site, summary = result["site"], result["summary"]
    print(f"{site['address']} ({site['bbl']}) | pulled {result['pull']['pulled_at']} | as of {result['as_of'] or 'pull time'}")
    print(f"Excavation: {result['excavation']['status']}")
    for row in result["rows"]:
        tag = ("GAP" if row["open_gap"] else row["applies"]["status"].upper()) + ("+LEAD" if row["proof"]["leads"] else "")
        needs = f" needs: {', '.join(row['applies']['needs'])}" if row["applies"]["needs"] else ""
        print(f"  [{tag:<17}] {row['section']:<10} {row['title']}{needs}")
    for ctx in result["adjacent_buildings"]:
        c = ctx["counts"]
        open_counts = " ".join(f"{k}={v['open'] if v['status'] == 'ok' else v['status']}" for k, v in c.items())
        print(f"  adjacent {ctx['bbl']} {ctx['address'] or '?'} built {ctx['year_built'] or '?'} | open: {open_counts}")
    print(f"Summary: {summary}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pull_file", type=Path, help="a data_pull JSON file")
    parser.add_argument("--inputs", type=Path, help="project inputs JSON")
    parser.add_argument("--as-of", type=date.fromisoformat, help="count only records dated before YYYY-MM-DD")
    parser.add_argument("--no-leads", action="store_true", help="skip data/leads/<pull file name>.json")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)

    pull = json.loads(args.pull_file.read_text(encoding="utf-8"))
    raw_inputs = json.loads(args.inputs.read_text(encoding="utf-8")) if args.inputs else {}
    leads_path = LEADS_DIR / args.pull_file.name
    raw_leads = None if args.no_leads or not leads_path.exists() else json.loads(leads_path.read_text(encoding="utf-8"))
    result = build(pull, raw_inputs, args.as_of, raw_leads)
    name = args.pull_file.stem + (f"-as-of-{args.as_of}" if args.as_of else "") + (f"-{args.inputs.stem}" if args.inputs else "") + ("-no-leads" if args.no_leads else "")
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"{name}.json"
    out_path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    _print_summary(result)
    print(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
