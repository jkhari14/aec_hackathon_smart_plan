// "What we already know about this lot": the setup card's lines, each with its source; nothing invented.
import assert from "node:assert/strict";
import { test } from "node:test";

import { knownFacts } from "../src/features/project_screen/known_facts.ts";

const neighbor = (bbl: string, year: number, floors: number, attached = true) =>
  ({ bbl, bins: [], attached, year_built: year, floors }) as never;

const profile = {
  bbl: "3015790010", bins: [], address_matched: "861 PARK AVENUE", lat: 0, lon: 0,
  lot: { lot_area_sqft: 8000 },
  neighbors: [neighbor("1", 1910, 2), neighbor("2", 1931, 3), neighbor("3", 1925, 3), neighbor("4", 1931, 2),
    neighbor("5", 1920, 3), neighbor("6", 1950, 6, false)],
  job_type: "new_building", work_types: [], work_types_inferred: true,
  flood: { fema_zone: "X" }, e_designation: null, signals: [], datasets: [],
} as never;

const line = (label: string) => knownFacts(profile).find((f) => f.label === label);

test("neighbors: how many are attached, when they were built, how tall", () => {
  assert.deepEqual(line("Neighbors"), {
    label: "Neighbors", value: "5 attached, built 1910–1931, 2–3 storeys", source: "PLUTO and building footprints",
  });
});

test("flood zone with its source", () => {
  assert.deepEqual(line("Flood zone"), { label: "Flood zone", value: "Zone X", source: "FEMA flood maps" });
});

test("lot size", () => {
  assert.equal(line("Lot size")?.value, "8,000 sq ft");
});

test("the filed job when the records name it", () => {
  assert.deepEqual(line("Filed with DOB"), { label: "Filed with DOB", value: "New building", source: "DOB NOW filings" });
});

test("an e-designation line only when there is one", () => {
  assert.equal(line("E-designation"), undefined);
  const flagged = knownFacts({ ...(profile as object), e_designation: "E-123" } as never);
  assert.equal(flagged.find((f) => f.label === "E-designation")?.value, "E-123");
});

test("a profile that couldn't load leaves every line empty, not invented", () => {
  const lines = knownFacts(null);
  assert.ok(lines.length >= 3);
  assert.ok(lines.every((f) => f.value === null));
});

test("a fact the profile doesn't check says 'not checked', not 'couldn't load'", () => {
  const flood = knownFacts({ ...(profile as object), flood: { fema_zone: null } } as never).find((f) => f.label === "Flood zone");
  assert.equal(flood?.value, null);
  assert.equal(flood?.missing, "not checked for this lot");
  assert.equal(knownFacts(null).find((f) => f.label === "Flood zone")?.missing, undefined);
});
