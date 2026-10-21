import revisions from "../content/fundamentals-revisions.json";
import type { FundamentalCompletion, FundamentalsProgress, PracticeApi } from "./practice-api";
import type { QuickQuestion } from "./fundamentals";

export type QuickProgressApi = Pick<PracticeApi, "fundamentalsProgress" | "completeFundamental" | "resetFundamental">;
export type QuickHistoryView = "unanswered" | "completed" | "all";
export type QuickCompletionState = "unanswered" | "completed" | "updated";

export function quickRevision(key: string) {
  const revision = (revisions as Record<string, string>)[key];
  if (!revision) throw new Error("Missing quick-question revision");
  return revision;
}

function isCompletion(value: unknown): value is FundamentalCompletion {
  if (!value || typeof value !== "object") return false;
  const row = value as FundamentalCompletion;
  return typeof row.question_key === "string" && /^quick-(hw|sw)-\d{2,4}$/.test(row.question_key) &&
    typeof row.content_revision === "string" && /^[a-f0-9]{64}$/.test(row.content_revision) &&
    typeof row.completed_at === "string" && Number.isFinite(Date.parse(row.completed_at));
}

export function readQuickProgress(value: FundamentalsProgress): Record<string, FundamentalCompletion> {
  if (!value || !Array.isArray(value.completed)) throw new Error("Progress could not be confirmed");
  const records: Record<string, FundamentalCompletion> = {};
  for (const row of value.completed) {
    if (!isCompletion(row) || records[row.question_key]) throw new Error("Progress could not be confirmed");
    records[row.question_key] = row;
  }
  return records;
}

export function confirmQuickCompletion(value: FundamentalCompletion, key: string): FundamentalCompletion {
  if (!isCompletion(value) || value.question_key !== key || value.content_revision !== quickRevision(key))
    throw new Error("Completion was not confirmed for this question version");
  return value;
}

export function quickCompletionState(question: Pick<QuickQuestion, "id">, records: Record<string, FundamentalCompletion>): QuickCompletionState {
  const record = records[question.id];
  return !record ? "unanswered" : record.content_revision === quickRevision(question.id) ? "completed" : "updated";
}

export function filterQuickHistory(questions: QuickQuestion[], records: Record<string, FundamentalCompletion>, view: QuickHistoryView) {
  return questions.filter(question => view === "all" || (view === "completed"
    ? !!records[question.id] : !records[question.id]));
}
