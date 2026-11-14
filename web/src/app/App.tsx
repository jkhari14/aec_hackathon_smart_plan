// Placeholder shell: full-bleed map with the layer catalog on top. Camilo's PR 10 replaces this with the
// real app shell; until then it proves the contracts, client and map wire together.
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { LayerCatalogEntry, LayerFeature } from "../contracts";
import { CityMap } from "../features/city_map/CityMap";

export function App() {
  const [layers, setLayers] = useState<LayerCatalogEntry[]>([]);
  const [features, setFeatures] = useState<LayerFeature[]>([]);
  const [sample, setSample] = useState(false);

  useEffect(() => {
    api.layers().then((result) => {
      setLayers(result.data);
      setSample((s) => s || result.sample);
    });
    api.layerFeatures("construction_incidents").then((result) => {
      setFeatures(result.data.features);
      setSample((s) => s || result.sample);
    });
  }, []);

  return (
    <main className="relative h-full overflow-hidden">
      <CityMap features={features} />
      <aside className="absolute left-4 top-4 w-72 rounded-lg border border-line bg-panel/90 p-4 backdrop-blur">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">ForeSite</h1>
          {sample && (
            <span className="rounded bg-sample/15 px-2 py-0.5 text-xs font-medium text-sample">Sample data</span>
          )}
        </div>
        <ul className="mt-3 space-y-1.5 text-sm">
          {layers.map((layer) => (
            <li key={layer.layer_id} className="flex items-center justify-between gap-2">
              <span>{layer.name}</span>
              <span className="text-xs text-muted">{layer.status === "ok" ? layer.hazard : "unavailable"}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-muted">
          Public records and reported cases only. Not a DOB determination or engineering advice.
        </p>
      </aside>
    </main>
  );
}
