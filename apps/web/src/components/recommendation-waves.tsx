"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { proseDirection } from "../lib/bidi-segments";
import { ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, ReadinessQuestion } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { distinctRecommendations } from "../lib/recommendations";
import { BidiText } from "./bidi-text";
import styles from "./recommendation-waves.module.css";

/** Exact next-question recommendations, rather than a preview of questions not selected by the server yet. */
export function RecommendationWaves({ api, lang, refreshKey, enabled, busyKey, disabled, actionError, onStart, onOpenGoal, onOpenLibrary }: {
  api: Pick<PracticeApi, "readiness">;
  lang: Lang;
  refreshKey: string;
  enabled: boolean;
  busyKey: string | null;
  disabled?: boolean;
  actionError?: string;
  onStart: (question: ReadinessQuestion) => void;
  onOpenGoal: () => void;
  onOpenLibrary: () => void;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const id = useId();
  const [questions, setQuestions] = useState<ReadinessQuestion[]>([]);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const load = useCallback(() => {
    const version = ++generation.current;
    setQuestions([]);
    setError("");
    setLoading(enabled);
    if (!enabled) return;
    void api.readiness(lang).then(value => {
      if (generation.current === version) setQuestions(distinctRecommendations(value.next_questions ?? []));
    }).catch(reason => {
      if (generation.current === version) setError(apiMessage(reason, lang));
    }).finally(() => {
      if (generation.current === version) setLoading(false);
    });
  }, [api, lang, enabled]);
  useEffect(() => {
    load();
    return () => { ++generation.current; };
  }, [load, refreshKey]);
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  const blocked = disabled || !!busyKey || loading;
  const wave = `M0 132 ${questions.map((_, index) => {
    const x = index * 300;
    return `C${x + 75} 132 ${x + 75} 48 ${x + 150} 48 S${x + 225} 132 ${x + 300} 132`;
  }).join(" ")}`;

  return <section className={styles.section} aria-labelledby={`${id}-title`} aria-busy={loading} data-recommendation-waves>
    <header className={styles.heading}>
      <div><h2 id={`${id}-title`}>{t("השאלות הבאות בשבילכם", "Your next questions")}</h2>
        <p>{t("כל גל הוא שאלה מומלצת. בחרו אחת כדי להתחיל לתרגל.", "Each wave is a recommended question. Choose one to start practicing.")}</p></div>
      {enabled && <button type="button" className={styles.refresh} disabled={blocked} onClick={load} aria-label={t("רענון השאלות המומלצות", "Refresh recommended questions")}><RotateCcw size={17} aria-hidden="true" /></button>}
    </header>
    <span className={styles.visuallyHidden} role="status">{busyKey?.startsWith("recommendation:") ? t("פותחים את השאלה שבחרתם…", "Opening your chosen question…") : ""}</span>
    {actionError && <p className="notice error" role="alert" dir={proseDirection(actionError)}><BidiText>{actionError}</BidiText></p>}
    {!enabled ? <div className={styles.empty}><p>{t("בחרו תפקידים או למידה ללא יעד מוגדר, ונציע שאלות שמתאימות לתוכנית שלכם.", "Choose roles or open-ended learning to get questions for your plan.")}</p><button type="button" onClick={onOpenGoal}>{t("לבחירת מסלול למידה", "Choose a learning approach")}</button></div>
      : loading ? <p className={styles.status} role="status">{t("מוצאים את השאלות הבאות שלכם…", "Finding your next questions…")}</p>
      : error ? <div className="notice error" role="alert"><p dir={proseDirection(error)}><BidiText>{error}</BidiText></p><button type="button" disabled={!!busyKey} onClick={load}><RotateCcw size={16} aria-hidden="true" />{t("לנסות שוב", "Try again")}</button></div>
      : !questions.length ? <div className={styles.empty}><p>{t("אין כרגע המלצות נוספות. אפשר לבחור שאלה מהמאגר או לרענן את ההמלצות.", "There are no further recommendations right now. Choose a question from the library or refresh the recommendations.")}</p><button type="button" onClick={onOpenLibrary}>{t("למאגר השאלות", "Open the question library")}</button></div>
      : <div className={styles.path} data-recommendation-path>
        <svg className={styles.desktopWave} viewBox={`0 0 ${questions.length * 300} 160`} preserveAspectRatio="none" aria-hidden="true"><path d={wave} /></svg>
        <ol className={styles.questions} style={{ "--recommendation-count": questions.length } as React.CSSProperties}>
          {questions.map((question, index) => <li className={styles.item} key={question.key} data-recommendation-key={question.key}>
            <svg className={styles.mobileWave} viewBox="0 0 72 100" preserveAspectRatio="none" aria-hidden="true"><path d="M48 0 C48 25 24 25 24 50 S48 75 48 100" /></svg>
            <button type="button" className={styles.question} disabled={blocked} onClick={() => onStart(question)} aria-label={t(`לתרגל: ${question.title}`, `Practice: ${question.title}`)} aria-describedby={question.reason ? `${id}-reason-${index}` : undefined}>
              <span className={styles.node} aria-hidden="true">{index + 1}</span>
              <span className={styles.topic} dir={proseDirection(question.skill_label)}><BidiText>{question.skill_label}</BidiText></span>
              <strong className={styles.title} dir={proseDirection(question.title)}><BidiText>{question.title}</BidiText></strong>
              {question.reason && <span id={`${id}-reason-${index}`} className={styles.reason} dir={proseDirection(question.reason)}><BidiText>{question.reason}</BidiText></span>}
              <span className={styles.action}>{busyKey === `recommendation:${question.key}` ? t("פותחים…", "Opening…") : t("לתרגול השאלה", "Practice this question")}<Arrow size={16} aria-hidden="true" /></span>
            </button>
          </li>)}
        </ol>
      </div>}
  </section>;
}
