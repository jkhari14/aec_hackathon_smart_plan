// "What could go wrong here": lessons from similar past projects for every option, worst first. Pick an option,
// then scopes, to narrow; each lesson says what prevents it and what this lot's own records already show.
// Not blame: incidents are what happened on similar projects, causes only as reported.
import "./lessons.css";

import { useEffect, useState, type CSSProperties } from "react";

import { api } from "../../api/client";
import type { Lesson, SiteOutlook, WorkType } from "../../contracts";
import { Chip, EmptyState, HAZARD_LABELS, humanize, Skeleton } from "../../design";
import { filterLessons, type Option, OPTIONS, scopeChoices, setupFor } from "./model";
import { savePrefill } from "./prefill";

export function Lessons({ bbl, onStart }: { bbl: string; onStart?: () => void }) {
  const [outlook, setOutlook] = useState<SiteOutlook | null | "failed">(null);
  const [option, setOption] = useState<Option>("all");
  const [scopes, setScopes] = useState<WorkType[]>([]);

  useEffect(() => {
    let live = true;
    setOutlook(null);
    api.outlook(bbl).then(({ data, sample }) => live && setOutlook(sample ? "failed" : data));
    return () => {
      live = false;
    };
  }, [bbl]);

  if (outlook === null) return <div className="fs-lessons"><Skeleton height={64} /><Skeleton height={64} /></div>;
  if (outlook === "failed") {
    return <EmptyState title="Lessons couldn't load">The lessons for this lot need the 4site API. Try again in a moment.</EmptyState>;
  }

  const choices = scopeChoices(outlook.lessons, option);
  const picked = scopes.filter((s) => choices.includes(s));
  const shown = filterLessons(outlook.lessons, option, picked);
  const setup = setupFor(option, picked);
  const toggle = (s: WorkType) => setScopes((xs) => (xs.includes(s) ? xs.filter((x) => x !== s) : [...xs, s]));

  return (
    <div className="fs-lessons">
      <p className="fs-quiet">
        What went wrong on similar past projects, and what prevents it. Pick what you might do here to narrow it.
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
      <p className="fs-quiet fs-num">{shown.length} of {outlook.lessons.length} lessons</p>

      {shown.length === 0 && <EmptyState title="No lessons match">Clear a scope to see the rest.</EmptyState>}
      {shown.map((l) => <LessonCard key={l.id} lesson={l} />)}

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

function LessonCard({ lesson }: { lesson: Lesson }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="fs-lesson" style={{ "--fs-hz": `var(--fs-hz-${lesson.hazard})` } as CSSProperties}>
      <h4 className="fs-lesson__title">{lesson.label}</h4>
      <p className="fs-lesson__meta fs-num">
        {lesson.case_count} past incident{lesson.case_count === 1 ? "" : "s"} · {HAZARD_LABELS[lesson.hazard]}
      </p>
      {lesson.here && <p className="fs-lesson__here">{lesson.here}</p>}
      <div className="fs-lesson__prevent">
        <span className="fs-lesson__label">Prevent it with</span>
        <ul>
          {lesson.prevent_with.map((p) => (
            <li key={p.source_rule}>
              {p.title}
              {p.code_ref && <span className="fs-num fs-quiet"> · {p.code_ref.replace(/^2022 NYC /, "")}</span>}
            </li>
          ))}
        </ul>
      </div>
      <button type="button" className="fs-linkbtn fs-lesson__toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Hide the incidents" : `See the closest incident${lesson.cases.length === 1 ? "" : "s"}`}
      </button>
      {open && (
        <ul className="fs-lesson__cases">
          {lesson.cases.map((c) => (
            <li key={c.case_id}>
              <span>{c.title}</span>
              <span className="fs-quiet fs-num">
                {c.address.split(",")[0]} · {c.date.slice(0, 4)}
                {c.basis === "event_only" ? " · no cause published" : " · cause as reported"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
