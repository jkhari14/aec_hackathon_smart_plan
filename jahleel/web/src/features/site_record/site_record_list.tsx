import { useState } from "react";

import { OVERLAP_311_NOTE, mentionsStopWorkAsOf, writtenBefore } from "../../brief/brief_as_of";
import type { ComplaintCodeKeys, PublicRecord } from "../../brief/brief_types";
import { ComplaintCodeLines } from "./complaint_code_lines";

type Props = { records: PublicRecord[]; asOf: string | null; codeKeys?: ComplaintCodeKeys; capped?: string[]; limit?: number };

function approvalText(r: PublicRecord, asOf: string | null): string {
  if (r.approved_on && writtenBefore(r.approved_on, asOf)) return `Approved ${r.approved_on}.`;
  return asOf ? "Not approved before this day." : "Not approved.";
}

// Status is today's; the date is when the record was issued or filed.
export function SiteRecordList({ records, asOf, codeKeys = {}, capped = [], limit = 40 }: Props) {
  const [showAll, setShowAll] = useState(false);
  const cappedNote = capped.length > 0 && (
    <p className="mb-1 text-xs text-site">Hit the 5,000-row cap, so the oldest records are missing: {capped.join(", ")}.</p>
  );
  if (records.length === 0) return <>{cappedNote}<p className="text-sm text-gap">No records dated before this day.</p></>;
  const keys = new Set(records.map((r) => r.dataset_key));
  return (
    <>
      {cappedNote}
      {keys.has("dob_311_requests") && keys.has("dob_complaints") && (
        <p className="mb-1 text-xs text-stone-600">{OVERLAP_311_NOTE}</p>
      )}
      <ul className="divide-y rounded border bg-white text-sm">
        {records.slice(0, showAll ? records.length : limit).map((r) => (
          <li key={r.id} className={`p-2 ${mentionsStopWorkAsOf(r, asOf) ? "bg-red-50" : ""}`}>
            <p className="text-xs text-stone-500">
              {r.date ?? "undated"} · {r.dataset_name} {r.record_id} · status today: {r.status_today ?? "?"}
              {r.query_url && <> · <a className="underline" href={r.query_url} target="_blank" rel="noreferrer">source</a></>}
            </p>
            <p>{r.summary}</p>
            {r.dataset_key === "dob_now_filings" && <p className="mt-1 text-xs">{approvalText(r, asOf)}</p>}
            {r.dataset_key === "dob_complaints" && <ComplaintCodeLines record={r} asOf={asOf} codeKeys={codeKeys} />}
            {r.resolution && (writtenBefore(r.resolution_recorded, asOf) ? (
              <p className="mt-1 text-xs">
                DOB's resolution, recorded {r.resolution_recorded ?? "on an unknown day"}: {r.resolution}
              </p>
            ) : (
              <p className="mt-1 text-xs text-stone-500">DOB's resolution was recorded after this day, so the replay hides it.</p>
            ))}
          </li>
        ))}
      </ul>
      {records.length > limit && (
        <p className="mt-1 text-xs text-stone-600">
          {showAll ? `All ${records.length} records shown. ` : `Showing the newest ${limit} of ${records.length}. `}
          <button className="underline" onClick={() => setShowAll(!showAll)}>{showAll ? "Show fewer" : "Show all"}</button>
        </p>
      )}
    </>
  );
}
