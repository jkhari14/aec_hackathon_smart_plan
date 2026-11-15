// "What could go wrong here": narrowing lessons by option, then by scope.
import assert from "node:assert/strict";
import { test } from "node:test";

import { filterLessons, OPTIONS, scopeChoices, setupFor } from "../src/features/lessons/model.ts";

const lesson = (id: string, options: string[], scopes: string[]) => ({ id, options, scopes }) as never;
const all = [
  lesson("undermined", ["renovate", "demolish_rebuild", "new_build"], ["excavation", "underpinning"]),
  lesson("bearing", ["renovate"], ["structural", "facade"]),
  lesson("crane", ["demolish_rebuild", "new_build"], ["structural"]),
];
const ids = (xs: { id: string }[]) => xs.map((x) => x.id);

test("all options shows every lesson", () => {
  assert.deepEqual(ids(filterLessons(all, "all", [])), ["undermined", "bearing", "crane"]);
});

test("an option keeps only the lessons that apply to it", () => {
  assert.deepEqual(ids(filterLessons(all, "renovate", [])), ["undermined", "bearing"]);
  assert.deepEqual(ids(filterLessons(all, "new_build", [])), ["undermined", "crane"]);
});

test("scopes narrow further: a lesson stays if it shares any picked scope", () => {
  assert.deepEqual(ids(filterLessons(all, "all", ["structural"])), ["bearing", "crane"]);
  assert.deepEqual(ids(filterLessons(all, "renovate", ["excavation"])), ["undermined"]);
});

test("scope chips come from the lessons the option leaves", () => {
  assert.deepEqual(scopeChoices(all, "new_build"), ["excavation", "underpinning", "structural"]);
});

test("options run all, renovate, demolish and rebuild, new build", () => {
  assert.deepEqual(OPTIONS.map((o) => o.value), ["all", "renovate", "demolish_rebuild", "new_build"]);
});

test("starting a project carries the option and scopes into setup", () => {
  assert.deepEqual(setupFor("renovate", ["structural"]), { jobType: "alteration", scope: ["structural"] });
  assert.deepEqual(setupFor("demolish_rebuild", []), { jobType: "new_building", scope: ["demolition"] });
  assert.deepEqual(setupFor("new_build", ["excavation"]), { jobType: "new_building", scope: ["excavation"] });
  assert.equal(setupFor("all", []), null);
});
