import type { Brief, Lot } from "../../brief/brief_types";

type Feature = { type: "Feature"; geometry: object; properties: Record<string, string | number | null> };
export type FeatureCollection = { type: "FeatureCollection"; features: Feature[] };

const FEET_TO_METERS = 0.3048;

// Lots and building footprints as one GeoJSON collection (EPSG:4326), for the map and for export.
export function briefGeoJson(brief: Brief): FeatureCollection {
  const lots: Lot[] = [brief.site, ...brief.touching_lots];
  const features: Feature[] = [];
  for (const lot of lots) {
    if (lot.lot_geometry) {
      features.push({ type: "Feature", geometry: lot.lot_geometry,
        properties: { kind: "lot", bbl: lot.bbl, role: lot.role, address: lot.facts?.address ?? null,
          year_built: lot.facts?.year_built ?? null } });
    }
    for (const b of lot.buildings) {
      if (!b.geometry) continue;
      features.push({ type: "Feature", geometry: b.geometry,
        properties: { kind: "building", bbl: lot.bbl, role: lot.role, bin: b.bin ?? null,
          height_roof_ft: b.height_roof_ft ?? null, height_m: (b.height_roof_ft ?? 0) * FEET_TO_METERS,
          status: b.status ?? null } });
    }
  }
  return { type: "FeatureCollection", features };
}
