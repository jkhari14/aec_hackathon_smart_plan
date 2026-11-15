// "Draft checklist": load the site's checklist for the chosen job, then create the project with the setup
// choices and add the items with owners. Takes its calls as arguments so it can be tested without the API.
// The checklist is loaded first, so a sample or failed load makes no project at all (setup keeps its
// choices and says why). Only a refused save after the project exists leaves it empty, with a notice and
// a retry (`addProjectItems`), never as "no items for this work type".
import type { ActionItem, ConstructionType, JobType, ProjectCreate, Role, Stage, WorkType } from "../../contracts";
import { scopeValues, type ScopeOption, withOwners } from "./model.ts";

export type DraftInput = {
  bbl: string;
  siteLabel?: string;
  jobType: JobType;
  constructionType: ConstructionType;
  scope: ScopeOption[];
  members: { name: string; role: Role }[];
  /** Setup's quick answers. A null depth is "not sure" and is left out; stage defaults to design. */
  depthFt?: number | null;
  proposedStoreys?: number | null;
  stage?: Stage;
};

/** What the checklist call takes beyond the BBL. */
export type ActionsOptions = { jobType: JobType; workTypes: WorkType[]; depthFt?: number; proposedStoreys?: number; stage?: Stage };

/** The optional answers, with empty ones left out rather than sent as null or zero. */
function answers(depthFt?: number | null, proposedStoreys?: number | null) {
  return {
    ...(depthFt != null ? { depthFt } : {}),
    ...(proposedStoreys != null ? { proposedStoreys } : {}),
  };
}

export type DraftDeps = {
  /** Resolves to the new project's id; rejects with the reason it was not created. */
  create: (body: ProjectCreate) => Promise<string>;
  actions: (bbl: string, opts: ActionsOptions) => Promise<{ data: ActionItem[]; sample: boolean }>;
  /** Rejects with the reason nothing was saved. */
  addItems: (projectId: string, items: ActionItem[]) => Promise<void>;
};

/** `notice` is a line to show on the checklist when its items could not be added; null when they were. */
export type DraftResult = { projectId: string; notice: string | null };

const message = (error: unknown) => (error instanceof Error ? error.message : "Something went wrong.");

const SAMPLE = "Only sample checklist items could be loaded for this site, so no project was made from them.";

/** The checklist for a job on a site, with owners. Rejects on a failed load or sample data. */
async function loadItems(deps: DraftDeps, bbl: string, opts: ActionsOptions, members?: Role[]): Promise<ActionItem[]> {
  const actions = await deps.actions(bbl, opts);
  if (actions.sample) throw new Error(SAMPLE);
  return withOwners(actions.data, members);
}

export async function draftProject(deps: DraftDeps, input: DraftInput): Promise<DraftResult> {
  const workTypes = scopeValues(input.jobType, input.scope);
  const stage = input.stage ?? "design";
  const given = answers(input.depthFt, input.proposedStoreys);
  const items = await loadItems(deps, input.bbl, { jobType: input.jobType, workTypes, ...given, stage },
    input.members.map((m) => m.role));
  const projectId = await deps.create({
    name: `Project: ${input.siteLabel ?? input.bbl}`,
    site_bbl: input.bbl,
    stage,
    ...(given.depthFt != null ? { excavation_depth_ft: given.depthFt } : {}),
    ...(given.proposedStoreys != null ? { proposed_storeys: given.proposedStoreys } : {}),
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
  project: {
    id: string; site_bbl: string; job_type?: JobType | null; work_types: WorkType[]; members?: { role: Role }[];
    stage?: Stage; excavation_depth_ft?: number | null; proposed_storeys?: number | null;
  },
): Promise<void> {
  if (!project.job_type) throw new Error("This project has no work type saved, so its checklist cannot be drafted.");
  const members = project.members?.map((m) => m.role);
  const opts: ActionsOptions = { jobType: project.job_type, workTypes: project.work_types,
    ...answers(project.excavation_depth_ft, project.proposed_storeys), ...(project.stage ? { stage: project.stage } : {}) };
  const items = await loadItems(deps as DraftDeps, project.site_bbl, opts, members);
  await deps.addItems(project.id, items);
}
