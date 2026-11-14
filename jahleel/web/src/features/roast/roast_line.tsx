import type { ChecklistRow } from "../../brief/brief_types";
import type { RoastIntensity } from "./roast_dial";

// On a life-safety row the serious line comes first and the roast second.
// `intensity` is wired for the roast writer: the brief carries one line per row today.
export function RoastLine({ row }: { row: ChecklistRow; intensity: RoastIntensity }) {
  if (!row.roast) return null;
  const serious = <p className="text-sm">{row.roast.serious}</p>;
  const roast = <p className="text-sm italic text-stone-600">“{row.roast.line}”</p>;
  return <div className="mt-1 space-y-0.5">{row.life_safety ? <>{serious}{roast}</> : <>{roast}{serious}</>}</div>;
}
