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
import type { VisualAnswer } from "./circuit";
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
  /** published, or on trial by the founders' choice: what the coach may suggest as "next" */
  reviewed?: boolean;
  /** "on trial": being checked live before publication; show a badge */
  trial?: boolean;
  /** job types (keys from jobTypes()) this question is relevant to */
  job_types?: string[];
  /** "I saw it at ..." tags, most reported first */
  companies?: CompanyTag[];
  /** how well it fits the requested job type; only set when listQuestions was called with a job */
  relevance?: number | null;
};

/** "Seen at company X" by `count` candidates. Aggregated, never who. */
export type CompanyTag = { slug: string; name: string; count: number };

export type JobType = { key: string; label: string; description: string };

export type Company = {
  slug: string;
  name: string;
  questions: number;
  sightings: number;
};

/** What the user is preparing for. Asked once at the start; editable any time. */
export type Goal = {
  job_type: string | null;
  job_type_label: string | null;
  /** ISO date */
  interview_date: string | null;
  /** negative once the date has passed */
  days_to_interview: number | null;
  minutes_per_day: number | null;
  seniority: Seniority | null;
  /** job type and minutes are known: the onboarding was answered */
  complete: boolean;
};

export type Seniority =
  | "student"
  | "junior"
  | "mid"
  | "senior"
  | "staff"
  | "principal";

export type GoalRequest = {
  job_type?: string | null;
  interview_date?: string | null;
  minutes_per_day?: number | null;
  seniority?: Seniority | null;
  language?: ApiLang;
};

export type QuestionDetail = QuestionSummary & {
  prompt: string;
  requirements: string;
  choices: string[] | null;
  starter_code: string | null;
  code_language: string | null;
};

export type Hint = { level: number; text: string };
export type Check = {
  /** truth_table | numeric | code_tests */
  type: string;
  passed: boolean | null;
  detail: string;
  /** the first differing truth-table rows or failing test cases (shape depends on type) */
  mismatches?: Record<string, unknown>[];
};
export type Card = {
  what_happened: string;
  why_it_matters: string;
  next_step: string;
  your_reasoning_vs_reference: string;
};
export type Tip = { key: string; text: string };

export type SubmissionStatus = "evaluating" | "done" | "failed";
export type Band = "STRONG" | "PARTIAL" | "WEAK";

export type Submission = {
  revision: number;
  key: string;
  turn: number;
  answer: string;
  visual?: VisualAnswer | null;
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
  /** "demo" while the server runs the scripted stand-in; only "model" results are real assessments. */
  assessed_by: "demo" | "model" | "unassessed";
  model: string | null;
  hints_seen?: number;
  reference_seen?: boolean;
  evidence: "full" | "reduced" | "none";
  flags: string[];
  replayed: boolean;
  /** What to practise next, decided from this evaluation. Null when the bank has nothing left to suggest. */
  next_question?: NextQuestion | null;
};

/** The engine's suggestion after an evaluation: a servable question and the reason, in the practice language. */
export type NextQuestion = {
  key: string;
  title: string;
  subject: string;
  skill: string;
  difficulty: number;
  why: "reinforce" | "consolidate" | "advance" | "explore";
  reason: string;
  /** what was hard in this attempt, in the practice language, when a known mistake was recognised */
  focus?: string | null;
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
  /** The latest suggestion for this attempt; survives a refresh. */
  next_question?: NextQuestion | null;
};

export type SkillProgress = {
  key: string;
  label: string;
  subject: string;
  level: number | null;
  status: "not_assessed" | "insufficient_evidence" | "assessed";
  trend: "new" | "stable" | "improving" | "declining";
  required_level: number;
  assessments: number;
  last_assessed_at: string | null;
  retention_due_at: string | null;
};

/** One subject rolled up from its skills: what the progress donuts draw. */
export type SubjectProgress = {
  key: string;
  label: string;
  skills_total: number;
  skills_assessed: number;
  skills_started: number;
  /** level ("1".."5") -> number of skills currently at that level */
  levels: Record<string, number>;
  average_level: number | null;
  /** STRONG / PARTIAL / WEAK answer counts in this subject */
  bands: Record<"STRONG" | "PARTIAL" | "WEAK", number>;
  attempts: number;
  /** share of the role plan, 0-1 */
  weight: number;
  questions_available: number;
};

/** The one card meant to inspire: counts and a level in words, never a percentage. */
export type ProgressOverview = {
  answered: number;
  strong: number;
  partial: number;
  weak: number;
  skills_assessed: number;
  skills_total: number;
  /** Getting started | Awareness | Foundational | Proficient | Advanced | Expert (localised) */
  level: string;
  /** 0..5 for the meter */
  level_rank: number;
  message: string;
};

export type TimelinePoint = {
  day: string;
  answered: number;
  strong: number;
  partial: number;
  weak: number;
  /** average assessed level across skills at the end of that day */
  level: number | null;
};

export type PlanItem = {
  /** 0 = today */
  day_index: number;
  date: string;
  mode: "quick" | "deep" | "simulation" | "diagnostic" | "retention_check" | string;
  skills: LabelledSkill[];
  minutes: number;
  reason: string;
  done: boolean;
};

export type Plan = {
  items: PlanItem[];
  minutes_per_day: number;
  days_to_interview: number | null;
  interview_date: string | null;
  generated_for: string;
};

export type Progress = {
  skills: SkillProgress[];
  subjects: SubjectProgress[];
  overview?: ProgressOverview | null;
  timeline?: TimelinePoint[];
  plan?: Plan | null;
  goal?: Goal | null;
  recent: {
    id: string;
    question_key: string;
    subject?: string;
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

// ---------------------------------------------------------------- mock interviews

export type InterviewPlanSkill = {
  skill: string;
  label: string;
  subject: string;
  importance: "core" | "important" | "nice_to_have" | string;
  required_level: number;
  planned_turns: number;
};

export type InterviewTurnStatus = "open" | "evaluating" | "done" | "failed" | "skipped";

/** One interviewer question. Bands and summaries are null until the interview is over. */
export type InterviewTurn = {
  index: number;
  skill: string;
  skill_label: string;
  subject: string;
  difficulty: number;
  archetype: string;
  question: string;
  question_key: string | null;
  /** the question is "on trial": being checked live before publication */
  trial: boolean;
  status: InterviewTurnStatus;
  hints: Hint[];
  answer: string | null;
  /** a drawn circuit and/or photos sent with the answer */
  visual?: VisualAnswer | null;
  /** circuit_assessed | images_assessed | images_unavailable | visual_review_pending ... */
  flags?: string[];
  asked_at: string;
  answered_at: string | null;
  band: Band | null;
  summary: string | null;
  key_points_hit: string[];
  key_points_missed: string[];
  check: Check | null;
  action_after: string | null;
  subject_switch: boolean;
};

export type InterviewStatus = "in_progress" | "evaluating" | "completed";

export type Interview = {
  id: string;
  status: InterviewStatus;
  language: ApiLang;
  duration_min: number;
  elapsed_ms: number;
  remaining_min: number;
  started_at: string;
  ended_at: string | null;
  ended_early: boolean;
  turn_count: number;
  current_turn: InterviewTurn | null;
  turns: InterviewTurn[];
  plan: InterviewPlanSkill[];
  can_answer: boolean;
  can_hint: boolean;
  hints_used: number;
  results_revealed: boolean;
  report_ready: boolean;
};

export type InterviewListItem = {
  id: string;
  status: string;
  duration_min: number | null;
  language: ApiLang | null;
  turn_count: number;
  started_at: string | null;
  ended_at: string | null;
};

export type Fit = {
  fit_score: number | null;
  skills_total: number;
  skills_assessed: number;
  skills_meeting_requirement: number;
  core_gaps: string[];
  top_strengths: string[];
  domain_breakdown: Record<string, number>;
  partial_evaluation: boolean;
  cap_applied: number | null;
};

export type SkillReport = {
  key: string;
  label: string;
  subject: string;
  status: "assessed" | "insufficient_evidence" | "not_assessed" | string;
  proficiency_level: number | null;
  required_level: number;
  level_gap: number | null;
  turns_count: number;
  hints_used: number;
  importance: string;
  strengths: string[];
  gaps: string[];
};

export type LabelledSkill = { key: string; label: string };

export type InterviewReport = {
  session_id: string;
  language: ApiLang;
  duration_min: number;
  turn_count: number;
  /** role | company | session_overall */
  fit: Record<string, Fit>;
  skills: SkillReport[];
  subjects: Record<string, unknown>[];
  timeline: Record<string, unknown>[];
  recommended_next_skills: LabelledSkill[];
  cover_next_time: LabelledSkill[];
  top_tips: string[];
  narrative_md: string;
  narrative_source: "generated" | "fallback" | string;
  turns: InterviewTurn[];
};

export type StartInterviewRequest = {
  duration_min: 20 | 30 | 45;
  language?: ApiLang;
};

export type Me = {
  id: string;
  email: string | null;
  pilot_member: boolean;
  can_manage_tasks: boolean;
};

export type StartAttemptRequest = {
  question_key?: string;
  question_id?: string;
  mode?: "quick" | "deep";
  language?: ApiLang;
  self_confidence?: 1 | 2 | 3 | 4 | 5;
};

export type SubmitRequest = {
  text: string;
  visual?: VisualAnswer | null;
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
  | "no_reviewed_questions"
  | "usage_limit"
  | "evaluation_unavailable"
  | "temporarily_unavailable"
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
    if (!access)
      throw new PracticeApiError("unauthenticated", "not signed in", 401);
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
        cache: "no-store",
        signal: AbortSignal.timeout(method === "GET" ? 65000 : 150000),
      });
    } catch (error) {
      throw new PracticeApiError(
        "network",
        `could not reach the practice API: ${String(error)}`,
        0,
      );
    }
    const requestId = response.headers.get("x-request-id") ?? undefined;
    if (response.ok) return (await response.json()) as T;
    let payload: {
      error?: { code?: string; message?: string; details?: unknown };
    } = {};
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
    health: () =>
      call<{ llm_provider: string; env: string; store: string }>(
        "GET",
        "/health",
      ),
    me: () => call<Me>("GET", "/v1/me"),
    progress: (language?: ApiLang) =>
      call<Progress>("GET", `/v1/me/progress${q({ language })}`),
    getGoal: (language?: ApiLang) =>
      call<Goal>("GET", `/v1/me/goal${q({ language })}`),
    saveGoal: (body: GoalRequest) => call<Goal>("POST", "/v1/me/goal", body),
    jobTypes: (language: ApiLang) =>
      call<JobType[]>("GET", `/v1/job-types${q({ language })}`),
    companies: () => call<Company[]>("GET", "/v1/companies"),

    /** With `job`, only questions relevant to that job type, most relevant first. `company` is a name or slug. */
    listQuestions: (
      language: ApiLang,
      subject?: string,
      filters: { job?: string; company?: string } = {},
    ) =>
      call<QuestionSummary[]>(
        "GET",
        `/v1/questions${q({ language, subject, job: filters.job, company: filters.company })}`,
      ),
    /** "I saw this question at company X". Resolves with the question's company tags afterwards. */
    addSighting: (keyOrId: string, company: string) =>
      call<{ companies: CompanyTag[] }>(
        "POST",
        `/v1/questions/${encodeURIComponent(keyOrId)}/sightings`,
        { company },
      ),
    getQuestion: (keyOrId: string, language: ApiLang) =>
      call<QuestionDetail>(
        "GET",
        `/v1/questions/${encodeURIComponent(keyOrId)}${q({ language })}`,
      ),

    startAttempt: (body: StartAttemptRequest) =>
      call<Attempt>("POST", "/v1/practice/attempts", body),
    getAttempt: (attemptId: string) =>
      call<Attempt>("GET", `/v1/practice/attempts/${attemptId}`),
    nextHint: (attemptId: string) =>
      call<{ hint: Hint | null; attempt: Attempt }>(
        "POST",
        `/v1/practice/attempts/${attemptId}/hints/next`,
      ),

    // mock interviews
    startInterview: (body: StartInterviewRequest) =>
      call<Interview>("POST", "/v1/interviews", body),
    listInterviews: () => call<InterviewListItem[]>("GET", "/v1/interviews"),
    getInterview: (interviewId: string) =>
      call<Interview>("GET", `/v1/interviews/${interviewId}`),
    /** 202 means saved and still being evaluated: poll getInterview until status leaves "evaluating". */
    answerInterview: (
      interviewId: string,
      turnIndex: number,
      answer: string | { text: string; visual?: VisualAnswer | null },
      idempotencyKey: string,
      latencyMs?: number,
    ) =>
      call<{ turn: InterviewTurn; interview: Interview }>(
        "POST",
        `/v1/interviews/${interviewId}/turns/${turnIndex}/answer`,
        {
          answer:
            typeof answer === "string"
              ? answer
              : { text: answer.text, visual: answer.visual ?? null },
          idempotency_key: idempotencyKey,
          latency_ms: latencyMs,
        },
        { "Idempotency-Key": idempotencyKey },
      ),
    interviewHint: (interviewId: string) =>
      call<{ hint: Hint | null; interview: Interview }>(
        "POST",
        `/v1/interviews/${interviewId}/hints/next`,
      ),
    endInterview: (interviewId: string) =>
      call<Interview>("POST", `/v1/interviews/${interviewId}/end`),
    interviewReport: (interviewId: string) =>
      call<InterviewReport>("GET", `/v1/interviews/${interviewId}/report`),
    revealReference: (attemptId: string) =>
      call<{ reference: string; attempt: Attempt }>(
        "POST",
        `/v1/practice/attempts/${attemptId}/reference`,
      ),

    /** Main answer. `idempotencyKey`: one per click, reused on retry (newIdempotencyKey()). */
    submit: (attemptId: string, body: SubmitRequest, idempotencyKey: string) =>
      call<SubmissionResponse>(
        "POST",
        `/v1/practice/attempts/${attemptId}/submissions`,
        {
          answer: { text: body.text, visual: body.visual },
          latency_ms: body.latency_ms,
          revision_count: body.revision_count,
        },
        { "Idempotency-Key": idempotencyKey },
      ),
    submitFollowUp: (
      attemptId: string,
      turn: number,
      body: SubmitRequest,
      idempotencyKey: string,
    ) =>
      call<SubmissionResponse>(
        "POST",
        `/v1/practice/attempts/${attemptId}/follow-ups/${turn}/submissions`,
        {
          answer: { text: body.text, visual: body.visual },
          latency_ms: body.latency_ms,
        },
        { "Idempotency-Key": idempotencyKey },
      ),
    /** After a submission with status "failed": evaluate the saved answer again. */
    retry: (attemptId: string, revision: number) =>
      call<SubmissionResponse>(
        "POST",
        `/v1/practice/attempts/${attemptId}/submissions/${revision}/retry`,
      ),

    /**
     * submit/submitFollowUp/retry answer 202 with status "evaluating" when the model takes longer than
     * the server's response budget (about two minutes); the evaluation continues on the server. Poll
     * with this until the attempt leaves "evaluating". Resolves with the latest attempt view.
     */
    waitForEvaluation: async (
      attemptId: string,
      opts: { intervalMs?: number; timeoutMs?: number } = {},
    ) => {
      const interval = opts.intervalMs ?? 3000;
      const deadline = Date.now() + (opts.timeoutMs ?? 10 * 60 * 1000);
      for (;;) {
        const attempt = await call<Attempt>(
          "GET",
          `/v1/practice/attempts/${attemptId}`,
        );
        if (attempt.status !== "evaluating" || Date.now() > deadline)
          return attempt;
        await new Promise((resolve) => setTimeout(resolve, interval));
      }
    },
  };
}
