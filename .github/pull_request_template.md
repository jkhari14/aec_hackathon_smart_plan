## [W?/PR?] What this does

<!-- One or two sentences. Title format: [W<wave>/PR<n>] <what it does>; branch: <name>/pr<n>-<topic>. -->

**Owner:**
**Depends on:** <!-- PR numbers from BUILD.md that must merge first -->

## Checklist

- [ ] Only touches my paths from BUILD.md (or a contract change agreed with Jacob, in its own PR)
- [ ] Builds against `contracts/` and its fixtures; regenerated with `python -m contracts.generate` and `npm run contracts` if a contract changed
- [ ] `.venv/bin/python -m unittest discover -s tests -t .` passes
- [ ] `cd web && npm run build` passes (if `web/` changed)
- [ ] Every number and claim in the UI names its source; errors are shown as errors, never as zero
- [ ] No owner, applicant, permit holder or contractor names; no keys in code

## What I could not do

## Screenshot or demo
