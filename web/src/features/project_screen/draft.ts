// "Draft checklist": load the site's checklist for the chosen job, then create the project with the setup
// choices and add the items with owners. Takes its calls as arguments so it can be tested without the API.
// The checklist is loaded first, so a sample or failed load makes no project at all (setup keeps its
// choices and says why). Only a refused save after the project exists leaves it empty, with a notice and
// a retry (`addProjectItems`), never as "no items for this work type".
import type { ActionItem, ConstructionType, JobType, ProjectCreate, Role, WorkType } from "../../contracts";
import { scopeValues, type ScopeOption, withOwners } from "./model.ts";

export type DraftInput = {
  bbl: string;
  siteLabel?: string;
  jobType: JobType;
  constructionType: ConstructionType;
  scope: ScopeOption[];
  members: { name: string; role: Role }[];
};

export type DraftDeps = {
  /** Resolves to the new project's id; rejects with the reason it was not created. */
  create: (body: ProjectCreate) => Promise<string>;
  actions: (bbl: string, opts: { jobType: JobType; workTypes: WorkType[] }) => Promise<{ data: ActionItem[]; sample: boolean }>;
  /** Rejects with the reason nothing was saved. */
  addItems: (projectId: string, items: ActionItem[]) => Promise<void>;
};

/** `notice` is a line to show on the checklist when its items could not be added; null when they were. */
export type DraftResult = { projectId: string; notice: string | null };

const message = (error: unknown) => (error instanceof Error ? error.message : "Something went wrong.");

const SAMPLE = "Only sample checklist items could be loaded for this site, so no project was made from them.";

/** The checklist for a job on a site, with owners. Rejects on a failed load or sample data. */
async function loadItems(deps: DraftDeps, bbl: string, jobType: JobType, workTypes: WorkType[], members?: Role[]): Promise<ActionItem[]> {
  const actions = await deps.actions(bbl, { jobType, workTypes });
  if (actions.sample) throw new Error(SAMPLE);
  return withOwners(actions.data, members);
}

export async function draftProject(deps: DraftDeps, input: DraftInput): Promise<DraftResult> {
  const workTypes = scopeValues(input.jobType, input.scope);
  const items = await loadItems(deps, input.bbl, input.jobType, workTypes, input.members.map((m) => m.role));
  const projectId = await deps.create({
    name: `Project: ${input.siteLabel ?? input.bbl}`,
    site_bbl: input.bbl,
    stage: "pre_filing",
    members: input.members,
    job_type: input.jobType,
    construction_type: input.constructionType,
    work_types: workTypes,
  });
  try {
    await deps.addItems(projectId, items);
    return { projectId, notice: null };
  } catch (error) {
    return { projectId, notice: `The checklist was not added: ${message(error)}` };
  }
}

/** Retry for a project whose items were not saved: reload its checklist from the saved setup and add it. */
export async function addProjectItems(
  deps: Pick<DraftDeps, "actions" | "addItems">,
  project: { id: string; site_bbl: string; job_type?: JobType | null; work_types: WorkType[]; members?: { role: Role }[] },
): Promise<void> {
  if (!project.job_type) throw new Error("This project has no work type saved, so its checklist cannot be drafted.");
  const members = project.members?.map((m) => m.role);
  const items = await loadItems(deps as DraftDeps, project.site_bbl, project.job_type, project.work_types, members);
  await deps.addItems(project.id, items);
}
