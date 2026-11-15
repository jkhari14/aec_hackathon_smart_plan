// The map home: a full-bleed dark city map with every layer from /api/layers (clustered, fading in by
// zoom), extruded buildings, address search or click to pick a site, a cinematic fly-to, and the site
// with its touching lots highlighted, the shared party wall glowing, and similar cases arcing in from
// across the city. 3D buildings come from Cityweft (the blocks around a picked site) or, to compare,
// Google Photorealistic 3D Tiles (citywide, needs VITE_GOOGLE_MAPS_KEY); a switch on the map picks one.
import type { Layer } from "@deck.gl/core";
import { MapboxOverlay } from "@deck.gl/mapbox";
import type { FeatureCollection, Point } from "geojson";
import { type GeoJSONSource, Map as MapLibreMap, type MapGeoJSONFeature, Popup } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import "./city_map.css";

import { api } from "../../api/client";
import type { LayerFeature } from "../../contracts";
import { SEVERITY_LABELS } from "../../contracts";
import { LayerPanel, type LayerState } from "../layer_panel/LayerPanel";
import {
  addAreaLayers, addBuildings, addPointLayers, addSiteLayers, areaLayerIds, BASEMAP, NYC_CENTER, pointLayerIds, sourceId,
} from "./map_style";
import { loadSiteLots, type Picked, siteAt } from "./site_lots";
import {
  ADJACENT_M, GOOGLE_KEY, googleTiles, HEIGHT_RAMP, loadMeshLayers, loadSiteModel, type ModelScope, similarCaseLayers,
  similarCaseTooltip, SITE_COLOR, type SiteModel, siteModelLayer,
} from "./story_layers";
import { CameraControls } from "./CameraControls";
import { SiteSearch } from "./SiteSearch";

// `features` is unused: kept so the PR 0 placeholder App still compiles until Camilo's shell replaces it.
type Props = { features?: LayerFeature[] };

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

type Source3d = "cityweft" | "google";
type CameraView = { center: [number, number]; zoom: number; pitch: number; bearing: number };
const CITY_VIEW: CameraView = { center: NYC_CENTER as [number, number], zoom: 10.4, pitch: 30, bearing: 0 };

/** Pick where the 3D buildings come from, to compare Cityweft with Google. Google needs its key. */
function Source3dSwitch({ value, onChange, note }: { value: Source3d; onChange: (s: Source3d) => void; note: string | null }) {
  const option = (id: Source3d, label: string, disabled = false, title?: string) => (
    <button
      type="button"
      disabled={disabled}
      title={title}
      aria-pressed={value === id}
      onClick={() => onChange(id)}
      className={`rounded px-2 py-0.5 ${value === id ? "bg-white/15 text-white" : "text-muted hover:text-white"} disabled:cursor-not-allowed disabled:opacity-40`}
    >
      {label}
    </button>
  );
  return (
    <div className="flex flex-col gap-1 text-[11px]">
      <div className="flex w-fit items-center gap-1 rounded bg-panel/90 p-0.5" role="group" aria-label="3D buildings from">
        <span className="px-1.5 text-muted">3D</span>
        {option("cityweft", "Cityweft")}
        {option("google", "Google", !GOOGLE_KEY, GOOGLE_KEY ? undefined : "Set VITE_GOOGLE_MAPS_KEY to compare with Google 3D Tiles")}
      </div>
      {note && <span className="rounded bg-panel/80 px-2 py-0.5 text-muted">{note}</span>}
    </div>
  );
}

const rgb = (c: readonly number[]) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;

/** What the Cityweft colours mean, and how much of the model to draw. */
function ModelLegend({ model, scope, onScope }: { model: SiteModel; scope: ModelScope; onScope: (s: ModelScope) => void }) {
  const top = HEIGHT_RAMP[HEIGHT_RAMP.length - 1][0];
  const gradient = HEIGHT_RAMP.map(([h, c]) => `${rgb(c)} ${(h / top) * 100}%`).join(", ");
  const option = (id: ModelScope, label: string, title: string) => (
    <button
      type="button"
      title={title}
      aria-pressed={scope === id}
      onClick={() => onScope(id)}
      className={`rounded px-2 py-0.5 ${scope === id ? "bg-white/15 text-white" : "text-muted hover:text-white"}`}
    >
      {label} <span className="tabular-nums opacity-70">{model.counts[id]}</span>
    </button>
  );
  return (
    <div className="flex w-64 flex-col gap-1.5 rounded-lg bg-panel/90 p-2 text-[11px] shadow-lg backdrop-blur">
      <div className="flex items-center justify-between">
        <span className="font-medium text-white">Building height</span>
        <span className="flex items-center gap-1.5 text-muted">
          <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: rgb(SITE_COLOR) }} aria-hidden="true" />
          Your site
        </span>
      </div>
      <div className="h-2 rounded-full" style={{ background: `linear-gradient(to right, ${gradient})` }} aria-hidden="true" />
      <div className="flex justify-between tabular-nums text-muted">
        <span>0 m</span><span>45</span><span>90</span><span>160</span><span>{top}+ m</span>
      </div>
      <div className="flex items-center gap-1" role="group" aria-label="Buildings shown">
        <span className="text-muted">Show</span>
        {option("adjacent", "Adjacent", `The site and buildings within ${ADJACENT_M} m of it`)}
        {option("area", "Wider area", "Every building Cityweft returned, about 500 m across")}
      </div>
    </div>
  );
}

export function CityMap(_props: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [ready, setReady] = useState(false);
  const [layers, setLayers] = useState<LayerState[]>([]);
  const [picked, setPicked] = useState<Picked | null>(null);
  const [home, setHome] = useState<CameraView>(CITY_VIEW);
  const [siteStatus, setSiteStatus] = useState<string | null>(null);
  const [sample, setSample] = useState(false);
  const [source3d, setSource3d] = useState<Source3d>("cityweft");
  const [cityweftNote, setCityweftNote] = useState<string | null>(null);
  const [googleNote, setGoogleNote] = useState<string | null>(null);
  // The Cityweft model once it has risen; while rising it is drawn straight to deck.
  const [cityweft, setCityweft] = useState<{ model: SiteModel; meshLayers: Awaited<ReturnType<typeof loadMeshLayers>> } | null>(null);
  const [scope, setScope] = useState<ModelScope>("adjacent");
  const source3dRef = useRef<Source3d>("cityweft");
  source3dRef.current = source3d;
  const scopeRef = useRef<ModelScope>("adjacent");
  scopeRef.current = scope;
  const [googleLayer, setGoogleLayer] = useState<Layer | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const deckLayers = useRef<{ tiles: Layer[]; arcs: Layer[] }>({ tiles: [], arcs: [] });
  const drawDeck = () => overlayRef.current?.setProps({ layers: [...deckLayers.current.tiles, ...deckLayers.current.arcs] });

  useEffect(() => {
    if (!container.current) return;
    const map = new MapLibreMap({ container: container.current, style: BASEMAP, ...CITY_VIEW, maxPitch: 75 });
    // Not interleaved: with MapLibre 6 the shared-context mode drew nothing; its own canvas works.
    const overlay = new MapboxOverlay({ interleaved: false, layers: [], getTooltip: similarCaseTooltip as never });
    map.addControl(overlay);
    overlayRef.current = overlay;
    map.on("load", () => {
      addBuildings(map);
      addSiteLayers(map);
      setReady(true);
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

  // Clicks: a cluster zooms in, a record explains itself, anywhere else picks the site under the cursor.
  const pickSite = useCallback((site: Picked) => setPicked(site), []);
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
    if (!ready || !map || !picked) return;
    let cancelled = false;
    // Far enough back to see the site with its surrounding blocks, not just the lot.
    const camera: CameraView = { center: [picked.lon, picked.lat], zoom: 16.4, pitch: 52, bearing: -28 };
    setHome(camera);
    if (reducedMotion()) map.jumpTo(camera);
    else map.flyTo({ ...camera, duration: 3200, curve: 1.6, essential: false });
    setSiteStatus("Loading the site and its touching lots…");
    const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
    (map.getSource("site-lots") as GeoJSONSource).setData(empty);
    (map.getSource("party-walls") as GeoJSONSource).setData(empty);
    deckLayers.current.arcs = [];
    setCityweft(null);
    setCityweftNote("Loading the Cityweft 3D model of the surrounding blocks…");
    drawDeck();
    let frame = 0;
    let riseFrame = 0;
    // Cityweft's model of the blocks around the site; on failure the extruded buildings stay and the reason shows.
    // It waits for the camera to land, then the buildings rise out of the ground.
    const landsAt = performance.now() + (reducedMotion() ? 0 : 3200);
    const modelRequest = new AbortController();
    Promise.all([loadSiteModel(picked, modelRequest.signal), loadMeshLayers()])
      .then(([model, meshLayers]) => {
        if (cancelled) return;
        const sources = model.attributions.length ? ` (${model.attributions.join("; ")})` : "";
        setCityweftNote(`3D buildings from Cityweft${sources}`);
        const start = Math.max(performance.now(), landsAt);
        // Among towers, back off further so the camera isn't inside them: about a zoom level per 250 m over 80 m.
        const backOff = Math.min(1.4, Math.max(0, (model.tallestNearby - 80) / 250));
        if (backOff > 0.05) {
          setTimeout(() => {
            if (cancelled) return;
            const view = { ...camera, zoom: camera.zoom - backOff, pitch: camera.pitch - 4 * backOff };
            setHome(view);
            map.easeTo({ zoom: view.zoom, pitch: view.pitch, duration: reducedMotion() ? 0 : 1400 });
          }, Math.max(0, start - performance.now()));
        }
        const step = (now: number) => {
          if (cancelled) return;
          const t = reducedMotion() ? 1 : Math.min(1, Math.max(0, (now - start) / 1400));
          if (t < 1) {
            const layer = siteModelLayer(meshLayers, model, scopeRef.current, 1 - (1 - t) ** 3);
            // Drawn straight to deck while rising; the state only gets the finished layer.
            if (source3dRef.current === "cityweft" && now >= start) {
              deckLayers.current.tiles = [layer];
              drawDeck();
            }
            riseFrame = requestAnimationFrame(step);
          } else {
            setCityweft({ model, meshLayers });
          }
        };
        riseFrame = requestAnimationFrame(step);
      })
      .catch((error: Error) => {
        if (!cancelled) setCityweftNote(`Cityweft model unavailable: ${error.message}. Showing extruded buildings.`);
      });
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
      modelRequest.abort();
      cancelAnimationFrame(frame);
      cancelAnimationFrame(riseFrame);
    };
  }, [ready, picked]);

  // Google tiles load the first time Google is picked, then stay ready for switching back and forth.
  useEffect(() => {
    if (source3d !== "google" || googleLayer || !GOOGLE_KEY) return;
    setGoogleNote("Loading Google 3D tiles…");
    googleTiles(GOOGLE_KEY, (c) => setGoogleNote(c ? `Google 3D tiles: ${c}` : "Google 3D tiles"))
      .then(setGoogleLayer)
      .catch(() => setGoogleNote("Google 3D tiles couldn't load; showing extruded buildings."));
  }, [source3d, googleLayer]);

  // Show the picked source's buildings. Google replaces the extrusions citywide; Cityweft sits on top of them.
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const layer = source3d === "google" ? googleLayer : cityweft && siteModelLayer(cityweft.meshLayers, cityweft.model, scope);
    deckLayers.current.tiles = layer ? [layer] : [];
    if (map.getLayer("buildings-3d")) {
      map.setLayoutProperty("buildings-3d", "visibility", source3d === "google" && googleLayer ? "none" : "visible");
    }
    drawDeck();
  }, [ready, source3d, googleLayer, cityweft, scope]);

  // Keep the site in view when the layer panel opens over the map's right side.
  const onPanelOpen = useCallback((open: boolean) => {
    mapRef.current?.easeTo({ padding: { right: open ? 352 : 0, top: 72, left: 0, bottom: 0 }, duration: reducedMotion() ? 0 : 250 });
  }, []);

  const toggle = (layerId: string) => {
    const map = mapRef.current;
    setLayers((ls) => ls.map((l) => {
      if (l.entry.layer_id !== layerId) return l;
      const on = !l.on;
      for (const id of [...pointLayerIds(layerId), ...areaLayerIds(layerId)]) {
        if (map?.getLayer(id)) map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
      }
      return { ...l, on };
    }));
  };

  // maplibre-gl.css sets the map element to position: relative, so it sizes to this wrapper instead.
  return (
    <div className="absolute inset-0">
      <div ref={container} className="h-full w-full" />
      <SiteSearch picked={picked} status={siteStatus} onPick={pickSite} />
      <LayerPanel layers={layers} onToggle={toggle} onOpenChange={onPanelOpen} />
      <div className="absolute bottom-20 left-4 flex max-w-sm flex-col gap-1.5">
        <CameraControls map={ready ? mapRef.current : null} site={picked ? [picked.lon, picked.lat] : null} home={home} />
        {source3d === "cityweft" && cityweft && <ModelLegend model={cityweft.model} scope={scope} onScope={setScope} />}
        <Source3dSwitch value={source3d} onChange={setSource3d} note={source3d === "google" ? googleNote : cityweftNote} />
      </div>
      {sample && (
        <span className="absolute bottom-4 left-4 rounded bg-sample/15 px-2 py-0.5 text-xs font-medium text-sample">
          Sample data
        </span>
      )}
    </div>
  );
}
