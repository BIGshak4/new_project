"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Clock3, Sparkles, Target } from "lucide-react";
import type { Lang } from "./auth";
import type { Goal, JobType, PracticeApi, Seniority } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";

const MINUTES = [15, 30, 45, 60, 90] as const;
const SENIORITIES: Seniority[] = ["student", "junior", "mid", "senior", "staff", "principal"];

/**
 * The first thing a new user answers: which job they are interviewing for, when, and how much time they have
 * each day. The plan, the question order and the mock interview follow these answers. Editable any time.
 */
export function GoalSetup({
  api,
  lang,
  goal,
  onSaved,
  onSkip,
  compact = false,
}: {
  api: PracticeApi;
  lang: Lang;
  goal: Goal | null;
  onSaved: (goal: Goal) => void;
  onSkip?: () => void;
  compact?: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [jobs, setJobs] = useState<JobType[]>([]);
  const [jobType, setJobType] = useState(goal?.job_type ?? "");
  const [date, setDate] = useState(goal?.interview_date ?? "");
  const [minutes, setMinutes] = useState<number>(goal?.minutes_per_day ?? 30);
  const [seniority, setSeniority] = useState<Seniority>(goal?.seniority ?? "student");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .jobTypes(lang)
      .then((list) => {
        if (!cancelled) setJobs(list);
      })
      .catch((e) => {
        if (!cancelled) setError(apiMessage(e, lang));
      });
    return () => {
      cancelled = true;
    };
  }, [api, lang]);

  const today = new Date();
  const todayIso = today.toISOString().slice(0, 10);
  const days = date ? Math.round((new Date(`${date}T12:00:00`).getTime() - new Date(`${todayIso}T12:00:00`).getTime()) / 86_400_000) : null;

  async function save() {
    if (!jobType || busy) return;
    setBusy(true);
    setError("");
    try {
      const saved = await api.saveGoal({
        job_type: jobType,
        interview_date: date || null,
        minutes_per_day: minutes,
        seniority,
        language: lang,
      });
      onSaved(saved);
    } catch (e) {
      setError(apiMessage(e, lang));
    } finally {
      setBusy(false);
    }
  }

  const seniorityLabel = (s: Seniority) =>
    ({
      student: t("סטודנט/ית או בוגר/ת טרי/ה", "Student or new graduate"),
      junior: t("ג׳וניור (עד 2 שנים)", "Junior (up to 2 years)"),
      mid: t("ניסיון בינוני (2-5 שנים)", "Mid-level (2-5 years)"),
      senior: t("סניור", "Senior"),
      staff: t("סטאף", "Staff"),
      principal: t("פרינסיפל", "Principal"),
    })[s];

  return (
    <section className={`goal-setup ${compact ? "compact" : ""}`} aria-labelledby="goal-title">
      <header className="goal-head">
        <Target size={22} aria-hidden="true" />
        <div>
          <h2 id="goal-title">
            {goal?.complete
              ? t("עדכון היעד שלכם", "Update your goal")
              : t("לאיזה ראיון אתם מתכוננים?", "What are you preparing for?")}
          </h2>
          <p className="muted">
            {t(
              "לפי התשובות נבנה תוכנית עבודה עד הראיון, נסדר את השאלות לפי הרלוונטיות ונתאים את הראיון המדומה.",
              "Your answers shape the plan until the interview, the order of the questions and the mock interview.",
            )}
          </p>
        </div>
      </header>

      <div className="goal-field">
        <h3>{t("סוג התפקיד", "The kind of job")}</h3>
        <div className="job-grid" role="radiogroup" aria-label={t("סוג התפקיד", "Job type")}>
          {jobs.map((job) => (
            <button
              key={job.key}
              type="button"
              role="radio"
              aria-checked={jobType === job.key}
              className={`job-card ${jobType === job.key ? "on" : ""}`}
              onClick={() => setJobType(job.key)}
            >
              <strong dir="auto">{job.label}</strong>
              <span dir="auto">{job.description}</span>
            </button>
          ))}
          {!jobs.length && !error && <span className="muted small">{t("טוענים את סוגי התפקידים…", "Loading job types…")}</span>}
        </div>
      </div>

      <div className="goal-columns">
        <div className="goal-field">
          <h3>
            <CalendarDays size={16} aria-hidden="true" /> {t("מתי הראיון?", "When is the interview?")}
          </h3>
          <input
            type="date"
            value={date}
            min={todayIso}
            onChange={(e) => setDate(e.target.value)}
            aria-label={t("תאריך הראיון", "Interview date")}
          />
          <p className="small muted">
            {days === null
              ? t("לא ידוע עדיין? השאירו ריק, נבנה תוכנית שבועית.", "Not known yet? Leave it empty; the plan runs week by week.")
              : days < 0
                ? t("התאריך עבר. בחרו תאריך עתידי.", "That date has passed. Pick a future one.")
                : days === 0
                  ? t("היום! בהצלחה.", "Today! Good luck.")
                  : `${days} ${t("ימים עד הראיון", "days until the interview")}`}
          </p>
        </div>
        <div className="goal-field">
          <h3>
            <Clock3 size={16} aria-hidden="true" /> {t("כמה זמן ביום?", "How much time a day?")}
          </h3>
          <div className="chips" role="radiogroup" aria-label={t("דקות ביום", "Minutes a day")}>
            {MINUTES.map((m) => (
              <button
                key={m}
                type="button"
                role="radio"
                aria-checked={minutes === m}
                className={`chip-button ${minutes === m ? "on" : ""}`}
                onClick={() => setMinutes(m)}
              >
                {m} {t("דק׳", "min")}
              </button>
            ))}
          </div>
        </div>
        <div className="goal-field">
          <h3>{t("איפה אתם בקריירה?", "Where are you in your career?")}</h3>
          <select value={seniority} onChange={(e) => setSeniority(e.target.value as Seniority)} aria-label={t("ניסיון", "Seniority")}>
            {SENIORITIES.map((s) => (
              <option key={s} value={s}>
                {seniorityLabel(s)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      <div className="goal-actions">
        <button className="primary" disabled={busy || !jobType} onClick={() => void save()}>
          <Sparkles size={16} aria-hidden="true" />
          {busy ? t("שומרים…", "Saving…") : goal?.complete ? t("שמירת היעד", "Save goal") : t("בונים לי תוכנית", "Build my plan")}
        </button>
        {onSkip && (
          <button className="text-button" type="button" onClick={onSkip}>
            {t("אחר כך", "Later")}
          </button>
        )}
      </div>
    </section>
  );
}
