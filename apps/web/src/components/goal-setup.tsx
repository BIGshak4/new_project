"use client";

import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { proseDirection } from "../lib/bidi-segments";
import { BookOpen, BriefcaseBusiness, CalendarDays, ChevronDown, Clock3, GraduationCap, RotateCcw, Sparkles, Target, X } from "lucide-react";
import type { Lang } from "./auth";
import type { Goal, JobType, PracticeApi, Seniority } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { goalJobTypes } from "../lib/goal-selection";
import { BidiText } from "./bidi-text";
import { toast } from "./toaster";
import styles from "./goal-setup.module.css";

const MINUTES = [15, 30, 45, 60, 90] as const;
const MIN_DAILY_MINUTES = 5;
const MAX_DAILY_MINUTES = 600;
const SENIORITIES: Seniority[] = ["student", "junior", "mid", "senior", "staff", "principal"];
type Mode = "targeted" | "explore";
type Field = "roles" | "minutes" | "date";
const selectedKeys = goalJobTypes;
const signature = (goal: Goal | null) => JSON.stringify([selectedKeys(goal), goal?.learning_mode ?? "targeted", goal?.minutes_per_day, goal?.seniority, goal?.interview_date]);

/** Goal choices stay compact; the account stores the complete set of selected roles. */
export function GoalSetup({ api, userId, lang, goal, onSaved, onSkip, compact = false, focusRequest = 0 }: {
  api: PracticeApi;
  userId: string;
  lang: Lang;
  goal: Goal | null;
  onSaved: (goal: Goal) => void;
  onSkip?: () => void;
  compact?: boolean;
  /** Increment on each explicit open, including when this form is already mounted. */
  focusRequest?: number;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const id = useId();
  const [jobs, setJobs] = useState<JobType[]>([]);
  const [jobsLoading, setJobsLoading] = useState(true);
  const [jobsError, setJobsError] = useState("");
  const [jobsRetry, setJobsRetry] = useState(0);
  const [jobTypes, setJobTypes] = useState<string[]>(() => selectedKeys(goal));
  const [mode, setMode] = useState<Mode>(goal?.learning_mode ?? "targeted");
  const [date, setDate] = useState(goal?.interview_date ?? "");
  const [hasDate, setHasDate] = useState(!!goal?.interview_date);
  const [minutes, setMinutes] = useState(String(goal?.minutes_per_day ?? 30));
  const [customMinutes, setCustomMinutes] = useState(!MINUTES.some(value => value === (goal?.minutes_per_day ?? 30)));
  const [seniority, setSeniority] = useState<Seniority>(goal?.seniority ?? "student");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [invalid, setInvalid] = useState<Field | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const rolesSection = useRef<HTMLDetailsElement>(null);
  const minutesSection = useRef<HTMLDetailsElement>(null);
  const dateSection = useRef<HTMLDetailsElement>(null);
  const dirty = useRef(false);
  const savedSignature = signature(goal);

  // Loading the saved goal must not replace an edit or reset it when language changes.
  useEffect(() => {
    if (dirty.current) return;
    setJobTypes(selectedKeys(goal));
    setMode(goal?.learning_mode ?? "targeted");
    setDate(goal?.interview_date ?? "");
    setHasDate(!!goal?.interview_date);
    setMinutes(String(goal?.minutes_per_day ?? 30));
    setCustomMinutes(!MINUTES.some(value => value === (goal?.minutes_per_day ?? 30)));
    setSeniority(goal?.seniority ?? "student");
  }, [savedSignature]);

  useEffect(() => {
    if (!focusRequest) return;
    const frame = requestAnimationFrame(() => {
      heading.current?.focus({ preventScroll: true });
      heading.current?.scrollIntoView({ block: "start", behavior: "instant" });
    });
    return () => cancelAnimationFrame(frame);
  }, [focusRequest]);

  useEffect(() => {
    let current = true;
    setJobsLoading(true);
    setJobsError("");
    void api.jobTypes(lang).then(list => {
      if (!current) return;
      if (!list.length) throw new Error(t("רשימת התפקידים אינה זמינה כרגע.", "The list of roles is unavailable right now."));
      setJobs(list);
    }).catch(reason => {
      if (current) setJobsError(apiMessage(reason, lang));
    }).finally(() => {
      if (current) setJobsLoading(false);
    });
    return () => { current = false; };
  }, [api, lang, jobsRetry]);

  function edited() {
    dirty.current = true;
    setError("");
    setInvalid(null);
  }

  const today = new Date();
  const todayIso = new Date(today.getTime() - today.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  const days = date ? Math.round((new Date(`${date}T12:00:00`).getTime() - new Date(`${todayIso}T12:00:00`).getTime()) / 86_400_000) : null;
  const minuteCount = Number(minutes);
  const minutesValid = minutes.trim() !== "" && Number.isInteger(minuteCount) && minuteCount >= MIN_DAILY_MINUTES && minuteCount <= MAX_DAILY_MINUTES;
  const selectedJobs = jobTypes.map(key => jobs.find(job => job.key === key));
  const unavailableRoles = selectedJobs.some(job => !job);
  const seniorityLabel = (value: Seniority) => ({
    student: t("סטודנט/ית או בוגר/ת טרי/ה", "Student or new graduate"),
    junior: t("ג׳וניור (עד שנתיים)", "Junior (up to 2 years)"),
    mid: t("ניסיון בינוני (2–5 שנים)", "Mid-level (2–5 years)"),
    senior: t("סניור", "Senior"),
    staff: t("סטאף", "Staff"),
    principal: t("פרינסיפל", "Principal"),
  })[value];

  function showValidation(field: Field, message: string) {
    setInvalid(field);
    setError(message);
    const section = field === "roles" ? rolesSection.current : field === "minutes" ? minutesSection.current : dateSection.current;
    if (section) section.open = true;
    requestAnimationFrame(() => section?.querySelector<HTMLInputElement>(field === "minutes" ? 'input[type="number"]' : field === "date" ? 'input[type="date"]' : "input")?.focus());
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || jobsLoading || jobsError) return;
    if (mode === "targeted" && (!jobTypes.length || unavailableRoles)) {
      showValidation("roles", unavailableRoles
        ? t("אחד התפקידים שנשמרו כבר לא זמין. הסירו אותו ובחרו תפקיד מהרשימה.", "One saved role is no longer available. Remove it and choose a role from the list.")
        : t("בחרו לפחות תפקיד אחד, או עברו למסלול ללא יעד מוגדר.", "Choose at least one role, or switch to learning without a defined goal."));
      return;
    }
    if (!minutesValid) {
      setCustomMinutes(true);
      showValidation("minutes", t("הזינו מספר שלם בין 5 ל־600 דקות ביום.", "Enter a whole number from 5 to 600 minutes a day."));
      return;
    }
    if (mode === "targeted" && hasDate && (!date || days === null || !Number.isFinite(days) || days < 0)) {
      showValidation("date", t("בחרו תאריך מהיום והלאה, או סמנו שעדיין אין תאריך לראיון.", "Choose today or a future date, or select that you do not have an interview date yet."));
      return;
    }
    setBusy(true);
    setError("");
    try {
      const saved = await api.saveGoal({
        job_type: mode === "targeted" ? jobTypes[0] : null,
        job_types: mode === "targeted" ? jobTypes : [],
        learning_mode: mode,
        interview_date: mode === "targeted" && hasDate ? date : null,
        minutes_per_day: minuteCount,
        seniority,
        language: lang,
      }, userId);
      dirty.current = false;
      onSaved(saved);
      toast.success(t("ההעדפות נשמרו. תוכנית הלמידה מתעדכנת.", "Preferences saved. Your learning plan is updating."));
    } catch (reason) {
      setError((reason as { code?: string }).code === "network"
        ? t("לא הצלחנו לאשר את השמירה. הבחירות עדיין בטופס, ואפשר לנסות שוב.", "We couldn’t confirm the save. Your choices are still in the form. Please try again.")
        : apiMessage(reason, lang));
    } finally {
      setBusy(false);
    }
  }

  function bar(label: string, value: string, icon: ReactNode, labelId: string, tourControl?: string) {
    return <summary className={styles.bar} data-muxi-control={tourControl} aria-disabled={busy || undefined} onClick={event => { if (busy) event.preventDefault(); }}>
      <span className={styles.barIcon}>{icon}</span>
      <span className={styles.barText}><span id={labelId} className={styles.barLabel}>{label}</span><span className={styles.barValue} dir={proseDirection(value, lang === "he" ? "rtl" : "ltr")}><BidiText>{value}</BidiText></span></span>
      <ChevronDown className={styles.chevron} size={18} aria-hidden="true" />
    </summary>;
  }

  return <section className={`goal-setup ${compact ? "compact" : ""} ${styles.setup}`} aria-labelledby={`${id}-title`}>
    <header className="goal-head">
      <Target size={22} aria-hidden="true" />
      <div>
        <h2 id={`${id}-title`} className={styles.heading} ref={heading} tabIndex={-1}>{goal?.complete ? t("עדכון תוכנית הלמידה", "Update your learning plan") : t("איך תרצו ללמוד?", "How would you like to learn?")}</h2>
        <p className={styles.intro}>{t("בחרו כיוון וקצב שנוח לכם. אפשר לשנות הכול בהמשך.", "Choose a direction and a pace that work for you. You can change them later.")}</p>
      </div>
    </header>

    <form className={styles.form} noValidate onSubmit={event => void save(event)} aria-busy={busy}>
      <fieldset className={styles.mode} disabled={busy}>
        <legend className={styles.visuallyHidden}>{t("מסלול הלמידה", "Learning approach")}</legend>
        <label className={`${styles.modeChoice} ${mode === "targeted" ? styles.chosen : ""}`}>
          <input type="radio" name={`${id}-mode`} value="targeted" checked={mode === "targeted"} onChange={() => { edited(); setMode("targeted"); }} />
          <span>{t("אני מתכונן לתפקיד", "I’m preparing for a role")}</span>
        </label>
        <label className={`${styles.modeChoice} ${mode === "explore" ? styles.chosen : ""}`}>
          <input data-muxi-control="goal-mode-explore" type="radio" name={`${id}-mode`} value="explore" checked={mode === "explore"} onChange={() => { edited(); setMode("explore"); }} />
          <span>{t("אין לי יעד מוגדר, למד אותי", "I don’t have a defined goal. Teach me")}</span>
        </label>
      </fieldset>

      <div className={styles.sections}>
        <div>
          {mode === "targeted" ? <>
            <details className={styles.section} ref={rolesSection} data-goal-section="roles">
              {bar(t("תפקיד", "Role"), jobTypes.length === 1 ? t("תפקיד אחד נבחר", "One role selected") : jobTypes.length > 1 ? t(`${jobTypes.length} תפקידים נבחרו`, `${jobTypes.length} roles selected`) : t("בחרו תפקיד אחד או יותר", "Choose one or more roles"), <BriefcaseBusiness size={19} aria-hidden="true" />, `${id}-roles-label`, "goal-roles")}
              <fieldset className={styles.options} disabled={busy || jobsLoading || !!jobsError} aria-labelledby={`${id}-roles-label`}>
                <legend className={styles.visuallyHidden}>{t("בחירת תפקידים", "Choose roles")}</legend>
                <p className={styles.help}>{t("אפשר לבחור כמה תפקידים. התוכנית תשלב ביניהם.", "Choose as many roles as you like. Your plan will combine them.")}</p>
                {jobs.map(job => <label className={styles.option} key={job.key}>
                  <input type="checkbox" checked={jobTypes.includes(job.key)} aria-invalid={invalid === "roles" || undefined} onChange={event => { edited(); setJobTypes(keys => event.target.checked ? [...keys, job.key] : keys.filter(key => key !== job.key)); }} />
                  <span dir={proseDirection(job.label)}><BidiText>{job.label}</BidiText></span>
                </label>)}
              </fieldset>
            </details>
            {jobTypes.length > 0 && <div className={styles.selectedRoles} role="list" aria-label={t("התפקידים שבחרתם", "Your selected roles")}>
              {jobTypes.map((key, index) => {
                const job = selectedJobs[index];
                const label = job?.label ?? goal?.job_type_labels?.[index] ?? (goal?.job_type === key ? goal.job_type_label : null) ?? key;
                return <article className={styles.selectedRole} key={key} role="listitem">
                  <div className={styles.roleTitle}><strong dir={proseDirection(label)}><BidiText>{label}</BidiText></strong><button type="button" className={styles.remove} disabled={busy} aria-label={t(`הסרת התפקיד ${label}`, `Remove ${label}`)} onClick={() => { edited(); setJobTypes(keys => keys.filter(value => value !== key)); }}><X size={17} aria-hidden="true" /></button></div>
                  <p dir={proseDirection(job?.description ?? "", lang === "he" ? "rtl" : "ltr")}><BidiText>{job?.description ?? (jobsLoading ? t("טוענים את תיאור התפקיד…", "Loading the role description…") : t("התפקיד הזה אינו זמין כרגע. אפשר להסיר אותו ולבחור תפקיד אחר.", "This role is unavailable right now. Remove it and choose another role."))}</BidiText></p>
                </article>;
              })}
            </div>}
          </> : <section className={styles.explore} aria-labelledby={`${id}-explore-title`}>
            <div className={styles.exploreHead}><BookOpen size={20} aria-hidden="true" /><h3 id={`${id}-explore-title`}>{t("מכירים את התפקידים", "Explore the roles")}</h3></div>
            <p className={styles.help}>{t("נלמד יסודות ממגוון התחומים, בלי לבחור תפקיד או לקבוע תאריך לראיון.", "Learn fundamentals across the fields, without choosing a role or setting an interview date.")}</p>
            <div className={styles.roleOverview}>{jobs.map(job => <article className={styles.overviewRole} key={job.key}><h4 dir={proseDirection(job.label)}><BidiText>{job.label}</BidiText></h4><p dir={proseDirection(job.description)}><BidiText>{job.description}</BidiText></p></article>)}</div>
          </section>}
          {jobsLoading && <p className={styles.catalogStatus} role="status">{t("טוענים את התפקידים…", "Loading roles…")}</p>}
          {jobsError && <div className={styles.catalogError} role="alert"><p>{t("לא הצלחנו לטעון את התפקידים. נסו שוב כדי להמשיך.", "We couldn’t load the roles. Try again to continue.")}</p><button type="button" disabled={busy} onClick={() => setJobsRetry(value => value + 1)}><RotateCcw size={16} aria-hidden="true" />{t("טעינה מחדש", "Retry loading")}</button></div>}
        </div>

        <details className={styles.section} ref={minutesSection} data-goal-section="minutes">
          {bar(t("זמן ביום", "Daily time"), minutesValid ? t(`${minuteCount} דקות ביום`, `${minuteCount} minutes a day`) : t("הזינו זמן בדקות", "Enter a time in minutes"), <Clock3 size={19} aria-hidden="true" />, `${id}-minutes-label`)}
          <fieldset className={styles.options} disabled={busy} aria-labelledby={`${id}-minutes-label`}>
            <legend className={styles.visuallyHidden}>{t("כמה זמן ביום?", "How much time a day?")}</legend>
            <div className={styles.presets}>{MINUTES.map(value => <label className={`${styles.preset} ${!customMinutes && Number(minutes) === value ? styles.chosen : ""}`} key={value}>
              <input type="radio" name={`${id}-minutes`} checked={!customMinutes && Number(minutes) === value} onChange={() => { edited(); setCustomMinutes(false); setMinutes(String(value)); }} />
              <span>{value} {t("דקות", "min")}</span>
            </label>)}</div>
            <label className={styles.option}><input type="radio" name={`${id}-minutes`} checked={customMinutes} onChange={() => { edited(); setCustomMinutes(true); }} /><span>{t("הגדרה ידנית בדקות", "Set a custom number of minutes")}</span></label>
            {customMinutes && <div className={styles.customMinutes}><label htmlFor={`${id}-custom-minutes`}>{t("מספר דקות ביום", "Minutes per day")}</label><input id={`${id}-custom-minutes`} type="number" inputMode="numeric" step={1} min={MIN_DAILY_MINUTES} max={MAX_DAILY_MINUTES} value={minutes} aria-invalid={invalid === "minutes" || undefined} aria-describedby={`${id}-minutes-help`} onChange={event => { edited(); setMinutes(event.target.value); }} /><p id={`${id}-minutes-help`} className={styles.help}>{t("מספר שלם בין 5 ל־600 דקות.", "A whole number from 5 to 600 minutes.")}</p></div>}
          </fieldset>
        </details>

        <details className={styles.section} data-goal-section="seniority">
          {bar(t("שלב בקריירה", "Career stage"), seniorityLabel(seniority), <GraduationCap size={19} aria-hidden="true" />, `${id}-seniority-label`)}
          <fieldset className={styles.options} disabled={busy} aria-labelledby={`${id}-seniority-label`}>
            <legend className={styles.visuallyHidden}>{t("שלב בקריירה", "Career stage")}</legend>
            {SENIORITIES.map(value => <label className={styles.option} key={value}><input type="radio" name={`${id}-seniority`} checked={seniority === value} onChange={() => { edited(); setSeniority(value); }} /><span>{seniorityLabel(value)}</span></label>)}
          </fieldset>
        </details>

        {mode === "targeted" && <details className={styles.section} ref={dateSection} data-goal-section="date">
          {bar(t("תאריך ראיון", "Interview date"), !hasDate ? t("עדיין אין תאריך לראיון", "No interview date yet") : date && Number.isFinite(days) ? new Date(`${date}T12:00:00`).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB") : t("בחרו תאריך", "Choose a date"), <CalendarDays size={19} aria-hidden="true" />, `${id}-date-label`)}
          <fieldset className={styles.options} disabled={busy} aria-labelledby={`${id}-date-label`}>
            <legend className={styles.visuallyHidden}>{t("תאריך הראיון", "Interview date")}</legend>
            <label className={styles.option}><input type="radio" name={`${id}-date`} checked={!hasDate} onChange={() => { edited(); setHasDate(false); }} /><span>{t("עדיין אין תאריך לראיון", "I don’t have an interview date yet")}</span></label>
            <label className={styles.option}><input type="radio" name={`${id}-date`} checked={hasDate} onChange={() => { edited(); setHasDate(true); }} /><span>{t("יש לי תאריך לראיון", "I have an interview date")}</span></label>
            {hasDate && <div className={styles.dateInput}><label htmlFor={`${id}-interview-date`}>{t("תאריך הראיון", "Interview date")}</label><input id={`${id}-interview-date`} type="date" value={date} min={todayIso} aria-invalid={invalid === "date" || undefined} onChange={event => { edited(); setDate(event.target.value); }} />{date && <p className={styles.help}>{days !== null && days < 0 ? t("התאריך עבר. בחרו תאריך מהיום והלאה.", "That date has passed. Choose today or a future date.") : days === 0 ? t("היום! בהצלחה.", "Today! Good luck.") : t(`${days} ימים עד הראיון`, `${days} days until the interview`)}</p>}</div>}
            {!hasDate && <p className={styles.help}>{t("אין צורך בתאריך כדי להתחיל. התוכנית תתקדם משבוע לשבוע.", "You can start without a date. The plan will continue week by week.")}</p>}
          </fieldset>
        </details>}
      </div>

      {error && <p className="notice error" role="alert" dir={proseDirection(error)}><BidiText>{error}</BidiText></p>}
      <div className="goal-actions">
        <button className="primary" type="submit" data-muxi-control="goal-save" disabled={busy || jobsLoading || !!jobsError || (mode === "targeted" && !jobTypes.length)}><Sparkles size={16} aria-hidden="true" />{busy ? t("שומרים…", "Saving…") : mode === "explore" ? t("מתחילים ללמוד", "Start learning") : goal?.complete ? t("שמירת התוכנית", "Save plan") : t("בונים לי תוכנית", "Build my plan")}</button>
        {onSkip && <button className="text-button" type="button" disabled={busy} onClick={onSkip}>{t("אחר כך", "Later")}</button>}
      </div>
    </form>
  </section>;
}
