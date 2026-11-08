"use client";

import { useEffect, useId, useRef, useState } from "react";
import { BidiText } from "../bidi-text";
import styles from "./guest-interview-demo.module.css";

type Lang = "he" | "en";

const question = {
  he: "איך תוודאו שמונה לחיצות סופר לחיצה ארוכה פעם אחת בלבד?",
  en: "How would you check that a counter counts a held button press only once?",
};
const example = {
  he: "אתחיל כשהכפתור משוחרר והמונה על 0. אלחץ ואמשיך להחזיק אותו. המונה צריך לעלות ל־1 ולהישאר שם. אחרי שחרור ולחיצה נוספת הוא צריך להגיע ל־2.",
  en: "I would start with the button released and the counter at 0. I would press and hold it. The count should reach 1 and stay there. After releasing and pressing again, it should reach 2.",
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
      <h3 id={id}>{he ? "שאלה אחת מתוך ראיון מדומה" : "One question from a mock interview"}</h3>
      <p>{he ? "בראיון בחשבון בוחרים משך ועונים בכתב, שאלה אחרי שאלה. כאן אפשר לנסות שאלה אחת בקצב שלכם." : "In your account, you choose a duration and answer one question at a time in writing. Here you can try one at your own pace."}</p>
      <p className={styles.note}>{he ? "הדוח שתראו בסוף נכתב מראש על תשובה לדוגמה. התשובה שתקלידו נשארת בהדגמה." : "The report at the end was written in advance for a sample answer. What you type stays in this demo."}</p>
      <button type="button" className="primary" data-muxi-control="guest-interview-start" onClick={() => setPhase("question")}>
        {he ? "לנסות את שאלת הראיון" : "Try the interview question"}
      </button>
    </> : phase === "question" ? <>
      <h3 id={id} ref={heading} tabIndex={-1}><BidiText>{question[lang]}</BidiText></h3>
      <label htmlFor={`${id}-answer`}>{he ? "איך הייתם בודקים את זה?" : "How would you test it?"}</label>
      <textarea id={`${id}-answer`} ref={answerField} dir="auto" maxLength={2000}
        data-muxi-control="guest-interview-answer" value={answer} onChange={event => setAnswer(event.target.value)} />
      <div className={styles.actions}>
        <button type="button" data-muxi-control="guest-interview-example" onClick={() => { setAnswer(example[lang]); answerField.current?.focus(); }}>
          {he ? "להשתמש בתשובה לדוגמה" : "Use the sample answer"}
        </button>
        <button type="button" className="primary" data-muxi-control="guest-interview-finish" disabled={!answer.trim()}
          onClick={() => { setPhase("report"); onAction("interview-tried"); }}>
          {he ? "להציג דוח לדוגמה" : "View the sample report"}
        </button>
      </div>
    </> : <>
      <h3 id={id} ref={heading} tabIndex={-1}>{he ? "דוח ראיון לדוגמה" : "Sample interview report"}</h3>
      <p className={styles.note}>{he ? "הדוח הזה נכתב מראש עבור הדוגמה הבאה. התשובה שלכם לא נבדקה." : "This report was prepared for the example below. Your own answer wasn’t graded."}</p>
      <div className={styles.sample}>
        <h4>{he ? "התשובה שעליה נכתב הדוח" : "The answer this report describes"}</h4>
        <p><BidiText>{example[lang]}</BidiText></p>
      </div>
      <dl>
        <dt>{he ? "מה עבד" : "What worked"}</dt>
        <dd>{he ? "התשובה מגדירה מראש את ערכי המונה הצפויים בזמן ההחזקה ובלחיצה הבאה." : "The answer specifies the expected count during the hold and after the next press."}</dd>
        <dt>{he ? "מה אפשר לבדוק בהמשך" : "What to test next"}</dt>
        <dd>{he ? "נסו שתי לחיצות קצרות ברצף. מה המרווח הקצר ביותר שבו המערכת עדיין צריכה לזהות שתיים?" : "Try two short presses in succession. How close can they be and still need to count as two?"}</dd>
      </dl>
      <button type="button" onClick={() => setPhase("question")}>{he ? "לחזור לתשובה שלי" : "Back to my answer"}</button>
    </>}
  </section>;
}
