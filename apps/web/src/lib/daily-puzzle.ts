import { emptyVisual, type VisualAnswer } from "./circuit";
import type { DuelLanguage } from "./duel-types";
import type { Submission } from "./practice-api";

export type DailyPuzzle = {
  day: string;
  expires_at: string;
  id: string;
  title: string;
  prompt: string;
  subject: string;
  attempt_id: string;
  status: "open" | "evaluating" | "failed" | "done";
  submission: Submission | null;
  score: number | null;
  passed: boolean | null;
  feedback_remaining: number;
  feedback_limit: number;
};
type PuzzleIdentity = Pick<DailyPuzzle, "day" | "id">;
export type DailyPuzzleSolution = PuzzleIdentity & { solution: string };
export type DailyAnswer = { text: string; visual?: VisualAnswer };
export type DailyPuzzleClient = {
  get(language: DuelLanguage, day?: string): Promise<DailyPuzzle>;
  submit(language: DuelLanguage, day: string, id: string, answer: DailyAnswer): Promise<DailyPuzzle>;
  retry(language: DuelLanguage, day: string, id: string): Promise<DailyPuzzle>;
  reveal(language: DuelLanguage, day: string, id: string): Promise<DailyPuzzleSolution>;
};

export type DailyDraft = { answer: string; visual: VisualAnswer };

function storageKey(userId: string) { return `jobrun:daily-puzzle:${userId}`; }

// Only the server knows whether a daily submission has been accepted and graded.
export function readDailyDraft(userId: string, puzzle: PuzzleIdentity): DailyDraft {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey(userId)) ?? "null");
    if (saved?.day === puzzle.day && saved.id === puzzle.id && typeof saved.answer === "string") {
      return { answer: saved.answer, visual: Array.isArray(saved.visual?.images) ? saved.visual : emptyVisual() };
    }
  } catch { /* Storage is optional. */ }
  return { answer: "", visual: emptyVisual() };
}

export function writeDailyDraft(userId: string, puzzle: PuzzleIdentity, draft: DailyDraft) {
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify({ day: puzzle.day, id: puzzle.id, ...draft }));
  } catch { /* Continue in memory when browser storage is unavailable. */ }
}
