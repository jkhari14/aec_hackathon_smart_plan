// A chat answer as a project pin. The body is the answer as the reader saw it, each part led by the
// label of where it came from, so a pinned answer can never be shown without its sources' labels.
import type { ChatPinDraft } from "../chat/chat_page_actions";
import type { PinCreate, Role } from "./project_client";

export const MAX_PIN_BODY_CHARS = 8000;

function shortHash(text: string): string {
  let hash = 5381;
  for (let index = 0; index < text.length; index++) hash = ((hash << 5) + hash + text.charCodeAt(index)) >>> 0;
  return hash.toString(36);
}

/** Throws an Error to show the reader when the answer cannot be pinned as it is. */
export function chatAnswerPin(draft: ChatPinDraft, role: Role): PinCreate {
  const heading = [
    `Chat answer to: ${draft.question}`,
    draft.as_of ? `Site data as of ${draft.as_of}.` : null,
    draft.offline ? "Offline answer: no model was called." : null,
  ].filter(Boolean);
  const body = `${heading.join("\n")}\n\n${draft.text}`;
  if (body.length > MAX_PIN_BODY_CHARS) throw new Error(`this answer is over ${MAX_PIN_BODY_CHARS} characters, too long to pin`);
  return { kind: "chat_answer", ref_id: `chat-${shortHash(body)}`, title: draft.title, by_role: role, body };
}
