// "What ForeSite doesn't know": always on screen, collapsed to one line, one click to read in full.
// The forensic advisor's ask from session 3. Interim wording: Ethnie's copy pass (PR 11) owns the final text.
import { useId, useState } from "react";

import { ChevronIcon, InfoIcon } from "../../design";

export const LIMITATIONS: string[] = [
  "Not exhaustive. Checking every item here does not mean a site is safe.",
  "Not engineering advice and not a DOB determination.",
  "Public records only. Anything not filed, or filed late, is missing.",
  "Proof is never inferred from public data. A document only counts once someone has read it.",
  "Housing violations are shown for context and never scored as structural risk.",
  "The pattern score compares this site with similar sites. It does not predict that a building will fail.",
  "Past cases give a cause only as publicly reported, or as under investigation.",
  "Every fact shows its source and date. A query that fails shows \"couldn't load\", never zero.",
];

export function LimitationsPanel() {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <aside className="fs-limits fs-panel" data-open={open} aria-label="What ForeSite doesn't know">
      <button type="button" className="fs-limits__head" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}>
        <InfoIcon width={16} height={16} />
        <span className="fs-limits__title">What ForeSite doesn't know</span>
        <span className="fs-limits__short">Not exhaustive · not engineering advice</span>
        <ChevronIcon width={14} height={14} className="fs-limits__chev" />
      </button>
      <div id={id} className="fs-limits__body" hidden={!open}>
        <ul>
          {LIMITATIONS.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
