"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Clock3, Mic, Play, RefreshCw, Target } from "lucide-react";
import type { Lang } from "./auth";
import { SkillStrength, StreakCard } from "./skill-strength";
import { SubjectSketch, sketchCaption } from "./sketches";
import type { Goal, PracticeApi, Program, Progress } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { dayLabel, modeLabel } from "../lib/timeline";
import { daysToGoLabel, pathNodes, todayProgress, type PathNode } from "../lib/path";
import { revealDelay, shouldScrollToNode } from "../lib/ui";
import { Breathe, Pop, motion, spring, useReducedMotion } from "./ui/motion";

/** The real adaptive program, displayed in the approved Ion shell. */
export function LearnHome({
  api,
  lang,
  goal,
  progress,
  refreshKey,
  goalSlot,
  userName,
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
  /** the user's first name, for the kicker */
  userName?: string;
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

  // on open, bring the day's sheet into view once (only if it is not already visible)
  const reduced = useReducedMotion();
  const scrolled = useRef(false);
  useEffect(() => {
    if (scrolled.current || !program) return;
    const el = document.querySelector<HTMLElement>(".today-sheet");
    if (!el) return;
    scrolled.current = true;
    if (shouldScrollToNode(el.getBoundingClientRect(), window.innerHeight)) {
      el.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
    }
  }, [program, reduced]);

  async function start(node: PathNode | null) {
    const id = node?.item.id ?? undefined;
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

  const goalComplete = goal ? !!goal.complete : !!program?.goal_complete;
  const items = program?.plan.items ?? [];
  const nodes = pathNodes(items, program?.next?.id ?? null);
  const todayNodes = nodes.filter((n) => n.dayIndex === 0);
  const laterNodes = nodes.filter((n) => n.dayIndex > 0);
  const current = todayNodes.find((n) => n.state === "current") ?? null;
  const today = todayProgress(program);
  const overview = progress.overview ?? null;
  const daysLabel = daysToGoLabel(goal?.days_to_interview ?? program?.plan.days_to_interview, lang);
  const minutes = goal?.minutes_per_day ?? program?.plan.minutes_per_day ?? null;
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  const interviewDate = goal?.interview_date
    ? new Date(`${goal.interview_date}T12:00:00`).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB", { day: "numeric", month: "long" })
    : null;
  const remainingMinutes = program?.minutes_due_today ?? 0;
  const subjectOf = (skillKey: string | undefined) => progress.skills?.find((s) => s.key === skillKey)?.subject ?? null;

  const currentSkills = current?.item.skills.map((s) => s.label).join(", ") ?? "";

  // the corner stamp: yesterday's band from the timeline, today's items and minutes
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yKey = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;   // the local day, as the user counts days
  const yPoint = progress.timeline?.find((p) => p.day === yKey);
  const yesterdayWord = !yPoint
    ? "—"
    : yPoint.strong >= yPoint.partial && yPoint.strong >= yPoint.weak
      ? t("חזקה", "strong")
      : yPoint.partial >= yPoint.weak
        ? t("חלקית", "partial")
        : t("לחיזוק", "needs work");

  // The title is grounded in the current program item.
  const topic = goalComplete && current ? current.item.skills[0]?.label ?? "" : "";
  const title = !goalComplete
    ? t("נבנה לכם תוכנית עד הראיון.", "Let’s build your plan until the interview.")
    : current
      ? current.kind === "interview"
        ? t("היום ראיון מדומה.", "Today, a mock interview.")
        : t("היום עובדים על ", "Today’s work: ")
      : today.total > 0 && today.done >= today.total
        ? t("להיום סיימתם.", "Done for today.")
        : t("הדרך שלכם.", "Your path.");

  // one sentence of attitude per mode
  const modeLine =
    current?.kind === "interview"
      ? t(`ראיון של ${current.item.minutes} דקות. הציונים נחשפים בסוף, בדוח.`, `A ${current.item.minutes}-minute interview. Grades are revealed at the end, in the report.`)
      : current?.item.mode === "quick"
        ? t("שאלה קצרה. משוב ושאלת המשך שנולדת מהתשובה שלכם. אין פה טריק, יש פה דיוק.", "A short question. Feedback and a follow-up born from your answer. No trick here, just precision.")
        : t("תרגול מעמיק: התשובה, שאלת המשך, ואז השאלה הבאה שנבחרת לפי מה שכתבתם.", "Deep practice: your answer, one follow-up, then the next question chosen by what you wrote.");

  const tomorrow = laterNodes.find((n) => n.dayIndex === 1) ?? laterNodes[0] ?? null;

  return (
    <div className="learn">
      <div className="learn-main">
        <header className="learn-head">
          <div>
            <h1 dir="auto">
              {daysLabel && goalComplete ? `${daysLabel}. ` : ""}
              {title}
              {topic && current?.kind !== "interview" && <span className="mark"><bdi dir="auto">{topic}</bdi>.</span>}
            </h1>
            <div className="learn-context" dir="auto">
              {[userName, goal?.job_type_label ?? t("סוג התפקיד לא נבחר עדיין", "No job type chosen yet"), interviewDate ? `${t("ראיון ב", "interview on")}${lang === "he" ? "־" : " "}${interviewDate}` : null]
                .filter(Boolean)
                .join(" · ")}
            </div>
          </div>
          {goalComplete && (
            <p className="stamp" role="note" aria-label={t("סיכום היום", "Today in numbers")} dir={lang === "he" ? "rtl" : "ltr"}>
              {today.total} {today.total === 1 ? t("פריט", "item") : t("פריטים", "items")} · {remainingMinutes || minutes || 0} {t("דק׳", "min")}
              <br />
              {t("אתמול", "yesterday")}: {yesterdayWord}
              <br />
              {t("רצף", "streak")}: {overview?.streak_days ?? 0}
            </p>
          )}
        </header>

        {goalSlot}

        {loading && !program ? (
          <p className="loading loading-sheet" role="status">
            {t("טוענים את התוכנית…", "Loading your program…")}
          </p>
        ) : !goalComplete ? (
          <section className="sheet path-empty">
            <Target size={28} aria-hidden="true" />
            <p>
              {t(
                "ספרו לנו לאיזה תפקיד אתם מתכוננים, מתי הראיון וכמה זמן יש לכם ביום. הכול נגזר מזה.",
                "Tell us the job you are preparing for, when the interview is and how much time you have a day. Everything follows from that.",
              )}
            </p>
            <button type="button" className="primary" onClick={onOpenGoal}>
              {t("להגדיר את היעד", "Set my goal")}
            </button>
          </section>
        ) : nodes.length === 0 ? (
          <section className="sheet path-empty">
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
          </section>
        ) : (
          <>
            <section className="sheet today-sheet" aria-label={t("הפריט של עכשיו", "The item to do now")}>
              {current ? (
                <>
                  <h2 className="sheet-title" dir="auto">
                    {current.kind === "interview"
                      ? t(`ראיון מדומה, ${current.item.minutes} דקות, על ${currentSkills}.`, `A ${current.item.minutes}-minute mock interview on ${currentSkills}.`)
                      : `${modeLabel(current.item.mode, lang)} ${t("על", "on")} ${currentSkills}.`}
                  </h2>
                  <div className="sheet-row">
                    <span className="tag">
                      {t("עכשיו", "Now")} · {today.done + 1}/{today.total} · {current.item.minutes} {t("דק׳", "min")}
                    </span>
                    <span className="sheet-skill" dir="auto">{currentSkills}</span>
                  </div>
                  <p className="sheet-why" dir="auto">
                    {current.item.reason} {modeLine}
                  </p>
                  <div className="sheet-actions">
                    <button type="button" className="primary" disabled={!!busy} onClick={() => void start(current)}>
                      {busy
                        ? t("פותחים…", "Opening…")
                        : current.kind === "interview"
                          ? t("לראיון", "To the interview")
                          : current.item.status === "started"
                            ? t("להמשיך מאיפה שעצרתם", "Continue where you stopped")
                            : t(`${minutesWord(current.item.minutes, lang)}. קדימה`, `${current.item.minutes} minutes. Go`)}{" "}
                      <Arrow size={16} aria-hidden="true" />
                    </button>
                    {current.carried && (
                      <span className="badge carried">
                        <RefreshCw size={11} aria-hidden="true" /> {t("הועבר מאתמול", "carried from yesterday")}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <>
                  <h2 className="sheet-title">{today.total > 0 ? t("להיום סיימתם. כל הכבוד.", "Done for today. Well done.") : t("אין פריט מתוכנן להיום.", "Nothing planned for today.")}</h2>
                  <p className="sheet-why">
                    {today.total > 0
                      ? t("מחר מחכה הפריט הבא. בינתיים המאגר פתוח.", "Tomorrow’s item is waiting. The library is open meanwhile.")
                      : t("אפשר לבחור שאלה מהמאגר.", "Pick a question from the library.")}
                  </p>
                  <div className="sheet-actions">
                    <button type="button" onClick={onOpenLibrary}>
                      {t("למאגר השאלות", "To the library")}
                    </button>
                  </div>
                </>
              )}

              {todayNodes.length > 0 && (
                <div className="trace" role="group" aria-label={t("הפריטים של היום", "Today’s items")}>
                  <Trace count={todayNodes.length} lit={todayNodes.filter((n) => n.state === "done").length + (current ? 1 : 0)} />
                  <ol className="probes">
                    {todayNodes.map((node, i) => (
                      <motion.li
                        key={node.key}
                        className={`probe state-${node.state} kind-${node.kind}`}
                        initial={reduced ? false : { opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ ...spring, delay: revealDelay(i, !!reduced) }}
                      >
                        <Breathe className="probe-dot-wrap" active={node.state === "current" && !busy}>
                          {node.state === "current" ? (
                            <button
                              type="button"
                              className="probe-dot"
                              onClick={() => void start(node)}
                              disabled={!!busy}
                              aria-label={`${t("להתחיל", "Start")}: ${modeLabel(node.item.mode, lang)} · ${node.item.skills.map((s) => s.label).join(", ")}`}
                            >
                              {node.kind === "interview" ? <Mic size={20} aria-hidden="true" /> : <Play size={20} aria-hidden="true" fill="currentColor" />}
                            </button>
                          ) : (
                            <span className="probe-dot" aria-hidden="true">
                              {node.state === "done" ? (
                                <Pop delay={revealDelay(i, !!reduced) + 0.12}>
                                  <Check size={20} strokeWidth={3} />
                                </Pop>
                              ) : node.kind === "interview" ? (
                                <Mic size={18} />
                              ) : (
                                i + 1
                              )}
                            </span>
                          )}
                        </Breathe>
                        <b dir="auto">{node.kind === "interview" ? t("ראיון מדומה", "Mock interview") : node.item.skills.map((s) => s.label).join(", ")}</b>
                        <span>
                          {node.state === "done"
                            ? t("הושלם", "done")
                            : node.state === "current"
                              ? `${t("עכשיו", "now")} · ${node.item.minutes} ${t("דק׳", "min")}`
                              : node.state === "skipped"
                                ? t("דולג", "skipped")
                                : `${modeLabel(node.item.mode, lang)} · ${node.item.minutes} ${t("דק׳", "min")}`}
                        </span>
                      </motion.li>
                    ))}
                  </ol>
                </div>
              )}
            </section>

            {laterNodes.length > 0 && (
              <section className="later" aria-label={t("בהמשך השבוע", "Later this week")}>
                <h3>{t("בהמשך השבוע", "Later this week")}</h3>
                <ol>
                  {laterNodes.slice(0, 8).map((node, i) => {
                    const previousDay = i > 0 ? laterNodes[i - 1].dayIndex : null;
                    return (
                      <li key={node.key} className={node.dayIndex !== previousDay ? "first" : ""}>
                        <span className="later-day">{node.dayIndex !== previousDay ? dayLabel(node.item.date, node.dayIndex, lang) : ""}</span>
                        <span className="later-what" dir="auto">
                          {node.kind === "interview" ? t("ראיון מדומה", "Mock interview") : node.item.skills.map((s) => s.label).join(", ")}
                        </span>
                        <span className="later-mode">
                          {modeLabel(node.item.mode, lang)} · {node.item.minutes} {t("דק׳", "min")}
                        </span>
                      </li>
                    );
                  })}
                </ol>
                <button type="button" className="text-button" onClick={onOpenProgress}>
                  {t("כל התוכנית בטבלה", "The whole plan as a table")} <Arrow size={14} aria-hidden="true" />
                </button>
              </section>
            )}
          </>
        )}
        {message && (
          <p className="notice path-message" role="status">
            {message}
          </p>
        )}
      </div>

      <aside className="learn-side">
        <section className="panel today-panel" aria-labelledby="today-title">
          <h3 id="today-title">
            {t("היום", "Today")}
            <small>
              {today.total > 0 ? `${today.done} / ${today.total} · ${remainingMinutes} ${t("דק׳ נשארו", "min left")}` : "—"}
            </small>
          </h3>
          <div
            className="bar"
            role="progressbar"
            aria-label={t("התקדמות היום", "Today's progress")}
            aria-valuemin={0}
            aria-valuemax={today.total || 1}
            aria-valuenow={today.done}
          >
            <i style={{ width: `${Math.round(today.fraction * 100)}%` }} />
          </div>
          <p className="note">
            {today.total === 0
              ? t("אין פריטים להיום עדיין.", "Nothing due today yet.")
              : today.done >= today.total
                ? t("היום סגור. מחר בשעה הזאת שוב.", "Today is closed. Same time tomorrow.")
                : today.done === 0
                  ? today.total === 1
                    ? t(`פריט אחד, ${remainingMinutes} דקות. הראשון הוא הקשה.`, `One item, ${remainingMinutes} minutes. The first one is the hard one.`)
                    : t(`${today.total} פריטים ו־${remainingMinutes} דקות. הראשון הוא הקשה.`, `${today.total} items and ${remainingMinutes} minutes. The first one is the hard one.`)
                  : today.total - today.done === 1
                    ? t("עוד אחד ואתם סוגרים את היום.", "One more and today is closed.")
                    : t(`${today.done} בפנים. עוד ${today.total - today.done} קצרים ואתם סוגרים את היום.`, `${today.done} in. ${today.total - today.done} more and today is closed.`)}
            {overview && (overview.xp_today ?? 0) > 0 ? (
              <>
                {" "}
                <bdi dir="ltr">+{overview.xp_today} XP</bdi> {t("עד עכשיו.", "so far.")}
              </>
            ) : null}
          </p>
        </section>
        <SkillStrength skills={progress.focus_skills ?? []} lang={lang} limit={5} ordered hotKey={current?.item.skills[0]?.key} />
        <StreakCard days={overview?.streak_days ?? 0} todayDone={(overview?.xp_today ?? 0) > 0} lang={lang} />
        {tomorrow && (
          <div className="sticky" dir="auto">
            {t("מחר: ", "Tomorrow: ")}
            {tomorrow.kind === "interview" ? t("ראיון מדומה", "a mock interview") : tomorrow.item.skills.map((s) => s.label).join(", ")}
            {" · "}
            {modeLabel(tomorrow.item.mode, lang)} · {tomorrow.item.minutes} {t("דק׳", "min")}
            <small>{t("פתק מהמאמן · מתעדכן כל בוקר", "A note from the coach · refreshed every morning")}</small>
          </div>
        )}
        {minutes ? (
          <button type="button" className="pill-button" onClick={onOpenGoal} aria-label={t("עריכת היעד", "Edit goal")}>
            <Clock3 size={15} aria-hidden="true" /> {minutes} {t("דק׳ ביום · עריכת היעד", "min a day · edit goal")}
          </button>
        ) : null}
      </aside>
    </div>
  );
}

/** The signal trace: one pulse per item; the first `lit` pulses are drawn in the signal colour. Mirrored in RTL by CSS. */
function Trace({ count, lit }: { count: number; lit: number }) {
  const w = 1000;
  const seg = w / Math.max(1, count);
  const pulse = (i: number) => `H${(i * seg + seg / 2 - 10).toFixed(1)} V30 H${(i * seg + seg / 2 + 10).toFixed(1)} V90`;
  const all = `M0 90 ${Array.from({ length: count }, (_, i) => pulse(i)).join(" ")} H${w}`;
  const litCount = Math.min(count, Math.max(0, lit));
  const litPath = litCount === 0 ? "" : `M0 90 ${Array.from({ length: litCount }, (_, i) => pulse(i)).join(" ")} H${(litCount * seg - 6).toFixed(1)}`;
  return (
    <svg className="trace-svg" viewBox={`0 0 ${w} 120`} preserveAspectRatio="none" aria-hidden="true">
      <path d={all} fill="none" stroke="var(--line)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
      {litPath && <path d={litPath} fill="none" stroke="var(--signal)" strokeWidth="6" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />}
    </svg>
  );
}

function minutesWord(n: number, lang: "he" | "en"): string {
  if (lang === "en") return `${n} minutes`;
  const words: Record<number, string> = { 1: "דקה אחת", 2: "שתי דקות", 3: "שלוש דקות", 4: "ארבע דקות", 5: "חמש דקות", 10: "עשר דקות", 15: "רבע שעה", 20: "עשרים דקות", 30: "חצי שעה", 45: "שלושת רבעי שעה" };
  return words[n] ?? `${n} דקות`;
}
