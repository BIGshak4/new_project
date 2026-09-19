import {
  PracticeApiError,
  type Attempt,
  type ApiLang,
  type Submission,
} from "./practice-api";

export type Entry = {
  id: string;
  user_id: string;
  question_id: string;
  answer: string;
  self_rating: number | null;
  bookmarked: boolean;
  completed: boolean;
  version: number;
};

// A language refresh can finish after a bookmark save. Never replace a newly
// saved entry with an older snapshot from the parallel library request.
export function mergeEntries(current: Entry[], incoming: Entry[]) {
  const byQuestion = new Map(
    current.map((entry) => [entry.question_id, entry]),
  );
  for (const entry of incoming) {
    const previous = byQuestion.get(entry.question_id);
    if (!previous || entry.version >= previous.version)
      byQuestion.set(entry.question_id, entry);
  }
  return [...byQuestion.values()];
}

const subjects: Record<string, [string, string]> = {
  digital_fundamentals: ["יסודות ספרתיים", "Digital fundamentals"],
  sequential_logic: ["לוגיקה סדרתית", "Sequential logic"],
  fsms: ["מכונות מצבים", "State machines"],
  relevant_programming: ["תכנות לחומרה ותוכנה", "Relevant programming"],
  reasoning: ["היגיון ופתרון בעיות", "Reasoning"],
  projects_behavioral: [
    "פרויקטים ושאלות התנהגותיות",
    "Projects and behavioral",
  ],
  digital_logic: ["לוגיקה ספרתית", "Digital logic"],
  digital_design: ["תכנון ספרתי", "Digital design"],
  programming: ["תכנות", "Programming"],
  software_fundamentals: ["יסודות תוכנה", "Software fundamentals"],
  problem_solving: ["פתרון בעיות", "Problem solving"],
  communication: ["תקשורת בראיון", "Communication"],
};
export function subjectLabel(key: string, lang: ApiLang) {
  return subjects[key]?.[lang === "he" ? 0 : 1] ?? key.replaceAll("_", " ");
}
export function bandLabel(band: string | null, lang: ApiLang) {
  const labels: Record<string, [string, string]> = {
    STRONG: ["תשובה חזקה", "Strong answer"],
    PARTIAL: ["תשובה חלקית", "Partial answer"],
    WEAK: ["דורשת שיפור", "Needs work"],
  };
  return (
    labels[band ?? ""]?.[lang === "he" ? 0 : 1] ??
    (lang === "he" ? "טרם הוערכה" : "Not evaluated")
  );
}
export function apiMessage(error: unknown, lang: ApiLang) {
  const he = lang === "he";
  const messages: Record<string, [string, string]> = {
    unauthenticated: [
      "ההתחברות פגה. התחברו שוב; התשובות שנשלחו נשמרות בחשבון.",
      "Your session expired. Sign in again; submitted answers remain saved.",
    ],
    forbidden: [
      "החשבון עדיין לא אושר לפיילוט.",
      "This account has not been approved for the pilot.",
    ],
    network: [
      "לא הצלחנו להגיע לשרת. הטיוטה נשמרת בדפדפן; בדקו חיבור ונסו שוב.",
      "Could not reach the server. Your draft stays in this browser; check your connection and retry.",
    ],
    usage_limit: [
      "הגעתם למכסת התרגולים היומית. אפשר לחזור לתרגולים קיימים ולנסות שוב מחר.",
      "Daily attempt limit reached. You can revisit existing attempts and start again tomorrow.",
    ],
    not_found: [
      "התרגול אינו זמין לחשבון הזה, או שהשאלה אינה זמינה כרגע.",
      "This attempt is unavailable to this account, or the question is currently unavailable.",
    ],
    conflict: [
      "התרגול השתנה בחלון אחר. בדקו את הגרסה השמורה לפני שליחה נוספת.",
      "The attempt changed in another tab. Check the saved version before submitting again.",
    ],
    already_submitted: [
      "כבר נשלחה תשובה. טענו את התוצאה השמורה או התחילו תרגול חדש.",
      "An answer was already submitted. Load its saved result or start a new attempt.",
    ],
    no_pending_follow_up: [
      "שאלת ההמשך השתנתה. טענו שוב את התרגול.",
      "The follow-up changed. Reload the attempt.",
    ],
    nothing_to_retry: [
      "אין כרגע הערכה שניתן לנסות מחדש. טענו את התרגול המעודכן.",
      "No evaluation is ready to retry. Load the latest attempt.",
    ],
    evaluation_unavailable: [
      "המשוב אינו זמין כרגע. בדקו את התשובה השמורה ונסו להעריך אותה שוב.",
      "Feedback is unavailable. Check the saved answer and retry its evaluation.",
    ],
    temporarily_unavailable: [
      "השרת אינו זמין זמנית. נסו שוב בעוד רגע.",
      "The server is temporarily unavailable. Try again shortly.",
    ],
    validation: [
      "בדקו שהתשובה מכילה עד 20,000 תווים ושהפרטים תקינים.",
      "Check the answer is at most 20,000 characters and the details are valid.",
    ],
  };
  const text =
    error instanceof PracticeApiError ? messages[error.code] : undefined;
  return (
    text?.[he ? 0 : 1] ??
    (he
      ? "הפעולה לא הושלמה. הטיוטה נשמרת בדפדפן. נסו שוב."
      : "The action could not finish. Your draft stays in this browser. Please retry.")
  );
}

export function allSubmissions(a: Attempt): Submission[] {
  return [a.submission, ...a.follow_ups.map((f) => f.submission)].filter(
    (s): s is Submission => !!s,
  );
}
export function latestSubmission(a: Attempt) {
  return allSubmissions(a).sort((x, y) => y.revision - x.revision)[0];
}
export type PendingAnswer = { key: string; text: string; turn: number | null };
export function hasAccepted(a: Attempt, pending: PendingAnswer) {
  return allSubmissions(a).some((s) => s.key === pending.key);
}
// A different tab may have answered this turn with another key. Do not replay a
// stale main answer when the server has already moved on to a follow-up.
export function pendingResolved(a: Attempt, pending: PendingAnswer) {
  return (
    hasAccepted(a, pending) ||
    allSubmissions(a).some((s) => s.turn === (pending.turn ?? 0))
  );
}

// Only drafts and retry identity are local; attempts and feedback are always read from the server.
export function readLocal<T>(key: string): T | null {
  try {
    return JSON.parse(sessionStorage.getItem(key) ?? "null") as T | null;
  } catch {
    return null;
  }
}
export function writeLocal(key: string, value: unknown) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* Browser storage can be disabled. Keep the in-memory draft. */
  }
}
export function removeLocal(key: string) {
  try {
    sessionStorage.removeItem(key);
  } catch {
    /* no local storage */
  }
}
