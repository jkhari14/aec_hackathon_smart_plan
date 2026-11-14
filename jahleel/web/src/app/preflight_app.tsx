import { useEffect, useMemo, useState } from "react";

import { recordsAsOf } from "../brief/brief_as_of";
import { loadBrief, loadBriefList } from "../brief/brief_load";
import type { Brief, BriefListing, ProjectType } from "../brief/brief_types";
import { ChecklistLanes } from "../features/checklist/checklist_lanes";
import { BriefExportButtons } from "../features/export/brief_export_buttons";
import { NeighborCards } from "../features/neighbors/neighbor_cards";
import { PrecedentList } from "../features/precedents/precedent_list";
import type { RoastIntensity } from "../features/roast/roast_dial";
import { SiteMapView } from "../features/site_map/site_map_view";
import { SiteRecordList } from "../features/site_record/site_record_list";
import { SiteSearchBar } from "../features/site_search/site_search_bar";

// The URL carries the brief's inputs, so a shared link reopens the same view.
function readUrl() {
  const q = new URLSearchParams(window.location.search);
  return { slug: q.get("site"), asOf: q.get("as_of"), projectType: q.get("project") as ProjectType | null };
}

export function PreflightApp() {
  const initial = readUrl();
  const [listings, setListings] = useState<BriefListing[]>([]);
  const [slug, setSlug] = useState<string | null>(initial.slug);
  const [projectType, setProjectType] = useState<ProjectType>(initial.projectType ?? "excavation_next_to_existing");
  const [asOf, setAsOf] = useState<string | null>(initial.asOf);
  const [intensity, setIntensity] = useState<RoastIntensity>("senior_examiner");
  const [brief, setBrief] = useState<Brief | null>(null);
  const [offline, setOffline] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBbl, setSelectedBbl] = useState<string | null>(null);
  const [adjoiningOwnerView, setAdjoiningOwnerView] = useState(false);

  useEffect(() => {
    loadBriefList().then(({ data }) => {
      setListings(data);
      setSlug((current) => current ?? data[0]?.slug ?? null);
    }).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!slug) return;
    loadBrief(slug, asOf).then(({ data, offline: wasOffline }) => {
      setBrief(data);
      setOffline(wasOffline);
      setError(null);
    }).catch((e: Error) => setError(e.message));
  }, [slug, asOf]);

  useEffect(() => {
    const q = new URLSearchParams();
    if (slug) q.set("site", slug);
    if (asOf) q.set("as_of", asOf);
    q.set("project", projectType);
    window.history.replaceState(null, "", `?${q}`);
  }, [slug, asOf, projectType]);

  const visible = useMemo(() => (brief ? recordsAsOf(brief, asOf) : []), [brief, asOf]);
  // An offline copy for a date with no saved replay is the as-pulled checklist: say so.
  const checklistAsOfMismatch = brief != null && (brief.as_of ?? null) !== asOf;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-baseline gap-3 bg-ink px-4 py-2 text-white">
        <h1 className="text-lg font-semibold">PreFlight</h1>
        <p className="text-xs text-stone-300">What was knowable about this site and its neighbors, by whom, and when.</p>
      </header>
      {slug && (
        <SiteSearchBar listings={listings} slug={slug} projectType={projectType} asOf={asOf} intensity={intensity}
          onSlug={setSlug} onProjectType={setProjectType} onAsOf={setAsOf} onIntensity={setIntensity} />
      )}
      {offline && <p className="bg-amber-100 px-4 py-1 text-xs">API not running: showing the saved demo copy.</p>}
      {error && <p className="bg-red-100 px-4 py-1 text-xs">{error}</p>}
      {brief && (
        <main className="grid flex-1 gap-4 p-4 lg:grid-cols-[3fr_2fr]">
          <div className="space-y-4">
            <p className="text-sm">Matched: <strong>{brief.matched_label}</strong> · BBL {brief.site.bbl} · pulled {brief.pulled_at.slice(0, 10)}</p>
            <div className="h-96 overflow-hidden rounded border">
              <SiteMapView brief={brief} selectedBbl={selectedBbl} onSelect={setSelectedBbl} />
            </div>
            <h2 className="font-semibold">Touching lots</h2>
            <NeighborCards lots={brief.touching_lots} visible={visible} asOf={asOf} selectedBbl={selectedBbl} onSelect={setSelectedBbl} />
            <h2 className="font-semibold">Site record {asOf ? `as of ${asOf}` : ""}</h2>
            <SiteRecordList records={visible.filter((r) => r.bbl === brief.site.bbl)} />
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Checklist by party</h2>
              <label className="flex items-center gap-1 text-xs">
                <input type="checkbox" checked={adjoiningOwnerView} onChange={(e) => setAdjoiningOwnerView(e.target.checked)} />
                Adjoining owner view
              </label>
            </div>
            <p className="text-xs">
              {brief.checklist_summary.applies} duties apply on the record · {brief.checklist_summary.open_gaps} open gaps ·{" "}
              {brief.checklist_summary.needs_input} need project input
              {brief.as_of ? ` · records dated before ${brief.as_of}` : ""}
            </p>
            {checklistAsOfMismatch && (
              <p className="bg-amber-100 px-2 py-1 text-xs">No saved replay for this date offline: the checklist is as pulled.</p>
            )}
            <ChecklistLanes rows={brief.checklist} intensity={intensity} adjoiningOwnerView={adjoiningOwnerView} />
            <h2 className="font-semibold">Past failures nearby</h2>
            <PrecedentList precedents={brief.precedents} />
            <BriefExportButtons brief={brief} />
            <ul className="list-disc pl-4 text-xs text-stone-500">{brief.caveats.map((c) => <li key={c}>{c}</li>)}</ul>
          </div>
        </main>
      )}
    </div>
  );
}
