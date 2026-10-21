import type { QuestionSummary } from "./practice-api";

export function hasHumanReviewedSolution(question: Pick<QuestionSummary, "solution_review">) {
  return question.solution_review?.status === "human_reviewed";
}

export function solutionReviewLabel(question: Pick<QuestionSummary, "solution_review">, lang: "he" | "en") {
  return hasHumanReviewedSolution(question)
    ? lang === "he" ? "נבדק בידי אנשים" : "Human reviewed"
    : lang === "he" ? "ממתין לבדיקת הפתרון" : "Solution review pending";
}
