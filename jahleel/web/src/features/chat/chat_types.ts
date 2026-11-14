// The chat API's shapes (jahleel/api/chat/chat_models.py), written by hand until the chat routes are in
// openapi.json; after that `npm run types` generates them and these can become aliases.

export type BriefSource = {
  type: "public_record" | "requirement" | "lot_facts" | "dataset_count";
  ref: string;
  label: string;
  detail: string | null;
  date: string | null;
  bbl: string | null;
  url: string | null;
};

export type ReportedSource = {
  type: "reported_document";
  ref: string;
  reported_by: string;
  document: string;
  url: string | null;
  reported_on: string | null;
  document_date: string | null;
};

export type WebSource = { type: "web_result"; url: string; title: string; page_age: string | null; official: boolean };

export type QueriedDataset = { key: string; name: string; bbl: string | null; url: string | null };

// A part's kind says where it came from. The server chooses it from what the statement cites.
export type AnswerPart =
  | { kind: "record"; text: string; sources: BriefSource[] }
  | { kind: "lead"; text: string; sources: (WebSource | ReportedSource)[] }
  | { kind: "not_found"; text: string; queried: QueriedDataset[] }
  | { kind: "unknown"; text: string; queried: QueriedDataset[] }
  | { kind: "notice"; code: string; text: string };

export type ExampleQuestion = { id: string; question: string };

export type ChatAnswer = {
  mode: "live" | "saved" | "mock";
  question: string;
  parts: AnswerPart[];
  plain_text: string;
  as_of: string | null;
  web_search: "used" | "not_used" | "off_as_of" | "off";
  examples: ExampleQuestion[];
  usage: { model: string; input_tokens: number; output_tokens: number; web_searches: number } | null;
};

export type ChatSetup = {
  live: boolean;
  examples: ExampleQuestion[];
  max_question_chars: number;
  max_earlier_exchanges: number;
  max_history_chars: number;
};

export type Exchange = { question: string; answer: ChatAnswer };
