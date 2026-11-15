// Similar projects: what happened on past projects like this one, and the lessons from them. Pick what you might
// do here (an option, then scopes) to narrow both views. "By risk" groups the cases into lessons, each with the
// checklist items for that risk; "By project" lists the cases, closest first. Any case opens its popup, which
// shows its lessons. "Start a project" carries the option and scopes into setup.
import { useMemo, useState } from "react";

import type { SimilarCase, WorkType } from "../../contracts";
import { Chip, EmptyState, humanize, Skeleton, Tabs } from "../../design";
import { CaseDialog, SimilarCases, type StrandControls } from "../similar_cases/SimilarCases";
import { LessonCard, useOutlook } from "./Lessons";
import { casesFor, filterLessons, lessonsByCase, type Option, OPTIONS, scopeChoices, setupFor } from "./model";
import { savePrefill } from "./prefill";

type View = "risk" | "project";

export function SimilarProjects({ bbl, results, strands, onStart }: {
  bbl: string; results: SimilarCase[]; strands?: StrandControls; onStart?: () => void;
}) {
  const outlook = useOutlook(bbl);
  const [option, setOption] = useState<Option>("all");
  const [scopes, setScopes] = useState<WorkType[]>([]);
  const [view, setView] = useState<View>("risk");
  const [openId, setOpenId] = useState<string | null>(null);

  const lessons = outlook && outlook !== "failed" ? outlook.lessons : [];
  const byCase = useMemo(() => lessonsByCase(lessons), [lessons]);
  const openable = useMemo(() => new Set(results.map((r) => r.case_id)), [results]);
  const choices = scopeChoices(lessons, option);
  const picked = scopes.filter((s) => choices.includes(s));
  const shownLessons = filterLessons(lessons, option, picked);
  const shownCases = casesFor(results, lessons, option, picked);
  const setup = setupFor(option, picked);
  const open = results.find((r) => r.case_id === openId);
  const toggle = (s: WorkType) => setScopes((xs) => (xs.includes(s) ? xs.filter((x) => x !== s) : [...xs, s]));
  const focusAndOpen = (caseId: string) => {
    if (strands && strands.focusedId !== caseId) strands.onFocus(caseId);
    setOpenId(caseId);
  };

  return (
    <div className="fs-lessons">
      <p className="fs-quiet">
        What happened on past projects like this one, and the lessons from them. Pick what you might do here to narrow it.
      </p>
      <div className="fs-filters" role="group" aria-label="What you might do">
        {OPTIONS.map((o) => (
          <Chip key={o.value} pressed={option === o.value} onClick={() => setOption(o.value)}>{o.label}</Chip>
        ))}
      </div>
      {/* Scopes come after an option: address, then everything, then what you'd do, then how. */}
      {option !== "all" && choices.length > 0 && (
        <div className="fs-filters fs-lessons__scopes" role="group" aria-label="Scope">
          {choices.map((s) => (
            <Chip key={s} pressed={picked.includes(s)} onClick={() => toggle(s)}>{humanize(s)}</Chip>
          ))}
        </div>
      )}
      <Tabs<View> label="Group similar projects" value={view} onChange={setView}
        options={[
          { value: "risk", label: <span className="fs-num">By risk {outlook && outlook !== "failed" ? shownLessons.length : ""}</span> },
          { value: "project", label: <span className="fs-num">By project {shownCases.length}</span> },
        ]} />

      {view === "risk" && outlook === null && <><Skeleton height={64} /><Skeleton height={64} /></>}
      {view === "risk" && outlook === "failed" && (
        <EmptyState title="Lessons couldn't load">They need the 4site API. The projects are still listed under By project.</EmptyState>
      )}
      {view === "risk" && outlook && outlook !== "failed" && shownLessons.length === 0 && (
        <EmptyState title="No lessons match">Clear a scope to see the rest.</EmptyState>
      )}
      {view === "risk" && shownLessons.map((l) => (
        <LessonCard key={l.id} lesson={l} openable={openable} onOpenCase={focusAndOpen} />
      ))}

      {view === "project" && (
        shownCases.length === 0
          ? <EmptyState title="No projects match">Clear a scope or pick Every option.</EmptyState>
          : <SimilarCases results={shownCases} strands={strands} embedded onOpen={setOpenId} />
      )}

      {open && <CaseDialog key={open.case_id} result={open} lessons={byCase.get(open.case_id)} onClose={() => setOpenId(null)} />}

      {setup && onStart && (
        <button type="button" className="fs-btn fs-lessons__start" onClick={() => {
          savePrefill({ bbl, ...setup });
          onStart();
        }}>
          Start a project: {OPTIONS.find((o) => o.value === option)?.label} →
        </button>
      )}
    </div>
  );
}
