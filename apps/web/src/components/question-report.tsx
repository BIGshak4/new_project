"use client";

import { useId, useState } from "react";
import { BidiText } from "./bidi-text";
import { proseDirection } from "../lib/bidi-segments";
import * as RadixPopover from "@radix-ui/react-popover";
import { CircleHelp } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, PracticeApiError } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { toast } from "./toaster";

type Reason = "unclear" | "wrong" | "other";

/**
 * A question-specific report from the question sheet and interview room. Three reasons and an
 * optional line, stored per question for the review queue; a second press by the same person updates the note.
 * Nothing about grading changes, and other users never see it.
 */
export function QuestionReport({ api, questionKey, lang, context, triggerClassName }: { api: Pick<PracticeApi, "reportQuestion">; questionKey: string; lang: Lang; context: "practice" | "interview" | "library"; triggerClassName?: string }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<Reason>("unclear");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const id = useId();
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
      toast.success(t("תודה, הדיווח נשלח לבדיקת הצוות.", "Thank you. Your report was sent to the team for review."));
    } catch (e) {
      const code = (e as PracticeApiError).code;
      setError(code === "temporarily_unavailable" ? t("לא ניתן לשלוח את הדיווח כרגע. נסו שוב בעוד רגע.", "The report could not be sent right now. Please try again shortly.") : apiMessage(e, lang));
    } finally {
      setBusy(false);
    }
  }
  return (
    <RadixPopover.Root open={open} onOpenChange={setOpen}>
      <RadixPopover.Trigger asChild>
        <button type="button" className={triggerClassName ?? "text-button report-trigger"}>
          <CircleHelp size={17} aria-hidden="true" /> {t("שאלה לא ברורה", "Unclear question")}
        </button>
      </RadixPopover.Trigger>
      <RadixPopover.Portal>
        <RadixPopover.Content className="ui-popover report-popover" side="bottom" align="start" sideOffset={8} collisionPadding={12} dir={lang === "he" ? "rtl" : "ltr"} lang={lang} aria-labelledby={`${id}-title`}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <p className="report-title" id={`${id}-title`}>{t("מה לא ברור בשאלה?", "What is unclear about the question?")}</p>
            <div className="report-reasons" role="radiogroup" aria-label={t("סיבה", "Reason")}>
              {reasons.map(([value, label]) => (
                <label key={value} className={`report-reason ${reason === value ? "on" : ""}`}>
                  <input type="radio" name={`${id}-reason`} value={value} checked={reason === value} onChange={() => setReason(value)} disabled={busy} />
                  {label}
                </label>
              ))}
            </div>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={500}
              rows={2}
              disabled={busy}
              dir="auto"
              placeholder={t("במילה או שתיים: מה היה לא ברור?", "In a word or two: what was unclear?")}
              aria-label={t("הערה", "Note")}
            />
            {error && (
              <p className="small" role="alert" dir={proseDirection(error)}>
                <BidiText>{error}</BidiText>
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
