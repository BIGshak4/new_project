import type { Progress } from "./practice-api";
import type { QuestionVisit } from "./question-visit-store";

/** Opening an existing attempt is more recent than its start date. Newer attempts
 * still count on browsers that have never recorded a visit for this account. */
export function resumeCandidates(visits: QuestionVisit[], recent: Progress["recent"]): QuestionVisit[] {
  const byId = new Map(recent.map(attempt => [attempt.id, attempt]));
  const newest = new Map<string, Progress["recent"][number]>();
  for (const attempt of [...recent].sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at))) {
    if (!newest.has(attempt.question_key)) newest.set(attempt.question_key, attempt);
  }
  const candidates: QuestionVisit[] = [];
  for (const visit of visits) {
    if (visit.kind === "quick") { candidates.push(visit); continue; }
    const attempt = visit.attemptId ? byId.get(visit.attemptId) : newest.get(visit.questionKey);
    if (attempt && (attempt.question_key !== visit.questionKey || attempt.submitted_at || attempt.band)) continue;
    candidates.push({ ...visit, attemptId: visit.attemptId ?? attempt?.id ?? null });
  }
  for (const attempt of newest.values()) {
    if (attempt.submitted_at || attempt.band) continue;
    candidates.push({ kind: "practice", questionKey: attempt.question_key, attemptId: attempt.id, visitedAt: Date.parse(attempt.started_at) });
  }
  const seen = new Set<string>();
  return candidates.sort((a, b) => b.visitedAt - a.visitedAt).filter(item => {
    const identity = JSON.stringify([item.kind, item.questionKey, item.attemptId]);
    if (seen.has(identity)) return false;
    seen.add(identity);
    return true;
  });
}
