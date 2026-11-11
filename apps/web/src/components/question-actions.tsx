"use client";

import { useId, useRef, useState } from "react";
import { Building2, ChevronDown, CircleHelp, Flag, X } from "lucide-react";
import type { Lang } from "./auth";
import type { CompanyTag, PracticeApi, PracticeApiError, QuestionSummary } from "../lib/practice-api";
import { apiMessage } from "../lib/practice-ui";
import { proseDirection } from "../lib/bidi-segments";
import { openSupportReport } from "../lib/support-report";
import { questionSupportRequest, type QuestionActionTarget, type QuestionSupportAction } from "../lib/question-action-context";
import { BidiText } from "./bidi-text";
import { QuestionReport } from "./question-report";
import { ReportedCompanies } from "./question-metadata";
import { toast } from "./toaster";
import styles from "./question-actions.module.css";

type QuestionActionsProps = QuestionActionTarget & {
  lang: Lang;
  /** Only long-bank questions use these endpoints. Short and quiz questions go to the support inbox. */
  api?: Pick<PracticeApi, "addSighting" | "reportQuestion">;
  companies?: CompanyTag[];
  reportedCompanies?: QuestionSummary["reported_companies"];
};

/** Stable placement for all three actions; opening a report leaves the answer workspace mounted. */
export function QuestionActions(props: QuestionActionsProps) {
  return <QuestionActionsForQuestion key={`${props.context}:${props.questionKey}:${props.variant ?? ""}`} {...props} />;
}

function QuestionActionsForQuestion({ lang, api, companies, reportedCompanies, ...target }: QuestionActionsProps) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [companyOpen, setCompanyOpen] = useState(false);
  const [company, setCompany] = useState("");
  const [savedTags, setSavedTags] = useState<CompanyTag[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const working = useRef(false);
  const companyTrigger = useRef<HTMLButtonElement>(null);
  const id = useId();
  const bankContext = target.context === "practice" || target.context === "interview" || target.context === "library" ? target.context : null;
  const directApi = bankContext ? api : undefined;

  function report(action: QuestionSupportAction) {
    const request = questionSupportRequest(target, action, lang, company);
    openSupportReport(request.category, request);
  }

  async function saveCompany() {
    const name = company.trim();
    if (!name || working.current) return;
    if (!directApi) { report("company"); return; }
    working.current = true; setBusy(true); setError("");
    try {
      const result = await directApi.addSighting(target.questionKey, name);
      setSavedTags(result.companies); setCompany(""); setCompanyOpen(false);
      companyTrigger.current?.focus();
      toast.success(t("תודה! החברה נוספה לדיווחים על השאלה.", "Thanks! The company was added to this question's reports."));
    } catch (failure) {
      setError((failure as PracticeApiError).code === "temporarily_unavailable"
        ? t("לא ניתן לשמור את החברה כרגע. נסו שוב בעוד רגע.", "The company could not be saved right now. Please try again shortly.")
        : apiMessage(failure, lang));
    } finally { working.current = false; setBusy(false); }
  }

  return <div className={styles.root} dir={lang === "he" ? "rtl" : "ltr"} lang={lang}>
    <section className={styles.frame} data-member-tour="question-reports" aria-label={t("דיווחים על השאלה", "Question reports")}>
      <div className={styles.toolbar}>
        <strong className={styles.label}>{t("על השאלה הזאת", "About this question")}</strong>
        <div className={styles.actions}>
          <button type="button" className={styles.action} onClick={() => report("problem")} aria-haspopup="dialog"><Flag size={17} aria-hidden="true" />{t("דיווח בעיה", "Report a problem")}</button>
          {directApi && bankContext ? <QuestionReport api={directApi} questionKey={target.questionKey} context={bankContext} lang={lang} triggerClassName={styles.action} />
            : <button type="button" className={styles.action} onClick={() => report("unclear")} aria-haspopup="dialog"><CircleHelp size={17} aria-hidden="true" />{t("שאלה לא ברורה", "Unclear question")}</button>}
          <button ref={companyTrigger} type="button" className={styles.action} aria-expanded={companyOpen} aria-controls={`${id}-company`} onClick={() => setCompanyOpen(!companyOpen)}>
            <Building2 size={17} aria-hidden="true" />{t("ראיתי בחברה", "Seen at a company")}<ChevronDown size={15} className={companyOpen ? styles.expanded : undefined} aria-hidden="true" />
          </button>
        </div>
      </div>
      {companyOpen && <form id={`${id}-company`} className={styles.companyForm} onSubmit={event => { event.preventDefault(); void saveCompany(); }}>
        <label htmlFor={`${id}-name`}>{t("באיזו חברה פגשתם את השאלה?", "At which company did you see this question?")}</label>
        <div className={styles.companyFields}>
          <input id={`${id}-name`} value={company} onChange={event => setCompany(event.target.value)} maxLength={80} placeholder={t("למשל Intel", "For example, Intel")} dir="auto" disabled={busy} autoComplete="organization" required />
          <button type="submit" className="primary" disabled={busy || !company.trim()}>{busy ? t("שומרים…", "Saving…") : directApi ? t("הוספת החברה", "Add company") : t("המשך לדיווח", "Continue to report")}</button>
          <button type="button" className={styles.close} disabled={busy} onClick={() => { setCompanyOpen(false); companyTrigger.current?.focus(); }}><X size={16} aria-hidden="true" />{t("סגירה", "Close")}</button>
        </div>
        {!directApi && <p className={styles.help}>{t("שם החברה ופרטי השאלה ייכללו בפנייה לצוות. אפשר לבדוק אותם לפני השליחה.", "The company and question details will be included in your report to the team. You can review them before sending.")}</p>}
        {error && <p className={styles.error} role="alert" dir={proseDirection(error)}><BidiText>{error}</BidiText></p>}
      </form>}
    </section>
    {(companies !== undefined || reportedCompanies !== undefined || savedTags !== null) && <div className={styles.provenance}>
      <ReportedCompanies question={{ companies: savedTags ?? companies, reported_companies: reportedCompanies }} lang={lang} />
      <p>{t("לפי דיווחי מתרגלים ומקורות הכנה, ללא אישור רשמי של החברות. הנוסח עשוי להשתנות בין ראיונות.", "Based on learner reports and preparation sources, without official company confirmation. Wording may vary between interviews.")}</p>
    </div>}
  </div>;
}
