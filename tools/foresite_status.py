"""Where one teammate stands: their PRs from BUILD.md, what GitHub says about each, and what to do next.

    python3 tools/foresite_status.py Lise                 # status and the next step
    python3 tools/foresite_status.py Lise --check-staged  # are the staged files inside Lise's paths?

Uses only the standard library and the `gh` CLI, so it works before the venv exists. The agent goal
(.claude/skills/foresite-goal/SKILL.md) runs this at the start of every loop instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "BUILD.md"
TITLE_PR = re.compile(r"\[W\d+/PR(\d+)\]")

# Anyone may touch these in a PR, in small and clearly described edits.
SHARED_PATHS = [
    "tests/",
    "web/package.json",
    "web/package-lock.json",
    "api/requirements.txt",
    "api/main.py",
    "api/stubs.py",
    "web/src/api/client.ts",
    # Generated from the app and the contracts: regenerate, never edit by hand.
    "api/openapi.json",
    "web/src/api_types.ts",
]
# Never committed by anyone: the unredacted root transcripts and PDFs, secrets, build output.
FORBIDDEN = re.compile(r"^[^/]+\.(pdf|txt)$|^AECtech_Hackathon_Brainstorm_Transcript|(^|/)\.env|/dist/|node_modules/")


@dataclass
class PlannedPr:
    number: int
    wave: int
    owner: str
    what: str
    depends_on: list[int] = field(default_factory=list)
    target: str = ""


def read_plan() -> tuple[list[PlannedPr], dict[str, list[str]]]:
    text = BUILD.read_text()
    order = text[text.index("## PR order") : text.index("## Rules every agent follows")]
    prs = []
    for line in order.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 6 and cells[0].isdigit():
            deps = [] if cells[4] in ("", "all") else [int(d) for d in re.findall(r"\d+", cells[4])]
            if cells[4] == "all":
                deps = [-1]
            prs.append(PlannedPr(int(cells[0]), int(cells[1]), cells[2], cells[3], deps, cells[5]))
    owns = {}
    for section in text.split("\n## ")[1:]:
        person = section.split(":", 1)[0]
        match = re.search(r"\*\*Owns:\*\*(.*?)(?:\n\n|\n\*\*)", section, re.S)
        if match and person.isalpha():
            owns[person] = [p for p in re.findall(r"`([^`]+)`", match.group(1)) if "/" in p or "." in p]
    return prs, owns


def github_prs() -> dict[int, dict]:
    if not shutil.which("gh"):
        sys.exit("The GitHub CLI is missing. Install it (brew install gh), then run: gh auth login")
    auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, cwd=ROOT)
    if auth.returncode != 0:
        sys.exit("Not signed in to GitHub. Run: gh auth login   (choose GitHub.com, HTTPS, browser)")
    fields = "number,title,state,headRefName,baseRefName,url,mergeStateStatus,statusCheckRollup,reviewDecision"
    out = subprocess.run(
        ["gh", "pr", "list", "--state", "all", "--limit", "300", "--json", fields],
        capture_output=True, text=True, cwd=ROOT, check=True,
    ).stdout
    found: dict[int, dict] = {}
    for pr in json.loads(out):
        match = TITLE_PR.search(pr["title"])
        if not match or pr["state"] == "CLOSED":
            continue
        n = int(match.group(1))
        if n not in found or pr["state"] == "MERGED":
            found[n] = pr
    return found


def ci_state(pr: dict) -> str:
    checks = pr.get("statusCheckRollup") or []
    if not checks:
        return "no checks yet"
    conclusions = {(c.get("conclusion") or c.get("status") or "").upper() for c in checks}
    if conclusions & {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT"}:
        return "CI failing"
    if conclusions & {"IN_PROGRESS", "QUEUED", "PENDING", ""}:
        return "CI running"
    return "CI green"


def describe(n: int, gh: dict[int, dict]) -> str:
    pr = gh.get(n)
    if not pr:
        return "not opened"
    if pr["state"] == "MERGED":
        return "merged"
    notes = [f"open #{pr['number']}", ci_state(pr)]
    merged_branches = {p["headRefName"] for p in gh.values() if p["state"] == "MERGED"}
    if pr["baseRefName"] != "main" and pr["baseRefName"] in merged_branches:
        notes.append(f"its base {pr['baseRefName']} has merged: retarget to main and rebase")
    if pr.get("mergeStateStatus") == "DIRTY":
        notes.append("merge conflicts: rebase on main")
    elif pr.get("mergeStateStatus") == "BEHIND":
        notes.append("behind main: rebase")
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        notes.append("changes requested")
    return ", ".join(notes)


def status(name: str) -> int:
    prs, owns = read_plan()
    mine = [p for p in prs if p.owner.lower() == name.lower()]
    if not mine:
        print(f"{name} is not in BUILD.md. The team: {', '.join(sorted({p.owner for p in prs}))}.")
        return 2
    name = mine[0].owner
    gh = github_prs()
    merged = {n for n, pr in gh.items() if pr["state"] == "MERGED"}

    print(f"{name}'s PRs (from BUILD.md and GitHub):")
    for p in mine:
        deps = "all earlier PRs" if p.depends_on == [-1] else ", ".join(
            f"PR {d} ({'merged' if d in merged else 'not merged'})" for d in p.depends_on
        ) or "nothing"
        print(f"  PR {p.number} (wave {p.wave}, target {p.target}): {p.what}")
        print(f"      status: {describe(p.number, gh)}; depends on: {deps}")
        if p.number in gh and gh[p.number]["state"] == "OPEN":
            print(f"      branch {gh[p.number]['headRefName']} -> {gh[p.number]['baseRefName']}, {gh[p.number]['url']}")
    print(f"\nYour paths: {', '.join(owns.get(name, []))}")
    print(f"Shared, small edits only: {', '.join(SHARED_PATHS)}")

    print("\nNext:")
    fixes = [p for p in mine if p.number in gh and gh[p.number]["state"] == "OPEN" and any(
        s in describe(p.number, gh) for s in ("failing", "conflicts", "behind", "changes requested", "retarget"))]
    if fixes:
        for p in fixes:
            print(f"  Fix PR {p.number} first: {describe(p.number, gh)}.")
        return 0
    todo = [p for p in mine if p.number not in gh]
    if not todo:
        waiting = [p.number for p in mine if gh[p.number]["state"] == "OPEN"]
        if waiting:
            print(f"  All your PRs are open and healthy. Waiting on Jacob to merge: PR {', PR '.join(map(str, waiting))}.")
        else:
            print("  All your PRs are merged. Ask Jacob what to pick up next.")
        return 0
    p = todo[0]
    if 0 not in merged and p.number != 0:
        print("  PR 0 has not merged yet, so contracts/, api/ and web/ are not on main. Do your")
        print("  'Before PR 0' prep from your section of BUILD.md, then run this again.")
        return 0
    owner_of = {q.number: q.owner for q in prs}
    own_open = [d for d in p.depends_on if owner_of.get(d) == name and d in gh and gh[d]["state"] == "OPEN"]
    base = gh[own_open[-1]]["headRefName"] if own_open else "main"
    others = [d for d in p.depends_on if d >= 0 and d not in merged and d not in own_open]
    print(f"  Build PR {p.number}: {p.what}.")
    print(f"  Branch: {name.lower()}/pr{p.number}-<short-topic>, created from {base}.")
    if own_open:
        print(f"  It builds on your own open PR {own_open[-1]}, so open it with --base {base}. When that")
        print("  PR merges, this script will tell you to retarget it to main and rebase.")
    if others:
        print(f"  PR {', PR '.join(map(str, others))} not merged yet: build against contracts/fixtures/ and")
        print("  say so in the PR description.")
    print(f"  Title: [W{p.wave}/PR{p.number}] <what it does>")
    return 0


def classify(paths: list[str], owner: str, owned: list[str]) -> tuple[list[str], list[str]]:
    """Problems (forbidden or outside the owner's paths) and shared-path notes for a list of files."""
    mine = [p.rstrip("/") for p in owned]
    problems, shared = [], []
    for path in paths:
        if FORBIDDEN.search(path):
            problems.append(f"{path}: never commit this (unredacted transcript, PDF, secret or build output)")
        elif any(path == p or path.startswith(p + "/") for p in mine):
            continue
        elif any(path == s.rstrip("/") or path.startswith(s) for s in SHARED_PATHS):
            shared.append(path)
        else:
            problems.append(f"{path}: outside {owner}'s paths")
    return problems, shared


def check_staged(name: str) -> int:
    _, owns = read_plan()
    owner = next((o for o in owns if o.lower() == name.lower()), None)
    if not owner:
        print(f"{name} is not in BUILD.md.")
        return 2
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout.splitlines()
    problems, shared = classify(staged, owner, owns[owner])
    for path in shared:
        print(f"note: {path} is shared; keep the edit small and mention it in the PR description")
    for problem in problems:
        print(f"error: {problem}")
    if problems:
        print("Unstage with: git restore --staged <path>")
        return 1
    print(f"ok: {len(staged)} staged files, all inside {owner}'s paths or the shared ones.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name")
    parser.add_argument("--check-staged", action="store_true")
    args = parser.parse_args()
    return check_staged(args.name) if args.check_staged else status(args.name)


if __name__ == "__main__":
    sys.exit(main())
