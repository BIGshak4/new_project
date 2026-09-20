"use client";

import { MessageSquare } from "lucide-react";
import type { Lang } from "./auth";
import type { Attempt } from "../lib/practice-api";
import { bandLabel } from "../lib/practice-ui";

/**
 * The follow-up conversation of a deep-mode attempt: every follow-up the engine asked so far,
 * with the answer given and the band it earned, and the one still waiting for an answer.
 */
export function FollowUps({
  attempt,
  lang,
  value,
  onChange,
  onSubmit,
  disabled,
  busy,
  resend,
}: {
  attempt: Attempt;
  lang: Lang;
  value: string;
  onChange: (text: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  busy: boolean;
  /** an earlier send of this same follow-up answer may not have arrived */
  resend: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const answered = attempt.follow_ups.filter((f) => f.submission);
  const pending = attempt.pending_follow_up;
  if (!answered.length && !pending) return null;
  const actionLabel = (action: string) =>
    action === "escalate"
      ? t("שאלה מאתגרת יותר", "A harder question")
      : action === "step_back"
        ? t("צעד אחורה", "A step back")
        : action === "scaffold"
          ? t("פירוק לשלבים", "Broken into steps")
          : t("שאלת המשך", "Follow-up");
  return (
    <section className="follow-ups" aria-label={t("שאלות המשך", "Follow-up questions")}>
      <h3>
        <MessageSquare size={18} aria-hidden="true" /> {t("שאלות המשך", "Follow-up questions")}
      </h3>
      <p className="small muted">
        {t(
          "אחרי התשובה הראשית, העוזר בודק את ההבנה בשאלה קצרה נוספת, לפי מה שראה בתשובה.",
          "After your main answer, the assistant checks understanding with a short extra question based on what it saw.",
        )}
      </p>
      <ol className="follow-up-list">
        {answered.map((f) => (
          <li key={f.turn} className="follow-up done">
            <span className="follow-up-kind">{actionLabel(f.action)}</span>
            <p className="follow-up-question" dir="auto">
              {f.question}
            </p>
            <p className="follow-up-answer" dir="auto">
              {f.submission!.answer}
            </p>
            {f.submission!.status === "done" && (
              <div className="row">
                <span className={`badge band-${f.submission!.band?.toLowerCase()}`}>
                  {bandLabel(f.submission!.band, lang)}
                </span>
                {f.submission!.summary && (
                  <span className="small" dir="auto">
                    {f.submission!.summary}
                  </span>
                )}
              </div>
            )}
          </li>
        ))}
        {pending && (
          <li key={pending.turn} className="follow-up open">
            <span className="follow-up-kind">{actionLabel(pending.action)}</span>
            <p className="follow-up-question" dir="auto">
              {pending.question}
            </p>
            <textarea
              value={value}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled}
              rows={4}
              dir="auto"
              placeholder={t("התשובה שלכם לשאלת ההמשך…", "Your answer to the follow-up…")}
            />
            <button
              type="button"
              className="primary"
              disabled={disabled || (!resend && !value.trim())}
              onClick={onSubmit}
            >
              {busy
                ? t("שולחים…", "Sending…")
                : resend
                  ? t("שליחה חוזרת של אותה תשובה", "Resend the same answer")
                  : t("שליחת התשובה להמשך", "Send follow-up answer")}
            </button>
          </li>
        )}
      </ol>
    </section>
  );
}
