import { supabase } from "./supabase";

export type AccountActivityDay = { date: string; questions: number };
export type AccountActivity = {
  timezone: string; today: string; streak_days: number; today_count: number;
  last_solved_date: string | null; days: AccountActivityDay[];
};
export type AccountWallet = { balance: number; enabled: boolean };

const nonnegativeInteger = (value: unknown) => Number.isInteger(value) && Number(value) >= 0;

/** Every read is bound to its caller before transmission and again before publication. */
export function accountStatsApi(userId: string, baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL) {
  async function read(path: string, signal: AbortSignal): Promise<unknown> {
    if (!baseUrl) throw new Error("The account service is unavailable.");
    const session = await supabase.auth.getSession();
    if (session.error || session.data.session?.user.id !== userId) throw new Error("The account changed.");
    const response = await fetch(`${baseUrl.replace(/\/+$/, "")}${path}`, {
      headers: { Authorization: `Bearer ${session.data.session.access_token}` },
      cache: "no-store", signal: AbortSignal.any([signal, AbortSignal.timeout(20000)]),
    });
    const payload = await response.json();
    const current = await supabase.auth.getSession();
    if (current.error || current.data.session?.user.id !== userId) throw new Error("The account changed.");
    if (!response.ok) throw new Error("The account service could not complete the read.");
    return payload;
  }
  return {
    async activity(timezone: string, signal: AbortSignal): Promise<AccountActivity> {
      const value = await read(`/v1/me/activity?${new URLSearchParams({ timezone })}`, signal) as AccountActivity;
      if (!value || typeof value.timezone !== "string" || typeof value.today !== "string" ||
          !nonnegativeInteger(value.streak_days) || !nonnegativeInteger(value.today_count) || !Array.isArray(value.days) ||
          value.days.some(day => typeof day.date !== "string" || !nonnegativeInteger(day.questions))) throw new Error("Incomplete activity response.");
      return value;
    },
    async wallet(lang: "he" | "en", signal: AbortSignal): Promise<AccountWallet> {
      const value = await read(`/v1/me/coins?language=${lang}`, signal) as AccountWallet;
      if (!value || !nonnegativeInteger(value.balance) || typeof value.enabled !== "boolean") throw new Error("Incomplete wallet response.");
      return value;
    },
  };
}
