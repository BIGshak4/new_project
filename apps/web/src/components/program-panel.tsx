"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Clock3, Compass, RefreshCw, Target } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, Program } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { modeLabel } from "../lib/timeline";

/**
 * "My program" at the top of the library: the next item of the saved plan, chosen for the user's goal and what
 * has been assessed so far. Start opens a practice attempt on a fitting question (or the interview lobby); from
 * there the usual flow continues: answer, feedback, follow-up, the next question picked from the evidence.
 */
export function ProgramPanel({
  api,
  lang,
  goalComplete,
  refreshKey,
  onOpenGoal,
  onStartAttempt,
  onStartInterview,
  onOpenProgress,
}: {
  api: PracticeApi;
  lang: Lang;
  goalComplete: boolean;
  /** changes when something happened that may have ticked or rebuilt the program */
  refreshKey: string;
  onOpenGoal: () => void;
  onStartAttempt: (attemptId: string) => void;
  onStartInterview: (durationMin: number | null) => void;
  onOpenProgress: () => void;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [program, setProgram] = useState<Program | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;

  const load = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    api
      .program(lang)
      .then((p) => {
        if (!cancelled) setProgram(p);
      })
      .catch((e) => {
        if (!cancelled) setMessage(apiMessage(e, lang));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [api, lang]);

  useEffect(() => load(), [load, refreshKey]);

  async function start(itemId?: string) {
    if (busy) return;
    setBusy(true);
    setMessage("");
    try {
      const result = await api.startProgram(itemId, lang);
      if (result.kind === "attempt" && result.attempt) onStartAttempt(result.attempt.id);
      else if (result.kind === "interview") onStartInterview(result.interview_duration_min);
      else {
        setMessage(result.message ?? t("אין מה להתחיל כרגע.", "Nothing to start right now."));
        load();
      }
    } catch (e) {
      setMessage(apiMessage(e, lang));
    } finally {
      setBusy(false);
    }
  }

  const next = program?.next ?? null;
  const total = (program?.today.length ?? 0) + (program?.done_today ?? 0);
  return (
    <section className="daily-panel program-panel" aria-labelledby="program-title">
      <div className="program-main">
        <span className="overview-kicker">
          <Compass size={16} aria-hidden="true" /> {t("התוכנית שלי", "My program")}
        </span>
        {loading && !program ? (
          <p className="muted">{t("טוענים את התוכנית…", "Loading your program…")}</p>
        ) : !goalComplete ? (
          <>
            <h2 id="program-title">{t("נבנה לכם תוכנית עד הראיון.", "Let’s build your plan until the interview.")}</h2>
            <p>
              {t(
                "ספרו לנו לאיזה תפקיד אתם מתכוננים, מתי הראיון וכמה זמן יש לכם ביום. הכול נגזר מזה.",
                "Tell us the job you are preparing for, when the interview is and how much time you have a day. Everything follows from that.",
              )}
            </p>
          </>
        ) : next ? (
          <>
            <h2 id="program-title" dir="auto">
              {modeLabel(next.mode, lang)}
              {" · "}
              {next.skills.map((s) => s.label).join(", ")}
            </h2>
            <p dir="auto">{next.reason}</p>
            <p className="small muted program-meta">
              <Clock3 size={13} aria-hidden="true" /> {next.minutes} {t("דק׳", "min")}
              {next.carried && (
                <span className="badge trial">
                  <RefreshCw size={11} aria-hidden="true" /> {t("הועבר מיום קודם", "carried from an earlier day")}
                </span>
              )}
              {total > 0 && (
                <>
                  {" · "}
                  {program?.done_today ?? 0}/{total} {t("להיום הושלמו", "of today done")}
                </>
              )}
            </p>
          </>
        ) : (
          <>
            <h2 id="program-title">{t("להיום סיימתם.", "You are done for today.")}</h2>
            <p>
              {(program?.done_today ?? 0) > 0
                ? t("כל הכבוד. מחר מחכה הפריט הבא; אפשר גם להציץ במאגר.", "Well done. Tomorrow’s item is waiting; the library is open meanwhile.")
                : t("אין פריט מתוכנן להיום. אפשר לבחור שאלה מהמאגר.", "Nothing is planned for today. Pick a question from the library.")}
            </p>
          </>
        )}
        {message && (
          <p className="small" role="status">
            {message}
          </p>
        )}
      </div>
      <div className="program-actions">
        {!goalComplete ? (
          <button className="primary" onClick={onOpenGoal}>
            <Target size={16} aria-hidden="true" /> {t("להגדיר את היעד", "Set my goal")}
          </button>
        ) : next ? (
          <button className="primary" disabled={busy} onClick={() => void start(next.id ?? undefined)}>
            {busy
              ? t("פותחים…", "Opening…")
              : next.mode === "simulation"
                ? t("לראיון המדומה", "To the mock interview")
                : t("מתחילים", "Start")}{" "}
            <Arrow size={16} aria-hidden="true" />
          </button>
        ) : (
          <button onClick={onOpenProgress}>
            <Check size={16} aria-hidden="true" /> {t("לתוכנית המלאה", "See the full plan")}
          </button>
        )}
        {goalComplete && (
          <button className="text-button" onClick={onOpenProgress}>
            {t("כל התוכנית", "Whole plan")}
          </button>
        )}
      </div>
    </section>
  );
}
