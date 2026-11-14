import type { ReactNode } from "react";

import type { AnswerPart, BriefSource, QueriedDataset, ReportedSource, WebSource } from "./chat_types";

// One look per kind, so a record, a lead, "not found" and "unknown" can't be mistaken for each other:
// solid green for the public record, dashed amber for a lead, grey for not found, dashed red for unknown.
const KIND = {
  record: { label: "From the public record", box: "border-l-4 border-l-record", tag: "text-record" },
  lead: { label: "A lead · not checked by us", box: "border-dashed border-lead", tag: "text-lead" },
  not_found: { label: "Not found", box: "border-gap", tag: "text-gap" },
  unknown: { label: "Unknown: a query failed", box: "border-dashed border-site", tag: "text-site" },
} as const;

const SOURCE_TAG: Record<BriefSource["type"], string> = {
  public_record: "Record",
  requirement: "Code duty (a paraphrase: read the linked text)",
  lot_facts: "Lot facts from PLUTO (can lag)",
  dataset_count: "Count from the dataset",
};

function Link({ href, children }: { href: string; children: ReactNode }) {
  return <a className="underline" href={href} target="_blank" rel="noreferrer">{children}</a>;
}

function BriefSourceItem({ source }: { source: BriefSource }) {
  return (
    <li>
      <details>
        <summary className="cursor-pointer">
          <span className="font-semibold">{SOURCE_TAG[source.type]}:</span> {source.label}
          {source.date ? ` · ${source.date}` : ""}
        </summary>
        {source.detail && <p className="mt-1 pl-3 text-stone-600">{source.detail}</p>}
        {source.url && (
          <p className="pl-3">
            <Link href={source.url}>{source.type === "requirement" ? "the city's code text" : "the query that returned it"}</Link>
          </p>
        )}
      </details>
    </li>
  );
}

function LeadSourceItem({ source }: { source: WebSource | ReportedSource }) {
  if (source.type === "web_result") {
    return (
      <li>
        <span className="font-semibold">From the web:</span> <Link href={source.url}>{source.title || source.url}</Link>{" "}
        <span className="text-stone-500">
          ({new URL(source.url).hostname}{source.official ? ", a government site" : ""}{source.page_age ? `, ${source.page_age}` : ""})
        </span>
      </li>
    );
  }
  return (
    <li>
      <span className="font-semibold">Reported, not read:</span> {source.document}{" "}
      <span className="text-stone-500">
        (reported by {source.reported_by}{source.reported_on ? ` on ${source.reported_on}` : ""})
      </span>{" "}
      {source.url && <Link href={source.url}>the report</Link>}
    </li>
  );
}

function Queried({ queried }: { queried: QueriedDataset[] }) {
  return (
    <p className="mt-1 text-xs text-stone-500">
      Queried:{" "}
      {queried.map((q, i) => (
        <span key={`${q.key}-${q.bbl ?? ""}`}>
          {i > 0 ? ", " : ""}
          {q.url ? <Link href={q.url}>{q.name}</Link> : q.name}
        </span>
      ))}
    </p>
  );
}

export function ChatAnswerParts({ parts }: { parts: AnswerPart[] }) {
  return (
    <div className="space-y-2">
      {parts.map((part, index) => {
        if (part.kind === "notice") {
          return <p key={index} className="text-xs italic text-stone-600">{part.text}</p>;
        }
        const look = KIND[part.kind];
        return (
          <div key={index} className={`rounded border bg-white p-2 ${look.box}`}>
            <p className={`text-xs font-semibold uppercase tracking-wide ${look.tag}`}>{look.label}</p>
            <p className="text-sm">{part.text}</p>
            {part.kind === "record" && (
              <ul className="mt-1 space-y-1 text-xs">{part.sources.map((s) => <BriefSourceItem key={s.ref} source={s} />)}</ul>
            )}
            {part.kind === "lead" && (
              <ul className="mt-1 space-y-1 text-xs">
                {part.sources.map((s) => <LeadSourceItem key={s.type === "web_result" ? s.url : s.ref} source={s} />)}
              </ul>
            )}
            {(part.kind === "not_found" || part.kind === "unknown") && <Queried queried={part.queried} />}
          </div>
        );
      })}
    </div>
  );
}
