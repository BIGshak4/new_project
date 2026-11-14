"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { Maximize, Minimize } from "lucide-react";
import { lockBodyScroll } from "../lib/body-scroll-lock";

export function CodeWorkspace({ lang, children }: { lang: "he" | "en"; children: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  const [full, setFull] = useState(false);
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
      {children}
    </dialog>
  );
}
