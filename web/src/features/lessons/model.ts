// "What could go wrong here": the rules for narrowing lessons, kept free of React so they can be tested
// (web/tests/lessons_model.test.ts). An option keeps the lessons that apply to it; scopes narrow further.
import type { JobType, Lesson, WorkType } from "../../contracts";
import type { ScopeOption } from "../project_screen/model";

export type Option = "all" | Lesson["options"][number];

export const OPTIONS: { value: Option; label: string }[] = [
  { value: "all", label: "Every option" },
  { value: "renovate", label: "Renovate" },
  { value: "demolish_rebuild", label: "Demolish and rebuild" },
  { value: "new_build", label: "New build" },
];

type Narrowable = Pick<Lesson, "options" | "scopes">;

export function filterLessons<T extends Narrowable>(lessons: T[], option: Option, scopes: WorkType[]): T[] {
  return lessons
    .filter((l) => option === "all" || l.options.includes(option))
    .filter((l) => scopes.length === 0 || l.scopes.some((s) => scopes.includes(s)));
}

/** The scope chips worth offering: every scope among the lessons this option leaves, in first-seen order. */
export function scopeChoices(lessons: Narrowable[], option: Option): WorkType[] {
  return [...new Set(filterLessons(lessons, option, []).flatMap((l) => l.scopes))];
}

const SETUP_SCOPES = new Set<string>(["excavation", "foundation", "support_of_excavation", "underpinning", "structural",
  "facade", "scaffold", "demolition"]);

/** What "Start a project" carries into setup: the job type and the picked scopes it can show. Null for "all". */
export function setupFor(option: Option, scopes: WorkType[]): { jobType: JobType; scope: ScopeOption[] } | null {
  if (option === "all") return null;
  const picked = scopes.filter((s) => SETUP_SCOPES.has(s)) as ScopeOption[];
  if (option === "renovate") return { jobType: "alteration", scope: picked };
  if (option === "demolish_rebuild") return { jobType: "new_building", scope: picked.length ? picked : ["demolition"] };
  return { jobType: "new_building", scope: picked };
}
