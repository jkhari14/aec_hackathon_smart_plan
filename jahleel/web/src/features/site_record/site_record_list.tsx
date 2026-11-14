import type { PublicRecord } from "../../brief/brief_types";

// Status is today's; the date is when the record was issued or filed.
export function SiteRecordList({ records, limit = 40 }: { records: PublicRecord[]; limit?: number }) {
  if (records.length === 0) return <p className="text-sm text-gap">No records dated before this day.</p>;
  return (
    <ul className="divide-y rounded border bg-white text-sm">
      {records.slice(0, limit).map((r) => (
        <li key={r.id} className={`p-2 ${r.mentions_stop_work ? "bg-red-50" : ""}`}>
          <p className="text-xs text-stone-500">
            {r.date ?? "undated"} · {r.dataset_name} {r.record_id} · status today: {r.status_today ?? "?"}
            {r.query_url && <> · <a className="underline" href={r.query_url} target="_blank" rel="noreferrer">source</a></>}
          </p>
          <p>{r.summary}</p>
        </li>
      ))}
    </ul>
  );
}
