// The loading state while a geotechnical report is read: a site section where three borings drill down
// through the soil. The section is an illustration, labelled as one; once the real reading is back, the
// water table and rock (if any) are drawn at the depths the report states, and the facts appear beside it.
import "./drawing_scan.css";

import { useEffect, useState } from "react";

import type { GeotechFindings } from "../project/project_client";
import type { ScanFact, ScanPhase } from "./DrawingScan";

const TOP = 110; // ground line
const PX_PER_FT = 6.5;
const MAX_FT = 40;
const y = (ft: number) => TOP + Math.min(ft, MAX_FT) * PX_PER_FT;
const BORINGS = [170, 300, 430];
const STEPS = ["Reading the boring logs…", "Finding the water table…", "Reading the soil layers…",
  "Checking the bearing recommendation…"];

type Props = { phase: ScanPhase; document: string; facts: ScanFact[]; findings: GeotechFindings | null; source?: string };

export function BoringScan({ phase, document, facts, findings, source }: Props) {
  const [step, setStep] = useState(0);
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (phase !== "reading") return;
    const tick = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    const words = window.setInterval(() => setStep((s) => (s + 1) % STEPS.length), 4000);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(words);
    };
  }, [phase]);

  const water = findings?.groundwater_depth_ft ?? null;
  const rock = findings?.rock_depth_ft ?? null;
  const caption = phase === "reading" ? (seconds < 2 ? `Report received: ${document}` : STEPS[step])
    : phase === "read" ? "Read: check it below" : "Confirmed: checklist updated";

  return (
    <div className="fs-scan fs-bore" data-phase={phase} aria-busy={phase === "reading"}>
      <div className="fs-scan__caption">
        <span className="fs-ps__eyebrow">Documents · Geotechnical report</span>
        <strong className="fs-scan__doc">{document}</strong>
        <span className="fs-scan__step" role="status" aria-live="polite">
          {caption}
          {phase === "reading" && seconds >= 2 && <span className="fs-num fs-quiet"> · {seconds} s, usually 10 to 30</span>}
        </span>
      </div>
      <span className="fs-scan__tag" title="This section is a drawing of the idea, not your site">Illustration</span>

      <svg className="fs-bore__svg" viewBox="0 0 600 400" role="img"
        aria-label={water !== null ? `Section with groundwater at ${water} feet` : "Illustrated site section with borings"}>
        <defs>
          <pattern id="fs-bore-fill" width="10" height="10" patternUnits="userSpaceOnUse">
            <circle cx="3" cy="3" r="1.3" className="fs-bore__grain" />
            <circle cx="8" cy="7" r="0.9" className="fs-bore__grain" />
          </pattern>
          <pattern id="fs-bore-sand" width="8" height="8" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="0.7" className="fs-bore__grain" />
            <circle cx="6" cy="5" r="0.6" className="fs-bore__grain" />
          </pattern>
          <pattern id="fs-bore-rock" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="12" className="fs-bore__rockline" />
          </pattern>
        </defs>

        {/* Soil layers (illustration) */}
        <rect x="40" y={y(0)} width="540" height={6 * PX_PER_FT} className="fs-bore__layer fs-bore__layer--fill" />
        <rect x="40" y={y(0)} width="540" height={6 * PX_PER_FT} fill="url(#fs-bore-fill)" />
        <rect x="40" y={y(6)} width="540" height={22 * PX_PER_FT} className="fs-bore__layer fs-bore__layer--sand" />
        <rect x="40" y={y(6)} width="540" height={22 * PX_PER_FT} fill="url(#fs-bore-sand)" />
        <rect x="40" y={y(28)} width="540" height={12 * PX_PER_FT} className="fs-bore__layer fs-bore__layer--silt" />

        {/* Buildings: this one and its neighbours, with the cellar below grade */}
        <rect x="70" y="40" width="120" height="70" className="fs-bore__ghost" />
        <rect x="410" y="20" width="140" height="90" className="fs-bore__ghost" />
        <rect x="190" y="30" width="220" height="80" className="fs-bore__house" />
        <rect x="190" y={y(0)} width="220" height={9.5 * PX_PER_FT} className="fs-bore__cellar" />
        <line x1="40" y1={TOP} x2="580" y2={TOP} className="fs-bore__ground" />

        {/* Depth scale */}
        {[0, 10, 20, 30, 40].map((ft) => (
          <g key={ft}>
            <line x1="34" y1={y(ft)} x2="40" y2={y(ft)} className="fs-bore__tick" />
            <text x="30" y={y(ft) + 3} textAnchor="end" className="fs-bore__label">{ft}'</text>
          </g>
        ))}

        {/* Water table and rock, at the depths the report states */}
        {phase !== "reading" && water !== null && water <= MAX_FT && (
          <g className="fs-bore__water">
            <rect x="40" y={y(water)} width="540" height={y(MAX_FT) - y(water)} className="fs-bore__wet" />
            <line x1="40" y1={y(water)} x2="580" y2={y(water)} className="fs-bore__waterline" />
            <path d={`M 520 ${y(water) - 12} l 8 10 l 8 -10 z`} className="fs-bore__tri" />
            <text x="512" y={y(water) - 4} textAnchor="end" className="fs-bore__wlabel">GROUNDWATER {water}'</text>
          </g>
        )}
        {phase !== "reading" && rock !== null && rock <= MAX_FT && (
          <g className="fs-bore__rock">
            <rect x="40" y={y(rock)} width="540" height={y(MAX_FT) - y(rock)} fill="url(#fs-bore-rock)" />
            <text x="574" y={y(rock) + 12} textAnchor="end" className="fs-bore__label">ROCK {rock}'</text>
          </g>
        )}

        {/* Borings drilling down */}
        {BORINGS.map((x, i) => (
          <g key={x} className="fs-bore__boring" style={{ animationDelay: `${i * 0.9}s` }}>
            <path d={`M ${x - 7} ${TOP - 2} l 7 -22 l 7 22`} className="fs-bore__rig" />
            <text x={x} y={TOP - 28} textAnchor="middle" className="fs-bore__label">B-{i + 1}</text>
            <line x1={x} y1={TOP} x2={x} y2={y(MAX_FT)} className="fs-bore__hole" style={{ animationDelay: `${i * 0.9}s` }} />
            {[5, 12, 19, 26, 33].map((ft, k) => (
              <rect key={ft} x={x - 4} y={y(ft) - 3} width="8" height="6" className="fs-bore__sample"
                style={{ animationDelay: `${i * 0.9 + 0.4 + k * 0.32}s` }} />
            ))}
          </g>
        ))}

        <text x="300" y="392" textAnchor="middle" className="fs-bore__label">ILLUSTRATION · NOT YOUR SITE</text>
      </svg>

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
