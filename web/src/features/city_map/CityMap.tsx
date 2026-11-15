// The map home: a full-bleed dark city map with every layer from /api/layers (clustered, fading in by
// zoom), extruded buildings, click to pick a site, a cinematic fly-to, and the site
// with its touching lots highlighted, the shared party wall glowing, and similar cases arcing in from
// across the city. Google Photorealistic 3D Tiles replace the extrusions when a key is set.
import type { Layer } from "@deck.gl/core";
import { MapboxOverlay } from "@deck.gl/mapbox";
import type { FeatureCollection, Point } from "geojson";
import { type GeoJSONSource, Map as MapLibreMap, type MapGeoJSONFeature, NavigationControl, Popup } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import "./city_map.css";

import { api } from "../../api/client";
import type { LayerFeature } from "../../contracts";
import { SEVERITY_LABELS } from "../../contracts";
import type { LayerState } from "../layer_panel/LayerPanel";
import {
  addAreaLayers, addBuildings, addPointLayers, addSiteLayers, areaLayerIds, BASEMAP, NYC_CENTER, pointLayerIds, sourceId,
} from "./map_style";
import { loadSiteLots, type Picked, siteAt } from "./site_lots";
import { GOOGLE_KEY, googleTiles, similarCaseLayers, similarCaseTooltip } from "./story_layers";

// The shell owns the picked site, the layer toggles and the search; the map draws them and reports clicks.
// Without `enabled`, every layer keeps its catalog default.
type Props = {
  site?: Picked | null;
  onPick?: (site: Picked) => void;
  enabled?: Set<string>;
  onSample?: () => void;
};

const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** "Why am I seeing this?": what the record is, its severity, source and date. Built as DOM, never HTML. */
function recordCard(p: Record<string, unknown>): HTMLElement {
  const el = document.createElement("div");
  el.className = "fs-popup";
  const title = el.appendChild(document.createElement("strong"));
  title.textContent = String(p.title ?? "Record");
  const summary = el.appendChild(document.createElement("p"));
  summary.textContent = String(p.summary ?? "");
  const meta = el.appendChild(document.createElement("p"));
  meta.className = "fs-popup-meta";
  const severity = SEVERITY_LABELS[Number(p.severity) as keyof typeof SEVERITY_LABELS] ?? "";
  meta.textContent = `${severity} · ${p.date ?? "undated"} · `;
  const link = meta.appendChild(document.createElement("a"));
  link.href = String(p.source_url ?? "#");
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = String(p.source_name ?? "source");
  return el;
}

export function CityMap({ site: picked = null, onPick, enabled, onSample }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [ready, setReady] = useState(false);
  const [layers, setLayers] = useState<LayerState[]>([]);
  const [siteStatus, setSiteStatus] = useState<string | null>(null);
  const [sample, setSample] = useState(false);
  const [credits, setCredits] = useState<string | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const deckLayers = useRef<{ tiles: Layer[]; arcs: Layer[] }>({ tiles: [], arcs: [] });
  const drawDeck = () => overlayRef.current?.setProps({ layers: [...deckLayers.current.tiles, ...deckLayers.current.arcs] });

  useEffect(() => {
    if (!container.current) return;
    const map = new MapLibreMap({ container: container.current, style: BASEMAP, center: NYC_CENTER, zoom: 10.4, pitch: 30 });
    map.addControl(new NavigationControl({ visualizePitch: true }), "bottom-right");
    // Not interleaved: with MapLibre 6 the shared-context mode drew nothing; its own canvas works.
    const overlay = new MapboxOverlay({ interleaved: false, layers: [], getTooltip: similarCaseTooltip as never });
    map.addControl(overlay);
    overlayRef.current = overlay;
    map.on("load", () => {
      addBuildings(map);
      addSiteLayers(map);
      setReady(true);
      if (GOOGLE_KEY) {
        googleTiles(GOOGLE_KEY, setCredits).then((tiles) => {
          if (!mapRef.current) return;
          map.setLayoutProperty("buildings-3d", "visibility", "none");
          deckLayers.current.tiles = [tiles];
          drawDeck();
        }).catch(() => setCredits("Google 3D tiles couldn't load; showing extruded buildings."));
      }
    });
    mapRef.current = map;
    return () => {
      overlayRef.current = null;
      mapRef.current = null;
      setReady(false);
      map.remove();
    };
  }, []);

  // Load the catalog, then each layer's features into its own clustered source.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    let cancelled = false;
    api.layers().then(({ data, sample: s }) => {
      if (cancelled) return;
      setSample((was) => was || s);
      setLayers(data.map((entry) => ({ entry, on: entry.default_on, loaded: null, sample: s })));
      data.filter((e) => e.status !== "error").forEach((entry) => {
        api.layerFeatures(entry.layer_id).then(({ data: collection, sample: fs }) => {
          if (cancelled || !mapRef.current || map.getSource(sourceId(entry.layer_id))) return;
          setSample((was) => was || fs);
          // The offline fixture holds one layer's records; never show them under another layer's name.
          const features = collection.features.filter((f) => f.properties.layer_id === entry.layer_id);
          const points = features.filter((f) => f.geometry.type === "Point");
          const areas = features.filter((f) => f.geometry.type !== "Point");
          const asCollection = (fs2: LayerFeature[]) => ({ type: "FeatureCollection", features: fs2 }) as FeatureCollection;
          if (areas.length > 0) {
            map.addSource(sourceId(entry.layer_id), { type: "geojson", data: asCollection(areas) });
            addAreaLayers(map, entry.layer_id, entry.hazard, entry.default_on);
          } else {
            map.addSource(sourceId(entry.layer_id), {
              type: "geojson", data: asCollection(points), cluster: true, clusterRadius: 48, clusterMaxZoom: 14,
            });
            addPointLayers(map, entry.layer_id, entry.hazard, entry.default_on);
          }
          setLayers((ls) => ls.map((l) => (l.entry.layer_id === entry.layer_id ? { ...l, loaded: features.length, sample: fs } : l)));
        });
      });
    });
    return () => {
      cancelled = true;
    };
  }, [ready]);

  useEffect(() => {
    if (sample) onSample?.();
  }, [sample, onSample]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !enabled) return;
    for (const { entry } of layers) {
      for (const id of [...pointLayerIds(entry.layer_id), ...areaLayerIds(entry.layer_id)]) {
        if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", enabled.has(entry.layer_id) ? "visible" : "none");
      }
    }
  }, [ready, layers, enabled]);

  // Clicks: a cluster zooms in, a record explains itself, anywhere else picks the site under the cursor.
  const pickSite = useCallback((site: Picked) => onPick?.(site), [onPick]);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const onClick = async (e: { point: [number, number] | { x: number; y: number }; lngLat: { lng: number; lat: number } }) => {
      const pointIds = layers.flatMap((l) => pointLayerIds(l.entry.layer_id)).filter((id) => map.getLayer(id));
      const hits: MapGeoJSONFeature[] = pointIds.length ? map.queryRenderedFeatures(e.point as never, { layers: pointIds }) : [];
      const hit = hits[0];
      if (hit?.properties.cluster_id != null) {
        const source = map.getSource(hit.source) as GeoJSONSource;
        const zoom = await source.getClusterExpansionZoom(hit.properties.cluster_id);
        map.easeTo({ center: (hit.geometry as Point).coordinates as [number, number], zoom, duration: reducedMotion() ? 0 : 400 });
        return;
      }
      if (hit) {
        new Popup({ closeButton: false, maxWidth: "280px" }).setLngLat(e.lngLat).setDOMContent(recordCard(hit.properties)).addTo(map);
        return;
      }
      const site = await siteAt(e.lngLat.lng, e.lngLat.lat);
      if (site) pickSite(site);
    };
    map.on("click", onClick);
    return () => {
      map.off("click", onClick);
    };
  }, [ready, layers, pickSite]);

  // Picking a site: fly in, then highlight it and its touching lots.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
    (map.getSource("site-lots") as GeoJSONSource).setData(empty);
    (map.getSource("party-walls") as GeoJSONSource).setData(empty);
    deckLayers.current.arcs = [];
    drawDeck();
    setSiteStatus(null);
    if (!picked) return;
    let cancelled = false;
    const camera = { center: [picked.lon, picked.lat] as [number, number], zoom: 17.4, pitch: 60, bearing: -28 };
    if (reducedMotion()) map.jumpTo(camera);
    else map.flyTo({ ...camera, duration: 3200, curve: 1.6, essential: false });
    setSiteStatus("Loading the site and its touching lots…");
    let frame = 0;
    loadSiteLots(picked).then(({ lots, walls, profile, sample: s, note }) => {
      if (cancelled) return;
      setSample((was) => was || s);
      (map.getSource("site-lots") as GeoJSONSource).setData(lots);
      (map.getSource("party-walls") as GeoJSONSource).setData(walls);
      const touching = profile?.neighbors.length;
      setSiteStatus(note ?? `site and ${touching} touching lot${touching === 1 ? "" : "s"} highlighted`);
    });
    // Similar cases arc in once the camera has settled on the site.
    api.similar(picked.bbl).then(({ data, sample: s }) => {
      // The offline fixture is for one demo lot; never arc its cases into a different site.
      if (cancelled || data.bbl !== picked.bbl || data.results.length === 0) return;
      setSample((was) => was || s);
      const start = performance.now() + (reducedMotion() ? 0 : 2600);
      const step = (now: number) => {
        if (cancelled) return;
        const t = reducedMotion() ? 1 : Math.min(1, Math.max(0, (now - start) / 1200));
        deckLayers.current.arcs = similarCaseLayers(picked, data.results, 1 - (1 - t) ** 3);
        drawDeck();
        if (t < 1) frame = requestAnimationFrame(step);
      };
      frame = requestAnimationFrame(step);
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
    };
  }, [ready, picked]);

  // maplibre-gl.css sets the map element to position: relative, so it sizes to this wrapper instead.
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" />
      {picked && siteStatus && (
        <div className="fs-hint" role="status">{siteStatus}</div>
      )}
      {credits && (
        <span className="absolute bottom-10 right-4 max-w-md rounded bg-panel/80 px-2 py-0.5 text-[11px] text-muted">{credits}</span>
      )}
    </div>
  );
}
