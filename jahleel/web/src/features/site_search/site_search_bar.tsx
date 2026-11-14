import type { BriefListing, ProjectType } from "../../brief/brief_types";
import { RoastDial, type RoastIntensity } from "../roast/roast_dial";

const PROJECT_TYPES: { value: ProjectType; label: string }[] = [
  { value: "excavation_next_to_existing", label: "Excavation next to existing" },
  { value: "new_building", label: "New building" },
  { value: "renovation", label: "Renovation" },
];

type Props = {
  listings: BriefListing[];
  slug: string;
  projectType: ProjectType;
  asOf: string | null;
  intensity: RoastIntensity;
  onSlug: (slug: string) => void;
  onProjectType: (projectType: ProjectType) => void;
  onAsOf: (asOf: string | null) => void;
  onIntensity: (intensity: RoastIntensity) => void;
};

// Demo sites only for now; free-text address search lands when the API calls data_pull live.
export function SiteSearchBar(props: Props) {
  return (
    <div className="flex flex-wrap items-end gap-4 border-b border-stone-300 bg-white px-4 py-3">
      <label className="flex w-full flex-col text-xs sm:w-auto">Site
        <select className="w-full rounded border px-2 py-1 text-sm" value={props.slug} onChange={(e) => props.onSlug(e.target.value)}>
          {props.listings.map((l) => <option key={l.slug} value={l.slug}>{l.address}</option>)}
        </select>
      </label>
      <label className="flex flex-col text-xs">Project
        <select className="rounded border px-2 py-1 text-sm" value={props.projectType}
          onChange={(e) => props.onProjectType(e.target.value as ProjectType)}>
          {PROJECT_TYPES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
      </label>
      <label className="flex flex-col text-xs">As of
        <span className="flex gap-1">
          <input type="date" className="rounded border px-2 py-1 text-sm" value={props.asOf ?? ""}
            onChange={(e) => props.onAsOf(e.target.value || null)} />
          {props.asOf && <button className="text-xs underline" onClick={() => props.onAsOf(null)}>today</button>}
        </span>
      </label>
      <RoastDial value={props.intensity} onChange={props.onIntensity} />
    </div>
  );
}
