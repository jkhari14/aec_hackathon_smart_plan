import { writtenBefore } from "../../brief/brief_as_of";
import type { ComplaintCodeKeys, PublicRecord } from "../../brief/brief_types";

type Props = { record: PublicRecord; asOf: string | null; codeKeys: ComplaintCodeKeys };

function Source({ href, children }: { href?: string | null; children: string }) {
  return href ? <a className="underline" href={href} target="_blank" rel="noreferrer">{children}</a> : <>{children}</>;
}

// The category's meaning was typed in by hand from a list DOB printed, so it never reads like a pulled record.
function CategoryLine({ record, codeKeys }: Omit<Props, "asOf">) {
  const c = record.complaint_category;
  if (!c || c.status === "not_recorded") return null;
  const list = <Source href={codeKeys.dob_complaint_categories?.source_url}>DOB's printed category list</Source>;
  if (c.status === "not_in_key") {
    return <p className="mt-1 text-xs text-stone-600">Category {c.code} is not in {list}, which may be older than the code.</p>;
  }
  if (c.status === "key_unavailable") {
    return <p className="mt-1 text-xs text-stone-600">Category {c.code}: the category list didn't load, so its meaning is unknown.</p>;
  }
  const checked = c.status === "imported_checked" ? "checked by a second person" : "not yet checked by a second person";
  return (
    <p className="mt-1 border-l-2 border-dashed border-amber-500 pl-2 text-xs">
      Category {c.code}: {c.description}{" "}
      <span className="text-stone-500">(from {list}, typed in by hand, {checked})</span>
    </p>
  );
}

// The disposition is written when DOB closes the complaint, so a replay shows it only once it existed.
function DispositionLine({ record, asOf, codeKeys }: Props) {
  const d = record.complaint_disposition;
  if (!d) return null;
  if (d.status === "not_recorded") return <p className="mt-1 text-xs text-stone-500">No disposition recorded.</p>;
  if (!writtenBefore(d.date, asOf)) {
    return (
      <p className="mt-1 text-xs text-stone-500">
        DOB's disposition {d.date ? "was recorded after this day" : "is undated"}, so the replay hides it.
      </p>
    );
  }
  const key = codeKeys.dob_complaint_dispositions;
  const table = <Source href={key?.source_url}>DOB's disposition code table</Source>;
  const head = `DOB's disposition ${d.code}, ${d.date ?? "undated"}`;
  if (d.status === "not_in_table") {
    return (
      <p className="mt-1 text-xs text-stone-600">
        {head}: not in {table}{key?.rows_updated_at ? ` (last updated ${key.rows_updated_at})` : ""}, so its meaning isn't shown.
      </p>
    );
  }
  if (d.status === "key_unavailable") {
    return <p className="mt-1 text-xs text-stone-600">{head}: the code table didn't load, so its meaning is unknown.</p>;
  }
  return <p className="mt-1 text-xs">{head}: {d.description} <span className="text-stone-500">(from {table})</span></p>;
}

export function ComplaintCodeLines(props: Props) {
  return <><CategoryLine record={props.record} codeKeys={props.codeKeys} /><DispositionLine {...props} /></>;
}
