// Building colours that mean something for the checklist: the picked site, the attached neighbours the
// party-wall and underpinning items are about, and everything else.

export type BuildingKind = "site" | "attached" | "other";

/** Footprint boxes this close to the site's box (metres) count as attached: touching, give or take a seam. */
export const ATTACHED_M = 1.5;

export const KIND_COLORS: Record<BuildingKind, [number, number, number]> = {
  site: [74, 108, 240], // the accent blue
  attached: [58, 58, 58], // charcoal
  other: [214, 211, 204], // pale grey, like card stock
};

type Box = [number, number, number, number]; // x0, y0, x1, y1 in metres

/** The kind of each building, from footprint boxes and the indexes that make up the site's building. */
export function buildingKinds(boxes: Box[], site: Set<number>): BuildingKind[] {
  const siteBox: Box | null = site.size
    ? [...site].reduce<Box>((u, b) => [Math.min(u[0], boxes[b][0]), Math.min(u[1], boxes[b][1]), Math.max(u[2], boxes[b][2]),
      Math.max(u[3], boxes[b][3])], [Infinity, Infinity, -Infinity, -Infinity])
    : null;
  return boxes.map(([x0, y0, x1, y1], b) => {
    if (site.has(b)) return "site";
    if (!siteBox) return "other";
    const dx = Math.max(0, siteBox[0] - x1, x0 - siteBox[2]);
    const dy = Math.max(0, siteBox[1] - y1, y0 - siteBox[3]);
    return Math.hypot(dx, dy) <= ATTACHED_M ? "attached" : "other";
  });
}
