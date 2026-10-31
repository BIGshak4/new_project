"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Play, Square } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi } from "../lib/practice-api";
import {
  ExecutionRequestGate,
  executionErrorMessage,
  executionInputKey,
  executionSourceLimit,
  executionStdinLimit,
  type CodeExecutionResult,
  type ExecutionCapabilities,
} from "../lib/code-execution";
import styles from "./code-execution.module.css";
import { ExecutionResultView } from "./code-execution-result";
export { ExecutionResultView } from "./code-execution-result";

export type CodeExecutionContext = {
  attemptId: string;
  api: Pick<PracticeApi, "executionCapabilities" | "executeCode">;
};

export function CodeExecutionPanel({ context, language, source, lang, disabled, onUseStarter }: {
  context: CodeExecutionContext;
  language: string;
  source: string;
  lang: Lang;
  disabled: boolean;
  onUseStarter: (source: string) => void;
}) {
  const { attemptId, api } = context;
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const inputId = useId();
  const [capabilities, setCapabilities] = useState<{ attemptId: string; value: ExecutionCapabilities } | null>(null);
  const [capabilityError, setCapabilityError] = useState("");
  const [reload, setReload] = useState(0);
  const [stdin, setStdin] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [cancelled, setCancelled] = useState(false);
  const [result, setResult] = useState<{ key: string; value: CodeExecutionResult } | null>(null);
  const gate = useRef(new ExecutionRequestGate());
  const request = useRef<AbortController | null>(null);
  const inputKey = executionInputKey(attemptId, language, source, stdin);
  const currentInput = useRef(inputKey);
  currentInput.current = inputKey;
  const available = capabilities?.attemptId === attemptId ? capabilities.value : null;
  const tested = available?.tested_languages.includes(language) ?? false;
  const supported = available?.languages.includes(language) ?? false;

  useEffect(() => {
    const controller = new AbortController();
    setCapabilityError("");
    void api.executionCapabilities(attemptId, controller.signal).then((value) => {
      if (!controller.signal.aborted) setCapabilities({ attemptId, value });
    }).catch((issue) => {
      if (!controller.signal.aborted) setCapabilityError(executionErrorMessage(issue, lang));
    });
    return () => controller.abort();
  }, [api, attemptId, reload, lang]);

  useEffect(() => {
    gate.current.invalidate();
    request.current?.abort();
    setRunning(false);
    setError(null);
    setCancelled(false);
    return () => {
      gate.current.invalidate();
      request.current?.abort();
    };
  }, [inputKey]);

  const run = async () => {
    if (!available?.available || !supported || !source.trim() || source.length > executionSourceLimit || stdin.length > executionStdinLimit || running || disabled) return;
    const controller = new AbortController();
    request.current?.abort();
    request.current = controller;
    const revision = gate.current.begin();
    const startedInput = inputKey;
    setRunning(true);
    setError(null);
    setCancelled(false);
    setResult(null);
    try {
      const value = await api.executeCode(attemptId, { language, source, stdin: tested ? "" : stdin, idempotency_key: crypto.randomUUID() }, controller.signal);
      if (!controller.signal.aborted && gate.current.accepts(revision, startedInput, currentInput.current)) setResult({ key: startedInput, value });
    } catch (issue) {
      if (!controller.signal.aborted && gate.current.accepts(revision, startedInput, currentInput.current)) setError(issue);
    } finally {
      if (gate.current.accepts(revision, startedInput, currentInput.current)) setRunning(false);
    }
  };

  const cancel = () => {
    gate.current.invalidate();
    request.current?.abort();
    setRunning(false);
    setCancelled(true);
  };

  return <section className={styles.panel} aria-label={t("הרצת קוד", "Code execution")} aria-busy={running}>
    <div className={styles.heading}>
      <h3>{t("הרצה ובדיקה", "Run and test")}</h3>
      <span className="small muted">{t("הרצה אינה מגישה את התשובה למשוב", "Running does not submit your answer for feedback")}</span>
    </div>
    {!available && !capabilityError && <p className="small muted" role="status">{t("בודקים אילו אפשרויות הרצה זמינות…", "Checking available execution options…")}</p>}
    {capabilityError && <div role="alert"><p>{capabilityError}</p><button type="button" onClick={() => setReload((n) => n + 1)}>{t("ניסיון נוסף", "Try again")}</button></div>}
    {available && !available.available && <div><p role="status" className="small muted">{t("שירות ההרצה אינו זמין כרגע. אפשר להמשיך לכתוב ולשלוח תשובה למשוב.", "Execution is currently unavailable. You can continue editing and submit your answer for feedback.")}</p><button type="button" onClick={() => setReload((n) => n + 1)}>{t("בדיקת זמינות מחדש", "Check availability again")}</button></div>}
    {available?.available && !supported && <p className="small muted">{t("אין הרצה לשפה הזאת. בחרו שפת תכנות או HDL נתמכת.", "This language cannot be executed. Choose a supported programming or HDL language.")}</p>}
    {available?.available && supported && <>
      {tested ? <>
        <p className="small">{t("הקוד יורץ מול בדיקות השאלה לפי הממשק הבא:", "Your code will run against the question tests using this interface:")}</p>
        {available.contract?.[lang] && <p className={styles.contract} dir="auto">{available.contract[lang]}</p>}
        {!source.trim() && available.starters[language] && <button type="button" disabled={disabled} onClick={() => onUseStarter(available.starters[language])}>{t("טעינת שלד קוד לבדיקה", "Load a test-ready starter")}</button>}
      </> : <>
        <p className="small muted">{t("לשאלה הזאת אין בדיקות מוכנות בשפה שבחרתם. אפשר להריץ תוכנית מלאה או testbench משלכם; הצלחת ההרצה לא קובעת שהתשובה נכונה.", "This question has no prepared tests in the selected language. Run a complete program or your own testbench; successful execution does not establish answer correctness.")}</p>
        <details className={styles.input}>
          <summary>{t("קלט לתוכנית (stdin) · אופציונלי", "Program input (stdin) · optional")}</summary>
          <label htmlFor={inputId} className="small">{t("טקסט שיועבר לתוכנית בזמן ההרצה", "Text passed to the program during execution")}</label>
          <textarea id={inputId} dir="ltr" value={stdin} onChange={(event) => setStdin(event.target.value)} maxLength={executionStdinLimit} disabled={disabled} spellCheck={false} rows={3} />
          <span className="small muted">{stdin.length.toLocaleString()} / {executionStdinLimit.toLocaleString()}</span>
        </details>
      </>}
      {source.length > executionSourceLimit && <p role="alert">{t("אפשר להריץ עד 20,000 תווי קוד. קצרו את הקוד ונסו שוב.", "Execution accepts up to 20,000 source characters. Shorten the code and retry.")}</p>}
      <div className={styles.actions}>
        <button type="button" className="primary" data-muxi-control="code-execute" onClick={() => void run()} disabled={disabled || running || !source.trim() || source.length > executionSourceLimit}>
          <Play size={16} aria-hidden="true" />
          {running ? t("מריצים…", "Running…") : tested ? t("הרצה מול בדיקות השאלה", "Run question tests") : t("הרצת הקוד", "Run code")}
        </button>
        {running && <button type="button" onClick={cancel}><Square size={15} aria-hidden="true" />{t("הפסקת המתנה", "Stop waiting")}</button>}
      </div>
      {running && <p className="small muted" role="status">{t("הקוד רץ בסביבה מבודדת. התוצאה תוצג כאן; אפשר להמשיך לערוך את הטיוטה.", "Code runs in an isolated environment. Results will appear here; you may continue editing the draft.")}</p>}
      {cancelled && <p className="small muted" role="status">{t("ההמתנה הופסקה. ההרצה בשרת עשויה להסתיים עד מגבלת הזמן שלה.", "Waiting stopped. The server execution may continue until its time limit.")}</p>}
      {!!error && <p role="alert">{executionErrorMessage(error, lang)}</p>}
    </>}
    {result && <ExecutionResultView result={result.value} lang={lang} stale={result.key !== inputKey} />}
  </section>;
}
