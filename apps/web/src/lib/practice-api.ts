/**
 * Typed client for the JobRun practice API (backend/, contract at <API>/docs).
 *
 * Every call sends the Supabase access token as a Bearer token. Errors are thrown as
 * `PracticeApiError` with the backend's stable `code` (see docs/practice-api-integration.md).
 *
 *   const api = practiceApi();                       // reads NEXT_PUBLIC_API_BASE_URL
 *   const questions = await api.listQuestions("he");
 *   const attempt = await api.startAttempt({ question_key: q.key, language: "he", mode: "deep" });
 *   const key = newIdempotencyKey();                 // one per submit click; reuse it on retry
 *   const { submission } = await api.submit(attempt.id, { text }, key);
 *
 * Types mirror backend/app/schemas/api.py. Nothing here contains a reference solution or a
 * hidden hint: hints come one at a time from nextHint(), the reference from revealReference().
 */
import { supabase } from "./supabase";

export type ApiLang = "en" | "he";

export type QuestionSummary = {
  id: string;
  key: string;
  title: string;
  subject: string;
  format: string;
  difficulty: number;
  estimated_minutes: number | null;
  practice_modes: string[];
  language: ApiLang;
  languages: string[];
  status: string;
  hint_count: number;
  has_reference: boolean;
  has_check: boolean;
};

export type QuestionDetail = QuestionSummary & {
  prompt: string;
  requirements: string;
  choices: string[] | null;
  starter_code: string | null;
  code_language: string | null;
};

export type Hint = { level: number; text: string };
export type Check = { type: string; passed: boolean | null; detail: string };
export type Card = {
  what_happened: string;
  why_it_matters: string;
  next_step: string;
  your_reasoning_vs_reference: string;
};
export type Tip = { key: string; text: string };

export type SubmissionStatus = "pending" | "evaluating" | "done" | "failed";
export type Band = "STRONG" | "PARTIAL" | "WEAK";

export type Submission = {
  revision: number;
  key: string;
  turn: number;
  answer: string;
  status: SubmissionStatus;
  accepted_at: string;
  evaluated_at: string | null;
  band: Band | null;
  summary: string | null;
  key_points_hit: string[];
  key_points_missed: string[];
  check: Check | null;
  card: Card | null;
  tip: Tip | null;
  follow_up: string | null;
  evidence: "full" | "reduced" | "none";
  flags: string[];
  replayed: boolean;
};

export type FollowUp = {
  turn: number;
  question: string;
  action: string;
  created_at: string;
  submission: Submission | null;
};

export type AttemptStatus = "in_progress" | "evaluating" | "done" | "failed";

export type Attempt = {
  id: string;
  question: QuestionDetail;
  mode: "quick" | "deep";
  language: ApiLang;
  self_confidence_before: number | null;
  status: AttemptStatus;
  started_at: string;
  hints: Hint[];
  hints_remaining: number;
  reference: string | null;
  submission: Submission | null;
  follow_ups: FollowUp[];
  pending_follow_up: FollowUp | null;
  can_submit: boolean;
  can_retry: boolean;
};

export type SkillProgress = {
  key: string;
  label: string;
  subject: string;
  level: number | null;
  status: "not_assessed" | "insufficient" | "assessed";
  trend: "new" | "stable" | "improving" | "declining";
  required_level: number;
  assessments: number;
  last_assessed_at: string | null;
  retention_due_at: string | null;
};

export type Progress = {
  skills: SkillProgress[];
  recent: {
    id: string;
    question_key: string;
    mode: string;
    band: Band | null;
    started_at: string;
    submitted_at: string | null;
    language: ApiLang;
    hints_used: number;
    reference_revealed: boolean;
  }[];
  attempts_today: number;
  daily_limit: number;
};

export type Me = { id: string; email: string | null; pilot_member: boolean; can_manage_tasks: boolean };

export type StartAttemptRequest = {
  question_key?: string;
  question_id?: string;
  mode?: "quick" | "deep";
  language?: ApiLang;
  self_confidence?: 1 | 2 | 3 | 4 | 5;
};

export type SubmitRequest = {
  text: string;
  latency_ms?: number;
  revision_count?: number;
};

export type SubmissionResponse = { submission: Submission; attempt: Attempt };

/** The backend's stable error codes (docs/practice-api-integration.md §2). */
export type ApiErrorCode =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "validation"
  | "conflict"
  | "already_submitted"
  | "no_pending_follow_up"
  | "nothing_to_retry"
  | "usage_limit"
  | "evaluation_unavailable"
  | "payload_too_large"
  | "method_not_allowed"
  | "internal"
  | "network";

export class PracticeApiError extends Error {
  constructor(
    public readonly code: ApiErrorCode,
    message: string,
    public readonly status: number,
    public readonly requestId?: string,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "PracticeApiError";
  }
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}

export type PracticeApi = ReturnType<typeof practiceApi>;

export function practiceApi(baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL) {
  if (!baseUrl) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
  const base = baseUrl.replace(/\/+$/, "");

  async function token(): Promise<string> {
    const { data } = await supabase.auth.getSession();
    const access = data.session?.access_token;
    if (!access) throw new PracticeApiError("unauthenticated", "not signed in", 401);
    return access;
  }

  async function call<T>(
    method: "GET" | "POST",
    path: string,
    body?: unknown,
    extraHeaders: Record<string, string> = {},
  ): Promise<T> {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${await token()}`,
      ...extraHeaders,
    };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    let response: Response;
    try {
      response = await fetch(base + path, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
      });
    } catch (error) {
      throw new PracticeApiError("network", `could not reach the practice API: ${String(error)}`, 0);
    }
    const requestId = response.headers.get("x-request-id") ?? undefined;
    if (response.ok) return (await response.json()) as T;
    let payload: { error?: { code?: string; message?: string; details?: unknown } } = {};
    try {
      payload = await response.json();
    } catch {
      /* not json: keep the status */
    }
    throw new PracticeApiError(
      (payload.error?.code as ApiErrorCode) ?? "internal",
      payload.error?.message ?? `request failed with ${response.status}`,
      response.status,
      requestId,
      payload.error?.details,
    );
  }

  const q = (params: Record<string, string | undefined>) => {
    const search = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v) search.set(k, v);
    const s = search.toString();
    return s ? `?${s}` : "";
  };

  return {
    me: () => call<Me>("GET", "/v1/me"),
    progress: () => call<Progress>("GET", "/v1/me/progress"),

    listQuestions: (language: ApiLang, subject?: string) =>
      call<QuestionSummary[]>("GET", `/v1/questions${q({ language, subject })}`),
    getQuestion: (keyOrId: string, language: ApiLang) =>
      call<QuestionDetail>("GET", `/v1/questions/${encodeURIComponent(keyOrId)}${q({ language })}`),

    startAttempt: (body: StartAttemptRequest) => call<Attempt>("POST", "/v1/practice/attempts", body),
    getAttempt: (attemptId: string) => call<Attempt>("GET", `/v1/practice/attempts/${attemptId}`),
    nextHint: (attemptId: string) =>
      call<{ hint: Hint | null; attempt: Attempt }>("POST", `/v1/practice/attempts/${attemptId}/hints/next`),
    revealReference: (attemptId: string) =>
      call<{ reference: string; attempt: Attempt }>("POST", `/v1/practice/attempts/${attemptId}/reference`),

    /** Main answer. `idempotencyKey`: one per click, reused on retry (newIdempotencyKey()). */
    submit: (attemptId: string, body: SubmitRequest, idempotencyKey: string) =>
      call<SubmissionResponse>(
        "POST",
        `/v1/practice/attempts/${attemptId}/submissions`,
        { answer: { text: body.text }, latency_ms: body.latency_ms, revision_count: body.revision_count },
        { "Idempotency-Key": idempotencyKey },
      ),
    submitFollowUp: (attemptId: string, turn: number, body: SubmitRequest, idempotencyKey: string) =>
      call<SubmissionResponse>(
        "POST",
        `/v1/practice/attempts/${attemptId}/follow-ups/${turn}/submissions`,
        { answer: { text: body.text }, latency_ms: body.latency_ms },
        { "Idempotency-Key": idempotencyKey },
      ),
    /** After a submission with status "failed": evaluate the saved answer again. */
    retry: (attemptId: string, revision: number) =>
      call<SubmissionResponse>("POST", `/v1/practice/attempts/${attemptId}/submissions/${revision}/retry`),
  };
}
