import type { QuestionSummary } from "./practice-api";

/** Reviewed duplicates only. Different constraints (for example brackets with text) remain separate exercises.
 * Keep the original records, IDs and URLs: saved questions and attempt history must never be rewritten. */
const DUPLICATES: Readonly<Record<string, string>> = {
  // The manually collected preparation question is the primary version, with its source/company reports.
  "example-power-of-two-check": "prep-power-of-two-check",
  "example-merge-measurement-streams": "prep-merge-two-sorted-arrays",
  "example-overlapping-sequence-1011": "prep-detect-overlapping-1011-stream",
  "example-mod-six-counter": "prep-enabled-mod-six-counter",
};

export function questionFamily(key: string): string {
  return DUPLICATES[key] ?? key;
}

/** Call after filtering so searching a legacy title/number/company can still find that exact record. */
export function uniqueLibraryQuestions(rows: QuestionSummary[]): QuestionSummary[] {
  const groups = new Map<string, QuestionSummary>();
  for (const row of rows) {
    const key = questionFamily(row.key);
    if (!groups.has(key) || row.key === key) groups.set(key, row);
  }
  return [...groups.values()];
}

export function relatedQuestionKeys(key: string): string[] {
  const family = questionFamily(key);
  return [family, ...Object.keys(DUPLICATES).filter((alias) => DUPLICATES[alias] === family)]
    .filter((candidate) => candidate !== key);
}
