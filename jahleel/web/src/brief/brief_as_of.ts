import type { Brief, PublicRecord } from "./brief_types";

// The checklist engine's rule: a record counts only if it is dated BEFORE the as-of day.
// Status is today's, so the UI never says a record was "open" on that day.
export function recordsAsOf(brief: Brief, asOf: string | null): PublicRecord[] {
  if (!asOf) return brief.records;
  return brief.records.filter((record) => record.date != null && record.date < asOf);
}

// Text written after the record's own date (a stop-work mention, DOB's 311 resolution) shows only
// once it existed: undated text stays hidden in a replay, since it can't be placed.
export function writtenBefore(written: string | null | undefined, asOf: string | null): boolean {
  return !asOf || (written != null && written < asOf);
}

export function mentionsStopWorkAsOf(record: PublicRecord, asOf: string | null): boolean {
  return Boolean(record.mentions_stop_work) && writtenBefore(record.stop_work_first_mentioned, asOf);
}

export const OVERLAP_311_NOTE =
  "311 requests and DOB complaints can be the same complaint and share no key, so their counts are never added.";
