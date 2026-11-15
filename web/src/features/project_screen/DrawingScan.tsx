// The loading state while a drawing is read (10 to 30 s): a sheet arrives, a scan line inks it in, it tilts
// and its walls rise, walls on the lot line in the accent colour. The plan drawn here is an illustration,
// labelled as one; the facts beside it appear only once the real reading is back.
import "./drawing_scan.css";

import { useEffect, useRef, useState, type CSSProperties } from "react";

export type ScanPhase = "reading" | "read" | "ingested";
export type ScanFact = { label: string; party?: boolean };

type Box = { x: number; y: number; w: number; h: number; to: number; party?: boolean };

// Plan pixels on a 600 x 420 sheet. The two lot-line walls are the party walls.
const WALLS: Box[] = [
  { x: 56, y: 70, w: 10, h: 260, to: 78, party: true },
  { x: 494, y: 70, w: 10, h: 260, to: 78, party: true },
  { x: 66, y: 66, w: 428, h: 8, to: 78 },
  { x: 66, y: 326, w: 140, h: 8, to: 78 },
  { x: 250, y: 326, w: 244, h: 8, to: 78 },
  { x: 276, y: 74, w: 6, h: 70, to: 70 },
  { x: 276, y: 180, w: 6, h: 146, to: 70 },
  { x: 66, y: 206, w: 134, h: 6, to: 70 },
  { x: 230, y: 206, w: 46, h: 6, to: 70 },
  { x: 282, y: 236, w: 110, h: 6, to: 70 },
];
const NEIGHBOURS: Box[] = [
  { x: -150, y: 70, w: 136, h: 260, to: 110 },
  { x: 514, y: 90, w: 120, h: 220, to: 60 },
];

const STEPS = ["Reading the sheets…", "Finding walls on the lot line…", "Classifying the structural system…",
  "Checking the foundation notes…"];

const reducedMotion = () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function Mass({ box, kind }: { box: Box; kind: "wall" | "ghost" }) {
  const style = { left: box.x, top: box.y, width: box.w, height: box.h, "--to": `${box.to}px` } as CSSProperties;
  return (
    <div className={`fs-scan__${kind}`} data-party={box.party || undefined} style={style}>
      <div className="fs-scan__cap" />
      <div className="fs-scan__s" />
      <div className="fs-scan__w" />
    </div>
  );
}

type Props = { phase: ScanPhase; document: string; facts: ScanFact[]; source?: string };

export function DrawingScan({ phase, document, facts, source }: Props) {
  // 0 nothing, 1 sheet in, 2 scanning, 3 tilted and built.
  const [stage, setStage] = useState(() => (phase !== "reading" || reducedMotion() ? 3 : 0));
  const [step, setStep] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const fit = useFit();

  useEffect(() => {
    if (stage === 3) return;
    const timers = [
      window.setTimeout(() => setStage(1), 100),
      window.setTimeout(() => setStage(2), 1200),
      // Drop the clip before tilting: clip-path flattens 3D.
      window.setTimeout(() => setStage(3), 2450),
    ];
    return () => timers.forEach(window.clearTimeout);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (phase !== "reading") {
      setStage(3);
      return;
    }
    const tick = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    const words = window.setInterval(() => setStep((s) => (s + 1) % STEPS.length), 4000);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(words);
    };
  }, [phase]);

  const caption = phase === "reading" ? (stage < 2 ? `Drawing received: ${document}` : stage === 2 ? "Scanning the drawing…" : STEPS[step])
    : phase === "read" ? "Read: check it below" : "Confirmed: checklist updated";

  return (
    <div className="fs-scan" data-phase={phase} aria-busy={phase === "reading"}>
      <div className="fs-scan__caption">
        <span className="fs-ps__eyebrow">Documents · Structural drawings</span>
        <strong className="fs-scan__doc">{document}</strong>
        <span className="fs-scan__step" role="status" aria-live="polite">
          {caption}
          {phase === "reading" && stage === 3 && <span className="fs-num fs-quiet"> · {seconds} s, usually 10 to 30</span>}
        </span>
      </div>
      <span className="fs-scan__tag" title="This plan is a drawing of the idea, not your sheet">Illustration</span>

      <div className="fs-scan__stage" ref={fit.outer} style={{ height: 420 * fit.k + 40 }}>
        <div className="fs-scan__fit" style={{ transform: `scale(${fit.k})` }}>
          <div className="fs-scan__sheet" data-in={stage >= 1} data-iso={stage >= 3} data-live={phase === "reading" && stage >= 3}>
            <div className="fs-scan__reveal" data-scanning={stage === 2}>
              {NEIGHBOURS.map((b, i) => <Mass key={`n${i}`} box={b} kind="ghost" />)}
              <div className="fs-scan__floor" style={{ left: 60, top: 70, width: 440, height: 260 }} />
              <PlanLines />
              {WALLS.map((b, i) => <Mass key={`w${i}`} box={b} kind="wall" />)}
              <div className="fs-scan__glow" data-go={stage === 2} />
            </div>
            <div className="fs-scan__line" data-go={stage === 2} />
          </div>
        </div>
      </div>

      <div className="fs-scan__ingest">
        <div className="fs-scan__stamp" data-on={phase !== "reading"}>{phase === "ingested" ? "Ingested" : "Read"}</div>
        <div className="fs-scan__facts">
          {phase !== "reading" && facts.map((f, i) => (
            <span key={f.label} className="fs-scan__fact" style={{ animationDelay: `${200 + i * 140}ms` }}>
              <span className="fs-scan__dot" data-party={f.party || undefined} />
              {f.label}
            </span>
          ))}
        </div>
        {phase !== "reading" && source && <span className="fs-scan__src">{source}</span>}
      </div>
    </div>
  );
}

function PlanLines() {
  return (
    <svg viewBox="0 0 600 420" width="600" height="420" aria-hidden="true" className="fs-scan__svg">
      <g className="fs-scan__annot" fill="none" strokeWidth="1">
        <g strokeDasharray="6 4">
          <line x1="60" y1="40" x2="60" y2="360" /><line x1="280" y1="40" x2="280" y2="360" /><line x1="500" y1="40" x2="500" y2="360" />
          <line x1="30" y1="70" x2="530" y2="70" /><line x1="30" y1="330" x2="530" y2="330" />
        </g>
        <circle cx="60" cy="28" r="10" /><circle cx="280" cy="28" r="10" /><circle cx="500" cy="28" r="10" />
        <circle cx="18" cy="70" r="10" /><circle cx="18" cy="330" r="10" />
        <line x1="60" y1="372" x2="500" y2="372" />
        <line x1="60" y1="366" x2="60" y2="378" /><line x1="280" y1="366" x2="280" y2="378" /><line x1="500" y1="366" x2="500" y2="378" />
        <path d="M200 210 A 30 30 0 0 1 230 240" /><path d="M360 150 A 26 26 0 0 0 386 176" />
        <rect x="420" y="250" width="70" height="70" />
        {[262, 274, 286, 298, 310].map((y) => <line key={y} x1="420" y1={y} x2="490" y2={y} />)}
        <rect x="420" y="384" width="170" height="30" />
      </g>
      <g className="fs-scan__text">
        <text x="56" y="32">A</text><text x="276" y="32">B</text><text x="496" y="32">C</text>
        <text x="15" y="74">1</text><text x="15" y="334">2</text>
        <text x="64" y="64" className="fs-scan__party-label">LOT LINE</text>
        <text x="428" y="398" className="fs-scan__title">ILLUSTRATION</text>
        <text x="428" y="409">Not your drawing</text>
      </g>
    </svg>
  );
}

/** Scale the fixed 600 px sheet down to the width it has (phones). */
function useFit() {
  const outer = useRef<HTMLDivElement>(null);
  const [k, setK] = useState(1);
  useEffect(() => {
    const el = outer.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setK(Math.min(1, entry.contentRect.width / 640)));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return { outer, k };
}
