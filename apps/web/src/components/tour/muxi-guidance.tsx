"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { createPortal } from "react-dom";
import { ArrowDown, ArrowUp } from "lucide-react";
import { MuxiMascot } from "./muxi-mascot";
import styles from "./muxi-tour.module.css";

type Lang = "he" | "en";
type Target = { element: HTMLElement; label: string };
type Pointer = Target & { x: number; y: number; below: boolean; host: HTMLElement };

/** Follow the actual controls, including intermediate clicks and native dialogs. */
export function MuxiGuidance({ root, station, lang, actions, ready, onAction }: {
  root: RefObject<HTMLDivElement | null>; station: string; lang: Lang;
  actions: readonly string[]; ready: boolean; onAction: (action: string) => void;
}) {
  const [pointer, setPointer] = useState<Pointer | null>(null);
  const lastScroll = useRef<{ station: string; element: HTMLElement; host: HTMLElement } | null>(null);
  const actionKey = actions.join("|");

  useEffect(() => {
    const scope = root.current;
    if (!scope) return;
    let highlighted: HTMLElement | null = null;
    let frame = 0;
    const t = (he: string, en: string) => lang === "he" ? he : en;
    const seen = (action: string) => actionKey.split("|").includes(action);
    const visible = (el: HTMLElement) => !!el.getClientRects().length && !el.closest("[hidden]");
    const choose = (): Target | null => {
      if (ready && !["feedback", "followup"].includes(station)) return null;
      // The circuit editor also uses <dialog open> inline. Only :modal is top-layer.
      const active = scope.querySelector<HTMLElement>("dialog:modal") ?? scope;
      const find = (name: string) => [...active.querySelectorAll<HTMLElement>(`[data-muxi-control="${name}"]`)].find(visible);
      const target = (name: string, he: string, en: string): Target | null => {
        const element = find(name);
        return element ? { element, label: t(he, en) } : null;
      };
      const openCode = () => target("code-open", "לחצו כאן כדי לפתוח את עורך הקוד", "Click here to open the code editor");
      const input = (name: string) => find(name) as HTMLInputElement | HTMLSelectElement | undefined;
      const run = () => target("circuit-simulate", "כאן מפעילים את הסימולציה", "Start the simulation here");
      const selectInput = (name: string) => target("circuit-component", `בחרו כאן את כניסת ${name}`, `Select input ${name} here`);
      switch (station) {
        case "goal": return !input("goal-date")?.value
          ? target("goal-date", "בחרו תאריך יעד כאן", "Choose a target date here")
          : target("goal-save", "שמרו את יעד ההיכרות כאן", "Save the example goal here");
        case "search": return target("library-search", "כאן מחפשים: נסו אינטל או Intel", "Search here: try Intel or אינטל");
        case "filter": return input("library-search")?.value
          ? target("library-search", "נקו את החיפוש, ואז נבחר נושא", "Clear the search, then choose a topic")
          : target("library-filter", "בחרו נושא במסנן הזה", "Choose a subject in this filter");
        case "topics": return target("topics-hardware", "בחרו תחום כדי לראות את הנושאים שלו", "Choose an area to see its subjects");
        case "explanation": return target("answer-explanation", "כאן כותבים את דרך הפתרון", "Write your reasoning here");
        case "code": return openCode()
          ?? target("code-copy", "כעת העתיקו את קוד השאלה לעורך", "Now copy the question code into the editor")
          ?? target("code-input", "תקנו כאן את תנאי הלולאה; הקוד ניתן לעריכה", "Edit the loop condition here; this code is editable");
        case "languages": return openCode()
          ?? target("code-language", "זה בורר שפת הקוד — לחצו ובחרו שפה", "This is the code-language selector; choose a language");
        case "wire": {
          const details = find("circuit-wire-details") as HTMLDetailsElement | undefined;
          if (details && !details.open) details.open = true;
          if (!seen("guide-wire-source")) return target("circuit-wire-source", "בחרו את היציאה B.Q ברשימה הזאת", "Select output B.Q in this list");
          if (!seen("guide-wire-target")) return target("circuit-wire-target", "בחרו את הכניסה AND.A1 כאן", "Select input AND.A1 here");
          return target("circuit-wire-connect", "לחצו כאן כדי לחבר את החוט", "Click here to connect the wire");
        }
        case "simulate":
          if (active.querySelectorAll(".react-flow__edge").length < 3 && !ready) return target("circuit-prewired", "טענו קודם את המעגל המחובר", "First load the connected circuit");
          return run();
        case "inputs":
          if (!seen("guide-component-selected") || !find("circuit-input-toggle")) return selectInput("A");
          return target("circuit-input-toggle", "כאן מחליפים בין 0 ל־1 ורואים את הפלט משתנה", "Toggle 0 / 1 here and watch the output change");
        case "truth": return (find("circuit-truth-table") as HTMLButtonElement | undefined)?.disabled
          ? target("circuit-prewired", "חברו את המעגל או טענו כאן דוגמה מחוברת כדי ליצור טבלת אמת", "Connect the circuit or load a prewired example here to enable its truth table")
          : target("circuit-truth-table", "לחצו כאן ליצירת כל שורות טבלת האמת", "Generate every truth-table row here");
        case "palette": return target("circuit-add-part", "לחצו על רכיב כאן כדי להוסיף אותו ללוח", "Click a component here to add it to the canvas");
        case "configure":
          if (!seen("guide-component-selected")) return target("circuit-component", "בחרו כאן רכיב שתרצו להגדיר", "Select a component to configure here");
          return target("circuit-count", "כאן משנים את מספר הכניסות", "Change the input count here")
            ?? target("circuit-label", "כאן משנים את שם הרכיב", "Change the component label here");
        case "undo": return target("circuit-undo", "כאן מבטלים את השינוי האחרון", "Undo the last change here");
        case "expand": return target("circuit-expand", "פתחו כאן את סביבת השרטוט המורחבת", "Open the expanded drawing workspace here");
        case "export-circuit": return target("circuit-download", "כאן מורידים עותק של השרטוט", "Download a copy of the circuit here");
        case "mux":
          if (find("circuit-simulate")?.getAttribute("aria-pressed") !== "true") return run();
          if (input("circuit-component")?.value !== "s" || !seen("guide-component-selected")) return selectInput("S");
          return target("circuit-input-toggle", "החליפו את S וראו איזה נתון מגיע לפלט", "Toggle S and watch which input reaches the output");
        case "clock-start": return run();
        case "clock": return (find("circuit-clock-step") as HTMLButtonElement | undefined)?.disabled ? run()
          : target("circuit-clock-step", "כאן מקדמים את השעון צעד אחד", "Advance the clock one step here");
        case "reset": return target("circuit-reset", "כאן מאפסים את מצב הסימולציה", "Reset the simulation state here");
        case "hint": return target("hint-next", "כאן מבקשים את הרמז הבא", "Request the next hint here");
        case "solution": return target("solution-confirm", "אשרו כאן את חשיפת הפתרון", "Confirm reference exposure here")
          ?? target("solution-open", "כאן מבקשים לראות את הפתרון", "Request the reference solution here");
        case "materials": return !seen("resource-opened")
          ? target("materials-open", "פתחו כאן את השרטוט", "Open the diagram here")
          : target("materials-download", "כאן מורידים את חומר העזר", "Download the reference here");
        case "photo": return target("photo-sample", "אפשר לנסות כאן תמונת דוגמה, או לבחור קובץ לצד הכפתור", "Try a sample image here, or choose your own file beside it");
        case "remove-photo": return target("photo-remove", "כאן מסירים תמונה לפני ההגשה", "Remove an image before submitting here")
          ?? target("photo-sample", "צרפו קודם תמונת דוגמה", "First attach a sample image");
        case "feedback":
          if (ready) return target("feedback-grade", "זה ציון לתשובת הדוגמה בלבד — התשובה שהקלדתם לא נבדקה", "This score belongs only to the sample answer; your typed response was not graded");
          return !input("feedback-answer")?.value.trim()
            ? target("feedback-answer", "כתבו כאן תשובת התנסות; היא לא תיבדק בסיור", "Write a practice response here; it will not be graded in the tour")
            : target("feedback-request", "פתחו כאן את דוגמת ההערכה", "Open the sample assessment here");
        case "feedback-details": return target("feedback-details", "ליד ציון הדוגמה: פתחו את הדגשים והצעד הבא", "Beside the sample score: open the feedback and next step")
          ?? (!input("feedback-answer")?.value.trim() ? target("feedback-answer", "כתבו תשובת התנסות כדי לפתוח את דוגמת הציון", "Write a practice response to open the sample score")
            : target("feedback-request", "פתחו קודם את דוגמת ההערכה", "First open the sample assessment"));
        case "followup": return ready ? target("followup-reference", "התשובה נשמרה ללא בדיקה. כאן אפשר לפתוח פתרון לדוגמה", "Your response is saved, ungraded. Reveal the reference here if useful")
          : !input("followup-answer")?.value.trim()
            ? target("followup-answer", "כאן כותבים תשובה לשאלת ההמשך", "Write your follow-up response here")
            : target("followup-save", "שמרו כאן; השמירה אינה בדיקת נכונות", "Save here; saving does not check correctness");
        case "reports": return !seen("self-assessed") ? target("confidence-save", "שמרו כאן דירוג עצמי להתנסות", "Save an example self-assessment here")
          : !input("report-answer")?.value.trim() ? target("report-answer", "כתבו כאן מה תרצו לדווח", "Describe the issue here")
            : target("report-submit", "שלחו כאן דיווח מקומי לדוגמה", "Send the local example report here");
        case "interview": return target("interview-start", "בחרו משך ולחצו כאן להתחלת הדוגמה", "Choose a duration and start the example here");
        case "interview-answer": return !input("interview-answer")?.value.trim() ? target("interview-answer", "כאן כותבים תשובה בראיון", "Write an interview response here")
          : target("interview-submit", "שמרו כאן את תשובת ההתנסות", "Save your practice response here");
        case "interview-report": return target("interview-finish", "סיימו כאן כדי לראות את דוח הדוגמה", "Finish here to view the example report");
        case "saved": return target("history-bookmark", "כאן שומרים שאלה לחזרה", "Bookmark a question here");
        case "history": return target("history-open", "כאן פותחים תרגול קודם", "Open a previous practice record here");
        case "progress": return target("progress-skill", "פתחו כאן מיומנות לחיזוק", "Open a skill to practice here");
        case "readiness": return target("readiness-open", "כאן פותחים את הראיות למוכנות", "Open the readiness evidence here");
        case "plan": return target("progress-plan", "כאן פותחים את המשימה הבאה", "Open the next task here");
        case "theme": {
          const element = scope.querySelector<HTMLElement>(".theme-toggle");
          return element ? { element, label: t("כאן מחליפים בין מצב בהיר לכהה", "Switch between light and dark here") } : null;
        }
        case "language": {
          const element = scope.querySelector<HTMLElement>("button.language-switch");
          return element ? { element, label: t("פתחו כאן את בחירת שפת האתר", "Open the site-language menu here") } : null;
        }
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
      if (lastScroll.current?.station !== station || lastScroll.current.element !== element || lastScroll.current.host !== host) {
        lastScroll.current = { station, element, host };
        // Scroll to the action vertically without sliding a long code line sideways.
        const horizontal: [HTMLElement, number][] = [];
        for (let ancestor = element.parentElement; ancestor; ancestor = ancestor.parentElement) horizontal.push([ancestor, ancestor.scrollLeft]);
        element.scrollIntoView({ block: "center", inline: "nearest", behavior: "instant" });
        horizontal.forEach(([ancestor, left]) => { ancestor.scrollLeft = left; });
      }
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
    const changed = (event: Event) => {
      const control = (event.target as Element | null)?.closest<HTMLElement>("[data-muxi-control]")?.dataset.muxiControl;
      if (event.type === "change" && control === "circuit-component") onAction("guide-component-selected");
      if (event.type === "change" && control === "circuit-wire-source") onAction("guide-wire-source");
      if (event.type === "change" && control === "circuit-wire-target") onAction("guide-wire-target");
      schedule();
    };
    const observer = new MutationObserver(schedule);
    observer.observe(scope, { childList: true, subtree: true, attributes: true, attributeFilter: ["open", "aria-pressed"] });
    const resize = new ResizeObserver(schedule);
    resize.observe(scope);
    const stage = scope.querySelector<HTMLElement>("[data-muxi-stage]");
    if (stage) resize.observe(stage);
    scope.addEventListener("input", changed, true);
    scope.addEventListener("change", changed, true);
    scope.addEventListener("click", changed, true);
    window.addEventListener("scroll", schedule, { capture: true, passive: true });
    window.addEventListener("resize", schedule);
    schedule();
    return () => {
      cancelAnimationFrame(frame); observer.disconnect(); resize.disconnect(); highlighted?.removeAttribute("data-muxi-spotlight");
      scope.removeEventListener("input", changed, true); scope.removeEventListener("change", changed, true);
      scope.removeEventListener("click", changed, true); window.removeEventListener("scroll", schedule, true);
      window.removeEventListener("resize", schedule);
    };
  }, [root, station, lang, actionKey, ready, onAction]);

  if (!pointer) return null;
  return createPortal(<div className={styles.pointer} data-muxi-pointer data-muxi-for={pointer.element.dataset.muxiControl}
    data-below={pointer.below} style={{ left: pointer.x, top: pointer.y }} aria-hidden="true">
    {pointer.below ? <ArrowUp size={18} /> : <ArrowDown size={18} />}
    <MuxiMascot pose="point" pointDirection={pointer.below ? "left" : "down"} className={styles.pointerMascot} />
    <span>{pointer.label}</span>
  </div>, pointer.host);
}
