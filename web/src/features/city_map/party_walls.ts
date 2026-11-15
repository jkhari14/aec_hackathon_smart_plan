// Where the site's lot line runs along a neighbor's: the shared (party) wall, drawn as a glowing edge.
// Type-only imports, so Node can run this file directly for tests/test_party_walls.py.
import type { Feature, LineString, MultiPolygon, Polygon, Position } from "geojson";

const TOLERANCE_M = 0.6; // lot polygons from different digitizing passes rarely share exact vertices

function rings(geometry: Polygon | MultiPolygon): Position[][] {
  return geometry.type === "Polygon" ? geometry.coordinates : geometry.coordinates.flat();
}

function segmentDistance(p: number[], a: number[], b: number[]): number {
  const [dx, dy] = [b[0] - a[0], b[1] - a[1]];
  const len2 = dx * dx + dy * dy;
  const t = len2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2));
  return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}

/** Site edges whose both ends (and midpoint) lie on a neighbor's boundary, one LineString per neighbor. */
export function partyWalls(
  site: Polygon | MultiPolygon,
  neighbors: { bbl: string; geometry: Polygon | MultiPolygon }[],
): Feature<LineString, { bbl: string; length_m: number }>[] {
  const origin = rings(site)[0][0];
  const kx = 111320 * Math.cos((origin[1] * Math.PI) / 180);
  const toM = (p: Position) => [(p[0] - origin[0]) * kx, (p[1] - origin[1]) * 110540];
  const siteRings = rings(site);
  const out: Feature<LineString, { bbl: string; length_m: number }>[] = [];
  for (const n of neighbors) {
    const edges = rings(n.geometry).flatMap((r) => r.slice(1).map((p, i) => [toM(r[i]), toM(p)]));
    const onNeighbor = (p: number[]) => edges.some(([a, b]) => segmentDistance(p, a, b) <= TOLERANCE_M);
    const shared: Position[][] = [];
    let length = 0;
    for (const ring of siteRings) {
      for (let i = 0; i < ring.length - 1; i++) {
        const [a, b] = [toM(ring[i]), toM(ring[i + 1])];
        const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
        if (onNeighbor(a) && onNeighbor(b) && onNeighbor(mid)) {
          shared.push([ring[i], ring[i + 1]]);
          length += Math.hypot(b[0] - a[0], b[1] - a[1]);
        }
      }
    }
    for (const coordinates of shared) {
      out.push({ type: "Feature", geometry: { type: "LineString", coordinates }, properties: { bbl: n.bbl, length_m: length } });
    }
  }
  return out;
}
