"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Maximize, Minimize, PanelRightClose, PanelRightOpen, X } from "lucide-react";
import { lockBodyScroll } from "../lib/body-scroll-lock";
import type { CircuitQuestionReference } from "./circuit-editor";
import { BidiText } from "./bidi-text";
import { QuestionTitle } from "./question-title";

export function CodeWorkspace({ lang, children, question }: {
  lang: "he" | "en";
  children: ReactNode;
  question?: CircuitQuestionReference;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  const questionToggle = useRef<HTMLButtonElement>(null);
  const questionId = useId();
  const [full, setFull] = useState(false);
  const [showQuestion, setShowQuestion] = useState(true);
  const title = lang === "he" ? "עורך הקוד" : "Code editor";

  useEffect(() => {
    if (full) return lockBodyScroll();
  }, [full]);

  function openFullscreen() {
    const element = dialog.current;
    if (!element) return;
    // Promote the same editor and run panel to the top layer, preserving their state.
    element.close();
    element.showModal();
    setFull(true);
    toggle.current?.focus({ preventScroll: true });
  }

  function returnToAnswer() {
    const element = dialog.current;
    if (!element) return;
    element.close();
    element.show();
    setFull(false);
    toggle.current?.focus({ preventScroll: true });
  }

  return (
    <dialog
      ref={dialog}
      open
      className="code-workspace"
      role={full ? "dialog" : "region"}
      aria-modal={full || undefined}
      aria-label={title}
      dir={lang === "he" ? "rtl" : "ltr"}
      onKeyDownCapture={(event) => {
        if (!full || event.key !== "Escape" || !(event.target instanceof Element)) return;
        const editor = event.target.closest(".cm-editor");
        if (!editor || editor.querySelector(".cm-tooltip-autocomplete, .cm-search, .cm-snippetField")) return;
        event.preventDefault();
        event.stopPropagation();
        returnToAnswer();
      }}
      onCancel={(event) => {
        event.preventDefault();
        if (full) returnToAnswer();
      }}
    >
      <div className="code-workspace-controls">
        {full && <strong>{title}</strong>}
        <div className="code-workspace-actions">
          {full && question && <button
            ref={questionToggle}
            type="button"
            data-muxi-control="code-question-toggle"
            aria-expanded={showQuestion}
            aria-controls={questionId}
            onClick={() => setShowQuestion(shown => !shown)}
          >
            {showQuestion ? <PanelRightClose size={16} aria-hidden="true" /> : <PanelRightOpen size={16} aria-hidden="true" />}
            {showQuestion
              ? (lang === "he" ? "הסתרת השאלה" : "Hide question")
              : (lang === "he" ? "הצגת השאלה" : "Show question")}
          </button>}
          <button
            ref={toggle}
            type="button"
            data-muxi-control="code-fullscreen"
            aria-haspopup={full ? undefined : "dialog"}
            onClick={full ? returnToAnswer : openFullscreen}
          >
            {full ? <Minimize size={16} aria-hidden="true" /> : <Maximize size={16} aria-hidden="true" />}
            {full
              ? (lang === "he" ? "חזרה לתשובה" : "Back to answer")
              : (lang === "he" ? "מסך מלא" : "Full screen")}
          </button>
        </div>
      </div>
      <div className="code-workspace-body" data-question-open={full && !!question && showQuestion}>
        <div className="code-workspace-editor">{children}</div>
        {full && question && showQuestion && <aside
          className="code-workspace-question"
          id={questionId}
          aria-label={lang === "he" ? "השאלה בזמן כתיבת הקוד" : "Question reference"}
        >
          <div className="code-workspace-question-header">
            <QuestionTitle as="h2" lang={lang}><BidiText>{question.title || (lang === "he" ? "השאלה" : "Question")}</BidiText></QuestionTitle>
            <button type="button" className="code-workspace-question-close"
              aria-label={lang === "he" ? "סגירת תצוגת השאלה" : "Close question reference"}
              onClick={() => {
                setShowQuestion(false);
                questionToggle.current?.focus({ preventScroll: true });
              }}><X size={18} aria-hidden="true" /></button>
          </div>
          <div className="code-workspace-question-content">{question.content}</div>
        </aside>}
      </div>
    </dialog>
  );
}
