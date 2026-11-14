import type { Brief } from "../../brief/brief_types";
import { briefGeoJson } from "./brief_geojson";

function download(name: string, body: object) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(body, null, 1)], { type: "application/json" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  URL.revokeObjectURL(url);
}

// The same brief the API serves: Grasshopper, Revit or the voice agent can read either file.
export function BriefExportButtons({ brief }: { brief: Brief }) {
  return (
    <div className="flex gap-2 text-xs">
      <button className="rounded border bg-white px-2 py-1" onClick={() => download(`${brief.slug}.brief.json`, brief)}>
        Download brief (JSON)
      </button>
      <button className="rounded border bg-white px-2 py-1"
        onClick={() => download(`${brief.slug}.geojson`, briefGeoJson(brief))}>
        Download lots + buildings (GeoJSON)
      </button>
    </div>
  );
}
