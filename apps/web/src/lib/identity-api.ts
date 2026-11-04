import { supabase } from "./supabase";
import { IdentityApiError, normalizeFriendCode, normalizeUsername, readFriends, readIdentity, readUsernameAvailability, type IdentityClient, type UsernameAvailability } from "./identity-types";

type AuthSession = { access_token: string; user: { id: string } };
export type IdentityAuth = {
  getSession(): Promise<{ data: { session: AuthSession | null }; error?: unknown }>;
  onAuthStateChange(callback: (event: string, session: AuthSession | null) => void): { data: { subscription: { unsubscribe(): void } } };
};

async function responsePayload(response: Response): Promise<unknown> {
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new IdentityApiError(response.status === 429 ? "rate_limited" : payload?.error?.code ?? (response.status === 401 ? "unauthenticated" : "internal"), payload?.error?.message ?? "Identity request failed", response.status);
  return payload;
}

export async function usernameAvailability(username: string, signal?: AbortSignal, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL): Promise<UsernameAvailability> {
  if (!baseUrl) throw new IdentityApiError("configuration", "Identity API is not configured");
  let response: Response;
  try {
    response = await fetch(`${baseUrl.replace(/\/+$/, "")}/v1/usernames/availability?username=${encodeURIComponent(normalizeUsername(username))}`, {
      cache: "no-store", signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(12000)]) : AbortSignal.timeout(12000),
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new IdentityApiError("network", "Unable to check username availability");
  }
  return readUsernameAvailability(await responsePayload(response));
}

/** A request can only be sent and read within the same signed-in account lifecycle. */
export function identityApi(userId: string, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL, auth: IdentityAuth = supabase.auth): IdentityClient {
  async function call<T>(path: string, read: (value: unknown) => T, method = "GET", body?: unknown): Promise<T> {
    if (!baseUrl) throw new IdentityApiError("configuration", "Identity API is not configured");
    const controller = new AbortController();
    let changed = false;
    const { data: { subscription } } = auth.onAuthStateChange((_event, session) => {
      if (session?.user.id !== userId) { changed = true; controller.abort(); }
    });
    try {
      const initial = await auth.getSession();
      if (changed || initial.error || initial.data.session?.user.id !== userId || !initial.data.session.access_token) throw new IdentityApiError("unauthenticated", "The account is not signed in", 401);
      let response: Response;
      try {
        response = await fetch(baseUrl.replace(/\/+$/, "") + path, {
          method, cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(25000)]),
          headers: { Authorization: `Bearer ${initial.data.session.access_token}`, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
          ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        });
      } catch {
        if (changed) throw new IdentityApiError("account_changed", "The account changed", 401);
        throw new IdentityApiError("network", "Unable to reach the identity service");
      }
      const payload = await responsePayload(response);
      const current = await auth.getSession();
      if (changed || current.error || current.data.session?.user.id !== userId) throw new IdentityApiError("account_changed", "The account changed", 401);
      return read(payload);
    } finally { subscription.unsubscribe(); }
  }
  return {
    identity: () => call("/v1/me/identity", readIdentity),
    claimUsername: username => call("/v1/me/identity/username", readIdentity, "PUT", { username: normalizeUsername(username) }),
    friends: () => call("/v1/me/friends", readFriends),
    requestFriend: friendCode => call("/v1/me/friends/requests", readFriends, "POST", { friend_code: normalizeFriendCode(friendCode) }),
    acceptRequest: id => call(`/v1/me/friends/requests/${encodeURIComponent(id)}/accept`, readFriends, "POST", {}),
    declineRequest: id => call(`/v1/me/friends/requests/${encodeURIComponent(id)}/decline`, readFriends, "POST", {}),
    cancelRequest: id => call(`/v1/me/friends/requests/${encodeURIComponent(id)}`, readFriends, "DELETE"),
    removeFriend: id => call(`/v1/me/friends/${encodeURIComponent(id)}`, readFriends, "DELETE"),
  };
}
