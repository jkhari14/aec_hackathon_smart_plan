// The early-warnings panel: record sequences on the site and its touching lots that are worth a look,
// with every rule's check underneath so "couldn't check" never reads as "nothing found".
// Uses the PR 0 placeholder tokens; it moves onto Camilo's design system (web/src/design/) once that lands.
import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { EarlyWarning, Severity, WarningRuleCheck } from "../../contracts";
import { SEVERITY_LABELS } from "../../contracts";
import { evidence } from "./evidence";

type Props = {
  bbl: string;
  asOf?: string;
  onEvidence?: (recordId: string) => void;
};

type State =
  | { kind: "loading" }
  | { kind: "ready"; warnings: EarlyWarning[]; checks: WarningRuleCheck[]; sample: boolean };

const HAZARD_LABELS: Record<string, string> = {
  structural: "Structural",
  geotech: "Geotech",
  fire: "Fire",
  flood: "Flood",
  contamination: "Contamination",
  facade: "Facade",
  weather: "Weather",
  construction_safety: "Construction safety",
};

export function WarningsPanel({ bbl, asOf, onEvidence }: Props) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let live = true;
    setState({ kind: "loading" });
    Promise.all([api.warnings(bbl, asOf), api.warningChecks(bbl, asOf)]).then(([warnings, checks]) => {
      if (!live) return;
      setState({
        kind: "ready",
        warnings: warnings.data,
        checks: checks.data,
        sample: warnings.sample || checks.sample,
      });
    });
    return () => {
      live = false;
    };
  }, [bbl, asOf]);

  return (
    <section
      aria-labelledby="early-warnings-title"
      className="w-[26rem] max-w-full rounded-xl border border-line bg-panel/95 text-text shadow-2xl shadow-black/40 backdrop-blur"
    >
      <header className="flex items-start justify-between gap-3 border-b border-line px-5 pb-3 pt-4">
        <div>
          <h2 id="early-warnings-title" className="text-[15px] font-semibold tracking-tight">
            Early warnings
          </h2>
          <p className="mt-0.5 text-xs text-muted">Record sequences worth a look</p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {state.kind === "ready" && state.sample && (
            <span className="rounded bg-sample/15 px-2 py-0.5 text-[11px] font-medium text-sample">Sample data</span>
          )}
          <span
            className="rounded border border-line px-2 py-0.5 text-[11px] tabular-nums text-muted"
            title="Only records dated before this day are used"
          >
            {asOf ? `As of ${asOf}` : "All records pulled"}
          </span>
        </div>
      </header>

      {state.kind === "loading" ? <Skeleton /> : <Body {...state} onEvidence={onEvidence} />}

      <footer className="border-t border-line px-5 py-3 text-[11px] leading-relaxed text-muted">
        Prompts to look, not findings or predictions. Public records lag and are incomplete; this is not
        engineering advice.
      </footer>
    </section>
  );
}

function Body({
  warnings,
  checks,
  onEvidence,
}: {
  warnings: EarlyWarning[];
  checks: WarningRuleCheck[];
  onEvidence?: (recordId: string) => void;
}) {
  const failed = checks.filter((c) => c.status === "error");
  const byRule = new Map(checks.map((c) => [c.rule_id, c]));
  return (
    <div className="max-h-[60vh] overflow-y-auto px-3 py-3">
      {failed.length > 0 && (
        <p role="status" className="mx-2 mb-3 rounded-lg border border-sample/30 bg-sample/10 px-3 py-2 text-xs text-sample">
          {failed.length === 1 ? "1 rule" : `${failed.length} rules`} couldn't be fully checked. See below.
        </p>
      )}
      {warnings.length === 0 ? (
        <Empty checked={checks.filter((c) => c.status === "ok").length} />
      ) : (
        <ol className="space-y-2">
          {warnings.map((w) => (
            <li key={w.id}>
              <WarningCard warning={w} check={byRule.get(w.rule_id)} onEvidence={onEvidence} />
            </li>
          ))}
        </ol>
      )}
      <Checks checks={checks} />
    </div>
  );
}

function WarningCard({
  warning,
  check,
  onEvidence,
}: {
  warning: EarlyWarning;
  check?: WarningRuleCheck;
  onEvidence?: (recordId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <article className="group rounded-lg border border-transparent px-2 py-2.5 transition-colors duration-200 hover:border-line hover:bg-white/[0.02]">
      <div className="flex gap-3">
        <SeverityMark severity={warning.severity} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px] text-muted">
            <span className="font-medium text-text/80">{SEVERITY_LABELS[warning.severity]}</span>
            <span aria-hidden>·</span>
            <span>{HAZARD_LABELS[warning.hazard] ?? warning.hazard}</span>
            <span aria-hidden>·</span>
            <span className="tabular-nums" title="The day this sequence first showed in the records">
              since {warning.first_seen}
            </span>
          </div>
          <h3 className="mt-1 text-sm font-medium leading-snug">{warning.title}</h3>
          <p className={`mt-1 text-[13px] leading-relaxed text-text/75 ${open ? "" : "line-clamp-3"}`}>
            {warning.explanation}
          </p>
          <ul className="mt-2 flex flex-wrap gap-1.5" aria-label="Records behind this warning">
            {warning.evidence_record_ids.slice(0, open ? undefined : 4).map((ref) => (
              <li key={ref}>
                <EvidenceChip refId={ref} onEvidence={onEvidence} />
              </li>
            ))}
            {!open && warning.evidence_record_ids.length > 4 && (
              <li className="px-1 py-0.5 text-[11px] text-muted">+{warning.evidence_record_ids.length - 4} more</li>
            )}
          </ul>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="mt-2 text-[11px] font-medium text-muted underline-offset-2 hover:text-text hover:underline focus-visible:text-text focus-visible:outline-none"
          >
            {open ? "Show less" : "Why am I seeing this?"}
          </button>
          {open && check && (
            <div className="mt-2 rounded-md border border-line bg-night/60 px-3 py-2 text-[12px] leading-relaxed text-text/75">
              <p>
                <span className="text-text/90">Rule:</span> {check.title}.
              </p>
              <p className="mt-1">{check.detail}</p>
              <Sources sources={check.sources} />
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

// Severity is shown by size and ring, with its name in text beside it: color is never the only cue.
function SeverityMark({ severity }: { severity: Severity }) {
  const ring = ["h-2.5 w-2.5 border", "h-3 w-3 border-2", "h-3.5 w-3.5 border-[3px]", "h-4 w-4 border-4"][severity];
  const tone = severity === 0 ? "border-muted" : "border-amber-300/90";
  return (
    <span className="mt-1 flex h-4 w-4 shrink-0 items-center justify-center" aria-hidden>
      <span className={`rounded-full ${ring} ${tone}`} />
    </span>
  );
}

function EvidenceChip({ refId, onEvidence }: { refId: string; onEvidence?: (recordId: string) => void }) {
  const item = evidence(refId);
  const className =
    "inline-flex items-center rounded-md border border-line bg-night/50 px-1.5 py-0.5 text-[11px] tabular-nums text-text/80 transition-colors duration-150 hover:border-muted hover:text-text focus-visible:border-muted focus-visible:outline-none";
  if (onEvidence) {
    return (
      <button type="button" className={className} title={`Show on the map · ${item.source}`} onClick={() => onEvidence(refId)}>
        {item.label}
      </button>
    );
  }
  return item.url ? (
    <a className={className} href={item.url} target="_blank" rel="noreferrer" title={`Open the record · ${item.source}`}>
      {item.label}
    </a>
  ) : (
    <span className={className}>{item.label}</span>
  );
}

function Sources({ sources }: { sources: WarningRuleCheck["sources"] }) {
  if (sources.length === 0) return null;
  return (
    <p className="mt-1.5 text-[11px] text-muted">
      Sources:{" "}
      {sources.map((s, i) => (
        <span key={`${s.name}-${i}`}>
          {i > 0 && ", "}
          {s.url ? (
            <a href={s.url} target="_blank" rel="noreferrer" className="underline-offset-2 hover:text-text hover:underline">
              {s.name}
            </a>
          ) : (
            s.name
          )}
          {s.date && <span className="tabular-nums"> ({s.date})</span>}
        </span>
      ))}
    </p>
  );
}

const CHECK_MARK: Record<WarningRuleCheck["status"], { symbol: string; label: string; tone: string }> = {
  ok: { symbol: "✓", label: "Checked", tone: "text-muted" },
  error: { symbol: "!", label: "Couldn't fully check", tone: "text-sample" },
  not_applicable: { symbol: "–", label: "Doesn't apply", tone: "text-muted/70" },
};

function Checks({ checks }: { checks: WarningRuleCheck[] }) {
  const [open, setOpen] = useState<string | null>(null);
  return (
    <details className="group/checks mt-3 rounded-lg px-2" open={checks.some((c) => c.status === "error")}>
      <summary className="flex cursor-pointer list-none items-center gap-1.5 py-1.5 text-[11px] font-medium uppercase tracking-wider text-muted hover:text-text [&::-webkit-details-marker]:hidden">
        <span aria-hidden className="inline-block transition-transform duration-150 group-open/checks:rotate-90">
          ›
        </span>
        Rules checked · {checks.length}
      </summary>
      <ul className="space-y-1 pb-1">
        {checks.map((c) => {
          const mark = CHECK_MARK[c.status];
          const expanded = open === c.rule_id;
          return (
            <li key={c.rule_id}>
              <button
                type="button"
                onClick={() => setOpen(expanded ? null : c.rule_id)}
                aria-expanded={expanded}
                className="flex w-full items-start gap-2 rounded px-1 py-1 text-left text-xs hover:bg-white/[0.03] focus-visible:bg-white/[0.04] focus-visible:outline-none"
              >
                <span className={`w-3 shrink-0 text-center font-semibold ${mark.tone}`} aria-label={mark.label}>
                  {mark.symbol}
                </span>
                <span className="flex-1 text-text/80">{c.title}</span>
                <span className="shrink-0 tabular-nums text-muted">
                  {c.status === "ok" ? (c.warnings === 1 ? "1 warning" : `${c.warnings} warnings`) : mark.label}
                </span>
              </button>
              {expanded && (
                <div className="ml-6 mr-1 pb-1.5 text-[12px] leading-relaxed text-text/70">
                  <p>{c.detail}</p>
                  <Sources sources={c.sources} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

function Empty({ checked }: { checked: number }) {
  return (
    <div className="mx-2 rounded-lg border border-dashed border-line px-4 py-5 text-center">
      <p className="text-sm text-text/85">No warning sequences in the records checked</p>
      <p className="mt-1 text-xs text-muted">
        {checked} {checked === 1 ? "rule" : "rules"} ran cleanly. That is not an all-clear: the records are public
        and incomplete.
      </p>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-4 px-5 py-4" aria-busy="true" aria-label="Loading early warnings">
      {[0, 1].map((i) => (
        <div key={i} className="flex gap-3">
          <span className="mt-1 h-3 w-3 rounded-full bg-line motion-safe:animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-2.5 w-1/3 rounded bg-line motion-safe:animate-pulse" />
            <div className="h-3.5 w-4/5 rounded bg-line motion-safe:animate-pulse" />
            <div className="h-2.5 w-full rounded bg-line/70 motion-safe:animate-pulse" />
            <div className="h-2.5 w-2/3 rounded bg-line/70 motion-safe:animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}
