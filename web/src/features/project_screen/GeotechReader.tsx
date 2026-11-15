// A geotechnical report PDF goes to the report reader. Its reading is a suggestion: the uploader checks it,
// can correct it, and confirms. Only then do the geotech rules add or flag checklist items for the roles
// they concern (each saying who added it and why). Nothing changes on a discard.
import { useEffect, useRef, useState } from "react";

import type { Project, Role } from "../../contracts";
import { Button } from "../../design";
import { readGeotech, ROLE_LABELS, type GeotechFindings, type GeotechReading } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { BoringScan } from "./BoringScan";
import type { ScanFact } from "./DrawingScan";
import { Changes } from "./DrawingReader";

type Props = {
  project: Project;
  workspace: ProjectWorkspace;
  file: File;
  slot: string;
  onDone: () => void;
  onNameOnly: () => Promise<void>;
};

const ft = (v: number | null | undefined) => (v === null || v === undefined ? null : `${v} ft`);

export function geotechFacts(f: GeotechFindings): ScanFact[] {
  return [
    { label: f.groundwater_depth_ft != null ? `Groundwater at ${ft(f.groundwater_depth_ft)}` : "Groundwater not stated", party: f.groundwater_depth_ft != null },
    f.soil_description ? { label: f.soil_description } : null,
    { label: f.allowable_bearing_tsf != null ? `Bearing ${f.allowable_bearing_tsf} tsf` : "Bearing not stated" },
    { label: f.rock_depth_ft != null ? `Rock at ${ft(f.rock_depth_ft)}` : "No rock reached" },
    f.boring_count != null ? { label: `${f.boring_count} borings${f.max_boring_depth_ft ? ` to ${f.max_boring_depth_ft} ft` : ""}` } : null,
  ].filter((x): x is ScanFact => x !== null);
}

export function GeotechReader({ project, workspace, file, slot, onDone, onNameOnly }: Props) {
  const [reading, setReading] = useState<GeotechReading | null>(null);
  const [confirmed, setConfirmed] = useState<{ at: string; role: Role; findings: GeotechFindings } | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // one read (and one API call) per upload
    started.current = true;
    readGeotech(project.id, file).then(setReading).catch(() => undefined);
  }, [project.id, file]);

  const phase = confirmed ? "ingested" : reading?.status === "ok" ? "read" : "reading";
  const findings = confirmed?.findings ?? (reading?.status === "ok" ? reading.findings : null);

  if (reading && reading.status !== "ok") {
    return (
      <div className="fs-ps-card fs-ps-reader" role="alert">
        <strong>Couldn't read {file.name}</strong>
        <p className="fs-quiet">
          {reading.status === "refused" ? reading.reason : "The report reader could not be reached."} Nothing was changed.
        </p>
        <div className="fs-ps-reader__actions">
          <Button onClick={() => void onNameOnly().then(onDone)}>Just list the file name</Button>
          <Button variant="ghost" onClick={onDone}>Close</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="fs-ps-reader">
      <BoringScan phase={phase} document={file.name} findings={findings} facts={findings ? geotechFacts(findings) : []}
        source={confirmed
          ? `AI reading of ${file.name}, confirmed by the ${ROLE_LABELS[confirmed.role].toLowerCase()}`
          : `AI reading of ${file.name} · a suggestion for you to check`} />
      {reading?.status === "ok" && !confirmed && (
        <ConfirmForm reading={reading} workspace={workspace} file={file} slot={slot} onDiscard={onDone}
          onConfirmed={(role, f) => setConfirmed({ at: new Date().toISOString(), role, findings: f })} />
      )}
      {confirmed && <Changes project={project} role={confirmed.role} since={confirmed.at} onDone={onDone} />}
    </div>
  );
}

function ConfirmForm({ reading, workspace, file, slot, onDiscard, onConfirmed }: {
  reading: Extract<GeotechReading, { status: "ok" }>;
  workspace: ProjectWorkspace;
  file: File;
  slot: string;
  onDiscard: () => void;
  onConfirmed: (role: Role, findings: GeotechFindings) => void;
}) {
  const f = reading.findings;
  const num = (v: number | null | undefined) => (v === null || v === undefined ? "" : String(v));
  const [water, setWater] = useState(num(f.groundwater_depth_ft));
  const [soil, setSoil] = useState(f.soil_description ?? "");
  const [bearing, setBearing] = useState(num(f.allowable_bearing_tsf));
  const [rock, setRock] = useState(num(f.rock_depth_ft));
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const toNum = (v: string) => {
    const n = Number(v.trim());
    return v.trim() === "" || !Number.isFinite(n) || n < 0 ? null : n;
  };

  const confirm = async () => {
    setSaving(true);
    setProblem(null);
    const role = workspace.role;
    const findings: GeotechFindings = {
      ...f,
      groundwater_depth_ft: toNum(water),
      soil_description: soil.trim().slice(0, 300) || null,
      allowable_bearing_tsf: toNum(bearing),
      rock_depth_ft: toNum(rock),
    };
    try {
      await workspace.confirmGeotech({ findings, document: file.name.slice(0, 200), slot,
        evidence: reading.evidence.slice(0, 2000) || null });
      onConfirmed(role, findings);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
      setSaving(false);
    }
  };

  const field = (label: string, value: string, set: (v: string) => void, unit?: string) => (
    <label className="fs-ps-reader__field">
      <span className="fs-quiet">{label}{unit ? ` (${unit})` : ""}</span>
      <input className="fs-ps-input" value={value} placeholder="Not stated in the report" maxLength={300}
        inputMode={unit ? "decimal" : undefined} onChange={(e) => set(e.target.value)} />
    </label>
  );

  return (
    <div className="fs-ps-card fs-ps-reader__form">
      <div>
        <strong>Check the reading</strong>
        <p className="fs-quiet">
          Read by AI from {file.name}, confidence {f.confidence.toFixed(2)} (AI readings are capped at 0.70).
          Correct anything that is wrong. Nothing changes on anyone's checklist until you confirm.
        </p>
        {reading.evidence && <p className="fs-quiet">Reader's note: {reading.evidence}</p>}
      </div>
      {field("Groundwater depth", water, setWater, "ft below grade")}
      {field("Soil", soil, setSoil)}
      {field("Allowable bearing", bearing, setBearing, "tsf")}
      {field("Rock depth", rock, setRock, "ft below grade")}
      {problem && <p className="fs-ps-problem" role="alert">{problem}</p>}
      <div className="fs-ps-reader__actions">
        <Button variant="primary" disabled={saving} onClick={() => void confirm()}>
          {saving ? "Updating the checklist…" : `Confirm as ${ROLE_LABELS[workspace.role]}`}
        </Button>
        <Button variant="ghost" disabled={saving} onClick={onDiscard}>Discard</Button>
      </div>
    </div>
  );
}
