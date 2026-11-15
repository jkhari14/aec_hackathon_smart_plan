// "Draft checklist": create the project with the setup choices, load the site's checklist for that job,
// and add it with owners. Takes its calls as arguments so it can be tested without the API.
// Sample items are never added to a real project; a failure after the project exists keeps the project
// and says what was not saved, so the team is never left with a half-made project and no explanation.
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

export async function draftProject(deps: DraftDeps, input: DraftInput): Promise<DraftResult> {
  const workTypes = scopeValues(input.jobType, input.scope);
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
    const actions = await deps.actions(input.bbl, { jobType: input.jobType, workTypes });
    if (actions.sample) {
      return { projectId, notice: "Only sample checklist items could be loaded for this site, so none were added." };
    }
    await deps.addItems(projectId, withOwners(actions.data));
    return { projectId, notice: null };
  } catch (error) {
    return { projectId, notice: `The checklist was not added: ${message(error)}` };
  }
}
