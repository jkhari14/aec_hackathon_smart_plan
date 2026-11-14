import { useEffect, useState } from "react";

import type { Brief, ProjectType } from "../../brief/brief_types";
import { ChatAnswerParts } from "./chat_answer_parts";
import { askChat, chatIsFull, loadChatSetup, offlineSetup, savedAnswers, type Site } from "./chat_api";
import type { ChatSetup, Exchange } from "./chat_types";

type Props = { brief: Brief; projectType: ProjectType; asOf: string | null; offline: boolean };

// The conversation lives in this browser tab only (sessionStorage), one per site, project type and as-of day.
function storageKey(site: Site) {
  return `preflight-chat:${site.slug}:${site.projectType}:${site.asOf ?? "as-pulled"}`;
}

function readStored(site: Site): Exchange[] {
  try {
    return JSON.parse(window.sessionStorage.getItem(storageKey(site)) ?? "[]") as Exchange[];
  } catch {
    return [];
  }
}

const WEB_LINE: Record<string, string> = {
  used: "Web search was used for this answer.",
  not_used: "Answered from the brief; no web search was run.",
  off_as_of: "",
  off: "",
};

export function ChatPanel({ brief, projectType, asOf, offline }: Props) {
  const site: Site = { slug: brief.slug, projectType, asOf };
  const key = storageKey(site);
  const [setup, setSetup] = useState<ChatSetup | null>(null);
  const [apiUp, setApiUp] = useState(false);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [question, setQuestion] = useState("");
  const [waiting, setWaiting] = useState<"saved" | "live" | null>(null);
  const [error, setError] = useState<string | null>(null);

  // A new site, project type or as-of day is a new conversation: answers from one view never carry into another.
  useEffect(() => {
    let current = true;
    setExchanges(readStored(site));
    setError(null);
    setSetup(null);
    (offline ? Promise.resolve(null) : loadChatSetup(site.slug)).then((loaded) => {
      if (!current) return;
      setApiUp(loaded != null);
      setSetup(loaded ?? offlineSetup(site));
    });
    return () => { current = false; };
  }, [key, offline]);

  function keep(next: Exchange[]) {
    setExchanges(next);
    try {
      window.sessionStorage.setItem(key, JSON.stringify(next));
    } catch {
      // storage full or blocked: the chat still works for this page view
    }
  }

  async function ask(input: { question?: string; exampleId?: string }) {
    setError(null);
    if (!apiUp && input.exampleId != null) {
      const saved = savedAnswers(site)[Number(input.exampleId)];
      if (saved) keep([...exchanges, { question: saved.question, answer: saved }]);
      return;
    }
    setWaiting(input.exampleId != null ? "saved" : "live");
    try {
      const answer = await askChat(site, { ...input, exchanges });
      keep([...exchanges, { question: answer.question, answer }]);
      setQuestion("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setWaiting(null);
    }
  }

  const full = setup ? chatIsFull(exchanges, setup) : null;
  // A disabled box always says why.
  const whyDisabled = !setup ? "Checking whether live answers are available…"
    : !apiUp ? "Typed questions need the API running. The saved examples above work offline."
    : full;
  // Mock mode: the API is up with no model key, so a typed question gets a prepared answer and no model runs.
  const mock = setup != null && apiUp && !setup.live;
  const examples = setup?.examples ?? [];

  return (
    <section className="rounded border bg-stone-50 p-3" aria-label="Ask about this site">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="font-semibold">Ask about this site</h2>
        {exchanges.length > 0 && (
          <button className="text-xs underline" onClick={() => { keep([]); setError(null); }}>New chat</button>
        )}
      </div>
      <p className="text-xs text-stone-600">
        Answers rest on the brief on this page{asOf ? ` (records dated before ${asOf})` : ""}
        {mock ? "" : " and, outside an as-of view, on web search"}. Each part shows where it came from. A coordination aid, not a compliance or safety
        determination.
      </p>

      <div className="mt-2 max-h-[32rem] space-y-3 overflow-y-auto pr-1" aria-live="polite">
        {exchanges.map((exchange, index) => (
          <div key={index}>
            <p className="text-sm font-semibold">{exchange.question}</p>
            <ChatAnswerParts parts={exchange.answer.parts} />
            {exchange.answer.mode === "live" && WEB_LINE[exchange.answer.web_search] && (
              <p className="mt-1 text-xs text-stone-500">{WEB_LINE[exchange.answer.web_search]}</p>
            )}
          </div>
        ))}
        {waiting && (
          <p className="text-sm text-stone-600">
            {waiting === "saved" ? "Checking the saved example against the brief…"
              : mock ? "Matching the question to a prepared answer…"
              : `Reading the brief${asOf ? "" : " and searching the web"}…`}
          </p>
        )}
        {error && <p className="bg-red-100 px-2 py-1 text-xs">{error}</p>}
      </div>

      {examples.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          <span className="text-xs text-stone-600">{apiUp ? "Saved examples:" : "Saved examples (these work offline):"}</span>
          {examples.map((example) => (
            <button key={example.id} disabled={waiting != null} onClick={() => ask({ exampleId: example.id })}
              className="rounded border border-lead bg-white px-2 py-0.5 text-left text-xs">
              {example.question}
            </button>
          ))}
        </div>
      )}
      {setup && !apiUp && examples.length === 0 && (
        <p className="mt-2 text-xs text-stone-600">No saved examples for this site and date offline.</p>
      )}

      <form className="mt-2 flex gap-2" onSubmit={(e) => { e.preventDefault(); if (question.trim()) void ask({ question }); }}>
        <label className="sr-only" htmlFor="chat-question">Your question</label>
        <input id="chat-question" className="min-w-0 flex-1 rounded border px-2 py-1 text-sm disabled:bg-stone-100"
          value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={setup?.max_question_chars ?? 1000}
          disabled={whyDisabled != null || waiting != null} placeholder="Ask what the record shows, or what a duty needs" />
        <button className="rounded bg-ink px-3 py-1 text-sm text-white disabled:opacity-40"
          disabled={whyDisabled != null || waiting != null || !question.trim()}>Ask</button>
      </form>
      {whyDisabled && <p className="mt-1 text-xs text-stone-600">{whyDisabled}</p>}
      {mock && !whyDisabled && (
        <p className="mt-1 text-xs text-stone-600">
          <span className="font-semibold">Mock mode:</span> the server has no model key, so no model is called and
          there is no web search. A typed question is matched by keyword to a prepared answer built from this brief:
          try "how many ECB violations", "which duties apply" or "what are the open gaps".
        </p>
      )}
    </section>
  );
}
