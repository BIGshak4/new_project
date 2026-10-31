"use client";

import { useRef, useState } from "react";
import { Check, Circle, Eye, EyeOff } from "lucide-react";
import type { Lang } from "./auth";
import type { QuestionSummary } from "../lib/practice-api";
import type { Entry } from "../lib/practice-ui";
import { questionStateIds, saveQuestionState } from "../lib/question-personal-state";

/** Personal organization only: these flags do not change grades or skill estimates. */
export function QuestionStatusControl({
  userId,
  question,
  questions,
  state,
  lang,
  ready,
  onSaved,
}: {
  userId: string;
  question: QuestionSummary;
  questions: QuestionSummary[];
  state: { completed: boolean; hidden: boolean };
  lang: Lang;
  ready: boolean;
  onSaved: (entries: Entry[]) => void;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const saving = useRef(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save(patch: { completed?: boolean; hidden?: boolean }) {
    if (!ready || saving.current) return;
    saving.current = true;
    setBusy(true);
    setError("");
    try {
      const saved = await saveQuestionState(userId, questionStateIds(question, questions), patch);
      onSaved(saved);
    } catch {
      setError(t("המצב לא נשמר. נסו שוב.", "Status was not saved. Try again."));
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }

  return (
    <div className="question-status" role="group" aria-label={`${t("מצב אישי", "Personal status")}: ${question.title}`} aria-busy={busy}>
      <div className="question-status-actions">
        <button
          type="button"
          className={`question-completion${ready && state.completed ? " is-completed" : ""}`}
          disabled={!ready || busy}
          aria-pressed={ready && state.completed}
          aria-label={`${state.completed ? t("סימון כלא בוצעה", "Mark as not done") : t("סימון כבוצעה", "Mark as done")}: ${question.title}`}
          onClick={() => void save({ completed: !state.completed })}
        >
          {ready && state.completed ? <Check size={16} aria-hidden="true" /> : <Circle size={16} aria-hidden="true" />}
          {ready ? state.completed ? t("בוצעה", "Done") : t("לא בוצעה", "Not done") : t("טוענים מצב…", "Loading status…")}
        </button>
        <button
          type="button"
          className="question-visibility"
          disabled={!ready || busy}
          aria-label={`${state.hidden ? t("החזרת שאלה למאגר", "Restore question") : t("הסתרת שאלה", "Hide question")}: ${question.title}`}
          onClick={() => void save({ hidden: !state.hidden })}
        >
          {state.hidden ? <Eye size={16} aria-hidden="true" /> : <EyeOff size={16} aria-hidden="true" />}
          {state.hidden ? t("החזרה למאגר", "Restore") : t("הסתר", "Hide")}
        </button>
      </div>
      {ready && state.hidden && <span className="small muted question-hidden-label">{t("מוסתרת", "Hidden")}</span>}
      {busy && <span className="small muted" role="status">{t("שומרים…", "Saving…")}</span>}
      {error && <span className="question-status-error small" role="alert">{error}</span>}
    </div>
  );
}
