// Step 2: the shared checklist as a compliance register: a milestone line on top, then numbered rows grouped
// by owner, each with its proof, code section, when it's due, status and owner. The why unfolds on demand.
// "Done" is a person's sign-off (who, when), never proof: 4site does not check it against any record.
import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import type { ActionItem, Project, Role } from "../../contracts";
import { api } from "../../api/client";
import { Button, Chip, EmptyState } from "../../design";
import { projectWrites, ROLE_LABELS, whyNotSaved } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { addProjectItems } from "./draft";
import {
  addedLine, appliesSummary, currentMilestone, trailKind, groupByOwner, itemNumbers, milestoneSummary, MILESTONES, type Phase, phaseOf,
} from "./model";

type Status = ActionItem["status"];
const STATUS_LABELS: Record<Status, string> = { open: "Open", in_progress: "In progress", done: "Done", not_applicable: "N/A" };
const NEXT: Record<Status, Status> = { open: "in_progress", in_progress: "done", done: "open", not_applicable: "open" };
const finished = (s: Status) => s === "done" || s === "not_applicable";

type Props = {
  project: Project;
  workspace: ProjectWorkspace;
  notice: string | null;
  onDismissNotice: () => void;
  /** Items another role's document added to this role's list since it last looked. */
  newForMe: ActionItem[];
  onSeen: () => void;
};

export function ChecklistStep({ project, workspace, notice, onDismissNotice, newForMe, onSeen }: Props) {
  const newIds = useMemo(() => new Set(newForMe.map((i) => i.id)), [newForMe]);
  const [mine, setMine] = useState(false);
  const [lifeSafety, setLifeSafety] = useState(false);
  const [openOnly, setOpenOnly] = useState(false);
  const [phase, setPhase] = useState<Phase | null>(null);
  const changed = useChangedIds(project.items);

  const items = project.items;
  const done = items.filter((i) => finished(i.status)).length;
  const shown = items
    .filter((i) => !mine || i.owner_role === workspace.role)
    .filter((i) => !lifeSafety || i.life_safety)
    .filter((i) => !openOnly || !finished(i.status))
    .filter((i) => !phase || phaseOf(i) === phase);
  const groups = groupByOwner(shown);
  // Numbered from the whole list, so a row keeps its number while filters are on.
  const numbers = useMemo(() => itemNumbers(groupByOwner(items)), [items]);
  const memberRoles = useMemo(() => [...new Set(project.members.map((m) => m.role))], [project.members]);

  return (
    <div className="fs-ps-checklist fs-enter">
      {notice && (
        <div className="fs-ps-notice" role="status">
          <span>{notice}</span>
          <button type="button" className="fs-linkbtn" onClick={onDismissNotice}>Dismiss</button>
        </div>
      )}

      {newForMe.length > 0 && (
        <div className="fs-ps-notice fs-ps-new" role="status">
          <span>
            <strong>{newForMe.length} new for you</strong> since you last looked.{" "}
            {[...new Set(newForMe.map((i) => i.added_reason).filter(Boolean))].slice(0, 2).join(" ")}
          </span>
          <button type="button" className="fs-linkbtn" onClick={onSeen}>Got it</button>
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

      {items.length > 0 && <Timeline items={items} stage={project.stage} selected={phase} onSelect={setPhase} />}

      {items.length === 0 && <NoItems project={project} />}
      {items.length > 0 && shown.length === 0 && <EmptyState title="Nothing matches these filters">Clear a filter to see the rest.</EmptyState>}

      {groups.map((group) => (
        <section key={group.role ?? "none"} className="fs-ps-group">
          <header className="fs-ps-reg__group">
            <h3>{group.role ? ROLE_LABELS[group.role] : "Not assigned"}</h3>
            <span className="fs-num fs-quiet">
              {group.items.filter((i) => finished(i.status)).length} of {group.items.length} complete
            </span>
          </header>
          <div className="fs-ps-reg" role="table" aria-label={`${group.role ? ROLE_LABELS[group.role] : "Not assigned"} items`}>
            <div className="fs-ps-reg__head" role="row">
              <span role="columnheader">No.</span>
              <span role="columnheader">Requirement</span>
              <span role="columnheader">Code</span>
              <span role="columnheader">When</span>
              <span role="columnheader">Status</span>
              <span role="columnheader">Owner</span>
            </div>
            {group.items.map((item) => (
              <ItemRow key={item.id} item={item} number={numbers.get(item.id) ?? ""} roles={memberRoles} workspace={workspace}
                flash={changed.has(item.id)} isNew={newIds.has(item.id)} />
            ))}
          </div>
        </section>
      ))}
      <p className="fs-quiet fs-ps-reg__foot">
        <span className="fs-ps-reg__lskey" aria-hidden="true" /> Life safety · A tick is a person's sign-off that the work
        was done; 4site does not check it against any record.
      </p>
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

function ItemRow({ item, number, roles, workspace, flash, isNew }: {
  item: ActionItem; number: string; roles: Role[]; workspace: ProjectWorkspace; flash: boolean; isNew: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const update = async (change: { status?: Status; owner_role?: Role | null }) => {
    setSaving(true);
    setProblem(null);
    try {
      // A status change carries who made it: marking done records it as the sign-off.
      await workspace.updateItem({ id: item.id, ...change, ...(change.status ? { by_role: workspace.role } : {}) });
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fs-ps-row" role="row" data-status={item.status} data-flash={flash} data-ls={item.life_safety}
      style={{ "--fs-hz": `var(--fs-hz-${item.hazard})` } as CSSProperties}>
      <span className="fs-ps-row__no fs-num" role="cell">{number}</span>
      <div className="fs-ps-row__req" role="cell">
        <button type="button" className="fs-ps-row__title" aria-expanded={open} onClick={() => setOpen(!open)}>
          {item.title}
          {isNew && <span className="fs-ps-newtag">New for you</span>}
        </button>
        {item.status === "done" ? (
          <span className="fs-ps-row__signoff">
            ✓ Marked done{item.done_by_role ? ` by ${ROLE_LABELS[item.done_by_role]}` : ""}
            {item.done_at ? ` · ${signedOn(item.done_at)}` : ""} · not checked against records
          </span>
        ) : (
          item.proof_needed && <span className="fs-ps-row__proof">Proof: {item.proof_needed}</span>
        )}
        <AppliesTo applies={item.applies_to} />
        {item.evidence && <span className="fs-ps-row__record">{item.evidence}</span>}
        <Trail item={item} />
        {open && (
          <div className="fs-ps-item__more">
            <p>{item.why}</p>
            {item.status !== "not_applicable" ? (
              <button type="button" className="fs-linkbtn" onClick={() => update({ status: "not_applicable" })}>Mark not applicable</button>
            ) : (
              <button type="button" className="fs-linkbtn" onClick={() => update({ status: "open" })}>Reopen</button>
            )}
          </div>
        )}
        {problem && <span className="fs-ps-problem" role="alert">{problem}</span>}
      </div>
      <span className="fs-ps-row__code fs-num" role="cell">{item.code_ref ? item.code_ref.replace(/^2022 NYC /, "") : "—"}</span>
      <span className="fs-ps-row__when" role="cell">{item.when ?? MILESTONES.find((m) => m.phase === phaseOf(item))?.sub}</span>
      <span role="cell">
        <button type="button" className="fs-ps-check" data-status={item.status} disabled={saving}
          title="Change status" aria-label={`Status: ${STATUS_LABELS[item.status]}. Change it.`}
          onClick={() => update({ status: NEXT[item.status] })}>
          <span className="fs-ps-check__box" aria-hidden="true">{item.status === "done" ? "✓" : ""}</span>
          {STATUS_LABELS[item.status]}
        </button>
      </span>
      <span role="cell">
        <select className="fs-ps-owner" value={item.owner_role ?? ""} disabled={saving} aria-label="Owner"
          onChange={(e) => update({ owner_role: (e.target.value || null) as Role | null })}>
          <option value="">Unassigned</option>
          {roles.map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
      </span>
    </div>
  );
}

/** A document's trail on the row: a blue "Added" or "Flagged" tag with who and when; the full reason on a click. */
function Trail({ item }: { item: ActionItem }) {
  const [open, setOpen] = useState(false);
  const kind = trailKind(item.added_reason);
  if (!kind) return null;
  const by = addedLine(item, ROLE_LABELS);
  return (
    <span className="fs-ps-trail">
      <span className="fs-ps-trail__line">
        <span className="fs-ps-trail__tag">{kind}</span>
        {by && <span className="fs-quiet fs-num">{by}</span>}
        <button type="button" className="fs-linkbtn" aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "Hide trail" : "View trail"}
        </button>
      </span>
      {open && <span className="fs-ps-trail__reason">{item.added_reason}</span>}
    </span>
  );
}

/** "Applies to 19 Marcus Garvey Blvd (…), 21 … and 6 more": the neighbours this row concerns, all on a click. */
function AppliesTo({ applies }: { applies?: string[] }) {
  const [all, setAll] = useState(false);
  const { shown, more } = appliesSummary(applies);
  if (shown.length === 0) return null;
  const names = all ? applies ?? [] : shown;
  return (
    <span className="fs-ps-row__applies">
      <span className="fs-ps-row__applies-label">Applies to {(applies ?? []).length} building{(applies ?? []).length > 1 ? "s" : ""}:</span>{" "}
      {names.join(" · ")}
      {more > 0 && (
        <button type="button" className="fs-linkbtn" onClick={() => setAll(!all)}>
          {all ? "show fewer" : `and ${more} more`}
        </button>
      )}
    </span>
  );
}

const signedOn = (iso: string) => {
  const at = new Date(iso);
  return Number.isNaN(at.getTime()) ? iso : at.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
};

/** The project's checkpoints on a line: where the job is now, how much is done at each, and where life-safety
    items sit. Clicking a checkpoint shows only its items; clicking it again shows everything. */
function Timeline({ items, stage, selected, onSelect }: {
  items: ActionItem[]; stage: Project["stage"]; selected: Phase | null; onSelect: (p: Phase | null) => void;
}) {
  const summary = milestoneSummary(items);
  const now = currentMilestone(stage);
  const nowIndex = MILESTONES.findIndex((m) => m.phase === now);
  return (
    <div className="fs-ps-tl" role="group" aria-label="Project timeline">
      <div className="fs-ps-tl__line" aria-hidden="true">
        <span style={{ width: `${(nowIndex / (MILESTONES.length - 1)) * 100}%` }} />
      </div>
      <ol className="fs-ps-tl__stops">
        {MILESTONES.map((m, i) => {
          const s = summary[i];
          const complete = s.total > 0 && s.done === s.total;
          return (
            <li key={m.phase}>
              <button type="button" className="fs-ps-tl__stop" aria-pressed={selected === m.phase}
                data-now={m.phase === now} data-complete={complete} data-ls={s.lifeSafety && !complete}
                onClick={() => onSelect(selected === m.phase ? null : m.phase)}>
                {m.phase === now && <span className="fs-ps-tl__here">You are here</span>}
                <span className="fs-ps-tl__dot" aria-hidden="true">{complete ? "✓" : ""}</span>
                <span className="fs-ps-tl__label">{m.label}</span>
                <span className="fs-ps-tl__sub">{m.sub}</span>
                <span className="fs-ps-tl__count fs-num">
                  {s.total === 0 ? "Nothing due" : `${s.done} of ${s.total} done`}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

/** Ids added, or whose status, owner or provenance changed, since the last copy of the project, for a short highlight. */
function useChangedIds(items: ActionItem[]): Set<string> {
  const previous = useRef<Map<string, string> | null>(null);
  const [changed, setChanged] = useState<Set<string>>(new Set());
  useEffect(() => {
    const now = new Map(items.map((i) => [i.id, `${i.status}|${i.owner_role ?? ""}|${i.added_at ?? ""}`]));
    const before = previous.current;
    previous.current = now;
    if (!before) return;
    // Changed rows, and rows another tab's document just added.
    const ids = new Set([...now].filter(([id, key]) => before.get(id) !== key).map(([id]) => id));
    if (ids.size === 0) return;
    setChanged(ids);
    const timer = window.setTimeout(() => setChanged(new Set()), 2000);
    return () => window.clearTimeout(timer);
  }, [items]);
  return changed;
}
