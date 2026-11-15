// ForeSite core components. Every screen builds from these so the app reads as one system.
// Styles live in components.css; tokens in tokens.css.
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";

import type { Hazard, Severity } from "../contracts";
import { SEVERITY_LABELS } from "../contracts";
import { HAZARD_LABELS } from "./hazards";
import { AlertIcon, CloseIcon, InfoIcon } from "./icons";

const hazardVar = (hazard?: Hazard) => (hazard ? ({ "--fs-hz": `var(--fs-hz-${hazard})` } as CSSProperties) : undefined);

// ---- Panel ---------------------------------------------------------------------------------------

type PanelProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  onClose?: () => void;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  open?: boolean;
  edge?: "left" | "right" | "bottom";
  label?: string;
};

export function Panel({ title, subtitle, actions, onClose, children, className, style, open = true, edge = "left", label }: PanelProps) {
  return (
    <section
      className={`fs-panel fs-slide ${className ?? ""}`}
      style={style}
      data-open={open}
      data-edge={edge}
      aria-label={label}
      aria-hidden={!open}
      inert={!open}
    >
      <header className="fs-panel__head">
        <h2 className="fs-panel__title">
          {title}
          {subtitle && <span className="fs-panel__sub">{subtitle}</span>}
        </h2>
        {actions}
        {onClose && (
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close panel">
            <CloseIcon />
          </Button>
        )}
      </header>
      <div className="fs-panel__body">{children}</div>
    </section>
  );
}

// ---- Card ----------------------------------------------------------------------------------------

type CardProps = {
  title?: ReactNode;
  meta?: ReactNode;
  hazard?: Hazard;
  onClick?: () => void;
  children?: ReactNode;
};

export function Card({ title, meta, hazard, onClick, children }: CardProps) {
  const interactive = Boolean(onClick);
  return (
    <article
      className="fs-card"
      data-hazard={hazard}
      data-interactive={interactive}
      style={hazardVar(hazard)}
      onClick={onClick}
      onKeyDown={interactive ? (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onClick?.()) : undefined}
      tabIndex={interactive ? 0 : undefined}
      role={interactive ? "button" : undefined}
    >
      {title && <h3 className="fs-card__title">{title}</h3>}
      {children}
      {meta && <div className="fs-card__meta">{meta}</div>}
    </article>
  );
}

// ---- Chip ----------------------------------------------------------------------------------------

type ChipProps = {
  children: ReactNode;
  pressed?: boolean;
  hazard?: Hazard;
  onClick?: () => void;
};

export function Chip({ children, pressed, hazard, onClick }: ChipProps) {
  return (
    <button type="button" className="fs-chip" aria-pressed={pressed} style={hazardVar(hazard)} onClick={onClick}>
      {hazard && <span className="fs-chip__dot" aria-hidden="true" />}
      {pressed && <span aria-hidden="true">✓</span>}
      {children}
    </button>
  );
}

export function HazardChip({ hazard, pressed, onClick }: { hazard: Hazard; pressed?: boolean; onClick?: () => void }) {
  return (
    <Chip hazard={hazard} pressed={pressed} onClick={onClick}>
      {HAZARD_LABELS[hazard]}
    </Chip>
  );
}

// ---- Source label --------------------------------------------------------------------------------

export type SourceKind = "record" | "ai" | "user";
const KIND_TEXT: Record<SourceKind, string> = { record: "Public record", ai: "AI suggestion", user: "User input" };

type SourceLabelProps = {
  kind?: SourceKind;
  name?: string;
  url?: string | null;
  date?: string | null;
};

/** Who says so and when. A missing date reads "date unknown", never blank. */
export function SourceLabel({ kind = "record", name, url, date }: SourceLabelProps) {
  const when = date ? formatDate(date) : "date unknown";
  return (
    <span className="fs-src" data-kind={kind} title={`${KIND_TEXT[kind]}${name ? `: ${name}` : ""}, ${when}`}>
      <span className="fs-src__kind">{KIND_TEXT[kind]}</span>
      {name &&
        (url ? (
          <a href={url} target="_blank" rel="noreferrer">
            {name}
          </a>
        ) : (
          <span>{name}</span>
        ))}
      <span className="fs-num">· {when}</span>
    </span>
  );
}

// ---- Badge and severity --------------------------------------------------------------------------

type BadgeProps = { children: ReactNode; tone?: "neutral" | "sample" | "error" | "accent" | "safety"; title?: string };

export function Badge({ children, tone = "neutral", title }: BadgeProps) {
  return (
    <span className="fs-badge" data-tone={tone} title={title}>
      {children}
    </span>
  );
}

export function SampleBadge() {
  return (
    <Badge tone="sample" title="The API is not answering, so this screen shows fixture data from contracts/fixtures.">
      Sample data
    </Badge>
  );
}

export function SeverityMark({ level }: { level: Severity }) {
  return (
    <span
      className="fs-sev"
      data-level={level}
      style={{ "--fs-sev": `var(--fs-sev-${level})` } as CSSProperties}
      role="img"
      aria-label={`Severity: ${SEVERITY_LABELS[level]}`}
      title={SEVERITY_LABELS[level]}
    />
  );
}

export function SeverityBadge({ level }: { level: Severity }) {
  return (
    <Badge>
      <SeverityMark level={level} />
      {SEVERITY_LABELS[level]}
    </Badge>
  );
}

/** A count that may be unknown or capped. A failed query is "couldn't load", never zero. */
export function Count({ value, status = "ok" }: { value?: number | null; status?: "ok" | "error" | "capped" }) {
  if (status === "error") return <Badge tone="error">Couldn't load</Badge>;
  if (value == null) return <span className="fs-num" style={{ color: "var(--fs-muted)" }}>count unknown</span>;
  return (
    <span className="fs-num">
      {status === "capped" ? "at least " : ""}
      {value.toLocaleString("en-US")}
    </span>
  );
}

// ---- Skeleton, empty and error -------------------------------------------------------------------

export function Skeleton({ width = "100%", height = 12, style }: { width?: number | string; height?: number; style?: CSSProperties }) {
  return <span className="fs-skel" style={{ width, height, ...style }} aria-hidden="true" />;
}

export function SkeletonCard({ lines = 2 }: { lines?: number }) {
  return (
    <div className="fs-card" aria-busy="true" aria-label="Loading">
      <Skeleton width="60%" height={14} />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} width={i === lines - 1 ? "40%" : "100%"} />
      ))}
    </div>
  );
}

type StateProps = { title: ReactNode; children?: ReactNode; action?: ReactNode };

export function EmptyState({ title, children, action }: StateProps) {
  return (
    <div className="fs-state">
      <p className="fs-state__title">
        <InfoIcon width={16} height={16} />
        {title}
      </p>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ title = "Couldn't load", children, action }: Partial<StateProps>) {
  return (
    <div className="fs-state" data-tone="error" role="status">
      <p className="fs-state__title">
        <AlertIcon width={16} height={16} />
        {title}
      </p>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

// ---- Button, toggle, tabs, kbd -------------------------------------------------------------------

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "ghost";
  size?: "default" | "icon";
};

export function Button({ variant = "default", size = "default", type = "button", ...props }: ButtonProps) {
  return <button type={type} className="fs-btn" data-variant={variant} data-size={size} {...props} />;
}

type ToggleProps = { checked: boolean; onChange: (next: boolean) => void; label: ReactNode; hint?: ReactNode; trailing?: ReactNode };

export function Toggle({ checked, onChange, label, hint, trailing }: ToggleProps) {
  return (
    <button type="button" role="switch" aria-checked={checked} className="fs-toggle" onClick={() => onChange(!checked)}>
      <span className="fs-toggle__track" aria-hidden="true" />
      <span className="fs-toggle__label">
        <span>{label}</span>
        {hint && <span style={{ fontSize: "var(--fs-text-xs)", color: "var(--fs-muted)" }}>{hint}</span>}
      </span>
      {trailing}
    </button>
  );
}

type TabsProps<T extends string> = { value: T; onChange: (v: T) => void; options: { value: T; label: ReactNode }[]; label: string };

export function Tabs<T extends string>({ value, onChange, options, label }: TabsProps<T>) {
  return (
    <div className="fs-tabs" role="tablist" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} type="button" role="tab" className="fs-tab" aria-selected={o.value === value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return <kbd className="fs-kbd">{children}</kbd>;
}

// ---- Explain -------------------------------------------------------------------------------------

/** "Why am I seeing this?" A quiet disclosure every item carries, so no element goes unexplained. */
export function Explain({ children, label = "Why am I seeing this?" }: { children: ReactNode; label?: string }) {
  return (
    <details className="fs-explain" onClick={(e) => e.stopPropagation()}>
      <summary>{label}</summary>
      <div className="fs-explain__body">{children}</div>
    </details>
  );
}

/** "support_of_excavation" -> "support of excavation" */
export const humanize = (key: string) => key.replace(/_/g, " ");

// ---- Format --------------------------------------------------------------------------------------

/** 2026-11-14 -> "Nov 14, 2026". Dates are always shown with the year. */
export function formatDate(iso: string) {
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}
