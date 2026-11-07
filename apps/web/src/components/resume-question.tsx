"use client";

import { ArrowLeft, ArrowRight, History } from "lucide-react";
import { useEffect, useState } from "react";
import { readRecentVisits, type QuestionVisit } from "../lib/question-visit-store";
import { resumeCandidates } from "../lib/resume-question";
import { buildQuestionStates } from "../lib/question-personal-state";
import type { Entry } from "../lib/practice-ui";
import type { ApiLang, PracticeApi, Progress, QuestionSummary } from "../lib/practice-api";
import type { WorkspaceRoute } from "../lib/workspace-route";
import { BidiText } from "./bidi-text";
import styles from "./resume-question.module.css";

type Continuation = { visit: QuestionVisit; title: string };
type Inputs = { api: PracticeApi; userId: string; lang: ApiLang; questions: QuestionSummary[]; entries: Entry[]; recent: Progress["recent"] };

export async function findContinuation({ api, userId, lang, questions, entries, recent }: Inputs, visits: QuestionVisit[], cancelled: () => boolean): Promise<Continuation | null> {
  const candidates = resumeCandidates(visits, recent);
  const byKey = new Map(questions.map(question => [question.key, question]));
  const personalStates = buildQuestionStates(questions, entries);
  let quickTitles: Map<string, string> | undefined;
  for (const visit of candidates) {
    if (cancelled()) return null;
    if (visit.kind === "quick") {
      if (!quickTitles) {
        const [{ quickQuestions }, { readQuickProgress }, progress] = await Promise.all([
          import("../lib/fundamentals"), import("../lib/fundamentals-progress"), api.fundamentalsProgress(userId),
        ]);
        const completed = readQuickProgress(progress);
        quickTitles = new Map(quickQuestions.filter(q => !completed[q.id]).map(q => [q.id, q.title[lang]]));
      }
      const title = quickTitles.get(visit.questionKey);
      if (title) return { visit, title };
      continue;
    }
    const question = byKey.get(visit.questionKey);
    const flags = question && personalStates.get(question.id);
    if (!question || flags?.hidden || flags?.completed) continue;
    if (visit.attemptId) {
      try {
        const attempt = await api.getAttempt(visit.attemptId);
        if (attempt.question.key !== question.key || attempt.submission || attempt.status !== "in_progress" || !attempt.can_submit) continue;
      } catch (error) {
        if ((error as { status?: number }).status === 404) continue;
        throw error;
      }
    }
    return { visit, title: question.title };
  }
  return null;
}

export function ResumeQuestion({ api, userId, lang, questions, entries, recent, ready, navigate }: Inputs & {
  ready: boolean; navigate: (route: WorkspaceRoute) => void;
}) {
  const [result, setResult] = useState<Continuation | null>(null);
  useEffect(() => {
    let generation = 0;
    setResult(null);
    if (!ready) return;
    function refresh() {
      const request = ++generation;
      const cancelled = () => request !== generation;
      void readRecentVisits(userId).catch(() => [])
        .then(visits => findContinuation({ api, userId, lang, questions, entries, recent }, visits, cancelled))
        .then(next => { if (!cancelled()) setResult(next); })
        .catch(() => { if (!cancelled()) setResult(null); });
    }
    refresh();
    window.addEventListener("focus", refresh);
    return () => { generation++; window.removeEventListener("focus", refresh); };
  }, [api, userId, lang, questions, entries, recent, ready]);
  if (!result || !ready) return null;
  const he = lang === "he";
  const Arrow = he ? ArrowLeft : ArrowRight;
  const { visit } = result;
  function resume() {
    if (visit.kind === "quick") navigate({ view: "fundamentals", quick: visit.questionKey });
    else if (visit.attemptId) navigate({ view: "library", attempt: visit.attemptId });
    else navigate({ view: "library", question: visit.questionKey });
  }
  return <section className={styles.resume}>
    <History size={22} aria-hidden="true" />
    <div className={styles.copy}><h2>{he ? "שנמשיך מאיפה שעצרת?" : "Pick up where you left off?"}</h2>
      <p><BidiText>{result.title}</BidiText></p></div>
    <button type="button" onClick={resume}>{he ? "להמשיך בשאלה" : "Continue question"} <Arrow size={17} aria-hidden="true" /></button>
  </section>;
}
