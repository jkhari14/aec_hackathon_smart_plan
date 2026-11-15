# UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Light "paper" look by default, one strand at a time with a fly-out, similarity rings, lighter case cards, meaningful building colours, tidier controls, and layers that follow the work type.

**Architecture:** Pure rules go in new React-free modules tested with `node:test`: `strands.ts`, `building_kinds.ts`, `ring.ts`, `work_layers.ts`. The UI wires them in. Focus state (`focusCase`, `allStrands`) lives in `App` and flows to the map and the similar-case list.

**Tech Stack:** React 19 + TS, MapLibre 6, deck.gl 9, Node test runner.

**Spec:** `docs/superpowers/specs/2026-11-14-ui-refresh-design.md`

## Global Constraints

- No new npm dependencies. Fonts via Google Fonts `<link>` in `web/index.html`: Space Grotesk 400/500/600/700, Silkscreen 400.
- Palette values exactly as the spec's table. Accent `#4A6CF0`.
- Light is the default theme. Dark stays behind the toggle.
- Do not change similarity scoring, chat or the project-screen logic.
- Reduced motion: the fly-out uses `jumpTo` / `fitBounds` with `duration: 0`.
- The similarity number is always labelled "similar", never a probability.

## Review Focus

1. **A focused case with no lat/lon, or at the site itself:** no fly-out to NaN; the strand is skipped and the card still toggles. (Task 1: `boundsFor` test.)
2. **Theme toggle while a site is picked:** custom map layers (site lots, layers, selection) survive the basemap swap. (Task 6: browser check.)
3. **Manual layer toggles after work-type defaults applied:** they are not overwritten on the next render. (Task 2: `shouldApply` test.)
4. **Score 0 or 1:** the ring draws an empty or full circle, with no NaN dash. (Task 1: ring test.)
5. **Picking a different site while a case is focused:** the focus clears, so the strand never points from the old case to the new site. (Task 5: App effect, browser check.)

---

### Task 1: Pure rules (strands, ring, building kinds)

**Files:**
- Create: `web/src/features/city_map/strands.ts`, `web/src/features/city_map/building_kinds.ts`, `web/src/features/similar_cases/ring.ts`
- Test: `web/tests/ui_refresh.test.ts`

**Interfaces:**
- `visibleStrands<T extends { case_id: string }>(results: T[], focusId: string | null, showAll: boolean): T[]`: all of them if `showAll`, else only the focused one, else `[]`.
- `boundsFor(site: {lon:number;lat:number}, c: {lon:number;lat:number}): [[number,number],[number,number]] | null`: `null` if any value is non-finite or both points are equal.
- `ringDash(score: number, r: number): { circumference: number; dash: number }`: score clamped to 0..1.
- `type BuildingKind = "site" | "attached" | "other"`; `ATTACHED_M = 1.5`.
- `buildingKinds(boxes: [number,number,number,number][], site: Set<number>): BuildingKind[]`: "attached" when the box-to-site-box gap is ≤ `ATTACHED_M`.
- `KIND_COLORS: Record<BuildingKind, [number,number,number]>`: site `[74,108,240]`, attached `[58,58,58]`, other `[214,211,204]`.

- [ ] Write the tests: three cases for `visibleStrands`; `boundsFor` returns `[[min lon, min lat],[max lon, max lat]]` and is null for NaN or identical points; `ringDash(0,10).dash===0`, `ringDash(1,10).dash===circumference`, `ringDash(2,10)` is clamped; `buildingKinds` with a touching box marks it attached, with a box 5 m away marks it other, and the site index marks it site.
- [ ] Run `npm test`: FAIL (modules missing).
- [ ] Implement. Run `npm test` and `npx tsc --noEmit`: PASS.
- [ ] Commit `feat(ui): strand, ring and building-kind rules`.

### Task 2: Layers by work type

**Files:** Create `web/src/app/work_layers.ts`. Test: same test file.

**Interfaces:**
- `WORK_LAYERS: Record<JobType, string[]>`, exactly the spec table (ids: `construction_incidents`, `structural_complaints`, `watchlist`, `fema_flood_zones`, `e_designations`, `unsafe_facades`, `vacate_orders`).
- `layersForWork(job: JobType, available: string[]): Set<string>`: the intersection.
- `shouldApply(lastApplied: string | null, key: string | null): boolean`: true only when `key` is non-null and differs (key = `${projectId}:${job}`).

- [ ] Tests, RED, implement, GREEN, commit `feat(ui): layers follow the work type`.

### Task 3: Light paper theme by default

**Files:** `web/src/design/tokens.css` (light block values, plus `--fs-font`, `--fs-pixel`, `--fs-grid`), `web/src/app/preferences.ts` (default light), `web/index.html` (fonts), `web/src/design/components.css` (`.fs-label` uses `--fs-pixel`), `web/src/features/city_map/city_map.css` (popup uses tokens), `web/src/features/project_screen/project_screen.css` (grid paper on `.fs-ps`).
- [ ] Apply the palette, check typecheck and build, then check the screen in the browser.
- [ ] Commit `feat(ui): light paper theme by default`.

### Task 4: Map follows the theme, with new building colours

**Files:** `web/src/features/city_map/map_style.ts` (`basemapFor(theme)`, `mapColors(theme)`, building colour), `CityMap.tsx` (`theme` prop; on change `map.setStyle(basemapFor(theme), { transformStyle })` keeping custom sources and layers; re-apply colours), `story_layers.ts` (colour by `buildingKinds`/`KIND_COLORS` instead of `heightColor`; remove `HEIGHT_RAMP`, `heightColor`; the "Show" scope buttons stay without the height legend), `selection_blink.ts` (`SELECTION_COLOR` = accent).
- [ ] Implement. Browser: light map, blue site, charcoal neighbours; toggle the theme with a site picked and the layers survive (Review Focus #2).
- [ ] Commit `feat(map): light basemap, buildings coloured by site and attached neighbours`.

### Task 5: One strand at a time, with fly-out

**Files:** `App.tsx` (state `focusCase: string|null`, `allStrands: boolean`; clear focus on site change), `slots.tsx` → `SitePanel.tsx` → `SimilarCases.tsx` (props `focusedId`, `onFocus(id)`, `allStrands`, `onAllStrands`), `CityMap.tsx` (props `focusCaseId`, `showAllStrands`, `onFocusCase`; draw `visibleStrands`; on focus, `fitBounds(boundsFor(...), { padding: 120, pitch: 45, duration: 1600 })`; highlight the case building by `queryRenderedFeatures` on `buildings-3d` at the case point after `moveend`, put into a geojson source `case-building` with an accent `fill-extrusion`, falling back to the ring marker), `story_layers.ts` (arcs in accent; the origin dot for the focused case is larger, with a ring).
- [ ] Implement. Browser: click a card → zoom-out showing both, one strand; click again → clears; "Show all strands" → all.
- [ ] Commit `feat(map): click a similar case to see it and your site joined by one strand`.

### Task 6: Ring and lighter case cards; controls

**Files:** `SimilarCases.tsx` + `similar_cases.css` (`ScoreRing` with an SVG circle using `ringDash`; card layout per the spec: ring, title, date, one meta line, up to 3 ✓ and 2 ✗ chips, "+N more" folded; whole card is a button toggling focus with `aria-pressed`), `CameraControls.tsx` (2D/3D button; remove `ViewModeControl` from CityMap, keep the pitchend blink), `App.tsx` (Layers button with a "Layers · N" label; apply `layersForWork` when returning from a project with a job type, guarded by `shouldApply`).
- [ ] Implement. Browser: ring at 0 / mid / 100; no control left at the bottom right except chat; Layers label count; return from a demolition project and the demolition layers are on; toggle one off and it stays off.
- [ ] Commit `feat(ui): similarity ring, lighter case cards, 2D in camera controls, labelled layers`.

### Task 7: Final checks

- [ ] `.venv/bin/python -m unittest discover -s tests -t .`, `cd web && npx tsc --noEmit && npm test && npm run build`.
- [ ] Browser pass: light and dark, phone width, reduced motion.
