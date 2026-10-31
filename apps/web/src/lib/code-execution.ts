import type { ApiLang } from "./practice-api";

export type ExecutionCapabilities = {
  available: boolean;
  languages: string[];
  tested_languages: string[];
  contract: { he: string; en: string } | null;
  starters: Record<string, string>;
  reason?: string;
};

export type CodeExecutionRequest = {
  language: string;
  source: string;
  stdin: string;
  idempotency_key: string;
};

export type CodeExecutionResult = {
  status: "passed" | "failed" | "compile_error" | "runtime_error" | "timeout" | "completed" | "compile_only" | "unavailable";
  language: string;
  compiled: boolean | null;
  executed: boolean;
  passed: boolean | null;
  stdout: string;
  stderr: string;
  compile_output: string;
  /** Totals come from the server; cases is only a bounded diagnostic sample. */
  test_count?: number;
  passed_count?: number;
  cases: { index: number; passed: boolean; input?: unknown; expected?: unknown; actual?: unknown }[];
  runtime_ms: number;
  detail: string;
};

export const executionSourceLimit = 20_000;
export const executionStdinLimit = 8_000;

/** A result belongs to all of these inputs, including stdin and the owned attempt. */
export function executionInputKey(attemptId: string, language: string, source: string, stdin: string): string {
  return JSON.stringify([attemptId, language, source, stdin]);
}

/** Cancelling or superseding a request invalidates its reply even if transport abort is late. */
export class ExecutionRequestGate {
  private revision = 0;
  begin() { return ++this.revision; }
  invalidate() { ++this.revision; }
  accepts(revision: number, startedInput: string, currentInput: string) {
    return revision === this.revision && startedInput === currentInput;
  }
}

export function executionStatusLabel(result: CodeExecutionResult, lang: ApiLang): string {
  const labels: Record<CodeExecutionResult["status"], [string, string]> = {
    passed: ["כל הבדיקות שהוגדרו עברו", "All configured tests passed"],
    failed: ["חלק מהבדיקות שהוגדרו נכשלו", "Some configured tests failed"],
    compile_error: ["הקומפילציה נכשלה", "Compilation failed"],
    runtime_error: ["ההרצה הסתיימה בשגיאה", "The program raised an error"],
    timeout: ["ההרצה עברה את מגבלת הזמן", "Execution exceeded the time limit"],
    completed: ["ההרצה הסתיימה · נכונות התשובה לא נבדקה", "Execution completed · correctness was not checked"],
    compile_only: ["הקומפילציה הצליחה · לא בוצעה בדיקת התנהגות", "Compilation succeeded · behavior was not tested"],
    unavailable: ["ההרצה אינה זמינה כרגע", "Execution is currently unavailable"],
  };
  return labels[result.status]?.[lang === "he" ? 0 : 1] ?? (lang === "he" ? "תוצאת הרצה" : "Execution result");
}

export function executionErrorMessage(error: unknown, lang: ApiLang): string {
  const he = lang === "he";
  const issue = error as { status?: number; code?: string } | null;
  if (issue?.status === 429)
    return he ? "הגעתם למגבלת ההרצות. נסו שוב מאוחר יותר; הטיוטה נשארת בעורך." : "The execution limit has been reached. Try again later; your draft stays in the editor.";
  if (issue?.status === 401)
    return he ? "ההתחברות פגה. התחברו שוב כדי להריץ את הקוד." : "Your session expired. Sign in again to run the code.";
  if (issue?.status === 403 || issue?.status === 404)
    return he ? "אין גישה להרצה בתרגול הזה. טענו שוב את התרגול." : "Execution is unavailable for this attempt. Reload the attempt.";
  if (issue?.status === 422 || issue?.status === 413)
    return he ? "בדקו את שפת הקוד ואת מגבלות גודל הקוד והקלט." : "Check the language and the source and input size limits.";
  return he ? "לא הצלחנו להשלים את ההרצה. נסו שוב; הטיוטה נשארת בעורך." : "Execution could not complete. Try again; your draft stays in the editor.";
}

export function executionValue(value: unknown): string {
  if (typeof value === "string") return value.slice(0, 4_000);
  const text = JSON.stringify(value, null, 2);
  return text === undefined ? "—" : text.slice(0, 4_000);
}
