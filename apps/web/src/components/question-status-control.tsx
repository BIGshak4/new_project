"use client";

import { useEffect, useRef, useState } from "react";
import { Bookmark, Eye, EyeOff } from "lucide-react";
import type { Lang } from "./auth";
import type { QuestionSummary } from "../lib/practice-api";
import type { Entry } from "../lib/practice-ui";
import { questionStateIds, saveQuestionState } from "../lib/question-personal-state";
import { saveQuestionBookmark } from "../lib/question-bookmark";

/** Personal organization only: these flags do not change grades or skill estimates. */
export function QuestionStatusControl({
  userId,
  question,
  questions,
  state,
  lang,
  ready,
  onSaved,
  bookmark,
}: {
  userId: string;
  question: QuestionSummary;
  questions: QuestionSummary[];
  state: { completed: boolean; hidden: boolean };
  lang: Lang;
  ready: boolean;
  onSaved: (entries: Entry[]) => void;
  bookmark?: { saved: boolean; onSaved: (entry: Entry) => void };
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const saving = useRef(false);
  const requestVersion = useRef(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<"status" | "bookmark" | null>(null);
  useEffect(() => () => { requestVersion.current++; }, [userId, question.id]);

  async function save(patch: { completed?: boolean; hidden?: boolean; bookmarked?: boolean }) {
    if (!ready || saving.current) return;
    saving.current = true;
    const request = ++requestVersion.current;
    setBusy(true);
    setError(null);
    try {
      if (typeof patch.bookmarked === "boolean") {
        const saved = await saveQuestionBookmark(userId, question.id, patch.bookmarked);
        if (request === requestVersion.current) bookmark?.onSaved(saved);
      } else {
        const saved = await saveQuestionState(userId, questionStateIds(question, questions), patch);
        if (request === requestVersion.current) onSaved(saved);
      }
    } catch {
      if (request === requestVersion.current) setError(typeof patch.bookmarked === "boolean" ? "bookmark" : "status");
    } finally {
      if (request === requestVersion.current) {
        saving.current = false;
        setBusy(false);
      }
    }
  }

  return (
    <div className="question-status" role="group" aria-label={`${t("מצב אישי", "Personal status")}: ${question.title}`} aria-busy={busy}>
      <div className="question-status-actions">
        <label
          className={`question-completion${ready && state.completed ? " is-completed" : ""}`}
        >
          <input
            type="checkbox"
            checked={ready && state.completed}
            disabled={!ready || busy}
            aria-label={`${t("בוצעה", "Done")}: ${question.title}`}
            onChange={(event) => void save({ completed: event.target.checked })}
          />
          <span>{t("בוצעה", "Done")}</span>
        </label>
        {bookmark && <button
          type="button"
          className="question-bookmark"
          disabled={!ready || busy}
          aria-pressed={ready && bookmark.saved}
          aria-label={`${bookmark.saved ? t("ביטול שמירת שאלה", "Unsave question") : t("שמירת שאלה", "Save question")}: ${question.title}`}
          onClick={() => void save({ bookmarked: !bookmark.saved })}
        >
          <Bookmark size={16} fill={ready && bookmark.saved ? "currentColor" : "none"} aria-hidden="true" />
          {bookmark.saved ? t("ביטול שמירה", "Unsave") : t("שמירה", "Save")}
        </button>}
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
      {error && <span className="question-status-error small" role="alert">{error === "bookmark"
        ? t("השמירה לא התעדכנה. נסו שוב.", "Bookmark was not updated. Try again.")
        : t("המצב לא נשמר. נסו שוב.", "Status was not saved. Try again.")}</span>}
    </div>
  );
}
