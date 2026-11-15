// Lessons from similar past projects: a card per risk (failure mode) with its incidents, the checklist items
// for it and what this lot's own records show. Shown inside the Similar projects tab. Not blame: incidents are
// what happened on similar projects, causes only as reported.
import "./lessons.css";

import { useEffect, useState, type CSSProperties } from "react";

import { api } from "../../api/client";
import type { Lesson, SiteOutlook } from "../../contracts";
import { HAZARD_LABELS } from "../../design";

/** The lessons for a lot (null while loading, "failed" when the API couldn't answer: sample lessons are never shown). */
export function useOutlook(bbl: string): SiteOutlook | null | "failed" {
  const [outlook, setOutlook] = useState<SiteOutlook | null | "failed">(null);
  useEffect(() => {
    let live = true;
    setOutlook(null);
    api.outlook(bbl).then(({ data, sample }) => live && setOutlook(sample ? "failed" : data));
    return () => {
      live = false;
    };
  }, [bbl]);
  return outlook;
}

/** `openable` are the incidents that are also among this lot's similar cases: those open their popup. */
export function LessonCard({ lesson, openable, onOpenCase }: {
  lesson: Lesson; openable?: Set<string>; onOpenCase?: (caseId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <article className="fs-lesson" style={{ "--fs-hz": `var(--fs-hz-${lesson.hazard})` } as CSSProperties}>
      <h4 className="fs-lesson__title">{lesson.label}</h4>
      <p className="fs-lesson__meta fs-num">
        {lesson.case_count} past incident{lesson.case_count === 1 ? "" : "s"} · {HAZARD_LABELS[lesson.hazard]}
      </p>
      {lesson.here && <p className="fs-lesson__here">{lesson.here}</p>}
      <div className="fs-lesson__prevent">
        <span className="fs-lesson__label">Checklist items for this risk</span>
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
              {onOpenCase && openable?.has(c.case_id) ? (
                <button type="button" className="fs-linkbtn fs-lesson__case" onClick={() => onOpenCase(c.case_id)}>{c.title}</button>
              ) : (
                <span>{c.title}</span>
              )}
              <span className="fs-quiet fs-num">
                {c.address.split(",")[0]} · {c.date.slice(0, 4)}
                {c.basis === "event_only" ? " · no cause published" : " · cause as reported"}
              </span>
              <span className="fs-quiet">
                Source:{" "}
                {c.source_url ? <a href={c.source_url} target="_blank" rel="noreferrer">{c.source_name}</a> : c.source_name}
              </span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
