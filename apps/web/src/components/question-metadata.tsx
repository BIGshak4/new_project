import type { ApiLang, QuestionSummary } from "../lib/practice-api";
import { categoryLabel, companyNames, companyReportNote, questionCategory } from "../lib/question-discovery";
import { subjectLabel } from "../lib/practice-ui";

export function ReportedCompanies({ question, lang, note = false }: {
  question: Pick<QuestionSummary, "companies" | "reported_companies">; lang: ApiLang; note?: boolean;
}) {
  const names = companyNames(question);
  return <div className="question-companies">
    <span className="metadata-label">{lang === "he" ? "נשאלה ב:" : "Asked at:"}</span>{" "}
    {names.length ? names.map(name => <bdi className="company-name" key={name}>{name}</bdi>)
      : <span className="metadata-empty">{lang === "he" ? "טרם נוסף דיווח על חברה" : "No company reported yet"}</span>}
    {note && <p className="company-report-note">{companyReportNote(lang)}</p>}
  </div>;
}

export function QuestionMetadata({ question, lang, showCompanies = true }: {
  question: QuestionSummary; lang: ApiLang; showCompanies?: boolean;
}) {
  return <div className="question-metadata">
    <div className="question-taxonomy">
      <span className="discipline-label">{lang === "he" ? "תחום: " : "Discipline: "}{categoryLabel(questionCategory(question), lang)}</span>
      <span><span className="metadata-label">{lang === "he" ? "נושא: " : "Topic: "}</span>{subjectLabel(question.subject, lang)}</span>
      {question.preparation_id && <bdi className="metadata-id">{question.preparation_id}</bdi>}
    </div>
    {!!question.topics?.length && <div className="question-topics" dir="auto">{question.topics.map(topic => <bdi key={topic}>{topic.replaceAll("_", " ")}</bdi>)}</div>}
    {showCompanies && <ReportedCompanies question={question} lang={lang} />}
  </div>;
}
