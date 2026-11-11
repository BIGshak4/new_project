"use client";

import { useEffect, useRef, useState } from "react";
import { Check, CircleHelp, Play, RotateCcw } from "lucide-react";
import { BidiText } from "../bidi-text";
import { QuestionActions } from "../question-actions";
import type { DuelLanguage, QuizPracticeClient, QuizPracticeRound, QuizPracticeResult } from "../../lib/duel-types";
import styles from "./duels.module.css";
import practiceStyles from "./duel-practice.module.css";

/** A real approved bank round, checked by the API without creating a duel or spending coins. */
export function DuelPractice({ client, lang }: { client: QuizPracticeClient; lang: DuelLanguage }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [round, setRound] = useState<QuizPracticeRound | null>(null);
  const [choice, setChoice] = useState<number | null>(null);
  const [result, setResult] = useState<QuizPracticeResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const mounted = useRef(false);
  const inFlight = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => { if (round) heading.current?.focus({ preventScroll: true }); }, [round]);
  useEffect(() => { if (result) resultHeading.current?.focus({ preventScroll: true }); }, [result]);

  async function run(action: "start" | "answer") {
    if (inFlight.current || (action === "answer" && (!round || choice === null))) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      if (action === "start") {
        const next = await client.start(lang);
        if (!mounted.current) return;
        setRound(next); setChoice(null); setResult(null); setExpired(false);
      } else {
        const next = await client.answer(round!.round_token, choice!);
        if (mounted.current) setResult(next);
      }
    } catch (cause) {
      if (!mounted.current) return;
      const code = (cause as { code?: string }).code;
      if (code === "practice_round_expired") {
        setExpired(true);
        setError(t("השאלה הייתה פתוחה זמן רב או התעדכנה. פתחו שאלה חדשה כדי להמשיך.", "This round expired or its question changed. Open a new question to continue."));
      } else if (code === "unauthenticated" || code === "forbidden") {
        setError(t("ההתחברות השתנתה. היכנסו שוב כדי להמשיך.", "Your sign-in changed. Sign in again to continue."));
      } else {
        setError(t("לא הצלחנו להתחבר למאגר המשחק. אפשר לנסות שוב.", "We could not reach the game bank. Please try again."));
      }
    } finally {
      inFlight.current = false;
      if (mounted.current) setBusy(false);
    }
  }

  return <section className={practiceStyles.practice} data-member-tour="game-practice" aria-busy={busy} aria-labelledby="game-practice-title">
    <h2 id="game-practice-title">{t("מתנסים בשאלה מהמשחק", "Try a question from the game")}</h2>
    <p>{t("שאלה אמריקאית אמיתית מהמאגר. בחרו תשובה וגלו את ההסבר, בלי להזמין חבר ובלי להשתמש במטבעות.", "A real multiple-choice question from the bank. Choose an answer and see the explanation, without inviting a friend or using coins.")}</p>
    {!round && <button type="button" className={styles.primary} data-member-tour="game-practice-start" disabled={busy} onClick={() => void run("start")}><Play size={17} aria-hidden="true" />{busy ? t("בוחרים שאלה מהמאגר…", "Choosing a bank question…") : t("לנסות שאלה", "Try a question")}</button>}
    {error && <p className={styles.error} role="alert">{error}</p>}
    {round && <div className={practiceStyles.round}>
      <h3 ref={heading} tabIndex={-1}><BidiText>{round.question.prompt}</BidiText></h3>
      <QuestionActions key={round.question.key} lang={lang} questionKey={round.question.key} questionTitle={round.question.prompt} variant={round.question.variant} context="quiz" />
      <fieldset className={practiceStyles.choices} disabled={busy || !!result || expired}>
        <legend className={practiceStyles.legend}>{t("בחרו תשובה אחת", "Choose one answer")}</legend>
        {round.question.choices.map((value, index) => <label key={index} className={`${practiceStyles.choice} ${choice === index ? practiceStyles.selected : ""} ${result?.correct_index === index ? practiceStyles.correct : ""}`}>
          <input type="radio" name="game-practice-answer" value={index} checked={choice === index} onChange={() => setChoice(index)} data-member-tour="game-practice-choice" />
          <span className={styles.choiceNumber} aria-hidden="true">{lang === "he" ? ["א", "ב", "ג", "ד"][index] : ["A", "B", "C", "D"][index]}</span>
          <BidiText>{value}</BidiText>
          {result?.correct_index === index && <Check size={18} aria-label={t("התשובה הנכונה", "Correct answer")} />}
        </label>)}
      </fieldset>
      {!result && !expired && <button type="button" className={styles.primary} data-member-tour="game-practice-check" disabled={choice === null || busy} onClick={() => void run("answer")}>{busy ? t("בודקים את התשובה…", "Checking your answer…") : t("בדיקת התשובה", "Check answer")}</button>}
      {result && <div className={practiceStyles.result} data-member-tour="game-practice-result" role="status">
        <h3 ref={resultHeading} tabIndex={-1}>{result.correct ? <Check size={20} aria-hidden="true" /> : <CircleHelp size={20} aria-hidden="true" />}{result.correct ? t("נכון! הנה ההסבר", "Correct! Here is why") : t("הפעם זו לא התשובה הנכונה. הנה ההסבר", "That is not the correct answer. Here is why")}</h3>
        {!result.correct && <p><strong>{t("התשובה הנכונה", "Correct answer")}</strong> <BidiText>{result.question.choices[result.correct_index]}</BidiText></p>}
        <p><BidiText>{result.explanation}</BidiText></p>
        <p className={styles.muted}>{t("במשחק מול חבר עונים על חמש שאלות, עד דקה לכל שאלה. הניקוד נקבע לפי מספר התשובות הנכונות, ובתיקו לפי זמן המענה הכולל.", "In a game with a friend, you answer five questions with up to a minute each. Correct answers decide the score, with total answering time breaking ties.")}</p>
      </div>}
      {(result || expired) && <button type="button" data-member-tour="game-practice-start" disabled={busy} onClick={() => void run("start")}><RotateCcw size={17} aria-hidden="true" />{busy ? t("טוענים שאלה…", "Loading a question…") : t("שאלה נוספת מהמאגר", "Another bank question")}</button>}
    </div>}
  </section>;
}
