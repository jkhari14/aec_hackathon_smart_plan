// Friendly names for the generated contract types. Regenerate api_types.ts with `npm run contracts`
// after any change to api/contracts.py; never edit api_types.ts by hand.
import type { components } from "./api_types";

type S = components["schemas"];

export type Source = S["Source"];
export type DatasetStatus = S["DatasetStatus"];
export type LayerCatalogEntry = S["LayerCatalogEntry"];
export type LayerFeature = S["LayerFeature"];
export type LayerFeatureCollection = S["LayerFeatureCollection"];
export type SearchResult = S["SearchResult"];
export type Case = S["Case"];
export type StructuralModel = S["StructuralModel"];
export type SiteProfile = S["SiteProfile"];
export type Neighbor = S["Neighbor"];
export type Signal = S["Signal"];
export type SimilarCase = S["SimilarCase"];
export type SimilarCases = S["SimilarCases"];
export type EarlyWarning = S["EarlyWarning"];
export type WarningRuleCheck = S["WarningRuleCheck"];
export type PatternScore = S["PatternScore"];
export type ActionItem = S["ActionItem"];
export type Project = S["Project"];
export type ProjectCreate = S["ProjectCreate"];
export type ChatRequest = S["ChatRequest"];
export type ChatResponse = S["ChatResponse"];

export type Hazard = LayerCatalogEntry["hazard"];
export type Severity = LayerFeature["properties"]["severity"];
export type Stage = ProjectCreate["stage"];

export const HAZARDS: Hazard[] = [
  "structural",
  "geotech",
  "fire",
  "flood",
  "contamination",
  "facade",
  "weather",
  "construction_safety",
];

export const SEVERITY_LABELS: Record<Severity, string> = {
  0: "Signal",
  1: "Enforcement",
  2: "Incident",
  3: "Catastrophic",
};
