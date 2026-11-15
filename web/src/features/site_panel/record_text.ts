// Turns a signal's raw record text (inspector notes arrive in capitals, one long run-on) into a few short
// plain lines. Only case and abbreviations change: the record's own words and order are kept.

const ACRONYMS = /\b(dob|ecb|hpd|nyc|nycbc|bc|ac|swo|osha|sro|pw\d?|tpp|soe|bin|bbl)\b/gi;
const LEAD_INS = /^(at (the )?time of (inspection|insp\.?)[^:]*:\s*|observed:\s*|re:\s*)/i;
const CODE = /\s*,?\s*(?:contrary to|contra|in violation of|violation of)?\s*\b(?:nyc\s*)?(bc|ac|nycbc)\s*(§\s*)?(\d[\d.\-]*\d)/gi;

function sentenceCase(text: string): string {
  const lower = text.toLowerCase().replace(ACRONYMS, (m) => m.toUpperCase());
  return lower.replace(/(^|[.!?]\s+)([a-z])/g, (_, a: string, b: string) => a + b.toUpperCase());
}

export type RecordText = { lines: string[]; codes: string[] };

/** 'The X record says: "…"' -> the quote as short lines, plus any code sections it cites. Null if not a quote. */
export function readRecordQuote(explanation: string): RecordText | null {
  const match = /^The .+? record says: "([\s\S]*)"$/.exec(explanation.trim());
  if (!match) return null;
  let text = match[1].trim();
  const codes: string[] = [];
  text = text.replace(CODE, (_m, kind: string, _s, section: string) => {
    const name = kind.toUpperCase() === "AC" ? "Administrative Code" : "Building Code";
    const label = `${name} ${section}`;
    if (!codes.includes(label)) codes.push(label);
    return "";
  });
  text = text.replace(LEAD_INS, "");
  const shouty = text === text.toUpperCase();
  const lines = text
    .split(/(?<=[.;])\s+|:\s+/)
    .map((s) => s.replace(/[\s,;:]+$/, "").replace(/\.$/, "").trim())
    .filter((s) => s.length > 2)
    .map((s) => (shouty ? sentenceCase(s) : s))
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1));
  return { lines, codes };
}

/** "dob_complaints:123" -> "123" (the source name is shown next to it). */
export const recordNumber = (id: string) => id.split(":").slice(1).join(":") || id;
