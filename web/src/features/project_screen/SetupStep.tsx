// Step 1: say what the job is, on cards. Work type and construction type are one choice each; scope is
// pre-ticked from the work type; everyone on the project is added so items can be assigned to any role.
import { type ReactNode, useState } from "react";

import type { ConstructionType, JobType, Role, Stage } from "../../contracts";
import { Button } from "../../design";
import { ROLE_LABELS } from "../project/project_client";
import type { DraftInput } from "./draft";
import { KnownFacts } from "./KnownFacts";
import {
  CONSTRUCTION_CARDS, defaultScope, DEPTH_BANDS, type DepthBand, ROLES, SCOPE_OPTIONS, type ScopeOption, STAGE_OPTIONS, WORK_TYPE_CARDS,
} from "./model";

type Props = {
  bbl: string;
  siteLabel?: string;
  busy: boolean;
  problem: string | null;
  onDraft: (input: DraftInput, myRole: Role) => void;
};

export function SetupStep({ bbl, siteLabel, busy, problem, onDraft }: Props) {
  const [job, setJob] = useState<JobType | null>(null);
  const [construction, setConstruction] = useState<ConstructionType | null>(null);
  const [scope, setScope] = useState<ScopeOption[]>([]);
  const [names, setNames] = useState<Record<Role, string>>({ architect: "", structural_engineer: "", developer: "", contractor: "" });
  const [me, setMe] = useState<Role>("architect");
  const [depth, setDepth] = useState<DepthBand>("unsure");
  const [storeys, setStoreys] = useState("");
  const [stage, setStage] = useState<Stage>("design");

  const pickJob = (value: JobType) => {
    setJob(value);
    setScope(defaultScope(value));
  };
  const toggleScope = (value: ScopeOption) =>
    setScope((s) => (s.includes(value) ? s.filter((x) => x !== value) : [...s, value]));
  const ready = job !== null && construction !== null && !busy;
  // Depth matters only when the job digs; the new building's height only for new construction.
  const digs = scope.includes("excavation") || scope.includes("foundation");
  const building = job === "new_building";
  const storeysValue = building && storeys.trim() !== "" && Number(storeys) > 0 ? Number(storeys) : null;

  const submit = () => {
    if (!job || !construction) return;
    onDraft(
      {
        bbl,
        siteLabel,
        jobType: job,
        constructionType: construction,
        scope,
        members: ROLES.map((role) => ({ name: names[role].trim() || ROLE_LABELS[role], role })),
        depthFt: digs ? (DEPTH_BANDS.find((b) => b.value === depth)?.feet ?? null) : null,
        proposedStoreys: storeysValue,
        stage,
      },
      me,
    );
  };

  return (
    <div className="fs-ps-setup fs-enter">
      <KnownFacts bbl={bbl} />

      <Group title="Work type" help="What is happening on this site?">
        <div className="fs-ps-cards fs-ps-cards--3">
          {WORK_TYPE_CARDS.map((c) => (
            <button key={c.value} type="button" className="fs-ps-card" aria-pressed={job === c.value} onClick={() => pickJob(c.value)}>
              <strong>{c.label}</strong>
              <span>{c.hint}</span>
            </button>
          ))}
        </div>
      </Group>

      <Group title="Construction type" help="What the building is mostly built of.">
        <div className="fs-ps-cards fs-ps-cards--5">
          {CONSTRUCTION_CARDS.map((c) => (
            <button key={c.value} type="button" className="fs-ps-card fs-ps-card--small" aria-pressed={construction === c.value}
              onClick={() => setConstruction(c.value)}>
              <strong>{c.label}</strong>
            </button>
          ))}
        </div>
      </Group>

      {job && (
        <Group title="Scope" help="Pre-ticked for this work type. Untick what doesn't apply.">
          <div className="fs-ps-chips" role="group" aria-label="Scope">
            {SCOPE_OPTIONS.map((o) => (
              <button key={o.value} type="button" className="fs-chip" aria-pressed={scope.includes(o.value)} onClick={() => toggleScope(o.value)}>
                {o.label}
              </button>
            ))}
          </div>
        </Group>
      )}

      {job && (
        <Group title="The job" help="Three quick answers the code turns on. Each one changes the checklist.">
          <div className="fs-ps-quick">
            {digs && (
              <div className="fs-ps-field">
                <span className="fs-ps-field__label">How deep will you dig?</span>
                <div className="fs-ps-chips" role="group" aria-label="How deep will you dig?">
                  {DEPTH_BANDS.map((b) => (
                    <button key={b.value} type="button" className="fs-chip" aria-pressed={depth === b.value} onClick={() => setDepth(b.value)}>
                      {b.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {building && (
              <label className="fs-ps-field">
                <span className="fs-ps-field__label">New building height</span>
                <span className="fs-ps-storeys">
                  <input className="fs-ps-input" type="number" min={1} max={120} inputMode="numeric" placeholder="e.g. 6"
                    value={storeys} onChange={(e) => setStoreys(e.target.value)} aria-label="New building height in storeys" />
                  <span className="fs-quiet">storeys</span>
                </span>
              </label>
            )}
            <div className="fs-ps-field">
              <span className="fs-ps-field__label">Stage</span>
              <div className="fs-ps-chips" role="group" aria-label="Stage">
                {STAGE_OPTIONS.map((o) => (
                  <button key={o.value} type="button" className="fs-chip" aria-pressed={stage === o.value} onClick={() => setStage(o.value)}>
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Group>
      )}

      <Group title="Who's on it" help="Everyone shares one checklist. Names are optional.">
        <div className="fs-ps-cards fs-ps-cards--4">
          {ROLES.map((role) => (
            <div key={role} className="fs-ps-card fs-ps-card--role" data-me={me === role}>
              <strong>{ROLE_LABELS[role]}</strong>
              <input className="fs-ps-input" placeholder="Name (optional)" value={names[role]} maxLength={80}
                aria-label={`${ROLE_LABELS[role]} name`}
                onChange={(e) => setNames((n) => ({ ...n, [role]: e.target.value }))} />
              <label className="fs-ps-me">
                <input type="radio" name="fs-ps-me" checked={me === role} onChange={() => setMe(role)} />
                That's me
              </label>
            </div>
          ))}
        </div>
      </Group>

      <div className="fs-ps-submit">
        {problem && <p className="fs-ps-problem" role="alert">{problem}</p>}
        <Button variant="primary" disabled={!ready} onClick={submit}>
          {busy ? "Drafting…" : "Draft checklist →"}
        </Button>
        {!job || !construction ? <span className="fs-quiet">Pick a work type and a construction type.</span> : null}
      </div>
    </div>
  );
}

function Group({ title, help, children }: { title: string; help: string; children: ReactNode }) {
  return (
    <section className="fs-ps-group">
      <h3 className="fs-label">{title}</h3>
      <p className="fs-quiet">{help}</p>
      {children}
    </section>
  );
}
