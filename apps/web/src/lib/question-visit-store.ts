/** Only routing metadata is synced. Answers and editor drafts stay in their own stores. */
export type QuestionVisit = {
  kind: "practice" | "quick";
  questionKey: string;
  attemptId: string | null;
  visitedAt: number;
};
type VisitEvent = QuestionVisit & { dismissed: boolean; pending: boolean; preview?: boolean };
const limit = 64;
const memory = new Map<string, VisitEvent[]>();
const memoryOnly = new Set<string>();
const generation = new Map<string, number>();
const cacheKey = (userId: string) => `jobrun-resume-visits-v1:${userId}`;
const key = (event: QuestionVisit) => event.kind + "/" + event.questionKey;
const newest = (a: QuestionVisit, b: QuestionVisit) => b.visitedAt - a.visitedAt;

function valid(value: unknown): value is VisitEvent {
  if (!value || typeof value !== "object") return false;
  const event = value as VisitEvent;
  return (event.kind === "practice" || event.kind === "quick") &&
    typeof event.questionKey === "string" && !!event.questionKey && event.questionKey.length <= 160 &&
    (event.attemptId === null || (event.kind === "practice" && typeof event.attemptId === "string" &&
      /^[\da-f]{8}-(?:[\da-f]{4}-){3}[\da-f]{12}$/i.test(event.attemptId))) &&
    Number.isSafeInteger(event.visitedAt) && event.visitedAt > 0 && event.visitedAt <= 8640000000000000 &&
    typeof event.dismissed === "boolean" && typeof event.pending === "boolean";
}

function cached(owner: string): VisitEvent[] {
  if (memoryOnly.has(owner)) return memory.get(owner) ?? [];
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(cacheKey(owner)) ?? "null");
    if (Array.isArray(raw)) return raw.filter(valid).sort(newest).slice(0, limit);
  } catch { /* Storage may be unavailable. */ }
  return memory.get(owner) ?? [];
}

function save(owner: string, events: VisitEvent[]) {
  const trimmed = events.sort(newest).slice(0, limit);
  memory.set(owner, trimmed);
  try {
    localStorage.setItem(cacheKey(owner), JSON.stringify(trimmed));
    memoryOnly.delete(owner);
  } catch { memoryOnly.add(owner); }
}

function same(a: VisitEvent | undefined, b: VisitEvent) {
  return a?.visitedAt === b.visitedAt && a.dismissed === b.dismissed && a.attemptId === b.attemptId && !!a.preview === !!b.preview;
}

async function accountClient(owner: string) {
  if (typeof window === "undefined" || !owner) return null;
  const { supabase } = await import("./supabase");
  const session = await supabase.auth.getSession();
  return session.data.session?.user.id === owner ? supabase : null;
}

type Client = NonNullable<Awaited<ReturnType<typeof accountClient>>>;

async function send(owner: string, client: Client, events: VisitEvent[]) {
  if (!events.length) return;
  const { error } = await client.rpc("sync_question_resume_visits", {
    p_owner: owner,
    p_events: events.map(event => ({
      kind: event.kind, question_key: event.questionKey, attempt_id: event.preview ? null : event.attemptId,
      visited_at_ms: event.visitedAt, dismissed: event.dismissed,
    })),
  }).abortSignal(AbortSignal.timeout(3500));
  if (error) return;
  const sent = new Map(events.map(event => [key(event), event]));
  save(owner, cached(owner).map(event => same(sent.get(key(event)), event) ? { ...event, pending: false } : event));
}

async function record(owner: string, visit: QuestionVisit, dismissed: boolean) {
  const event: VisitEvent = { ...visit, dismissed, pending: true };
  if (!owner || !valid(event)) return;
  const rows = cached(owner);
  const previous = rows.find(row => key(row) === key(event));
  if (previous && (previous.visitedAt > event.visitedAt ||
      (previous.visitedAt === event.visitedAt && previous.dismissed) ||
      (dismissed && event.attemptId !== null && previous.attemptId !== event.attemptId))) return;
  if (!dismissed && event.kind === "practice" && event.attemptId === null && previous?.attemptId && !previous.dismissed) {
    // Keep the local draft route offline; let the server retain its own latest attempt when syncing a preview.
    event.attemptId = previous.attemptId;
    event.preview = true;
  }
  save(owner, [event, ...rows.filter(row => key(row) !== key(event))]);
  try {
    const client = await accountClient(owner);
    if (client) await send(owner, client, [event]);
  } catch { /* Retry pending changes when the dashboard opens. */ }
}

export const rememberVisit = (owner: string, visit: QuestionVisit) => record(owner, visit, false);
export const forgetVisit = (owner: string, visit: QuestionVisit) => record(owner, visit, true);

export async function readRecentVisits(owner: string): Promise<QuestionVisit[]> {
  const request = (generation.get(owner) ?? 0) + 1;
  generation.set(owner, request);
  try {
    const client = await accountClient(owner);
    if (client) {
      await send(owner, client, cached(owner).filter(event => event.pending));
      const before = new Map(cached(owner).map(event => [key(event), event]));
      const pendingKeys = [...before.values()].filter(event => event.pending).map(event => event.questionKey);
      const read = () => client.from("question_resume_visits")
        .select("kind,question_key,attempt_id,visited_at_ms,dismissed").eq("user_id", owner);
      const [active, dismissed] = await Promise.all([
        read().eq("dismissed", false).order("visited_at_ms", { ascending: false })
          .limit(limit).abortSignal(AbortSignal.timeout(3500)),
        pendingKeys.length ? read().eq("dismissed", true).in("question_key", pendingKeys)
          .abortSignal(AbortSignal.timeout(3500)) : Promise.resolve({ data: [], error: null }),
      ]);
      if (generation.get(owner) === request && !active.error && !dismissed.error) {
        const remote = new Map<string, VisitEvent>();
        for (const row of [...(active.data ?? []), ...(dismissed.data ?? [])]) {
          const item = { kind: row.kind, questionKey: row.question_key, attemptId: row.attempt_id,
            visitedAt: row.visited_at_ms, pending: false, dismissed: row.dismissed };
          if (valid(item)) remote.set(key(item), item);
        }
        // A read must not undo a click or submission that arrived while it was in flight.
        for (const local of cached(owner)) {
          if (local.pending || !same(before.get(key(local)), local)) {
            const newer = remote.get(key(local));
            if (local.dismissed && local.attemptId !== null && newer && newer.attemptId !== local.attemptId) continue;
            if (!newer || newer.visitedAt < local.visitedAt || (newer.visitedAt === local.visitedAt && local.dismissed)) {
              remote.set(key(local), local);
            }
          }
        }
        save(owner, [...remote.values()]);
      }
    }
  } catch { /* Offline and blocked-storage sessions still use this browser's recent visits. */ }
  return cached(owner).filter(event => !event.dismissed).sort(newest);
}
