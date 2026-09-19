import type { ApiLang, QuestionSummary } from "./practice-api";

const TTL = 12 * 60 * 60 * 1000;
const key = (userId: string, lang: ApiLang) =>
  `jobrun:question-list:v1:${userId}:${lang}`;

// Store only catalog metadata, never full questions, answers, hints, or assessments.
export function writeQuestionCache(
  userId: string,
  lang: ApiLang,
  questions: QuestionSummary[],
) {
  try {
    const summaries = questions.map((q) => ({
      id: q.id,
      key: q.key,
      title: q.title,
      subject: q.subject,
      format: q.format,
      difficulty: q.difficulty,
      estimated_minutes: q.estimated_minutes,
      practice_modes: q.practice_modes,
      language: q.language,
      languages: q.languages,
      status: q.status,
      hint_count: q.hint_count,
      has_reference: q.has_reference,
      has_check: q.has_check,
    }));
    sessionStorage.setItem(
      key(userId, lang),
      JSON.stringify({ savedAt: Date.now(), questions: summaries }),
    );
  } catch {
    /* Storage may be disabled or full; live requests still work. */
  }
}

export function readQuestionCache(
  userId: string,
  lang: ApiLang,
): QuestionSummary[] | null {
  try {
    const raw = sessionStorage.getItem(key(userId, lang));
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (
      typeof data.savedAt !== "number" ||
      Date.now() - data.savedAt > TTL ||
      data.savedAt > Date.now() ||
      !Array.isArray(data.questions) ||
      !data.questions.every(
        (q: QuestionSummary) =>
          q &&
          typeof q.id === "string" &&
          typeof q.key === "string" &&
          typeof q.title === "string" &&
          typeof q.subject === "string" &&
          Array.isArray(q.practice_modes) &&
          Array.isArray(q.languages),
      )
    )
      return null;
    return data.questions;
  } catch {
    return null;
  }
}
