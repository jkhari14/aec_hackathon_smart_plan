// Every data source on the map, with its toggle, status, count, source link and updated date.
// A failed source says "couldn't load", never zero; a capped one says "at least".
import { useEffect, useState } from "react";

import type { LayerCatalogEntry } from "../../contracts";
import { HAZARD_COLORS } from "../city_map/map_style";

export type LayerState = { entry: LayerCatalogEntry; on: boolean; loaded: number | null; sample: boolean };

type Props = { layers: LayerState[]; onToggle: (layerId: string) => void; onOpenChange?: (open: boolean) => void };

export function countLabel({ entry, loaded, sample }: LayerState): string {
  if (entry.status === "error") return "Couldn't load";
  const n = entry.feature_count ?? loaded;
  if (n == null) return "Loading…";
  // The offline sample has records for one layer only; an empty sample is not "0 in the city".
  if (n === 0 && sample) return "No sample records";
  const shown = n.toLocaleString();
  return entry.status === "capped" ? `at least ${shown}` : shown;
}

export function LayerPanel({ layers, onToggle, onOpenChange }: Props) {
  const [open, setOpen] = useState(true);
  useEffect(() => onOpenChange?.(open), [open, onOpenChange]);
  return (
    <section className="absolute right-4 top-4 w-80 overflow-hidden rounded-lg border border-line bg-panel/90 backdrop-blur"
      aria-label="Map layers">
      <button className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-semibold"
        onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        Layers <span className="text-xs font-normal text-muted">{open ? "Hide" : `${layers.filter((l) => l.on).length} on`}</span>
      </button>
      {open && (
        <ul className="max-h-[70vh] space-y-1 overflow-y-auto px-2 pb-3">
          {layers.length === 0 && <li className="mx-2 h-10 animate-pulse rounded bg-line/40" />}
          {layers.map((layer) => {
            const { entry, on } = layer;
            const failed = entry.status === "error";
            return (
              <li key={entry.layer_id} className="rounded-md px-2 py-2 hover:bg-line/30" title={entry.description}>
                <label className={`flex items-start gap-3 ${failed ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}>
                  <input type="checkbox" className="mt-1 accent-current" checked={on && !failed} disabled={failed}
                    onChange={() => onToggle(entry.layer_id)} style={{ color: HAZARD_COLORS[entry.hazard] }} />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className="flex items-center gap-2 text-sm">
                        <span className="inline-block h-2 w-2 shrink-0 rounded-full" aria-hidden
                          style={{ background: HAZARD_COLORS[entry.hazard] }} />
                        {entry.name}
                      </span>
                      <span className={`shrink-0 text-xs tabular-nums ${failed ? "text-sample" : "text-muted"}`}>
                        {countLabel(layer)}
                      </span>
                    </span>
                    <span className="mt-0.5 block text-xs text-muted">
                      <a className="underline decoration-line underline-offset-2 hover:text-text" href={entry.source_url}
                        target="_blank" rel="noreferrer">{entry.source_name}</a>
                      {" · "}
                      {entry.updated_at ? `updated ${entry.updated_at}` : "update date unknown"}
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
