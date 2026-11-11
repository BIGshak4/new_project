"use client";

import { useId } from "react";
import { proseDirection } from "../lib/bidi-segments";
import { CalendarDays, Clock3, GraduationCap, PencilLine, Target } from "lucide-react";
import type { Goal, Seniority } from "../lib/practice-api";
import { goalRoleLabel } from "../lib/goal-selection";
import { BidiText } from "./bidi-text";
import styles from "./goal-summary.module.css";

const stages: Record<Seniority, [string, string]> = {
  student: ["סטודנט/ית או בוגר/ת טרי/ה", "Student or new graduate"],
  junior: ["ג׳וניור (עד שנתיים)", "Junior (up to 2 years)"],
  mid: ["ניסיון בינוני (2–5 שנים)", "Mid-level (2–5 years)"],
  senior: ["סניור", "Senior"], staff: ["סטאף", "Staff"], principal: ["פרינסיפל", "Principal"],
};

/** A permanent entry to every saved learning preference, independent of today's current question. */
export function GoalSummary({ goal, lang, onEdit }: { goal: Goal; lang: "he" | "en"; onEdit: () => void }) {
  const he = lang === "he";
  const id = useId();
  const explore = goal.learning_mode === "explore";
  const roles = explore ? [goalRoleLabel(goal, lang)] : goal.job_type_labels?.length ? goal.job_type_labels : [goalRoleLabel(goal, lang)];
  const career = goal.seniority ? stages[goal.seniority][he ? 0 : 1] : he ? "עדיין לא נבחר שלב" : "No stage chosen yet";
  const date = goal.interview_date ? new Date(`${goal.interview_date}T12:00:00`).toLocaleDateString(he ? "he-IL" : "en-GB", { day: "numeric", month: "long", year: "numeric" }) : he ? "עדיין אין תאריך לראיון" : "No interview date yet";
  return <section className={styles.summary} aria-labelledby={`${id}-title`} data-goal-summary tabIndex={-1}>
    <header className={styles.header}>
      <h2 id={`${id}-title`}><Target size={25} aria-hidden="true" />{he ? "היעד שלכם" : "Your learning goal"}</h2>
      <button type="button" data-member-tour="goal-edit" data-muxi-control="goal-edit" onClick={onEdit} aria-label={he ? "עריכת היעד" : "Edit goal"}><PencilLine size={17} aria-hidden="true" />{he ? "עריכת היעד" : "Edit goal"}</button>
    </header>
    <dl className={styles.fields}>
      <div className={styles.roles}><dt>{he ? explore ? "מסלול הלמידה" : "התפקידים שבחרתם" : explore ? "Learning approach" : "Your chosen roles"}</dt><dd className={styles.roleList}>{roles.map((role) => <span className={styles.role} key={role} dir={proseDirection(role)}><BidiText>{role}</BidiText></span>)}</dd></div>
      <div className={styles.detail}><dt><Clock3 size={17} aria-hidden="true" />{he ? "זמן ביום" : "Daily time"}</dt><dd>{goal.minutes_per_day !== null ? he ? `${goal.minutes_per_day} דקות` : `${goal.minutes_per_day} minutes` : he ? "עדיין לא נבחר זמן" : "No time chosen yet"}</dd></div>
      <div className={styles.detail}><dt><GraduationCap size={18} aria-hidden="true" />{he ? "שלב בקריירה" : "Career stage"}</dt><dd dir={proseDirection(career, he ? "rtl" : "ltr")}><BidiText>{career}</BidiText></dd></div>
      {!explore && <div className={styles.detail}><dt><CalendarDays size={17} aria-hidden="true" />{he ? "תאריך ראיון" : "Interview date"}</dt><dd>{date}</dd></div>}
    </dl>
    <footer className={styles.footer}><p className={styles.note}>{he ? "אפשר לשנות את הבחירות בכל רגע. התוכנית והשאלות המומלצות יתעדכנו בהתאם." : "Change these choices whenever you need. Your plan and recommended questions will update with them."}</p></footer>
  </section>;
}
