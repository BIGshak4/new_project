export type WorkspaceRoute = { view: string; question?: string; attempt?: string; interview?: string; quick?: string; source?: "retry" | "suggestion"; duration?: number };
export const DEFAULT_WORKSPACE_VIEW = "learn";

/** Choose the landing URL once when the practice account becomes available. */
export function personalAreaEntryUrl(url: URL, referrer: string, navigationType: NavigationTimingType | undefined, signedInNow: boolean): string | null {
  // Invitations and public pages have independent entry flows.
  if (!["/", "/games", "/games/shop"].includes(url.pathname)) return null;
  const internalLink = referrer.startsWith(url.origin + "/");
  if (!signedInNow && (navigationType === "back_forward" || (navigationType !== "reload" && internalLink))) return null;
  if (url.pathname !== "/") return "/";
  const query = new URLSearchParams(url.search);
  for (const key of ["view", "question", "attempt", "interview", "quick", "duration", "source", "nav"]) query.delete(key);
  return query.size ? `/?${query}` : "/";
}

/** Decode the current in-workspace destination, including Back and Forward. */
export function readWorkspaceRoute(search: string): { route: WorkspaceRoute; search: string } {
  const query = new URLSearchParams(search);
  query.delete("nav");
  const quick = query.get("view") === "fundamentals" && /^quick-(hw|sw)-\d{2,4}$/.test(query.get("quick") ?? "")
    ? query.get("quick")! : undefined;
  if (!quick) query.delete("quick");
  if (query.get("view") === "progress") {
    query.delete("view");
    query.delete("duration");
  }
  return {
    route: {
      view: query.get("view") ?? DEFAULT_WORKSPACE_VIEW,
      question: query.get("question") || undefined,
      attempt: query.get("attempt") || undefined,
      interview: query.get("interview") || undefined,
      ...(quick ? { quick } : {}),
      source: query.get("source") === "retry" ? "retry" : query.get("source") === "suggestion" ? "suggestion" : undefined,
      duration: [20, 30, 45].includes(Number(query.get("duration"))) ? Number(query.get("duration")) : undefined,
    },
    search: query.toString(),
  };
}
