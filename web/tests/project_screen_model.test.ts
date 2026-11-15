// The project screen's pure rules: card values, default scope, owners, grouping and document slots.
// Run: node --test web/tests/   (Node 22.6+ strips the types; no test runner dependency needed.)
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  asksDepth, currentMilestone, itemNumbers, milestoneSummary, MILESTONES, phaseOf, CONSTRUCTION_CARDS, DEPTH_BANDS, DOC_SLOTS, defaultScope, STAGE_OPTIONS, groupByOwner, ownerFor, ROLES, scopeValues, SCOPE_OPTIONS, withOwners,
  WORK_TYPE_CARDS,
} from "../src/features/project_screen/model.ts";

const item = (id: string, discipline: string, extra: Record<string, unknown> = {}) => ({
  id, discipline, hazard: "structural", title: id, why: "", status: "open", owner_role: null,
  source_rule: "r", life_safety: false, ...extra,
}) as never;

test("work type cards map to the contract job types", () => {
  assert.deepEqual(WORK_TYPE_CARDS.map((c) => [c.label, c.value]), [
    ["New construction", "new_building"],
    ["Modification to existing structure", "alteration"],
    ["Demolition", "demolition"],
  ]);
});

test("construction cards carry the five construction types", () => {
  assert.deepEqual(CONSTRUCTION_CARDS.map((c) => [c.value, c.label]), [
    ["wood", "Wood frame"], ["masonry", "Masonry"], ["steel", "Steel"], ["concrete", "Concrete"], ["unknown", "Not sure"],
  ]);
});

test("default scope follows the job type and only offers scope options", () => {
  assert.deepEqual(defaultScope("new_building"), ["excavation", "foundation", "support_of_excavation", "structural", "scaffold"]);
  assert.deepEqual(defaultScope("alteration"), ["structural", "scaffold"]);
  assert.deepEqual(defaultScope("demolition"), ["scaffold"]);
  const offered = new Set(SCOPE_OPTIONS.map((o) => o.value));
  for (const job of ["new_building", "alteration", "demolition"] as const) {
    for (const w of defaultScope(job)) assert.ok(offered.has(w), w);
  }
});

test("scopeValues keeps the job's other work, swaps in the picked scope, and ties earth_work to digging", () => {
  assert.deepEqual(scopeValues("alteration", ["structural", "scaffold"]),
    ["structural", "sprinkler", "plumbing", "mechanical", "sidewalk_shed", "scaffold"]);
  assert.deepEqual(scopeValues("alteration", ["structural"]), ["structural", "sprinkler", "plumbing", "mechanical"]);
  assert.deepEqual(scopeValues("alteration", ["excavation"]), ["earth_work", "excavation", "sprinkler", "plumbing", "mechanical"]);
  assert.deepEqual(scopeValues("new_building", ["excavation"]),
    ["earth_work", "excavation", "sprinkler", "standpipe", "plumbing", "mechanical", "construction_fence"]);
  assert.deepEqual(scopeValues("demolition", []), ["demolition", "construction_fence"]);
});

test("roles are in the screen's order", () => {
  assert.deepEqual(ROLES, ["architect", "structural_engineer", "developer", "contractor"]);
});

test("owners follow the discipline; geotech goes to the structural engineer", () => {
  assert.equal(ownerFor("architect"), "architect");
  assert.equal(ownerFor("structural"), "structural_engineer");
  assert.equal(ownerFor("geotech"), "structural_engineer");
  assert.equal(ownerFor("contractor"), "contractor");
});

test("withOwners fills only missing owners", () => {
  const out = withOwners([item("a", "geotech"), item("b", "architect", { owner_role: "developer" })]) as { owner_role: string }[];
  assert.deepEqual(out.map((i) => i.owner_role), ["structural_engineer", "developer"]);
});

test("withOwners leaves an item unassigned when its role is not on the project", () => {
  const out = withOwners([item("a", "geotech"), item("b", "architect")], ["architect", "contractor"]) as { owner_role: string | null }[];
  assert.deepEqual(out.map((i) => i.owner_role), [null, "architect"]);
});

test("groupByOwner keeps role order, puts unassigned last and life safety first", () => {
  const groups = groupByOwner([
    item("x", "contractor", { owner_role: "contractor" }),
    item("y", "architect", { owner_role: "architect" }),
    item("z", "architect", { owner_role: "architect", life_safety: true }),
    item("u", "geotech"),
  ]) as { role: string | null; items: { id: string }[] }[];
  assert.deepEqual(groups.map((g) => g.role), ["architect", "contractor", null]);
  assert.deepEqual(groups[0].items.map((i) => i.id), ["z", "y"]);
});

test("document slots show only when the work makes them relevant", () => {
  const shown = (job: never, scope: string[]) => DOC_SLOTS.filter((s) => s.relevant(job, scope as never)).map((s) => s.id);
  assert.deepEqual(shown("new_building" as never, ["excavation", "support_of_excavation"]),
    ["survey", "architectural", "geotech", "soe", "neighbor_survey"]);
  assert.deepEqual(shown("alteration" as never, ["structural"]), ["survey", "architectural", "structural"]);
  assert.deepEqual(shown("demolition" as never, []), ["survey", "architectural", "demolition"]);
  assert.deepEqual(shown(null as never, []), ["survey", "architectural"]);
});

test("attached neighbours alone bring the neighbour survey slot", () => {
  const slot = DOC_SLOTS.find((s) => s.id === "neighbor_survey")!;
  assert.equal(slot.relevant("alteration" as never, ["structural"] as never, { attached: true }), true);
  assert.equal(slot.relevant("alteration" as never, ["structural"] as never, { attached: false }), false);
  assert.equal(slot.relevant("alteration" as never, ["structural"] as never), false);
});

test("dig depth bands send their deepest depth, and 'not sure' sends nothing", () => {
  assert.deepEqual(DEPTH_BANDS.map((b) => b.feet), [null, 4.9, 10, 20, 21]);
  assert.equal(DEPTH_BANDS[0].label, "Not sure");
});

test("stage options are design, filing and construction", () => {
  assert.deepEqual(STAGE_OPTIONS.map((s) => s.value), ["design", "pre_filing", "construction"]);
  assert.deepEqual(STAGE_OPTIONS.map((s) => s.label), ["Design", "Filing", "Construction"]);
});

test("the depth question shows for any job that digs, underpinning-only included", () => {
  assert.equal(asksDepth("alteration", ["underpinning"]), true);
  assert.equal(asksDepth("new_building", ["support_of_excavation"]), true);
  assert.equal(asksDepth("alteration", ["structural", "facade"]), false);
});

test("items are numbered by owner group: A for architect, S for structural engineer", () => {
  const groups = [
    { role: "architect" as const, items: [item("a1", "architect"), item("a2", "architect")] },
    { role: "structural_engineer" as const, items: [item("s1", "structural")] },
    { role: null, items: [item("u1", "contractor")] },
  ];
  const n = itemNumbers(groups as never);
  assert.deepEqual([n.get("a1"), n.get("a2"), n.get("s1"), n.get("u1")], ["A1", "A2", "S1", "U1"]);
});

test("an item saved before phases existed is placed in Design", () => {
  assert.equal(phaseOf(item("x", "architect") as never), "design");
  assert.equal(phaseOf(item("y", "architect", { phase: "notice" }) as never), "notice");
});

test("milestones run in project order", () => {
  assert.deepEqual(MILESTONES.map((m) => m.phase), ["design", "filing", "notice", "before_excavation", "during_work"]);
});

test("each milestone counts its items, how many are done, and whether any is life safety", () => {
  const items = [
    item("a", "architect", { phase: "notice", status: "done", life_safety: false }),
    item("b", "architect", { phase: "notice", status: "open", life_safety: true }),
    item("c", "architect", { status: "open", life_safety: false }),
  ];
  const byPhase = Object.fromEntries(milestoneSummary(items as never).map((m) => [m.phase, m]));
  assert.deepEqual(byPhase.notice, { phase: "notice", total: 2, done: 1, lifeSafety: true });
  assert.deepEqual(byPhase.design, { phase: "design", total: 1, done: 0, lifeSafety: false });
  assert.deepEqual(byPhase.filing, { phase: "filing", total: 0, done: 0, lifeSafety: false });
});

test("the project's stage marks where it is on the timeline", () => {
  assert.equal(currentMilestone("design"), "design");
  assert.equal(currentMilestone("pre_filing"), "filing");
  assert.equal(currentMilestone("construction"), "during_work");
  assert.equal(currentMilestone("pre_acquisition"), "design");
});
