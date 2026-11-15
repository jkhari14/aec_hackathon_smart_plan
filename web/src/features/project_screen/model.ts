// The project screen's rules, kept free of React and the API so they can be tested on their own
// (web/tests/project_screen_model.test.ts): the setup cards, the scope sent to the checklist, who owns an
// item, how the checklist groups, and when a document slot is worth showing.
import type { ActionItem, ConstructionType, Discipline, JobType, Role, WorkType } from "../../contracts";

export const WORK_TYPE_CARDS: { value: JobType; label: string; hint: string }[] = [
  { value: "new_building", label: "New construction", hint: "A new building on the lot" },
  { value: "alteration", label: "Modification to existing structure", hint: "Work on a building that stays" },
  { value: "demolition", label: "Demolition", hint: "Taking a building down" },
];

export const CONSTRUCTION_CARDS: { value: ConstructionType; label: string }[] = [
  { value: "wood", label: "Wood frame" },
  { value: "masonry", label: "Masonry" },
  { value: "steel", label: "Steel" },
  { value: "concrete", label: "Concrete" },
  { value: "unknown", label: "Not sure" },
];

/** The scope a user can tick. "scaffold" stands for scaffolding and the sidewalk shed together. */
export type ScopeOption = "excavation" | "foundation" | "support_of_excavation" | "underpinning" | "structural" | "facade" | "scaffold";

export const SCOPE_OPTIONS: { value: ScopeOption; label: string }[] = [
  { value: "excavation", label: "Excavation" },
  { value: "foundation", label: "Foundation" },
  { value: "support_of_excavation", label: "Support of excavation" },
  { value: "underpinning", label: "Underpinning" },
  { value: "structural", label: "Structural" },
  { value: "facade", label: "Façade" },
  { value: "scaffold", label: "Scaffold / sidewalk shed" },
];

// Same order and defaults as site_profile/work_types.py (_ORDER, DEFAULT_WORK_TYPES).
const ORDER: WorkType[] = [
  "earth_work", "excavation", "foundation", "support_of_excavation", "underpinning", "structural", "facade", "demolition",
  "sprinkler", "standpipe", "plumbing", "mechanical", "sidewalk_shed", "scaffold", "construction_fence",
];
const JOB_DEFAULTS: Record<JobType, WorkType[]> = {
  new_building: ["earth_work", "excavation", "foundation", "support_of_excavation", "structural", "plumbing", "mechanical",
    "sprinkler", "standpipe", "sidewalk_shed", "construction_fence"],
  alteration: ["structural", "plumbing", "mechanical", "sprinkler", "sidewalk_shed", "scaffold"],
  demolition: ["demolition", "sidewalk_shed", "construction_fence", "scaffold"],
};
const EARTH: WorkType[] = ["excavation", "foundation", "support_of_excavation", "underpinning"];
// Work types the scope cards decide; every other default of the job is kept as it is.
const DECIDED_BY_SCOPE = new Set<WorkType>(["earth_work", ...EARTH, "structural", "facade", "scaffold", "sidewalk_shed"]);

const ordered = (types: Iterable<WorkType>): WorkType[] => {
  const wanted = new Set(types);
  return ORDER.filter((w) => wanted.has(w));
};

/** The scope cards pre-ticked for a job type. */
export function defaultScope(job: JobType): ScopeOption[] {
  const defaults = new Set(JOB_DEFAULTS[job]);
  return SCOPE_OPTIONS.map((o) => o.value).filter((o) =>
    o === "scaffold" ? defaults.has("scaffold") || defaults.has("sidewalk_shed") : defaults.has(o));
}

/** The work types sent to the checklist: the job's other work, plus what was ticked. */
export function scopeValues(job: JobType, picked: ScopeOption[]): WorkType[] {
  const out = new Set<WorkType>(JOB_DEFAULTS[job].filter((w) => !DECIDED_BY_SCOPE.has(w)));
  for (const option of picked) {
    if (option === "scaffold") {
      out.add("scaffold");
      out.add("sidewalk_shed");
    } else {
      out.add(option);
    }
  }
  if (EARTH.some((w) => out.has(w))) out.add("earth_work");
  return ordered(out);
}

/** Scope options back from a project's saved work types, to show what was picked. */
export function pickedScope(workTypes: WorkType[]): ScopeOption[] {
  const have = new Set(workTypes);
  return SCOPE_OPTIONS.map((o) => o.value).filter((o) => have.has(o));
}

export const ROLES: Role[] = ["architect", "structural_engineer", "developer", "contractor"];

const OWNER: Record<Discipline, Role> = {
  architect: "architect",
  structural: "structural_engineer",
  geotech: "structural_engineer",
  contractor: "contractor",
};

export const ownerFor = (discipline: Discipline): Role => OWNER[discipline];

/** Items with an owner set from their discipline where they have none. With `members`, only a role the
    project has is assigned (the store refuses an owner it has no member for); others stay unassigned. */
export function withOwners(items: ActionItem[], members?: Role[]): ActionItem[] {
  return items.map((item) => {
    const owner = item.owner_role ?? ownerFor(item.discipline);
    return { ...item, owner_role: !members || members.includes(owner) ? owner : null };
  });
}

export type OwnerGroup = { role: Role | null; items: ActionItem[] };

/** Groups in role order, unassigned last, empty groups left out; life-safety items first inside each. */
export function groupByOwner(items: ActionItem[]): OwnerGroup[] {
  const order: (Role | null)[] = [...ROLES, null];
  return order
    .map((role) => ({
      role,
      items: items
        .filter((i) => (i.owner_role ?? null) === role)
        .sort((a, b) => Number(b.life_safety) - Number(a.life_safety)),
    }))
    .filter((g) => g.items.length > 0);
}

/** What the site profile says about the neighbours; unknown is treated as not attached. */
export type SiteFacts = { attached?: boolean };

export type DocSlot = {
  id: string;
  label: string;
  hint: string;
  relevant: (job: JobType | null, scope: WorkType[], site?: SiteFacts) => boolean;
};

const has = (scope: WorkType[], ...types: WorkType[]) => types.some((t) => scope.includes(t));
const digging = (scope: WorkType[]) => has(scope, "earth_work", ...EARTH);

export const DOC_SLOTS: DocSlot[] = [
  { id: "survey", label: "Site survey", hint: "Lot lines, levels and existing conditions", relevant: () => true },
  { id: "architectural", label: "Architectural drawings", hint: "Plans, sections and elevations", relevant: () => true },
  {
    id: "structural", label: "Structural drawings", hint: "Framing, foundations and details",
    relevant: (job, scope) => job === "alteration" || has(scope, "structural", "foundation"),
  },
  { id: "geotech", label: "Geotechnical report", hint: "Borings, soil and groundwater", relevant: (_job, scope) => digging(scope) },
  {
    id: "soe", label: "Support of excavation / underpinning plan", hint: "Stamped drawings for the support design",
    relevant: (_job, scope) => has(scope, "support_of_excavation", "underpinning"),
  },
  {
    id: "neighbor_survey", label: "Pre-construction survey of neighbours", hint: "Condition of adjoining buildings before work",
    relevant: (_job, scope, site) => digging(scope) || site?.attached === true,
  },
  { id: "demolition", label: "Demolition plan", hint: "Sequence and protection of the public", relevant: (job) => job === "demolition" },
];

/** Items someone else's document added to `role`'s list (or flagged there) after `since` (an ISO time):
    the "new for you" set. Drafted items carry no `added_at`, so they are never new. */
export function newForRole(items: ActionItem[], role: Role, since: string | null): ActionItem[] {
  const after = since ? Date.parse(since) : Number.NEGATIVE_INFINITY;
  return items.filter((i) =>
    i.owner_role === role && i.added_at && i.added_by_role && i.added_by_role !== role && Date.parse(i.added_at) > after);
}

/** A short line for an item's provenance: who and when (the reason itself is `added_reason`). */
export function addedLine(item: Pick<ActionItem, "added_by_role" | "added_at">, roleLabels: Record<Role, string>): string | null {
  if (!item.added_by_role || !item.added_at) return null;
  const at = new Date(item.added_at);
  const when = Number.isNaN(at.getTime())
    ? item.added_at
    : at.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  return `${roleLabels[item.added_by_role]} · ${when}`;
}
