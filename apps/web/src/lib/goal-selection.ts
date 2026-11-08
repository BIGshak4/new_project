import type { Goal } from "./practice-api";

/** A saved tour goal also updates a workspace mounted beneath the tour. */
export const ACCOUNT_GOAL_SAVED = "jobrun:account-goal-saved";
export type AccountGoalSaved = { userId: string; goal: Goal };

/** An explicit plural selection wins over the legacy primary role. */
export function goalJobTypes(goal: Goal | null): string[] {
  if (!goal || goal.learning_mode === "explore") return [];
  return [...new Set(goal.job_types ?? (goal.job_type ? [goal.job_type] : []))];
}

/** The order of role chips does not change the meaning of the saved program. */
export function goalProgramKey(goal: Goal | null): string {
  return JSON.stringify([
    goal?.learning_mode ?? "targeted", goalJobTypes(goal).sort(),
    goal?.seniority ?? null, goal?.minutes_per_day ?? null, goal?.interview_date ?? null,
  ]);
}

export function goalRoleLabel(goal: Goal | null, lang: "he" | "en"): string {
  if (goal?.learning_mode === "explore") return lang === "he" ? "למידה ללא יעד מוגדר" : "Learning without a fixed goal";
  const labels = goal?.job_type_labels?.length ? goal.job_type_labels : goal?.job_type_label ? [goal.job_type_label] : [];
  return labels.join(" · ") || (lang === "he" ? "עדיין לא נבחרו תפקידים" : "No roles chosen yet");
}
