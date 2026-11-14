import type { ApplyStatus, ChecklistRow } from "../brief/brief_types";

const APPLY_LABELS: Record<ApplyStatus, { text: string; className: string }> = {
  applies: { text: "Applies (on the record)", className: "bg-site text-white" },
  needs_input: { text: "Needs project input", className: "border border-neighbor text-neighbor" },
  set_by_dob: { text: "Starts when DOB orders it", className: "border border-gap text-gap" },
  unknown: { text: "Unknown: a query failed", className: "border border-dashed border-site text-site" },
  does_not_apply: { text: "Does not apply", className: "border border-gap text-gap" },
};

export function ApplyBadge({ status }: { status: ApplyStatus }) {
  const { text, className } = APPLY_LABELS[status];
  return <span className={`rounded px-2 py-0.5 text-xs ${className}`}>{text}</span>;
}

// Public data never proves a row. A lead (a document a public source reports, unread) is dashed
// and links to where it was reported; it never closes a gap.
export function ProofBadge({ proof }: { proof: ChecklistRow["proof"] }) {
  if (proof.status === "provided_unverified") {
    return <span className="rounded border border-dashed border-lead px-2 py-0.5 text-xs text-lead">Provided, not verified</span>;
  }
  const lead = proof.status === "reported_not_read" ? (proof.leads ?? [])[0] : undefined;
  if (lead) {
    return (
      <a href={lead.url ?? undefined} target="_blank" rel="noreferrer"
        className="rounded border border-dashed border-lead px-2 py-0.5 text-xs text-lead underline">
        Reported, not read
      </a>
    );
  }
  return <span className="rounded border border-gap px-2 py-0.5 text-xs text-gap">Proof not provided</span>;
}

export function SectionLink({ section, url }: { section: string; url: string }) {
  return (
    <a href={url} target="_blank" rel="noreferrer" className="font-mono text-xs underline">
      BC §{section}
    </a>
  );
}
