// On-screen camera controls for inspecting a site in 3D: orbit left and right around the picked site,
// tilt up and down, zoom, and reset to the starting view. A click turns one step; holding keeps turning.
// Keys: Q and E orbit, R resets (ignored while typing). Right-drag or Ctrl-drag still rotates freely.
import type { Map as MapLibreMap } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import { PITCH_3D, viewMode, type ViewMode } from "./selection_blink";

type Props = {
  map: MapLibreMap | null;
  /** The picked site, [lon, lat]: orbiting pivots around it. Without one, around the screen centre. */
  site: [number, number] | null;
  /** The view "Reset" returns to. */
  home: { center: [number, number]; zoom: number; pitch: number; bearing: number };
};

const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const HOLD_MS = 220; // a press longer than this keeps moving instead of stepping once
const ORBIT_STEP = 45; // degrees per click
const ORBIT_SPEED = 50; // degrees per second while held
const TILT_STEP = 12;
const TILT_SPEED = 30;

type Motion = { orbit: number; tilt: number }; // -1, 0 or 1 each

const Icon = ({ d, flip = false }: { d: string; flip?: boolean }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true" style={flip ? { transform: "scaleX(-1)" } : undefined}>
    <path d={d} />
  </svg>
);
// An arc with an arrowhead (orbit), a chevron (tilt), and a compass needle.
const ORBIT = "M3 12a9 9 0 1 0 3-6.7M3 4v5h5";
const TILT_UP = "M6 15l6-6 6 6";
const TILT_DOWN = "M6 9l6 6 6-6";
const PLUS = "M12 5v14M5 12h14";
const MINUS = "M5 12h14";


const inField = (target: EventTarget | null) =>
  target instanceof HTMLElement && (target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName));

export function CameraControls({ map, site, home }: Props) {
  const motion = useRef<Motion>({ orbit: 0, tilt: 0 });
  const frame = useRef(0);
  const holdTimer = useRef(0);
  const [bearing, setBearing] = useState(0);
  const [mode, setMode] = useState<ViewMode>("3d");

  useEffect(() => {
    if (!map) return;
    const update = () => setBearing(map.getBearing());
    const pitched = () => setMode(viewMode(map.getPitch()));
    map.on("rotate", update);
    map.on("pitch", pitched);
    update();
    pitched();
    return () => {
      map.off("rotate", update);
      map.off("pitch", pitched);
    };
  }, [map]);

  /** 2D is straight down; 3D tilts back to the default angle. The map blinks the site on the switch. */
  const toggleMode = useCallback(() => {
    if (!map) return;
    const pitch = mode === "2d" ? PITCH_3D : 0;
    if (reducedMotion()) map.jumpTo({ pitch });
    else map.easeTo({ pitch, duration: 600 });
  }, [map, mode]);

  // Continuous motion while a button or key is held: turn around the site, sliding the centre onto it.
  const loop = useCallback(() => {
    if (!map) return;
    let last = performance.now();
    const step = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000); // seconds since the last frame; capped so a stall cannot jump
      last = now;
      const { orbit, tilt } = motion.current;
      if (!orbit && !tilt) {
        frame.current = 0;
        return;
      }
      const center = map.getCenter();
      const target = site ?? [center.lng, center.lat];
      map.jumpTo({
        center: [center.lng + (target[0] - center.lng) * 0.12, center.lat + (target[1] - center.lat) * 0.12],
        bearing: map.getBearing() + orbit * ORBIT_SPEED * dt,
        pitch: Math.max(0, Math.min(map.getMaxPitch(), map.getPitch() + tilt * TILT_SPEED * dt)),
      });
      frame.current = requestAnimationFrame(step);
    };
    if (!frame.current) frame.current = requestAnimationFrame(step);
  }, [map, site]);

  const stepOnce = useCallback((m: Motion) => {
    if (!map) return;
    map.easeTo({
      ...(site ? { center: site } : {}),
      bearing: map.getBearing() + m.orbit * ORBIT_STEP,
      pitch: Math.max(0, Math.min(map.getMaxPitch(), map.getPitch() + m.tilt * TILT_STEP)),
      duration: reducedMotion() ? 0 : 600,
    });
  }, [map, site]);

  const start = useCallback((m: Motion) => {
    window.clearTimeout(holdTimer.current);
    holdTimer.current = window.setTimeout(() => {
      holdTimer.current = 0;
      motion.current = m;
      loop();
    }, HOLD_MS);
  }, [loop]);

  const stop = useCallback((m: Motion) => {
    if (holdTimer.current) {
      // Released before the hold kicked in: one step.
      window.clearTimeout(holdTimer.current);
      holdTimer.current = 0;
      stepOnce(m);
    }
    motion.current = { orbit: 0, tilt: 0 };
  }, [stepOnce]);

  const reset = useCallback(() => {
    map?.flyTo({ ...home, duration: reducedMotion() ? 0 : 1200, essential: false });
  }, [map, home]);

  // Q / E orbit while held, R resets.
  useEffect(() => {
    const keys: Record<string, Motion> = { q: { orbit: 1, tilt: 0 }, e: { orbit: -1, tilt: 0 } };
    const down = (e: KeyboardEvent) => {
      if (inField(e.target) || e.metaKey || e.ctrlKey || e.altKey) return;
      const key = e.key.toLowerCase();
      if (key === "r" && !e.repeat) reset();
      const m = keys[key];
      if (m && !e.repeat) {
        motion.current = m;
        loop();
      }
    };
    const up = (e: KeyboardEvent) => {
      if (keys[e.key.toLowerCase()]) motion.current = { orbit: 0, tilt: 0 };
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, [loop, reset]);

  useEffect(() => () => {
    cancelAnimationFrame(frame.current);
    window.clearTimeout(holdTimer.current);
  }, []);

  const hold = (m: Motion) => ({
    onPointerDown: (e: React.PointerEvent) => {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      start(m);
    },
    onPointerUp: () => stop(m),
    onPointerCancel: () => stop(m),
    onKeyDown: (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        stepOnce(m);
      }
    },
  });

  const button = "fs-cam__btn";
  const next = mode === "2d" ? "3D" : "2D";
  return (
    <div className="flex flex-col items-start gap-1 text-[11px]">
      <div className="fs-cam" role="toolbar" aria-label="Camera">
        <button type="button" className="fs-cam__btn fs-cam__mode" title={`Switch to ${next} view`} aria-label={`Switch to ${next} view`}
          onClick={toggleMode}>
          {next}
        </button>
        <span className="fs-cam__sep" aria-hidden="true" />
        <button type="button" className={button} title="Orbit left (Q) · hold to keep turning" aria-label="Orbit left" {...hold({ orbit: 1, tilt: 0 })}><Icon d={ORBIT} /></button>
        <button
          type="button"
          className={button}
          title="Reset view (R)"
          aria-label="Reset view"
          onClick={reset}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" style={{ transform: `rotate(${-bearing}deg)` }}>
            <path d="M12 3l4 9h-8z" fill="var(--fs-accent)" />
            <path d="M12 21l-4-9h8z" fill="currentColor" />
          </svg>
        </button>
        <button type="button" className={button} title="Orbit right (E) · hold to keep turning" aria-label="Orbit right" {...hold({ orbit: -1, tilt: 0 })}><Icon d={ORBIT} flip /></button>
        <span className="fs-cam__sep" aria-hidden="true" />
        <button type="button" className={button} title="Tilt up, toward street level · hold to keep tilting" aria-label="Tilt up" {...hold({ orbit: 0, tilt: 1 })}><Icon d={TILT_UP} /></button>
        <button type="button" className={button} title="Tilt down, toward the top view · hold to keep tilting" aria-label="Tilt down" {...hold({ orbit: 0, tilt: -1 })}><Icon d={TILT_DOWN} /></button>
        <span className="fs-cam__sep" aria-hidden="true" />
        <button type="button" className={button} title="Zoom in" aria-label="Zoom in" onClick={() => map?.zoomIn({ duration: reducedMotion() ? 0 : 300 })}><Icon d={PLUS} /></button>
        <button type="button" className={button} title="Zoom out" aria-label="Zoom out" onClick={() => map?.zoomOut({ duration: reducedMotion() ? 0 : 300 })}><Icon d={MINUS} /></button>
      </div>
      <span className="fs-cam__hint">Hold the arrows or Q / E to orbit · right-drag rotates · R resets</span>
    </div>
  );
}
