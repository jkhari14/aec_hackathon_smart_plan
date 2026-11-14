import type { ProjectType } from "../../brief/brief_types";
import type { AnswerPart, ChatAnswer, ChatSetup, Exchange } from "./chat_types";

// Saved answers written by `python -m jahleel.api.chat.chat_saved_export`, one file per site and
// as-of day. They are what the API returns for each saved example, so the panel works with no API.
const SAVED = import.meta.glob<ChatAnswer[]>("./saved/*.json", { eager: true, import: "default" });

const OFFLINE_LIMITS = { max_question_chars: 1000, max_earlier_exchanges: 8, max_history_chars: 12000 };

export type Site = { slug: string; projectType: ProjectType; asOf: string | null };

// Only a copy saved for this exact as-of day: an as-pulled copy would show later records in a replay.
export function savedAnswers(site: Site): ChatAnswer[] {
  const name = site.asOf ? `${site.slug}.as-of-${site.asOf}` : site.slug;
  return SAVED[`./saved/${name}.json`] ?? [];
}

// null when the chat routes cannot be reached (API down, or the routes not mounted yet).
export async function loadChatSetup(slug: string): Promise<ChatSetup | null> {
  try {
    const response = await fetch(`/api/chat/setup/${encodeURIComponent(slug)}`);
    return response.ok ? ((await response.json()) as ChatSetup) : null;
  } catch {
    return null;
  }
}

export function offlineSetup(site: Site): ChatSetup {
  const examples = savedAnswers(site).map((answer, index) => ({ id: String(index), question: answer.question }));
  return { live: false, examples, ...OFFLINE_LIMITS };
}

// What goes back to the model as an earlier answer: the sourced parts, without the server's notices.
export function answerText(parts: AnswerPart[]): string {
  return parts.filter((part) => part.kind !== "notice").map((part) => part.text).join("\n");
}

export function historyOf(exchanges: Exchange[]) {
  return exchanges.map((exchange) => ({ question: exchange.question, answer: answerText(exchange.answer.parts) }));
}

// Why another question cannot be sent, or null. The server refuses over these limits; it never cuts.
export function chatIsFull(exchanges: Exchange[], setup: ChatSetup): string | null {
  const history = historyOf(exchanges);
  const size = history.reduce((sum, turn) => sum + turn.question.length + turn.answer.length, 0);
  const tooLong = history.some((turn) => turn.answer.length > 4000);
  if (history.length >= setup.max_earlier_exchanges || size > setup.max_history_chars - 1500 || tooLong) {
    return "This chat has reached its length limit. Start a new chat to keep asking.";
  }
  return null;
}

type Ask = { question?: string; exampleId?: string; exchanges: Exchange[] };

export async function askChat(site: Site, ask: Ask): Promise<ChatAnswer> {
  let response: Response;
  try {
    response = await fetch("/api/chat/answer", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        slug: site.slug,
        project_type: site.projectType,
        as_of: site.asOf,
        history: ask.exampleId ? [] : historyOf(ask.exchanges),
        question: ask.question ?? "",
        example_id: ask.exampleId ?? null,
      }),
    });
  } catch {
    throw new Error("The API did not answer. Saved examples still work.");
  }
  if (response.status === 429) throw new Error("Too many live questions this minute. Wait a moment and ask again.");
  if (response.status === 422) throw new Error("That question or this chat is over the size limit, so it was not sent on.");
  if (!response.ok) throw new Error(`The chat could not answer (HTTP ${response.status}).`);
  return (await response.json()) as ChatAnswer;
}
