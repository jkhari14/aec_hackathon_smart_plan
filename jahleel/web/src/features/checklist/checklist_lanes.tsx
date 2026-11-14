import type { ChecklistRow, Party } from "../../brief/brief_types";
import { ApplyBadge, ProofBadge, SectionLink } from "../../ui/evidence_badge";

const PARTY_LABELS: Record<Party, string> = {
  owner_developer: "Owner / developer",
  design_professional: "Design professional",
  excavation_support_engineer: "Excavation-support engineer",
  geotechnical_engineer: "Geotechnical engineer",
  contractor: "Contractor",
  special_inspector: "Special inspector",
  adjoining_owner: "Adjoining owner",
  dob: "DOB",
};

type Props = { rows: ChecklistRow[]; adjoiningOwnerView: boolean };

function basisText(row: ChecklistRow): string | null {
  const details = (row.applies.basis ?? []).map((b) => (typeof b.detail === "string" ? b.detail : null)).filter(Boolean);
  return details.length ? details.join(" ") : null;
}

// One lane per party (a row with two parties shows in both): a building fails when several
// parties miss at once, so each lane is one "cable".
export function ChecklistLanes({ rows, adjoiningOwnerView }: Props) {
  if (rows.length === 0) return <p className="p-4 text-sm text-gap">No checklist rows.</p>;
  const parties = (Object.keys(PARTY_LABELS) as Party[]).filter((p) => rows.some((r) => r.parties.includes(p)));
  return (
    <div className="space-y-4">
      {parties.map((party) => (
        <section key={party}>
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-stone-500">{PARTY_LABELS[party]}</h3>
          <ul className="space-y-2">
            {rows.filter((r) => r.parties.includes(party)).map((row) => {
              const related = (row.related_records.filings.records ?? []).length + (row.related_records.citations ?? []).length;
              const needs = row.applies.needs ?? [];
              const why = basisText(row);
              return (
                <li key={`${party}-${row.id}`} className={`rounded border bg-white p-2 ${row.open_gap ? "border-l-4 border-l-site" : ""}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-semibold">
                      {row.title} <SectionLink section={row.section} url={row.source_url} />
                    </span>
                    <span className="flex flex-wrap gap-1">
                      {row.life_safety && <span className="rounded border border-site px-1 text-xs text-site">Life safety</span>}
                      <ApplyBadge status={row.applies.status} /><ProofBadge proof={row.proof} />
                    </span>
                  </div>
                  <p className="mt-1 text-sm">
                    {adjoiningOwnerView ? <>Ask for: <strong>{row.proof_needed}</strong>. </> : null}
                    {row.requirement}
                  </p>
                  {why && <p className="mt-1 text-xs italic text-gap">Why: {why}</p>}
                  {needs.length > 0 && (
                    <p className="mt-1 text-xs text-neighbor">Decided by: {needs.join(", ").replaceAll("_", " ")}</p>
                  )}
                  {row.scope === "each_adjacent_building" && (
                    <p className="mt-1 text-xs text-stone-500">Judged for each of {(row.per_building ?? []).length} adjacent buildings.</p>
                  )}
                  {related > 0 && <p className="mt-1 text-xs text-stone-500">{related} related records beside this row (not proof).</p>}
                  {row.proof.status === "reported_not_read" && <p className="mt-1 text-xs text-lead">{row.proof.note}</p>}
                  {row.open_gap && <p className="mt-1 text-xs font-semibold text-site">Open gap: applies, no proof provided.</p>}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
