// Which layers a work type switches on when you come back to the map from its project. Applied once per
// project and work type, so a toggle you make afterwards is kept.
import type { JobType } from "../contracts";

export const WORK_LAYERS: Record<JobType, string[]> = {
  new_building: ["construction_incidents", "structural_complaints", "watchlist", "fema_flood_zones", "e_designations"],
  alteration: ["structural_complaints", "unsafe_facades", "vacate_orders", "watchlist"],
  demolition: ["construction_incidents", "structural_complaints", "unsafe_facades", "watchlist"],
};

/** The work type's layers that the catalog actually has. */
export function layersForWork(job: JobType, available: string[]): Set<string> {
  const have = new Set(available);
  return new Set(WORK_LAYERS[job].filter((id) => have.has(id)));
}

/** `key` is `${projectId}:${jobType}`; apply when it is new. */
export const shouldApply = (lastApplied: string | null, key: string | null): boolean => key !== null && key !== lastApplied;
