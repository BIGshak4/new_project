"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import type { Lang } from "./auth";
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
export function AnswerEditor({
  value,
  onChange,
  lang,
  disabled,
  codeLanguage,
  starterCode,
}: {
  value: string;
  onChange: (value: string) => void;
  lang: Lang;
  disabled: boolean;
  codeLanguage: string | null;
  starterCode: string | null;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const parts = parseTechnicalAnswer(value);
  const [chosenLanguage, setLanguage] = useState<AnswerLanguage>(
    parts.language ?? defaultAnswerLanguage(codeLanguage),
  );
  const [showCode, setShowCode] = useState(!!codeLanguage || !!parts.code);
  const language = parts.language ?? chosenLanguage;
  const update = (explanation: string, code: string, nextLanguage = language) =>
    onChange(formatTechnicalAnswer(explanation, code, nextLanguage));
  return (
    <div className="answer-editor">
      <label className="setup-label">
        {t("הסבר ודרך הפתרון", "Explanation and reasoning")}
        <textarea
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
      {!showCode && !parts.code ? (
        <button disabled={disabled} onClick={() => setShowCode(true)}>
          {t(
            "הוספת קוד, נוסחה או טבלת אמת",
            "Add code, a formula, or a truth table",
          )}
        </button>
      ) : (
        <>
          <div className="code-toolbar">
            <label>
              {t("קוד / תוכן טכני", "Code / technical content")}
              <select
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
              "כתיבה משמאל לימין. Ctrl+Space לפתיחת הצעות השלמה; Enter לבחירה. Tab להזחה; Esc ואז Tab כדי לצאת מהעורך. הקוד נשמר כחלק מהתשובה ואינו מורץ כאן.",
              "Left-to-right editing. Ctrl+Space opens completions; Enter accepts a suggestion. Tab indents; Esc then Tab leaves the editor. Code is saved with your answer and is not executed here.",
            )}
          </p>
        </>
      )}
      <p
        className={`small ${value.length > 20000 ? "answer-limit" : "muted"}`}
        role={value.length > 20000 ? "alert" : undefined}
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
