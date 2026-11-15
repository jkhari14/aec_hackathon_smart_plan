// The site panel body: overview (top signals, then lot facts tucked into sections), similar cases and
// actions. Loads its three sources independently, so each tab shows a skeleton until its own data lands.
import "./site_panel.css";

import { useEffect, useState, type ReactNode } from "react";

import { api, type Loaded } from "../../api/client";
import type { ActionItem, SimilarCases as SimilarCasesData, SiteProfile } from "../../contracts";
import { Badge, formatDate, SkeletonCard, Tabs } from "../../design";
import { ActionsList } from "../actions/ActionsList";
import { SimilarCases } from "../similar_cases/SimilarCases";
import { LotFacts, Neighbors, SourcesChecked, WorkAndGround } from "./LotFacts";
import { Signals } from "./Signals";

export type SiteTab = "overview" | "similar" | "actions";

type Data = {
  profile?: Loaded<SiteProfile>;
  similar?: Loaded<SimilarCasesData>;
  actions?: Loaded<ActionItem[]>;
};

export function useSiteData(bbl: string | null) {
  const [data, setData] = useState<Data>({});
  useEffect(() => {
    setData({});
    if (!bbl) return;
    let live = true;
    const put = <K extends keyof Data>(key: K) => (value: Data[K]) => live && setData((d) => ({ ...d, [key]: value }));
    api.siteProfile(bbl).then(put("profile"));
    api.similar(bbl).then(put("similar"));
    api.actions(bbl).then(put("actions"));
    return () => {
      live = false;
    };
  }, [bbl]);
  return data;
}

export function SitePanel({ data, tab, onTab }: { data: Data; tab: SiteTab; onTab: (t: SiteTab) => void }) {
  const { profile, similar, actions } = data;
  const sample = [profile, similar, actions].some((x) => x?.sample);
  const count = (n?: number) => (n == null ? "" : ` ${n}`);

  return (
    <>
      <div className="fs-site__bar">
        <Tabs<SiteTab>
          label="Site sections"
          value={tab}
          onChange={onTab}
          options={[
            { value: "overview", label: "Overview" },
            { value: "similar", label: <span className="fs-num">Similar{count(similar?.data.results.length)}</span> },
            { value: "actions", label: <span className="fs-num">Actions{count(actions?.data.length)}</span> },
          ]}
        />
        <div className="fs-site__meta">
          {profile?.data.as_of && <span className="fs-num">Records dated before {formatDate(profile.data.as_of)}</span>}
          {sample && <Badge tone="sample">Sample data</Badge>}
        </div>
      </div>

      {tab === "overview" &&
        (profile ? (
          <>
            <Section title="Top signals">
              <Signals signals={profile.data.signals} datasets={profile.data.datasets} />
            </Section>
            <Section title="Work and ground" collapsible>
              <WorkAndGround profile={profile.data} />
            </Section>
            <Section title={`Neighbors (${profile.data.neighbors.length})`} collapsible>
              <Neighbors profile={profile.data} />
            </Section>
            <Section title="Lot facts" collapsible>
              <LotFacts profile={profile.data} />
            </Section>
            <Section title="Sources checked" collapsible>
              <SourcesChecked profile={profile.data} />
            </Section>
          </>
        ) : (
          <Loading />
        ))}

      {tab === "similar" && (similar ? <SimilarCases results={similar.data.results} /> : <Loading />)}
      {tab === "actions" && (actions ? <ActionsList actions={actions.data} /> : <Loading />)}
    </>
  );
}

function Section({ title, children, collapsible }: { title: string; children: ReactNode; collapsible?: boolean }) {
  if (!collapsible) {
    return (
      <section className="fs-site__section">
        <h3 className="fs-label">{title}</h3>
        {children}
      </section>
    );
  }
  return (
    <details className="fs-site__section fs-site__fold">
      <summary className="fs-label">{title}</summary>
      <div className="fs-site__foldbody">{children}</div>
    </details>
  );
}

function Loading() {
  return (
    <div className="fs-site__section" aria-busy="true">
      <SkeletonCard lines={2} />
      <SkeletonCard lines={2} />
      <SkeletonCard lines={1} />
    </div>
  );
}
