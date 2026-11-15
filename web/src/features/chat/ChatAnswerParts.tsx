// One answer, part by part. Every part shows where it came from before it shows what it says.
import type { Case } from "../../contracts";
import { flyTargetForPart, type FlyTarget } from "./chat_page_actions";
import { PART_KINDS, safeLink, type ChatPart } from "./chat_part_kinds";

type Props = {
  parts: ChatPart[];
  siteBbl: string;
  cases: Case[];
  onFlyTo?: (target: FlyTarget) => void;
};

const CHIP = "rounded border border-line px-1.5 py-0.5 text-xs text-text hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400";

function SourceChips({ part, siteBbl, cases, onFlyTo }: { part: ChatPart } & Omit<Props, "parts">) {
  const link = safeLink(part.source_url);
  const place = onFlyTo ? flyTargetForPart(part, siteBbl, cases) : null;
  if (!part.source_name && !link && !place) return null;
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
      {part.source_name &&
        (link ? (
          <a className={CHIP} href={link} target="_blank" rel="noopener noreferrer">
            {part.source_name} <span aria-hidden="true">↗</span>
            <span className="sr-only"> (opens in a new tab)</span>
          </a>
        ) : (
          <span className="rounded border border-line px-1.5 py-0.5 text-xs text-muted">{part.source_name}</span>
        ))}
      {place && onFlyTo && (
        <button type="button" className={CHIP} onClick={() => onFlyTo(place.target)}>
          {place.label}
        </button>
      )}
    </div>
  );
}

export function ChatAnswerParts({ parts, siteBbl, cases, onFlyTo }: Props) {
  return (
    <ul className="space-y-2">
      {parts.map((part, index) => {
        const look = PART_KINDS[part.kind] ?? PART_KINDS.notice;
        if (part.kind === "notice") {
          return (
            <li key={index} className="text-xs leading-snug text-muted">
              {part.text}
            </li>
          );
        }
        return (
          <li key={index} className={`border-l-2 pl-2.5 ${look.tone}`}>
            <p className="text-[0.7rem] font-semibold uppercase tracking-wide">{look.label}</p>
            <p className="mt-0.5 whitespace-pre-wrap text-sm leading-snug text-text">{part.text}</p>
            <SourceChips part={part} siteBbl={siteBbl} cases={cases} onFlyTo={onFlyTo} />
          </li>
        );
      })}
    </ul>
  );
}
