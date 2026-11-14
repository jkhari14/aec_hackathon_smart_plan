import type { Brief, PublicRecord } from "./brief_types";

// The checklist engine's rule: a record counts only if it is dated BEFORE the as-of day.
// Status is today's, so the UI never says a record was "open" on that day.
export function recordsAsOf(brief: Brief, asOf: string | null): PublicRecord[] {
  if (!asOf) return brief.records;
  return brief.records.filter((record) => record.date != null && record.date < asOf);
}
