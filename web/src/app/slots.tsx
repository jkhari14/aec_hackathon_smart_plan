// The panels the shell hosts. Each is a slot with a working interim body so the shell can be judged on
// fixtures now; the owners' PRs replace the bodies, not the frames:
//   LayerSlot   -> Shandon's layer panel (PR 5)
//   SiteSlot    -> Camilo's site, similar-case and action panels (PR 10, filled)
//   ChatSlot    -> Jahleel's chat panel (PR 9, filled)
import type { CSSProperties } from "react";

import type { LayerCatalogEntry, SearchResult } from "../contracts";
import { copy } from "../copy";
import {
  Badge,
  Count,
  EmptyState,
  ErrorState,
  formatDate,
  HAZARD_LABELS,
  Panel,
  SampleBadge,
  Skeleton,
  SkeletonCard,
  SourceLabel,
  Toggle,
} from "../design";
import { ChatPanel } from "../features/chat/ChatPanel";
import { SitePanel, useSiteData, type SiteTab } from "../features/site_panel/SitePanel";
import { titleCase } from "./CommandBar";

// ---- Layers --------------------------------------------------------------------------------------

type LayerSlotProps = {
  open: boolean;
  onClose: () => void;
  layers: LayerCatalogEntry[] | null;
  enabled: Set<string>;
  onToggle: (id: string, on: boolean) => void;
};

export function LayerSlot({ open, onClose, layers, enabled, onToggle }: LayerSlotProps) {
  const usable = layers?.filter((l) => l.status !== "error") ?? [];
  const allOn = usable.length > 0 && usable.every((l) => enabled.has(l.layer_id));
  const onCount = usable.filter((l) => enabled.has(l.layer_id)).length;
  return (
    <Panel
      title="Layers"
      subtitle="Public data by hazard. Off means filtered, not deleted."
      open={open}
      edge="left"
      onClose={onClose}
      className="fs-shell__layers"
      label="Layers"
    >
      {layers === null && (
        <>
          <SkeletonCard lines={1} />
          <SkeletonCard lines={1} />
          <SkeletonCard lines={1} />
        </>
      )}
      {layers?.length === 0 && <EmptyState title="No layers yet">The layer catalog came back empty.</EmptyState>}
      {usable.length > 1 && (
        <div className="fs-layer fs-layer--all">
          <Toggle
            checked={allOn}
            onChange={(on) => usable.forEach((l) => onToggle(l.layer_id, on))}
            label={<span className="fs-layer__name">All layers</span>}
            hint={`${onCount} of ${usable.length} on`}
          />
        </div>
      )}
      {layers?.map((layer) => (
        <div key={layer.layer_id} className="fs-layer" style={{ "--fs-hz": `var(--fs-hz-${layer.hazard})` } as CSSProperties}>
          {layer.status === "error" ? (
            <ErrorState title={`${layer.name}: ${copy.queryStatus.error.toLowerCase()}`}>{copy.states.couldntLoad}</ErrorState>
          ) : (
            <Toggle
              checked={enabled.has(layer.layer_id)}
              onChange={(on) => onToggle(layer.layer_id, on)}
              label={
                <span className="fs-layer__name">
                  <span className="fs-chip__dot" aria-hidden="true" />
                  {layer.name}
                </span>
              }
              hint={
                <>
                  {HAZARD_LABELS[layer.hazard]} · <Count value={layer.feature_count} status={layer.status} />
                </>
              }
            />
          )}
          <SourceLabel name={layer.source_name} url={layer.source_url} date={layer.updated_at} />
        </div>
      ))}
    </Panel>
  );
}

// ---- Site ----------------------------------------------------------------------------------------

type SiteSlotProps = {
  bbl: string | null;
  site: SearchResult | null;
  onClose: () => void;
  tab: SiteTab;
  onTab: (tab: SiteTab) => void;
};

export function SiteSlot({ bbl, site, onClose, tab, onTab }: SiteSlotProps) {
  const open = Boolean(bbl);
  const data = useSiteData(bbl);
  return (
    <Panel
      title={site ? titleCase(site.label).split(",")[0] : bbl ? <Skeleton width={180} height={14} /> : "Site"}
      subtitle={
        site ? (
          <span className="fs-num">
            {titleCase(site.label).split(",").slice(1).join(",").trim()} · BBL {site.bbl}
            {site.bin ? ` · BIN ${site.bin}` : ""}
          </span>
        ) : undefined
      }
      open={open}
      edge="right"
      onClose={onClose}
      className="fs-shell__site"
      label="Site"
    >
      {open && <SitePanel data={data} tab={tab} onTab={onTab} />}
    </Panel>
  );
}

// ---- Chat ----------------------------------------------------------------------------------------

type ChatSlotProps = {
  open: boolean;
  bbl: string | null;
  site: SearchResult | null;
  onPickBbl: (bbl: string) => void;
  onToggleLayer: (id: string, on: boolean) => void;
};

// The chat frames itself; it stays mounted while closed so the conversation survives the chat button.
export function ChatSlot({ open, bbl, site, onPickBbl, onToggleLayer }: ChatSlotProps) {
  return (
    <div className="fs-shell__chat" data-open={open}>
      <ChatPanel
        bbl={bbl}
        siteLabel={site ? titleCase(site.label).split(",")[0] : undefined}
        className="min-h-0 max-h-full"
        onFlyTo={(target) => target.bbl && onPickBbl(target.bbl)}
        onToggleLayer={onToggleLayer}
      />
    </div>
  );
}

// ---- Status line ---------------------------------------------------------------------------------

export function DataStatus({ layers, sample }: { layers: LayerCatalogEntry[] | null; sample: boolean }) {
  if (!layers) return null;
  const failed = layers.filter((l) => l.status === "error").length;
  const newest = layers.map((l) => l.updated_at).filter(Boolean).sort().pop();
  return (
    <div className="fs-status" role="status">
      {sample && <SampleBadge />}
      {failed > 0 && (
        <Badge tone="error" title={copy.states.couldntLoad}>
          {failed} layer{failed > 1 ? "s" : ""}: {copy.queryStatus.error.toLowerCase()}
        </Badge>
      )}
      {newest && <span className="fs-num">Data as of {formatDate(newest)}</span>}
    </div>
  );
}
