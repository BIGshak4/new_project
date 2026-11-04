"use client";
import dynamic from "next/dynamic";
import { useId, useState } from "react";
import { ChevronDown, ChevronUp, CodeXml, MessageSquareText } from "lucide-react";
import type { Lang } from "./auth";
import { DictationControls } from "./dictation-controls";
import { dictationExplanationLimit } from "../lib/speech-dictation";
import type { CodeExecutionContext } from "./code-execution-panel";
import {
  answerLanguages,
  defaultAnswerLanguage,
  formatTechnicalAnswer,
  parseTechnicalAnswer,
  type AnswerLanguage,
} from "../lib/technical-answer";

const CodeEditor = dynamic(() => import("./technical-code-editor"), {
  ssr: false,
});
const CodeExecutionPanel = dynamic(() => import("./code-execution-panel").then((module) => module.CodeExecutionPanel), { ssr: false });
export function AnswerEditor({
  value,
  onChange,
  lang,
  disabled,
  codeLanguage,
  starterCode,
  initiallyShowCode,
  execution,
}: {
  value: string;
  onChange: (value: string) => void;
  lang: Lang;
  disabled: boolean;
  codeLanguage: string | null;
  starterCode: string | null;
  initiallyShowCode?: boolean;
  execution?: CodeExecutionContext;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const id = useId();
  const parts = parseTechnicalAnswer(value);
  const [chosenLanguage, setLanguage] = useState<AnswerLanguage>(
    parts.language ?? defaultAnswerLanguage(codeLanguage),
  );
  const [showExplanation, setShowExplanation] = useState(false);
  const [showCode, setShowCode] = useState(initiallyShowCode ?? false);
  // Once opened, keep the editor mounted so folding it preserves undo and cursor state.
  const [codeMounted, setCodeMounted] = useState(initiallyShowCode ?? false);
  const language = parts.language ?? chosenLanguage;
  const update = (explanation: string, code: string, nextLanguage = language) =>
    onChange(formatTechnicalAnswer(explanation, code, nextLanguage));
  return (
    <div className="answer-editor">
      <div className="visual-answer-actions" role="group" aria-label={t("כלי כתיבת תשובה", "Answer writing tools")}>
        <button
          type="button"
          data-muxi-control={showExplanation ? undefined : "explanation-open"}
          disabled={disabled}
          aria-expanded={showExplanation}
          aria-controls={`${id}-explanation`}
          onClick={() => setShowExplanation((open) => !open)}
        >
          <MessageSquareText size={18} aria-hidden="true" />
          {showExplanation
            ? t("סגירת ההסבר", "Close explanation")
            : t("כתיבת הסבר לפתרון", "Write an explanation")}
          {!showExplanation && parts.explanation.trim() && <span className="small muted">{t("יש תוכן", "Has content")}</span>}
          {showExplanation ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
        </button>
        <button
          type="button"
          data-muxi-control={showCode ? undefined : "code-open"}
          disabled={disabled}
          aria-expanded={showCode}
          aria-controls={`${id}-code`}
          onClick={() => {
            setCodeMounted(true);
            setShowCode((open) => !open);
          }}
        >
          <CodeXml size={18} aria-hidden="true" />
          {showCode
            ? t("סגירת עורך הקוד והנוסחאות", "Close code and formulas")
            : t("קוד, נוסחה או טבלת אמת", "Code, formula, or truth table")}
          {!showCode && parts.code.trim() && <span className="small muted">{t("יש תוכן", "Has content")}</span>}
          {showCode ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
        </button>
      </div>
      <div id={`${id}-explanation`} hidden={!showExplanation}>
        <label className="setup-label">
          {t("הסבר ודרך הפתרון", "Explanation and reasoning")}
          <textarea
            data-muxi-control="answer-explanation"
            aria-label={t("הסבר הפתרון", "Solution explanation")}
            dir="auto"
            value={parts.explanation}
            onChange={(e) => update(e.target.value, parts.code)}
            disabled={disabled}
            maxLength={20000}
            placeholder={t(
              "מה הרעיון שלכם? אילו הנחות ומקרי קצה לקחתם בחשבון?",
              "What is your approach? Include assumptions and edge cases.",
            )}
          />
        </label>
        <DictationControls
          value={parts.explanation}
          onChange={(explanation) => update(explanation, parts.code)}
          lang={lang}
          disabled={disabled || !showExplanation}
          maxLength={dictationExplanationLimit(value)}
        />
      </div>
      <div id={`${id}-code`} hidden={!showCode}>
        {codeMounted && (
          <>
            <div className="code-toolbar">
              <label>
                {t("קוד / תוכן טכני", "Code / technical content")}
                <select
                  data-muxi-control="code-language"
                  dir="ltr"
                  aria-label={t("שפת הקוד", "Code language")}
                  value={language}
                  disabled={disabled}
                  onChange={(e) => {
                    const next = e.target.value as AnswerLanguage;
                    setLanguage(next);
                    if (parts.code) update(parts.explanation, parts.code, next);
                  }}
                >
                  {answerLanguages.map((l) => (
                    <option value={l} key={l}>
                      {l === "text"
                        ? t(
                            "נוסחה / טבלה / פסאודו־קוד",
                            "Formula / table / pseudocode",
                          )
                        : {
                            c: "C",
                            cpp: "C++",
                            python: "Python",
                            javascript: "JavaScript",
                            verilog: "Verilog",
                            systemverilog: "SystemVerilog",
                            vhdl: "VHDL",
                          }[l]}
                    </option>
                  ))}
                </select>
              </label>
              {starterCode && !parts.code && (
                <button
                  type="button"
                  data-muxi-control="code-copy"
                  disabled={disabled}
                  onClick={() =>
                    update(
                      parts.explanation,
                      starterCode,
                      defaultAnswerLanguage(codeLanguage),
                    )
                  }
                >
                  {t("העתקת קוד השאלה לעורך", "Copy question code into editor")}
                </button>
              )}
            </div>
            <CodeEditor
              value={parts.code}
              language={language}
              disabled={disabled}
              label={t(
                "עורך קוד ותוכן טכני",
                "Code and technical content editor",
              )}
              onChange={(code) => update(parts.explanation, code)}
            />
            <p id="code-keyboard-help" className="small muted">
              {t(
                "כתיבה משמאל לימין. Ctrl+Space לפתיחת הצעות השלמה; Enter לבחירה. Tab להזחה; Esc ואז Tab כדי לצאת מהעורך. הקוד נשמר כחלק מהתשובה.",
                "Left-to-right editing. Ctrl+Space opens completions; Enter accepts a suggestion. Tab indents; Esc then Tab leaves the editor. Code is saved with your answer.",
              )}
            </p>
            {execution && language !== "text" ? <CodeExecutionPanel context={execution} language={language} source={parts.code} lang={lang} disabled={disabled} onUseStarter={(source) => update(parts.explanation, source)} /> : <p className="small muted">{t("הקוד אינו מורץ אוטומטית בזמן העריכה. הרצה זמינה בתרגול עם כפתור הרצה ייעודי.", "Code does not run automatically while editing. Execution is available in practice through a dedicated run button.")}</p>}
          </>
        )}
      </div>
      <p
        className={`small ${value.length > 20000 ? "answer-limit" : "muted"}`}
        role={value.length > 20000 ? "alert" : undefined}
        hidden={!value.length && !showExplanation && !showCode}
      >
        {value.length.toLocaleString()} / 20,000{" "}
        {t(
          "תווים · ההסבר והקוד נשמרים יחד",
          "characters · explanation and code are saved together",
        )}
      </p>
    </div>
  );
}
