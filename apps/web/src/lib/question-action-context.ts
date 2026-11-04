import { supportOpenRequest, type SupportLanguage, type SupportOpenDetail } from "./support-report";

export type QuestionActionContext = "practice" | "interview" | "library" | "quick" | "quiz";
export type QuestionActionTarget = { questionKey: string; questionTitle?: string; context: QuestionActionContext; variant?: number | null };
export type QuestionSupportAction = "problem" | "unclear" | "company";

/** Select only public question metadata. In particular, quiz solutions and a learner's answer are never copied. */
export function questionSupportRequest(target: QuestionActionTarget, action: QuestionSupportAction, lang: SupportLanguage, company?: string): SupportOpenDetail {
  const he = lang === "he";
  const label = action === "problem" ? (he ? "דיווח בעיה בשאלה" : "Question issue")
    : action === "unclear" ? (he ? "שאלה לא ברורה" : "Unclear question")
    : (he ? "ראיתי את השאלה בחברה" : "Question seen at a company");
  const title = target.questionTitle?.trim().slice(0, 240);
  const kind = target.context === "quick" ? (he ? "שאלה קצרה" : "Short question")
    : target.context === "quiz" ? (he ? "שאלה אמריקאית" : "Multiple-choice question")
    : target.context === "interview" ? (he ? "ראיון מדומה" : "Mock interview")
    : (he ? "שאלת תרגול" : "Practice question");
  const lines = [
    title && `${he ? "שאלה" : "Question"}: ${title}`,
    `${he ? "מזהה שאלה" : "Question ID"}: ${target.questionKey}`,
    `${he ? "סוג" : "Type"}: ${kind}`,
    Number.isSafeInteger(target.variant) && Number(target.variant) >= 0 ? `${he ? "גרסה" : "Variant"}: ${target.variant}` : null,
    "",
    action === "company" ? `${he ? "ראיתי את השאלה בחברה" : "I saw this question at"}: ${company?.trim().slice(0, 80) ?? ""}`
      : action === "unclear" ? (he ? "מה לא ברור בשאלה: " : "What is unclear about the question: ")
      : (he ? "תיאור הבעיה: " : "Description of the issue: "),
  ];
  return supportOpenRequest({ category: "question", questionKey: target.questionKey, subject: `${label}${title ? `: ${title}` : ""}`, description: lines.filter(line => line !== null && line !== undefined).join("\n") });
}
