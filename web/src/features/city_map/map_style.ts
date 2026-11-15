// Paint rules for the city map. Calm by default: clusters in a neutral tone at city zoom, hazard color
// only on single records once you are close enough to read them, severity shown by size and ring.
import type { ExpressionSpecification, Map as MapLibreMap } from "maplibre-gl";

import type { Hazard } from "../../contracts";

export type MapTheme = "light" | "dark";

/** The page's theme, as the shell sets it on <html>. Light is the default. */
export const themeNow = (): MapTheme => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

/** The basemap follows the theme: OpenFreeMap's Positron on paper, its dark style at night. */
export const basemapFor = (theme: MapTheme) =>
  `https://tiles.openfreemap.org/styles/${theme === "light" ? "positron" : "dark"}`;

/** The map's own colours per theme. Light is the 4site paper palette: ink, card stock and one blue. */
const PALETTE = {
  light: {
    buildings: ["#ebe9e3", "#dad7d0", "#c9c5bc"],
    cluster: "#ffffff",
    clusterText: "#141414",
    ring: "#141414",
    site: "#4a6cf0",
    neighbor: "#3a3a3a",
    partyWall: "#4a6cf0",
    partyWallCore: "#1f3fb8",
    light: "#ffffff",
    // Water (the basemap's rivers, bay and creeks): a pale cyan.
    water: "#e1f0f2",
  },
  dark: {
    buildings: ["#18212c", "#243243", "#30425a"],
    cluster: "#3a4a5f",
    clusterText: "#e6edf3",
    ring: "#f5f7fa",
    site: "#f5f7fa",
    neighbor: "#e8a33d",
    partyWall: "#ffb547",
    partyWallCore: "#fff4d6",
    light: "#dfe7f2",
    // The dark basemap keeps its own water: a pale cyan would glare against it.
    water: null,
  },
} as const;
const palette = (theme: MapTheme = themeNow()) => PALETTE[theme];

const buildingColor = (theme?: MapTheme): ExpressionSpecification => {
  const [low, mid, high] = palette(theme).buildings;
  return ["interpolate", ["linear"], ["coalesce", ["get", "render_height"], 10], 0, low, 60, mid, 200, high];
};
const roleColor = (theme?: MapTheme): ExpressionSpecification =>
  ["match", ["get", "role"], "site", palette(theme).site, palette(theme).neighbor];

/** Repaint everything this file drew, for a theme switch. Layers that are not on the map are skipped. */
export function applyMapPalette(map: MapLibreMap, theme: MapTheme, layerIds: string[]): void {
  const p = palette(theme);
  const set = (id: string, prop: string, value: unknown) => {
    if (map.getLayer(id)) map.setPaintProperty(id, prop as never, value as never);
  };
  map.setLight({ anchor: "map", position: [1.4, 210, 35], color: p.light, intensity: 0.35 });
  if (p.water) {
    set("water", "fill-color", p.water);
    set("waterway", "line-color", p.water);
  }
  set("buildings-3d", "fill-extrusion-color", buildingColor(theme));
  set("site-lots-fill", "fill-color", roleColor(theme));
  set("site-lots-edge", "line-color", roleColor(theme));
  set("party-walls-glow", "line-color", p.partyWall);
  set("party-walls-core", "line-color", p.partyWallCore);
  for (const layerId of layerIds) {
    const [clusters, count, points] = pointLayerIds(layerId);
    set(clusters, "circle-color", p.cluster);
    set(count, "text-color", p.clusterText);
    set(points, "circle-stroke-color", p.ring);
  }
}
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


// Opacity that grows with zoom, so far-out views stay quiet.
const fadeIn = (from: number, to: number, low: number, high: number): ExpressionSpecification =>
  ["interpolate", ["linear"], ["zoom"], from, low, to, high];

export const sourceId = (layerId: string) => `layer:${layerId}`;
export const pointLayerIds = (layerId: string) => [`${layerId}-clusters`, `${layerId}-count`, `${layerId}-points`];
export const areaLayerIds = (layerId: string) => [`${layerId}-fill`, `${layerId}-outline`];

/** Soft extruded buildings from the basemap's own footprints (heights from OpenStreetMap). */
export function addBuildings(map: MapLibreMap): void {
  // A low, warm key light so facades read as volumes instead of flat blocks.
  map.setLight({ anchor: "map", position: [1.4, 210, 35], color: palette().light, intensity: 0.35 });
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
        "fill-extrusion-color": buildingColor(),
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
      "circle-color": palette().cluster,
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
    paint: { "text-color": palette().clusterText },
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
      "circle-stroke-color": palette().ring,
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
        "fill-color": roleColor(),
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
      "line-color": roleColor(),
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
    paint: { "line-color": palette().partyWall, "line-width": 14, "line-blur": 10, "line-opacity": 0.55 },
  });
  map.addLayer({
    id: "party-walls-core",
    type: "line",
    source: "party-walls",
    layout: { "line-cap": "round" },
    paint: { "line-color": palette().partyWallCore, "line-width": 2.5 },
  });
}
