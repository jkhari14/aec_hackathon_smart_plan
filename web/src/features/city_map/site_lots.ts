// Lot outlines for the picked site and its touching neighbors, and the click-to-site lookup.
import type { Feature, FeatureCollection } from "geojson";
import { api } from "../../api/client";
import type { SiteProfile } from "../../contracts";

// MapPLUTO tax lot polygons, the same dataset data_pull/lot_neighbors.py uses.
const TAX_LOTS = "https://data.cityofnewyork.us/resource/i38t-6if2.geojson";
const BBL = /^\d{10}$/;

export type Picked = { label: string; bbl: string; lat: number; lon: number };

export type SiteLots = {
  lots: FeatureCollection;
  profile: SiteProfile | null;
  sample: boolean;
  /** Why neighbors are missing, when they are: shown to the user, never as "0 neighbors". */
  note: string | null;
};

async function lotPolygons(bbls: string[]): Promise<Feature[]> {
  const safe = bbls.filter((b) => BBL.test(b));
  if (safe.length === 0) return [];
  const where = `bbl in(${safe.map((b) => `'${b}'`).join(",")})`;
  const response = await fetch(`${TAX_LOTS}?$select=bbl,the_geom&$where=${encodeURIComponent(where)}`);
  if (!response.ok) throw new Error(`${response.status} tax lots`);
  const data = (await response.json()) as FeatureCollection;
  return data.features;
}

/** The site's profile (for its touching lots) and every lot's outline, tagged site or neighbor. */
export async function loadSiteLots(site: Picked): Promise<SiteLots> {
  const result = await api.siteProfile(site.bbl);
  // The offline fixture describes one demo lot; never draw its neighbors around a different site.
  const profile = result.data.bbl === site.bbl ? result.data : null;
  const neighborBbls = profile?.neighbors.map((n) => n.bbl) ?? [];
  let note: string | null = profile ? null : "Touching lots couldn't load: the site profile is unavailable for this lot.";
  let features: Feature[] = [];
  try {
    features = await lotPolygons([site.bbl, ...neighborBbls]);
  } catch {
    note = "Lot outlines couldn't load from NYC Open Data.";
  }
  for (const f of features) {
    const bbl = String(f.properties?.bbl ?? "").split(".")[0];
    f.properties = { bbl, role: bbl === site.bbl ? "site" : "neighbor" };
  }
  return { lots: { type: "FeatureCollection", features }, profile, sample: result.sample, note };
}

// shortcut: the API has no reverse lookup yet, so a map click asks NYC Planning's GeoSearch directly;
// move this behind /api/search once Jahleel's routers (PR 4) offer a point query.
export async function siteAt(lon: number, lat: number): Promise<Picked | null> {
  try {
    const url = `https://geosearch.planninglabs.nyc/v2/reverse?point.lat=${lat}&point.lon=${lon}&size=1`;
    const response = await fetch(url);
    if (!response.ok) return null;
    const data = await response.json();
    const feature = data.features?.[0];
    const bbl = feature?.properties?.addendum?.pad?.bbl;
    if (!feature || !BBL.test(bbl ?? "")) return null;
    const [flon, flat] = feature.geometry.coordinates as [number, number];
    return { label: feature.properties.label, bbl, lat: flat, lon: flon };
  } catch {
    return null;
  }
}
