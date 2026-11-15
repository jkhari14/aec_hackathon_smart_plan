# Agent instructions: ForeSite

ForeSite is a citywide 3D map of NYC for architects and structural engineers. It brings in the public
data that matters for a site at the right time, finds similar-profile cases across the city, and flags
early-warning patterns before work starts. Eight people build it in parallel, each with an agent.

## When the user says "I'm <name>"

Follow [.claude/skills/foresite-goal/SKILL.md](.claude/skills/foresite-goal/SKILL.md): it is the same
procedure in Cursor and Claude Code. In short:

1. Read [BUILD.md](BUILD.md) (rules, PR order, shared contracts, then **that person's section** only)
   and [planning/foresite_build_plan.md](planning/foresite_build_plan.md). The team is Jacob, Camilo,
   Shandon, Jahleel, Lise, Rishabh, Hongyu and Ethnie; if the name is not one of them, ask.
2. Run `python3 tools/foresite_status.py <name>` and do what it says: fix their open PRs first, then
   build the next unopened PR, only in their paths, against `contracts/` and its fixtures.
3. Check the `jahleel/` files listed in their section and reuse what fits. Never edit `jahleel/`.
4. Run the tests, stage files by explicit path, run the script again with `--check-staged`, push the
   branch `<name>/pr<n>-<short-topic>` and open the PR titled `[W<wave>/PR<n>] <what it does>`.
5. Report briefly and continue with the next PR until all of theirs are open and green.

Many teammates are new to git: do the git work for them, explain it in plain words, never push to
`main`, never merge, and never discard work you did not create. If a needed contract is missing,
open a small contract PR for Jacob instead of working around it.

## Rules

- Stay in your own paths; a `contracts/` change is its own small PR.
- No names of owners, applicants, permit holders or contractors.
- Every fact shows its source and date; a failed query is never shown as zero.
- Proof is never inferred from public data; housing violations are never scored as structural risk.
- Past cases carry a cause only as publicly reported or under investigation; no blame.
- The pattern score is relative to similar sites, never a prediction of failure.
- Limitations are visible on every screen.
- Keys stay in the environment, never in code.
- Do not commit the unredacted transcripts or PDFs in the repo root.

## Commands

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r api/requirements.txt   # Python 3.10+
.venv/bin/uvicorn api.main:app --port 8000
cd web && npm install && npm run dev        # http://localhost:5173
.venv/bin/python -m unittest discover -s tests -t .
cd web && npm run build
.venv/bin/python -m contracts.generate && (cd web && npm run contracts)   # after changing api/contracts.py
```

`api/` and `web/` exist once PR 0 has merged.
