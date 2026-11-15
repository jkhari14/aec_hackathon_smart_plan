// The shared project workspace for the architect and the structural engineer: who is on it, the
// action items and who owns them, notes, and pins (including pinned chat answers).
// See README.md for how the shell mounts it with useProject.
import { useState, type FormEvent } from "react";

import "../chat/chat_theme.css";

import type { ProjectCreate } from "../../contracts";
import { ProjectItems } from "./ProjectItems";
import { ROLE_LABELS, type ProjectPin, type Role } from "./project_client";
import type { ProjectWorkspace } from "./useProject";

export type ProjectPanelProps = {
  workspace: ProjectWorkspace;
  /** The site on the page: with no project open, one can be started for it. */
  siteBbl?: string | null;
  siteLabel?: string;
  onProjectCreated?: (projectId: string) => void;
  /** Called when a pin of a record, case, warning or action item is opened, so the page can show it. */
  onOpenPin?: (pin: ProjectPin) => void;
  defaultOpen?: boolean;
  className?: string;
  /** Only the workspace itself, for a frame the shell already draws. */
  embedded?: boolean;
};

const DOCKED = "absolute bottom-4 left-4 z-10 w-[24rem] max-w-[calc(100vw-2rem)]";
const BUTTON = "rounded border border-line px-2 py-1 text-xs hover:bg-line/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--fs-focus)] disabled:cursor-not-allowed disabled:opacity-50";
const INPUT = "w-full rounded border border-line bg-night px-2 py-1.5 text-sm placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--fs-focus)]";
const HEADING = "text-xs font-semibold uppercase tracking-wide text-muted";
const PIN_KINDS: Record<ProjectPin["kind"], string> = {
  record: "Public record",
  case: "Past case",
  warning: "Early warning",
  action: "Action item",
  chat_answer: "Chat answer",
};
const STAGES: Record<ProjectCreate["stage"], string> = {
  pre_acquisition: "Before acquisition",
  design: "Design",
  pre_filing: "Before filing",
  construction: "Construction",
};

const when = (iso: string) => {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? iso : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
};
const message = (error: unknown) => (error instanceof Error ? error.message : "not saved");

function StartProject({ workspace, siteBbl, siteLabel, onProjectCreated }: ProjectPanelProps) {
  const [name, setName] = useState(siteLabel ? `Project: ${siteLabel}` : "");
  const [stage, setStage] = useState<ProjectCreate["stage"]>("pre_filing");
  const [members, setMembers] = useState<Record<Role, string>>({ architect: "", structural_engineer: "" });
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  if (!siteBbl) return <p className="text-sm text-muted">Pick a site on the map to start a project for it.</p>;
  const missing = !name.trim() ? "Give the project a name." : !Object.values(members).some((member) => member.trim()) ? "Add at least one member." : null;

  async function start(event: FormEvent) {
    event.preventDefault();
    if (missing || !siteBbl) return;
    setBusy(true);
    setProblem(null);
    try {
      const list = (Object.keys(members) as Role[]).filter((role) => members[role].trim()).map((role) => ({ name: members[role].trim(), role }));
      onProjectCreated?.(await workspace.create({ name: name.trim(), site_bbl: siteBbl, stage, members: list }));
    } catch (error) {
      setProblem(message(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={start} className="space-y-2">
      <p className="text-sm text-muted">Start a shared project for this site. The architect and the structural engineer each open it and act in their role.</p>
      <label className="block text-xs text-muted">Project name<input className={INPUT} value={name} maxLength={120} onChange={(event) => setName(event.target.value)} /></label>
      <label className="block text-xs text-muted">Stage
        <select className={INPUT} value={stage} onChange={(event) => setStage(event.target.value as ProjectCreate["stage"])}>
          {Object.entries(STAGES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      {(Object.keys(ROLE_LABELS) as Role[]).map((role) => (
        <label key={role} className="block text-xs text-muted">{ROLE_LABELS[role]} (name)
          <input className={INPUT} value={members[role]} maxLength={80} onChange={(event) => setMembers({ ...members, [role]: event.target.value })} />
        </label>
      ))}
      <button type="submit" className={BUTTON} disabled={busy || missing !== null}>{busy ? "Starting…" : "Start the project"}</button>
      {missing && <p className="text-xs text-sample">{missing}</p>}
      {problem && <p className="text-xs text-[color:var(--fs-error)]">Not started: {problem}</p>}
    </form>
  );
}

function Notes({ workspace }: { workspace: ProjectWorkspace }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  if (workspace.state.status !== "ok") return null;
  const notes = [...workspace.state.project.notes].reverse();

  async function add(event: FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    setBusy(true);
    setProblem(null);
    try {
      await workspace.addNote(text.trim());
      setText("");
    } catch (error) {
      setProblem(message(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <form onSubmit={add} className="space-y-1.5">
        <label className="block text-xs text-muted">Add a note as the {ROLE_LABELS[workspace.role].toLowerCase()}
          <textarea className={`${INPUT} resize-none`} rows={2} maxLength={4000} value={text} onChange={(event) => setText(event.target.value)} />
        </label>
        <button type="submit" className={BUTTON} disabled={busy || !text.trim()}>{busy ? "Saving…" : "Add note"}</button>
        {problem && <p className="text-xs text-[color:var(--fs-error)]">Not saved: {problem}</p>}
      </form>
      {notes.length === 0 && <p className="text-sm text-muted">No notes yet.</p>}
      <ul className="space-y-1.5">
        {notes.map((note) => (
          <li key={note.id} className="rounded border border-line p-2">
            <p className="whitespace-pre-wrap text-sm">{note.text}</p>
            <p className="mt-1 text-[0.7rem] text-muted">{ROLE_LABELS[note.author_role]} · {when(note.created_at)}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Pins({ pins, onOpenPin }: { pins: ProjectPin[]; onOpenPin?: (pin: ProjectPin) => void }) {
  if (pins.length === 0) return <p className="text-sm text-muted">Nothing is pinned yet. Pin an answer from the chat to keep it here.</p>;
  return (
    <ul className="space-y-1.5">
      {[...pins].reverse().map((pin) => (
        <li key={pin.id} className="rounded border border-line p-2">
          <p className="text-[0.7rem] font-semibold uppercase tracking-wide text-muted">{PIN_KINDS[pin.kind] ?? pin.kind}</p>
          <p className="mt-0.5 text-sm font-medium">{pin.title}</p>
          {pin.body && (
            <details className="mt-1">
              <summary className="cursor-pointer text-xs text-muted">The answer as it was shown</summary>
              <p className="mt-1 whitespace-pre-wrap text-xs leading-snug">{pin.body}</p>
            </details>
          )}
          {pin.kind === "chat_answer" && !pin.body && <p className="mt-0.5 text-xs text-muted">The answer's text was not kept with this pin.</p>}
          <div className="mt-1 flex flex-wrap items-center gap-2 text-[0.7rem] text-muted">
            <span>Pinned by the {ROLE_LABELS[pin.by_role].toLowerCase()} · {when(pin.created_at)}</span>
            {onOpenPin && pin.kind !== "chat_answer" && <button type="button" className={BUTTON} onClick={() => onOpenPin(pin)}>Open</button>}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function ProjectPanel(props: ProjectPanelProps) {
  const { workspace } = props;
  const { state, role } = workspace;
  const [open, setOpen] = useState(props.defaultOpen ?? true);
  const [adding, setAdding] = useState<{ busy: boolean; problem: string | null }>({ busy: false, problem: null });
  const project = state.status === "ok" ? state.project : null;
  const embedded = props.embedded ?? false;

  async function addSiteItems() {
    setAdding({ busy: true, problem: null });
    try {
      await workspace.addSiteActionItems();
      setAdding({ busy: false, problem: null });
    } catch (error) {
      setAdding({ busy: false, problem: message(error) });
    }
  }

  const body = (
        <div className={embedded ? "space-y-4" : "max-h-[60vh] space-y-4 overflow-y-auto border-t border-line px-3 py-3"}>
          {state.status === "none" && <StartProject {...props} />}
          {state.status === "loading" && <p className="text-sm text-muted">Loading the project…</p>}
          {state.status === "not_found" && <p className="text-sm">No project was found at this link.</p>}
          {state.status === "unreachable" && <p className="text-sm">The project could not be loaded: the server could not be reached. Nothing is shown rather than a stale or sample copy.</p>}
          {project && (
            <>
              <div className="space-y-1.5">
                <h3 className={HEADING}>Members</h3>
                <ul className="text-sm">
                  {project.members.map((member, index) => (
                    <li key={index}>{member.name} <span className="text-muted">· {ROLE_LABELS[member.role]}</span></li>
                  ))}
                </ul>
                <label className="flex items-center gap-1.5 text-xs text-muted">
                  This tab acts as
                  <select
                    className="rounded border border-line bg-night px-1.5 py-1 text-xs focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--fs-focus)]"
                    value={role}
                    onChange={(event) => workspace.setRole(event.target.value as Role)}
                  >
                    {(Object.keys(ROLE_LABELS) as Role[]).map((value) => <option key={value} value={value}>{ROLE_LABELS[value]}</option>)}
                  </select>
                </label>
                {!project.members.some((member) => member.role === role) && (
                  <p className="text-xs text-sample">This project has no {ROLE_LABELS[role].toLowerCase()}, so notes and pins in this role will be refused.</p>
                )}
              </div>
              <div className="space-y-1.5">
                <h3 className={HEADING}>Action items</h3>
                <ProjectItems items={project.items} role={role} onUpdate={workspace.updateItem} />
                <button type="button" className={BUTTON} disabled={adding.busy} onClick={() => void addSiteItems()}>
                  {adding.busy ? "Adding…" : "Add this site's action items"}
                </button>
                {adding.problem && <p className="text-xs text-[color:var(--fs-error)]">Not added: {adding.problem}</p>}
              </div>
              <div className="space-y-1.5">
                <h3 className={HEADING}>Notes</h3>
                <Notes workspace={workspace} />
              </div>
              <div className="space-y-1.5">
                <h3 className={HEADING}>Pins</h3>
                <Pins pins={project.pins} onOpenPin={props.onOpenPin} />
              </div>
            </>
          )}
        </div>
  );

  if (embedded) {
    return (
      <div className="fs-chatscope">
        {state.status === "ok" && state.sample && <p className="pb-2 text-xs font-medium text-sample">Sample data</p>}
        {body}
      </div>
    );
  }

  return (
    <section aria-label="Project workspace" className={`fs-chatscope ${props.className ?? DOCKED} flex flex-col rounded-lg border border-line bg-panel/95 text-text shadow-lg backdrop-blur`}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-left hover:bg-line/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--fs-focus)]"
      >
        <span className="min-w-0">
          <span className="block text-sm font-semibold">Project</span>
          <span className="block truncate text-xs text-muted">{project ? project.name : state.status === "none" ? "No project open" : "…"}</span>
        </span>
        <span className="flex items-center gap-2">
          {state.status === "ok" && state.sample && <span className="rounded bg-sample/15 px-2 py-0.5 text-xs font-medium text-sample">Sample data</span>}
          <span aria-hidden="true" className="text-muted">{open ? "–" : "+"}</span>
        </span>
      </button>
      {open && body}
    </section>
  );
}
