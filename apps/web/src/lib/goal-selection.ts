import type { Goal } from "./practice-api";

export const GOAL_JOBS_FILTER = "__goal_jobs__";

/** An explicit plural selection wins over the legacy primary role. */
export function goalJobTypes(goal: Goal | null): string[] {
  if (!goal || goal.learning_mode === "explore") return [];
  return [...new Set(goal.job_types ?? (goal.job_type ? [goal.job_type] : []))];
}

export function defaultGoalJobFilter(goal: Goal | null): string {
  const roles = goalJobTypes(goal);
  return roles.length > 1 ? GOAL_JOBS_FILTER : roles[0] ?? "";
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
