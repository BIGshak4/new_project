"use client";

import { useRef, useState } from "react";
import { Shuffle } from "lucide-react";
import { QuickQuiz, QuickQuizDialog } from "../quick-quiz";
import type { QuickQuizRun } from "../../lib/quick-quiz";
import styles from "./tour-exercises.module.css";

export function TourQuizDemo({ lang, onAction }: { lang: "he" | "en"; onAction: (action: string) => void }) {
  const he = lang === "he";
  const [open, setOpen] = useState(false);
  const [run, setRun] = useState<QuickQuizRun | null>(null);
  const opener = useRef<HTMLButtonElement>(null);
  return <>
    {!run && <>
      <p>{he ? "בתרגול הקצר אפשר לחשוב על תשובה ולפתוח את הפתרון כשמוכנים. נרכיב בוחן מתוך המאגר של האתר." : "Think through each short question, then reveal its solution when you’re ready. Build a quiz from JobRun’s question bank."}</p>
      <button type="button" className={styles.primary} ref={opener} data-muxi-control="quiz-open" aria-haspopup="dialog" onClick={() => setOpen(true)}><Shuffle size={16} />{he ? "בחירת נושאים לבוחן" : "Choose quiz topics"}</button>
    </>}
    <QuickQuizDialog open={open} lang={lang} returnFocus={opener} onClose={() => setOpen(false)} onStart={next => {
      setOpen(false); setRun(next); onAction("quiz-started");
    }} />
    {run && <QuickQuiz key={run.id} preview run={run} lang={lang} onNew={() => setOpen(true)} onBack={() => setRun(null)} />}
  </>;
}
