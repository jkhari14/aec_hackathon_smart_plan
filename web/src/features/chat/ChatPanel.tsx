// The docked chat: questions about one site, answered in parts that each say where they came from.
// The panel keeps the conversation and asks the page to act (move the map, show a layer, pin an answer)
// through the handlers it is given. See README.md for how the shell mounts it.
import { useEffect, useId, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { api } from "../../api/client";
import type { Case, ChatRequest, ChatResponse } from "../../contracts";
import { ChatAnswerParts } from "./ChatAnswerParts";
import { askChat, DEFAULT_CHAT_SETUP, loadChatSetup, type ChatSetup } from "./chat_client";
import { historyFor, isAnswered, type Exchange } from "./chat_conversation";
import { carryOutActions, pinDraft, type ChatPageHandlers } from "./chat_page_actions";
import { EXAMPLE_QUESTIONS, savedAnswersFor, savedAnswerTo } from "./chat_saved_answers";

export type ChatPanelProps = ChatPageHandlers & {
  /** The site the chat is about; null until one is picked on the map. */
  bbl: string | null;
  siteLabel?: string;
  /** The open project, if any: answers can be pinned to it. */
  projectId?: string | null;
  /** The page's as-of day (YYYY-MM-DD), when it is replaying an earlier date. */
  asOf?: string | null;
  jobType?: ChatRequest["job_type"];
  stage?: ChatRequest["stage"];
  defaultOpen?: boolean;
  /** Where the panel sits; the default docks it bottom right over the map. */
  className?: string;
};

type PinState = { state: "saving" } | { state: "pinned" } | { state: "failed"; reason: string };

const DOCKED = "absolute bottom-4 right-4 z-10 w-[26rem] max-w-[calc(100vw-2rem)]";
const BUTTON = "rounded border border-line px-2 py-1 text-xs hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 disabled:cursor-not-allowed disabled:opacity-50";

export function ChatPanel(props: ChatPanelProps) {
  const { bbl, siteLabel, projectId = null, asOf = null, jobType = null, stage = null, onFlyTo, onPin } = props;
  const [open, setOpen] = useState(props.defaultOpen ?? true);
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [draft, setDraft] = useState("");
  const [setup, setSetup] = useState<ChatSetup>(DEFAULT_CHAT_SETUP);
  const [cases, setCases] = useState<Case[]>([]);
  const [pins, setPins] = useState<Record<number, PinState>>({});
  const nextId = useRef(1);
  const inFlight = useRef<AbortController | null>(null);
  const logEnd = useRef<HTMLDivElement | null>(null);
  const inputId = useId();
  const waiting = exchanges.some((exchange) => exchange.outcome.state === "waiting");

  useEffect(() => {
    const stop = new AbortController();
    loadChatSetup(stop.signal).then((loaded) => loaded && setSetup(loaded));
    api.cases().then((result) => setCases(result.data));
    return () => stop.abort();
  }, []);

  // A conversation is about one site on one day. Answers from today's view must never be sent as
  // context to a question about an earlier date, so a change of either starts a new conversation.
  useEffect(() => {
    inFlight.current?.abort();
    setExchanges([]);
    setPins({});
  }, [bbl, asOf]);

  useEffect(() => {
    logEnd.current?.scrollIntoView({ block: "end" });
  }, [exchanges]);

  const settle = (id: number, outcome: Exchange["outcome"]) =>
    setExchanges((current) => current.map((exchange) => (exchange.id === id ? { ...exchange, outcome } : exchange)));

  function pin(id: number, question: string, response: ChatResponse) {
    if (!onPin) return;
    setPins((current) => ({ ...current, [id]: { state: "saving" } }));
    Promise.resolve()
      .then(() => onPin(pinDraft(question, response, asOf)))
      .then(() => setPins((current) => ({ ...current, [id]: { state: "pinned" } })))
      .catch((error: unknown) =>
        setPins((current) => ({
          ...current,
          [id]: { state: "failed", reason: error instanceof Error ? error.message : "the project could not be reached" },
        })),
      );
  }

  function answered(id: number, question: string, response: ChatResponse, sample: boolean, saved: boolean, earlier: Exchange[]) {
    const previous = earlier.filter(isAnswered).at(-1);
    const notDone = carryOutActions(
      response.actions,
      { onFlyTo, onToggleLayer: props.onToggleLayer, onPin: projectId ? onPin : undefined },
      (target) =>
        target === "this"
          ? pinDraft(question, response, asOf)
          : previous
            ? pinDraft(previous.question, previous.outcome.response, asOf)
            : null,
      (reason) => setPins((current) => ({ ...current, [id]: { state: "failed", reason } })),
    );
    settle(id, { state: "answered", response, sample, saved, notDone });
  }

  async function ask(question: string) {
    const asked = question.trim();
    if (!asked || !bbl || waiting) return;
    const id = nextId.current++;
    const earlier = exchanges;
    setExchanges([...earlier, { id, question: asked, outcome: { state: "waiting" } }]);
    setDraft("");
    const stop = new AbortController();
    inFlight.current = stop;
    try {
      const result = await askChat(
        { question: asked, bbl, project_id: projectId, as_of: asOf, job_type: jobType, stage, history: historyFor(earlier, setup) },
        stop.signal,
      );
      if (stop.signal.aborted) return; // the site or the day changed: this answer belongs to no conversation
      if (result.status === "answered") return answered(id, asked, result.response, result.sample, false, earlier);
      if (result.status === "refused") return settle(id, { state: "refused", reason: result.reason });
      const saved = savedAnswerTo(asked, bbl, asOf);
      if (saved) return answered(id, asked, saved.response, true, true, earlier);
      settle(id, { state: "unreachable" });
    } catch {
      // The site or the as-of day changed while waiting: the conversation was already cleared.
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void ask(draft);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void ask(draft);
    }
  }

  const overCap = draft.length > setup.max_question_chars;
  const whyDisabled = !bbl
    ? "Pick a site on the map first: the chat answers about one site at a time."
    : waiting
      ? "Waiting for the answer to your last question."
      : overCap
        ? `A question is at most ${setup.max_question_chars} characters.`
        : null;
  const savedHere = savedAnswersFor(bbl, asOf);

  return (
    <section aria-label="Chat about this site" className={`${props.className ?? DOCKED} flex flex-col rounded-lg border border-line bg-panel/95 text-text shadow-lg backdrop-blur`}>
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-left hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
      >
        <span className="min-w-0">
          <span className="block text-sm font-semibold">Ask about this site</span>
          <span className="block truncate text-xs text-muted">
            {bbl ? (siteLabel ?? `Lot ${bbl}`) : "No site picked"}
            {asOf ? ` · as of ${asOf}` : ""}
            {setup.live ? "" : " · offline answers"}
          </span>
        </span>
        <span aria-hidden="true" className="text-muted">{open ? "–" : "+"}</span>
      </button>

      {open && (
        <>
          <div role="log" aria-live="polite" aria-label="Questions and answers" className="max-h-[50vh] space-y-4 overflow-y-auto border-t border-line px-3 py-3">
            {exchanges.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-muted">
                  {bbl
                    ? "Ask about this site's public records, similar past cases, early warnings and action items. Every part of an answer shows where it came from."
                    : "Pick a site on the map first: the chat answers about one site at a time."}
                </p>
                {bbl && (
                  <div className="flex flex-wrap gap-1.5">
                    {EXAMPLE_QUESTIONS.slice(0, 4).map((question) => (
                      <button key={question} type="button" className={BUTTON} onClick={() => void ask(question)}>
                        {question}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {exchanges.map((exchange) => {
              const outcome = exchange.outcome;
              const pinState = pins[exchange.id];
              return (
                <article key={exchange.id} className="space-y-2">
                  <p className="ml-8 rounded-md bg-white/10 px-2.5 py-1.5 text-sm">
                    <span className="sr-only">You asked: </span>
                    {exchange.question}
                  </p>
                  {outcome.state === "waiting" && <p className="text-sm text-muted">Looking this up…</p>}
                  {outcome.state === "refused" && (
                    <p className="border-l-2 border-red-400/70 pl-2.5 text-sm">Not answered: {outcome.reason}</p>
                  )}
                  {outcome.state === "unreachable" && (
                    <div className="space-y-2 border-l-2 border-red-400/70 pl-2.5 text-sm">
                      <p>The chat server could not be reached, so this question was not answered.</p>
                      {savedHere.length > 0 && (
                        <>
                          <p className="text-xs text-muted">Answers saved ahead of time for this site:</p>
                          <div className="flex flex-wrap gap-1.5">
                            {savedHere.map((saved) => (
                              <button key={saved.id} type="button" className={BUTTON} disabled={waiting} onClick={() => void ask(saved.question)}>
                                {saved.question}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  {outcome.state === "answered" && bbl && (
                    <>
                      <ChatAnswerParts parts={outcome.response.answer_parts} siteBbl={bbl} cases={cases} onFlyTo={onFlyTo} />
                      {outcome.notDone.map((line) => (
                        <p key={line} className="text-xs text-amber-300">{line}</p>
                      ))}
                      <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted">
                        {outcome.saved && <span className="rounded bg-white/10 px-1.5 py-0.5">Saved answer: the chat server could not be reached</span>}
                        {!outcome.saved && outcome.response.offline && <span className="rounded bg-white/10 px-1.5 py-0.5">Offline answer: no model was called</span>}
                        {outcome.sample && <span className="rounded bg-sample/15 px-1.5 py-0.5 font-medium text-sample">Sample data</span>}
                        {onPin && projectId && outcome.response.answer_parts.some((part) => part.kind !== "notice") && (
                          <button
                            type="button"
                            className={BUTTON}
                            disabled={pinState?.state === "saving" || pinState?.state === "pinned"}
                            onClick={() => pin(exchange.id, exchange.question, outcome.response)}
                          >
                            {pinState?.state === "pinned" ? "Pinned to the project" : pinState?.state === "saving" ? "Pinning…" : "Pin to the project"}
                          </button>
                        )}
                        {pinState?.state === "failed" && <span className="text-red-300">Not pinned: {pinState.reason}</span>}
                      </div>
                    </>
                  )}
                </article>
              );
            })}
            <div ref={logEnd} />
          </div>

          <form onSubmit={submit} className="space-y-1.5 border-t border-line px-3 py-2">
            <label htmlFor={inputId} className="sr-only">Your question about this site</label>
            <div className="flex items-end gap-2">
              <textarea
                id={inputId}
                rows={2}
                value={draft}
                disabled={!bbl}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onKeyDown}
                placeholder={bbl ? "Ask a question about this site" : "Pick a site on the map first"}
                className="min-h-0 flex-1 resize-none rounded border border-line bg-night px-2 py-1.5 text-sm placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 disabled:opacity-50"
              />
              <button type="submit" className={`${BUTTON} px-3 py-1.5 text-sm font-medium`} disabled={whyDisabled !== null || !draft.trim()}>
                Ask
              </button>
            </div>
            {whyDisabled && bbl && <p className="text-xs text-amber-300">{whyDisabled}</p>}
            <p className="text-[0.7rem] leading-snug text-muted">
              Public records, reported cases and rule results only. Not a DOB determination or engineering advice. Names of
              owners, applicants and contractors are left out.
            </p>
          </form>
        </>
      )}
    </section>
  );
}
