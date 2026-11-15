// The UI refresh's pure rules: which strands draw, the fly-out bounds, the score ring, building colours by
// kind, and which layers a work type switches on.
import assert from "node:assert/strict";
import { test } from "node:test";

import { shouldApply, layersForWork, WORK_LAYERS } from "../src/app/work_layers.ts";
import { ATTACHED_M, buildingKinds, KIND_COLORS } from "../src/features/city_map/building_kinds.ts";
import { boundsFor, fitPadding, resultsFor, visibleStrands } from "../src/features/city_map/strands.ts";
import { ringDash } from "../src/features/similar_cases/ring.ts";

const results = [{ case_id: "a" }, { case_id: "b" }, { case_id: "c" }];

test("no strands by default, one when a case is focused, all when asked", () => {
  assert.deepEqual(visibleStrands(results, null, false), []);
  assert.deepEqual(visibleStrands(results, "b", false), [{ case_id: "b" }]);
  assert.deepEqual(visibleStrands(results, "b", true), results);
  assert.deepEqual(visibleStrands(results, "zzz", false), []);
});

test("fly-out bounds hold both points, and refuse bad or identical points", () => {
  assert.deepEqual(boundsFor({ lon: -73.9, lat: 40.7 }, { lon: -74.0, lat: 40.8 }), [[-74.0, 40.7], [-73.9, 40.8]]);
  assert.equal(boundsFor({ lon: -73.9, lat: 40.7 }, { lon: Number.NaN, lat: 40.8 }), null);
  assert.equal(boundsFor({ lon: -73.9, lat: 40.7 }, { lon: -73.9, lat: 40.7 }), null);
});

test("the ring draws empty at 0, full at 1, and clamps outside", () => {
  const empty = ringDash(0, 10);
  const full = ringDash(1, 10);
  assert.equal(empty.dash, 0);
  assert.equal(full.dash, full.circumference);
  assert.ok(Math.abs(full.circumference - 2 * Math.PI * 10) < 1e-9);
  assert.equal(ringDash(2, 10).dash, full.circumference);
  assert.equal(ringDash(-1, 10).dash, 0);
  assert.equal(ringDash(Number.NaN, 10).dash, 0);
});

test("buildings touching the site are attached; ones across a gap are not", () => {
  const boxes: [number, number, number, number][] = [
    [-5, -5, 5, 5], // the site
    [5 + ATTACHED_M / 2, -5, 15, 5], // touching, across a hairline gap
    [20, -5, 30, 5], // 15 m away
  ];
  assert.deepEqual(buildingKinds(boxes, new Set([0])), ["site", "attached", "other"]);
  assert.deepEqual(KIND_COLORS.site, [74, 108, 240]);
});

test("work types switch on their layers, only those the catalog has", () => {
  const all = ["construction_incidents", "structural_complaints", "watchlist", "fema_flood_zones", "e_designations",
    "unsafe_facades", "vacate_orders", "sandy_inundation"];
  assert.deepEqual([...layersForWork("demolition", all)].sort(),
    ["construction_incidents", "structural_complaints", "unsafe_facades", "watchlist"]);
  assert.deepEqual([...layersForWork("alteration", ["watchlist"])], ["watchlist"]);
  assert.ok(WORK_LAYERS.new_building.includes("fema_flood_zones"));
});

test("work-type layers apply once per project, so a manual toggle afterwards wins", () => {
  assert.equal(shouldApply(null, "p1:demolition"), true);
  assert.equal(shouldApply("p1:demolition", "p1:demolition"), false);
  assert.equal(shouldApply("p1:demolition", "p2:alteration"), true);
  assert.equal(shouldApply("p1:demolition", null), false);
});

test("fly-out padding leaves room to fit on narrow maps and clears the panels on wide ones", () => {
  const wide = fitPadding(1600, 900);
  assert.equal(wide.left, 340);
  assert.equal(wide.right, 470);
  for (const [w, h] of [[800, 500], [640, 480], [375, 700]]) {
    const p = fitPadding(w, h);
    assert.ok(p.left + p.right <= w * 0.6, `horizontal padding fits ${w}`);
    assert.ok(p.top + p.bottom <= h * 0.6, `vertical padding fits ${h}`);
    assert.ok(p.left >= 0 && p.right >= 0 && p.top >= 0 && p.bottom >= 0);
  }
});

test("similar results belong to the site they were loaded for", () => {
  const loaded = { bbl: "3052110074", results: [{ case_id: "a" }] };
  assert.deepEqual(resultsFor(loaded, "3052110074"), [{ case_id: "a" }]);
  assert.deepEqual(resultsFor(loaded, "1000010001"), []);
  assert.deepEqual(resultsFor(null, "3052110074"), []);
});
