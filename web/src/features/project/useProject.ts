// One project, kept in step with the store: a tab polls it so the other role's work shows up, and
// every write returns the whole project. The shell calls this once and hands the result to the
// project panel; `pinChatAnswer` is what it passes to the chat panel's `onPin`.
import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "../../api/client";
import type { Project, ProjectCreate } from "../../contracts";
import type { ChatPinDraft } from "../chat/chat_page_actions";
import { projectWrites, readProject, whyNotSaved, type ActionItemUpdate, type ProjectWrite, type Role } from "./project_client";
import { chatAnswerPin } from "./project_pins";

const POLL_MS = 4000;

export type ProjectState =
  | { status: "none" } // no project is open
  | { status: "loading" }
  | { status: "ok"; project: Project; sample: boolean }
  | { status: "not_found" }
  | { status: "unreachable" };

export type ProjectWorkspace = {
  projectId: string | null;
  state: ProjectState;
  role: Role;
  setRole: (role: Role) => void;
  /** Each write rejects with an Error whose message says why nothing was saved. */
  updateItem: (update: ActionItemUpdate) => Promise<void>;
  addSiteActionItems: () => Promise<void>;
  addNote: (text: string) => Promise<void>;
  pinChatAnswer: (draft: ChatPinDraft) => Promise<void>;
  create: (body: ProjectCreate) => Promise<string>;
};

export function useProject(projectId: string | null, initialRole: Role = "architect"): ProjectWorkspace {
  const [state, setState] = useState<ProjectState>(projectId ? { status: "loading" } : { status: "none" });
  const [role, setRole] = useState<Role>(initialRole);
  const etag = useRef<string | null>(null);

  useEffect(() => {
    etag.current = null;
    if (!projectId) {
      setState({ status: "none" });
      return;
    }
    setState({ status: "loading" });
    const stop = new AbortController();
    async function poll() {
      if (document.hidden) return;
      try {
        const read = await readProject(projectId!, etag.current, stop.signal);
        if (read.status === "unchanged") return;
        if (read.status === "ok") {
          etag.current = read.etag;
          setState({ status: "ok", project: read.project, sample: read.sample });
        } else {
          // Keep showing the last good copy while the store is out of reach; say so only when there is none.
          setState((current) => (current.status === "ok" && read.status === "unreachable" ? current : { status: read.status }));
        }
      } catch {
        // The project changed or the panel closed while waiting.
      }
    }
    void poll();
    const timer = window.setInterval(poll, POLL_MS);
    return () => {
      stop.abort();
      window.clearInterval(timer);
    };
  }, [projectId]);

  const saved = useCallback((result: ProjectWrite) => {
    const why = whyNotSaved(result);
    if (why) throw new Error(why);
    if (result.status === "ok") {
      etag.current = result.etag;
      setState({ status: "ok", project: result.project, sample: false });
    }
  }, []);

  const open = useCallback((): string => {
    if (!projectId) throw new Error("no project is open");
    return projectId;
  }, [projectId]);

  return {
    projectId,
    state,
    role,
    setRole,
    updateItem: async (update) => saved(await projectWrites.updateItems(open(), [update])),
    addSiteActionItems: async () => {
      if (state.status !== "ok") throw new Error("no project is open");
      const actions = await api.actions(state.project.site_bbl);
      if (actions.sample) throw new Error("only sample action items could be loaded, so none were added");
      saved(await projectWrites.addItems(open(), actions.data));
    },
    addNote: async (text) => saved(await projectWrites.addNote(open(), role, text)),
    pinChatAnswer: async (draft) => saved(await projectWrites.addPin(open(), chatAnswerPin(draft, role))),
    create: async (body) => {
      const result = await projectWrites.create(body);
      const why = whyNotSaved(result);
      if (why || result.status !== "ok") throw new Error(why ?? "the project was not created");
      return result.project.id;
    },
  };
}
