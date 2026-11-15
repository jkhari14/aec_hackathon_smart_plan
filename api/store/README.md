SQLite project store. Owner: Jahleel (PR 4, 9).

One file, `api/store/data/projects.sqlite` (gitignored; `FORESITE_PROJECTS_DB` moves it). There are no
accounts: a browser tab acts as one of the project's roles, and a note, pin or item owner is refused
(422) unless the project has a member in that role. Anyone with a project's id can read and change it: fine for the demo, not for
real client work. The value lists come from `api/contracts.py`, and
the tables repeat them as CHECK constraints.

**Two tabs on one project.** Every write bumps the project's version. `GET /api/projects/{id}` sends it
as an `ETag`; a tab that polls with `If-None-Match` gets `304` and no body until the other tab writes.
Every write answers with the whole project and its new `ETag`. (A `fetch` that sets `If-None-Match`
itself sees the 304 as `ok: false`, so treat 304 as "unchanged", not as a failure.)

**The structural model.** `POST /model` keeps the model on the project, replacing the last one. With
PR 13's `model_input` in, a Revit export goes through `model_input.revit.read_revit` first (its
`ModelInputError` is a 422, and nothing is kept), and `model_input.store.save(project_id, site_bbl,
model)` gets a copy, which the site profile reads. Without `model_input`, the model is kept as sent; one
that is there but fails to import refuses the upload (500). The site's copy is in memory, so after a
restart the project still has its model but the profile does not until it is uploaded again.

**Items.** `POST /items` adds the site's action items; one already on the project keeps its status and
owner. `PATCH /items` is all or nothing: an unknown id is a 404 and nothing changes. `owner_role` sent
as `null` unassigns; left out, it stays. `done` is the team's claim, never a proof read from records.

**Limits.** Over a cap is refused, never cut: 20 members, 500 items, 2000 notes, 500 pins per project;
4000 characters a note; 200 KB a structural model. Project ids are 16 random hex characters.
