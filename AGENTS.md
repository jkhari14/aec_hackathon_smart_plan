# Agent instructions: ForeSite

ForeSite is a citywide 3D map of NYC for architects and structural engineers. It brings in the public
data that matters for a site at the right time, finds similar-profile cases across the city, and flags
early-warning patterns before work starts. Eight people build it in parallel, each with an agent.

## When the user says "I'm <name>"

1. Read [BUILD.md](BUILD.md): the kickoff, PR order, rules and shared contracts, then **that person's
   section** only. The team is Jacob, Camilo, Shandon, Jahleel, Lise, Rishabh, Hongyu and Ethnie.
2. Read [planning/foresite_build_plan.md](planning/foresite_build_plan.md) for the product, data
   sources and the UX bar.
3. Find their first PR that is not merged yet (check `git log` on `main` and open PRs). Build only that
   PR, only in their paths, against `contracts/` and its fixtures.
4. Check the `jahleel/` files listed in their section and reuse what fits. Never edit `jahleel/`.
5. Run the tests, rebase on `main`, push the branch `<name>/pr<n>-<short-topic>` and open the PR titled
   `[W<wave>/PR<n>] <what it does>` using the PR template.
6. Report what was built, what is missing, and the next PR.

If the name is not in BUILD.md, ask who they are. If a needed contract is missing, propose a small
contract PR for Jacob instead of working around it.

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
