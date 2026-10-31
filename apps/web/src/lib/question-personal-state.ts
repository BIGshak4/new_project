import type { QuestionSummary } from "./practice-api";
import type { Entry } from "./practice-ui";
import { questionFamily } from "./question-families";
import { supabase } from "./supabase";

export type QuestionPersonalState = { completed: boolean; hidden: boolean };
export type QuestionStatusFilter = "visible" | "not_done" | "done" | "hidden";
export const emptyQuestionState: QuestionPersonalState = { completed: false, hidden: false };

/** A legacy alias must not resurrect a hidden question or lose a past completion. */
export function buildQuestionStates(questions: QuestionSummary[], entries: Entry[]) {
  const byId = new Map(questions.map(q => [q.id, questionFamily(q.key)]));
  const families = new Map<string, QuestionPersonalState>();
  for (const entry of entries) {
    const family = byId.get(entry.question_id);
    if (!family) continue;
    const previous = families.get(family) ?? emptyQuestionState;
    families.set(family, {
      completed: previous.completed || entry.completed,
      hidden: previous.hidden || entry.hidden,
    });
  }
  return new Map(questions.map(q => [q.id, families.get(questionFamily(q.key)) ?? emptyQuestionState]));
}

export function questionStateIds(question: QuestionSummary, questions: QuestionSummary[]) {
  const family = questionFamily(question.key);
  return [...new Set([question.id, ...questions.filter(q => questionFamily(q.key) === family).map(q => q.id)])].sort();
}

export function matchesQuestionStatus(state: QuestionPersonalState, filter: QuestionStatusFilter) {
  if (filter === "hidden") return state.hidden;
  if (state.hidden) return false;
  return filter === "visible" || (filter === "done" ? state.completed : !state.completed);
}

/** The owner-only RPC patches flags atomically across aliases, preserving notes and bookmarks.
 * Independent completion/hide actions cannot overwrite each other, even in different tabs. */
export async function saveQuestionState(
  userId: string,
  questionIds: string[],
  patch: Partial<QuestionPersonalState>,
): Promise<Entry[]> {
  const ids = [...new Set(questionIds)].sort();
  if (!ids.length || ids.length > 8 ||
      (typeof patch.completed !== "boolean" && typeof patch.hidden !== "boolean")) {
    throw new Error("Invalid personal question state");
  }
  const { data, error } = await supabase.rpc("jr_set_question_state", {
    p_question_ids: ids,
    p_completed: patch.completed ?? null,
    p_hidden: patch.hidden ?? null,
  });
  if (error || !Array.isArray(data) || data.length !== ids.length ||
      data.some((entry: Entry) => entry.user_id !== userId || !ids.includes(entry.question_id))) {
    throw new Error("Could not save personal question state");
  }
  return data as Entry[];
}
