// Actions grouped by discipline, life safety first. Each shows who owns it, its status and the proof
// that would close it. Public data never closes an action; only proof the project provides does.
import "./actions.css";

import type { ActionItem } from "../../contracts";
import { Badge, Card, EmptyState, Explain, humanize } from "../../design";

const DISCIPLINES: { key: ActionItem["discipline"]; label: string }[] = [
  { key: "structural", label: "Structural" },
  { key: "architect", label: "Architect" },
  { key: "geotech", label: "Geotechnical" },
  { key: "contractor", label: "Contractor" },
];

const STATUS: Record<ActionItem["status"], { label: string; tone: "neutral" | "accent" }> = {
  open: { label: "Open", tone: "neutral" },
  in_progress: { label: "In progress", tone: "accent" },
  done: { label: "Done", tone: "neutral" },
  not_applicable: { label: "Not applicable", tone: "neutral" },
};

const OWNER: Record<NonNullable<ActionItem["owner_role"]>, string> = {
  architect: "Architect",
  structural_engineer: "Structural engineer",
};

export function ActionsList({ actions }: { actions: ActionItem[] }) {
  if (actions.length === 0) {
    return (
      <EmptyState title="No actions for this site yet">
        Actions appear when a rule matches the site's work types or records. This list is not exhaustive.
      </EmptyState>
    );
  }
  return (
    <div className="fs-actions">
      <p className="fs-quiet">Not exhaustive. Closing every item here does not mean the site is safe.</p>
      {DISCIPLINES.map(({ key, label }) => {
        const items = actions
          .filter((a) => a.discipline === key)
          .sort((a, b) => Number(b.life_safety) - Number(a.life_safety));
        if (items.length === 0) return null;
        return (
          <section key={key} className="fs-actions__group" aria-label={label}>
            <h3 className="fs-label">
              {label} <span className="fs-num">{items.length}</span>
            </h3>
            {items.map((a) => (
              <ActionCard key={a.id} action={a} />
            ))}
          </section>
        );
      })}
    </div>
  );
}

function ActionCard({ action: a }: { action: ActionItem }) {
  const status = STATUS[a.status];
  return (
    <Card
      hazard={a.hazard}
      title={a.title}
      meta={
        <>
          <span>{a.owner_role ? `Owner: ${OWNER[a.owner_role]}` : "No owner yet"}</span>
          {a.code_ref && <span className="fs-num">· {a.code_ref}</span>}
        </>
      }
    >
      <div className="fs-action__badges">
        <Badge tone={status.tone}>
          <span className="fs-action__dot" data-status={a.status} aria-hidden="true" />
          {status.label}
        </Badge>
        {a.life_safety && <Badge tone="safety" title="Life-safety items always sort first">Life safety</Badge>}
      </div>
      {a.proof_needed && (
        <p className="fs-action__proof">
          <span className="fs-quiet">Proof needed:</span> {a.proof_needed}
        </p>
      )}
      <Explain>
        <p>{a.why}</p>
        <p className="fs-quiet">
          From rule <code>{a.source_rule}</code>
          {a.hazard ? ` (${humanize(a.hazard)})` : ""}. A suggestion from public records and the site's work types, not a
          determination.
        </p>
      </Explain>
    </Card>
  );
}
