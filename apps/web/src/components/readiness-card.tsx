"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, RefreshCw, Target } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, Readiness, ReadinessQuestion, ReadinessSkill } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { BidiText } from "./bidi-text";

/** A fresh view of readiness for the current goal. It never turns the report's private numeric score into a grade. */
export function ReadinessCard({ api, lang, refreshKey, onStartAttempt, onEditGoal }: {
  api: PracticeApi;
  lang: Lang;
  refreshKey: string;
  onStartAttempt: (id: string) => void;
  onEditGoal: () => void;
}) {
  const [retry, setRetry] = useState(0);
  const requestKey = `${lang}:${refreshKey}:${retry}`;
  const [loaded, setLoaded] = useState<{ key: string; data: Readiness | null; error: string } | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [actionError, setActionError] = useState<{ key: string; message: string } | null>(null);
  const starting = useRef(false);
  const mounted = useRef(false);
  const contextVersion = useRef(0);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    const version = ++contextVersion.current;
    // A new role/language invalidates the old report immediately. Keep any
    // in-flight start locked until it settles, even if the new report arrives first.
    setLoaded(null);
    setActionError(null);
    api.readiness(lang).then(
      (data) => { if (mounted.current && contextVersion.current === version) setLoaded({ key: requestKey, data, error: "" }); },
      (error) => { if (mounted.current && contextVersion.current === version) setLoaded({ key: requestKey, data: null, error: apiMessage(error, lang) }); },
    );
    return () => { ++contextVersion.current; };
  }, [api, lang, requestKey]);

  async function start(question: ReadinessQuestion) {
    if (!mounted.current || starting.current || loaded?.key !== requestKey || !loaded.data) return;
    starting.current = true;
    setBusyKey(question.key);
    setActionError(null);
    const keyAtStart = requestKey;
    const versionAtStart = contextVersion.current;
    const isCurrent = () => mounted.current && contextVersion.current === versionAtStart;
    try {
      const attempt = await api.startAttempt({ question_key: question.key, language: lang, mode: "deep", source: "readiness", screen: "progress" });
      if (isCurrent()) onStartAttempt(attempt.id);
    } catch (error) {
      if (isCurrent()) setActionError({ key: keyAtStart, message: apiMessage(error, lang) });
    } finally {
      starting.current = false;
      if (mounted.current) setBusyKey(null);
    }
  }

  const current = loaded?.key === requestKey ? loaded : null;
  return <ReadinessContent readiness={current?.data ?? null} lang={lang} loading={!current} error={current?.error ?? ""}
    busyKey={busyKey} actionError={actionError?.key === requestKey ? actionError.message : ""} onRetry={() => setRetry((n) => n + 1)} onEditGoal={onEditGoal} onStart={(question) => void start(question)} />;
}

/** Kept separate so rendering covers all evidence states without calling the live service. */
export function ReadinessContent({ readiness, lang, loading = false, error = "", actionError = "", busyKey = null, onRetry, onEditGoal, onStart }: {
  readiness: Readiness | null;
  lang: Lang;
  loading?: boolean;
  error?: string;
  actionError?: string;
  busyKey?: string | null;
  onRetry: () => void;
  onEditGoal: () => void;
  onStart: (question: ReadinessQuestion) => void;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  const skills = [...(readiness?.skills ?? [])].sort((a, b) => b.weight_share - a.weight_share);
  const questions = readiness?.next_questions.slice(0, 3) ?? [];
  const renderSkills = (list: ReadinessSkill[]) => <ul className="readiness-skills">{list.map((skill) => (
    <li key={skill.key} className={`readiness-skill freshness-${skill.freshness}`}>
      <div className="readiness-skill-head"><strong><bdi dir="auto"><BidiText>{skill.label}</BidiText></bdi></strong><span className="badge">{freshnessLabel(skill.freshness, lang)}</span></div>
      <dl className="readiness-levels">
        <div><dt>{t("רמה נדרשת", "Required level")}</dt><dd><bdi dir="ltr">{skill.required_level} / 5</bdi></dd></div>
        <div><dt>{skill.freshness === "expired" ? t("רמה שנמדדה בעבר", "Previously measured level") : t("הרמה שלכם", "Your level")}</dt><dd>{skill.level === null ? t("טרם הוערכה", "Not assessed yet") : <bdi dir="ltr">{skill.level} / 5</bdi>}</dd></div>
        <div><dt>{t("פער ליעד", "Gap to goal")}</dt><dd>{skill.gap === null ? t("נדרשת תשובה להערכה", "Needs an answer to assess") : skill.gap > 0 ? t(`${skill.gap} רמות לחיזוק`, `${skill.gap} ${skill.gap === 1 ? "level" : "levels"} to build`) : t("עומדים בדרישה", "Meets the requirement")}</dd></div>
      </dl>
      {!skill.askable && <p className="small muted readiness-unavailable">{t("עדיין אין במאגר שאלה שבודקת את המיומנות הזו.", "There is no question in the bank that examines this skill yet.")}</p>}
    </li>
  ))}</ul>;

  return (
    <section className="readiness-card" aria-labelledby="readiness-title" aria-busy={loading}>
      <header className="board-head"><h2 id="readiness-title"><Target size={20} aria-hidden="true" />{t("מוכנות לתפקיד שלכם", "Readiness for your role")}</h2>{readiness?.job_type_label && <span className="small muted"><bdi dir="auto"><BidiText>{readiness.job_type_label}</BidiText></bdi></span>}</header>
      {loading ? <p role="status" className="loading">{t("בודקים את התמונה לפי היעד שלכם…", "Loading readiness for your goal…")}</p> : error ? (
        <div className="readiness-error"><p role="alert">{error}</p><button type="button" onClick={onRetry}><RefreshCw size={15} aria-hidden="true" />{t("לנסות שוב", "Try again")}</button></div>
      ) : readiness ? (
        <>
          {readiness.ready_to_judge && readiness.readiness_word && <p className="readiness-word" dir="auto">{readiness.readiness_word}</p>}
          <p className="readiness-message" dir="auto"><BidiText>{readiness.message}</BidiText></p>
          {!readiness.job_type ? <button type="button" className="primary" onClick={onEditGoal}>{t("לבחור את התפקיד שלי", "Choose my role")}</button> : (
            <>
              {questions.length > 0 ? <div className="readiness-next"><h3>{t("הצעד הבא למוכנות", "The next step toward readiness")}</h3><p className="small muted">{t("שאלות שנבחרו לפי הפערים והמידע שחסר עליכם. אפשר לבחור אחת ולהתחיל תרגול מעמיק.", "Questions selected for your gaps and missing evidence. Choose one to start deep practice.")}</p><ol>{questions.map((question) => <li key={question.key}>
                <button type="button" className="readiness-question" disabled={!!busyKey} onClick={() => onStart(question)} aria-label={`${t("לתרגל", "Practise")}: ${question.title}`}>
                  <span className="readiness-question-copy"><strong><bdi dir="auto"><BidiText>{question.title}</BidiText></bdi></strong><span dir="auto"><BidiText>{question.reason}</BidiText></span><small><bdi dir="auto"><BidiText>{question.skill_label}</BidiText></bdi></small></span><span className="readiness-question-action">{busyKey === question.key ? t("פותחים…", "Opening…") : t("לתרגל", "Practise")}<Arrow size={16} aria-hidden="true" /></span>
                </button>
              </li>)}</ol></div> : <p className="small muted readiness-no-questions">{t("אין כרגע שאלות חדשות מומלצות. אפשר להמשיך לפי התוכנית שלכם או לחזור על שאלה מהמאגר.", "There are no new recommended questions right now. Continue with your plan or revisit a question in the library.")}</p>}
              {actionError && <p className="notice error" role="alert">{actionError}</p>}
              {skills.length > 0 && <div className="readiness-breakdown"><h3>{t("המיומנויות שהתפקיד דורש", "The skills your role requires")}</h3><p className="small muted">{t("מסודרות לפי המשקל שלהן בתפקיד. מידע ישן נשאר מוצג, אך נדרשת תשובה חדשה כדי לאמת אותו.", "Ordered by their weight in the role. Older levels remain visible; a fresh answer is needed to confirm them.")}</p>{renderSkills(skills.slice(0, 5))}{skills.length > 5 && <details className="readiness-more"><summary>{t(`לכל ${skills.length} המיומנויות`, `View all ${skills.length} skills`)}</summary>{renderSkills(skills.slice(5))}</details>}</div>}
            </>
          )}
        </>
      ) : null}
    </section>
  );
}

export function freshnessLabel(freshness: string, lang: Lang): string {
  const labels: Record<string, [string, string]> = { fresh: ["עדכני", "Fresh"], aging: ["כדאי לרענן", "Refresh soon"], expired: ["נדרש אימות מחדש", "Needs a fresh check"], none: ["אין הערכה עדכנית", "No current evidence"] };
  const label = labels[freshness] ?? labels.none;
  return label[lang === "he" ? 0 : 1];
}
