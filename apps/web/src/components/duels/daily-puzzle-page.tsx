"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, CalendarDays, Check, Target } from "lucide-react";
import { Auth } from "../auth";
import { AnswerEditor } from "../answer-editor";
import { VisualAnswer } from "../visual-answer";
import { EvaluationPanel } from "../evaluation-panel";
import { SubmittedAnswerContent } from "../submitted-answer-content";
import { BidiText } from "../bidi-text";
import { QuestionActions } from "../question-actions";
import { StudyText } from "../question-materials";
import { QuestionPrompt } from "../question-prompt";
import { learnerCopy } from "../../lib/learner-copy";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { lockBodyScroll } from "../../lib/body-scroll-lock";
import { hasVisual } from "../../lib/circuit";
import { duelApi, DuelApiError } from "../../lib/duel-api";
import type { DuelLanguage } from "../../lib/duel-types";
import { readDailyDraft, writeDailyDraft, type DailyPuzzle, type DailyPuzzleClient } from "../../lib/daily-puzzle";
import { subjectLabel } from "../../lib/practice-ui";
import { GamesNavigation, useDuelLanguage } from "./games-navigation";
import styles from "./daily-puzzle.module.css";

type Player = { userId: string; lang: DuelLanguage };

function showPuzzleDayInUrl(day?: string) {
  const url = new URL(window.location.href);
  if (day) url.searchParams.set("day", day);
  else url.searchParams.delete("day");
  if (url.href !== window.location.href) window.history.replaceState(window.history.state, "", url);
}

function MonthlyBalance({ puzzle, lang }: { puzzle: DailyPuzzle; lang: DuelLanguage }) {
  return <p className={styles.balance}>{lang === "he" ? "משובים שנותרו החודש" : "Monthly feedback credits left"}
    {" "}<strong><bdi dir="ltr">{puzzle.feedback_remaining} / {puzzle.feedback_limit}</bdi></strong></p>;
}

function PuzzleIntro({ lang, puzzle, onEnter }: {
  lang: DuelLanguage; puzzle: DailyPuzzle; onEnter: () => void;
}) {
  const he = lang === "he";
  const { status } = puzzle;
  const dialog = useRef<HTMLDialogElement>(null);
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    element.showModal();
    title.current?.focus();
    const unlock = lockBodyScroll();
    return () => { element.close(); unlock(); };
  }, []);
  return <dialog ref={dialog} className={styles.intro} aria-labelledby="daily-intro-title"
    aria-describedby="daily-rules" onCancel={event => { event.preventDefault(); window.location.assign("/games"); }}>
    <h2 id="daily-intro-title" ref={title} tabIndex={-1}>{status === "open"
      ? he ? "איך משחקים בחידה היומית?" : "How to play the daily puzzle"
      : he ? "התשובה שלכם לחידה היומית" : "Your daily puzzle submission"}</h2>
    <ul id="daily-rules">
      <li>{he ? "יש לכם ניסיון אחד להגיש פתרון לחידה של היום." : "You can submit one solution to today’s puzzle."}</li>
      <li>{he ? <>כדי להצליח צריך לקבל במשוב ציון <strong>90 ומעלה</strong> מתוך 100.</> : <>To solve the puzzle, your feedback score must be <strong>90 or higher</strong> out of 100.</>}</li>
      <li>{he ? <>שליחת הפתרון לבדיקה משתמשת <strong>במשוב AI אחד מהמכסה החודשית</strong>. פתיחת החידה וכתיבת טיוטה הן בחינם.</>
        : <>Submitting uses <strong>one AI feedback credit from your monthly allowance</strong>. Opening the puzzle and drafting your answer are free.</>}</li>
    </ul>
    <MonthlyBalance puzzle={puzzle} lang={lang} />
    {status !== "open" && <p>{he ? "התשובה שלכם כבר הוגשה. אפשר לחזור אליה בלי לנצל משוב נוסף." : "Your answer has already been submitted. Revisiting it uses no additional credit."}</p>}
    <div className={styles.introActions}><button className="primary" onClick={onEnter}>{status === "open"
      ? he ? "לפתיחת החידה" : "Open the puzzle"
      : he ? "לצפייה בתשובה שלי" : "View my submission"}</button>
      <a href="/games">{he ? "חזרה למשחקים" : "Back to games"}</a></div>
  </dialog>;
}

function PuzzleSession({ userId, lang, initial, client, onExpired }: Player & {
  initial: DailyPuzzle; client: DailyPuzzleClient; onExpired: () => void;
}) {
  const he = lang === "he";
  const [puzzle, setPuzzle] = useState(initial);
  const [draft, setDraft] = useState(() => readDailyDraft(userId, initial));
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [checkNeeded, setCheckNeeded] = useState(false);
  const [error, setError] = useState("");
  const [solution, setSolution] = useState("");
  const [expired, setExpired] = useState(() => Date.now() >= Date.parse(initial.expires_at));
  const guard = useRef(false);
  const mounted = useRef(false);
  const feedback = useRef<HTMLHeadingElement>(null);
  const questionHeading = useRef<HTMLHeadingElement>(null);
  const shouldFocusFeedback = useRef(initial.status === "evaluating");
  const question = { title: puzzle.title, content: <QuestionPrompt text={puzzle.prompt} questionKey={puzzle.id} lang={lang} /> };
  const { id, day, status, submission } = puzzle;

  useEffect(() => {
    mounted.current = true;
    questionHeading.current?.focus({ preventScroll: true });
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    if (status === "open") writeDailyDraft(userId, { day, id }, draft);
  }, [userId, day, id, draft, status]);

  useEffect(() => {
    const expires = Date.parse(initial.expires_at);
    const check = () => { if (Date.now() >= expires) setExpired(true); };
    const timer = window.setTimeout(check, Math.max(0, expires - Date.now()));
    document.addEventListener("visibilitychange", check);
    return () => { window.clearTimeout(timer); document.removeEventListener("visibilitychange", check); };
  }, [initial.expires_at]);
  useEffect(() => {
    if (expired && status === "open" && !busy && !checkNeeded) onExpired();
    if (status !== "open") showPuzzleDayInUrl(day);
  }, [expired, status, busy, checkNeeded, day, onExpired]);

  const accept = useCallback((next: DailyPuzzle) => {
    if (!mounted.current) return;
    if (next.id !== id || next.day !== day) { onExpired(); return; }
    setPuzzle(next);
    setCheckNeeded(false);
  }, [id, day, onExpired]);

  const waiting = status === "evaluating" || !!submission?.feedback_pending;
  useEffect(() => {
    if (!waiting || checkNeeded) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await client.get(lang, day);
        if (cancelled) return;
        accept(next);
        if (next.id === id && next.day === day && (next.status === "evaluating" || next.submission?.feedback_pending)) {
          timer = setTimeout(poll, 2500);
        }
      } catch {
        if (!cancelled) setCheckNeeded(true);
      }
    };
    timer = setTimeout(poll, 2000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [waiting, checkNeeded, client, lang, id, day, accept]);
  useEffect(() => {
    if (status !== "done" || submission?.feedback_pending || !shouldFocusFeedback.current) return;
    shouldFocusFeedback.current = false;
    feedback.current?.focus({ preventScroll: true });
    feedback.current?.scrollIntoView({ block: "start" });
  }, [status, submission?.feedback_pending]);

  async function submit(retry = false) {
    if (guard.current || uploading || checkNeeded) return;
    guard.current = true;
    setBusy(true); setError("");
    shouldFocusFeedback.current = true;
    try {
      const next = retry ? await client.retry(lang, day, id) : await client.submit(lang, day, id, {
        text: draft.answer, ...(hasVisual(draft.visual) ? { visual: draft.visual } : {}),
      });
      accept(next);
    } catch (cause) {
      if (!mounted.current) return;
      const apiError = cause instanceof DuelApiError ? cause : null;
      if (apiError?.code === "monthly_feedback_limit") {
        setPuzzle(previous => ({ ...previous, feedback_remaining: 0 }));
        setError(he ? "ניצלתם את מכסת המשובים החודשית. הבקשה לבדיקה לא נשלחה." : "Your monthly feedback allowance is used up. This assessment request was not accepted.");
        try {
          const next = await client.get(lang, day);
          accept(next);
          if (mounted.current && next.status === "done") setError("");
        } catch { /* The draft and last known balance stay on screen. */ }
      } else if (apiError?.code === "usage_limit") {
        setError(he ? "הגעתם למגבלת השימוש במשובי AI. הפתרון שמור, ותוכלו לנסות שוב כשהשירות יהיה זמין." : "The AI feedback usage limit has been reached. Your solution is saved and you can try again when access is available.");
      } else if (apiError?.status === 402) {
        setError(he ? "כדי להגיש פתרון דרושה גישה פעילה למשובי AI בחשבון." : "Your account needs access to AI feedback to submit a solution.");
      } else if (apiError?.status === 422) {
        setError(he ? "לא הצלחנו לקבל את התשובה. בדקו את התוכן והקבצים המצורפים ונסו שוב." : "Your answer could not be accepted. Check its content and attachments, then try again.");
      } else {
        // A lost response or another tab's submit must recover the server's attempt first.
        setCheckNeeded(true);
        try {
          const next = await client.get(lang, day);
          if (!mounted.current) return;
          accept(next);
          if (next.status === "open") setError(he ? "הפתרון עדיין לא הוגש. הטיוטה שמורה ואפשר לשלוח שוב." : "Your solution has not been submitted. Your draft is saved and you can submit again.");
        } catch (readError) {
          if (mounted.current && readError instanceof DuelApiError && [404, 409].includes(readError.status)) onExpired();
        }
      }
    } finally {
      guard.current = false;
      if (mounted.current) setBusy(false);
    }
  }

  async function checkStatus() {
    if (guard.current) return;
    guard.current = true; setBusy(true); setError("");
    try { accept(await client.get(lang, day)); }
    catch (cause) {
      if (mounted.current && cause instanceof DuelApiError && [404, 409].includes(cause.status)) onExpired();
      else if (mounted.current) setError(he ? "לא הצלחנו להתחבר. אפשר לנסות שוב." : "Couldn’t connect. Please try again.");
    }
    finally { guard.current = false; if (mounted.current) setBusy(false); }
  }

  async function revealSolution() {
    if (guard.current) return;
    guard.current = true; setBusy(true); setError("");
    try {
      const result = await client.reveal(lang, day, id);
      if (mounted.current && result.day === day && result.id === id) setSolution(result.solution);
    } catch (cause) {
      if (!mounted.current) return;
      if (cause instanceof DuelApiError && cause.status === 409) onExpired();
      else setError(he ? "טעינת הפתרון נכשלה. אפשר לנסות שוב." : "The solution didn’t load. Please try again.");
    } finally { guard.current = false; if (mounted.current) setBusy(false); }
  }
  return <>
    <article className={styles.sheet} aria-labelledby="daily-question-title">
      <p className={styles.subject}><BidiText>{subjectLabel(puzzle.subject === "relevant_programming" ? "programming" : puzzle.subject, lang)}</BidiText></p>
      <h2 id="daily-question-title" tabIndex={-1} ref={questionHeading}><BidiText>{puzzle.title}</BidiText></h2>
      {question.content}
      {status === "open" ? <section className={styles.answer}>
        <h3>{he ? "הפתרון שלכם" : "Your solution"}</h3>
        <AnswerEditor value={draft.answer} onChange={answer => setDraft(previous => ({ ...previous, answer }))} lang={lang}
          disabled={busy || checkNeeded} codeLanguage={null} starterCode={null} question={question} />
        <VisualAnswer value={draft.visual} onChange={visual => setDraft(previous => ({ ...previous, visual }))} lang={lang}
          disabled={busy || checkNeeded} attemptId={puzzle.attempt_id} userId={userId} question={question} onUploading={setUploading} />
        <p className={styles.allowance} id="daily-submit-rules">{he ? "השליחה מנצלת את הניסיון היומי ומשוב AI אחד מהמכסה החודשית. ציון 90 ומעלה מתוך 100 נחשב להצלחה."
          : "Submitting uses your daily attempt and one monthly AI feedback credit. A score of 90 or higher out of 100 solves the puzzle."}</p>
        <button type="button" className="primary" onClick={() => void submit()} aria-describedby="daily-submit-rules"
          disabled={busy || uploading || checkNeeded || puzzle.feedback_remaining <= 0 || draft.answer.length > 20000 || (!draft.answer.trim() && !hasVisual(draft.visual))}>
          {busy ? he ? "שולחים את הפתרון…" : "Submitting…" : he ? "הגשת פתרון וקבלת משוב AI" : "Submit solution for AI feedback"}</button>
        <MonthlyBalance puzzle={puzzle} lang={lang} />
      </section> : submission && <details className={styles.saved}>
        <summary>{he ? "התשובה ששלחתם" : "Your submitted answer"}</summary>
        <SubmittedAnswerContent answer={submission.answer} lang={lang} />
        {hasVisual(submission.visual) && <VisualAnswer value={submission.visual!} lang={lang} question={question} />}
      </details>}
    </article>

    {status === "evaluating" && <p className="notice" role="status">{he ? "הפתרון שלכם נשמר ונשלח לבדיקה. המשוב יופיע כאן כשהוא יהיה מוכן." : "Your solution is saved and is being assessed. Your feedback will appear here."}</p>}
    {status === "failed" && <section className="notice"><p role="status">{he ? "המשוב לא הושלם. אפשר לבדוק שוב את הפתרון שכבר שלחתם, בלי לנצל משוב נוסף."
      : "Feedback could not be completed. You can retry the assessment of your saved solution without using another credit."}</p>
      <button type="button" disabled={busy || checkNeeded || puzzle.feedback_remaining <= 0} onClick={() => void submit(true)}>{he ? "בדיקה חוזרת של הפתרון שנשלח" : "Retry assessment of my submitted solution"}</button>
      <MonthlyBalance puzzle={puzzle} lang={lang} /></section>}
    {status === "done" && submission && <section className={styles.result} aria-labelledby="daily-result-title">
      <header className={styles.resultHeader}>
        {puzzle.passed ? <Check aria-hidden="true" /> : <Target aria-hidden="true" />}
        <div><h2 id="daily-result-title" ref={feedback} tabIndex={-1}>{puzzle.passed
          ? he ? "פתרתם את החידה היומית!" : "You solved the daily puzzle!"
          : he ? "המשוב על הפתרון שלכם" : "Feedback on your solution"}</h2>
          <p>{he ? "הציון שלכם" : "Your score"} <strong><bdi dir="ltr">{puzzle.score}/100</bdi></strong>
            {!puzzle.passed && (he ? " · הפעם החידה לא נפתרה. כדי להצליח צריך ציון 90 ומעלה." : " · This attempt didn’t solve the puzzle. A score of 90 or higher is required.")}</p></div>
      </header>
      <EvaluationPanel submission={submission} lang={lang} />
      <MonthlyBalance puzzle={puzzle} lang={lang} />
      {solution ? <section className={styles.solution}><h3>{he ? "הפתרון המוצע" : "Suggested solution"}</h3>
        <StudyText text={learnerCopy(solution)} solution lang={lang} /></section>
        : <button type="button" disabled={busy} className={styles.reveal} onClick={() => void revealSolution()}>
          {he ? "השוואה לפתרון המוצע" : "Compare with the suggested solution"}</button>}
    </section>}
    {checkNeeded && <div className="notice"><p>{he ? "החיבור נקטע. אפשר לבדוק אם התשובה התקבלה ולחזור למשוב." : "The connection was interrupted. Check the saved submission status to continue."}</p>
      <button disabled={busy} onClick={() => void checkStatus()}>{he ? "בדיקת מצב התשובה" : "Check submission status"}</button></div>}
    {error && <p role="alert" className="notice">{error}</p>}
    {expired && status !== "open" ? <p className={styles.next}><button type="button" onClick={onExpired}>{he ? "לחידה החדשה של היום" : "Open today’s new puzzle"}</button></p>
      : <p className={styles.next}>{he ? "חידה חדשה נפתחת בחצות לפי שעון ישראל." : "A new puzzle opens at midnight, Israel time."}</p>}
    <div className={styles.actions}><QuestionActions context="daily" questionKey={id} questionTitle={puzzle.title} lang={lang} /></div>
  </>;
}

function PuzzleForToday({ userId, lang }: Player) {
  const he = lang === "he";
  const client = useMemo(() => duelApi(userId).daily, [userId]);
  const [puzzle, setPuzzle] = useState<DailyPuzzle | null>(null);
  const [activatedDay, setActivatedDay] = useState("");
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision(n => n + 1), []);
  const openToday = useCallback(() => { showPuzzleDayInUrl(); refresh(); }, [refresh]);

  useEffect(() => {
    let current = true;
    setError(false); setPuzzle(null);
    const day = new URLSearchParams(window.location.search).get("day");
    const savedDay = day && /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : undefined;
    client.get(lang, savedDay).then(value => { if (current) setPuzzle(value); })
      .catch(cause => {
        if (!current) return;
        if (savedDay && cause instanceof DuelApiError && [404, 409, 422].includes(cause.status)) openToday();
        else setError(true);
      });
    return () => { current = false; };
  }, [client, lang, revision, openToday]);

  useEffect(() => {
    if (!puzzle || activatedDay === puzzle.day || puzzle.status !== "open") return;
    const expires = Date.parse(puzzle.expires_at);
    const timer = window.setTimeout(openToday, Math.max(1000, expires - Date.now()));
    const checkDay = () => { if (document.visibilityState === "visible" && Date.now() >= expires) openToday(); };
    document.addEventListener("visibilitychange", checkDay);
    return () => { window.clearTimeout(timer); document.removeEventListener("visibilitychange", checkDay); };
  }, [puzzle, activatedDay, openToday]);

  return <>
    <header className={styles.masthead}>
      <h1>{he ? "החידה היומית" : "Daily puzzle"}</h1>
      {puzzle && <p className={styles.date}><CalendarDays size={18} aria-hidden="true" /><time dateTime={puzzle.day}>
        {new Intl.DateTimeFormat(he ? "he-IL" : "en-GB", { dateStyle: "full", timeZone: "UTC" }).format(new Date(puzzle.day + "T12:00:00Z"))}
      </time></p>}
    </header>
    {puzzle ? activatedDay !== puzzle.day ? <PuzzleIntro lang={lang} puzzle={puzzle} onEnter={() => setActivatedDay(puzzle.day)} />
      : <PuzzleSession key={puzzle.day + puzzle.id + lang} userId={userId} lang={lang} initial={puzzle} client={client} onExpired={openToday} />
      : error ? <div><p role="alert">{he ? "לא הצלחנו לטעון את החידה היומית." : "Today’s puzzle didn’t load."}</p>
        <button type="button" onClick={refresh}>{he ? "ניסיון נוסף" : "Try again"}</button></div>
      : <p role="status">{he ? "טוענים את החידה של היום…" : "Loading today’s puzzle…"}</p>}
  </>;
}

export function DailyPuzzlePage() {
  const [lang, setLang] = useDuelLanguage();
  const controls = <><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>;
  const Back = lang === "he" ? ArrowRight : ArrowLeft;
  return <Auth kind="practice" lang={lang} controls={controls}>{user =>
    <div dir={lang === "he" ? "rtl" : "ltr"} lang={lang}>
      <GamesNavigation lang={lang} controls={controls} />
      <main className={styles.main}>
        <a href="/games" className={styles.back}><Back size={17} aria-hidden="true" />{lang === "he" ? "לכל המשחקים" : "All games"}</a>
        <PuzzleForToday key={user.id} userId={user.id} lang={lang} />
      </main>
    </div>}
  </Auth>;
}
