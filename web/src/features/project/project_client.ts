// The project workspace's calls to the API. A project is real data two people share, so nothing here
// falls back to a fixture: a read or a write that did not reach the store says so.
import { API_BASE, STATIC } from "../../api/client";
import type { components } from "../../api_types";
import type { ActionItem, Project, ProjectCreate } from "../../contracts";

type S = components["schemas"];
export type Role = S["ProjectMember"]["role"];
export type PinCreate = S["PinCreate"];
export type ProjectPin = S["ProjectPin"];
export type ActionItemUpdate = S["ActionItemUpdate"];
export type DrawingConfirm = S["DrawingConfirm"];
export type StructuralModel = S["StructuralModel"];

/** A drawing reading: the AI's suggestion, saved nowhere until the uploader confirms it. */
export type DrawingReading =
  | { status: "ok"; model: StructuralModel; evidence: string; note: string }
  | { status: "refused"; reason: string }
  | { status: "unreachable" };

export const ROLE_LABELS: Record<Role, string> = {
  architect: "Architect",
  structural_engineer: "Structural engineer",
  developer: "Developer",
  contractor: "Contractor",
};

export type ProjectRead =
  | { status: "ok"; project: Project; etag: string | null; sample: boolean }
  | { status: "unchanged" }
  | { status: "not_found" }
  | { status: "unreachable" };

export type ProjectWrite =
  | { status: "ok"; project: Project; etag: string | null }
  | { status: "sample" } // the server answered from sample data: nothing was saved
  | { status: "refused"; reason: string }
  | { status: "unreachable" };

const FIXTURE_HEADER = "X-ForeSite-Fixture";
const url = (projectId?: string, rest = "") => `${API_BASE}/api/projects${projectId ? `/${encodeURIComponent(projectId)}` : ""}${rest}`;

function reasonFrom(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (!Array.isArray(detail)) return null;
  const lines = detail
    .map((item) => (typeof item === "string" ? item : typeof item?.msg === "string" ? item.msg : null))
    .filter((line): line is string => line !== null);
  return lines.length ? lines.join("; ") : null;
}

const looksLikeProject = (value: unknown): value is Project =>
  typeof value === "object" && value !== null && typeof (value as Project).id === "string" && Array.isArray((value as Project).items);

/** With `etag`, an unchanged project comes back as "unchanged" and no body. */
export async function readProject(projectId: string, etag: string | null, signal?: AbortSignal): Promise<ProjectRead> {
  if (STATIC) return { status: "unreachable" };
  try {
    const response = await fetch(url(projectId), { headers: etag ? { "If-None-Match": etag } : {}, signal });
    if (response.status === 304) return { status: "unchanged" };
    if (response.status === 404) return { status: "not_found" };
    const body: unknown = response.ok ? await response.json() : null;
    if (!looksLikeProject(body)) return { status: "unreachable" };
    return { status: "ok", project: body, etag: response.headers.get("ETag"), sample: response.headers.get(FIXTURE_HEADER) === "true" };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    return { status: "unreachable" };
  }
}

async function write(path: string, method: "POST" | "PATCH", body: unknown): Promise<ProjectWrite> {
  if (STATIC) return { status: "unreachable" };
  try {
    const response = await fetch(path, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const payload: unknown = await response.json();
    if (response.ok && looksLikeProject(payload)) {
      if (response.headers.get(FIXTURE_HEADER) === "true") return { status: "sample" };
      return { status: "ok", project: payload, etag: response.headers.get("ETag") };
    }
    const reason = response.status < 500 ? reasonFrom((payload as { detail?: unknown })?.detail) : null;
    return reason ? { status: "refused", reason } : { status: "unreachable" };
  } catch {
    return { status: "unreachable" };
  }
}

export const projectWrites = {
  create: (body: ProjectCreate) => write(url(), "POST", body),
  addItems: (projectId: string, items: ActionItem[]) => write(url(projectId, "/items"), "POST", items),
  updateItems: (projectId: string, updates: ActionItemUpdate[]) => write(url(projectId, "/items"), "PATCH", updates),
  addNote: (projectId: string, role: Role, text: string) => write(url(projectId, "/notes"), "POST", { author_role: role, text }),
  addPin: (projectId: string, pin: PinCreate) => write(url(projectId, "/pins"), "POST", pin),
  confirmDrawing: (projectId: string, body: DrawingConfirm) => write(url(projectId, "/model/confirm"), "POST", body),
};

/** Send a PDF to the drawing reader (10 to 30 s). 422: not a readable PDF; 503: no reader on this server. */
export async function readDrawing(projectId: string, file: Blob, signal?: AbortSignal): Promise<DrawingReading> {
  if (STATIC) return { status: "unreachable" };
  try {
    const response = await fetch(url(projectId, "/model/drawing"), {
      method: "POST", headers: { "Content-Type": "application/pdf" }, body: file, signal,
    });
    const payload = (await response.json().catch(() => null)) as
      | { model?: StructuralModel; evidence?: string; note?: string; detail?: unknown } | null;
    if (response.ok && payload?.model && Array.isArray(payload.model.bearing_walls_on_lot_line)) {
      return { status: "ok", model: payload.model, evidence: payload.evidence ?? "", note: payload.note ?? "" };
    }
    const reason = reasonFrom(payload?.detail);
    return reason ? { status: "refused", reason } : { status: "unreachable" };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    return { status: "unreachable" };
  }
}

/** The line to show when a write did not save, or null when it did. */
export function whyNotSaved(result: ProjectWrite): string | null {
  if (result.status === "ok") return null;
  if (result.status === "sample") return "This is the sample project: changes are not saved.";
  if (result.status === "refused") return result.reason;
  return "The project could not be reached, so this was not saved.";
}
