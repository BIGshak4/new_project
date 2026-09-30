"use client";

import { useState } from "react";
import * as RadixPopover from "@radix-ui/react-popover";
import { Flag } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, PracticeApiError } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { toast } from "./toaster";

type Reason = "unclear" | "wrong" | "other";

/**
 * "This question is not clear": a quiet flag on the question sheet and in the interview room. Three reasons and an
 * optional line, stored per question for the review queue; a second press by the same person updates the note.
 * Nothing about grading changes, and other users never see it.
 */
export function QuestionReport({ api, questionKey, lang, context }: { api: PracticeApi; questionKey: string; lang: Lang; context: "practice" | "interview" | "library" }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<Reason>("unclear");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const reasons: [Reason, string][] = [
    ["unclear", t("לא הבנתי מה נשאל", "I did not understand what is asked")],
    ["wrong", t("נראה לי שיש טעות בשאלה", "Something in the question looks wrong")],
    ["other", t("משהו אחר", "Something else")],
  ];
  async function send() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await api.reportQuestion(questionKey, { reason, note: note.trim() || undefined, language: lang, context });
      setOpen(false);
      setNote("");
      toast.success(t("תודה. נבדוק את השאלה ונתקן.", "Thank you. We will look at the question and fix it."));
    } catch (e) {
      const code = (e as PracticeApiError).code;
      setError(code === "temporarily_unavailable" ? t("הדיווח ייפתח בקרוב.", "Reporting opens soon.") : apiMessage(e, lang));
    } finally {
      setBusy(false);
    }
  }
  return (
    <RadixPopover.Root open={open} onOpenChange={setOpen}>
      <RadixPopover.Trigger asChild>
        <button type="button" className="text-button report-trigger">
          <Flag size={14} aria-hidden="true" /> {t("השאלה לא ברורה?", "Question unclear?")}
        </button>
      </RadixPopover.Trigger>
      <RadixPopover.Portal>
        <RadixPopover.Content className="ui-popover report-popover" side="bottom" align="start" sideOffset={8} collisionPadding={12}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <p className="report-title">{t("מה לא עבד בשאלה הזאת?", "What did not work in this question?")}</p>
            <div className="report-reasons" role="radiogroup" aria-label={t("סיבה", "Reason")}>
              {reasons.map(([value, label]) => (
                <label key={value} className={`report-reason ${reason === value ? "on" : ""}`}>
                  <input type="radio" name="reason" value={value} checked={reason === value} onChange={() => setReason(value)} />
                  {label}
                </label>
              ))}
            </div>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={500}
              rows={2}
              dir="auto"
              placeholder={t("במילה או שתיים: מה היה לא ברור?", "In a word or two: what was unclear?")}
              aria-label={t("הערה", "Note")}
            />
            {error && (
              <p className="small" role="alert">
                {error}
              </p>
            )}
            <div className="row report-actions">
              <button type="submit" className="primary" disabled={busy}>
                {busy ? t("שולחים…", "Sending…") : t("שליחה", "Send")}
              </button>
              <RadixPopover.Close asChild>
                <button type="button" className="text-button">
                  {t("ביטול", "Cancel")}
                </button>
              </RadixPopover.Close>
            </div>
          </form>
          <RadixPopover.Arrow className="ui-popover-arrow" width={16} height={8} />
        </RadixPopover.Content>
      </RadixPopover.Portal>
    </RadixPopover.Root>
  );
}
