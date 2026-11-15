// Top signals: the three that matter most (highest severity, life safety first), the rest one click away.
import { useState } from "react";

import type { DatasetStatus, Signal } from "../../contracts";
import { copy } from "../../copy";
import { SEVERITY_LABELS } from "../../contracts";
import { readRecordQuote, recordNumber } from "./record_text";
import { bySignalPriority, Button, Card, EmptyState, Explain, HAZARD_LABELS, SeverityMark, SourceLabel } from "../../design";

const TOP = 3;

export function Signals({ signals, datasets }: { signals: Signal[]; datasets: DatasetStatus[] }) {
  const [all, setAll] = useState(false);
  const sorted = [...signals].sort(bySignalPriority);
  const shown = all ? sorted : sorted.slice(0, TOP);
  const failed = datasets.filter((d) => d.status === "error");

  if (sorted.length === 0) {
    return (
      <EmptyState title={copy.sitePanel.noSignals}>
        {failed.length > 0
          ? `${failed.length} source${failed.length > 1 ? "s" : ""} couldn't load, so this may be incomplete.`
          : copy.limitations.points[1]}
      </EmptyState>
    );
  }

  return (
    <div className="fs-signals">
      {shown.map((s) => (
        <SignalCard key={s.id} signal={s} sourceUrl={datasets.find((d) => d.name === s.source_name)?.source_url} />
      ))}
      {sorted.length > TOP && (
        <Button variant="ghost" onClick={() => setAll((a) => !a)}>
          {all ? "Show the top 3 only" : `Show all ${sorted.length} signals`}
        </Button>
      )}
    </div>
  );
}

function SignalCard({ signal, sourceUrl }: { signal: Signal; sourceUrl?: string | null }) {
  return (
    <Card
      hazard={signal.hazard}
      title={
        <span className="fs-signal__title">
          <SeverityMark level={signal.severity} />
          {signal.title}
        </span>
      }
      meta={<SourceLabel name={signal.source_name} url={sourceUrl} date={signal.date} />}
    >
      <span className="fs-signal__tags">
        {HAZARD_LABELS[signal.hazard]} · {SEVERITY_LABELS[signal.severity]}
      </span>
      <Explain>
        <SignalWhy signal={signal} />
      </Explain>
    </Card>
  );
}

/** The record in a few short lines: what it says, any code it cites, which record, and how to read it. */
function SignalWhy({ signal }: { signal: Signal }) {
  const quote = readRecordQuote(signal.explanation);
  const parts = quote ? null : signal.explanation.split(/;\s+|\.\s+(?=[A-Z])/).filter(Boolean);
  return (
    <div className="fs-why">
      <p className="fs-why__label">What the record says</p>
      <ul className="fs-why__list">
        {(quote ? quote.lines : parts ?? []).map((line, i) => (
          <li key={i}>{line.replace(/\.$/, "")}</li>
        ))}
      </ul>
      {quote && quote.codes.length > 0 && (
        <p className="fs-why__row"><span>Code cited</span>{quote.codes.join(", ")}</p>
      )}
      <p className="fs-why__row">
        <span>Record</span>
        <span className="fs-num">{signal.source_name} #{signal.record_ids.map(recordNumber).join(", #")}</span>
      </p>
      {quote && (
        <details className="fs-why__original">
          <summary>Original text</summary>
          <p>{signal.explanation}</p>
        </details>
      )}
      <p className="fs-why__note">This is what the record says, not a finding. The top 3 are ranked by severity, life safety first.</p>
    </div>
  );
}
