// The app shell: a full-bleed map with floating panels that slide over it. The user never leaves the map.
//   top left     brand, search (/ or Cmd/Ctrl-K), panel buttons
//   left         layers (Shandon's PR 5 fills it)
//   right        the picked site (PR 10), with the chat (Jahleel's PR 9) under it
//   bottom right the chat button, which opens and closes the chat
//   bottom left  "What ForeSite doesn't know", always visible
// What is open lives in the URL (url_state.ts), so every view can be shared.
import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { LayerCatalogEntry, SearchResult } from "../contracts";
import { Button, ChatIcon, CloseIcon, Kbd, KeyboardIcon, LayersIcon, MoonIcon, SearchIcon, SunIcon } from "../design";
import { CityMap } from "../features/city_map/CityMap";
import type { Picked } from "../features/city_map/site_lots";
import { LimitationsPanel } from "../features/limitations/LimitationsPanel";
import { CommandBar, type Command } from "./CommandBar";
import { useTheme } from "./preferences";
import { ShortcutsHelp } from "./ShortcutsHelp";
import { keyLabel, useShortcuts, type Shortcut } from "./shortcuts";
import { ChatSlot, DataStatus, LayerSlot, SiteSlot } from "./slots";
import { useViewState } from "./url_state";
// After the design system's CSS (imported through ../design), so layout rules win over component defaults.
import "./shell.css";

export function App() {
  const [view, setView] = useViewState();
  const [theme, toggleTheme] = useTheme();
  const [commandOpen, setCommandOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

  const [layers, setLayers] = useState<LayerCatalogEntry[] | null>(null);
  const [enabled, setEnabled] = useState<Set<string>>(new Set());
  const [site, setSite] = useState<SearchResult | null>(null);
  const [sample, setSample] = useState(false);
  const markSample = useCallback(() => setSample(true), []);

  useEffect(() => {
    api.layers().then((r) => {
      setLayers(r.data);
      setEnabled(new Set(r.data.filter((l) => l.default_on && l.status !== "error").map((l) => l.layer_id)));
      setSample((s) => s || r.sample);
    });
  }, []);

  // A shared link carries only the BBL; look the address up so the panel can show it and the map can fly
  // there. Search does not match every BBL, so the site profile is the fallback.
  useEffect(() => {
    const bbl = view.site;
    if (!bbl || site?.bbl === bbl) return;
    let live = true;
    api.search(bbl).then(async (r) => {
      const found = r.data.find((x) => x.bbl === bbl);
      if (found) return live && setSite(found);
      const p = await api.siteProfile(bbl);
      if (!live || p.data.bbl !== bbl) return;
      if (p.sample) setSample(true);
      setSite({ label: p.data.address_matched, bbl, bin: p.data.bins[0] ?? null, lat: p.data.lat, lon: p.data.lon });
    });
    return () => {
      live = false;
    };
  }, [view.site, site?.bbl]);

  const toggleLayer = (id: string, on: boolean) =>
    setEnabled((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });

  const pickSite = useCallback((result: SearchResult | Picked) => {
    setSite(result);
    setView({ site: result.bbl, tab: "overview" });
  }, [setView]);

  const shortcuts: Shortcut[] = [
    { keys: ["/", "Mod+k"], label: "Search an address", run: () => setCommandOpen(true), allowInFields: true },
    { keys: ["l"], label: "Show or hide layers", run: () => setView({ layers: !view.layers }) },
    { keys: ["c"], label: "Show or hide the chat", run: () => setView({ chat: !view.chat }) },
    { keys: ["t"], label: "Switch light or dark theme", run: toggleTheme },
    { keys: ["?"], label: "Keyboard shortcuts", run: () => setHelpOpen((o) => !o) },
    {
      keys: ["Escape"],
      label: "Close the top panel",
      run: () => {
        if (helpOpen) setHelpOpen(false);
        else if (view.chat) setView({ chat: false });
        else if (view.site) setView({ site: null });
        else if (view.layers) setView({ layers: false });
      },
    },
  ];
  useShortcuts(commandOpen ? [] : shortcuts);

  const commands: Command[] = [
    { id: "layers", label: view.layers ? "Hide layers" : "Show layers", keys: "L", run: () => setView({ layers: !view.layers }) },
    { id: "chat", label: view.chat ? "Hide chat" : "Open chat", keys: "C", run: () => setView({ chat: !view.chat }) },
    { id: "theme", label: theme === "dark" ? "Switch to light theme" : "Switch to dark theme", keys: "T", run: toggleTheme },
    {
      id: "copy",
      label: "Copy a link to this view",
      hint: "The link opens the same site and panels",
      run: () => void navigator.clipboard?.writeText(window.location.href).catch(() => undefined),
    },
    { id: "help", label: "Keyboard shortcuts", keys: "?", run: () => setHelpOpen(true) },
  ];

  return (
    <main className="fs-shell" data-site={Boolean(view.site)} data-chat={view.chat} data-layers={view.layers}>
      <div className="fs-shell__map">
        <CityMap site={site && site.bbl === view.site ? site : null} onPick={pickSite} enabled={enabled} onSample={markSample} />
      </div>

      <div className="fs-shell__left">
        <header className="fs-topbar fs-panel">
          <span className="fs-brand">
            <span className="fs-brand__mark" aria-hidden="true" />
            ForeSite
          </span>
          <button type="button" className="fs-search" onClick={() => setCommandOpen(true)} aria-label="Search an address">
            <SearchIcon width={16} height={16} />
            <span>Search an address</span>
            <Kbd>/</Kbd>
          </button>
          <div className="fs-topbar__tools">
            <Button variant="ghost" size="icon" aria-label={`Layers (${keyLabel("l")})`} aria-pressed={view.layers} title="Layers (L)" onClick={() => setView({ layers: !view.layers })}>
              <LayersIcon />
            </Button>
            <Button variant="ghost" size="icon" aria-label={theme === "dark" ? "Light theme (T)" : "Dark theme (T)"} title="Theme (T)" onClick={toggleTheme}>
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            </Button>
            <Button variant="ghost" size="icon" aria-label="Keyboard shortcuts (?)" title="Shortcuts (?)" onClick={() => setHelpOpen(true)}>
              <KeyboardIcon />
            </Button>
          </div>
        </header>

        <LayerSlot
          open={view.layers}
          onClose={() => setView({ layers: false })}
          layers={layers}
          enabled={enabled}
          onToggle={toggleLayer}
        />
      </div>

      <div className="fs-shell__right">
        <SiteSlot
          bbl={view.site}
          site={site}
          onClose={() => setView({ site: null, tab: "overview" })}
          tab={view.tab}
          onTab={(tab) => setView({ tab })}
        />
        <ChatSlot
          open={view.chat}
          bbl={view.site}
          site={site}
          onPickBbl={(bbl) => setView({ site: bbl, tab: "overview" })}
          onToggleLayer={toggleLayer}
        />
      </div>

      <div className="fs-shell__bottom">
        <LimitationsPanel />
        <DataStatus layers={layers} sample={sample} />
      </div>

      <button type="button" className="fs-chat-fab" aria-label={view.chat ? "Close the chat (C)" : "Ask about this site (C)"}
        aria-pressed={view.chat} title="Chat (C)" onClick={() => setView({ chat: !view.chat })}>
        {view.chat ? <CloseIcon /> : <ChatIcon />}
      </button>

      {!view.site && !commandOpen && (
        <div className="fs-hint" role="note">
          Press <Kbd>/</Kbd> to find a site, or pick one on the map
        </div>
      )}

      <CommandBar open={commandOpen} onClose={() => setCommandOpen(false)} onPickSite={pickSite} commands={commands} />
      <ShortcutsHelp open={helpOpen} onClose={() => setHelpOpen(false)} shortcuts={shortcuts} />
    </main>
  );
}
