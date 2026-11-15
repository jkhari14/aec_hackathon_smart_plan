// Actions grouped by discipline, life safety first. Each shows who owns it, its status and the proof
// that would close it. Public data never closes an action; only proof the project provides does.
// Words come from the shared copy file (copy.actions, copy.disciplines, copy.itemStatus, copy.roles).
import "./actions.css";

import type { ActionItem } from "../../contracts";
import { copy } from "../../copy";
import { Badge, Card, EmptyState, Explain, HAZARD_LABELS } from "../../design";

const A = copy.actions;
const ORDER: ActionItem["discipline"][] = ["structural", "architect", "geotech", "contractor"];
const TONE: Record<ActionItem["status"], "neutral" | "accent"> = {
  open: "neutral",
  in_progress: "accent",
  done: "neutral",
  not_applicable: "neutral",
};

export function ActionsList({ actions }: { actions: ActionItem[] }) {
  if (actions.length === 0) {
    return <EmptyState title={A.empty}>{A.help}</EmptyState>;
  }
  return (
    <div className="fs-actions">
      <p className="fs-quiet">{A.help}</p>
      {ORDER.map((key) => {
        const items = actions
          .filter((a) => a.discipline === key)
          .sort((a, b) => Number(b.life_safety) - Number(a.life_safety));
        if (items.length === 0) return null;
        const label = copy.disciplines[key];
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
      <p className="fs-quiet">{A.proofNote}</p>
    </div>
  );
}

function ActionCard({ action: a }: { action: ActionItem }) {
  return (
    <Card
      hazard={a.hazard}
      title={a.title}
      meta={
        <>
          <span>
            {A.owner}: {a.owner_role ? copy.roles[a.owner_role] : "not assigned yet"}
          </span>
          {a.code_ref && (
            <span className="fs-num">
              · {A.codeRef} {a.code_ref}
            </span>
          )}
        </>
      }
    >
      <div className="fs-action__badges">
        <Badge tone={TONE[a.status]}>
          <span className="fs-action__dot" data-status={a.status} aria-hidden="true" />
          {copy.itemStatus[a.status]}
        </Badge>
        {a.life_safety && <Badge tone="safety" title="Life-safety items always sort first">{A.lifeSafety}</Badge>}
      </div>
      {a.proof_needed && (
        <p className="fs-action__proof">
          <span className="fs-quiet">{A.proofNeeded}:</span> {a.proof_needed}
        </p>
      )}
      <Explain>
        <p>{a.why}</p>
        <p className="fs-quiet">
          From rule <code>{a.source_rule}</code> ({HAZARD_LABELS[a.hazard]}). A suggestion from public records and the site's
          work types, not a determination.
        </p>
      </Explain>
    </Card>
  );
}
