// Similar cases: past events on sites with a similar profile. Each card says what matches and what
// differs; causes appear only as publicly reported or under investigation. No blame, no "would have
// prevented". Filters narrow by hazard, severity and date.
import "./similar_cases.css";

import { type CSSProperties, type MouseEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { Hazard, Severity, SimilarCase } from "../../contracts";
import { SEVERITY_LABELS } from "../../contracts";
import { causeText, copy } from "../../copy";
import { Chip, EmptyState, formatDate, HAZARD_LABELS, SeverityBadge, SourceLabel, Toggle } from "../../design";
import { ringDash } from "./ring";

type Since = "all" | "2020" | "2015";
const SINCE: { value: Since; label: string }[] = [
  { value: "all", label: "Any date" },
  { value: "2015", label: "Since 2015" },
  { value: "2020", label: "Since 2020" },
];

const S = copy.similarCases;

/** One strand at a time: the case joined to the site on the map, and the switch that draws them all. */
export type StrandControls = { focusedId: string | null; onFocus: (caseId: string) => void; all: boolean; onAll: (on: boolean) => void };

export function SimilarCases({ results, strands }: { results: SimilarCase[]; strands?: StrandControls }) {
  const [hazards, setHazards] = useState<Set<Hazard>>(new Set());
  const [severities, setSeverities] = useState<Set<Severity>>(new Set());
  const [since, setSince] = useState<Since>("all");
  const [openId, setOpenId] = useState<string | null>(null);

  const available = useMemo(() => {
    const h = new Set<Hazard>(), s = new Set<Severity>();
    results.forEach((r) => {
      r.case.hazards.forEach((x) => h.add(x));
      s.add(r.case.severity);
    });
    return { hazards: [...h], severities: [...s].sort((a, b) => b - a) };
  }, [results]);

  const shown = results
    .filter((r) => hazards.size === 0 || r.case.hazards.some((h) => hazards.has(h)))
    .filter((r) => severities.size === 0 || severities.has(r.case.severity))
    .filter((r) => since === "all" || r.case.date.slice(0, 4) >= since)
    .sort((a, b) => b.score - a.score);

  const toggle = <T,>(set: Set<T>, value: T, apply: (s: Set<T>) => void) => {
    const next = new Set(set);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    apply(next);
  };
  const filtered = hazards.size > 0 || severities.size > 0 || since !== "all";

  if (results.length === 0) {
    return <EmptyState title="No similar cases yet">The case library has no past event on a site with this profile.</EmptyState>;
  }

  return (
    <div className="fs-similar">
      <p className="fs-quiet">{S.help}</p>
      {strands && (
        <div className="fs-similar__strands">
          <Toggle checked={strands.all} onChange={strands.onAll} label="Show all strands"
            hint="Or pick a case to see it joined to this site on the map" />
        </div>
      )}
      <div className="fs-filters" role="group" aria-label="Filter similar cases">
        {available.hazards.map((h) => (
          <Chip key={h} hazard={h} pressed={hazards.has(h)} onClick={() => toggle(hazards, h, setHazards)}>
            {HAZARD_LABELS[h]}
          </Chip>
        ))}
        {available.severities.map((s) => (
          <Chip key={s} pressed={severities.has(s)} onClick={() => toggle(severities, s, setSeverities)}>
            {SEVERITY_LABELS[s]}
          </Chip>
        ))}
        {SINCE.filter((o) => o.value !== "all").map((o) => (
          <Chip key={o.value} pressed={since === o.value} onClick={() => setSince(since === o.value ? "all" : o.value)}>
            {o.label}
          </Chip>
        ))}
      </div>

      <p className="fs-quiet fs-num">
        {shown.length} of {results.length} case{results.length > 1 ? "s" : ""}, closest first
        {filtered && (
          <button
            type="button"
            className="fs-linkbtn"
            onClick={() => {
              setHazards(new Set());
              setSeverities(new Set());
              setSince("all");
            }}
          >
            Clear filters
          </button>
        )}
      </p>

      {shown.length === 0 && <EmptyState title={S.empty}>Clear a filter to see the rest.</EmptyState>}

      {shown.map((r) => (
        <CaseCard key={r.case_id} result={r} focused={strands?.focusedId === r.case_id}
          onFocus={strands ? () => strands.onFocus(r.case_id) : undefined} onOpen={() => setOpenId(r.case_id)} />
      ))}
      {(() => {
        const open = results.find((r) => r.case_id === openId);
        return open ? <CaseDialog key={open.case_id} result={open} onClose={() => setOpenId(null)} /> : null;
      })()}
    </div>
  );
}

const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;
const sentence = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const where = (c: SimilarCase["case"]) => {
  const borough = c.address.split(",").slice(1).join(",").trim();
  return `${c.address.split(",")[0]}${borough ? ` · ${borough}` : ""} · ${c.date.length === 10 ? formatDate(c.date) : c.date}`;
};

/** A case in two lines: the ring, what it was, where and when, and how much it shares with this site.
    Clicking anywhere on a card shows that case joined to the site on the map (its title row again lets go);
    "N things in common" opens the details in a popup. */
function CaseCard({ result, focused, onFocus, onOpen }: {
  result: SimilarCase; focused: boolean; onFocus?: () => void; onOpen: () => void;
}) {
  const c = result.case;
  const common = result.matched_on.length;
  const differs = result.differs_on.length;
  // Any click on an unfocused card picks it, the details button included. The title row is the one place
  // that also lets go, so it is left to its own button.
  const pick = (event: MouseEvent) => {
    if (!onFocus || focused || (event.target as HTMLElement).closest(".fs-case__main")) return;
    onFocus();
  };
  return (
    <article className="fs-case" data-case-id={result.case_id} data-focused={focused} data-pickable={Boolean(onFocus) && !focused} onClickCapture={pick}
      style={{ "--fs-hz": `var(--fs-hz-${c.hazards[0]})` } as CSSProperties}>
      <button type="button" className="fs-case__main" aria-pressed={focused} onClick={onFocus} disabled={!onFocus}
        title={focused ? "Hide it on the map" : "Show it joined to this site on the map"}>
        <ScoreRing score={result.score} />
        <span className="fs-case__head">
          <span className="fs-case__title">{c.title}</span>
          <span className="fs-case__meta fs-num">{where(c)}</span>
        </span>
        <SeverityBadge level={c.severity} />
      </button>
      <button type="button" className="fs-case__open" onClick={onOpen} aria-haspopup="dialog">
        {plural(common, "thing", "things")} in common{differs > 0 && `, ${plural(differs, "difference", "differences")}`}
        <span aria-hidden="true"> · Details</span>
      </button>
    </article>
  );
}

/** The case's details in a popup: in common, different, what happened, sources. X, Esc or a click outside
    closes it; the map keeps the case's strand behind it. */
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** The card a popup belongs to, measured now (the panel may have scrolled since it opened). */
function cardRect(caseId: string): DOMRect | null {
  const card = document.querySelector<HTMLElement>(`.fs-case[data-case-id="${CSS.escape(caseId)}"]`);
  const rect = card?.getBoundingClientRect();
  return rect && rect.width > 0 && rect.bottom > 0 && rect.top < window.innerHeight ? rect : null;
}

/** The transform that lays the popup over the card, for a grow-in or shrink-out. */
function overCard(dialog: HTMLElement, caseId: string): string | null {
  const from = cardRect(caseId);
  if (!from) return null;
  const to = dialog.getBoundingClientRect();
  const dx = from.left + from.width / 2 - (to.left + to.width / 2);
  const dy = from.top + from.height / 2 - (to.top + to.height / 2);
  return `translate(${dx}px, ${dy}px) scale(${from.width / to.width}, ${from.height / to.height})`;
}

const GROW = { duration: 420, easing: "cubic-bezier(0.2, 0.9, 0.25, 1.04)" };
const SHRINK = { duration: 260, easing: "cubic-bezier(0.4, 0, 0.8, 0.4)" };

/** The case's details in a popup that grows out of its card: in common, different, what happened, sources.
    X, Esc or a click outside shrinks it back into the card; the map keeps the case's strand behind it. */
function CaseDialog({ result, onClose }: { result: SimilarCase; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const closing = useRef(false);
  const c = result.case;
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  const close = useCallback(() => {
    const dialog = ref.current;
    if (!dialog || closing.current) return;
    closing.current = true;
    const target = reduceMotion() ? null : overCard(dialog, result.case_id);
    dialog.dataset.state = "closing";
    if (!target) {
      closeRef.current();
      return;
    }
    const anim = dialog.animate([{ transform: "none", opacity: 1 }, { transform: target, opacity: 0 }],
      { ...SHRINK, fill: "forwards" });
    // Close when the shrink ends, or shortly after in any case: a browser that pauses animations (a
    // background tab) must never leave the popup stuck open.
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      closeRef.current();
    };
    anim.onfinish = finish;
    window.setTimeout(finish, SHRINK.duration + 150);
  }, [result.case_id]);

  // Esc fires "cancel": stop the instant close so it can shrink back first.
  useEffect(() => {
    const dialog = ref.current;
    const cancel = (event: Event) => {
      event.preventDefault();
      close();
    };
    dialog?.addEventListener("cancel", cancel);
    return () => dialog?.removeEventListener("cancel", cancel);
  }, [close]);

  useEffect(() => {
    const dialog = ref.current;
    // No close() on cleanup: React re-runs this effect in development, and unmounting removes the dialog.
    if (!dialog || dialog.open) return;
    dialog.showModal();
    if (reduceMotion()) return;
    const from = overCard(dialog, result.case_id);
    dialog.animate(
      from ? [{ transform: from, opacity: 0.5 }, { transform: "none", opacity: 1 }]
        : [{ transform: "translateY(12px) scale(0.97)", opacity: 0 }, { transform: "none", opacity: 1 }],
      GROW,
    );
  }, [result.case_id]);

  return (
    <dialog ref={ref} className="fs-case-dialog" aria-labelledby="fs-case-dialog-title"
      onClick={(event) => event.target === ref.current && close()}
      style={{ "--fs-hz": `var(--fs-hz-${c.hazards[0]})` } as CSSProperties}>
      <header className="fs-case-dialog__head">
        <ScoreRing score={result.score} />
        <div className="fs-case__head">
          <h3 id="fs-case-dialog-title" className="fs-case__title">{c.title}</h3>
          <span className="fs-case__meta fs-num">{where(c)}</span>
        </div>
        <SeverityBadge level={c.severity} />
        <button type="button" className="fs-case-dialog__close" onClick={close} aria-label="Close">×</button>
      </header>
      <div className="fs-case__body">
        {result.matched_on.length > 0 && (
          <section>
            <h4>In common with this site</h4>
            <ul>{result.matched_on.map((m) => <li key={m}>{sentence(m)}</li>)}</ul>
          </section>
        )}
        {result.differs_on.length > 0 && (
          <section>
            <h4>Different from this site</h4>
            <ul>{result.differs_on.map((m) => <li key={m}>{sentence(m)}</li>)}</ul>
          </section>
        )}
        <section>
          <h4>What happened</h4>
          <p>{c.summary}</p>
          <p className="fs-quiet">{causeText(c.cause_status, c.cause_as_reported ?? null)}</p>
        </section>
        <section>
          <h4>Sources</h4>
          <div className="fs-case__sources">
            {c.sources.map((src) => <SourceLabel key={src.name} kind="case" name={src.name} url={src.url} date={src.date} />)}
          </div>
        </section>
        <p className="fs-quiet">{S.score}: {S.scoreHelp}</p>
      </div>
    </dialog>
  );
}

/** Similarity as a ring that fills to the score, the number inside: "similar", never a probability. */
function ScoreRing({ score }: { score: number }) {
  const r = 15;
  const { circumference, dash } = ringDash(score, r);
  const pct = Math.round(Math.min(1, Math.max(0, Number.isFinite(score) ? score : 0)) * 100);
  return (
    <span className="fs-ring" title={`${S.score} ${pct} out of 100. ${S.scoreHelp}`} role="img" aria-label={`${pct} similar`}>
      <svg viewBox="0 0 36 36" width="40" height="40" aria-hidden="true">
        <circle cx="18" cy="18" r={r} className="fs-ring__track" />
        <circle cx="18" cy="18" r={r} className="fs-ring__fill" strokeLinecap={dash > 0 ? "round" : "butt"} strokeDasharray={`${dash} ${circumference}`} transform="rotate(-90 18 18)" />
      </svg>
      <span className="fs-ring__num fs-num">{pct}</span>
    </span>
  );
}
