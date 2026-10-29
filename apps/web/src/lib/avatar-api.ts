import { supabase } from "./supabase";
import type { AvatarClient, AvatarConfig, AvatarPayload } from "./avatar-types";

export class AvatarApiError extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = "AvatarApiError"; }
}

export function avatarApi(userId: string, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL): AvatarClient {
  async function call(method: "GET" | "PUT" | "POST", suffix = "", body?: unknown): Promise<AvatarPayload> {
    if (!baseUrl) throw new AvatarApiError("configuration", "The wardrobe API is not configured.");
    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session?.access_token || data.session.user.id !== userId)
      throw new AvatarApiError("unauthenticated", "Please sign in again.", 401);
    let response: Response;
    try {
      response = await fetch(`${baseUrl.replace(/\/+$/, "")}/v1/me/avatar${suffix}`, {
        method, cache: "no-store", signal: AbortSignal.timeout(25000),
        headers: { Authorization: `Bearer ${data.session.access_token}`, ...(body ? { "Content-Type": "application/json" } : {}) },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
    } catch { throw new AvatarApiError("network", "Unable to reach the wardrobe server."); }
    const current = await supabase.auth.getSession();
    if (current.data.session?.user.id !== userId) throw new AvatarApiError("unauthenticated", "The account changed.", 401);
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new AvatarApiError(payload?.error?.code ?? "internal", payload?.error?.message ?? "Wardrobe request failed.", response.status);
    if (!payload?.avatar || !Array.isArray(payload.owned_skins) || !Array.isArray(payload.skins) || !Array.isArray(payload.components) || !Array.isArray(payload.colors) || typeof payload.balance !== "number" || typeof payload.enabled !== "boolean" || typeof payload.shop_enabled !== "boolean")
      throw new AvatarApiError("invalid_response", "The wardrobe response was incomplete.");
    return payload as AvatarPayload;
  }
  return {
    get: () => call("GET"),
    save: (config: AvatarConfig) => call("PUT", "", { component: config.component, color: config.color, skin: config.skin }),
    buy: (skin) => call("POST", "/buy", { skin }),
    completeOnboarding: (config) => call("POST", "/onboarding", config ?? {}),
  };
}
