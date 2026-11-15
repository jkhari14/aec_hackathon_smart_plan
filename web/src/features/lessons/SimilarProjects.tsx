// Similar projects: past projects like this one, closest first, and what went wrong on them. Pick what you might
// do here (an option, then scopes) to narrow. "Watch out for" sums up the risks most of the listed projects
// share; click one to see its checklist items and only those projects. Each card is tagged with its risks and
// its popup holds its lessons. "Start a project" carries the option and scopes into setup.
import { type CSSProperties, useMemo, useState } from "react";

import type { SimilarCase, WorkType } from "../../contracts";
import { Chip, EmptyState, humanize, Skeleton } from "../../design";
import { CaseDialog, SimilarCases, type StrandControls } from "../similar_cases/SimilarCases";
import { useOutlook } from "./Lessons";
import { casesFor, filterLessons, lessonsByCase, type Option, OPTIONS, scopeChoices, setupFor, topRisks } from "./model";
import { savePrefill } from "./prefill";

export function SimilarProjects({ bbl, results, strands, onStart }: {
  bbl: string; results: SimilarCase[]; strands?: StrandControls; onStart?: () => void;
}) {
  const outlook = useOutlook(bbl);
  const [option, setOption] = useState<Option>("all");
  const [scopes, setScopes] = useState<WorkType[]>([]);
  const [risk, setRisk] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  const lessons = outlook && outlook !== "failed" ? outlook.lessons : [];
  const byCase = useMemo(() => lessonsByCase(lessons), [lessons]);
  const choices = scopeChoices(lessons, option);
  const picked = scopes.filter((s) => choices.includes(s));
  const narrowed = casesFor(results, lessons, option, picked);
  const top = topRisks(filterLessons(lessons, option, picked), narrowed);
  const chosen = top.find((t) => t.lesson.id === risk)?.lesson ?? null;
  const listed = chosen ? narrowed.filter((r) => chosen.tagged.some((t) => t.case_id === r.case_id)) : narrowed;
  const riskTags = useMemo(() => new Map([...byCase].map(([id, xs]) => [id, xs.map((x) => x.lesson.label)])), [byCase]);
  const setup = setupFor(option, picked);
  const open = results.find((r) => r.case_id === openId);
  const toggle = (s: WorkType) => setScopes((xs) => (xs.includes(s) ? xs.filter((x) => x !== s) : [...xs, s]));

  return (
    <div className="fs-lessons">
      <p className="fs-quiet">
        Past projects like this one, and what went wrong on them. Pick what you might do here to narrow it.
      </p>
      <div className="fs-filters" role="group" aria-label="What you might do">
        {OPTIONS.map((o) => (
          <Chip key={o.value} pressed={option === o.value} onClick={() => { setOption(o.value); setRisk(null); }}>{o.label}</Chip>
        ))}
      </div>
      {/* Scopes come after an option: address, then everything, then what you'd do, then how. */}
      {option !== "all" && choices.length > 0 && (
        <div className="fs-filters fs-lessons__scopes" role="group" aria-label="Scope">
          {choices.map((s) => (
            <Chip key={s} pressed={picked.includes(s)} onClick={() => { toggle(s); setRisk(null); }}>{humanize(s)}</Chip>
          ))}
        </div>
      )}

      {outlook === null && <Skeleton height={72} />}
      {outlook && outlook !== "failed" && top.length > 0 && (
        <section className="fs-watch" aria-label="Watch out for">
          <h4 className="fs-watch__title">Watch out for</h4>
          <ul className="fs-watch__list">
            {top.map(({ lesson, count }) => (
              <li key={lesson.id}>
                <button type="button" className="fs-watch__risk" aria-pressed={risk === lesson.id}
                  style={{ "--fs-hz": `var(--fs-hz-${lesson.hazard})` } as CSSProperties}
                  onClick={() => setRisk(risk === lesson.id ? null : lesson.id)}>
                  <span>{lesson.label}</span>
                  <span className="fs-num fs-watch__count">{count} of these projects</span>
                </button>
              </li>
            ))}
          </ul>
          {chosen && (
            <div className="fs-watch__items">
              <span className="fs-lesson__label">Checklist items for this risk</span>
              <ul>
                {chosen.prevent_with.map((p) => (
                  <li key={p.source_rule}>{p.title}{p.code_ref ? <span className="fs-num fs-quiet"> · {p.code_ref.replace(/^2022 NYC /, "")}</span> : null}</li>
                ))}
              </ul>
              {chosen.here && <p className="fs-lesson__here">{chosen.here}</p>}
            </div>
          )}
        </section>
      )}

      {listed.length === 0
        ? <EmptyState title="No projects match">Clear a scope or pick Every option.</EmptyState>
        : <SimilarCases results={listed} strands={strands} embedded onOpen={setOpenId} riskTags={riskTags} />}

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
