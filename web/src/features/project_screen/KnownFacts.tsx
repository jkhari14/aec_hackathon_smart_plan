// The top of setup: what public records already say about the lot, each line with its source. It loads the
// same site profile the map shows; while it loads it says so, and a failed load says "couldn't load".
import { useEffect, useState } from "react";

import { api } from "../../api/client";
import type { SiteProfile } from "../../contracts";
import { formatDate, SampleBadge } from "../../design";
import { knownFacts } from "./known_facts";

export function KnownFacts({ bbl }: { bbl: string }) {
  const [state, setState] = useState<{ profile: SiteProfile | null; sample: boolean; done: boolean }>(
    { profile: null, sample: false, done: false });

  useEffect(() => {
    let live = true;
    api.siteProfile(bbl)
      .then(({ data, sample }) => live && setState({ profile: data, sample, done: true }))
      .catch(() => live && setState({ profile: null, sample: false, done: true }));
    return () => {
      live = false;
    };
  }, [bbl]);

  const { profile, sample, done } = state;
  return (
    <section className="fs-ps-known" aria-label="What we already know about this lot">
      <header className="fs-ps-known__head">
        <h3 className="fs-label">What we already know about this lot</h3>
        {sample && <SampleBadge />}
      </header>
      <dl className="fs-ps-known__list">
        {knownFacts(done ? profile : null).map((f) => (
          <div key={f.label} className="fs-ps-known__row">
            <dt>{f.label}</dt>
            <dd>
              {f.value ?? <span className="fs-quiet">{done ? "couldn't load" : "loading…"}</span>}
              <span className="fs-ps-known__src">{f.source}</span>
            </dd>
          </div>
        ))}
      </dl>
      <p className="fs-quiet fs-num">
        From public records{profile?.as_of ? `, as of ${formatDate(profile.as_of)}` : " (latest pulled for this lot)"}. Only the
        questions below are things the records can't tell us.
      </p>
    </section>
  );
}
