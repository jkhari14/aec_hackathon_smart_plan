// Similar cases: past events on sites with a similar profile. Each card says what matches and what
// differs; causes appear only as publicly reported or under investigation. No blame, no "would have
// prevented". Filters narrow by hazard, severity and date.
import "./similar_cases.css";

import { useMemo, useState } from "react";

import type { Hazard, Severity, SimilarCase } from "../../contracts";
import { SEVERITY_LABELS } from "../../contracts";
import { causeText, copy } from "../../copy";
import { Card, Chip, EmptyState, Explain, formatDate, HAZARD_LABELS, humanize, SeverityBadge, SourceLabel } from "../../design";

type Since = "all" | "2020" | "2015";
const SINCE: { value: Since; label: string }[] = [
  { value: "all", label: "Any date" },
  { value: "2015", label: "Since 2015" },
  { value: "2020", label: "Since 2020" },
];

const S = copy.similarCases;

export function SimilarCases({ results }: { results: SimilarCase[] }) {
  const [hazards, setHazards] = useState<Set<Hazard>>(new Set());
  const [severities, setSeverities] = useState<Set<Severity>>(new Set());
  const [since, setSince] = useState<Since>("all");

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
        <CaseCard key={r.case_id} result={r} />
      ))}
    </div>
  );
}

function CaseCard({ result }: { result: SimilarCase }) {
  const c = result.case;
  const primary = c.hazards[0];
  return (
    <Card
      hazard={primary}
      title={c.title}
      meta={c.sources.map((s) => <SourceLabel key={s.name} kind="case" name={s.name} url={s.url} date={s.date} />)}
    >
      <div className="fs-case__line fs-num">
        <span>{c.address}</span>
        <span>· {c.date.length === 10 ? formatDate(c.date) : c.date}</span>
        <SeverityBadge level={c.severity} />
      </div>
      <div className="fs-case__match">
        <MatchMeter score={result.score} />
        <ul className="fs-case__list" aria-label={`${S.matchesOn} and ${S.differsOn.toLowerCase()}`}>
          {result.matched_on.map((m) => (
            <li key={m} data-kind="match" title={S.matchesOn}>{m}</li>
          ))}
          {result.differs_on.map((m) => (
            <li key={m} data-kind="differ" title={S.differsOn}>{m}</li>
          ))}
        </ul>
      </div>
      <Explain label="What happened">
        <p>{c.summary}</p>
        <p>{causeText(c.cause_status, c.cause_as_reported ?? null)}</p>
        {c.work_types.length > 0 && <p className="fs-quiet">Work on site: {c.work_types.map(humanize).join(", ")}.</p>}
        <p className="fs-quiet">
          {S.score}: {S.scoreHelp}
        </p>
      </Explain>
    </Card>
  );
}

/** Similarity as a short bar plus the number, so it never reads as a probability of failure. */
function MatchMeter({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <span className="fs-meter" title={`${S.score} ${pct} out of 100. ${S.scoreHelp}`}>
      <span className="fs-meter__bar" aria-hidden="true">
        <span style={{ width: `${pct}%` }} />
      </span>
      <span className="fs-num">{pct}</span>
      <span className="fs-meter__label">similar</span>
    </span>
  );
}
