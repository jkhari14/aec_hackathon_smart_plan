// Answers written ahead of time for the sample site, shown only when the API cannot be reached.
// chat_saved_answers.json is generated (python -m api.routers.chat.chat_saved_answers_export); never edit it.
import type { ChatResponse } from "../../contracts";

import savedFile from "./chat_saved_answers.json";

export type SavedAnswer = { id: string; question: string; response: ChatResponse };

const saved = savedFile as unknown as { site_bbl: string; answers: SavedAnswer[] };

const plain = (question: string) => question.trim().toLowerCase().replace(/[?.!\s]+$/, "");

/** Saved answers describe the site as it is on file today, so an as-of view gets none. */
export function savedAnswersFor(bbl: string | null, asOf: string | null): SavedAnswer[] {
  return bbl === saved.site_bbl && !asOf ? saved.answers : [];
}

export function savedAnswerTo(question: string, bbl: string | null, asOf: string | null): SavedAnswer | null {
  return savedAnswersFor(bbl, asOf).find((answer) => plain(answer.question) === plain(question)) ?? null;
}

export const EXAMPLE_QUESTIONS: string[] = saved.answers.map((answer) => answer.question);
