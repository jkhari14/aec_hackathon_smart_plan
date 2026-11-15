// Step 3: the drawings and reports that matter for this job, each slot shown only when the work makes it
// relevant. A structural drawing PDF is read by the drawing reader (DrawingReader): once the uploader
// confirms the reading, the checklist changes for every role it concerns. Any other file records its name
// on the project so the rest of the team sees it was added; the file itself stays on this computer.
import { useEffect, useRef, useState } from "react";

import { api } from "../../api/client";
import type { Project } from "../../contracts";
import { Button, formatDate } from "../../design";
import { ROLE_LABELS } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { DrawingReader } from "./DrawingReader";
import { DOC_SLOTS, type DocSlot, type SiteFacts } from "./model";

/** Slots whose PDFs go to the drawing reader. */
const READ_SLOTS = new Set(["structural"]);
const isPdf = (file: File) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

export function DocumentsStep({ project, workspace }: { project: Project; workspace: ProjectWorkspace }) {
  // Attached neighbours bring the neighbour survey; sample or failed profiles count as unknown, not attached.
  const [site, setSite] = useState<SiteFacts>({});
  useEffect(() => {
    let live = true;
    api.siteProfile(project.site_bbl).then((p) => {
      if (live && !p.sample && p.data.bbl === project.site_bbl) setSite({ attached: p.data.neighbors.some((n) => n.attached) });
    }).catch(() => undefined);
    return () => {
      live = false;
    };
  }, [project.site_bbl]);
  const slots = DOC_SLOTS.filter((s) => s.relevant(project.job_type ?? null, project.work_types, site));
  const documents = project.pins.filter((p) => p.kind === "document");
  const [reading, setReading] = useState<{ file: File; slot: string } | null>(null);
  if (reading) {
    return (
      <div className="fs-ps-docs fs-enter">
        <DrawingReader key={`${reading.file.name}-${reading.file.lastModified}`} project={project} workspace={workspace}
          file={reading.file} slot={reading.slot} onDone={() => setReading(null)}
          onNameOnly={() => workspace.addPin({ kind: "document", ref_id: reading.slot, title: reading.file.name.slice(0, 200) })} />
      </div>
    );
  }
  return (
    <div className="fs-ps-docs fs-enter">
      <p className="fs-quiet">
        A structural drawing PDF is read by AI and, once you confirm the reading, updates everyone's checklist.
        Other files stay on your computer: only the name is shared with the team.
      </p>
      <div className="fs-ps-cards fs-ps-cards--2">
        {slots.map((slot) => (
          <Slot key={slot.id} slot={slot} files={documents.filter((d) => d.ref_id === slot.id)} workspace={workspace}
            onRead={READ_SLOTS.has(slot.id) ? (file) => setReading({ file, slot: slot.id }) : undefined} />
        ))}
      </div>
    </div>
  );
}

function Slot({ slot, files, workspace, onRead }: {
  slot: DocSlot; files: Project["pins"]; workspace: ProjectWorkspace; onRead?: (file: File) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const attach = async (file: File | undefined) => {
    if (!file) return;
    if (onRead && isPdf(file)) {
      if (input.current) input.current.value = "";
      onRead(file);
      return;
    }
    setSaving(true);
    setProblem(null);
    try {
      await workspace.addPin({ kind: "document", ref_id: slot.id, title: file.name.slice(0, 200) });
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "Not saved.");
    } finally {
      setSaving(false);
      if (input.current) input.current.value = "";
    }
  };

  return (
    <div className="fs-ps-card fs-ps-doc" data-filled={files.length > 0}>
      <div className="fs-ps-doc__head">
        <strong>{slot.label}</strong>
        <Button disabled={saving} onClick={() => input.current?.click()}>
          {saving ? "Adding…" : onRead ? "Upload" : "Attach"}
        </Button>
        <input ref={input} type="file" hidden onChange={(e) => void attach(e.target.files?.[0])} />
      </div>
      <span className="fs-quiet">{slot.hint}{onRead && ". A PDF is read by AI for you to confirm"}</span>
      {files.length > 0 ? (
        <ul className="fs-ps-doc__files">
          {files.map((f) => (
            <li key={f.id}>
              <span>{f.title}</span>
              <span className="fs-quiet fs-num">{ROLE_LABELS[f.by_role]} · {formatDate(f.created_at)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <span className="fs-ps-doc__empty">Nothing attached yet</span>
      )}
      {problem && <p className="fs-ps-problem" role="alert">{problem}</p>}
    </div>
  );
}
