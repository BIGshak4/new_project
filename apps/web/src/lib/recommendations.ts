import type { ReadinessQuestion } from "./practice-api";

/** Each wave represents a different real recommendation, in the server's order. */
export function distinctRecommendations(questions: readonly ReadinessQuestion[]): ReadinessQuestion[] {
  const seen = new Set<string>();
  return questions.filter(question => {
    if (!question || typeof question.key !== "string" || !question.key.trim() ||
        typeof question.title !== "string" || !question.title.trim() || seen.has(question.key)) return false;
    seen.add(question.key);
    return true;
  }).slice(0, 3);
}
