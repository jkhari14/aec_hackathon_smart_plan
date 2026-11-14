import type { Brief, BriefListing } from "./brief_types";

export type Loaded<T> = { data: T; offline: boolean };

// Dates with a static copy (see DEMO_AS_OF in api/brief/brief_export.py).
const DEMO_AS_OF = ["2026-06-01", "2026-11-11"];

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path);
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null; // not running
  }
}

export async function loadBriefList(): Promise<Loaded<BriefListing[]>> {
  const live = await fetchJson<BriefListing[]>("/api/briefs");
  if (live) return { data: live, offline: false };
  const saved = await fetchJson<BriefListing[]>("/demo_briefs/index.json");
  if (!saved) throw new Error("No API and no saved demo briefs: run `python -m api.brief.brief_export`.");
  return { data: saved, offline: true };
}

// The API first; with it down, the static copies brief_export wrote. A saved copy exists only
// for the demo dates, so another date falls back to the as-pulled brief and says so.
export async function loadBrief(slug: string, asOf: string | null): Promise<Loaded<Brief>> {
  const safe = encodeURIComponent(slug);
  const live = await fetchJson<Brief>(`/api/briefs/${safe}${asOf ? `?as_of=${encodeURIComponent(asOf)}` : ""}`);
  if (live) return { data: live, offline: false };
  const savedName = asOf && DEMO_AS_OF.includes(asOf) ? `${safe}.as-of-${asOf}` : safe;
  const saved = await fetchJson<Brief>(`/demo_briefs/${savedName}.json`);
  if (!saved) throw new Error(`No saved brief for ${slug}.`);
  return { data: saved, offline: true };
}
