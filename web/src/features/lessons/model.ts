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

type Tagged = Narrowable & Pick<Lesson, "id" | "tagged">;

/** For a case's popup: every lesson the case is tagged with, and whether from a reported cause or the event only. */
export function lessonsByCase<T extends Tagged>(lessons: T[]): Map<string, { lesson: T; basis: Lesson["tagged"][number]["basis"] }[]> {
  const out = new Map<string, { lesson: T; basis: Lesson["tagged"][number]["basis"] }[]>();
  for (const lesson of lessons) {
    for (const t of lesson.tagged ?? []) {
      out.set(t.case_id, [...(out.get(t.case_id) ?? []), { lesson, basis: t.basis }]);
    }
  }
  return out;
}

/** "By project": every similar case for every option; once narrowed, only cases in the lessons that remain. */
export function casesFor<R extends { case_id: string }>(results: R[], lessons: Tagged[], option: Option, scopes: WorkType[]): R[] {
  if (option === "all" && scopes.length === 0) return results;
  const keep = new Set(filterLessons(lessons, option, scopes).flatMap((l) => (l.tagged ?? []).map((t) => t.case_id)));
  return results.filter((r) => keep.has(r.case_id));
}

/** "Watch out for": the lessons most of the listed projects share, most first (ties keep the worst-first order),
    at most `n`. Counts are of the listed projects, so they match the list below. */
export function topRisks<T extends Tagged>(lessons: T[], listed: { case_id: string }[], n = 3): { lesson: T; count: number }[] {
  const ids = new Set(listed.map((r) => r.case_id));
  return lessons
    .map((lesson) => ({ lesson, count: (lesson.tagged ?? []).filter((t) => ids.has(t.case_id)).length }))
    .filter((x) => x.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, n);
}
