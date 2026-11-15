// Hazard and severity tokens for TypeScript: the map (deck.gl wants RGB arrays) and any component that
// needs a label. Colors mirror tokens.css; keep the two in step.
import type { Hazard, Severity } from "../contracts";

export const HAZARD_LABELS: Record<Hazard, string> = {
  structural: "Structural",
  geotech: "Geotechnical",
  fire: "Fire",
  flood: "Flood",
  contamination: "Contamination",
  facade: "Facade",
  weather: "Weather",
  construction_safety: "Construction safety",
};

type Rgb = [number, number, number];

const hex = (h: string): Rgb => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)) as Rgb;

export const HAZARD_RGB: Record<"dark" | "light", Record<Hazard, Rgb>> = {
  dark: {
    structural: hex("#ff9f43"),
    geotech: hex("#c9a27a"),
    fire: hex("#ff6b5a"),
    flood: hex("#4fa9ff"),
    contamination: hex("#b48cff"),
    facade: hex("#d9cbb0"),
    weather: hex("#74c9dc"),
    construction_safety: hex("#ffd24a"),
  },
  light: {
    structural: hex("#c25a00"),
    geotech: hex("#8a6239"),
    fire: hex("#c8321f"),
    flood: hex("#1b6fd1"),
    contamination: hex("#7444d4"),
    facade: hex("#786a4f"),
    weather: hex("#217f93"),
    construction_safety: hex("#8f6c00"),
  },
};

// Severity is drawn by size and ring count first. These are the map equivalents of .fs-sev.
export const SEVERITY_MARK: Record<Severity, { radiusPx: number; rings: number }> = {
  0: { radiusPx: 3, rings: 0 },
  1: { radiusPx: 4, rings: 1 },
  2: { radiusPx: 5, rings: 1 },
  3: { radiusPx: 6, rings: 2 },
};

// Life safety sorts first, then severity, then the newest date.
const LIFE_SAFETY: Hazard[] = ["structural", "fire", "construction_safety", "facade", "geotech", "flood", "weather", "contamination"];

export function bySignalPriority<T extends { hazard: Hazard; severity: Severity; date?: string | null }>(a: T, b: T) {
  return (
    b.severity - a.severity ||
    LIFE_SAFETY.indexOf(a.hazard) - LIFE_SAFETY.indexOf(b.hazard) ||
    (b.date ?? "").localeCompare(a.date ?? "")
  );
}
