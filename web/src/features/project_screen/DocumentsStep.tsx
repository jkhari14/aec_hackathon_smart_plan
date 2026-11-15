// Step 3: the drawings and reports that matter for this job, each slot shown only when the work makes it
// relevant. A placeholder for now: attaching records the file's name on the project so the rest of the
// team sees it was added; the file itself stays on the computer it was picked on.
import { useEffect, useRef, useState } from "react";

import { api } from "../../api/client";
import type { Project } from "../../contracts";
import { Button, formatDate } from "../../design";
import { ROLE_LABELS } from "../project/project_client";
import type { ProjectWorkspace } from "../project/useProject";
import { DOC_SLOTS, type DocSlot, type SiteFacts } from "./model";

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
  return (
    <div className="fs-ps-docs fs-enter">
      <p className="fs-quiet">Files stay on your computer for now: only the name is shared with the team. Upload is coming.</p>
      <div className="fs-ps-cards fs-ps-cards--2">
        {slots.map((slot) => (
          <Slot key={slot.id} slot={slot} files={documents.filter((d) => d.ref_id === slot.id)} workspace={workspace} />
        ))}
      </div>
    </div>
  );
}

function Slot({ slot, files, workspace }: { slot: DocSlot; files: Project["pins"]; workspace: ProjectWorkspace }) {
  const input = useRef<HTMLInputElement>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const attach = async (file: File | undefined) => {
    if (!file) return;
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
        <Button disabled={saving} onClick={() => input.current?.click()}>{saving ? "Adding…" : "Attach"}</Button>
        <input ref={input} type="file" hidden onChange={(e) => void attach(e.target.files?.[0])} />
      </div>
      <span className="fs-quiet">{slot.hint}</span>
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
