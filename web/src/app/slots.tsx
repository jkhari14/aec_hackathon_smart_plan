// The panels the shell hosts. Each is a slot with a working interim body so the shell can be judged on
// fixtures now; the owners' PRs replace the bodies, not the frames:
//   LayerSlot   -> Shandon's layer panel (PR 5)
//   SiteSlot    -> Camilo's site, similar-case and action panels (PR 10)
//   ChatSlot    -> Jahleel's chat panel (PR 9)
import type { CSSProperties } from "react";

import type { LayerCatalogEntry, SearchResult } from "../contracts";
import {
  Badge,
  Count,
  EmptyState,
  ErrorState,
  formatDate,
  HAZARD_LABELS,
  Kbd,
  Panel,
  SkeletonCard,
  SourceLabel,
  Toggle,
} from "../design";
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
      {layers?.map((layer) => (
        <div key={layer.layer_id} className="fs-layer" style={{ "--fs-hz": `var(--fs-hz-${layer.hazard})` } as CSSProperties}>
          {layer.status === "error" ? (
            <ErrorState title={`${layer.name}: couldn't load`}>
              The source did not answer, so nothing is drawn. This is not the same as zero records.
            </ErrorState>
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
};

export function SiteSlot({ bbl, site, onClose }: SiteSlotProps) {
  const open = Boolean(bbl);
  return (
    <Panel
      title={site ? titleCase(site.label).split(",")[0] : bbl ? `BBL ${bbl}` : "Site"}
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
      <p className="fs-label">Top signals</p>
      <SkeletonCard lines={2} />
      <SkeletonCard lines={2} />
      <SkeletonCard lines={1} />
      <EmptyState title="Site panel arrives in PR 10">
        The top three signals (life safety first), similar cases and actions by discipline fill this panel.
        Lot facts tuck into a section below them.
      </EmptyState>
    </Panel>
  );
}

// ---- Chat ----------------------------------------------------------------------------------------

export function ChatSlot({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Panel title="Ask about this site" open={open} edge="bottom" onClose={onClose} className="fs-shell__chat" label="Chat">
      <EmptyState title="Chat arrives in PR 9">
        Answers come back as cards with source chips. Click a chip to fly to the record; pin any answer to the project.
      </EmptyState>
      <div className="fs-chat__input" aria-disabled="true">
        <span>Ask a question about the site</span>
        <Kbd>Enter</Kbd>
      </div>
    </Panel>
  );
}

// ---- Status line ---------------------------------------------------------------------------------

export function DataStatus({ layers, sample }: { layers: LayerCatalogEntry[] | null; sample: boolean }) {
  if (!layers) return null;
  const failed = layers.filter((l) => l.status === "error").length;
  const newest = layers.map((l) => l.updated_at).filter(Boolean).sort().pop();
  return (
    <div className="fs-status" role="status">
      {sample && <Badge tone="sample">Sample data</Badge>}
      {failed > 0 && <Badge tone="error">{failed} layer{failed > 1 ? "s" : ""} couldn't load</Badge>}
      {newest && <span className="fs-num">Data as of {formatDate(newest)}</span>}
    </div>
  );
}
