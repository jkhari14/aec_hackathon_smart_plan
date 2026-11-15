// Step 2: the shared checklist, grouped by who owns each item. One line per item (status, title, owner);
// the why, code reference and proof needed unfold on demand. "Done" is a person's mark, never proof.
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import type { ActionItem, Project, Role } from "../../contracts";
import { api } from "../../api/client";
import { Button, Chip, EmptyState, HAZARD_LABELS } from "../../design";
import { projectWrites, ROLE_LABELS, whyNotSaved } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { addProjectItems } from "./draft";
import { groupByOwner } from "./model";

type Status = ActionItem["status"];
const STATUS_LABELS: Record<Status, string> = { open: "Open", in_progress: "In progress", done: "Done", not_applicable: "N/A" };
const NEXT: Record<Status, Status> = { open: "in_progress", in_progress: "done", done: "open", not_applicable: "open" };
const finished = (s: Status) => s === "done" || s === "not_applicable";

type Props = { project: Project; workspace: ProjectWorkspace; notice: string | null; onDismissNotice: () => void };

export function ChecklistStep({ project, workspace, notice, onDismissNotice }: Props) {
  const [mine, setMine] = useState(false);
  const [lifeSafety, setLifeSafety] = useState(false);
  const [openOnly, setOpenOnly] = useState(false);
  const changed = useChangedIds(project.items);

  const items = project.items;
  const done = items.filter((i) => finished(i.status)).length;
  const shown = items
    .filter((i) => !mine || i.owner_role === workspace.role)
    .filter((i) => !lifeSafety || i.life_safety)
    .filter((i) => !openOnly || !finished(i.status));
  const groups = groupByOwner(shown);
  const memberRoles = useMemo(() => [...new Set(project.members.map((m) => m.role))], [project.members]);

  return (
    <div className="fs-ps-checklist fs-enter">
      {notice && (
        <div className="fs-ps-notice" role="status">
          <span>{notice}</span>
          <button type="button" className="fs-linkbtn" onClick={onDismissNotice}>Dismiss</button>
        </div>
      )}

      <div className="fs-ps-progress">
        <div>
          <strong className="fs-num">{done} / {items.length}</strong> <span className="fs-quiet">done</span>
        </div>
        <div className="fs-ps-progress__bar" aria-hidden="true">
          <span style={{ width: items.length ? `${(done / items.length) * 100}%` : 0 }} />
        </div>
        <div className="fs-ps-chips" role="group" aria-label="Filter the checklist">
          <Chip pressed={mine} onClick={() => setMine(!mine)}>Mine</Chip>
          <Chip pressed={lifeSafety} onClick={() => setLifeSafety(!lifeSafety)}>Life safety</Chip>
          <Chip pressed={openOnly} onClick={() => setOpenOnly(!openOnly)}>Open</Chip>
        </div>
      </div>

      {items.length === 0 && <NoItems project={project} />}
      {items.length > 0 && shown.length === 0 && <EmptyState title="Nothing matches these filters">Clear a filter to see the rest.</EmptyState>}

      {groups.map((group) => (
        <section key={group.role ?? "none"} className="fs-ps-group">
          <h3 className="fs-label">
            {group.role ? ROLE_LABELS[group.role] : "Not assigned"}{" "}
            <span className="fs-num fs-quiet">
              {group.items.filter((i) => finished(i.status)).length}/{group.items.length}
            </span>
          </h3>
          <ul className="fs-ps-items">
            {group.items.map((item) => (
              <ItemRow key={item.id} item={item} roles={memberRoles} workspace={workspace} flash={changed.has(item.id)} />
            ))}
          </ul>
        </section>
      ))}
      <p className="fs-quiet">A tick is a person's mark that the work was done; 4site does not check it against any record.</p>
    </div>
  );
}

/** An empty project: either the items were never saved (retry) or the rules found nothing for this job. */
function NoItems({ project }: { project: Project }) {
  const [state, setState] = useState<"idle" | "busy" | "none">("idle");
  const [problem, setProblem] = useState<string | null>(null);
  const retry = async () => {
    setState("busy");
    setProblem(null);
    try {
      let added = 0;
      await addProjectItems(
        {
          actions: api.actions,
          addItems: async (id, items) => {
            added = items.length;
            if (items.length === 0) return;
            const why = whyNotSaved(await projectWrites.addItems(id, items));
            if (why) throw new Error(why);
          },
        },
        project,
      );
      // New items arrive with the next poll; with none, the rules found nothing for this job.
      setState(added === 0 ? "none" : "idle");
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
      setState("idle");
    }
  };
  if (state === "none") {
    return <EmptyState title="No items for this work type">The rules found nothing to check for this job on this site.</EmptyState>;
  }
  return (
    <EmptyState
      title="No checklist items on this project yet"
      action={
        <Button variant="primary" disabled={state === "busy"} onClick={() => void retry()}>
          {state === "busy" ? "Adding…" : "Add this job's checklist items"}
        </Button>
      }
    >
      {problem ?? "They were not saved when the project was made. Try adding them again."}
    </EmptyState>
  );
}

function ItemRow({ item, roles, workspace, flash }: { item: ActionItem; roles: Role[]; workspace: ProjectWorkspace; flash: boolean }) {
  const [open, setOpen] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const update = async (change: { status?: Status; owner_role?: Role | null }) => {
    setSaving(true);
    setProblem(null);
    try {
      await workspace.updateItem({ id: item.id, ...change });
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <li className="fs-ps-item" data-status={item.status} data-flash={flash}
      style={{ "--fs-hz": `var(--fs-hz-${item.hazard})` } as CSSProperties}>
      <div className="fs-ps-item__line">
        <button type="button" className="fs-ps-status" data-status={item.status} disabled={saving}
          title="Change status" aria-label={`Status: ${STATUS_LABELS[item.status]}. Change it.`}
          onClick={() => update({ status: NEXT[item.status] })}>
          {STATUS_LABELS[item.status]}
        </button>
        <button type="button" className="fs-ps-item__title" aria-expanded={open} onClick={() => setOpen(!open)}>
          <span className="fs-chip__dot" aria-hidden="true" title={HAZARD_LABELS[item.hazard]} />
          {item.title}
          {item.life_safety && <span className="fs-ps-ls" title="Life safety">Life safety</span>}
        </button>
        <select className="fs-ps-owner" value={item.owner_role ?? ""} disabled={saving} aria-label="Owner"
          onChange={(e) => update({ owner_role: (e.target.value || null) as Role | null })}>
          <option value="">Unassigned</option>
          {roles.map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
      </div>
      {open && (
        <div className="fs-ps-item__more">
          <p>{item.why}</p>
          {item.code_ref && <p className="fs-quiet fs-num">Code: {item.code_ref}</p>}
          {item.proof_needed && <p className="fs-quiet">Proof needed: {item.proof_needed}</p>}
          {item.status !== "not_applicable" ? (
            <button type="button" className="fs-linkbtn" onClick={() => update({ status: "not_applicable" })}>Mark not applicable</button>
          ) : (
            <button type="button" className="fs-linkbtn" onClick={() => update({ status: "open" })}>Reopen</button>
          )}
        </div>
      )}
      {problem && <p className="fs-ps-problem" role="alert">{problem}</p>}
    </li>
  );
}

/** Ids whose status or owner changed since the last copy of the project, for a short highlight. */
function useChangedIds(items: ActionItem[]): Set<string> {
  const previous = useRef<Map<string, string> | null>(null);
  const [changed, setChanged] = useState<Set<string>>(new Set());
  useEffect(() => {
    const now = new Map(items.map((i) => [i.id, `${i.status}|${i.owner_role ?? ""}`]));
    const before = previous.current;
    previous.current = now;
    if (!before) return;
    const ids = new Set([...now].filter(([id, key]) => before.has(id) && before.get(id) !== key).map(([id]) => id));
    if (ids.size === 0) return;
    setChanged(ids);
    const timer = window.setTimeout(() => setChanged(new Set()), 2000);
    return () => window.clearTimeout(timer);
  }, [items]);
  return changed;
}
