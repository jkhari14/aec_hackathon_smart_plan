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
