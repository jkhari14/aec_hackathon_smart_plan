// "New for you": items another role's document added to this role's list since it last looked.
import assert from "node:assert/strict";
import { test } from "node:test";

import { addedLine, newForRole } from "../src/features/project_screen/model.ts";

const item = (id: string, extra: Record<string, unknown> = {}) => ({
  id, discipline: "structural", hazard: "structural", title: id, why: "", status: "open", owner_role: "architect",
  source_rule: "r", life_safety: false, ...extra,
}) as never;

const LABELS = { architect: "Architect", structural_engineer: "Structural engineer", developer: "Developer", contractor: "Contractor" };
const SE = { added_by_role: "structural_engineer", added_reason: "Added because the structural engineer uploaded S-101" };

test("only items another role added to mine after I looked are new", () => {
  const items = [
    item("drafted"), // from the site's rules: no provenance, never new
    item("before", { ...SE, added_at: "2026-11-15T10:00:00+00:00" }),
    item("after", { ...SE, added_at: "2026-11-15T12:00:00+00:00" }),
    item("not-mine", { ...SE, owner_role: "contractor", added_at: "2026-11-15T12:00:00+00:00" }),
    item("my-own", { added_by_role: "architect", added_reason: "x", added_at: "2026-11-15T12:00:00+00:00" }),
  ];
  assert.deepEqual(newForRole(items, "architect", "2026-11-15T11:00:00Z").map((i: { id: string }) => i.id), ["after"]);
});

test("with no mark, everything another role added to my list is new", () => {
  const items = [item("a", { ...SE, added_at: "2026-11-15T10:00:00+00:00" }), item("b")];
  assert.equal(newForRole(items, "architect", null).length, 1);
});

test("the provenance line names the role and the time", () => {
  const line = addedLine({ added_by_role: "structural_engineer", added_at: "2026-11-15T12:05:00+00:00" } as never, LABELS);
  assert.match(line ?? "", /^Structural engineer · Nov 15/);
  assert.equal(addedLine({ added_by_role: null, added_at: null } as never, LABELS), null);
});
