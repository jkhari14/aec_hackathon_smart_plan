// Address search that picks a site. Camilo's command bar (PR 1) can call the same onPick.
import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { SearchResult } from "../../contracts";
import type { Picked } from "./site_lots";

type Props = { picked: Picked | null; status: string | null; onPick: (site: Picked) => void };

export function SiteSearch({ picked, status, onPick }: Props) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);

  useEffect(() => {
    if (q.trim().length < 3) {
      setResults([]);
      return;
    }
    const timer = setTimeout(() => api.search(q.trim()).then((r) => setResults(r.data)), 250);
    return () => clearTimeout(timer);
  }, [q]);

  const pick = (r: SearchResult) => {
    setQ("");
    setResults([]);
    onPick({ label: r.label, bbl: r.bbl, lat: r.lat, lon: r.lon });
  };

  return (
    <div className="absolute left-1/2 top-4 w-[min(30rem,calc(100%-44rem))] min-w-64 -translate-x-1/2">
      <input className="w-full rounded-lg border border-line bg-panel/90 px-4 py-2.5 text-sm text-text placeholder:text-muted backdrop-blur focus:border-muted focus:outline-none"
        placeholder="Search an NYC address, or click a building" value={q} aria-label="Search an address"
        onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && results[0] && pick(results[0])} />
      {results.length > 0 && (
        <ul className="mt-1 overflow-hidden rounded-lg border border-line bg-panel/95 text-sm backdrop-blur">
          {results.map((r) => (
            <li key={r.bbl}>
              <button className="w-full px-4 py-2 text-left hover:bg-line/40" onClick={() => pick(r)}>
                {r.label} <span className="text-xs text-muted tabular-nums">BBL {r.bbl}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {picked && results.length === 0 && (
        <p className="mt-1 rounded-lg bg-panel/80 px-4 py-1.5 text-xs text-muted backdrop-blur">
          <span className="text-text">{picked.label}</span> · BBL {picked.bbl}
          {status ? ` · ${status}` : ""}
        </p>
      )}
    </div>
  );
}
