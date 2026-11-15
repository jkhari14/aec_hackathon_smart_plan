// What each kind of answer part is called on screen. The kind comes from the server, which derives it
// from what the part rests on; the page never picks or changes one.
// The tone classes are placeholders until the design system's source label lands (web/src/design/, PR 1).
import type { ChatResponse } from "../../contracts";

export type ChatPart = ChatResponse["answer_parts"][number];
export type ChatPartKind = ChatPart["kind"];

type KindLook = { label: string; tone: string };

export const PART_KINDS: Record<ChatPartKind, KindLook> = {
  public_record: { label: "Public record", tone: "border-sky-400/60 text-sky-300" },
  case: { label: "Past case, as publicly reported", tone: "border-violet-400/60 text-violet-300" },
  warning: { label: "Early warning: a pattern, not a prediction", tone: "border-amber-400/60 text-amber-300" },
  action: { label: "Action item: a prompt to act, not a determination", tone: "border-emerald-400/60 text-emerald-300" },
  ai_suggestion: { label: "AI suggestion, not from a record", tone: "border-fuchsia-400/60 text-fuchsia-300" },
  web: { label: "From the web, not checked by us", tone: "border-dashed border-orange-400/60 text-orange-300" },
  user_input: { label: "From what you entered", tone: "border-teal-400/60 text-teal-300" },
  not_found: { label: "Looked for, none found", tone: "border-slate-400/60 text-slate-300" },
  unknown: { label: "Could not load: this is not zero", tone: "border-red-400/70 text-red-300" },
  notice: { label: "Note", tone: "border-transparent text-muted" },
};

/** The answer as one text, each part led by where it came from: what a follow-up question sends back. */
export function answerText(parts: ChatPart[]): string {
  return parts.map((part) => (part.kind === "notice" ? part.text : `${PART_KINDS[part.kind].label}: ${part.text}`)).join("\n");
}

/** Only http and https links are shown as links. */
export function safeLink(url: string | null | undefined): string | null {
  return url && /^https?:\/\//i.test(url) ? url : null;
}
