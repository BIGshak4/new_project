import type { DailyPuzzleClient, DailyPuzzle, DailyPuzzleSolution } from "./daily-puzzle";
import { supabase } from "./supabase";
import type { Duel, DuelClient, DuelInvitation, DuelLanguage, DuelList, DuelWallet, QuizPracticeRound, QuizPracticeResult } from "./duel-types";

export class DuelApiError extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = "DuelApiError"; }
}

/** Browser sessions supply a token; membership and ownership are enforced by the API. */
export function duelApi(userId: string, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL): DuelClient & {
  daily: DailyPuzzleClient;
  invitations(): Promise<{ invitations: DuelInvitation[] }>;
  presence(): Promise<void>;
} {
  async function call<T>(path: string, body?: unknown): Promise<T> {
    if (!baseUrl) throw new DuelApiError("configuration", "The game API is not configured.");
    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session?.access_token || data.session.user.id !== userId)
      throw new DuelApiError("unauthenticated", "Please sign in again.", 401);
    let response: Response;
    try {
      response = await fetch(baseUrl.replace(/\/+$/, "") + path, {
        method: body === undefined ? "GET" : "POST", cache: "no-store",
        headers: { Authorization: `Bearer ${data.session.access_token}`, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
        body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(20000),
      });
    } catch { throw new DuelApiError("network", "Unable to reach the game server."); }
    // An old request must not become visible after the account changes.
    const current = await supabase.auth.getSession();
    if (current.data.session?.user.id !== userId) throw new DuelApiError("unauthenticated", "The account changed.", 401);
    if (response.status === 204) return undefined as T;
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new DuelApiError(payload?.error?.code ?? "internal", payload?.error?.message ?? "The game request failed.", response.status);
    return payload as T;
  }
  return {
    daily: {
      get: language => call<DailyPuzzle>(`/v1/games/daily-puzzle?language=${language}`),
      reveal: (language, day, id) => call<DailyPuzzleSolution>(`/v1/games/daily-puzzle/reveal?language=${language}`, { day, id }),
    },
    practice: {
      start: (language) => call<QuizPracticeRound>(`/v1/duels/practice?language=${language}`),
      answer: (round_token, choice) => call<QuizPracticeResult>("/v1/duels/practice/answer", { round_token, choice }),
    },
    list: () => call<DuelList>("/v1/duels"),
    wallet: (language: DuelLanguage) => call<DuelWallet>(`/v1/me/coins?language=${language}`),
    get: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}`),
    create: (language, friendId) => call<Duel>("/v1/duels", { language, mode: "quiz", friend_id: friendId }),
    invitations: () => call<{ invitations: DuelInvitation[] }>("/v1/duels/invitations"),
    presence: () => call<void>("/v1/me/presence", {}),
    accept: (code) => call<Duel>("/v1/duels/accept", { code }),
    ready: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/ready`, {}),
    answer: (id, choice, item) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/answer`, { choice, item }),
    cancel: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/cancel`, {}),
  };
}
