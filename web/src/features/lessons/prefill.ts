// "Start a project with this option": the lessons panel leaves the option and scopes here for the setup screen,
// which reads them once for the same lot. Session storage, so nothing reaches the URL; if storage is blocked,
// setup simply starts empty.
import type { JobType } from "../../contracts";
import type { ScopeOption } from "../project_screen/model";

const KEY = "foresite.setup.prefill";
export type Prefill = { bbl: string; jobType: JobType; scope: ScopeOption[] };

export function savePrefill(prefill: Prefill) {
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(prefill));
  } catch {
    // Storage blocked: setup starts empty, which still works.
  }
}

/** The pre-fill for this lot, once: it is cleared as it is read. */
export function takePrefill(bbl: string): Prefill | null {
  try {
    const raw = window.sessionStorage.getItem(KEY);
    window.sessionStorage.removeItem(KEY);
    const value = raw ? (JSON.parse(raw) as Prefill) : null;
    return value && value.bbl === bbl ? value : null;
  } catch {
    return null;
  }
}
