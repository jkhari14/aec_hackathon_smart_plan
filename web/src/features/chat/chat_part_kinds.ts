// What each kind of answer part is called on screen. The kind comes from the server, which derives it
// from what the part rests on; the page never picks or changes one.
// The tones are the design system's colours (web/src/design/tokens.css), so they follow the theme.
import type { ChatResponse } from "../../contracts";

export type ChatPart = ChatResponse["answer_parts"][number];
export type ChatPartKind = ChatPart["kind"];

type KindLook = { label: string; tone: string };

export const PART_KINDS: Record<ChatPartKind, KindLook> = {
  public_record: { label: "Public record", tone: "border-[color:var(--fs-src-record)] text-[color:var(--fs-src-record)]" },
  case: { label: "Past case, as publicly reported", tone: "border-[color:var(--fs-accent)] text-[color:var(--fs-accent)]" },
  warning: { label: "Early warning: a pattern, not a prediction", tone: "border-[color:var(--fs-sample)] text-[color:var(--fs-sample)]" },
  action: { label: "Action item: a prompt to act, not a determination", tone: "border-[color:var(--fs-text-2)] text-[color:var(--fs-text-2)]" },
  ai_suggestion: { label: "AI suggestion, not from a record", tone: "border-[color:var(--fs-src-ai)] text-[color:var(--fs-src-ai)]" },
  web: { label: "From the web, not checked by us", tone: "border-dashed border-[color:var(--fs-muted)] text-[color:var(--fs-muted)]" },
  user_input: { label: "From what you entered", tone: "border-[color:var(--fs-src-user)] text-[color:var(--fs-src-user)]" },
  not_found: { label: "Looked for, none found", tone: "border-[color:var(--fs-muted)] text-[color:var(--fs-muted)]" },
  unknown: { label: "Could not load: this is not zero", tone: "border-[color:var(--fs-error)] text-[color:var(--fs-error)]" },
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
