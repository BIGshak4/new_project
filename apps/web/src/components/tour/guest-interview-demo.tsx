"use client";

import { useEffect, useId, useRef, useState } from "react";
import { BidiText } from "../bidi-text";
import styles from "./guest-interview-demo.module.css";

type Lang = "he" | "en";

const question = {
  he: "איך תבדקו שהמונה עולה רק פעם אחת כשמחזיקים את הכפתור לחוץ?",
  en: "How would you test that a counter goes up only once when you hold a button down?",
};
const example = {
  he: "אתחיל כשהכפתור משוחרר והמונה מראה 0. אלחץ ואחזיק את הכפתור. כל עוד הוא לחוץ, המונה צריך להראות 1. אשחרר ואלחץ שוב. עכשיו המונה צריך להראות 2.",
  en: "I’d start with the button released and the counter at 0. I’d press and hold the button. The count should stay at 1 the whole time. Then I’d release it and press again. Now the count should be 2.",
};

export function GuestInterviewDemo({ lang, onAction }: { lang: Lang; onAction: (action: string) => void }) {
  const he = lang === "he";
  const id = useId();
  const heading = useRef<HTMLHeadingElement>(null);
  const answerField = useRef<HTMLTextAreaElement>(null);
  const [phase, setPhase] = useState<"intro" | "question" | "report">("intro");
  const [answer, setAnswer] = useState("");
  useEffect(() => {
    if (phase !== "intro") heading.current?.focus({ preventScroll: true });
  }, [phase]);

  return <section className={styles.demo} aria-labelledby={id}>
    {phase === "intro" ? <>
      <h3 id={id}>{he ? "בדיקה של מונה לחיצות" : "Testing a button counter"}</h3>
      <p>{he ? "כאן תנסו שאלה אחת בקצב שלכם. אפשר לכתוב תשובה משלכם או לקרוא את התשובה של מוקסי." : "Try one question at your own pace. You can write your own answer or read Muxi’s."}</p>
      <p className={styles.note}>{he ? "בסוף תראו דוח שנכתב מראש על התשובה של מוקסי." : "At the end you’ll see a report written in advance about Muxi’s answer."}</p>
      <button type="button" className="primary" data-muxi-control="guest-interview-start" onClick={() => setPhase("question")}>
        {he ? "לפתוח את השאלה" : "Open the question"}
      </button>
    </> : phase === "question" ? <>
      <h3 id={id} ref={heading} tabIndex={-1}><BidiText>{question[lang]}</BidiText></h3>
      <label htmlFor={`${id}-answer`}>{he ? "התשובה שלכם" : "Your answer"}</label>
      <textarea id={`${id}-answer`} ref={answerField} dir="auto" maxLength={2000}
        data-muxi-control="guest-interview-answer" value={answer} onChange={event => setAnswer(event.target.value)} />
      <div className={styles.actions}>
        <button type="button" data-muxi-control="guest-interview-example" onClick={() => { setAnswer(example[lang]); answerField.current?.focus(); }}>
          {he ? "להשתמש בתשובה של מוקסי" : "Use Muxi’s answer"}
        </button>
        <button type="button" className="primary" data-muxi-control="guest-interview-finish" disabled={!answer.trim()}
          onClick={() => { setPhase("report"); onAction("interview-tried"); }}>
          {he ? "להציג דוח לדוגמה" : "View the sample report"}
        </button>
      </div>
    </> : <>
      <h3 id={id} ref={heading} tabIndex={-1}>{he ? "דוח ראיון לדוגמה" : "Sample interview report"}</h3>
      <p className={styles.note}>{he ? "הדוח הוכן מראש על התשובה של מוקסי. אפשר להשוות אותה למה שכתבתם." : "This report was prepared in advance for Muxi’s answer. You can compare it with your own."}</p>
      <div className={styles.sample}>
        <h4>{he ? "התשובה של מוקסי" : "Muxi’s answer"}</h4>
        <p><BidiText>{example[lang]}</BidiText></p>
      </div>
      <dl>
        <dt>{he ? "מה עבד בתשובה" : "What worked in this answer"}</dt>
        <dd>{he ? "אפשר לשחזר את הבדיקה כי ברור מתי המונה אמור להראות 1 ומתי הוא אמור להראות 2." : "Someone else could repeat the test because the answer says exactly when to expect 1 and when to expect 2."}</dd>
        <dt>{he ? "מה אפשר לבדוק בהמשך" : "What to test next"}</dt>
        <dd>{he ? "נסו שתי לחיצות קצרות ברצף. מה המרווח הקצר ביותר שבו המונה עדיין אמור לזהות שתי לחיצות?" : "Try two quick presses in a row. What is the shortest gap at which the counter should still recognize both presses?"}</dd>
      </dl>
      <button type="button" onClick={() => setPhase("question")}>{he ? "לחזור לתשובה שלי" : "Back to my answer"}</button>
    </>}
  </section>;
}
