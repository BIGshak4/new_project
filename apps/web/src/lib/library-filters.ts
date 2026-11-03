import type { QuestionSummary } from "./practice-api";
import { companyNames, matchesQuestion, questionCategory } from "./question-discovery";
import type { QuestionPersonalState } from "./question-personal-state";

export type LibraryStatus = "not_done" | "done" | "hidden";
export type LibraryFilters = { query: string; statuses: LibraryStatus[]; categories: string[]; subjects: string[]; jobs: string[]; companies: string[] };
export const emptyLibraryFilters = (): LibraryFilters => ({ query: "", statuses: [], categories: [], subjects: [], jobs: [], companies: [] });
export function matchesLibraryStatuses(state: QuestionPersonalState, statuses: LibraryStatus[]): boolean {
  return !statuses.length || statuses.some(status => status === "hidden" ? state.hidden : !state.hidden && (status === "done" ? state.completed : !state.completed));
}
/** Choices within a field form a union; different fields and free-text search intersect. */
export function matchesLibraryFilters(question: QuestionSummary, state: QuestionPersonalState, filters: LibraryFilters, subjectLabels: string[] = []): boolean {
  return matchesLibraryStatuses(state, filters.statuses) &&
    (!filters.categories.length || filters.categories.includes(questionCategory(question))) &&
    (!filters.subjects.length || filters.subjects.includes(question.subject)) &&
    (!filters.jobs.length || filters.jobs.some(job => question.job_types?.includes(job))) &&
    (!filters.companies.length || companyNames(question).some(company => filters.companies.includes(company))) &&
    matchesQuestion(question, filters.query, subjectLabels);
}
