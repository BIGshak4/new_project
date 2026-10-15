import type { ApiLang, QuestionSummary } from "../lib/practice-api";
import { categoryLabel, companyNames, companyReportNote, questionCategory } from "../lib/question-discovery";
import { subjectLabel } from "../lib/practice-ui";

export function ReportedCompanies({ question, lang, note = false, compact = false }: {
  question: Pick<QuestionSummary, "companies" | "reported_companies">; lang: ApiLang; note?: boolean; compact?: boolean;
}) {
  const names = companyNames(question);
  const shown = compact ? names.slice(0, 3) : names;
  const remaining = names.length - shown.length;
  return <div className="question-companies">
    <span className="metadata-label">{lang === "he" ? "נשאלה ב:" : "Asked at:"}</span>{" "}
    {names.length ? shown.map(name => <bdi className="company-name" key={name}>{name}</bdi>)
      : <span className="metadata-empty">{lang === "he" ? "טרם נוסף דיווח על חברה" : "No company reported yet"}</span>}
    {remaining > 0 && <span className="company-more">{lang === "he" ? `ועוד ${remaining}` : `+${remaining} more`}</span>}
    {note && <p className="company-report-note">{companyReportNote(lang)}</p>}
  </div>;
}

export function QuestionMetadata({ question, lang, showCompanies = true, compact = false }: {
  question: QuestionSummary; lang: ApiLang; showCompanies?: boolean; compact?: boolean;
}) {
  return <div className={`question-metadata${compact ? " is-compact" : ""}`}>
    <div className="question-taxonomy">
      <span className="discipline-label">{lang === "he" ? "תחום: " : "Discipline: "}{categoryLabel(questionCategory(question), lang)}</span>
      {!compact && <span><span className="metadata-label">{lang === "he" ? "נושא: " : "Topic: "}</span><bdi dir="auto">{subjectLabel(question.subject, lang)}</bdi></span>}
      {question.preparation_id && <bdi className="metadata-id">{question.preparation_id}</bdi>}
    </div>
    {!compact && !!question.topics?.length && <div className="question-topics">{[...new Set(question.topics)].map(topic => <bdi dir="auto" key={topic}>{topic.replaceAll("_", " ")}</bdi>)}</div>}
    {showCompanies && <ReportedCompanies question={question} lang={lang} compact={compact} />}
  </div>;
}
