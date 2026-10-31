import type { Lang } from "./auth";
import { executionStatusLabel, executionValue, type CodeExecutionResult } from "../lib/code-execution";

export function ExecutionResultView({ result, lang, stale = false }: {
  result: CodeExecutionResult;
  lang: Lang;
  stale?: boolean;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const hasTotals = typeof result.test_count === "number" && result.test_count > 0 && typeof result.passed_count === "number";
  const output = [
    [t("פלט התוכנית", "Program output"), result.stdout],
    [t("שגיאות הרצה", "Runtime diagnostics"), result.stderr],
    [t("פלט המהדר", "Compiler diagnostics"), result.compile_output],
  ].filter((row) => !!row[1]);
  return (
    <div className={`code-execution-result ${stale ? "code-execution-stale" : ""}`} data-execution-status={result.status}>
      {stale && <p className="code-execution-stale-notice">{t("הקוד או הקלט השתנו. התוצאה הזאת שייכת לגרסה הקודמת; הריצו שוב.", "The source or input changed. This result belongs to the previous version; run it again.")}</p>}
      <p className="code-execution-result-title" role="status">
        <strong>{executionStatusLabel(result, lang)}</strong>
        <span className="muted small"><bdi>{new Intl.NumberFormat(lang === "he" ? "he-IL" : "en").format(result.runtime_ms)}</bdi> {t("מ״ש", "ms")}</span>
      </p>
      <ul className="code-execution-phases" aria-label={t("שלבי הבדיקה", "Execution stages")}>
        {result.compiled !== null && <li>{result.compiled ? t("קומפילציה: הצליחה", "Compilation: passed") : t("קומפילציה: נכשלה", "Compilation: failed")}</li>}
        <li>{result.executed ? t("הרצה: בוצעה", "Execution: ran") : t("הרצה: לא בוצעה", "Execution: did not run")}</li>
        <li>{result.passed === null ? t("נכונות: לא נבדקה", "Correctness: not assessed") : result.passed ? t("בדיקות השאלה: עברו", "Question tests: passed") : t("בדיקות השאלה: נכשלו", "Question tests: failed")}</li>
      </ul>
      {hasTotals && <p className="small"><bdi dir="ltr">{result.passed_count}/{result.test_count}</bdi> {t("מהבדיקות שהוגדרו עברו", "defined tests passed")}</p>}
      {result.detail && <p className="small" dir="auto">{result.detail}</p>}
      {result.passed === true && <p className="small muted">{t("מעבר הבדיקות אינו מוכיח נכונות לכל קלט ואינו בודק בהכרח יעילות או מינימליות.", "Passing these tests does not prove correctness for every input or necessarily assess efficiency or minimality.")}</p>}
      {output.map(([label, value]) => <details key={label} open>
        <summary>{label}</summary>
        <pre tabIndex={0} dir="ltr" aria-label={label}>{value}</pre>
      </details>)}
      {!output.length && result.executed && <p className="small muted">{t("התוכנית לא כתבה פלט למסוף.", "The program did not write to the console.")}</p>}
      {!!result.cases.length && <details>
        <summary>{t("דוגמאות מתוצאות הבדיקה", "Sample test results")}</summary>
        <ol className="code-execution-cases">
          {result.cases.map((item, index) => <li key={`${item.index}-${index}`}>
            <strong>{t("מקרה", "Case")} {item.index > 0 ? item.index : index + 1}: {item.passed ? t("עבר", "passed") : t("נכשל", "failed")}</strong>
            {item.input !== undefined && <div>{t("קלט", "Input")}<pre tabIndex={0} dir="ltr">{executionValue(item.input)}</pre></div>}
            {item.expected !== undefined && <div>{t("פלט צפוי", "Expected")}<pre tabIndex={0} dir="ltr">{executionValue(item.expected)}</pre></div>}
            {item.actual !== undefined && <div>{t("פלט שהתקבל", "Actual")}<pre tabIndex={0} dir="ltr">{executionValue(item.actual)}</pre></div>}
          </li>)}
        </ol>
      </details>}
    </div>
  );
}
