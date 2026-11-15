// The picked lot and its building blink so the eye finds them: when a site is picked, and again when
// the view switches between 2D and 3D. After the blink the building keeps a soft tint.
import type { FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";
import type { IControl, Map as MapLibreMap } from "maplibre-gl";

// The accent blue of the 4site palette: the picked site is the one blue thing on the map.
export const SELECTION_COLOR = "#4a6cf0";

// NYC Building Footprints: outline and roof height (feet) for each building, keyed by lot.
const FOOTPRINTS = "https://data.cityofnewyork.us/resource/5zhs-2jue.geojson";
const BBL = /^\d{10}$/;
const FEET = 0.3048;
// The basemap draws the same building from OpenStreetMap. Grown a few percent around its middle, ours
// sits just outside those walls instead of on them, so its walls show instead of flickering.
const GROW = 1.04;

const BUILDING = "site-building-blink";
const LOT_FILL = "site-lot-blink-fill";
const LOT_EDGE = "site-lot-blink-edge";

const PULSES = 3;
const BLINK_MS = 1800;
const PEAK = { building: 1, fill: 0.45, edge: 1 };
// What stays once the blink ends: the building tinted, the lot back to its usual white edge.
const REST = { building: 0.6, fill: 0, edge: 0 };

/** Below this pitch the map counts as 2D. */
const FLAT_PITCH = 10;
export const PITCH_3D = 60;

export type ViewMode = "2d" | "3d";
export const viewMode = (pitch: number): ViewMode => (pitch < FLAT_PITCH ? "2d" : "3d");

const empty: FeatureCollection = { type: "FeatureCollection", features: [] };

/** The blink layers: the site's buildings raised above the basemap's, and the site lot's fill and edge. */
export function addSelectionLayers(map: MapLibreMap): void {
  map.addSource(BUILDING, { type: "geojson", data: empty });
  const onlySite = ["==", ["get", "role"], "site"] as never;
  // Opacity is driven frame by frame, so MapLibre's own fade would only make the blink lag.
  const instant = { duration: 0, delay: 0 };
  map.addLayer({
    id: LOT_FILL,
    type: "fill",
    source: "site-lots",
    filter: onlySite,
    paint: { "fill-color": SELECTION_COLOR, "fill-opacity": 0, "fill-opacity-transition": instant },
  });
  map.addLayer({
    id: LOT_EDGE,
    type: "line",
    source: "site-lots",
    filter: onlySite,
    paint: { "line-color": SELECTION_COLOR, "line-width": 4, "line-opacity": 0, "line-opacity-transition": instant },
  });
  map.addLayer({
    id: BUILDING,
    type: "fill-extrusion",
    source: BUILDING,
    paint: {
      "fill-extrusion-color": SELECTION_COLOR,
      "fill-extrusion-height": ["get", "height_m"],
      "fill-extrusion-base": 0,
      "fill-extrusion-opacity": 0,
      "fill-extrusion-opacity-transition": instant,
      // No darker base: the basemap's light already leaves the walls dim on the dark map.
      "fill-extrusion-vertical-gradient": false,
    },
  });
}

function grow(ring: Position[]): Position[] {
  const n = ring.length;
  const cx = ring.reduce((sum, p) => sum + p[0], 0) / n;
  const cy = ring.reduce((sum, p) => sum + p[1], 0) / n;
  return ring.map(([x, y]) => [cx + (x - cx) * GROW, cy + (y - cy) * GROW]);
}

/** The site's building outlines with their roof heights in meters; empty when none can be found. */
export async function loadSiteBuildings(bbl: string): Promise<FeatureCollection> {
  if (!BBL.test(bbl)) return empty;
  const where = `base_bbl='${bbl}' OR mappluto_bbl='${bbl}'`;
  try {
    const response = await fetch(`${FOOTPRINTS}?$select=bin,height_roof,the_geom&$where=${encodeURIComponent(where)}`);
    if (!response.ok) return empty;
    const data = (await response.json()) as FeatureCollection<Polygon | MultiPolygon>;
    for (const f of data.features) {
      const feet = Number(f.properties?.height_roof);
      // A footprint with no roof height still gets a low block, so the blink has something to show.
      // The extra meter keeps it just above the basemap's own building of the same height.
      f.properties = { bin: f.properties?.bin, height_m: (Number.isFinite(feet) && feet > 0 ? feet * FEET : 6) + 1 };
      const g = f.geometry;
      if (g?.type === "Polygon") g.coordinates = g.coordinates.map(grow);
      else if (g?.type === "MultiPolygon") g.coordinates = g.coordinates.map((poly) => poly.map(grow));
    }
    return data;
  } catch {
    return empty;
  }
}

export function setSiteBuildings(map: MapLibreMap, buildings: FeatureCollection): void {
  (map.getSource(BUILDING) as { setData: (d: FeatureCollection) => void } | undefined)?.setData(buildings);
}

function paint(map: MapLibreMap, level: { building: number; fill: number; edge: number }): void {
  if (map.getLayer(BUILDING)) map.setPaintProperty(BUILDING, "fill-extrusion-opacity", level.building);
  if (map.getLayer(LOT_FILL)) map.setPaintProperty(LOT_FILL, "fill-opacity", level.fill);
  if (map.getLayer(LOT_EDGE)) map.setPaintProperty(LOT_EDGE, "line-opacity", level.edge);
}

/** Hide the blink layers, as when no site is picked. */
export function clearSelection(map: MapLibreMap): void {
  paint(map, { building: 0, fill: 0, edge: 0 });
}

/**
 * Blink the picked lot and building three times, then settle on the resting tint. With reduced motion
 * there is no blink: the building takes its tint and the lot keeps a steady magenta edge.
 * Returns a function that stops the blink where it is and settles.
 */
export function blinkSelection(map: MapLibreMap, reducedMotion: boolean): () => void {
  if (reducedMotion) {
    paint(map, { ...REST, edge: PEAK.edge });
    return () => {};
  }
  const start = performance.now();
  let frame = 0;
  const lastPeak = (PULSES - 0.5) / PULSES;
  const step = (now: number) => {
    const t = Math.min(1, (now - start) / BLINK_MS);
    // 0 at the start and end of each pulse, 1 at its middle.
    const k = 0.5 - 0.5 * Math.cos(2 * Math.PI * PULSES * t);
    const settling = t >= lastPeak;
    paint(map, {
      building: settling ? Math.max(REST.building, PEAK.building * k) : PEAK.building * k,
      fill: PEAK.fill * k,
      edge: PEAK.edge * k,
    });
    if (t < 1) frame = requestAnimationFrame(step);
    else paint(map, REST);
  };
  frame = requestAnimationFrame(step);
  return () => {
    cancelAnimationFrame(frame);
    paint(map, REST);
  };
}

/** A 2D/3D button for the map's control stack: flat and straight down, or tilted to see the buildings. */
export class ViewModeControl implements IControl {
  private map: MapLibreMap | null = null;
  private container: HTMLDivElement | null = null;
  private button: HTMLButtonElement | null = null;

  constructor(private readonly reducedMotion: () => boolean) {}

  onAdd(map: MapLibreMap): HTMLElement {
    this.map = map;
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group fs-view-mode";
    this.button = this.container.appendChild(document.createElement("button"));
    this.button.type = "button";
    this.button.addEventListener("click", this.toggle);
    this.show(viewMode(map.getPitch()));
    return this.container;
  }

  onRemove(): void {
    this.button?.removeEventListener("click", this.toggle);
    this.container?.remove();
    this.map = null;
  }

  /** The button names the view it switches to. */
  show(mode: ViewMode): void {
    if (!this.button) return;
    const next = mode === "2d" ? "3D" : "2D";
    this.button.textContent = next;
    this.button.title = `Switch to ${next} view`;
    this.button.setAttribute("aria-label", `Switch to ${next} view`);
  }

  private toggle = () => {
    const map = this.map;
    if (!map) return;
    const pitch = viewMode(map.getPitch()) === "2d" ? PITCH_3D : 0;
    if (this.reducedMotion()) map.jumpTo({ pitch });
    else map.easeTo({ pitch, duration: 600 });
  };
}
