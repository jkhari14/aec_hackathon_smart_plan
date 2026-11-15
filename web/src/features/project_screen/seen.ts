// When this browser last looked at a project's checklist as a role, for "New for you". Kept per browser
// (localStorage): it is a reading mark, not project data. Without one, the project's creation time is used,
// so a teammate opening the link for the first time still sees what other roles' documents added.
import { useCallback, useEffect, useState } from "react";

import type { Role } from "../../contracts";

const key = (projectId: string, role: Role) => `4site.checklist-seen.${projectId}.${role}`;

function read(projectId: string, role: Role): string | null {
  try {
    return window.localStorage.getItem(key(projectId, role));
  } catch {
    return null;
  }
}

export function useLastSeen(projectId: string | null, role: Role, fallback: string | null) {
  const [stored, setStored] = useState<string | null>(() => (projectId ? read(projectId, role) : null));
  useEffect(() => setStored(projectId ? read(projectId, role) : null), [projectId, role]);

  const markSeen = useCallback(() => {
    if (!projectId) return;
    const now = new Date().toISOString();
    try {
      window.localStorage.setItem(key(projectId, role), now);
    } catch {
      // Private mode or blocked storage: the mark lasts for this page only.
    }
    setStored(now);
  }, [projectId, role]);

  return { since: stored ?? fallback, markSeen };
}
