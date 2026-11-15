"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, BookOpen, CalendarDays } from "lucide-react";
import { Auth } from "../auth";
import { BidiText } from "../bidi-text";
import { QuestionActions } from "../question-actions";
import { StudyText } from "../question-materials";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { duelApi } from "../../lib/duel-api";
import type { DuelLanguage } from "../../lib/duel-types";
import { readDailyDraft, writeDailyDraft, type DailyPuzzle, type DailyPuzzleClient } from "../../lib/daily-puzzle";
import { subjectLabel } from "../../lib/practice-ui";
import { GamesNavigation, useDuelLanguage } from "./games-navigation";
import game from "./duels.module.css";
import styles from "./daily-puzzle.module.css";

type PuzzleProps = { userId: string; lang: DuelLanguage };

function PuzzleSheet({ userId, lang, puzzle, client, onExpired }: PuzzleProps & {
  puzzle: DailyPuzzle; client: DailyPuzzleClient; onExpired: () => void;
}) {
  const he = lang === "he";
  const [draft, setDraft] = useState(() => readDailyDraft(userId, puzzle));
  const [requested, setRequested] = useState(draft.revealed);
  const [solution, setSolution] = useState("");
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const focusResult = useRef(false);
  const solutionHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => { writeDailyDraft(userId, puzzle, draft); }, [draft, puzzle, userId]);
  useEffect(() => {
    if (!requested) return;
    let current = true;
    setFailed(false);
    client.reveal(lang, puzzle.day, puzzle.id).then(result => {
      if (!current) return;
      if (result.day !== puzzle.day || result.id !== puzzle.id) { onExpired(); return; }
      setSolution(result.solution);
      setDraft(previous => previous.revealed ? previous : { ...previous, revealed: true });
    }).catch((err: { status?: number }) => {
      if (!current) return;
      if (err?.status === 409) onExpired();
      else setFailed(true);
    });
    return () => { current = false; };
  }, [client, lang, puzzle, requested, retry, onExpired]);
  useEffect(() => { if (solution && focusResult.current) solutionHeading.current?.focus(); }, [solution]);

  return <>
    <article className={styles.sheet} aria-labelledby="daily-question-title">
      <p className={styles.subject}><BidiText>{subjectLabel(puzzle.subject === "relevant_programming" ? "programming" : puzzle.subject, lang)}</BidiText></p>
      <h2 id="daily-question-title"><BidiText>{puzzle.title}</BidiText></h2>
      <StudyText text={puzzle.prompt} lang={lang} />
      <div className={styles.answer}>
        <label htmlFor="daily-answer">{he ? "הפתרון שלכם" : "Your solution"}</label>
        <textarea id="daily-answer" dir="auto" value={draft.answer} maxLength={20000}
          placeholder={he ? "אפשר לכתוב כאן את דרך הפתרון או לנסות לפתור בראש." : "Write out your reasoning here, or solve it in your head."}
          onChange={event => setDraft({ ...draft, answer: event.target.value })} />
        {!solution && <button type="button" className={`${game.primary} ${styles.reveal}`}
          disabled={requested && !failed} onClick={() => { focusResult.current = true; if (failed) setRetry(n => n + 1); else setRequested(true); }}>
          <BookOpen size={17} aria-hidden="true" />{requested && !failed ? he ? "טוענים את הפתרון…" : "Loading solution…" : he ? "הצגת הפתרון" : "Show solution"}
        </button>}
      </div>
      {failed && <p role="alert" className={styles.error}>{he ? "טעינת הפתרון נכשלה. לחצו שוב כדי לנסות." : "The solution didn’t load. Try opening it again."}</p>}
      {solution && <section className={styles.solution} aria-labelledby="daily-solution-title">
        <h3 id="daily-solution-title" tabIndex={-1} ref={solutionHeading}>{he ? "הפתרון המוצע" : "Suggested solution"}</h3>
        <StudyText text={solution} solution lang={lang} />
      </section>}
    </article>
    <p className={styles.next}>{he ? "חידה חדשה נפתחת בחצות לפי שעון ישראל." : "A new puzzle opens at midnight, Israel time."}</p>
    <div className={styles.actions}><QuestionActions context="daily" questionKey={puzzle.id} questionTitle={puzzle.title} lang={lang} /></div>
  </>;
}

function PuzzleForToday({ userId, lang }: PuzzleProps) {
  const he = lang === "he";
  const client = useMemo(() => duelApi(userId).daily, [userId]);
  const [puzzle, setPuzzle] = useState<DailyPuzzle | null>(null);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision(n => n + 1), []);

  useEffect(() => {
    let current = true;
    setError(false); setPuzzle(null);
    client.get(lang).then(value => { if (current) setPuzzle(value); })
      .catch(() => { if (current) setError(true); });
    return () => { current = false; };
  }, [client, lang, revision]);

  useEffect(() => {
    if (!puzzle) return;
    const expires = Date.parse(puzzle.expires_at);
    const timer = window.setTimeout(refresh, Math.max(1000, expires - Date.now()));
    const checkDay = () => { if (document.visibilityState === "visible" && Date.now() >= expires) refresh(); };
    document.addEventListener("visibilitychange", checkDay);
    return () => { window.clearTimeout(timer); document.removeEventListener("visibilitychange", checkDay); };
  }, [puzzle, refresh]);

  return <>
    <header className={styles.masthead}>
      <h1>{he ? "החידה היומית" : "Daily puzzle"}</h1>
      {puzzle && <p className={styles.date}><CalendarDays size={18} aria-hidden="true" /><time dateTime={puzzle.day}>
        {new Intl.DateTimeFormat(he ? "he-IL" : "en-GB", { dateStyle: "full", timeZone: "UTC" }).format(new Date(puzzle.day + "T12:00:00Z"))}
      </time></p>}
    </header>
    {puzzle ? <PuzzleSheet key={puzzle.day + puzzle.id} userId={userId} lang={lang} puzzle={puzzle} client={client} onExpired={refresh} />
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
    <div className={game.shell} dir={lang === "he" ? "rtl" : "ltr"} lang={lang}>
      <GamesNavigation lang={lang} controls={controls} />
      <main className={styles.main}>
        <a href="/games" className={styles.back}><Back size={17} aria-hidden="true" />{lang === "he" ? "לכל המשחקים" : "All games"}</a>
        <PuzzleForToday key={user.id + ":" + lang} userId={user.id} lang={lang} />
      </main>
    </div>}
  </Auth>;
}
