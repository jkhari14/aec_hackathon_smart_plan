// What the chat asks the page to do beside showing an answer: move the map, show or hide a layer, pin
// an answer to the project. The chat only asks. The page (the map, the layer panel, the project panel)
// does the work through the handlers it passes in, and anything it cannot do is said, never dropped.
import type { Case, ChatResponse } from "../../contracts";
import { answerText, type ChatPart } from "./chat_part_kinds";

export type ChatAction = ChatResponse["actions"][number];

/** Where to move the map. At least one of `bbl` or `lat` and `lon` is set. */
export type FlyTarget = { ref?: string; label?: string; bbl?: string; lat?: number; lon?: number };

/** A chat answer to save on the project, exactly as the reader saw it. */
export type ChatPinDraft = {
  title: string;
  question: string;
  as_of: string | null;
  offline: boolean;
  answer_parts: ChatPart[];
  text: string;
};

export type ChatPageHandlers = {
  onFlyTo?: (target: FlyTarget) => void;
  onToggleLayer?: (layerId: string, on: boolean) => void;
  /** Rejects with an Error whose message can be shown when the pin was not saved. */
  onPin?: (pin: ChatPinDraft) => void | Promise<void>;
};

export function pinDraft(question: string, response: ChatResponse, asOf: string | null): ChatPinDraft {
  return {
    title: question.slice(0, 120),
    question,
    as_of: asOf,
    offline: response.offline,
    answer_parts: response.answer_parts,
    text: answerText(response.answer_parts),
  };
}

const text = (value: unknown): string | undefined => (typeof value === "string" && value ? value : undefined);
const number = (value: unknown): number | undefined => (typeof value === "number" && Number.isFinite(value) ? value : undefined);

function flyTargetFrom(payload: ChatAction["payload"]): FlyTarget | null {
  const target: FlyTarget = {
    ref: text(payload.ref),
    label: text(payload.label),
    bbl: text(payload.bbl),
    lat: number(payload.lat),
    lon: number(payload.lon),
  };
  return target.bbl || (target.lat !== undefined && target.lon !== undefined) ? target : null;
}

/**
 * Carries out an answer's actions in order. `pinTarget` says which answer a pin action means:
 * "this" one, or the "previous" one the reader saw. Returns a line for each action not carried out.
 */
export function carryOutActions(
  actions: ChatAction[],
  handlers: ChatPageHandlers,
  pinTarget: (target: "this" | "previous") => ChatPinDraft | null,
  pinFailed: (reason: string) => void,
): string[] {
  const notDone: string[] = [];
  for (const action of actions) {
    if (action.type === "toggle_layer") {
      const layerId = text(action.payload.layer_id);
      if (layerId && typeof action.payload.on === "boolean" && handlers.onToggleLayer) {
        handlers.onToggleLayer(layerId, action.payload.on);
      } else {
        notDone.push("This page could not change the map layer.");
      }
    } else if (action.type === "fly_to") {
      const target = flyTargetFrom(action.payload);
      if (target && handlers.onFlyTo) handlers.onFlyTo(target);
      else notDone.push("This page could not move the map.");
    } else {
      const draft = pinTarget(action.payload.target === "previous" ? "previous" : "this");
      if (!draft || !handlers.onPin) {
        notDone.push("The answer was not pinned: no project is open on this page.");
      } else {
        Promise.resolve(handlers.onPin(draft)).catch((error: unknown) =>
          pinFailed(error instanceof Error ? error.message : "the project could not be reached"),
        );
      }
    }
  }
  return notDone;
}

/**
 * Where a part's source chip moves the map, or null when the part is not about a place.
 * A past case goes to the case; a lot's facts or counts go to that lot; a single record goes to the
 * site, since an answer part does not carry the record's own lot.
 */
export function flyTargetForPart(part: ChatPart, siteBbl: string, cases: Case[]): { target: FlyTarget; label: string } | null {
  const id = part.record_id;
  if (!id) return null;
  if (part.kind === "case") {
    const found = cases.find((item) => item.id === id);
    return found
      ? { target: { ref: `case:${id}`, label: found.title, bbl: found.bbl ?? undefined, lat: found.lat, lon: found.lon }, label: "Show the case on the map" }
      : null;
  }
  if (part.kind === "public_record") {
    const lot = /^(?:site|neighbor|dataset):(\d{10})(?::|$)/.exec(id);
    if (lot) return { target: { ref: id, bbl: lot[1] }, label: lot[1] === siteBbl ? "Show the site on the map" : "Show this lot on the map" };
    return { target: { ref: id, bbl: siteBbl }, label: "Show the site on the map" };
  }
  if (part.kind === "warning") return { target: { ref: `warning:${id}`, bbl: siteBbl }, label: "Show the site on the map" };
  return null;
}
