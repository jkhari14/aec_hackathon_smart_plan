// The project screen: a calmer, full-screen place for a team that has committed to a site. Setup (what the
// job is), then a checklist everyone shares live, then the documents that matter for this job.
// Live state is the project store's: useProject polls it every 4 s, so another role's change shows up here.
import "./project_screen.css";

import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { Role } from "../../contracts";
import { Badge, Button, LinkIcon, SkeletonCard } from "../../design";
import { projectWrites, ROLE_LABELS, whyNotSaved } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { ChecklistStep } from "./ChecklistStep";
import { DocumentsStep } from "./DocumentsStep";
import { draftProject, type DraftInput } from "./draft";
import { ROLES } from "./model";
import { SetupStep } from "./SetupStep";

type Step = "setup" | "checklist" | "documents";

type Props = {
  bbl: string | null;
  siteLabel?: string;
  workspace: ProjectWorkspace;
  onProjectCreated: (projectId: string) => void;
  onBack: () => void;
};

const STEPS: { value: Step; label: string }[] = [
  { value: "setup", label: "Setup" },
  { value: "checklist", label: "Checklist" },
  { value: "documents", label: "Documents" },
];

export function ProjectScreen({ bbl, siteLabel, workspace, onProjectCreated, onBack }: Props) {
  const { projectId, state } = workspace;
  const [step, setStep] = useState<Step>(projectId ? "checklist" : "setup");
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // A shared link opens straight on the checklist.
  // Without one (a new site), it starts at setup.
  useEffect(() => {
    if (projectId) setStep((s) => (s === "setup" ? "checklist" : s));
    else setStep("setup");
  }, [projectId]);

  const project = state.status === "ok" ? state.project : null;
  const siteBbl = project?.site_bbl ?? bbl;

  async function draft(input: DraftInput, me: Role) {
    setBusy(true);
    setProblem(null);
    try {
      const result = await draftProject(
        {
          create: workspace.create,
          actions: api.actions,
          addItems: async (id, items) => {
            const why = whyNotSaved(await projectWrites.addItems(id, items));
            if (why) throw new Error(why);
          },
        },
        input,
      );
      workspace.setRole(me);
      setNotice(result.notice);
      onProjectCreated(result.projectId);
      setStep("checklist");
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "The project was not created.");
    } finally {
      setBusy(false);
    }
  }

  const share = () => {
    void navigator.clipboard?.writeText(window.location.href).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    }).catch(() => undefined);
  };

  return (
    <section className="fs-ps" aria-label="Project">
      <header className="fs-ps__bar">
        <div className="fs-ps__title">
          <span className="fs-ps__eyebrow">Project</span>
          <h2>{project?.name.replace(/^Project: /, "") ?? siteLabel ?? (siteBbl ? `BBL ${siteBbl}` : "New project")}</h2>
          {siteBbl && <span className="fs-num fs-quiet">BBL {siteBbl}</span>}
        </div>
        <div className="fs-ps__tools">
          {projectId && <LiveDot workspace={workspace} />}
          {projectId && (
            <label className="fs-ps__role">
              <span>Acting as</span>
              <select value={workspace.role} onChange={(e) => workspace.setRole(e.target.value as Role)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                ))}
              </select>
            </label>
          )}
          {projectId && (
            <Button onClick={share} title="Copy a link everyone on the project can open">
              <LinkIcon width={14} height={14} /> {copied ? "Link copied" : "Share"}
            </Button>
          )}
          <Button variant="ghost" onClick={onBack}>← Map</Button>
        </div>
      </header>

      <nav className="fs-ps__steps" aria-label="Project steps">
        {STEPS.map((s, i) => {
          const locked = s.value !== "setup" && !projectId;
          const done = s.value === "setup" && Boolean(projectId);
          return (
            <button key={s.value} type="button" className="fs-ps__step" aria-current={step === s.value ? "step" : undefined}
              disabled={locked} data-done={done}
              onClick={() => setStep(s.value)}>
              <span className="fs-ps__stepnum">{done ? "✓" : i + 1}</span>
              {s.label}
            </button>
          );
        })}
      </nav>

      <div className="fs-ps__body">
        {step === "setup" && !projectId && siteBbl && (
          <SetupStep bbl={siteBbl} siteLabel={siteLabel} busy={busy} problem={problem} onDraft={draft} />
        )}
        {step === "setup" && !projectId && !siteBbl && (
          <p className="fs-quiet">Pick a site on the map first, then continue to its project.</p>
        )}
        {step === "setup" && project && <SetupSummary project={project} />}
        {step !== "setup" && projectId && !project && <Unavailable workspace={workspace} />}
        {step === "checklist" && project && (
          <ChecklistStep project={project} workspace={workspace} notice={notice} onDismissNotice={() => setNotice(null)} />
        )}
        {step === "documents" && project && <DocumentsStep project={project} workspace={workspace} />}
      </div>
    </section>
  );
}

function LiveDot({ workspace }: { workspace: ProjectWorkspace }) {
  const { state } = workspace;
  if (state.status === "ok" && state.sample) return <Badge tone="sample">Sample: changes not saved</Badge>;
  const live = state.status === "ok" && workspace.reachable;
  return (
    <span className="fs-ps__live" data-live={live} role="status"
      title={live ? "Changes from everyone on the project show here within a few seconds" : undefined}>
      <span className="fs-ps__livedot" aria-hidden="true" />
      {live ? "Live" : state.status === "loading" ? "Connecting…" : state.status === "ok" ? "Offline: showing the last copy" : "Offline"}
    </span>
  );
}

function Unavailable({ workspace }: { workspace: ProjectWorkspace }) {
  const { state } = workspace;
  if (state.status === "loading") {
    return (
      <div aria-busy="true">
        <SkeletonCard lines={2} />
        <SkeletonCard lines={2} />
      </div>
    );
  }
  return (
    <p className="fs-ps-problem" role="alert">
      {state.status === "not_found"
        ? "This project link doesn't open a project. It may have been made on another server."
        : "The project could not be reached. Nothing is shown rather than an old copy."}
    </p>
  );
}

function SetupSummary({ project }: { project: NonNullable<Extract<ProjectWorkspace["state"], { status: "ok" }>["project"]> }) {
  const line = (label: string, value: string) => (
    <div className="fs-ps-summary__row">
      <span className="fs-quiet">{label}</span>
      <strong>{value}</strong>
    </div>
  );
  const humanize = (v: string) => v.replace(/_/g, " ");
  return (
    <div className="fs-ps-summary fs-enter">
      {line("Work type", project.job_type ? humanize(project.job_type) : "not set")}
      {line("Construction", project.construction_type ? humanize(project.construction_type) : "not set")}
      {line("Scope", project.work_types.length ? project.work_types.map(humanize).join(", ") : "not set")}
      {line("Team", project.members.map((m) => `${m.name} (${ROLE_LABELS[m.role]})`).join(", "))}
      <p className="fs-quiet">The setup is fixed once the checklist is drafted. Start a new project from the map to change it.</p>
    </div>
  );
}
