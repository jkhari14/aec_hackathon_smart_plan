// "What ForeSite doesn't know": always on screen, collapsed to one line, one click to read in full.
// The forensic advisor's ask from session 3. Wording lives in the shared copy file (copy.limitations).
import { useId, useState } from "react";

import { copy } from "../../copy";
import { ChevronIcon, InfoIcon } from "../../design";

const L = copy.limitations;

export function LimitationsPanel() {
  const [open, setOpen] = useState(false);
  const id = useId();

  return (
    <aside className="fs-limits fs-panel" data-open={open} aria-label={L.title}>
      <button type="button" className="fs-limits__head" aria-expanded={open} aria-controls={id} onClick={() => setOpen((o) => !o)}>
        <InfoIcon width={16} height={16} />
        <span className="fs-limits__title">{L.title}</span>
        <span className="fs-limits__short">{L.short}</span>
        <ChevronIcon width={14} height={14} className="fs-limits__chev" />
      </button>
      <div id={id} className="fs-limits__body" hidden={!open}>
        <ul>
          {L.points.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
