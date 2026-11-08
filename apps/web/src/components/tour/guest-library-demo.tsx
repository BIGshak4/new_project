"use client";

import { useId, useState } from "react";
import { BookOpen, ChevronDown, Timer } from "lucide-react";
import shortQuestions from "../../content/fundamentals-code-logic.json";
import { BidiText } from "../bidi-text";
import styles from "./guest-library-demo.module.css";

const shortExample = shortQuestions.find(question => question.id === "quick-sw-02")!;
type Category = "interview" | "short";

export function GuestLibraryDemo({ lang, onAction }: { lang: "he" | "en"; onAction: (action: string) => void }) {
  const he = lang === "he";
  const id = useId();
  const [open, setOpen] = useState<Category | null>(null);
  const [revealed, setRevealed] = useState(false);

  const categories = [
    { id: "interview" as const, icon: BookOpen, title: he ? "שאלות ראיון" : "Interview questions",
      text: he ? "חומרה, תוכנה וחשיבה לוגית. אפשר לחפש לפי נושא, תפקיד או חברה." : "Find hardware, software and reasoning questions by topic, role or company." },
    { id: "short" as const, icon: Timer, title: he ? "יסודות בקטנה" : "Short fundamentals",
      text: he ? "שאלה קצרה על עיקרון אחד. מתאימה לכמה דקות של תרגול." : "One principle in one short question, for a few minutes of practice." },
  ];
  return <section className={styles.library} aria-labelledby={id}>
    <h2 id={id}>{he ? "מאגר השאלות" : "Question library"}</h2>
    {categories.map(({ id: category, icon: Icon, title, text }) => {
      const selected = open === category;
      const interview = category === "interview";
      return <div key={category} className={styles.category}>
        <button type="button" data-muxi-control={`guest-library-${category}`} aria-expanded={selected} aria-controls={`${id}-${category}`}
          onClick={() => { setOpen(selected ? null : category); setRevealed(false); onAction("library-explored"); }}>
          <Icon size={21} aria-hidden="true" /><span><strong>{title}</strong><small>{text}</small></span><ChevronDown size={18} aria-hidden="true" />
        </button>
        <div id={`${id}-${category}`} hidden={!selected} className={styles.example}>
          <h3>{interview ? (he ? "אזעקה עם שלושה חיישנים" : "A three-sensor alarm") : shortExample.title[lang]}</h3>
          <p><BidiText>{interview ? (he ? "אזעקה צריכה לפעול כשלפחות שניים משלושת החיישנים מזהים תקלה. איך תבנו את המעגל?" : "An alarm must sound when at least two of three sensors report a fault. How would you build the circuit?") : shortExample.prompt[lang]}</BidiText></p>
          <button type="button" className={styles.reveal} data-muxi-control="guest-library-reveal" aria-expanded={revealed} onClick={() => setRevealed(!revealed)}>
            {interview ? (he ? (revealed ? "סגירת הרמז" : "פתיחת רמז") : (revealed ? "Hide hint" : "Show hint")) : (he ? (revealed ? "הסתרת הפתרון" : "הצגת פתרון קצר") : (revealed ? "Hide solution" : "Show short solution"))}
          </button>
          {revealed && selected && <p className={styles.answer}><BidiText>{interview ? (he ? "חשבו על כל זוג חיישנים. מספיק ששניהם פעילים כדי להדליק את האזעקה, גם כשהחיישן השלישי כבוי." : "Think about each pair of sensors. If both are active, the alarm should sound even when the third sensor is off.") : shortExample.answer[lang]}</BidiText></p>}
        </div>
      </div>;
    })}
  </section>;
}
