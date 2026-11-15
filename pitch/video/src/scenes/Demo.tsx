// The product demo: the Playwright take of the real app, full screen, cut into segments, sped up, and zoomed
// toward whatever the user is reading. Times are seconds in the source recording (public/demo/markers.json).
import { AbsoluteFill, Easing, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame } from "remotion";

import { C, FPS, H, PIXEL, W } from "../theme";
import { Eyebrow, Headline, Reveal, Slide } from "../ui";

type Key = { t: number; z: number; x: number; y: number };
type Segment = { from: number; to: number; speed: number; keys: Key[]; chip?: string };

const PANEL = { x: 1640, y: 470 };
const wide = (t: number): Key => ({ t, z: 1, x: W / 2, y: H / 2 });
const panel = (t: number, z = 1.45, y = PANEL.y): Key => ({ t, z, x: PANEL.x, y });

export const SEGMENTS: Segment[] = [
  { from: 1.0, to: 12.5, speed: 2.2, chip: "01 · Pick a site", keys: [wide(1), wide(3.6), { t: 5, z: 1.3, x: 640, y: 380 }, { t: 12.5, z: 1.3, x: 640, y: 380 }] },
  { from: 18.4, to: 28.5, speed: 1.4, keys: [wide(18.4), { t: 19.3, z: 1.7, x: 480, y: 220 }, { t: 22.6, z: 1.7, x: 480, y: 220 }, wide(24.2), wide(28.5)] },
  { from: 28.5, to: 48.2, speed: 1.5, chip: "02 · See the public record", keys: [wide(28.5), panel(30), panel(38.5, 1.45, 520), panel(41, 1.45, 560), panel(48.2, 1.45, 560)] },
  { from: 48.2, to: 72.8, speed: 1.5, chip: "03 · Compare similar cases", keys: [panel(48.2), panel(53.2, 1.4, 640), wide(54.6), wide(59.8), panel(61.2, 1.4, 600), panel(70.2, 1.4, 600), wide(72.8)] },
  { from: 72.8, to: 82.0, speed: 1.5, chip: "04 · Act on it", keys: [wide(72.8), panel(73.8), panel(81.2), wide(82.0)] },
  { from: 82.0, to: 106.0, speed: 1.8, chip: "Shared checklist, by role", keys: [wide(82.0), { t: 83.5, z: 1.35, x: 960, y: 560 }, { t: 92.4, z: 1.35, x: 960, y: 560 }, wide(93.6), { t: 99.5, z: 1.5, x: 980, y: 620 }, { t: 106, z: 1.5, x: 980, y: 620 }] },
  { from: 112.0, to: 128.8, speed: 1.6, chip: "Early warnings", keys: [wide(112), wide(114.5), panel(116, 1.45, 620), panel(128, 1.45, 640), wide(128.8)] },
  { from: 128.8, to: 136.4, speed: 1.3, chip: "Ask in plain English", keys: [wide(128.8), panel(130.5, 1.6, 820), panel(136.4, 1.6, 820)] },
  { from: 175.2, to: 203.4, speed: 1.6, keys: [panel(175.2, 1.6, 820), panel(177.4, 1.55, 640), panel(192.8, 1.55, 640), panel(194.5, 1.5, 760), panel(198.2, 1.5, 760), panel(199.4, 1.45, 620), panel(202.6, 1.45, 620), wide(203.4)] },
];

const TITLE = 75;
const frames = (s: Segment) => Math.round(((s.to - s.from) * FPS) / s.speed);
export const DEMO_FRAMES = TITLE + SEGMENTS.reduce((n, s) => n + frames(s), 0);

function camera(keys: Key[], t: number) {
  const ease = Easing.inOut(Easing.cubic);
  const at = (k: keyof Key) => interpolate(t, keys.map((x) => x.t), keys.map((x) => x[k]), { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const z = at("z");
  const tx = Math.min(0, Math.max(W - W * z, W / 2 - at("x") * z));
  const ty = Math.min(0, Math.max(H - H * z, H / 2 - at("y") * z));
  return `translate(${tx}px, ${ty}px) scale(${z})`;
}

function Chip({ text }: { text: string }) {
  const frame = useCurrentFrame();
  const o = Math.min(
    interpolate(frame, [6, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(frame, [80, 92], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  return (
    <div style={{ position: "absolute", left: 40, top: 500, opacity: o, transform: `translateX(${(1 - o) * -20}px)`, background: C.ink, color: "#fff", fontFamily: PIXEL, fontSize: 24, letterSpacing: "0.16em", textTransform: "uppercase", padding: "16px 22px", boxShadow: `6px 6px 0 ${C.blue}` }}>
      {text}
    </div>
  );
}

function Clip({ s, cutIn }: { s: Segment; cutIn: boolean }) {
  const frame = useCurrentFrame();
  const t = s.from + (frame / FPS) * s.speed;
  const flash = cutIn ? interpolate(frame, [0, 8], [1, 0], { extrapolateRight: "clamp" }) : 0;
  return (
    <AbsoluteFill style={{ background: "#fff", overflow: "hidden" }}>
      <div style={{ position: "absolute", width: W, height: H, transformOrigin: "0 0", transform: camera(s.keys, t) }}>
        <OffthreadVideo src={staticFile("demo/demo.mp4")} trimBefore={Math.round(s.from * FPS)} playbackRate={s.speed} muted style={{ width: W, height: H }} />
      </div>
      {s.chip && <Chip text={s.chip} />}
      <AbsoluteFill style={{ background: "#fff", opacity: flash }} />
    </AbsoluteFill>
  );
}

function DemoTitle() {
  return (
    <Slide section="Product demo" duration={TITLE + 8}>
      <div style={{ position: "absolute", left: 120, top: 330 }}>
        <Eyebrow>Live product · recorded in the app</Eyebrow>
        <Headline delay={3} size={96} style={{ marginTop: 20 }} lines={[["861", "Park", "Avenue,", "Brooklyn"]]} />
        <Reveal delay={14}>
          <p style={{ fontSize: 38, color: C.ink2, marginTop: 26, maxWidth: 1300, lineHeight: 1.35 }}>
            An active new-building site with excavation, next to attached neighbors built 1910–1931.
          </p>
        </Reveal>
      </div>
    </Slide>
  );
}

export function Demo() {
  let at = TITLE;
  return (
    <AbsoluteFill style={{ background: "#fff" }}>
      {SEGMENTS.map((s, i) => {
        const from = at;
        at += frames(s);
        const cutIn = i > 0 && Math.abs(SEGMENTS[i - 1].to - s.from) > 0.5;
        return (
          <Sequence key={s.from} from={from} durationInFrames={frames(s)} premountFor={30}>
            <Clip s={s} cutIn={cutIn} />
          </Sequence>
        );
      })}
      <Sequence durationInFrames={TITLE + 8}>
        <DemoTitle />
      </Sequence>
    </AbsoluteFill>
  );
}
