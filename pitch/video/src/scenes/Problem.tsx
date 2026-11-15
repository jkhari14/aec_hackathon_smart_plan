// The problem: the warnings are public but sit on the wrong building, everyone holds one slice, and the
// patterns repeat across the city. Calm and factual; every number names its source.
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";

import { C, PIXEL } from "../theme";
import { Counter, Eyebrow, HardCard, Headline, PixelLabel, Reveal, Slide, useSpring } from "../ui";

const B = 280;
const CC = 470;

function Beat({ from, to, children }: { from: number; to: number; children: React.ReactNode }) {
  const frame = useCurrentFrame();
  const o = Math.min(
    interpolate(frame, [from, from + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(frame, [to - 14, to], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  if (frame < from - 1 || frame > to + 1) return null;
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
}

function Records() {
  const frame = useCurrentFrame();
  const items = ["Adjacent property not protected", "Work continued after a stop-work order", "Excavation and SOE permits open"];
  const x = useSpring(150, 14);
  const months = interpolate(frame, [120, 160], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 120, top: 400, right: 120, display: "flex", alignItems: "center", gap: 50 }}>
      <HardCard delay={40} style={{ width: 700 }}>
        <PixelLabel>Construction site · record</PixelLabel>
        {items.map((t, i) => (
          <Reveal key={t} delay={62 + i * 14} x={-16} y={0}>
            <div style={{ fontSize: 32, marginTop: 16, display: "flex", gap: 16 }}>
              <span style={{ color: C.red, fontWeight: 700 }}>!</span>
              {t}
            </div>
          </Reveal>
        ))}
      </HardCard>
      <div style={{ width: 230, textAlign: "center" }}>
        <PixelLabel color={C.red} size={20} style={{ opacity: months }}>Months apart</PixelLabel>
        <div style={{ fontSize: 120, lineHeight: 1, color: C.red, fontWeight: 700, transform: `scale(${x})`, margin: "10px 0" }}>×</div>
        <PixelLabel color={C.red} size={20} style={{ opacity: x }}>Never linked</PixelLabel>
      </div>
      <HardCard delay={80} style={{ width: 700 }}>
        <PixelLabel>Old neighbor next door · record</PixelLabel>
        <Reveal delay={100}>
          <div style={{ fontSize: 32, marginTop: 16, color: C.muted, fontStyle: "italic" }}>Clean file. No alerts.</div>
        </Reveal>
        <Reveal delay={116}>
          <div style={{ fontSize: 32, marginTop: 16 }}>The risk is next door, in someone else’s record.</div>
        </Reveal>
      </HardCard>
    </div>
  );
}

const ROLES = ["Architect", "Engineer", "Geotech", "Contractor", "DOB", "Neighbors"];

function Slices() {
  const frame = useCurrentFrame();
  const local = frame - B;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 120, top: 120, width: 820 }}>
        <Eyebrow color={C.red} delay={B}>Why it matters</Eyebrow>
        <Headline delay={B + 4} size={76} style={{ marginTop: 16 }}
          lines={[["Everyone", "sees", "one", "slice."], [{ t: "No", color: C.red }, { t: "one", color: C.red }, { t: "sees", color: C.red }, { t: "the", color: C.red }, { t: "whole", color: C.red }, { t: "site.", color: C.red }]]} />
        <Reveal delay={B + 40}>
          <p style={{ fontSize: 34, lineHeight: 1.4, color: C.ink2, marginTop: 34 }}>
            Filings, complaints, violations and past cases live in separate datasets, on separate lots, read by different people at different times.
          </p>
        </Reveal>
      </div>
      <svg width={760} height={760} viewBox="-380 -380 760 760" style={{ position: "absolute", right: 110, top: 150 }}>
        {ROLES.map((r, i) => {
          const a0 = (i / ROLES.length) * Math.PI * 2 - Math.PI / 2;
          const a1 = ((i + 1) / ROLES.length) * Math.PI * 2 - Math.PI / 2;
          const p = interpolate(local, [10 + i * 6, 34 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const drift = 26 + 10 * Math.sin((local + i * 20) / 30);
          const mid = (a0 + a1) / 2;
          const dx = Math.cos(mid) * drift * p, dy = Math.sin(mid) * drift * p;
          const R = 250, r0 = 110, gap = 0.04;
          const pt = (rad: number, a: number) => `${rad * Math.cos(a)},${rad * Math.sin(a)}`;
          const d = `M${pt(r0, a0 + gap)} L${pt(R, a0 + gap)} A${R},${R} 0 0 1 ${pt(R, a1 - gap)} L${pt(r0, a1 - gap)} A${r0},${r0} 0 0 0 ${pt(r0, a0 + gap)} Z`;
          return (
            <g key={r} transform={`translate(${dx},${dy})`} opacity={p}>
              <path d={d} fill={i % 2 ? "#e4e1d8" : "#d6d2c6"} stroke={C.ink} strokeWidth={3} />
              <text x={Math.cos(mid) * 322} y={Math.sin(mid) * 322 + 8} textAnchor="middle" fontFamily={PIXEL} fontSize={19} letterSpacing="2" fill={C.ink}>
                {r.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
}

const FACTS = [
  { n: 16581, label: "structural complaints to DOB since 2024", src: "DOB Complaints Received · pulled Nov 14, 2026" },
  { n: 1495, label: "construction accidents and incidents since 2024", src: "DOB Construction-Related Incidents" },
  { n: 1187, label: "active excavation permits next to attached pre-1940 buildings", src: "4site watchlist · DOB NOW + PLUTO" },
  { n: 42, label: "past NYC cases, 2007–2026, with the same patterns repeating", src: "4site case library · cause as publicly reported" },
];

function Facts() {
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 120, top: 120 }}>
        <Eyebrow color={C.red} delay={CC}>The scale</Eyebrow>
        <Headline delay={CC + 4} size={76} style={{ marginTop: 16 }} lines={[["The", "patterns", "are", "public,"], ["and", "they", "repeat."]]} />
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, top: 470, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 36 }}>
        {FACTS.map((f, i) => (
          <HardCard key={f.label} delay={CC + 24 + i * 10} style={{ minHeight: 330, display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 86, fontWeight: 700, letterSpacing: "-0.04em", color: i === 2 ? C.blue : C.ink }}>
              <Counter to={f.n} delay={CC + 30 + i * 10} frames={45} />
            </div>
            <div style={{ fontSize: 28, lineHeight: 1.3, marginTop: 10, flex: 1 }}>{f.label}</div>
            <PixelLabel size={14} style={{ marginTop: 18, lineHeight: 1.5 }}>{f.src}</PixelLabel>
          </HardCard>
        ))}
      </div>
    </AbsoluteFill>
  );
}

export function Problem({ duration }: { duration: number }) {
  return (
    <Slide section="Problem" index={2} duration={duration}>
      <Beat from={0} to={B}>
        <div style={{ position: "absolute", left: 120, top: 110 }}>
          <Eyebrow color={C.red}>The problem</Eyebrow>
          <Headline delay={6} size={80} style={{ marginTop: 16 }}
            lines={[["The", "warnings", "are", "public."], ["They’re", "filed", "on", "the", { t: "wrong", color: C.red }, { t: "building.", color: C.red }]]} />
        </div>
        <Records />
      </Beat>
      <Beat from={B} to={CC}>
        <Slices />
      </Beat>
      <Beat from={CC} to={duration + 20}>
        <Facts />
      </Beat>
    </Slide>
  );
}
