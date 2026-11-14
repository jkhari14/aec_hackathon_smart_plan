import type { Brief } from "../../brief/brief_types";

export function PrecedentList({ precedents }: { precedents: Brief["precedents"] }) {
  if (precedents.length === 0) {
    return <p className="text-sm text-gap">No precedents loaded yet. The precedent library fills this.</p>;
  }
  return (
    <ul className="space-y-2">
      {precedents.map((p) => (
        <li key={p.id} className="rounded border bg-white p-2 text-sm">
          <p className="font-semibold">{p.title} <span className="text-xs text-stone-500">{p.date}</span></p>
          <p>{p.summary}</p>
          {p.cause_as_publicly_reported && <p className="text-xs">As publicly reported: {p.cause_as_publicly_reported}</p>}
        </li>
      ))}
    </ul>
  );
}
