export type WorkspaceRoute = { view: string; question?: string; attempt?: string; interview?: string; quick?: string; source?: "retry" | "suggestion"; duration?: number };
export const DEFAULT_WORKSPACE_VIEW = "learn";

/** New visits start in Personal Area; focused practice links keep their destination. */
export function readWorkspaceRoute(search: string, entry = false): { route: WorkspaceRoute; search: string } {
  const query = new URLSearchParams(search);
  // Cross-page category links carry a one-use intent; refreshing that URL still starts in Personal Area.
  const navigation = query.get("nav") === "1" && ["learn", "library", "interview"].includes(query.get("view") ?? "");
  query.delete("nav");
  const quick = query.get("view") === "fundamentals" && /^quick-(hw|sw)-\d{2,4}$/.test(query.get("quick") ?? "")
    ? query.get("quick")! : undefined;
  if (!quick) query.delete("quick");
  const focused = !!(query.get("question") || query.get("attempt") || query.get("interview") || quick);
  if (query.get("view") === "progress" || (entry && !focused && !navigation)) {
    query.delete("view");
    if (!focused) query.delete("duration");
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
