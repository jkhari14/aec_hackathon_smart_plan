// Theme (dark first) and motion preferences. Stored per browser as a convenience only: the app renders
// correctly when storage is blocked.
import { useCallback, useEffect, useState } from "react";

export type Theme = "dark" | "light";

function load(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function save(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Storage blocked (private window, policy): the choice lasts for this page only.
  }
}

// A new key since light became the default: the old one saved "dark" for everyone on every visit.
const THEME_KEY = "foresite.theme.v2";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved: Theme = load(THEME_KEY) === "dark" ? "dark" : "light";
    // Set before the first paint, so the map is made (and its layers coloured) for the right theme.
    document.documentElement.dataset.theme = saved;
    return saved;
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // Saved only when someone chooses, so the default can change again later.
  const toggle = useCallback(() => setTheme((t) => {
    const next = t === "dark" ? "light" : "dark";
    save(THEME_KEY, next);
    return next;
  }), []);
  return [theme, toggle] as const;
}

/** True when the OS asks for reduced motion. CSS already shortens transitions; JS animations read this. */
export function usePrefersReducedMotion() {
  const query = "(prefers-reduced-motion: reduce)";
  const [reduce, setReduce] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setReduce(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduce;
}
