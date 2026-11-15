// The opening: the 4site logo building itself in 8-bit, once per visit, while the map loads underneath.
// When it ends (or on a click or a key) it fades, and the shell materialises. Skipped for reduced motion,
// and never blocks: if the video can't play, the app appears at once.
import { useCallback, useEffect, useRef, useState } from "react";

const SEEN = "foresite.intro.seen";
// The whole opening is 4 s: the 1.6 s build, a hold on the finished logo, then a 0.8 s fade-and-zoom
// into the map. A click or key skips it at any point; a video error skips it at once.
const HOLD_MS = 3200;
const FADE_MS = 800;

function alreadySeen(): boolean {
  try {
    return window.sessionStorage.getItem(SEEN) === "1" || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

function markSeen() {
  try {
    window.sessionStorage.setItem(SEEN, "1");
  } catch {
    // Storage blocked: the intro may show again next load, which is harmless.
  }
}

/** `onDone` fires as the intro starts to fade, so the shell can materialise underneath it. */
export function Intro({ onDone }: { onDone: () => void }) {
  const [state, setState] = useState<"playing" | "leaving" | "gone">(() => (alreadySeen() ? "gone" : "playing"));
  const done = useRef(false);

  const finish = useCallback(() => {
    if (done.current) return;
    done.current = true;
    markSeen();
    onDone();
    setState("leaving");
    window.setTimeout(() => setState("gone"), FADE_MS);
  }, [onDone]);

  useEffect(() => {
    if (state === "gone" && !done.current) {
      done.current = true;
      onDone();
    }
  }, [state, onDone]);

  useEffect(() => {
    if (state !== "playing") return;
    const timer = window.setTimeout(finish, HOLD_MS);
    const key = () => finish();
    window.addEventListener("keydown", key);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("keydown", key);
    };
  }, [state, finish]);

  if (state === "gone") return null;
  return (
    <div className="fs-intro" data-state={state} onClick={finish} role="presentation">
      <video
        className="fs-intro__video"
        src={`${import.meta.env.BASE_URL}4site-intro.mp4`}
        poster={`${import.meta.env.BASE_URL}4site-intro-poster.png`}
        autoPlay
        muted
        playsInline
        preload="auto"
        onError={finish}
        aria-label="4site"
      />
      <span className="fs-intro__skip">Click or press any key to skip</span>
    </div>
  );
}
