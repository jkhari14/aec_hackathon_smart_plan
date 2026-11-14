import { type GeoJSONSource, LngLatBounds, Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
// Vite bundles MapLibre's module worker and hands back its URL; without this the map stays blank.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import { useEffect, useRef, useState } from "react";

import type { Brief } from "../../brief/brief_types";
import { briefGeoJson } from "../export/brief_geojson";

setWorkerUrl(workerUrl);

const BASEMAP = "https://tiles.openfreemap.org/styles/positron";
const SOURCE = "brief";

type Props = { brief: Brief; selectedBbl: string | null; onSelect: (bbl: string) => void };

function extendBounds(bounds: LngLatBounds, coordinates: unknown): void {
  if (Array.isArray(coordinates) && typeof coordinates[0] === "number") {
    bounds.extend([coordinates[0], coordinates[1] as number]);
  } else if (Array.isArray(coordinates)) {
    coordinates.forEach((c) => extendBounds(bounds, c));
  }
}

export function SiteMapView({ brief, selectedBbl, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<MapLibreMap | null>(null);
  const onSelectRef = useRef(onSelect);
  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!container.current) return;
    const m = new MapLibreMap({ container: container.current, style: BASEMAP, center: [-73.95, 40.64], zoom: 17, pitch: 50 });
    m.on("load", () => {
      m.addSource(SOURCE, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      m.addLayer({ id: "lots", type: "fill", source: SOURCE, filter: ["==", ["get", "kind"], "lot"],
        paint: { "fill-color": ["match", ["get", "role"], "site", "#dc2626", "#d97706"], "fill-opacity": 0.25 } });
      m.addLayer({ id: "lot-lines", type: "line", source: SOURCE, filter: ["==", ["get", "kind"], "lot"],
        paint: { "line-color": "#1c1917", "line-width": 1 } });
      m.addLayer({ id: "buildings", type: "fill-extrusion", source: SOURCE, filter: ["==", ["get", "kind"], "building"],
        paint: { "fill-extrusion-color": ["match", ["get", "role"], "site", "#dc2626", "#a8a29e"],
          "fill-extrusion-height": ["get", "height_m"], "fill-extrusion-opacity": 0.8 } });
      m.addLayer({ id: "selected", type: "line", source: SOURCE, filter: ["==", ["get", "bbl"], ""],
        paint: { "line-color": "#d97706", "line-width": 4 } });
      m.on("click", "lots", (e) => {
        const bbl = e.features?.[0]?.properties?.bbl;
        if (typeof bbl === "string") onSelectRef.current(bbl);
      });
      setMap(m);
    });
    return () => {
      setMap(null);
      m.remove();
    };
  }, []);

  useEffect(() => {
    if (!map) return;
    const data = briefGeoJson(brief);
    (map.getSource(SOURCE) as GeoJSONSource).setData(data as Parameters<GeoJSONSource["setData"]>[0]);
    const bounds = new LngLatBounds();
    data.features.filter((f) => f.properties.kind === "lot")
      .forEach((f) => extendBounds(bounds, (f.geometry as { coordinates: unknown }).coordinates));
    if (!bounds.isEmpty()) map.fitBounds(bounds, { padding: 60, pitch: 50, duration: 0 });
  }, [map, brief]);

  useEffect(() => {
    map?.setFilter("selected", ["==", ["get", "bbl"], selectedBbl ?? ""]);
  }, [map, selectedBbl]);

  return <div ref={container} className="h-full min-h-80 w-full" />;
}
