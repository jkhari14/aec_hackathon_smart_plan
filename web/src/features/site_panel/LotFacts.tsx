// Lot facts, neighbors and the sources checked. Side info: tucked into sections, never a step to stop at.
import type { ReactNode } from "react";

import type { SiteProfile } from "../../contracts";
import { copy } from "../../copy";
import { Badge, Count, Explain, humanize, SourceLabel } from "../../design";

function Row({ label, value }: { label: string; value: ReactNode }) {
  const missing = value === null || value === undefined || value === "";
  return (
    <>
      <dt>{label}</dt>
      <dd data-missing={missing}>{missing ? "not on record" : value}</dd>
    </>
  );
}

const ft = (n?: number | null) => (n == null ? null : `${n.toLocaleString("en-US")} ft`);

export function LotFacts({ profile }: { profile: SiteProfile }) {
  const { lot } = profile;
  return (
    <dl className="fs-facts">
      <Row label="Year built" value={lot.year_built} />
      <Row label="Floors" value={lot.floors} />
      <Row label="Building class" value={lot.building_class} />
      <Row label="Zoning" value={lot.zoning} />
      <Row label="Built / max FAR" value={lot.built_far != null || lot.max_far != null ? `${lot.built_far ?? "?"} / ${lot.max_far ?? "?"}` : null} />
      <Row label="Lot area" value={lot.lot_area_sqft != null ? `${lot.lot_area_sqft.toLocaleString("en-US")} sq ft` : null} />
      <Row label="Landmark" value={lot.landmark} />
      <Row label="Historic district" value={lot.historic_district} />
      <Row label="BINs" value={profile.bins.join(", ")} />
    </dl>
  );
}

export function WorkAndGround({ profile }: { profile: SiteProfile }) {
  return (
    <>
      <div className="fs-worktypes">
        <span className="fs-worktypes__label">
          {profile.job_type ? copy.jobTypes[profile.job_type] : "Job type not on record"}
          {profile.stage && <Badge title={copy.stageHelp[profile.stage]}>{copy.stages[profile.stage]}</Badge>}
        </span>
        <div className="fs-worktypes__chips">
          {profile.work_types.map((w) => (
            <span key={w} className="fs-tag">{humanize(w)}</span>
          ))}
        </div>
        {profile.work_types_inferred && (
          <Explain label="Why these work types?">
            <p>Inferred from the job type, using the DOB NOW filing structure. Everything is on by default; the project can untick what does not apply.</p>
          </Explain>
        )}
      </div>
      <dl className="fs-facts">
        <Row label="Soil" value={profile.soil} />
        <Row label="Depth to bedrock" value={ft(profile.bedrock_depth_ft)} />
        <Row label="FEMA flood zone" value={profile.flood.fema_zone} />
        <Row label="Sandy inundation" value={profile.flood.sandy_inundation == null ? null : profile.flood.sandy_inundation ? "inside the 2012 zone" : "outside"} />
        <Row label="E-designation" value={profile.e_designation} />
      </dl>
    </>
  );
}

export function Neighbors({ profile }: { profile: SiteProfile }) {
  const attached = profile.neighbors.filter((n) => n.attached);
  if (profile.neighbors.length === 0) return <p className="fs-quiet">No neighboring lots on record.</p>;
  return (
    <ul className="fs-neighbors">
      {profile.neighbors.map((n) => (
        <li key={n.bbl}>
          <span className="fs-neighbors__addr">{n.address ? titleWords(n.address) : `BBL ${n.bbl}`}</span>
          <span className="fs-neighbors__meta fs-num">
            {n.attached ? copy.sitePanel.attached : copy.sitePanel.detached} · {n.year_built ?? copy.sitePanel.yearUnknown} ·{" "}
            {n.floors != null ? `${n.floors} fl` : "floors unknown"}
            {n.shared_wall_ft != null ? ` · ${n.shared_wall_ft} ft shared wall` : ""}
          </span>
        </li>
      ))}
      {attached.length > 0 && (
        <li className="fs-quiet">
          {attached.length} attached neighbor{attached.length > 1 ? "s" : ""}
          {attached.some((n) => (n.year_built ?? 9999) < 1940) ? ", built before 1940." : "."}
        </li>
      )}
    </ul>
  );
}

export function SourcesChecked({ profile }: { profile: SiteProfile }) {
  return (
    <ul className="fs-sources">
      {profile.datasets.map((d) => (
        <li key={d.key}>
          <SourceLabel name={d.name} url={d.source_url} date={profile.as_of} />
          <Count value={d.count} status={d.status} />
        </li>
      ))}
    </ul>
  );
}

const titleWords = (s: string) => s.replace(/\b([A-Z])([A-Z]{2,})\b/g, (_, a: string, b: string) => a + b.toLowerCase());
