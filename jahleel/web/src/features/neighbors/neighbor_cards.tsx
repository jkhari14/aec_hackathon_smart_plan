import { mentionsStopWorkAsOf } from "../../brief/brief_as_of";
import type { Lot, PublicRecord } from "../../brief/brief_types";

type Props = { lots: Lot[]; visible: PublicRecord[]; asOf: string | null; selectedBbl: string | null; onSelect: (bbl: string) => void };

export function NeighborCards({ lots, visible, asOf, selectedBbl, onSelect }: Props) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {lots.map((lot) => {
        const records = visible.filter((r) => r.bbl === lot.bbl);
        // 311 requests can repeat a DOB complaint (no shared key), so they're counted apart, never added.
        const requests311 = records.filter((r) => r.dataset_key === "dob_311_requests").length;
        // A dataset that hit the row cap makes its count a floor.
        const capped = new Set(lot.datasets.filter((d) => d.status === "ok" && d.truncated).map((d) => d.key));
        const cappedOther = [...capped].some((key) => key !== "dob_311_requests");
        const failed = lot.datasets.filter((d) => d.status !== "ok");
        const tallest = Math.max(0, ...lot.buildings.map((b) => b.height_roof_ft ?? 0));
        return (
          <button key={lot.bbl} onClick={() => onSelect(lot.bbl)}
            className={`rounded border bg-white p-2 text-left ${selectedBbl === lot.bbl ? "ring-2 ring-neighbor" : ""}`}>
            <p className="text-sm font-semibold">{lot.facts?.address ?? `Lot ${lot.bbl} (no PLUTO record)`}</p>
            <p className="text-xs text-stone-600">
              BBL {lot.bbl} · built {lot.facts?.year_built ?? "?"} · {lot.facts?.floors ?? "?"} floors · class{" "}
              {lot.facts?.building_class ?? "?"}{tallest ? ` · roof ${tallest.toFixed(0)} ft` : ""}
            </p>
            {(lot.facts?.landmark || lot.facts?.historic_district) && (
              <p className="text-xs text-stone-600">
                PLUTO lists{lot.facts.landmark ? ` landmark: ${lot.facts.landmark}` : ""}
                {lot.facts.landmark && lot.facts.historic_district ? ";" : ""}
                {lot.facts.historic_district ? ` historic district: ${lot.facts.historic_district}` : ""} (a hint; check with LPC)
              </p>
            )}
            <p className="mt-1 text-xs">
              {cappedOther ? "at least " : ""}{records.length - requests311} records dated {asOf ? `before ${asOf}` : "to date"}
              {requests311 > 0 ? ` · ${capped.has("dob_311_requests") ? "at least " : ""}${requests311} 311 requests, which may repeat a DOB complaint` : ""}
              {records.some((r) => mentionsStopWorkAsOf(r, asOf)) ? " · mentions a stop-work order" : ""}
            </p>
            {failed.length > 0 && (
              <p className="mt-1 text-xs text-site">Couldn't load: {failed.map((d) => d.name).join(", ")} (unknown, not zero)</p>
            )}
          </button>
        );
      })}
    </div>
  );
}
