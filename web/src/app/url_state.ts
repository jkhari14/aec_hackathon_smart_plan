// Shareable URLs: what is open lives in the query string, so any view can be copied and sent.
//   ?site=<bbl>      the picked site (opens the site panel)
//   &layers=1        the layer panel is open
//   &chat=1          the chat dock is open
// Changes replace the current history entry (no back-button spam); the back button still works across
// page loads because the URL is read on load and on popstate.
import { useCallback, useEffect, useState } from "react";

export type ViewState = {
  site: string | null;
  layers: boolean;
  chat: boolean;
};

function read(): ViewState {
  const q = new URLSearchParams(window.location.search);
  return {
    site: q.get("site"),
    layers: q.get("layers") === "1",
    chat: q.get("chat") === "1",
  };
}

function write(state: ViewState, push: boolean) {
  const q = new URLSearchParams(window.location.search);
  const set = (key: string, value: string | null) => (value ? q.set(key, value) : q.delete(key));
  set("site", state.site);
  set("layers", state.layers ? "1" : null);
  set("chat", state.chat ? "1" : null);
  const search = q.toString();
  const url = `${window.location.pathname}${search ? `?${search}` : ""}${window.location.hash}`;
  if (url === `${window.location.pathname}${window.location.search}${window.location.hash}`) return;
  window.history[push ? "pushState" : "replaceState"](null, "", url);
}

export function useViewState() {
  const [state, setState] = useState<ViewState>(read);

  useEffect(() => {
    const onPop = () => setState(read());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  /** Picking a new site pushes a history entry; panel toggles replace it. */
  const update = useCallback((patch: Partial<ViewState>) => {
    setState((prev) => {
      const next = { ...prev, ...patch };
      write(next, patch.site !== undefined && patch.site !== prev.site);
      return next;
    });
  }, []);

  return [state, update] as const;
}
