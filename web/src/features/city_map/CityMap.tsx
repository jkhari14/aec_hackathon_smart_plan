// Placeholder citywide map so every screen has something to sit on. Shandon's PR 5 replaces it with the
// real map home: all layers, site pick, 3D tiles and the extruded-footprint fallback.
import { MapboxOverlay } from "@deck.gl/mapbox";
import { ScatterplotLayer } from "@deck.gl/layers";
import { Map as MapLibreMap, NavigationControl } from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { LayerFeature } from "../../contracts";

const BASEMAP = "https://tiles.openfreemap.org/styles/dark";
const NYC: [number, number] = [-73.95, 40.7];

const SEVERITY_COLORS: Record<number, [number, number, number]> = {
  0: [148, 163, 184],
  1: [250, 204, 21],
  2: [249, 115, 22],
  3: [239, 68, 68],
};

type Props = { features: LayerFeature[] };

export function CityMap({ features }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapboxOverlay | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const map = new MapLibreMap({ container: container.current, style: BASEMAP, center: NYC, zoom: 10.5, pitch: 30 });
    map.addControl(new NavigationControl(), "bottom-right");
    const deck = new MapboxOverlay({ layers: [] });
    map.addControl(deck);
    overlay.current = deck;
    return () => {
      overlay.current = null;
      map.remove();
    };
  }, []);

  useEffect(() => {
    overlay.current?.setProps({
      layers: [
        new ScatterplotLayer<LayerFeature>({
          id: "sample-points",
          data: features.filter((f) => f.geometry.type === "Point"),
          getPosition: (f) => f.geometry.coordinates as [number, number],
          getFillColor: (f) => SEVERITY_COLORS[f.properties.severity],
          getRadius: 120,
          radiusMinPixels: 5,
          pickable: true,
        }),
      ],
    });
  }, [features]);

  // maplibre-gl.css sets the map element to position: relative, so it sizes to this wrapper instead.
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" />
    </div>
  );
}
