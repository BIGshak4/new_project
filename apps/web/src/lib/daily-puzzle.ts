import type { DuelLanguage } from "./duel-types";

export type DailyPuzzle = {
  day: string;
  expires_at: string;
  id: string;
  title: string;
  prompt: string;
  subject: string;
};
export type DailyPuzzleSolution = Pick<DailyPuzzle, "day" | "id"> & { solution: string };
export type DailyPuzzleClient = {
  get(language: DuelLanguage): Promise<DailyPuzzle>;
  reveal(language: DuelLanguage, day: string, id: string): Promise<DailyPuzzleSolution>;
};

type PuzzleIdentity = Pick<DailyPuzzle, "day" | "id">;
export type DailyDraft = { answer: string; revealed: boolean };

function storageKey(userId: string) { return `jobrun:daily-puzzle:${userId}`; }

// Keep one day's draft per account, including across Hebrew/English views of the same puzzle.
export function readDailyDraft(userId: string, puzzle: PuzzleIdentity): DailyDraft {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey(userId)) ?? "null");
    if (saved?.day === puzzle.day && saved.id === puzzle.id && typeof saved.answer === "string") {
      return { answer: saved.answer, revealed: saved.revealed === true };
    }
  } catch { /* Storage is optional. */ }
  return { answer: "", revealed: false };
}

export function writeDailyDraft(userId: string, puzzle: PuzzleIdentity, draft: DailyDraft) {
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify({ day: puzzle.day, id: puzzle.id, ...draft }));
  } catch { /* Continue in memory when browser storage is unavailable. */ }
}
