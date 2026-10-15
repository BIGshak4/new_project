"use client";

import { MessageSquare } from "lucide-react";
import { useEffect, useState } from "react";
import type { Lang } from "./auth";
import { Pop, Reveal } from "./ui/motion";
import type { Attempt } from "../lib/practice-api";
import { bandLabel } from "../lib/practice-ui";
import { BidiText } from "./bidi-text";
import { DictationControls } from "./dictation-controls";

/**
 * The follow-up conversation of a deep-mode attempt: every follow-up the engine asked so far,
 * with saved answers or skips, and the one still waiting for an answer.
 */
export function FollowUps({
  attempt,
  lang,
  value,
  onChange,
  onSubmit,
  onSkip,
  disabled,
  busy,
  resend,
  demo = false,
  skipDisabled = false,
}: {
  attempt: Attempt;
  lang: Lang;
  value: string;
  onChange: (text: string) => void;
  onSubmit: () => void;
  onSkip: () => void;
  disabled: boolean;
  busy: boolean;
  /** an earlier send of this same follow-up answer may not have arrived */
  resend: boolean;
  demo?: boolean;
  skipDisabled?: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [confirmSkip, setConfirmSkip] = useState(false);
  const answered = attempt.follow_ups.filter((f) => f.submission || f.skipped);
  const pending = attempt.pending_follow_up;
  useEffect(() => setConfirmSkip(false), [pending?.turn]);
  const cannotSkip =
    disabled || busy || resend || skipDisabled || attempt.status === "evaluating";
  const skipLabel = attempt.next_question
    ? t("דילוג לשאלה הבאה", "Skip to the next question")
    : t("דילוג על שאלת ההמשך", "Skip this follow-up");
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
          "אחרי התשובה הראשית, העוזר בודק את ההבנה בשאלה קצרה אחת לפי מה שראה בתשובה, ואז מציע את השאלה הבאה מהמאגר.",
          "After your main answer, the assistant checks understanding with one short question based on what it saw, then suggests the next question from the bank.",
        )}
      </p>
      <ol className="follow-up-list">
        {answered.map((f) => (
          <li key={f.turn} className="follow-up done">
            <span className="follow-up-kind">{actionLabel(f.action)}</span>
            {f.question && (
              <p className="follow-up-question" dir="auto"><BidiText>{f.question}</BidiText></p>
            )}
            {f.skipped ? (
              <p>
                <span className="badge">{t("דילגתם", "Skipped")}</span>{" "}
                <span className="small muted">
                  {t("ללא ציון או נקודות על שאלת ההמשך.", "No grade or XP for this follow-up.")}
                </span>
              </p>
            ) : f.submission && (
              <>
                <p className="follow-up-answer" dir="auto"><BidiText>{f.submission.answer}</BidiText></p>
                {f.submission.status === "evaluating" && (
                  <p className="small muted" role="status">
                    {t("התשובה נשמרה, המשוב בהכנה…", "Answer saved, preparing feedback…")}
                  </p>
                )}
                {f.submission.status === "failed" && (
                  <p className="small muted">
                    {t(
                      "ההערכה לא הושלמה. אפשר להעריך שוב את אותה תשובה בכפתור למטה.",
                      "Evaluation did not finish. You can retry the same answer with the button below.",
                    )}
                  </p>
                )}
                {f.submission.status === "done" && (
                  <div className="row">
                    <Pop>
                      <span className={`badge band-${f.submission.band?.toLowerCase()}`}>
                        {bandLabel(f.submission.band, lang)}
                      </span>
                    </Pop>
                    {(f.submission.xp_earned ?? 0) > 0 && (
                      <Pop delay={0.25}>
                        <span className="xp-pill small">
                          <bdi dir="ltr">+{f.submission.xp_earned} XP</bdi>
                        </span>
                      </Pop>
                    )}
                    {f.submission.summary && (
                      <span className="small" dir="auto"><BidiText>{f.submission.summary}</BidiText></span>
                    )}
                  </div>
                )}
              </>
            )}
          </li>
        ))}
        {pending && (
          <Reveal as="li" key={pending.turn} className="follow-up open">
            <span className="follow-up-kind">{actionLabel(pending.action)}</span>
            {pending.question_pending ? (
              <p className="follow-up-question muted" role="status">
                {t("כותבים את שאלת ההמשך…", "Writing your follow-up question…")}
              </p>
            ) : (
              <p className="follow-up-question" dir="auto">
                <BidiText>{pending.question}</BidiText>
              </p>
            )}
            <textarea
              value={value}
              onChange={(e) => onChange(e.target.value)}
              disabled={disabled || resend || !!pending.question_pending}
              rows={4}
              dir="auto"
              placeholder={t("התשובה שלכם לשאלת ההמשך…", "Your answer to the follow-up…")}
              aria-label={t("התשובה שלכם לשאלת ההמשך", "Your answer to the follow-up")}
              maxLength={20000}
            />
            <DictationControls
              key={pending.turn}
              value={value}
              onChange={onChange}
              lang={lang}
              disabled={disabled || busy || resend || !!pending.question_pending || confirmSkip}
            />
            <div className="row">
              <button
                type="button"
                className="primary"
                disabled={disabled || !!pending.question_pending || (!resend && !value.trim())}
                onClick={onSubmit}
              >
                {busy
                  ? t("שולחים…", "Sending…")
                  : resend
                    ? t("שליחה חוזרת של אותה תשובה", "Resend the same answer")
                    : t("שליחת התשובה להמשך", "Send follow-up answer")}
              </button>
              {!demo && (
                <button
                  type="button"
                  disabled={cannotSkip}
                  aria-expanded={confirmSkip}
                  onClick={() => {
                    if (cannotSkip) return;
                    if (value.trim()) setConfirmSkip(true);
                    else onSkip();
                  }}
                >{skipLabel}</button>
              )}
            </div>
            {!demo && confirmSkip && (
              <div className="notice" role="group" aria-label={t("אישור דילוג", "Confirm skip")}>
                <p>{t(
                  "כתבתם תשובה שעדיין לא נשלחה. דילוג ימחק את טיוטת שאלת ההמשך, ולא יינתן עליה ציון. להמשיך?",
                  "You have an unsent answer. Skipping discards this follow-up draft and gives it no grade. Continue?",
                )}</p>
                <div className="row">
                  <button type="button" disabled={cannotSkip} onClick={() => setConfirmSkip(false)}>
                    {t("לחזור לתשובה", "Keep answering")}
                  </button>
                  <button type="button" disabled={cannotSkip} onClick={() => {
                    if (!cannotSkip) onSkip();
                  }}>{t("כן, לדלג", "Yes, skip")}</button>
                </div>
              </div>
            )}
          </Reveal>
        )}
      </ol>
    </section>
  );
}
