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

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => (load("foresite.theme") === "light" ? "light" : "dark"));

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    save("foresite.theme", theme);
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
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
