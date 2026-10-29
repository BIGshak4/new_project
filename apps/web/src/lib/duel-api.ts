import { supabase } from "./supabase";
import type { Duel, DuelClient, DuelLanguage, DuelList, DuelWallet } from "./duel-types";

export class DuelApiError extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = "DuelApiError"; }
}

/** Browser sessions supply a token; membership and ownership are enforced by the API. */
export function duelApi(userId: string, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL): DuelClient {
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
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new DuelApiError(payload?.error?.code ?? "internal", payload?.error?.message ?? "The game request failed.", response.status);
    return payload as T;
  }
  return {
    list: () => call<DuelList>("/v1/duels"),
    wallet: (language: DuelLanguage) => call<DuelWallet>(`/v1/me/coins?language=${language}`),
    get: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}`),
    create: (language) => call<Duel>("/v1/duels", { language, mode: "quiz" }),
    accept: (code) => call<Duel>("/v1/duels/accept", { code }),
    ready: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/ready`, {}),
    answer: (id, choice, item) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/answer`, { choice, item }),
    cancel: (id) => call<Duel>(`/v1/duels/${encodeURIComponent(id)}/cancel`, {}),
  };
}
