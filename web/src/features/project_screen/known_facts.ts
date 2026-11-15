// "What we already know about this lot": the lines the setup card shows, read from the site profile the map
// already loaded. Each line names its source. Nothing is invented: a profile that couldn't load leaves every
// line empty (shown as "couldn't load"), and a fact the records don't hold is left out or empty.
import type { SiteProfile } from "../../contracts";

/** `missing` says why a loaded profile has no value (the profile doesn't check it); without it, an empty value
    means the profile itself couldn't load. */
export type KnownFact = { label: string; value: string | null; source: string; missing?: string };

const NOT_CHECKED = "not checked for this lot";

const JOB_LABELS: Record<string, string> = { new_building: "New building", alteration: "Alteration", demolition: "Demolition" };

const span = (values: number[], unit = "") => {
  if (values.length === 0) return null;
  const lo = Math.min(...values), hi = Math.max(...values);
  return lo === hi ? `${lo}${unit}` : `${lo}–${hi}${unit}`;
};

function neighbors(profile: SiteProfile): string | null {
  const attached = profile.neighbors.filter((n) => n.attached);
  if (attached.length === 0) return profile.neighbors.length ? `${profile.neighbors.length} touching, none attached` : "None touching";
  const years = span(attached.map((n) => n.year_built).filter((y): y is number => !!y));
  const floors = span(attached.map((n) => n.floors).filter((f): f is number => !!f), " storeys");
  return [`${attached.length} attached`, years && `built ${years}`, floors].filter(Boolean).join(", ");
}

export function knownFacts(profile: SiteProfile | null): KnownFact[] {
  const unchecked = (value: string | null) => (profile && value === null ? { missing: NOT_CHECKED } : {});
  const lotSize = profile?.lot.lot_area_sqft ? `${profile.lot.lot_area_sqft.toLocaleString("en-US")} sq ft` : null;
  const flood = profile?.flood.fema_zone ? `Zone ${profile.flood.fema_zone}` : null;
  const lines: KnownFact[] = [
    { label: "Neighbors", value: profile ? neighbors(profile) : null, source: "PLUTO and building footprints" },
    { label: "Lot size", value: lotSize, source: "PLUTO", ...unchecked(lotSize) },
    { label: "Flood zone", value: flood, source: "FEMA flood maps", ...unchecked(flood) },
  ];
  if (profile?.job_type) {
    lines.push({ label: "Filed with DOB", value: JOB_LABELS[profile.job_type] ?? profile.job_type, source: "DOB NOW filings" });
  }
  if (profile?.e_designation) {
    lines.push({ label: "E-designation", value: profile.e_designation, source: "NYC Office of Environmental Remediation" });
  }
  return lines;
}
