// App-wide keyboard shortcuts. Single keys are ignored while the user types in a field.
import { useEffect, useRef } from "react";

export type Shortcut = { keys: string[]; label: string; run: () => void; allowInFields?: boolean };

export const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

function matches(e: KeyboardEvent, key: string) {
  const parts = key.split("+");
  const main = parts[parts.length - 1];
  const wantMod = parts.includes("Mod");
  const hasMod = isMac ? e.metaKey : e.ctrlKey;
  if (wantMod !== hasMod) return false;
  if (!wantMod && (e.metaKey || e.ctrlKey || e.altKey)) return false;
  return e.key.toLowerCase() === main.toLowerCase();
}

function inField(target: EventTarget | null) {
  const el = target as HTMLElement | null;
  return !!el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName));
}

export function useShortcuts(shortcuts: Shortcut[]) {
  const ref = useRef(shortcuts);
  ref.current = shortcuts;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.isComposing) return;
      for (const s of ref.current) {
        const key = s.keys.find((k) => matches(e, k));
        if (!key) continue;
        // In a text field only modifier shortcuts (Cmd/Ctrl-K) and Escape can fire, and only when allowed.
        if (inField(e.target) && (!s.allowInFields || !(key.includes("Mod+") || key === "Escape"))) continue;
        e.preventDefault();
        s.run();
        return;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
}

/** "Mod+k" -> "Ctrl K" or "⌘ K" for display. */
export function keyLabel(key: string) {
  return key
    .split("+")
    .map((p) => (p === "Mod" ? (isMac ? "⌘" : "Ctrl") : p === "Escape" ? "Esc" : p.length === 1 ? p.toUpperCase() : p))
    .join(" ");
}
