// Strands join a similar case to the picked site. One at a time tells one story: none are drawn until a
// case is focused, then only that one, unless "Show all strands" is on.

export function visibleStrands<T extends { case_id: string }>(results: T[], focusId: string | null, showAll: boolean): T[] {
  if (showAll) return results;
  if (!focusId) return [];
  return results.filter((r) => r.case_id === focusId);
}

type Point = { lon: number; lat: number };

/** [[west, south], [east, north]] around the site and the case, or null when there is nothing to frame. */
export function boundsFor(site: Point, other: Point): [[number, number], [number, number]] | null {
  const values = [site.lon, site.lat, other.lon, other.lat];
  if (!values.every(Number.isFinite)) return null;
  if (site.lon === other.lon && site.lat === other.lat) return null;
  return [
    [Math.min(site.lon, other.lon), Math.min(site.lat, other.lat)],
    [Math.max(site.lon, other.lon), Math.max(site.lat, other.lat)],
  ];
}

export type Padding = { top: number; bottom: number; left: number; right: number };

// Clear of the camera controls (left), the site panel (right), the search bar and the bottom bar.
const FULL: Padding = { top: 110, bottom: 200, left: 340, right: 470 };

/** Fly-out padding for a map this size: the full margins when they fit, shrunk evenly when they don't, so
    the two places always land on screen (padding wider than the map makes MapLibre refuse to move). */
export function fitPadding(width: number, height: number): Padding {
  const scale = Math.min(1, (0.6 * width) / (FULL.left + FULL.right), (0.6 * height) / (FULL.top + FULL.bottom));
  const k = Math.max(0, scale);
  return { top: FULL.top * k, bottom: FULL.bottom * k, left: FULL.left * k, right: FULL.right * k };
}

/** Similar results are kept with the site they were loaded for; a different site gets none of them. */
export function resultsFor<T>(loaded: { bbl: string; results: T[] } | null, bbl: string | null): T[] {
  return loaded && bbl && loaded.bbl === bbl ? loaded.results : [];
}
