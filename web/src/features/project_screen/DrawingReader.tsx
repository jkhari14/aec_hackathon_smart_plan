// A structural drawing PDF goes to the drawing reader. Its reading is a suggestion: the uploader checks it,
// can correct it, and confirms. Only then does it become the project's model and change the checklist for
// every role it concerns (each item saying who added it and why). Nothing changes on a discard.
import { useEffect, useMemo, useRef, useState } from "react";

import type { Project, Role } from "../../contracts";
import { Button } from "../../design";
import { readDrawing, ROLE_LABELS, type DrawingReading, type StructuralModel } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { DrawingScan, type ScanFact } from "./DrawingScan";

type Props = {
  project: Project;
  workspace: ProjectWorkspace;
  file: File;
  slot: string;
  onDone: () => void;
  /** The reader is unavailable: record the file name only, as before. */
  onNameOnly: () => Promise<void>;
};

type Wall = StructuralModel["bearing_walls_on_lot_line"][number];

const wallLine = (w: Wall) =>
  [w.side === "unknown" ? "side not given" : w.side, w.material, w.length_ft ? `${w.length_ft} ft` : null].filter(Boolean).join(", ");

export function factsOf(model: StructuralModel): ScanFact[] {
  const walls = model.bearing_walls_on_lot_line.length;
  return [
    model.material ? { label: model.material } : null,
    { label: walls === 1 ? "1 wall on the lot line" : `${walls} walls on the lot line`, party: walls > 0 },
    { label: model.lateral_system ? `Lateral: ${model.lateral_system}` : "Lateral system not shown" },
    { label: model.foundation_type ? `Foundation: ${model.foundation_type}` : "Foundation not shown" },
    model.levels ? { label: `${model.levels} storeys` } : null,
  ].filter((f): f is ScanFact => f !== null);
}

export function DrawingReader({ project, workspace, file, slot, onDone, onNameOnly }: Props) {
  const [reading, setReading] = useState<DrawingReading | null>(null);
  const [confirmed, setConfirmed] = useState<{ at: string; role: Role } | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // StrictMode runs effects twice; one read (and one API call) per upload
    started.current = true;
    readDrawing(project.id, file).then(setReading).catch(() => undefined);
  }, [project.id, file]);

  const phase = confirmed ? "ingested" : reading?.status === "ok" ? "read" : "reading";
  // Once confirmed, the facts are the saved model's: the uploader's corrections included.
  const shown = confirmed && project.structural_model ? project.structural_model : reading?.status === "ok" ? reading.model : null;
  const facts = shown ? factsOf(shown) : [];

  if (reading && reading.status !== "ok") {
    return (
      <div className="fs-ps-card fs-ps-reader" role="alert">
        <strong>Couldn't read {file.name}</strong>
        <p className="fs-quiet">
          {reading.status === "refused" ? reading.reason : "The drawing reader could not be reached."} Nothing was changed.
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
      <DrawingScan phase={phase} document={file.name} facts={facts}
        source={confirmed
          ? `AI reading of ${file.name}, confirmed by the ${ROLE_LABELS[confirmed.role].toLowerCase()}`
          : `AI reading of ${file.name} · a suggestion for you to check`} />
      {reading?.status === "ok" && !confirmed && (
        <ConfirmForm reading={reading} workspace={workspace} file={file} slot={slot} onDiscard={onDone}
          onConfirmed={(role) => setConfirmed({ at: new Date().toISOString(), role })} />
      )}
      {confirmed && <Changes project={project} role={confirmed.role} since={confirmed.at} onDone={onDone} />}
    </div>
  );
}

function ConfirmForm({ reading, workspace, file, slot, onDiscard, onConfirmed }: {
  reading: Extract<DrawingReading, { status: "ok" }>;
  workspace: ProjectWorkspace;
  file: File;
  slot: string;
  onDiscard: () => void;
  onConfirmed: (role: Role) => void;
}) {
  const { model } = reading;
  const [material, setMaterial] = useState(model.material ?? "");
  const [lateral, setLateral] = useState(model.lateral_system ?? "");
  const [foundation, setFoundation] = useState(model.foundation_type ?? "");
  const [keep, setKeep] = useState<Set<string>>(() => new Set(model.bearing_walls_on_lot_line.map((w) => w.id)));
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  const confirm = async () => {
    setSaving(true);
    setProblem(null);
    const role = workspace.role;
    try {
      await workspace.confirmDrawing({
        model: {
          ...model,
          material: material.trim() || null,
          lateral_system: lateral.trim() || null,
          foundation_type: foundation.trim() || null,
          bearing_walls_on_lot_line: model.bearing_walls_on_lot_line.filter((w) => keep.has(w.id)),
        },
        document: file.name.slice(0, 200),
        slot,
        evidence: reading.evidence.slice(0, 2000) || null,
      });
      onConfirmed(role);
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
      setSaving(false);
    }
  };

  const field = (label: string, value: string, set: (v: string) => void) => (
    <label className="fs-ps-reader__field">
      <span className="fs-quiet">{label}</span>
      <input className="fs-ps-input" value={value} placeholder="Not shown on the drawing" maxLength={200}
        onChange={(e) => set(e.target.value)} />
    </label>
  );

  return (
    <div className="fs-ps-card fs-ps-reader__form">
      <div>
        <strong>Check the reading</strong>
        <p className="fs-quiet">
          Read by AI from {file.name}, confidence {model.confidence.toFixed(2)} (AI readings are capped at 0.70).
          Correct anything that is wrong. Nothing changes on anyone's checklist until you confirm.
        </p>
        {reading.evidence && <p className="fs-quiet">Reader's note: {reading.evidence}</p>}
      </div>
      {field("Material", material, setMaterial)}
      {field("Lateral system", lateral, setLateral)}
      {field("Foundation", foundation, setFoundation)}
      <fieldset className="fs-ps-reader__walls">
        <legend className="fs-quiet">Bearing walls on the lot line</legend>
        {model.bearing_walls_on_lot_line.length === 0 && <span className="fs-quiet">None shown</span>}
        {model.bearing_walls_on_lot_line.map((w) => (
          <label key={w.id}>
            <input type="checkbox" checked={keep.has(w.id)} onChange={(e) => {
              const next = new Set(keep);
              if (e.target.checked) next.add(w.id);
              else next.delete(w.id);
              setKeep(next);
            }} />
            {wallLine(w)}
          </label>
        ))}
      </fieldset>
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

/** What the confirmation added or flagged, by owner: the same items every other tab now shows. */
export function Changes({ project, role, since, onDone }: { project: Project; role: Role; since: string; onDone: () => void }) {
  const changed = useMemo(() => {
    const after = Date.parse(since) - 5000; // the server's clock may run a little behind this tab's
    return project.items.filter((i) => i.added_by_role === role && i.added_at && Date.parse(i.added_at) >= after);
  }, [project.items, role, since]);
  return (
    <div className="fs-ps-card fs-ps-reader__form" role="status">
      <strong>{changed.length === 0 ? "Confirmed. Nothing on the checklist needed to change." :
        `Checklist updated: ${changed.length} item${changed.length === 1 ? "" : "s"} added or flagged`}</strong>
      <ul className="fs-ps-reader__changes">
        {changed.map((i) => (
          <li key={i.id}>
            <span className="fs-quiet">{i.owner_role ? ROLE_LABELS[i.owner_role] : "Not assigned"}</span>
            <span>{i.title}</span>
          </li>
        ))}
      </ul>
      <p className="fs-quiet">Everyone on the project sees these within a few seconds, each saying why it was added.</p>
      <div className="fs-ps-reader__actions">
        <Button onClick={onDone}>Done</Button>
      </div>
    </div>
  );
}
