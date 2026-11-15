// The project's action items: who owns each one and where it stands. Status and owner are set by the
// people on the project; nothing here is checked against a record.
import { useState } from "react";

import type { ActionItem } from "../../contracts";
import { ROLE_LABELS, type ActionItemUpdate, type Role } from "./project_client";

type Props = {
  items: ActionItem[];
  role: Role;
  onUpdate: (update: ActionItemUpdate) => Promise<void>;
};

const STATUS_LABELS: Record<ActionItem["status"], string> = {
  open: "Open",
  in_progress: "In progress",
  done: "Done",
  not_applicable: "Not applicable",
};
const SELECT = "rounded border border-line bg-night px-1.5 py-1 text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 disabled:opacity-50";
const CLOSED: ActionItem["status"][] = ["done", "not_applicable"];

/** Life safety first, then what is still open. */
function inOrder(items: ActionItem[]): ActionItem[] {
  const rank = (item: ActionItem) => (item.life_safety ? 0 : 2) + (CLOSED.includes(item.status) ? 1 : 0);
  return [...items].sort((a, b) => rank(a) - rank(b));
}

export function ProjectItems({ items, role, onUpdate }: Props) {
  const [mineOnly, setMineOnly] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [problem, setProblem] = useState<{ id: string; reason: string } | null>(null);
  const shown = inOrder(mineOnly ? items.filter((item) => item.owner_role === role) : items);

  async function update(change: ActionItemUpdate) {
    setSaving(change.id);
    setProblem(null);
    try {
      await onUpdate(change);
    } catch (error) {
      setProblem({ id: change.id, reason: error instanceof Error ? error.message : "not saved" });
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-1.5 text-xs text-muted">
        <input type="checkbox" checked={mineOnly} onChange={(event) => setMineOnly(event.target.checked)} />
        Only items assigned to the {ROLE_LABELS[role].toLowerCase()}
      </label>
      {shown.length === 0 && (
        <p className="text-sm text-muted">{items.length ? "No items are assigned to this role." : "No action items are on this project yet."}</p>
      )}
      <ul className="space-y-2">
        {shown.map((item) => (
          <li key={item.id} className="rounded border border-line p-2">
            <div className="flex flex-wrap items-center gap-1.5">
              {item.life_safety && <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[0.7rem] font-semibold text-red-300">Life safety</span>}
              <span className="rounded bg-white/10 px-1.5 py-0.5 text-[0.7rem] text-muted">{item.discipline}</span>
              {item.code_ref && <span className="text-[0.7rem] text-muted">{item.code_ref}</span>}
            </div>
            <p className="mt-1 text-sm font-medium">{item.title}</p>
            <p className="mt-0.5 text-xs text-muted">{item.why}</p>
            {item.proof_needed && <p className="mt-0.5 text-xs text-muted">Proof needed: {item.proof_needed}</p>}
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <label className="flex items-center gap-1 text-xs text-muted">
                Status
                <select
                  className={SELECT}
                  value={item.status}
                  disabled={saving === item.id}
                  onChange={(event) => void update({ id: item.id, status: event.target.value as ActionItem["status"] })}
                >
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-1 text-xs text-muted">
                Owner
                <select
                  className={SELECT}
                  value={item.owner_role ?? ""}
                  disabled={saving === item.id}
                  onChange={(event) => void update({ id: item.id, owner_role: (event.target.value || null) as Role | null })}
                >
                  <option value="">Unassigned</option>
                  {Object.entries(ROLE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              {saving === item.id && <span className="text-xs text-muted">Saving…</span>}
            </div>
            {problem?.id === item.id && <p className="mt-1 text-xs text-red-300">Not saved: {problem.reason}</p>}
          </li>
        ))}
      </ul>
      <p className="text-[0.7rem] leading-snug text-muted">
        Status and owner are set by the people on this project. ForeSite does not check proof, and "done" here is not a finding
        that a duty was met.
      </p>
    </div>
  );
}
