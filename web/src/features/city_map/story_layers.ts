// deck.gl layers that tell the site's story: similar cases arcing in from across the city, and the
// 3D buildings: Cityweft's model of the blocks around the site (through /api/context3d, which holds the
// key), or Google Photorealistic 3D Tiles citywide when VITE_GOOGLE_MAPS_KEY is set, to compare the two.
import type { Layer, PickingInfo } from "@deck.gl/core";
import { ArcLayer, ScatterplotLayer } from "@deck.gl/layers";

import type { SimilarCase } from "../../contracts";
import type { Picked } from "./site_lots";

const ARC_FROM: [number, number, number] = [126, 168, 222];
const ARC_TO: [number, number, number] = [255, 181, 71];

/** Arcs from each similar case to the site. `progress` 0..1 draws them in from the case end. */
export function similarCaseLayers(site: Picked, results: SimilarCase[], progress: number): Layer[] {
  const target: [number, number] = [site.lon, site.lat];
  const toward = (c: SimilarCase): [number, number] => [
    c.case.lon + (target[0] - c.case.lon) * progress,
    c.case.lat + (target[1] - c.case.lat) * progress,
  ];
  return [
    new ArcLayer<SimilarCase>({
      id: "similar-case-arcs",
      data: results,
      getSourcePosition: (c) => [c.case.lon, c.case.lat],
      getTargetPosition: toward,
      getSourceColor: [...ARC_FROM, 200],
      getTargetColor: [...ARC_TO, 230],
      // Closer matches draw a little bolder; the score is similarity, never a prediction.
      getWidth: (c) => 1.5 + 2.5 * c.score,
      getHeight: 0.35,
      greatCircle: false,
      updateTriggers: { getTargetPosition: progress },
    }),
    new ScatterplotLayer<SimilarCase>({
      id: "similar-case-origins",
      data: results,
      getPosition: (c) => [c.case.lon, c.case.lat],
      getFillColor: [...ARC_FROM, 230],
      getLineColor: [245, 247, 250, 255],
      stroked: true,
      lineWidthMinPixels: 1,
      radiusMinPixels: 5,
      radiusMaxPixels: 9,
      getRadius: 60,
      pickable: true,
    }),
  ];
}

/** "Why am I seeing this?" for a similar case: what matched, what differs, and the reported cause. */
export function similarCaseTooltip(info: PickingInfo<SimilarCase>): { text: string } | null {
  const c = info.object;
  if (!c) return null;
  const cause = c.case.cause_status === "reported" && c.case.cause_as_reported
    ? `As publicly reported: ${c.case.cause_as_reported}`
    : c.case.cause_status === "under_investigation" ? "Cause under investigation." : "Cause not reported.";
  return {
    text: [
      `${c.case.title} (${c.case.date})`,
      c.case.address,
      `Matches on: ${c.matched_on.join(", ") || "n/a"}`,
      `Differs on: ${c.differs_on.join(", ") || "n/a"}`,
      cause,
      `Source: ${c.case.sources.map((s) => s.name).join("; ")}`,
    ].join("\n"),
  };
}

type Mesh = { attributes: Record<string, { value: Float32Array; size: number }>; indices: { value: Uint32Array; size: number } };

/** How much of the model to draw: the site and the buildings next to it, or everything Cityweft sent. */
export type ModelScope = "adjacent" | "area";

/** The Cityweft model of the blocks around a site, as /api/context3d packs it (see context3d_router.py). */
export type SiteModel = {
  origin: [number, number];
  attributions: string[];
  /** Buildings drawn in each scope. */
  counts: Record<ModelScope, number>;
  /** The tallest adjacent building, in metres: the camera backs off for towers. */
  tallestNearby: number;
  /** One mesh per scope sharing the same vertices, coloured by height with the site's building in cyan. */
  meshes: Record<ModelScope, Mesh>;
};

/** Buildings within this many metres of the site's own building are "adjacent": the touching ones and
    the ones across a street. */
export const ADJACENT_M = 30;

// Building height (metres) -> colour: deep indigo for low-rise, through violet and rose, to warm gold for towers.
export const HEIGHT_RAMP: [number, [number, number, number]][] = [
  [0, [58, 66, 138]],
  [20, [84, 92, 190]],
  [45, [138, 92, 200]],
  [90, [206, 98, 160]],
  [160, [246, 140, 104]],
  [260, [252, 206, 120]],
];
export const SITE_COLOR: [number, number, number] = [72, 226, 255];

export function heightColor(height: number): [number, number, number] {
  for (let i = 1; i < HEIGHT_RAMP.length; i++) {
    const [h1, c1] = HEIGHT_RAMP[i];
    if (height <= h1) {
      const [h0, c0] = HEIGHT_RAMP[i - 1];
      const t = (height - h0) / (h1 - h0);
      return [0, 1, 2].map((k) => c0[k] + (c1[k] - c0[k]) * t) as [number, number, number];
    }
  }
  return HEIGHT_RAMP[HEIGHT_RAMP.length - 1][1];
}

type Box = [number, number, number, number]; // x0, y0, x1, y1 in metres from the site

/** Colours, the site's building, and which buildings are adjacent to it. */
function analyse(positions: Float32Array, buildings: [number, number, number][]) {
  const boxes: Box[] = buildings.map(([first, count]) => {
    const box: Box = [Infinity, Infinity, -Infinity, -Infinity];
    for (let v = first; v < first + count; v++) {
      const x = positions[3 * v];
      const y = positions[3 * v + 1];
      box[0] = Math.min(box[0], x); box[1] = Math.min(box[1], y); box[2] = Math.max(box[2], x); box[3] = Math.max(box[3], y);
    }
    return box;
  });

  // The site's building: every part whose footprint box holds the picked point and is centred near it
  // (big buildings come in parts, like a tower and its spire). A large L-shaped neighbour whose box only
  // happens to cover the point is centred far off. With no part centred near, the smallest box wins.
  const site = new Set<number>();
  let smallest = -1;
  let smallestArea = Infinity;
  boxes.forEach(([x0, y0, x1, y1], b) => {
    if (!(x0 <= 0 && x1 >= 0 && y0 <= 0 && y1 >= 0)) return;
    const area = (x1 - x0) * (y1 - y0);
    if (area < smallestArea) {
      smallest = b;
      smallestArea = area;
    }
    if (Math.hypot((x0 + x1) / 2, (y0 + y1) / 2) < 30) site.add(b);
  });
  if (site.size === 0 && smallest >= 0) site.add(smallest);

  // Adjacent: footprint boxes within ADJACENT_M of the site's box (or of the picked point, on an empty lot).
  const siteBox: Box = site.size
    ? [...site].reduce<Box>((u, b) => [Math.min(u[0], boxes[b][0]), Math.min(u[1], boxes[b][1]), Math.max(u[2], boxes[b][2]), Math.max(u[3], boxes[b][3])],
      [Infinity, Infinity, -Infinity, -Infinity])
    : [0, 0, 0, 0];
  const adjacent = new Set<number>();
  boxes.forEach(([x0, y0, x1, y1], b) => {
    const dx = Math.max(0, siteBox[0] - x1, x0 - siteBox[2]);
    const dy = Math.max(0, siteBox[1] - y1, y0 - siteBox[3]);
    if (Math.hypot(dx, dy) <= ADJACENT_M) adjacent.add(b);
  });
  return { site, adjacent };
}

/** Fetch and unpack the site model. Throws with the API's reason (no key, Cityweft down) on failure. */
export async function loadSiteModel(site: Picked, signal?: AbortSignal): Promise<SiteModel> {
  const params = new URLSearchParams({ lat: String(site.lat), lon: String(site.lon) });
  const response = await fetch(`/api/context3d?${params}`, { signal });
  if (!response.ok) {
    let reason = `HTTP ${response.status}`;
    try {
      reason = ((await response.json()) as { detail?: string }).detail ?? reason;
    } catch {
      // not JSON: keep the status
    }
    throw new Error(reason);
  }
  const buffer = await response.arrayBuffer();
  const view = new DataView(buffer);
  const length = view.getUint32(0, true);
  const header = JSON.parse(new TextDecoder().decode(new Uint8Array(buffer, 4, length))) as {
    vertex_count: number; index_count: number; building_count: number; origin: [number, number]; attributions: string[];
    buildings?: [number, number, number][];
  };
  const start = 4 + length;
  const positions = new Float32Array(buffer, start, header.vertex_count * 3);
  const indices = new Uint32Array(buffer, start + header.vertex_count * 12, header.index_count);
  // An older cached answer has no per-building list: treat it as one building, coloured by vertex height.
  const buildings = header.buildings ?? [];
  const { site: siteParts, adjacent } = analyse(positions, buildings);

  const colors = new Float32Array(positions.length);
  const owner = new Int32Array(header.vertex_count).fill(-1);
  if (buildings.length === 0) {
    for (let v = 0; v < header.vertex_count; v++) colors.set(heightColor(positions[3 * v + 2]).map((c) => c / 255), 3 * v);
  }
  let tallestNearby = 0;
  buildings.forEach(([first, count, height], b) => {
    const rgb = (siteParts.has(b) ? SITE_COLOR : heightColor(height)).map((c) => c / 255);
    for (let v = first; v < first + count; v++) {
      colors.set(rgb, 3 * v);
      owner[v] = b;
    }
    if (adjacent.has(b)) tallestNearby = Math.max(tallestNearby, height);
  });
  if (buildings.length === 0) tallestNearby = positions.reduce((m, z, i) => (i % 3 === 2 ? Math.max(m, z) : m), 0);

  // The adjacent scope keeps the triangles of adjacent buildings; every triangle lies within one building.
  const near: number[] = [];
  for (let i = 0; i + 2 < indices.length; i += 3) {
    const b = owner[indices[i]];
    if (b < 0 || adjacent.has(b)) near.push(indices[i], indices[i + 1], indices[i + 2]);
  }
  const attributes = { positions: { value: positions, size: 3 }, colors: { value: colors, size: 3 } };
  return {
    tallestNearby,
    origin: header.origin,
    attributions: header.attributions,
    counts: { adjacent: buildings.length ? adjacent.size : header.building_count, area: header.building_count },
    meshes: {
      adjacent: { attributes, indices: { value: Uint32Array.from(near), size: 1 } },
      area: { attributes, indices: { value: indices, size: 1 } },
    },
  };
}

type MeshLayers = typeof import("@deck.gl/mesh-layers");

/** deck.gl's mesh layers, loaded on first use so the default bundle stays small. */
export const loadMeshLayers = (): Promise<MeshLayers> => import("@deck.gl/mesh-layers");

/** The site model as one lit mesh, metres east, north and up from the site. `rise` 0..1 grows it out of the ground. */
export function siteModelLayer({ SimpleMeshLayer }: MeshLayers, model: SiteModel, scope: ModelScope, rise = 1): Layer {
  const [lat, lon] = model.origin;
  return new SimpleMeshLayer<{ position: [number, number, number] }>({
    id: `cityweft-site-model-${scope}`,
    data: [{ position: [lon, lat, 0] }],
    mesh: model.meshes[scope],
    getPosition: (d) => d.position,
    getColor: [255, 255, 255, 255],
    getScale: [1, 1, Math.max(rise, 0.001)],
    updateTriggers: { getScale: rise },
    material: { ambient: 0.42, diffuse: 0.6, shininess: 24, specularColor: [70, 70, 80] },
    pickable: false,
  });
}

export const GOOGLE_KEY: string | undefined = import.meta.env.VITE_GOOGLE_MAPS_KEY;

/** Google Photorealistic 3D Tiles, loaded only when picked so the default bundle stays small. */
export async function googleTiles(key: string, onCredits: (credits: string) => void): Promise<Layer> {
  const { Tile3DLayer } = await import("@deck.gl/geo-layers");
  return new Tile3DLayer({
    id: "google-3d-tiles",
    data: "https://tile.googleapis.com/v1/3dtiles/root.json",
    loadOptions: { fetch: { headers: { "X-GOOG-API-KEY": key } } },
    operation: "terrain+draw",
    // Google requires showing the data providers for the tiles on screen.
    onTilesetLoad: (tileset) => {
      tileset.options.onTraversalComplete = (selected) => {
        const credits = new Set<string>();
        for (const tile of selected) {
          const copyright = (tile.content as { gltf?: { asset?: { copyright?: string } } })?.gltf?.asset?.copyright;
          copyright?.split(";").forEach((c) => credits.add(c.trim()));
        }
        onCredits([...credits].filter(Boolean).join("; "));
        return selected;
      };
    },
  });
}
