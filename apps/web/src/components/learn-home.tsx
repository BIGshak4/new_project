"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Clock3, Lock, Mic, Play, RefreshCw, Target } from "lucide-react";
import type { Lang } from "./auth";
import { SkillStrength, StreakCard } from "./skill-strength";
import type { Goal, PracticeApi, Program, Progress } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { dayLabel, modeLabel } from "../lib/timeline";
import { daysToGoLabel, nodeStyle, pathNodes, todayProgress, type PathNode } from "../lib/path";

const AMPLITUDE = 150;

/**
 * The Learn home: the saved program drawn as a winding path of nodes (done = green tick, the next item = large
 * with Start, the rest locked; a mock interview is a yellow microphone), a unit band with the goal, and a side
 * column with today's progress, skill strength and the streak. Start goes through the same program flow as
 * before: an attempt opens for a practice item, the interview lobby for a simulation item.
 */
export function LearnHome({
  api,
  lang,
  goal,
  progress,
  refreshKey,
  goalSlot,
  onStartAttempt,
  onStartInterview,
  onOpenGoal,
  onOpenProgress,
  onOpenLibrary,
}: {
  api: PracticeApi;
  lang: Lang;
  goal: Goal | null;
  progress: Progress;
  /** changes when something may have ticked or rebuilt the program */
  refreshKey: string;
  /** the goal card when the goal is incomplete (or being edited) */
  goalSlot?: React.ReactNode;
  onStartAttempt: (attemptId: string) => void;
  onStartInterview: (durationMin: number | null) => void;
  onOpenGoal: () => void;
  onOpenProgress: () => void;
  onOpenLibrary: () => void;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [program, setProgram] = useState<Program | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");

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

  async function start(node: PathNode) {
    const id = node.item.id ?? undefined;
    if (busy) return;
    setBusy(id ?? "next");
    setMessage("");
    try {
      const result = await api.startProgram(id, lang);
      if (result.kind === "attempt" && result.attempt) onStartAttempt(result.attempt.id);
      else if (result.kind === "interview") onStartInterview(result.interview_duration_min);
      else {
        setMessage(result.message ?? t("אין מה להתחיל כרגע.", "Nothing to start right now."));
        load();
      }
    } catch (e) {
      setMessage(apiMessage(e, lang));
    } finally {
      setBusy(null);
    }
  }

  const goalComplete = !!goal?.complete;
  const items = program?.plan.items ?? [];
  const nodes = pathNodes(items, program?.next?.id ?? null);
  const today = todayProgress(program);
  const overview = progress.overview ?? null;
  const daysLabel = daysToGoLabel(goal?.days_to_interview ?? program?.plan.days_to_interview, lang);
  const minutes = goal?.minutes_per_day ?? program?.plan.minutes_per_day ?? null;
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  const interviewDate = goal?.interview_date
    ? new Date(`${goal.interview_date}T12:00:00`).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB", { day: "numeric", month: "short" })
    : null;
  const unitTitle = program?.next
    ? program.next.skills.map((s) => s.label).join(", ")
    : today.total > 0 && today.done === today.total
      ? t("להיום סיימתם", "Done for today")
      : t("הדרך שלכם", "Your path");
  const remainingMinutes = program?.minutes_due_today ?? 0;

  return (
    <div className="learn">
      <div className="learn-main">
        <header className="learn-head">
          <div>
            <div className="kicker" dir="auto">
              {goal?.job_type_label ?? t("סוג התפקיד לא נבחר עדיין", "No job type chosen yet")}
              {interviewDate ? ` · ${t("ראיון ב", "interview on")}${lang === "he" ? "-" : " "}${interviewDate}` : ""}
            </div>
            <h1>{daysLabel ? `${t("הדרך שלכם, ", "Your path, ")}${daysLabel}` : t("הדרך שלכם", "Your path")}</h1>
          </div>
          {minutes ? (
            <button type="button" className="pill-button" onClick={onOpenGoal} aria-label={t("עריכת היעד", "Edit goal")}>
              <Clock3 size={15} aria-hidden="true" /> {minutes} {t("דק׳ ביום", "min a day")}
            </button>
          ) : null}
        </header>

        {goalSlot}

        <section className="path-card" aria-label={t("התוכנית שלי", "My program")}>
          <div className="unit-band">
            <span className="unit-label">{t("היום", "Today")}</span>
            <span className="unit-title" dir="auto">
              {unitTitle}
            </span>
            {today.total > 0 && (
              <span className="unit-count">
                {today.done} {t("מתוך", "of")} {today.total}
              </span>
            )}
          </div>

          {loading && !program ? (
            <p className="loading" role="status">
              {t("טוענים את התוכנית…", "Loading your program…")}
            </p>
          ) : !goalComplete ? (
            <div className="path-empty">
              <Target size={28} aria-hidden="true" />
              <h2>{t("נבנה לכם תוכנית עד הראיון.", "Let’s build your plan until the interview.")}</h2>
              <p>
                {t(
                  "ספרו לנו לאיזה תפקיד אתם מתכוננים, מתי הראיון וכמה זמן יש לכם ביום. הכול נגזר מזה.",
                  "Tell us the job you are preparing for, when the interview is and how much time you have a day. Everything follows from that.",
                )}
              </p>
              <button type="button" className="primary" onClick={onOpenGoal}>
                {t("להגדיר את היעד", "Set my goal")}
              </button>
            </div>
          ) : nodes.length === 0 ? (
            <div className="path-empty">
              <h2>{t("עוד אין תוכנית לצייר.", "Nothing to draw yet.")}</h2>
              <p>
                {t(
                  "כשיהיו שאלות מאושרות במאגר התוכנית תופיע כאן. בינתיים אפשר לבחור שאלה מהמאגר.",
                  "The plan appears here once the bank has approved questions. Meanwhile, pick a question from the library.",
                )}
              </p>
              <button type="button" onClick={onOpenLibrary}>
                {t("למאגר השאלות", "To the library")}
              </button>
            </div>
          ) : (
            <ol className="path" aria-label={t("שלבי התוכנית", "Program steps")}>
              {nodes.map((node, i) => {
                const previousDay = i > 0 ? nodes[i - 1].dayIndex : null;
                const showDay = node.dayIndex !== previousDay;
                return (
                  <li key={node.key} className={`path-row state-${node.state} kind-${node.kind}`} style={nodeStyle(node.offset, AMPLITUDE)}>
                    {showDay && node.dayIndex > 0 && (
                      <span className="path-day">{dayLabel(node.item.date, node.dayIndex, lang)}</span>
                    )}
                    <div className="path-node-wrap">
                      {node.state === "current" ? (
                        <button
                          type="button"
                          className="path-node"
                          onClick={() => void start(node)}
                          disabled={!!busy}
                          aria-label={`${t("להתחיל", "Start")}: ${modeLabel(node.item.mode, lang)} · ${node.item.skills.map((s) => s.label).join(", ")}`}
                        >
                          {node.kind === "interview" ? <Mic size={38} aria-hidden="true" /> : <Play size={38} aria-hidden="true" fill="currentColor" />}
                        </button>
                      ) : (
                        <span className="path-node" aria-hidden="true">
                          {node.state === "done" ? (
                            <Check size={32} strokeWidth={3.2} />
                          ) : node.kind === "interview" ? (
                            <Mic size={30} />
                          ) : (
                            <Lock size={28} />
                          )}
                        </span>
                      )}
                    </div>
                    <div className="path-text">
                      <div className="path-title" dir="auto">
                        {node.kind === "interview"
                          ? `${t("ראיון מדומה", "Mock interview")}, ${node.item.minutes} ${t("דק׳", "min")}`
                          : node.item.skills.map((s) => s.label).join(", ")}
                        {node.carried && (
                          <span className="badge carried">
                            <RefreshCw size={11} aria-hidden="true" /> {t("הועבר", "carried")}
                          </span>
                        )}
                      </div>
                      {node.state === "current" ? (
                        <>
                          <p className="path-reason" dir="auto">
                            {modeLabel(node.item.mode, lang)} · {node.item.minutes} {t("דק׳", "min")}. {node.item.reason}
                          </p>
                          <button type="button" className="primary start-button" disabled={!!busy} onClick={() => void start(node)}>
                            {busy
                              ? t("פותחים…", "Opening…")
                              : node.kind === "interview"
                                ? t("לראיון", "Interview")
                                : node.item.status === "started"
                                  ? t("להמשיך", "Continue")
                                  : t("להתחיל", "Start")}{" "}
                            <Arrow size={16} aria-hidden="true" />
                          </button>
                        </>
                      ) : (
                        <span className="path-sub">
                          {node.state === "done"
                            ? t("הושלם", "Done")
                            : node.state === "skipped"
                              ? t("דולג", "Skipped")
                              : node.dayIndex === 0
                                ? modeLabel(node.item.mode, lang)
                                : dayLabel(node.item.date, node.dayIndex, lang)}
                          {node.state !== "done" && node.state !== "skipped" ? ` · ${node.item.minutes} ${t("דק׳", "min")}` : ""}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          )}
          {message && (
            <p className="notice path-message" role="status">
              {message}
            </p>
          )}
          {goalComplete && nodes.length > 0 && (
            <div className="path-foot">
              <button type="button" className="text-button" onClick={onOpenProgress}>
                {t("כל התוכנית בטבלה", "The whole plan as a table")} <Arrow size={14} aria-hidden="true" />
              </button>
            </div>
          )}
        </section>
      </div>

      <aside className="learn-side">
        <section className="side-card today-card" aria-labelledby="today-title">
          <div className="side-head">
            <h2 id="today-title">{t("היום", "Today")}</h2>
            <span className="muted">
              {today.total > 0 ? `${today.done} ${t("מתוך", "of")} ${today.total}` : "—"}
            </span>
          </div>
          <div className="meter" role="progressbar" aria-valuemin={0} aria-valuemax={today.total || 1} aria-valuenow={today.done}>
            <span style={{ width: `${Math.round(today.fraction * 100)}%` }} />
          </div>
          <p>
            {today.total === 0
              ? t("אין פריטים להיום עדיין.", "Nothing due today yet.")
              : today.done >= today.total
                ? t("היום הושלם. כל הכבוד.", "Today is done. Well done.")
                : today.total - today.done === 1
                  ? `${t("עוד אחד והיום הושלם.", "One more and today is done.")} ${remainingMinutes} ${t("דק׳ נותרו.", "minutes left.")}`
                  : `${today.total - today.done} ${t("נותרו להיום.", "left today.")} ${remainingMinutes} ${t("דק׳.", "min.")}`}
          </p>
          {overview && (overview.xp_today ?? 0) > 0 && (
            <p className="xp-today">+{overview.xp_today} XP {t("היום", "today")}</p>
          )}
        </section>
        <SkillStrength skills={progress.skills} lang={lang} />
        <StreakCard days={overview?.streak_days ?? 0} todayDone={(overview?.xp_today ?? 0) > 0} lang={lang} />
      </aside>
    </div>
  );
}
