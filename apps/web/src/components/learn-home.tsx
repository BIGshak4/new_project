"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Clock3, MessageSquareText, Play, RefreshCw, Target } from "lucide-react";
import type { Lang } from "./auth";
import { SkillStrength, StreakCard } from "./skill-strength";
import { SubjectSketch, sketchCaption } from "./sketches";
import type { Goal, PlanItem, PracticeApi, Program, Progress } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { dayLabel, modeLabel } from "../lib/timeline";
import { daysToGoLabel, eligibleAhead, pathNodes, todayProgress, type PathNode } from "../lib/path";
import { revealDelay, shouldScrollToNode } from "../lib/ui";
import { Breathe, Pop, motion, spring, useReducedMotion } from "./ui/motion";
import { BidiText } from "./bidi-text";

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
  const [loadError, setLoadError] = useState("");
  const loadVersion = useRef(0);
  const starting = useRef(false);
  const mounted = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const load = useCallback(() => {
    const version = ++loadVersion.current;
    setLoading(true);
    setLoadError("");
    api
      .program(lang)
      .then((p) => {
        if (mounted.current && loadVersion.current === version) setProgram(p);
      })
      .catch((e) => {
        if (mounted.current && loadVersion.current === version) setLoadError(apiMessage(e, lang));
      })
      .finally(() => {
        if (mounted.current && loadVersion.current === version) setLoading(false);
      });
    return () => {
      // Invalidate manual reloads as well as this effect's original request.
      ++loadVersion.current;
    };
  }, [api, lang]);
  useEffect(() => load(), [load, refreshKey]);

  // on open, bring the day's sheet into view once (only if it is not already visible)
  const reduced = useReducedMotion();
  const scrolled = useRef(false);
  useEffect(() => {
    if (scrolled.current || !program || goalSlot || !program.goal_complete || !progress.overview?.answered) return;
    const el = document.querySelector<HTMLElement>(".today-sheet");
    if (!el) return;
    scrolled.current = true;
    if (shouldScrollToNode(el.getBoundingClientRect(), window.innerHeight)) {
      el.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
    }
  }, [program, reduced, goalSlot, progress.overview?.answered]);

  async function start(node: PathNode | null) {
    const id = node?.item.id ?? undefined;
    if (!mounted.current || starting.current || loading || loadError) return;
    starting.current = true;
    setBusy(id ?? "next");
    setMessage("");
    const versionAtStart = loadVersion.current;
    const isCurrent = () => mounted.current && loadVersion.current === versionAtStart;
    try {
      const result = await api.startProgram(id, lang);
      if (!isCurrent()) return;
      if (result.kind === "attempt" && result.attempt) onStartAttempt(result.attempt.id);
      else if (result.kind === "interview") onStartInterview(result.interview_duration_min);
      else {
        setMessage(result.message ?? t("אין מה להתחיל כרגע.", "Nothing to start right now."));
        load();
      }
    } catch (e) {
      if (isCurrent()) setMessage(apiMessage(e, lang));
    } finally {
      starting.current = false;
      if (mounted.current) setBusy(null);
    }
  }

  const goalComplete = goal ? !!goal.complete : !!program?.goal_complete;
  const items = program?.plan.items ?? [];
  const nodes = pathNodes(items, program?.next?.id ?? null);
  const todayNodes = nodes.filter((n) => n.dayIndex === 0);
  const laterNodes = nodes.filter((n) => n.dayIndex > 0);
  const current = todayNodes.find((n) => n.state === "current") ?? null;
  const aheadItem = eligibleAhead(program);
  const ahead = aheadItem ? pathNodes([aheadItem], aheadItem.id)[0] ?? null : null;
  const today = todayProgress(program);
  const overview = progress.overview ?? null;
  const firstPractice = !overview || overview.answered === 0;
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
      ? t(`ראיון של ${current.item.minutes} דקות עם תשובות בכתב וכלים חזותיים. הציונים נחשפים בסוף, בדוח.`, `A ${current.item.minutes}-minute interview with written answers and visual tools. Grades are revealed at the end, in the report.`)
      : current?.item.mode === "quick"
        ? t("שאלה קצרה. משוב ושאלת המשך שנולדת מהתשובה שלכם. אין פה טריק, יש פה דיוק.", "A short question. Feedback and a follow-up born from your answer. No trick here, just precision.")
        : t("תרגול מעמיק: התשובה, שאלת המשך, ואז השאלה הבאה שנבחרת לפי מה שכתבתם.", "Deep practice: your answer, one follow-up, then the next question chosen by what you wrote.");

  const tomorrow = laterNodes.find((n) => n.state !== "done" && n.state !== "skipped") ?? null;

  return (
    <div className="learn">
      <div className="learn-main">
        <header className="learn-head">
          <div>
            <h1 dir="auto">
              {daysLabel && goalComplete ? `${daysLabel}. ` : ""}
              {title}
              {topic && current?.kind !== "interview" && <span className="mark"><bdi dir="auto"><BidiText>{topic}</BidiText></bdi>.</span>}
            </h1>
            <div className="learn-context" dir="auto">
              <BidiText>{[userName, goal?.job_type_label ?? t("סוג התפקיד לא נבחר עדיין", "No job type chosen yet"), interviewDate ? `${t("ראיון ב", "interview on")}${lang === "he" ? "־" : " "}${interviewDate}` : null]
                .filter(Boolean)
                .join(" · ")}</BidiText>
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

        {loading ? (
          <p className="loading loading-sheet" role="status">
            {t("טוענים את התוכנית…", "Loading your program…")}
          </p>
        ) : loadError ? (
          <section className="sheet path-empty"><p role="alert">{loadError}</p><button type="button" onClick={() => { load(); }}>{t("לטעון שוב את התוכנית", "Reload the program")}</button></section>
        ) : !goalComplete && !goalSlot ? (
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
        ) : !goalComplete ? null : nodes.length === 0 && !ahead ? (
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
                    <BidiText>{current.kind === "interview"
                      ? t(`ראיון מדומה, ${current.item.minutes} דקות, על ${currentSkills}.`, `A ${current.item.minutes}-minute mock interview on ${currentSkills}.`)
                      : `${modeLabel(current.item.mode, lang)} ${t("על", "on")} ${currentSkills}.`}</BidiText>
                  </h2>
                  <div className="sheet-row">
                    <span className="tag">
                      {t("עכשיו", "Now")} · {today.done + 1}/{today.total} · {current.item.minutes} {t("דק׳", "min")}
                    </span>
                    <span className="sheet-skill" dir="auto"><BidiText>{currentSkills}</BidiText></span>
                  </div>
                  <p className="sheet-why" dir="auto">
                    <BidiText>{current.item.reason}</BidiText>{" "}<BidiText>{modeLine}</BidiText>
                  </p>
                  <div className="sheet-actions">
                    <button type="button" className="primary" disabled={!!busy} onClick={() => void start(current)}>
                      {busy
                        ? t("פותחים…", "Opening…")
                        : current.kind === "interview"
                          ? t("לראיון", "To the interview")
                          : firstPractice
                            ? t("להתחיל את התרגול הראשון", "Start my first practice")
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
                    {ahead
                      ? t("אפשר לעצור כאן, או לבחור להתחיל את הפריט הבא מראש. היעד היומי שלכם לא משתנה.", "You can stop here, or choose to start the next item early. Your daily target stays the same.")
                      : today.total > 0
                      ? t("אין כרגע פריט נוסף זמין בתוכנית. אפשר לנוח או לבחור שאלה מהמאגר.", "There is no further item available in the program right now. Rest or choose a question from the library.")
                      : t("אפשר לבחור שאלה מהמאגר.", "Pick a question from the library.")}
                  </p>
                  <div className="sheet-actions">
                    <button type="button" onClick={onOpenLibrary}>
                      {t("למאגר השאלות", "To the library")}
                    </button>
                  </div>
                  {ahead && <WorkAheadCard item={ahead.item} lang={lang} busy={!!busy} starting={busy === ahead.item.id} onStart={() => void start(ahead)} />}
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
                              {node.kind === "interview" ? <MessageSquareText size={20} aria-hidden="true" /> : <Play size={20} aria-hidden="true" fill="currentColor" />}
                            </button>
                          ) : (
                            <span className="probe-dot" aria-hidden="true">
                              {node.state === "done" ? (
                                <Pop delay={revealDelay(i, !!reduced) + 0.12}>
                                  <Check size={20} strokeWidth={3} />
                                </Pop>
                              ) : node.kind === "interview" ? (
                                <MessageSquareText size={18} />
                              ) : (
                                i + 1
                              )}
                            </span>
                          )}
                        </Breathe>
                        <b dir="auto"><BidiText>{node.kind === "interview" ? t("ראיון מדומה", "Mock interview") : node.item.skills.map((s) => s.label).join(", ")}</BidiText></b>
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
                          <BidiText>{node.kind === "interview" ? t("ראיון מדומה", "Mock interview") : node.item.skills.map((s) => s.label).join(", ")}</BidiText>
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
                ? ahead
                  ? t("היעד להיום הושלם. אפשר להמשיך מראש, לבחירתכם.", "Today's target is complete. Working ahead is optional.")
                  : t("היעד להיום הושלם. אפשר לנוח או לבחור שאלה מהמאגר.", "Today's target is complete. Rest or choose a question from the library.")
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
            {dayLabel(tomorrow.item.date, tomorrow.dayIndex, lang)}{": "}
            <BidiText>{tomorrow.kind === "interview" ? t("ראיון מדומה", "a mock interview") : tomorrow.item.skills.map((s) => s.label).join(", ")}</BidiText>
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

/** Future work is offered separately, without adding it to today's minutes or completed count. */
export function WorkAheadCard({ item, lang, busy, starting, onStart }: {
  item: PlanItem;
  lang: Lang;
  busy: boolean;
  starting: boolean;
  onStart: () => void;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  const isInterview = item.mode === "simulation";
  return <section className="work-ahead" aria-labelledby="work-ahead-title">
    <div className="work-ahead-copy"><span className="tag">{dayLabel(item.date, item.day_index, lang)} · {item.minutes} {t("דק׳", "min")}</span><h3 id="work-ahead-title">{item.status === "started" ? t("להמשיך את התרגול שהתחלתם מראש", "Continue the item you opened early") : t("רוצים להתקדם מעבר להיום?", "Want to work ahead?")}</h3><p dir="auto"><BidiText>{item.skills.map((skill) => skill.label).join(", ")}</BidiText> · {modeLabel(item.mode, lang)}</p><p className="small muted">{t("הפריט יישאר משויך ליום המקורי שלו. אם תשלימו אותו כעת, הוא יופיע שם כהושלם.", "This item stays assigned to its original day. If you complete it now, it will be marked done there.")}</p></div>
    <button type="button" className="primary" disabled={busy} onClick={onStart}>{starting ? t("פותחים…", "Opening…") : isInterview ? t("לראיון המתוכנן הבא", "Open the next planned interview") : item.status === "started" ? t("להמשיך את הפריט הבא", "Continue the next item") : t("להתחיל את הפריט הבא מראש", "Start the next item early")}<Arrow size={16} aria-hidden="true" /></button>
  </section>;
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
