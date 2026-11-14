import { OVERLAP_311_NOTE, mentionsStopWorkAsOf, writtenBefore } from "../../brief/brief_as_of";
import type { PublicRecord } from "../../brief/brief_types";

type Props = { records: PublicRecord[]; asOf: string | null; limit?: number };

// Status is today's; the date is when the record was issued or filed.
export function SiteRecordList({ records, asOf, limit = 40 }: Props) {
  if (records.length === 0) return <p className="text-sm text-gap">No records dated before this day.</p>;
  const keys = new Set(records.map((r) => r.dataset_key));
  return (
    <>
      {keys.has("dob_311_requests") && keys.has("dob_complaints") && (
        <p className="mb-1 text-xs text-stone-600">{OVERLAP_311_NOTE}</p>
      )}
      <ul className="divide-y rounded border bg-white text-sm">
        {records.slice(0, limit).map((r) => (
          <li key={r.id} className={`p-2 ${mentionsStopWorkAsOf(r, asOf) ? "bg-red-50" : ""}`}>
            <p className="text-xs text-stone-500">
              {r.date ?? "undated"} · {r.dataset_name} {r.record_id} · status today: {r.status_today ?? "?"}
              {r.query_url && <> · <a className="underline" href={r.query_url} target="_blank" rel="noreferrer">source</a></>}
            </p>
            <p>{r.summary}</p>
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
    </>
  );
}
