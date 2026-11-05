"use client";

import { useCallback, useEffect, useId, useRef, useState, type RefObject } from "react";
import { ArrowLeft, ArrowRight, CheckCheck, ListChecks, Shuffle, X } from "lucide-react";
import { quickAnswerMarkdown, quickQuestions, quickTopics, type QuickTopic } from "../lib/fundamentals";
import { QUICK_QUIZ_SIZE, readQuickQuizRun, selectQuickQuiz, type QuickQuizRun } from "../lib/quick-quiz";
import { lockBodyScroll } from "../lib/body-scroll-lock";
import { BidiText } from "./bidi-text";
import { StudyText } from "./question-materials";
import { QuestionActions } from "./question-actions";
import { QuickDiagramView } from "./quick-diagram";
import styles from "./quick-quiz.module.css";

const HISTORY_KEY = "jobrunQuickQuiz";

/** A quiz is a real browser history step while the existing workspace route stays intact. */
export function useQuickQuiz(userId: string) {
  const [run, setRun] = useState<QuickQuizRun | null>(null);
  useEffect(() => {
    const sync = () => setRun(readQuickQuizRun(window.history.state?.[HISTORY_KEY], userId));
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, [userId]);
  const start = useCallback((next: QuickQuizRun) => {
    const current = readQuickQuizRun(window.history.state?.[HISTORY_KEY], userId);
    const state = { ...window.history.state, [HISTORY_KEY]: { owner: userId, run: next } };
    window.history[current ? "replaceState" : "pushState"](state, "", window.location.href);
    setRun(next);
  }, [userId]);
  const exit = useCallback(() => {
    if (readQuickQuizRun(window.history.state?.[HISTORY_KEY], userId)) window.history.back();
    else setRun(null);
  }, [userId]);
  return { run, start, exit };
}

export function QuickQuizDialog({ open, lang, initialTopics, onClose, onStart, returnFocus }: {
  open: boolean; lang: "he" | "en"; initialTopics?: QuickTopic[];
  onClose: () => void; onStart: (run: QuickQuizRun) => void; returnFocus?: RefObject<HTMLButtonElement | null>;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [selected, setSelected] = useState<QuickTopic[]>(quickTopics.map(topic => topic.id));
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const selectAll = useRef<HTMLInputElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const wasOpen = useRef(false);
  const id = useId();
  const initialKey = initialTopics?.join(",") ?? quickTopics.map(topic => topic.id).join(",");
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open) {
      wasOpen.current = true;
      setSelected(initialKey.split(",").filter(topic => quickTopics.some(item => item.id === topic)) as QuickTopic[]);
      opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      element.showModal();
      heading.current?.focus();
      const release = lockBodyScroll();
      return () => { element.close(); release(); };
    }
    if (element.open) element.close();
    if (!wasOpen.current) return;
    wasOpen.current = false;
    const target = returnFocus?.current ?? opener.current;
    if (target?.isConnected && target.getClientRects().length) target.focus({ preventScroll: true });
  }, [open, initialKey, returnFocus]);
  useEffect(() => {
    if (selectAll.current) selectAll.current.indeterminate = selected.length > 0 && selected.length < quickTopics.length;
  }, [selected]);
  const count = quickQuestions.filter(question => selected.includes(question.topic)).length;
  return <dialog ref={dialog} className={styles.dialog} dir={lang === "he" ? "rtl" : "ltr"} lang={lang}
    aria-labelledby={`${id}-title`} aria-describedby={`${id}-intro`} onCancel={event => { event.preventDefault(); onClose(); }}>
    <div className={styles.dialogHeader}>
      <div><h2 ref={heading} tabIndex={-1} id={`${id}-title`}>{t("מה יהיה בבוחן שלכם?", "What goes into your quiz?")}</h2>
        <p id={`${id}-intro`}>{t("בחרו נושאים. נגריל מהם 10 שאלות קצרות שונות, ונציג את כולן באותו עמוד.", "Choose topics. We’ll pick 10 different short questions and show them together on one page.")}</p></div>
      <button type="button" className={styles.close} aria-label={t("סגירת בחירת הנושאים", "Close topic selection")} onClick={onClose}><X size={21} aria-hidden="true" /></button>
    </div>
    <form onSubmit={event => {
      event.preventDefault();
      if (count < QUICK_QUIZ_SIZE) return;
      const words = window.crypto.getRandomValues(new Uint32Array(2));
      const selection = selectQuickQuiz(selected, words[0]);
      if (selection) onStart({ ...selection, id: `${words[0].toString(16)}-${words[1].toString(16)}` });
    }}>
      <fieldset className={styles.topics}>
        <legend>{t("נושאי הבוחן", "Quiz topics")}</legend>
        <label className={styles.selectAll}><input ref={selectAll} type="checkbox" checked={selected.length === quickTopics.length}
          onChange={event => setSelected(event.target.checked ? quickTopics.map(topic => topic.id) : [])} />
          <CheckCheck size={18} aria-hidden="true" /><span>{t("בחר הכול", "Select all")}</span></label>
        <div className={styles.topicGrid}>{quickTopics.map(topic => <label key={topic.id} className={styles.topic}>
          <input type="checkbox" checked={selected.includes(topic.id)} onChange={event => setSelected(current => event.target.checked ? [...current, topic.id] : current.filter(value => value !== topic.id))} />
          <span>{topic.label[lang]}</span>
        </label>)}</div>
      </fieldset>
      <p className={styles.pool} role="status">{count >= QUICK_QUIZ_SIZE
        ? t(`10 שאלות יוגרלו מתוך ${count} שאלות בנושאים שבחרתם.`, `10 questions will be drawn from ${count} questions in your selected topics.`)
        : selected.length ? t("בחרו נושאים עם לפחות 10 שאלות.", "Choose topics containing at least 10 questions.") : t("סמנו לפחות נושא אחד כדי להתחיל.", "Select at least one topic to begin.")}</p>
      <div className={styles.dialogActions}><button className="primary" type="submit" disabled={count < QUICK_QUIZ_SIZE}><ListChecks size={18} aria-hidden="true" />{t("ליצור בוחן של 10 שאלות", "Create a 10-question quiz")}</button>
        <button type="button" onClick={onClose}>{t("ביטול", "Cancel")}</button></div>
    </form>
  </dialog>;
}

export function QuickQuiz({ run, lang, onBack, onNew }: { run: QuickQuizRun; lang: "he" | "en"; onBack: () => void; onNew: () => void }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [revealed, setRevealed] = useState<Set<string>>(() => new Set());
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    heading.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, [run.id]);
  const byId = new Map(quickQuestions.map(question => [question.id, question]));
  const BackArrow = lang === "he" ? ArrowRight : ArrowLeft;
  return <section className={`quick-practice ${styles.quiz}`} lang={lang} dir={lang === "he" ? "rtl" : "ltr"} aria-label={t("בוחן שאלות קצרות", "Short-question quiz")}>
    <div className={styles.navigation}><button type="button" onClick={onBack}><BackArrow size={18} aria-hidden="true" />{t("חזרה לשאלות הקצרות", "Back to short questions")}</button>
      <button type="button" onClick={onNew} aria-haspopup="dialog"><Shuffle size={18} aria-hidden="true" />{t("בוחן חדש", "New quiz")}</button></div>
    <header className={styles.quizHeader}><h1 ref={heading} tabIndex={-1}>{t("הבוחן שלכם", "Your quiz")}</h1>
      <p>{t("10 שאלות קצרות. ענו בקצב שלכם ופתחו כל פתרון כשאתם מוכנים לבדוק את עצמכם.", "10 short questions. Work at your own pace and open each solution when you’re ready to check your thinking.")}</p>
      <p className={styles.selectedTopics}><strong>{t("הנושאים שבחרתם: ", "Your topics: ")}</strong>{quickTopics.filter(topic => run.topics.includes(topic.id)).map(topic => topic.label[lang]).join(" · ")}</p>
    </header>
    <div className={styles.questions}>{run.questionIds.map((questionId, index) => {
      const question = byId.get(questionId)!;
      const open = revealed.has(questionId);
      const answerId = `quiz-${run.id}-${questionId}-answer`;
      return <article className="quick-sheet" key={questionId} data-quiz-question={questionId}>
        <h2><span className={styles.number}>{index + 1}.</span> <BidiText>{question.title[lang]}</BidiText></h2>
        <StudyText text={question.prompt[lang]} lang={lang} />
        <QuestionActions lang={lang} questionKey={question.id} questionTitle={question.title[lang]} context="quick" />
        <button className={open ? "text-button quick-reveal" : "primary quick-reveal"} type="button" aria-expanded={open} aria-controls={answerId}
          onClick={() => setRevealed(previous => { const next = new Set(previous); if (next.has(questionId)) next.delete(questionId); else next.add(questionId); return next; })}>
          {open ? t("הסתרת הפתרון", "Hide solution") : t("הצגת פתרון קצר", "Show short solution")}</button>
        {open && <section id={answerId} className="quick-answer" aria-label={t(`פתרון לשאלה ${index + 1}`, `Solution to question ${index + 1}`)}>
          <h3>{t("הפתרון בקצרה", "The short solution")}</h3>
          <StudyText text={quickAnswerMarkdown(question.answer[lang])} lang={lang} />
          {question.code && <pre className="code-block" dir="ltr" aria-label={`${question.code.language} ${t("קוד הפתרון", "solution code")}`}><code>{question.code.text}</code></pre>}
          {question.diagram && <QuickDiagramView diagram={question.diagram} lang={lang} />}
          <p className="quick-takeaway"><strong>{t("מה לוקחים הלאה?", "What carries over?")}</strong> <BidiText>{question.takeaway[lang]}</BidiText></p>
        </section>}
      </article>;
    })}</div>
    <footer className={styles.footer}><p>{t("הבוחן הוא לתרגול עצמי ללא ציון. פתיחת פתרונות אינה משנה את סימוני ההשלמה בחשבון.", "This is an ungraded self-study quiz. Opening solutions does not change your account’s completion markers.")}</p>
      <button type="button" className="primary" onClick={onBack}>{t("סיימתי, חזרה לשאלות הקצרות", "Finished, back to short questions")}</button></footer>
  </section>;
}
