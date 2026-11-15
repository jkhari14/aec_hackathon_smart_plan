// Every screen reads data through here. Each call tries the API and falls back to the matching fixture
// in contracts/fixtures/ when the API is down; both stub and fallback answers come back with
// `sample: true` so the UI can label them as sample data.
import type {
  ActionItem,
  Case,
  ChatRequest,
  ChatResponse,
  EarlyWarning,
  LayerCatalogEntry,
  LayerFeatureCollection,
  PatternScore,
  Project,
  SearchResult,
  SimilarCases,
  SiteProfile,
  WarningRuleCheck,
} from "../contracts";

import actionsFixture from "../../../contracts/fixtures/actions.json";
import casesFixture from "../../../contracts/fixtures/cases.json";
import chatFixture from "../../../contracts/fixtures/chat_response.json";
import layerCatalogFixture from "../../../contracts/fixtures/layer_catalog.json";
import layerFeaturesFixture from "../../../contracts/fixtures/layer_features.json";
import patternFixture from "../../../contracts/fixtures/pattern_score.json";
import projectFixture from "../../../contracts/fixtures/project.json";
import searchFixture from "../../../contracts/fixtures/search_results.json";
import similarFixture from "../../../contracts/fixtures/similar_cases.json";
import siteProfileFixture from "../../../contracts/fixtures/site_profile.json";
import warningChecksFixture from "../../../contracts/fixtures/warning_checks.json";
import warningsFixture from "../../../contracts/fixtures/warnings.json";

export type Loaded<T> = { data: T; sample: boolean };

const FIXTURE_HEADER = "X-ForeSite-Fixture";

async function request<T>(path: string, fallback: unknown, init?: RequestInit): Promise<Loaded<T>> {
  try {
    const response = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
    if (!response.ok) throw new Error(`${response.status} ${path}`);
    return { data: (await response.json()) as T, sample: response.headers.get(FIXTURE_HEADER) === "true" };
  } catch {
    return { data: fallback as T, sample: true };
  }
}

const site = (bbl: string) => `/api/sites/${encodeURIComponent(bbl)}`;

export const api = {
  layers: () => request<LayerCatalogEntry[]>("/api/layers", layerCatalogFixture),
  layerFeatures: (layerId: string) =>
    request<LayerFeatureCollection>(`/api/layers/${encodeURIComponent(layerId)}`, layerFeaturesFixture),
  search: (q: string) => request<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}`, searchFixture),
  siteProfile: (bbl: string) => request<SiteProfile>(`${site(bbl)}/profile`, siteProfileFixture),
  similar: (bbl: string) => request<SimilarCases>(`${site(bbl)}/similar`, similarFixture),
  warnings: (bbl: string, asOf?: string) =>
    request<EarlyWarning[]>(`${site(bbl)}/warnings${asOf ? `?as_of=${encodeURIComponent(asOf)}` : ""}`, warningsFixture),
  warningChecks: (bbl: string, asOf?: string) =>
    request<WarningRuleCheck[]>(`${site(bbl)}/warnings/checks${asOf ? `?as_of=${encodeURIComponent(asOf)}` : ""}`, warningChecksFixture),
  pattern: (bbl: string) => request<PatternScore>(`${site(bbl)}/pattern`, patternFixture),
  actions: (bbl: string) => request<ActionItem[]>(`${site(bbl)}/actions`, actionsFixture),
  cases: () => request<Case[]>("/api/cases", casesFixture),
  project: (id: string) => request<Project>(`/api/projects/${encodeURIComponent(id)}`, projectFixture),
  chat: (body: ChatRequest) =>
    request<ChatResponse>("/api/chat", chatFixture, { method: "POST", body: JSON.stringify(body) }),
};
