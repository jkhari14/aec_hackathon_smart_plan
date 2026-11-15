// "Draft checklist": create the project, load the site's items for the chosen job, add them with owners.
import assert from "node:assert/strict";
import { test } from "node:test";

import { addProjectItems, draftProject, type DraftDeps, type DraftInput } from "../src/features/project_screen/draft.ts";

const input: DraftInput = {
  bbl: "3052110074",
  siteLabel: "123 Main St",
  jobType: "alteration",
  constructionType: "masonry",
  scope: ["structural"],
  members: [{ name: "Ana", role: "architect" }, { name: "Sam", role: "structural_engineer" }, { name: "Contractor", role: "contractor" }],
};

const item = { id: "a", discipline: "geotech", hazard: "geotech", title: "t", why: "w", status: "open", owner_role: null,
  source_rule: "r", life_safety: true } as never;

function deps(over: Partial<DraftDeps> = {}) {
  const calls: Record<string, unknown[]> = { create: [], actions: [], addItems: [] };
  const d: DraftDeps = {
    create: async (body) => { calls.create.push(body); return "p1"; },
    actions: async (bbl, opts) => { calls.actions.push([bbl, opts]); return { data: [item], sample: false }; },
    addItems: async (id, items) => { calls.addItems.push([id, items]); },
    ...over,
  };
  return { d, calls };
}

test("creates the project with the setup choices and the full scope", async () => {
  const { d, calls } = deps();
  const result = await draftProject(d, input);
  assert.equal(result.projectId, "p1");
  assert.equal(result.notice, null);
  assert.deepEqual(calls.create[0], {
    name: "Project: 123 Main St", site_bbl: "3052110074", stage: "design", members: input.members,
    job_type: "alteration", construction_type: "masonry", work_types: ["structural", "sprinkler", "plumbing", "mechanical"],
  });
  assert.deepEqual(calls.actions[0], ["3052110074", { jobType: "alteration", workTypes: ["structural", "sprinkler", "plumbing", "mechanical"],
    stage: "design" }]);
});

test("adds the items with owners filled from their discipline", async () => {
  const { d, calls } = deps();
  await draftProject(d, input);
  const [id, items] = calls.addItems[0] as [string, { owner_role: string }[]];
  assert.equal(id, "p1");
  assert.equal(items[0].owner_role, "structural_engineer");
});

test("sample items stop the draft before any project is made", async () => {
  const { d, calls } = deps({ actions: async () => ({ data: [item], sample: true }) });
  await assert.rejects(draftProject(d, input), /sample/i);
  assert.equal(calls.create.length, 0);
  assert.equal(calls.addItems.length, 0);
});

test("a checklist that fails to load stops the draft before any project is made", async () => {
  const { d, calls } = deps({ actions: async () => { throw new Error("site profile could not answer"); } });
  await assert.rejects(draftProject(d, input), /could not answer/);
  assert.equal(calls.create.length, 0);
});

test("addProjectItems reloads a saved project's checklist and adds it with owners", async () => {
  const { d, calls } = deps();
  await addProjectItems(d, { id: "p9", site_bbl: "3052110074", job_type: "alteration", work_types: ["structural"] });
  assert.deepEqual(calls.actions[0], ["3052110074", { jobType: "alteration", workTypes: ["structural"] }]);
  const [id, items] = calls.addItems[0] as [string, { owner_role: string }[]];
  assert.equal(id, "p9");
  assert.equal(items[0].owner_role, "structural_engineer");
});

test("addProjectItems only assigns roles the project has", async () => {
  const { d, calls } = deps();
  await addProjectItems(d, { id: "p9", site_bbl: "3052110074", job_type: "alteration", work_types: [],
    members: [{ name: "A", role: "architect" }] });
  const [, items] = calls.addItems[0] as [string, { owner_role: string | null }[]];
  assert.equal(items[0].owner_role, null);
});

test("addProjectItems refuses sample items", async () => {
  const { d, calls } = deps({ actions: async () => ({ data: [item], sample: true }) });
  await assert.rejects(addProjectItems(d, { id: "p9", site_bbl: "3052110074", job_type: "alteration", work_types: [] }), /sample/i);
  assert.equal(calls.addItems.length, 0);
});

test("a project that could not be created adds nothing", async () => {
  const { d, calls } = deps({ create: async () => { throw new Error("this project has no developer"); } });
  await assert.rejects(draftProject(d, input), /no developer/);
  assert.equal(calls.addItems.length, 0);
});

test("items that fail to save keep the project and say so", async () => {
  const { d } = deps({ addItems: async () => { throw new Error("The project could not be reached, so this was not saved."); } });
  const result = await draftProject(d, input);
  assert.equal(result.projectId, "p1");
  assert.match(result.notice ?? "", /could not be reached/);
});

test("passes dig depth, new building height and stage to the checklist and the project", async () => {
  const { d, calls } = deps();
  await draftProject(d, { ...input, jobType: "new_building", depthFt: 20, proposedStoreys: 9, stage: "construction" });
  const [, opts] = calls.actions[0] as [string, Record<string, unknown>];
  assert.equal(opts.depthFt, 20);
  assert.equal(opts.proposedStoreys, 9);
  assert.equal(opts.stage, "construction");
  const body = calls.create[0] as Record<string, unknown>;
  assert.equal(body.excavation_depth_ft, 20);
  assert.equal(body.proposed_storeys, 9);
  assert.equal(body.stage, "construction");
});

test("a dig depth of 'not sure' is left out, not sent as zero", async () => {
  const { d, calls } = deps();
  await draftProject(d, { ...input, depthFt: null });
  const [, opts] = calls.actions[0] as [string, Record<string, unknown>];
  assert.equal("depthFt" in opts, false);
  assert.equal("excavation_depth_ft" in (calls.create[0] as object), false);
});

test("redrawing a saved project uses its saved depth and height", async () => {
  const { d, calls } = deps();
  await addProjectItems(d, { id: "p1", site_bbl: "3015790010", job_type: "new_building", work_types: ["excavation"],
    stage: "design", excavation_depth_ft: 10, proposed_storeys: 6 });
  const [, opts] = calls.actions[0] as [string, Record<string, unknown>];
  assert.equal(opts.depthFt, 10);
  assert.equal(opts.proposedStoreys, 6);
});
