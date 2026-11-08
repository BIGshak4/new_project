"use client";

import { useEffect, useState, type RefObject } from "react";
import { BidiText } from "../bidi-text";
import { proseDirection } from "../../lib/bidi-segments";
import { createPortal } from "react-dom";
import { ArrowDown, ArrowUp } from "lucide-react";
import { MuxiMascot } from "./muxi-mascot";
import styles from "./muxi-tour.module.css";

type Lang = "he" | "en";
type Target = { element: HTMLElement; label: string };
type Pointer = Target & { x: number; y: number; below: boolean; host: HTMLElement };

/** Follow the actual controls, including intermediate clicks and native dialogs. */
export function MuxiGuidance({ root, station, lang, ready }: {
  root: RefObject<HTMLDivElement | null>; station: string; lang: Lang;
  ready: boolean;
}) {
  const [pointer, setPointer] = useState<Pointer | null>(null);

  useEffect(() => {
    const scope = root.current;
    if (!scope) return;
    let highlighted: HTMLElement | null = null;
    let frame = 0;
    const t = (he: string, en: string) => lang === "he" ? he : en;
    const visible = (el: HTMLElement) => !!el.getClientRects().length && !el.closest("[hidden]");
    const choose = (): Target | null => {
      if (ready) return null;
      // The circuit editor also uses <dialog open> inline. Only :modal is top-layer.
      const active = scope.querySelector<HTMLElement>("dialog:modal") ?? scope;
      const find = (name: string) => [...active.querySelectorAll<HTMLElement>(`[data-muxi-control="${name}"]`)].find(visible);
      const target = (name: string, he: string, en: string): Target | null => {
        const element = find(name);
        return element ? { element, label: t(he, en) } : null;
      };
      switch (station) {
        case "goal":
          return target("goal-keep", "אפשר להמשיך עם היעד הקיים", "Keep this goal if it still fits")
            ?? (!find("goal-save") || find("goal-save")?.matches(":disabled")
              ? target("goal-roles", "בחרו תפקיד או למידה ללא יעד", "Choose a role or explore freely")
                  ?? target("goal-mode-explore", "אפשר גם ללמוד ללא יעד", "You can also explore freely")
              : target("goal-save", "כאן שומרים את היעד בחשבון", "Save your goal to your account"));
        case "library": return target("library-question", "בחרו שאלה למבט מקרוב", "Choose a question to take a closer look");
        case "code": return target("code-fix", "אפשר לנסות את התיקון כאן", "Try Muxi’s correction here");
        case "circuit": return target("xor-input-a", "החליפו את הערך של הכניסה", "Toggle this input");
        case "feedback": return find("feedback-review")?.matches(":disabled")
          ? target("feedback-answer", "בחרו תשובה לבדיקה", "Choose an answer to review")
          : target("feedback-review", "פתחו את המשוב של התשובה שבחרתם", "Open feedback on the answer you chose");
        case "quiz": return target("quiz-open", "כאן בוחרים נושאים לבוחן", "Choose quiz topics here");
        case "interview": return target("interview-start", "פתחו את הראיון לדוגמה", "Start the sample interview")
          ?? (find("interview-finish")?.matches(":disabled")
            ? target("interview-answer", "כתבו תשובה או השתמשו בדוגמה", "Write a response or use the example")
            : target("interview-finish", "פתחו את הדוח לדוגמה", "Open the sample report"));
        case "community": return find("friend-add")?.matches(":disabled")
          ? target("friend-preview", "נסו את קוד החברות של נועה", "Try Noa’s sample friend code")
          : target("friend-add", "שלחו בקשת חברות לדוגמה", "Try a friend request");
        case "helper": return target("helper-question", "בחרו מה לשאול את העוזר", "Choose what to ask your helper");
        default: return null;
      }
    };
    const position = () => {
      frame = 0;
      const chosen = choose();
      if (highlighted !== chosen?.element) {
        highlighted?.removeAttribute("data-muxi-spotlight");
        highlighted = chosen?.element ?? null;
        highlighted?.setAttribute("data-muxi-spotlight", "");
      }
      if (!chosen) { setPointer(null); return; }
      const { element, label } = chosen;
      const modal = element.closest<HTMLElement>("dialog:modal");
      const host = modal ?? scope;
      const rect = element.getBoundingClientRect();
      const headerBottom = modal ? 0 : scope.querySelector("header")?.getBoundingClientRect().bottom ?? 0;
      let top = Math.max(headerBottom, rect.top), bottom = Math.min(window.innerHeight - 70, rect.bottom);
      let left = Math.max(0, rect.left), right = Math.min(window.innerWidth, rect.right);
      for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) {
        const style = getComputedStyle(ancestor), box = ancestor.getBoundingClientRect();
        if (/auto|scroll|hidden|clip/.test(style.overflowY)) { top = Math.max(top, box.top); bottom = Math.min(bottom, box.bottom); }
        if (/auto|scroll|hidden|clip/.test(style.overflowX)) { left = Math.max(left, box.left); right = Math.min(right, box.right); }
        // Fixed/top-layer hosts escape the zero-height, scroll-locked document.
        if (ancestor === host) break;
      }
      if (bottom - top < 12 || right - left < 12) { setPointer(null); return; }
      const hit = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
      if (!hit || !element.contains(hit)) { setPointer(null); return; }
      const below = rect.top < headerBottom + 90;
      const visibleCenter = (left + right) / 2;
      const x = Math.max(150, Math.min(window.innerWidth - 150, visibleCenter));
      const y = below ? rect.bottom + 9 : rect.top - 9;
      if (rect.bottom < headerBottom || rect.top > window.innerHeight - 70 || rect.right < 0 || rect.left > window.innerWidth) { setPointer(null); return; }
      setPointer(old => old?.element === element && old.label === label && old.x === x && old.y === y && old.below === below && old.host === host ? old : { element, label, x, y, below, host });
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(position); };
    const observer = new MutationObserver(schedule);
    observer.observe(scope, { childList: true, subtree: true, attributes: true, attributeFilter: ["open", "aria-pressed", "disabled"] });
    const resize = new ResizeObserver(schedule);
    resize.observe(scope);
    const stage = scope.querySelector<HTMLElement>("[data-muxi-stage]");
    if (stage) resize.observe(stage);
    scope.addEventListener("input", schedule, true);
    scope.addEventListener("change", schedule, true);
    scope.addEventListener("click", schedule, true);
    window.addEventListener("scroll", schedule, { capture: true, passive: true });
    window.addEventListener("resize", schedule);
    schedule();
    return () => {
      cancelAnimationFrame(frame); observer.disconnect(); resize.disconnect(); highlighted?.removeAttribute("data-muxi-spotlight");
      scope.removeEventListener("input", schedule, true); scope.removeEventListener("change", schedule, true);
      scope.removeEventListener("click", schedule, true); window.removeEventListener("scroll", schedule, true);
      window.removeEventListener("resize", schedule);
    };
  }, [root, station, lang, ready]);

  if (!pointer) return null;
  return createPortal(<div className={styles.pointer} data-muxi-pointer data-muxi-for={pointer.element.dataset.muxiControl}
    data-below={pointer.below} style={{ left: pointer.x, top: pointer.y }} aria-hidden="true">
    {pointer.below ? <ArrowUp size={18} /> : <ArrowDown size={18} />}
    <MuxiMascot pose="point" pointDirection={pointer.below ? "left" : "down"} className={styles.pointerMascot} />
    <span dir={proseDirection(pointer.label, lang === "he" ? "rtl" : "ltr")}><BidiText>{pointer.label}</BidiText></span>
  </div>, pointer.host);
}
