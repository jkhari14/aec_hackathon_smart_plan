---
name: foresite-goal
description: Run one ForeSite teammate's build as a long-running goal. Pulls main, builds their PRs from BUILD.md in order, opens each PR, and keeps open PRs green and rebased. Use when someone says "I'm <name>" on the ForeSite team, asks to run or continue their goal, or invokes /foresite-goal <name>.
---

# ForeSite goal

You are running one teammate's part of the ForeSite build from start to finish: every PR in their
section of `BUILD.md`, in order, each one opened on GitHub with green CI. Many teammates are new to git,
so you do all the git and GitHub work for them and explain each step in one plain sentence.

The person's name is in the arguments or the message ("I'm Lise", `/foresite-goal Lise`). If it is
missing or not in `BUILD.md`, ask who they are before doing anything else.

## Once, at the start

1. Read `AGENTS.md`, the shared sections of `BUILD.md` (rules, PR order, shared contracts) and the
   person's own section, then `planning/foresite_build_plan.md` for the product and the UX bar.
2. Check the setup and fix what you can:
   - `gh auth status`. If they are not signed in, ask them to run `gh auth login` in a terminal
     (GitHub.com, HTTPS, log in with a browser). You cannot do the browser step for them.
   - `git config user.name` and `git config user.email` are set; if not, ask for them and set them.
   - `.venv/` exists; if not, create it with the first of `python3.12`, `python3.11`, `python3.10` that
     exists, then `.venv/bin/pip install -r api/requirements.txt`.
   - `web/node_modules/` exists; if not, run `npm install` in `web/`.
3. Run `git status`. If there are uncommitted changes, find out whose they are before touching them.
   Never discard work you did not create in this session.

## The loop

Repeat until the status script says every PR is open and healthy, or merged:

1. **Sync.** If you are on one of the person's branches with unfinished work, commit it there first.
   Then `git fetch origin`, `git checkout main` and `git pull --ff-only`.
2. **Ask the script.** `python3 tools/foresite_status.py <Name>`. It reads the PR order from
   `BUILD.md` and the PR states from GitHub. Do what its "Next" section says, in this order:
3. **Fix open PRs first.** For each PR it flags:
   - *Behind main or merge conflicts:* check out the branch, `git rebase origin/main`, resolve conflicts
     inside the person's own paths, rerun the tests, then `git push --force-with-lease`. If a conflict
     is in someone else's files, stop and ask the person to check with that file's owner.
   - *Its base has merged (a stacked PR):* `gh pr edit <number> --base main`, then
     `git rebase --onto origin/main <old base branch>` (this also handles squash merges), test, and
     push with `--force-with-lease`.
   - *CI failing:* `gh pr checks <number>`, then `gh run view <run id> --log-failed`; fix the cause
     and push.
   - *Changes requested:* `gh pr view <number> --comments`; address each comment, push, and reply on
     the PR saying what changed.
4. **Build the next PR** the script names:
   - Create the branch it gives you, from the base it gives you (`main`, or the person's own open PR
     when the new one builds on it).
   - Build only what that PR's paragraph in `BUILD.md` asks for, inside the person's paths plus the
     shared ones the script lists. Build against `contracts/` and its fixtures when an upstream PR
     has not merged. Check the `jahleel/` references in the person's section and port what fits into
     their own paths; never edit `jahleel/`. If a contract is missing, open a separate small PR that
     changes only `api/contracts.py`, the regenerated files and the fixture, and tell the person that
     Jacob needs to merge it first.
   - Run `.venv/bin/python -m unittest discover -s tests -t .` and, if `web/` changed,
     `cd web && npm run build`. For UI work, start the app and look at it; meet the UX bar.
   - Stage files by explicit path (never `git add .` or `git add -A`), then run
     `python3 tools/foresite_status.py <Name> --check-staged` and fix anything it reports.
   - Commit, `git push -u origin <branch>`, and open the PR:
     `gh pr create --base <base> --title "[W<wave>/PR<n>] <what it does>" --body-file <file>`, with the
     body following `.github/pull_request_template.md`, including what is missing and which upstream
     PRs it still waits on.
5. **Report, then keep going.** Tell the person in two or three sentences what you opened and the
   link, then go straight back to step 1 for the next PR. Do not wait for a merge; Jacob merges in
   order.

Stop and ask only when you are blocked: a sign-in, a conflict in someone else's files, a missing
contract, a decision only the person can make, or a check you cannot get green after two real tries.

## Done

The goal is done when the script reports that all the person's PRs are open and healthy, or merged.
Finish with a short report: each PR and its link, what each one still lacks, and what they are waiting
on. Then tell them how to pick it up again after Jacob merges (posted in Slack):
- Cursor: start a new chat and run `/foresite-goal <Name>` again (or `/goal` with the same prompt).
- Claude Code: run `/foresite-goal <Name>` again in the repo.

## Git rules

- Never push to `main`, never merge a PR, and never push to anyone else's branch. Jacob merges.
- Force-push only your own PR branch, and only with `--force-with-lease`, after a rebase.
- Never run `git reset --hard`, `git clean`, or `git checkout -- .` over work you did not create.
- Never commit the PDFs or transcripts in the repo root, `.env` files, keys, `node_modules/` or
  `dist/`. Keys stay in the environment.
- Keep each PR to the one row in `BUILD.md`; small PRs merge faster.
- Mind the clock: each PR has a target in the PR order table, and feature freeze is Sun 11:00 AM. If
  a PR is running late, open it with what works and list the rest under "What I could not do".
