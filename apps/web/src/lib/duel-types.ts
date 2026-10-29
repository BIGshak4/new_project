/** Public game contract. Correct options exist only in settled review rows. */
import type { AvatarConfig } from "./avatar-types";
export type DuelLanguage = "he" | "en";
export type DuelSide = { avatar?: AvatarConfig | null; ready: boolean; answered: boolean; answered_count: number; score: number | null; seconds: number | null; band?: string | null; summary?: string | null; submitted_at?: string | null };
export type QuizItem = { index: number; key: string; source_key: string; variant: number | null; prompt: string; choices: string[] };
export type QuizReview = QuizItem & { correct: number; explanation: string; mine: number | null; theirs: number | null; mine_correct: boolean; theirs_correct: boolean };
export type Duel = {
  id: string; code: string; share_path: string; share_url: string;
  status: "open" | "active" | "settled" | "cancelled"; mode: "quiz" | "judged";
  role: "challenger" | "opponent"; stake: number; pot: number; language: DuelLanguage;
  me: DuelSide; opponent: DuelSide | null;
  question: { key: string; title: string; prompt: string; format: string; difficulty: number } | null;
  quiz: { total: number; seconds_per_question: number; index: number; current: QuizItem | null; seconds_left: number | null; answers: { index: number; choice: number | null; correct: boolean; seconds: number }[]; score: number; finished: boolean; review: QuizReview[] } | null;
  deadline: string | null; seconds_left: number | null; started_at: string | null;
  server_now: string; lobby_expires_at: string | null; created_at: string; accepted_at: string | null; settled_at: string | null;
  outcome: string | null; won: boolean | null; coins_delta: number | null;
};
export type DuelRules = { stake: number; quiz_questions: number; quiz_seconds_per_question: number; quiz_available: boolean; quiz_source_count?: number; quiz_variant_count?: number; readiness_required?: boolean; no_monetary_value: boolean };
export type DuelList = { duels: Duel[]; rules: DuelRules };
export type DuelWallet = { balance: number; enabled: boolean; no_monetary_value: boolean };
export type DuelClient = {
  list(): Promise<DuelList>; wallet(language: DuelLanguage): Promise<DuelWallet>;
  get(id: string): Promise<Duel>; create(language: DuelLanguage): Promise<Duel>;
  accept(code: string): Promise<Duel>; ready(id: string): Promise<Duel>;
  answer(id: string, choice: number | null, item: number): Promise<Duel>; cancel(id: string): Promise<Duel>;
};

/** Monotonic elapsed time: changing the device's wall clock gives no extra answering time. */
export function quizSecondsLeft(seconds: number | null, receivedAt: number, now: number): number {
  return Math.max(0, Math.ceil((seconds ?? 0) - Math.max(0, now - receivedAt) / 1000));
}

export function inviteCode(value: string): string {
  const text = value.trim();
  try { return new URL(text).pathname.split("/").filter(Boolean).at(-1) ?? ""; } catch { return text; }
}
