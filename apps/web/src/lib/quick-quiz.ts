import { quickQuestions, quickTopics, type QuickQuestion, type QuickTopic } from "./fundamentals";
import { shuffleQuestions } from "./question-order";

export const QUICK_QUIZ_SIZE = 10;
export type QuickQuizSelection = { topics: QuickTopic[]; questionIds: string[] };
export type QuickQuizRun = QuickQuizSelection & { id: string };

/** Sample the full selected topic pool, independently of search or personal completion. */
export function selectQuickQuiz(topics: readonly QuickTopic[], seed: number, source: readonly QuickQuestion[] = quickQuestions): QuickQuizSelection | null {
  const selected = quickTopics.map(topic => topic.id).filter(topic => topics.includes(topic));
  const unique = new Map(source.filter(question => selected.includes(question.topic)).map(question => [question.id, question]));
  if (unique.size < QUICK_QUIZ_SIZE) return null;
  return { topics: selected, questionIds: shuffleQuestions([...unique.values()], seed, question => question.id).slice(0, QUICK_QUIZ_SIZE).map(question => question.id) };
}

/** Browser history can survive account changes; accept only an owned, intact run. */
export function readQuickQuizRun(value: unknown, userId: string): QuickQuizRun | null {
  if (!value || typeof value !== "object") return null;
  const state = value as Record<string, unknown>;
  if (state.owner !== userId || !state.run || typeof state.run !== "object") return null;
  const run = state.run as Record<string, unknown>;
  if (typeof run.id !== "string" || !run.id || run.id.length > 80 || !Array.isArray(run.topics) || !Array.isArray(run.questionIds)) return null;
  const topics = quickTopics.map(topic => topic.id).filter(topic => (run.topics as unknown[]).includes(topic));
  if (!topics.length || topics.length !== run.topics.length || run.questionIds.length !== QUICK_QUIZ_SIZE || new Set(run.questionIds).size !== QUICK_QUIZ_SIZE) return null;
  const byId = new Map(quickQuestions.map(question => [question.id, question]));
  if (!run.questionIds.every(id => typeof id === "string" && byId.has(id) && topics.includes(byId.get(id)!.topic))) return null;
  return { id: run.id, topics, questionIds: [...run.questionIds] as string[] };
}
