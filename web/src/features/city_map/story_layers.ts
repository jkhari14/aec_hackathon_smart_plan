// deck.gl layers that tell the site's story: similar cases arcing in from across the city, and Google
// Photorealistic 3D Tiles when VITE_GOOGLE_MAPS_KEY is set.
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

export const GOOGLE_KEY: string | undefined = import.meta.env.VITE_GOOGLE_MAPS_KEY;

/** Google Photorealistic 3D Tiles, loaded only when a key is set so the default bundle stays small. */
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
