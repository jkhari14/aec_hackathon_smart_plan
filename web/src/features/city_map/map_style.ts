// Paint rules for the city map. Calm by default: clusters in a neutral tone at city zoom, hazard color
// only on single records once you are close enough to read them, severity shown by size and ring.
import type { ExpressionSpecification, Map as MapLibreMap } from "maplibre-gl";

import type { Hazard } from "../../contracts";

export const BASEMAP = "https://tiles.openfreemap.org/styles/dark";
export const NYC_CENTER: [number, number] = [-73.95, 40.7];

// shortcut: placeholder hazard colors until Camilo's design tokens (PR 1) land; swap to the tokens then.
export const HAZARD_COLORS: Record<Hazard, string> = {
  structural: "#e8a33d",
  geotech: "#c08457",
  fire: "#ef6a4c",
  flood: "#4ea8de",
  contamination: "#9b8cff",
  facade: "#d4b483",
  weather: "#7dd3c0",
  construction_safety: "#f2c94c",
};

const SITE = "#f5f7fa";
const NEIGHBOR = "#e8a33d";
const PARTY_WALL = "#ffb547";

// Opacity that grows with zoom, so far-out views stay quiet.
const fadeIn = (from: number, to: number, low: number, high: number): ExpressionSpecification =>
  ["interpolate", ["linear"], ["zoom"], from, low, to, high];

export const sourceId = (layerId: string) => `layer:${layerId}`;
export const pointLayerIds = (layerId: string) => [`${layerId}-clusters`, `${layerId}-count`, `${layerId}-points`];
export const areaLayerIds = (layerId: string) => [`${layerId}-fill`, `${layerId}-outline`];

/** Soft extruded buildings from the basemap's own footprints (heights from OpenStreetMap). */
export function addBuildings(map: MapLibreMap): void {
  // A low, warm key light so facades read as volumes instead of flat blocks.
  map.setLight({ anchor: "map", position: [1.4, 210, 35], color: "#dfe7f2", intensity: 0.35 });
  const firstLabel = map.getStyle().layers.find((l) => l.type === "symbol")?.id;
  map.addLayer(
    {
      id: "buildings-3d",
      type: "fill-extrusion",
      source: "openmaptiles",
      "source-layer": "building",
      minzoom: 14,
      paint: {
        // Taller buildings catch a little more light, which reads as depth without adding color.
        "fill-extrusion-color": ["interpolate", ["linear"], ["coalesce", ["get", "render_height"], 10], 0, "#18212c", 60, "#243243", 200, "#30425a"],
        "fill-extrusion-height": ["coalesce", ["get", "render_height"], 10],
        "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
        "fill-extrusion-opacity": fadeIn(14, 15.5, 0, 0.85),
        "fill-extrusion-vertical-gradient": true,
      },
    },
    firstLabel,
  );
}

/** Clustered points for one layer: neutral clusters, hazard-colored records, size and ring by severity. */
export function addPointLayers(map: MapLibreMap, layerId: string, hazard: Hazard, visible: boolean): void {
  const source = sourceId(layerId);
  const [clusters, count, points] = pointLayerIds(layerId);
  const visibility = visible ? "visible" : "none";
  map.addLayer({
    id: clusters,
    type: "circle",
    source,
    filter: ["has", "point_count"],
    layout: { visibility },
    paint: {
      "circle-color": "#3a4a5f",
      "circle-radius": ["step", ["get", "point_count"], 12, 25, 16, 100, 22, 500, 28],
      "circle-opacity": fadeIn(9, 13, 0.45, 0.75),
      "circle-stroke-color": HAZARD_COLORS[hazard],
      "circle-stroke-width": 1,
      "circle-stroke-opacity": 0.5,
    },
  });
  map.addLayer({
    id: count,
    type: "symbol",
    source,
    filter: ["has", "point_count"],
    layout: {
      visibility,
      "text-field": ["get", "point_count_abbreviated"],
      "text-font": ["Noto Sans Regular"],
      "text-size": 11,
    },
    paint: { "text-color": "#e6edf3" },
  });
  map.addLayer({
    id: points,
    type: "circle",
    source,
    filter: ["!", ["has", "point_count"]],
    layout: { visibility },
    paint: {
      "circle-color": HAZARD_COLORS[hazard],
      "circle-radius": ["match", ["get", "severity"], 3, 9, 2, 7, 1, 5, 4],
      "circle-opacity": fadeIn(10, 14, 0.35, 0.9),
      // A light ring marks incidents and worse, so severity never relies on color alone.
      "circle-stroke-color": "#f5f7fa",
      "circle-stroke-width": ["case", [">=", ["get", "severity"], 2], 1.5, 0],
    },
  });
}

/** Area layers (flood zones, designations): a faint wash with a thin edge. */
export function addAreaLayers(map: MapLibreMap, layerId: string, hazard: Hazard, visible: boolean): void {
  const source = sourceId(layerId);
  const [fill, outline] = areaLayerIds(layerId);
  const visibility = visible ? "visible" : "none";
  const before = map.getLayer("buildings-3d") ? "buildings-3d" : undefined;
  map.addLayer(
    { id: fill, type: "fill", source, layout: { visibility }, paint: { "fill-color": HAZARD_COLORS[hazard], "fill-opacity": 0.12 } },
    before,
  );
  map.addLayer(
    { id: outline, type: "line", source, layout: { visibility }, paint: { "line-color": HAZARD_COLORS[hazard], "line-opacity": 0.4, "line-width": 1 } },
    before,
  );
}

/** The picked site and its touching lots, drawn flat under the buildings with a bright edge. */
export function addSiteLayers(map: MapLibreMap): void {
  map.addSource("site-lots", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  const before = map.getLayer("buildings-3d") ? "buildings-3d" : undefined;
  map.addLayer(
    {
      id: "site-lots-fill",
      type: "fill",
      source: "site-lots",
      paint: {
        "fill-color": ["match", ["get", "role"], "site", SITE, NEIGHBOR],
        "fill-opacity": ["match", ["get", "role"], "site", 0.28, 0.16],
      },
    },
    before,
  );
  map.addLayer({
    id: "site-lots-edge",
    type: "line",
    source: "site-lots",
    paint: {
      "line-color": ["match", ["get", "role"], "site", SITE, NEIGHBOR],
      "line-width": ["match", ["get", "role"], "site", 2.5, 1.5],
      "line-blur": 0.5,
    },
  });
  // The shared party wall: a wide soft glow under a thin bright core.
  map.addSource("party-walls", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addLayer({
    id: "party-walls-glow",
    type: "line",
    source: "party-walls",
    layout: { "line-cap": "round" },
    paint: { "line-color": PARTY_WALL, "line-width": 14, "line-blur": 10, "line-opacity": 0.55 },
  });
  map.addLayer({
    id: "party-walls-core",
    type: "line",
    source: "party-walls",
    layout: { "line-cap": "round" },
    paint: { "line-color": "#fff4d6", "line-width": 2.5 },
  });
}
