"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  Bookmark,
  Lightbulb,
  RotateCcw,
  Download,
} from "lucide-react";
import type { User } from "@supabase/supabase-js";
import type { Lang } from "./auth";
import { VisualAnswer } from "./visual-answer";
import {
  emptyVisual,
  hasVisual,
  type VisualAnswer as Visual,
} from "../lib/circuit";
import { AnswerEditor } from "./answer-editor";
import { parseTechnicalAnswer } from "../lib/technical-answer";
import { supabase } from "../lib/supabase";
import {
  newIdempotencyKey,
  type Attempt,
  type PracticeApi,
  type QuestionDetail,
  type Submission,
} from "../lib/practice-api";
import {
  apiMessage,
  bandLabel,
  hasAccepted,
  pendingResolved,
  latestSubmission,
  readLocal,
  writeLocal,
  removeLocal,
  type Entry,
  type PendingAnswer,
} from "../lib/practice-ui";

type Props = {
  api: PracticeApi;
  questionKey?: string;
  attemptId?: string;
  lang: Lang;
  user: User;
  entries: Entry[];
  onSaved: (entry: Entry) => void;
  onStarted: (id: string) => void;
  onNew: (key: string) => void;
  onBack: () => void;
  onProgress: () => void;
  demo: boolean;
};

export function PracticeSession({
  api,
  questionKey,
  attemptId,
  lang,
  user,
  entries,
  onSaved,
  onStarted,
  onNew,
  onBack,
  onProgress,
  demo,
}: Props) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [attempt, setAttempt] = useState<Attempt | null>(null),
    [question, setQuestion] = useState<QuestionDetail | null>(null);
  const [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [recoveryRequired, setRecoveryRequired] = useState(false);
  const [answer, setAnswer] = useState(""),
    [followAnswer, setFollowAnswer] = useState("");
  const [visual, setVisual] = useState<Visual>(emptyVisual);
  const [uploading, setUploading] = useState(false);
  const [pending, setPending] = useState<PendingAnswer | null>(null);
  const guard = useRef(false),
    live = useRef(true);
  const key = `jr-attempt-draft-v1-${user.id}-${attemptId}`;
  const entry = entries.find((e) => e.question_id === question?.id);

  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);
  const apply = useCallback(
    (next: Attempt) => {
      setAttempt(next);
      setPending((old) => {
        if (old && pendingResolved(next, old)) return null;
        return old;
      });
    },
    [key],
  );

  const reload = useCallback(async () => {
    if (!attemptId) return;
    const next = await api.getAttempt(attemptId);
    if (live.current) {
      apply(next);
      setRecoveryRequired(false);
    }
    return next;
  }, [api, attemptId, apply]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    (async () => {
      try {
        if (attemptId) {
          const a = await api.getAttempt(attemptId);
          if (cancelled) return;
          setAttempt(a);
          setQuestion(a.question);
          const draft = readLocal<{
            answer?: string;
            visual?: Visual;
            followAnswer?: string;
            pending?: PendingAnswer | null;
            turn?: number;
          }>(key);
          const p =
            draft?.pending && !pendingResolved(a, draft.pending)
              ? draft.pending
              : null;
          setPending(p);
          setVisual(a.submission?.visual ?? draft?.visual ?? emptyVisual());
          setAnswer(a.submission?.answer ?? draft?.answer ?? "");
          setFollowAnswer(
            draft?.turn === a.pending_follow_up?.turn
              ? (draft?.followAnswer ?? "")
              : "",
          );
        } else if (questionKey) {
          const q = await api.getQuestion(questionKey, lang);
          if (!cancelled) setQuestion(q);
        }
      } catch (e) {
        if (!cancelled) setError(apiMessage(e, lang));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // Existing attempts keep their original language and exposure history.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, attemptId, questionKey, key]);

  useEffect(() => {
    if (!question || question.language === lang) return;
    let cancelled = false;
    api
      .getQuestion(question.key, lang)
      .then((q) => {
        if (!cancelled) setQuestion(q);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [api, lang, question?.key, question?.language]);

  // A completed turn must not leave its answer prefilled for a different follow-up.
  const previousTurn = useRef<number | undefined>(undefined);
  useEffect(() => {
    const turn = attempt?.pending_follow_up?.turn;
    if (previousTurn.current !== undefined && previousTurn.current !== turn)
      setFollowAnswer("");
    previousTurn.current = turn;
  }, [attempt?.pending_follow_up?.turn]);

  useEffect(() => {
    // A failed initial GET must never erase a previously saved browser draft.
    if (!attemptId || loading || !attempt) return;
    writeLocal(key, {
      answer,
      visual,
      followAnswer,
      pending,
      turn: attempt?.pending_follow_up?.turn,
    });
  }, [
    answer,
    visual,
    followAnswer,
    pending,
    key,
    loading,
    attemptId,
    attempt?.id,
    attempt?.pending_follow_up?.turn,
  ]);

  // Resume observation after reload. Poll only while the server is evaluating, with bounded retries.
  useEffect(() => {
    if (attempt?.status !== "evaluating" || recoveryRequired) return;
    let cancelled = false,
      timer: ReturnType<typeof setTimeout>;
    const deadline = Date.now() + 10 * 60 * 1000;
    const poll = async () => {
      try {
        const next = await api.getAttempt(attempt.id);
        if (cancelled) return;
        apply(next);
        if (next.status !== "evaluating") {
          onProgress();
          return;
        }
        if (Date.now() < deadline) timer = setTimeout(poll, 3000);
        else {
          setRecoveryRequired(true);
          setError(
            t(
              "ההערכה עדיין מתעכבת. אפשר לבדוק שוב את התוצאה השמורה.",
              "Evaluation is taking longer. You can check the saved result again.",
            ),
          );
        }
      } catch (e) {
        if (!cancelled) {
          setError(apiMessage(e, lang));
          setRecoveryRequired(true);
        }
      }
    };
    timer = setTimeout(poll, 2000);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [
    api,
    attempt?.id,
    attempt?.status,
    apply,
    lang,
    onProgress,
    recoveryRequired,
  ]);

  const mutate = async (work: () => Promise<Attempt>) => {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      const next = await work();
      if (live.current) {
        apply(next);
        setRecoveryRequired(false);
        onProgress();
      }
    } catch (e) {
      if (!live.current) return;
      setError(apiMessage(e, lang));
      setRecoveryRequired(true);
      try {
        await reload();
      } catch {
        /* Keep the draft and require an explicit recovery check. */
      }
    } finally {
      guard.current = false;
      if (live.current) setBusy(false);
    }
  };

  async function start() {
    if (!question || guard.current) return;
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      const a = await api.startAttempt({
        question_key: question.key,
        language: lang,
        mode: "quick",
      });
      const old = readLocal<{ answer?: string }>(
        `jr-draft-${user.id}-${question.id}`,
      );
      writeLocal(`jr-attempt-draft-v1-${user.id}-${a.id}`, {
        answer: old?.answer ?? entry?.answer ?? "",
        followAnswer: "",
        pending: null,
      });
      if (live.current) {
        onProgress();
        onStarted(a.id);
      }
    } catch (e) {
      setError(
        apiMessage(e, lang) +
          " " +
          t(
            "אם הפתיחה התבצעה לפני הניתוק, התרגול יופיע תחת ״התרגול שלי״.",
            "If the attempt was created before disconnecting, find it in My practice.",
          ),
      );
    } finally {
      guard.current = false;
      if (live.current) setBusy(false);
    }
  }

  async function submit() {
    if (
      !attempt ||
      guard.current ||
      uploading ||
      recoveryRequired ||
      attempt.status === "evaluating"
    )
      return;
    const turn = attempt.submission ? attempt.pending_follow_up?.turn : null;
    if (attempt.submission && turn === undefined) return;
    const text = turn === null ? answer : followAnswer;
    if (!pending && !text.trim() && !hasVisual(visual)) return;
    const p: PendingAnswer = pending ?? {
      key: newIdempotencyKey(),
      text,
      visual: hasVisual(visual) ? visual : null,
      turn: turn ?? null,
    };
    setPending(p);
    // Persist identity BEFORE the request; a response lost in transit must not become a new submission.
    writeLocal(key, {
      answer,
      visual,
      followAnswer,
      pending: p,
      turn: attempt.pending_follow_up?.turn,
    });
    await mutate(async () => {
      const result =
        p.turn === null
          ? await api.submit(
              attempt.id,
              { text: p.text, visual: p.visual },
              p.key,
            )
          : await api.submitFollowUp(
              attempt.id,
              p.turn,
              { text: p.text },
              p.key,
            );
      if (live.current && hasAccepted(result.attempt, p)) {
        setFollowAnswer("");
        setPending(null);
      }
      return result.attempt;
    });
  }

  async function checkSaved() {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setError("");
    try {
      await reload();
      onProgress();
    } catch (e) {
      setError(apiMessage(e, lang));
    } finally {
      guard.current = false;
      if (live.current) setBusy(false);
    }
  }

  function download() {
    if (!attempt) return;
    const content = JSON.stringify(
      {
        exported_at: new Date().toISOString(),
        simulated_feedback: demo,
        attempt,
      },
      null,
      2,
    );
    const url = URL.createObjectURL(
      new Blob([content], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `jobrun-attempt-${attempt.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  const disabled = busy || recoveryRequired || attempt?.status === "evaluating";
  const retryable = attempt ? latestSubmission(attempt) : undefined;

  return (
    <>
      <div className="row spread" style={{ marginBottom: 22 }}>
        <button className="text-button" onClick={onBack}>
          <ArrowRight size={17} />
          {t("חזרה למאגר", "Back to library")}
        </button>
        {attempt && (
          <button className="text-button" onClick={download}>
            <Download size={16} />
            {t("הורדת תרגול לבדיקה", "Export for review")}
          </button>
        )}
      </div>
      {error && (
        <div className="notice error" role="alert">
          <span>{error}</span>
          <button
            onClick={
              attempt ? () => void checkSaved() : () => window.location.reload()
            }
            disabled={busy}
          >
            <RotateCcw size={15} />
            {t("בדיקת המצב השמור", "Check saved state")}
          </button>
        </div>
      )}
      {loading ? (
        <div className="loading" role="status">
          {t("טוענים את התרגול השמור…", "Loading your practice…")}
        </div>
      ) : (
        question && (
          <>
            {attempt && attempt.language !== lang && (
              <p className="pilot-note">
                {t(
                  "השאלה מוצגת בעברית. הרמזים והמשוב של התרגול הזה נשמרים בשפה שבה פתחתם אותו.",
                  "The question is shown in English. This attempt keeps hints and feedback in the language it was started in.",
                )}
              </p>
            )}
            <div
              className={`practice-layout ${!attempt ? "practice-preview" : ""}`}
            >
              <section className="question-sheet">
                <div className="row">
                  <span className="badge">
                    {t("קושי", "Difficulty")} {question.difficulty}/10
                  </span>
                  <span className="small muted">
                    {question.estimated_minutes ?? "—"} {t("דקות", "minutes")}
                  </span>
                </div>
                <h1 dir="auto">{question.title}</h1>
                {!attempt && (
                  <p className="preview-guide">
                    {t(
                      "קראו את השאלה ונסו לחשוב על פתרון. כשתהיו מוכנים, ",
                      "Read the question and think through your approach. When you're ready, ",
                    )}
                    <a href="#start-answer">
                      {t("עברו לכתיבת פתרון", "continue to your answer")}
                    </a>
                    .
                  </p>
                )}
                {attempt && (
                  <>
                    <div className="row" style={{ marginTop: 24 }}>
                      <button
                        disabled={
                          disabled ||
                          !!pending ||
                          !attempt.can_submit ||
                          attempt.hints_remaining === 0
                        }
                        onClick={() =>
                          void mutate(
                            async () =>
                              (await api.nextHint(attempt.id)).attempt,
                          )
                        }
                      >
                        <Lightbulb size={16} />
                        {t("הרמז הבא", "Next hint")} ·{" "}
                        {Math.min(
                          attempt.hints.length + 1,
                          question.hint_count,
                        )}
                        /{question.hint_count}
                      </button>
                      <button
                        disabled={disabled || !!pending || !!attempt.reference}
                        onClick={() =>
                          void mutate(
                            async () =>
                              (await api.revealReference(attempt.id)).attempt,
                          )
                        }
                      >
                        {t("הצגת פתרון השאלה", "Reveal solution")}
                      </button>
                    </div>
                    <p className="muted small">
                      {t(
                        "כל רמז מוסיף הכוונה. מספר הרמזים שנפתחו לפני השליחה נלקח בחשבון בהערכת העצמאות. חשיפת פתרון לפני השליחה מסמנת את התשובה כתרגול בעזרת פתרון.",
                        "Each hint adds guidance. Hints opened before submission affect the assessment of independence. Revealing the solution first marks your answer as practice with a reference.",
                      )}
                    </p>
                    <p className="help-status" role="status">
                      {t("רמזים שנפתחו", "Hints opened")}:{" "}
                      {attempt.hints.length}/{question.hint_count} ·{" "}
                      {attempt.reference
                        ? t("הפתרון נחשף", "Solution revealed")
                        : t("הפתרון טרם נחשף", "Solution not revealed")}
                    </p>
                    {attempt.hints.map((h) => (
                      <div className="hint" key={h.level}>
                        <h3>
                          {t("רמז", "Hint")} {h.level}
                        </h3>
                        <RichText text={h.text} />
                      </div>
                    ))}
                    {attempt.reference &&
                      attempt.submission?.status !== "done" && (
                        <ReferenceSolution
                          text={attempt.reference}
                          lang={lang}
                        />
                      )}
                  </>
                )}
                <RichText text={question.prompt} />
                {question.choices && (
                  <ol className="choices">
                    {question.choices.map((c, i) => (
                      <li key={i} dir="auto">
                        {c}
                      </li>
                    ))}
                  </ol>
                )}
                {!attempt && (
                  <section
                    className="practice-start"
                    id="start-answer"
                    aria-labelledby="start-answer-title"
                  >
                    <h2 id="start-answer-title">
                      {t("מוכנים לנסות?", "Ready to give it a try?")}
                    </h2>
                    <p>
                      {t(
                        "כתבו את הפתרון ואת הדרך שבה הגעתם אליו. אם תיתקעו, תוכלו לבקש רמז או להציג פתרון מוצע.",
                        "Write your solution and explain your reasoning. If you get stuck, you can request a hint or reveal a suggested solution.",
                      )}
                    </p>
                    <button
                      className="primary"
                      onClick={() => void start()}
                      disabled={busy}
                    >
                      {busy
                        ? t("פותחים מקום לפתרון…", "Opening your answer…")
                        : t("כתיבת פתרון", "Write my answer")}
                    </button>
                    <p className="small muted">
                      {t(
                        "הלחיצה מתחילה תרגול אחד מהמכסה היומית. אפשר לחזור אליו בהמשך דרך ׳התרגול שלי׳.",
                        "This starts one attempt from your daily allowance. You can return to it later in My practice.",
                      )}
                    </p>
                  </section>
                )}
                <PersonalNotes
                  key={question.id}
                  user={user}
                  questionId={question.id}
                  entry={entry}
                  lang={lang}
                  onSaved={onSaved}
                  draft={attempt?.submission?.answer ?? answer}
                />
              </section>
              <section className="answer-sheet">
                {attempt && (
                  <>
                    <h2>
                      {attempt.submission
                        ? t("התשובה שלך נשמרה", "Your answer is saved")
                        : t(
                            "איך הייתם פותרים את זה?",
                            "How would you solve it?",
                          )}
                    </h2>
                    <p className="muted small">
                      {attempt.submission && demo
                        ? t(
                            "התשובה עדיין לא נבדקה. משוב אישי יופיע לאחר חיבור עוזר התרגול. בינתיים אפשר לפתוח את הפתרון המוצע ולהשוות לתשובה שלך.",
                            "Your answer has not been assessed yet. Personal feedback will be available once the practice assistant is connected. For now, reveal the reference solution and compare it with your answer.",
                          )
                        : attempt.submission
                          ? t(
                              "התשובה ששלחתם מופיעה כאן. מצב המשוב מוצג בהמשך.",
                              "Your submitted answer is shown below. Feedback status follows.",
                            )
                          : t(
                              "כתבו הנחות, הסבירו את הדרך ובדקו מקרי קצה.",
                              "State assumptions, explain your reasoning, and check edge cases.",
                            )}
                    </p>
                    {!attempt.submission ? (
                      <>
                        <AnswerEditor
                          value={answer}
                          onChange={setAnswer}
                          lang={lang}
                          disabled={disabled || !!pending}
                          codeLanguage={question.code_language}
                          starterCode={question.starter_code}
                        />
                        <VisualAnswer
                          value={visual}
                          onChange={setVisual}
                          lang={lang}
                          attemptId={attempt.id}
                          userId={user.id}
                          disabled={disabled || !!pending}
                          onUploading={setUploading}
                        />
                        <p className="muted small">
                          {t(
                            "טיוטה בדפדפן · השליחה שומרת את התשובה בחשבון.",
                            "Browser draft · submitting saves the answer to your account.",
                          )}
                        </p>
                      </>
                    ) : (
                      <SavedAnswer
                        submission={attempt.submission}
                        lang={lang}
                        demo={demo}
                      />
                    )}
                    {attempt.follow_ups.length > 0 && (
                      <p className="small muted">
                        {t(
                          "זהו תרגול מהמסלול הקודם. התשובות הקודמות נשמרו ונכללות בקובץ ההורדה. לתרגול החדש אין שאלות המשך.",
                          "This attempt used the previous flow. Earlier answers remain saved and included in the download. New practice has no follow-up questions.",
                        )}
                      </p>
                    )}
                    {((attempt.can_submit && !attempt.submission) ||
                      !!pending) &&
                      !attempt.can_retry && (
                        <button
                          className="primary"
                          disabled={
                            disabled ||
                            uploading ||
                            (!pending &&
                              ((!answer.trim() && !hasVisual(visual)) ||
                                answer.length > 20000))
                          }
                          onClick={() => void submit()}
                        >
                          {busy
                            ? t("שומרים את הפתרון…", "Saving your solution…")
                            : pending
                              ? t(
                                  "שליחה חוזרת של אותה תשובה",
                                  "Resend the same answer",
                                )
                              : demo || hasVisual(visual)
                                ? t("שמירת הפתרון", "Save my solution")
                                : t("שליחה וקבלת משוב", "Submit for feedback")}
                        </button>
                      )}
                    {attempt.status === "evaluating" && (
                      <div className="evaluation-status" role="status">
                        {t(
                          "התשובה נשמרה. מכינים את המשוב… אפשר לצאת ולחזור לתרגול.",
                          "Your answer is saved. Preparing feedback… you can leave and return to this attempt.",
                        )}
                      </div>
                    )}
                    {attempt.can_retry && retryable && (
                      <div className="notice">
                        <p>
                          {t(
                            "התשובה נשמרה, אבל ההערכה לא הסתיימה. אפשר להעריך שוב את אותה תשובה.",
                            "The answer is saved, but evaluation did not finish. You can retry the same answer.",
                          )}
                        </p>
                        <button
                          disabled={disabled}
                          onClick={() =>
                            void mutate(
                              async () =>
                                (
                                  await api.retry(
                                    attempt.id,
                                    retryable.revision,
                                  )
                                ).attempt,
                            )
                          }
                        >
                          {t("ניסיון הערכה נוסף", "Retry evaluation")}
                        </button>
                      </div>
                    )}
                    {attempt.submission?.status === "done" && (
                      <>
                        <div className="attempt-complete">
                          {!attempt.reference && (
                            <>
                              <button
                                className="primary"
                                disabled={disabled || !!pending}
                                onClick={() =>
                                  void mutate(
                                    async () =>
                                      (await api.revealReference(attempt.id))
                                        .attempt,
                                  )
                                }
                              >
                                {t(
                                  "הצגת הפתרון המוצע להשוואה",
                                  "Reveal reference solution to compare",
                                )}
                              </button>
                              <p className="small muted">
                                {t(
                                  "פתיחת הפתרון כעת לא תשנה את רמת הסיוע שנרשמה לתשובה שכבר שלחתם.",
                                  "Revealing it now will not change the assistance recorded for your submitted answer.",
                                )}
                              </p>
                            </>
                          )}
                          <button
                            onClick={() => {
                              removeLocal(key);
                              onNew(question.key);
                            }}
                          >
                            {t(
                              "תרגול חדש של השאלה",
                              "Practice this question again",
                            )}
                          </button>
                        </div>
                        {attempt.reference && (
                          <ReferenceSolution
                            text={attempt.reference}
                            lang={lang}
                          />
                        )}
                      </>
                    )}
                  </>
                )}
              </section>
            </div>
            <aside
              className="practice-coach"
              aria-labelledby="practice-coach-title"
            >
              <div className="row spread">
                <h2 id="practice-coach-title">
                  {t("עוזר התרגול", "Practice assistant")}
                </h2>
                <span className="badge">
                  {demo
                    ? t("יחובר בהמשך", "Coming later")
                    : t("משוב על הפתרון", "Solution feedback")}
                </span>
              </div>
              {attempt?.submission?.visual ? (
                <p>
                  {t(
                    "התשובה החזותית נשמרה לבדיקה אנושית. הערכת מעגלים ותמונות תתחבר בהמשך; לא חושב ציון ולא שונתה רמת המיומנות.",
                    "Your visual answer is saved for human review. Circuit and image assessment will be connected later; no grade or skill update was generated.",
                  )}
                </p>
              ) : demo || attempt?.submission?.assessed_by === "demo" ? (
                <p>
                  {t(
                    "כאן תוכלו לקבל הכוונה אישית ולדון בדרך הפתרון. העוזר עדיין אינו מחובר, ולכן לא מוצגים ציונים או משובי הדגמה. בינתיים אפשר להיעזר ברמזים המדורגים ובפתרון המוצע.",
                    "This is where you will get personal guidance and discuss your approach. The assistant is not connected yet, so demo grades and feedback are hidden. For now, use the progressive hints and reference solution.",
                  )}
                </p>
              ) : attempt?.submission ? (
                <SubmissionFeedback
                  submission={attempt.submission}
                  lang={lang}
                  demo={false}
                />
              ) : (
                <p>
                  {t(
                    "אחרי שליחת הפתרון, המשוב יופיע כאן. להכוונה בזמן הפתרון אפשר להשתמש ברמזים.",
                    "Feedback appears here after you submit. Use the hints for guidance while solving.",
                  )}
                </p>
              )}
            </aside>
          </>
        )
      )}
    </>
  );
}

function RichText({ text }: { text: string }) {
  return (
    <div className="question-prompt">
      {text.split(/(```[\s\S]*?```)/g).map((part, i) =>
        part.startsWith("```") ? (
          <pre className="code-block" key={i} dir="ltr">
            <code>{part.replace(/^```[^\n]*\n?/, "").replace(/```$/, "")}</code>
          </pre>
        ) : (
          <span dir="auto" key={i}>
            {part}
          </span>
        ),
      )}
    </div>
  );
}

function ReferenceSolution({ text, lang }: { text: string; lang: Lang }) {
  return (
    <div
      className="solution"
      role="region"
      aria-label={lang === "he" ? "הפתרון המוצע" : "Reference solution"}
    >
      <h3>
        {lang === "he"
          ? "פתרון מוצע · בביקורת מקצועית"
          : "Reference · under technical review"}
      </h3>
      <RichText text={text} />
    </div>
  );
}

function SavedAnswer({
  submission: s,
  lang,
  demo,
}: {
  submission: Submission;
  lang: Lang;
  demo: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const parts = parseTechnicalAnswer(s.answer);
  return (
    <section className="saved-answer">
      <h3>{t("התשובה ששלחתם", "Your submitted answer")}</h3>
      {parts.explanation && <RichText text={parts.explanation} />}
      {parts.code && (
        <pre className="code-block" dir="ltr">
          <code>{parts.code}</code>
        </pre>
      )}
      {s.visual && <VisualAnswer value={s.visual} lang={lang} />}
      <p className="help-status">
        {t("רמזים שנראו לפני השליחה", "Hints seen before submission")}:{" "}
        {s.hints_seen ?? "—"}
      </p>
      <p className="small muted">
        {s.reference_seen === true
          ? t(
              "הפתרון נחשף לפני השליחה — נשמר כתרגול בעזרת פתרון, ללא ראיה לשליטה עצמאית.",
              "The solution was revealed before submission — saved as assisted practice, without independent skill evidence.",
            )
          : s.reference_seen === false
            ? t(
                "הפתרון לא נחשף לפני שליחת התשובה.",
                "The solution was not revealed before you submitted.",
              )
            : t(
                "פרטי הסיוע נשמרים עם התרגול.",
                "Assistance is recorded with the attempt.",
              )}
      </p>
      {demo && (
        <p className="small muted">
          {t(
            "הערכת הידע תתאפשר לאחר חיבור עוזר התרגול. כרגע נשמרים הפתרון והשימוש ברמזים.",
            "Skill assessment will be available once the assistant is connected. Your solution and hint usage are saved now.",
          )}
        </p>
      )}
    </section>
  );
}

function SubmissionFeedback({
  submission: s,
  lang,
  demo,
}: {
  submission: Submission;
  lang: Lang;
  demo: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  return (
    <div className="submission-feedback">
      {s.status === "done" && (
        <>
          <div className="row">
            <span className={`badge band-${s.band?.toLowerCase()}`}>
              {bandLabel(s.band, lang)}
            </span>
            {demo && (
              <span className="small muted">
                {t("משוב מדומה", "Simulated feedback")}
              </span>
            )}
          </div>
          {s.summary && <p dir="auto">{s.summary}</p>}
          {s.check && (
            <div className="check-result">
              <strong>
                {s.check.passed === true
                  ? t("הבדיקה האוטומטית עברה", "Automatic check passed")
                  : s.check.passed === false
                    ? t(
                        "הבדיקה האוטומטית מצאה אי־התאמה",
                        "Automatic check found a mismatch",
                      )
                    : t(
                        "הבדיקה האוטומטית לא הכריעה",
                        "Automatic check was inconclusive",
                      )}
              </strong>
              <p dir="auto">{s.check.detail}</p>
            </div>
          )}
          {s.card && (
            <dl className="feedback-card">
              {[
                [t("מה קרה בתשובה", "What happened"), s.card.what_happened],
                [
                  t("למה זה חשוב בראיון", "Why it matters"),
                  s.card.why_it_matters,
                ],
                [t("מה כדאי לעשות בהמשך", "Next step"), s.card.next_step],
                [
                  t("הדרך שלכם מול הפתרון", "Your reasoning and the reference"),
                  s.card.your_reasoning_vs_reference,
                ],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd dir="auto">{value}</dd>
                </div>
              ))}
            </dl>
          )}
          {!!s.key_points_hit.length && (
            <>
              <h4>{t("מה עשיתם היטב", "What went well")}</h4>
              <ul>
                {s.key_points_hit.map((p, i) => (
                  <li dir="auto" key={i}>
                    {p}
                  </li>
                ))}
              </ul>
            </>
          )}
          {!!s.key_points_missed.length && (
            <>
              <h4>{t("מה כדאי לחזק", "What to work on")}</h4>
              <ul>
                {s.key_points_missed.map((p, i) => (
                  <li dir="auto" key={i}>
                    {p}
                  </li>
                ))}
              </ul>
            </>
          )}
          {s.tip && (
            <div className="hint" dir="auto">
              {s.tip.text}
            </div>
          )}
          <p className="small muted">
            {s.evidence === "none"
              ? t(
                  "התשובה אינה מוסיפה ראיה לשליטה עצמאית.",
                  "This answer adds no independent skill evidence.",
                )
              : s.evidence === "reduced"
                ? t(
                    "משקל ההערכה הופחת לפי תנאי התרגול והחשיפה לשאלה.",
                    "Evidence weight is reduced based on practice conditions and question exposure.",
                  )
                : t(
                    "התשובה נכללת בהערכת המיומנות.",
                    "This answer contributes skill evidence.",
                  )}
          </p>
        </>
      )}
      {s.status === "failed" && (
        <p className="notice">
          {t(
            "ההערכה לא הושלמה. התשובה נשמרה.",
            "Evaluation failed. Your answer is saved.",
          )}
        </p>
      )}
    </div>
  );
}

function PersonalNotes({
  user,
  questionId,
  entry,
  lang,
  onSaved,
  draft,
}: {
  user: User;
  questionId: string;
  entry?: Entry;
  lang: Lang;
  onSaved: (e: Entry) => void;
  draft: string;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [rating, setRating] = useState(entry?.self_rating ?? 0),
    [completed, setCompleted] = useState(entry?.completed ?? false);
  const guard = useRef(false);
  useEffect(() => {
    setRating(entry?.self_rating ?? 0);
    setCompleted(entry?.completed ?? false);
  }, [entry?.self_rating, entry?.completed]);
  async function save(
    bookmarked = entry?.bookmarked ?? false,
    saveDraft = false,
  ) {
    if (guard.current) return;
    guard.current = true;
    setBusy(true);
    setMessage("");
    const payload = {
      bookmarked,
      self_rating: rating || null,
      completed,
      ...(saveDraft ? { answer: draft } : {}),
    };
    try {
      const result = entry
        ? await supabase
            .from("jr_practice_entries")
            .update(payload)
            .eq("id", entry.id)
            .eq("version", entry.version)
            .select()
            .maybeSingle()
        : await supabase
            .from("jr_practice_entries")
            .insert({ ...payload, user_id: user.id, question_id: questionId })
            .select()
            .single();
      if (result.error || !result.data) throw new Error("save conflict");
      onSaved(result.data);
      setMessage(t("נשמר בחשבון.", "Saved to your account."));
    } catch {
      setMessage(
        t(
          "השמירה לא הושלמה. ייתכן שיש שינוי בחלון אחר; חזרו למאגר וטענו מחדש.",
          "Save failed. Another tab may have changed this entry; return to the library and reload.",
        ),
      );
    } finally {
      guard.current = false;
      setBusy(false);
    }
  }
  return (
    <div className="personal-notes">
      <button
        disabled={busy}
        aria-pressed={entry?.bookmarked ?? false}
        onClick={() => void save(!entry?.bookmarked)}
      >
        <Bookmark
          size={16}
          fill={entry?.bookmarked ? "currentColor" : "none"}
        />
        {entry?.bookmarked
          ? t("שמורה להמשך", "Bookmarked")
          : t("שמירה להמשך", "Bookmark")}
      </button>
      <details>
        <summary>
          {t("הדיווח העצמי והטיוטה שלי", "My self-assessment and draft")}
        </summary>
        <label className="setup-label">
          {t("איך הרגשתם עם הנושא?", "How did this topic feel?")}
          <select
            value={rating}
            onChange={(e) => setRating(Number(e.target.value))}
          >
            <option value={0}>{t("ללא דירוג", "No rating")}</option>
            <option value={1}>
              {t("צריך לחזור על הנושא", "Need to revisit")}
            </option>
            <option value={2}>{t("בכיוון", "Getting there")}</option>
            <option value={3}>{t("מרגיש בטוח", "Feeling confident")}</option>
          </select>
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={completed}
            onChange={(e) => setCompleted(e.target.checked)}
          />
          {t("סיימתי ללמוד את השאלה", "I finished studying this question")}
        </label>
        {entry?.answer && (
          <details>
            <summary>
              {t("הטיוטה השמורה בחשבון", "Draft saved to account")}
            </summary>
            <RichText text={entry.answer} />
          </details>
        )}
        <div className="row">
          <button disabled={busy} onClick={() => void save()}>
            {t("שמירת דיווח עצמי", "Save self-assessment")}
          </button>
          {!!draft && (
            <button disabled={busy} onClick={() => void save(undefined, true)}>
              {t("שמירת טיוטה לחשבון", "Save draft to account")}
            </button>
          )}
        </div>
        <p className="small muted">
          {t(
            "הדיווח העצמי אינו משנה את הערכת המנוע.",
            "Self-assessment does not change the engine assessment.",
          )}
        </p>
      </details>
      <p className="small" role="status">
        {message}
      </p>
    </div>
  );
}
