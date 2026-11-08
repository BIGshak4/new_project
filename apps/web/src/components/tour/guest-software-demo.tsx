"use client";

import dynamic from "next/dynamic";
import { useEffect, useId, useRef, useState } from "react";
import { ChevronDown, ChevronUp, CodeXml, Pencil } from "lucide-react";
import { BidiText } from "../bidi-text";
import { EvaluationPanel } from "../evaluation-panel";
import { checkMaximumExample, fixedMaximum, starterMaximum, type MaximumCheck } from "../../lib/guest-software-example";
import styles from "./guest-software-demo.module.css";

const CodeEditor = dynamic(() => import("../technical-code-editor"), { ssr: false });
type Lang = "he" | "en";
type Props = {
  station: "guest-explain" | "guest-code";
  lang: Lang;
  explanation: string;
  onExplanationChange: (value: string) => void;
  onAction: (action: string) => void;
};
const sampleExplanation = {
  he: "אתחיל עם מקסימום של 0 ואעבור על המערך פעם אחת. אם אמצא מספר גדול יותר, אעדכן את המקסימום. בסוף אחזיר אותו. זמן הריצה הוא O(n) ונדרש זיכרון נוסף קבוע.",
  en: "I’ll start with a maximum of 0 and scan the array once. Whenever I find a larger number, I’ll update the maximum. I’ll return it at the end. This takes O(n) time and constant extra space.",
};
const question = {
  he: "כתבו פונקציה שמקבלת מערך לא ריק של מספרים שלמים ומחזירה את הערך הגדול ביותר. למשל, עבור [3, 9, 5] נחזיר 9.",
  en: "Write a function that returns the largest value in a nonempty array of integers. For example, [3, 9, 5] should return 9.",
};

function Prompt({ lang }: { lang: Lang }) {
  return <div className={styles.prompt}>
    <h2>{lang === "he" ? "הערך הגדול במערך" : "Largest value in an array"}</h2>
    <p><BidiText>{question[lang]}</BidiText></p>
  </div>;
}

function SampleReview({ lang, band }: { lang: Lang; band: "PARTIAL" | "STRONG" }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const remarks = band === "PARTIAL" ? {
    summary: t("הסריקה יעילה, אבל האתחול ל־0 מחמיץ מערכים שבהם כל הערכים שליליים.", "The scan is efficient, but starting at zero misses all-negative arrays."),
    key_points_hit: [
      t("ההסבר מתאר איך מעדכנים את המקסימום במעבר יחיד.", "The explanation describes how to update the maximum in one pass."),
      t("סיבוכיות הזמן היא O(n), ונדרש רק משתנה עזר אחד.", "The time complexity is O(n) and only one extra variable is needed."),
    ],
    key_points_missed: [t("עבור [-8, -3, -5] האלגוריתם יחזיר 0, אף שהערך הגדול במערך הוא ‎-3.", "For [-8, -3, -5] the algorithm returns 0, although the maximum is -3.")],
    card: {
      what_happened: t("השיטה שומרת את הערך הגדול שנמצא עד כה, אבל הערך ההתחלתי לא נלקח מהקלט.", "The algorithm keeps the largest value seen so far, but its initial value does not come from the input."),
      why_it_matters: t("בראיון יבקשו לדעת שהפתרון עובד על כל הקלטים שהשאלה מאפשרת, כולל ערכים שליליים.", "In an interview you need to cover all permitted inputs, including negative values."),
      next_step: t("אתחלו את best לאיבר הראשון ובדקו מערך שכולו שלילי.", "Initialize best from the first element and test an all-negative array."),
      your_reasoning_vs_reference: t("בשתי השיטות משווים את איברי המערך. בפתרון המוצע גם המקסימום הראשוני הוא איבר אמיתי במערך.", "Both approaches compare the array elements. In the reference approach, the initial maximum is itself an array element."),
    },
  } : {
    summary: t("הפונקציה המתוקנת מוצאת את המקסימום במעבר יחיד, גם כשהמספרים שליליים.", "The corrected function finds the maximum in one pass, including when every number is negative."),
    key_points_hit: [
      t("האתחול מכסה מערך של מספרים שליליים ומערך עם איבר יחיד.", "The initializer handles all-negative arrays and single-element arrays."),
      t("הסריקה משווה כל איבר למקסימום הנוכחי ומשתמשת בזיכרון נוסף קבוע.", "The scan compares each element with the current maximum and uses constant extra space."),
    ],
    key_points_missed: [],
    card: {
      what_happened: t("בדיקות הדוגמה מחזירות את הערך הצפוי בכל אחד ממקרי הקצה שהוצגו.", "The sample checks return the expected maximum for every displayed edge case."),
      why_it_matters: t("בדיקות של מערך בן איבר אחד ושל ערכים שליליים מבהירות מדוע האתחול שבחרתם מתאים.", "A singleton and an all-negative array make it clear why the initializer works."),
      next_step: t("הסבירו למה אחרי כל צעד best הוא הערך הגדול ביותר שנראה עד אותו רגע.", "Explain why best is the largest value seen after each step."),
      your_reasoning_vs_reference: t("הסריקה שומרת מקסימום מקומי ומעדכנת אותו רק כשהערך הבא גדול יותר. לכן הערך שנשאר בסוף הוא המקסימום במערך.", "The scan maintains a running maximum and updates it only for a larger element. The final value is therefore the array maximum."),
    },
  };
  return <EvaluationPanel example lang={lang} submission={{ ...remarks, status: "done", band, check: null,
    flags: [], tip: { key: "maximum", text: remarks.card.next_step } }} />;
}

function normalText(value: string) {
  return value.trim().replace(/\s+/g, " ");
}

function ExplanationDemo({ lang, explanation, onExplanationChange, onAction }: Omit<Props, "station">) {
  const [draft, setDraft] = useState(explanation);
  const [reviewNumber, setReviewNumber] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const he = lang === "he";
  const showReview = reviewNumber > 0 && draft.trim() === explanation;
  const matchesSample = Object.values(sampleExplanation).some(sample => normalText(sample) === normalText(explanation));
  useEffect(() => {
    if (!reviewNumber) return;
    heading.current?.focus({ preventScroll: true });
    heading.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, [reviewNumber]);

  return <>
    <Prompt lang={lang} />
    <label className={styles.field}>{he ? "איך הייתם פותרים את זה?" : "How would you solve this?"}
      <textarea data-muxi-control="guest-explain-input" value={draft} maxLength={3000} dir="auto"
        placeholder={he ? "איך מתחילים, ומה מעדכנים בכל צעד?" : "How do you start and what changes at each step?"}
        onChange={event => { setDraft(event.target.value); setReviewNumber(0); }} /></label>
    <div className={styles.actions}>
      <button type="button" data-muxi-control="guest-explain-fill" onClick={() => { setDraft(sampleExplanation[lang]); setReviewNumber(0); }}>
        <Pencil size={15} />{he ? "מילוי תשובה לדוגמה" : "Fill in a sample answer"}</button>
      <button type="button" className="primary" data-muxi-control="guest-explain-submit" disabled={!draft.trim()} onClick={() => {
        onExplanationChange(draft.trim()); setReviewNumber(number => number + 1); onAction("explanation-reviewed");
      }}>{he ? "שליחה וקבלת משוב לדוגמה" : "Submit for sample feedback"}</button>
    </div>
    {showReview && <section className={styles.review} data-muxi-control="guest-software-feedback">
      <h3 tabIndex={-1} ref={heading}>{he ? "המשוב על הסבר הדוגמה" : "Feedback on the sample explanation"}</h3>
      <p className={styles.note}>{he ? "מוקסי מציג משוב שהוכן מראש על תשובת הדוגמה." : "Muxi is showing feedback written in advance for the sample answer."}</p>
      {!matchesSample && <div className={styles.compare}>
        <h4>{he ? "ההסבר ששלחתם" : "Your submitted explanation"}</h4><blockquote dir="auto"><BidiText>{explanation}</BidiText></blockquote>
        <h4>{he ? "תשובת הדוגמה שקיבלה את המשוב" : "Sample answer being reviewed"}</h4><blockquote><BidiText>{sampleExplanation[lang]}</BidiText></blockquote>
      </div>}
      <SampleReview lang={lang} band="PARTIAL" />
    </section>}
  </>;
}

function CodeDemo({ lang, explanation, onAction }: Pick<Props, "lang" | "explanation" | "onAction">) {
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState(starterMaximum);
  const [result, setResult] = useState<MaximumCheck | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const region = useId();
  const he = lang === "he";
  useEffect(() => {
    if (!result) return;
    heading.current?.focus({ preventScroll: true });
    heading.current?.scrollIntoView({ block: "start", behavior: "instant" });
  }, [result]);

  function edit(value: string) { setCode(value); setResult(null); }
  function check() {
    const next = checkMaximumExample(code);
    setResult(next);
    if (next.supported && next.correct) onAction("code-reviewed");
  }
  return <>
    <Prompt lang={lang} />
    <details className={styles.prior}><summary>{explanation ? (he ? "ההסבר מהתחנה הקודמת" : "Your previous explanation") : (he ? "ההסבר לדוגמה" : "Sample explanation")}</summary>
      <blockquote dir="auto"><BidiText>{explanation || sampleExplanation[lang]}</BidiText></blockquote></details>
    <p><BidiText>{he ? "שנו את שורת האתחול של best. בחרו ערך מתוך המערך כדי שהפונקציה תעבוד גם כשהמספרים שליליים." : "Change the initializer for best. Choose a value from the array so the function also works when all its values are negative."}</BidiText></p>
    <button type="button" data-muxi-control="guest-code-open" aria-controls={region} aria-expanded={open} onClick={() => setOpen(v => !v)}>
      <CodeXml size={16} />{he ? (open ? "סגירת עורך הקוד" : "פתיחת עורך הקוד") : (open ? "Close code editor" : "Open code editor")}{open ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</button>
    <div id={region} hidden={!open}>
      {open && <div className={styles.editor}>
        <div dir="ltr"><CodeEditor value={code} onChange={edit} language="c" disabled={false} label={he ? "קוד למציאת המקסימום" : "Find the maximum in C"} /></div>
        <p className={styles.note} id="code-keyboard-help">{he ? "העורך מקבל קוד C. ההדגמה בודקת את שורת האתחול בתוך הפונקציה הנתונה." : "Edit the C code. The demo checks the initializer inside this function."}</p>
        <div className={styles.actions}>
          <button type="button" data-muxi-control="guest-code-fix" onClick={() => edit(fixedMaximum)}>{he ? "טעינת התיקון של מוקסי" : "Load Muxi’s repair"}</button>
          <button type="button" className="primary" data-muxi-control="guest-code-submit" disabled={!code.trim()} onClick={check}>{he ? "בדיקת הקוד וקבלת משוב" : "Check code and show feedback"}</button>
        </div></div>}
    </div>
    {result && <section className={styles.review} data-muxi-control="guest-software-feedback">
      <h3 ref={heading} tabIndex={-1}>{he ? "תוצאות בדיקת הקוד" : "Code check results"}</h3>
      {!result.supported ? <p>{he ? "בהדגמה אפשר להחליף את הערך שמאתחל את best במספר או באיבר מהמערך. החזירו את שאר הפונקציה לדוגמה או טענו את התיקון של מוקסי." : "This demo accepts a number or an array element as the initializer for best. Restore the rest of the sample function or load Muxi’s repair."}</p> :
        <>
          <table className={styles.cases}><caption>{he ? "בדיקות לשורת האתחול" : "Test cases for the initializer"}</caption>
            <thead><tr><th>{he ? "מערך" : "Array"}</th><th>{he ? "צפוי" : "Expected"}</th><th>{he ? "התקבל" : "Result"}</th></tr></thead>
            <tbody>{result.cases.map((test, index) => <tr key={index}><td><code dir="ltr">[{test.input.join(", ")}]</code></td><td><bdi dir="ltr">{test.expected}</bdi></td>
              <td data-pass={test.actual === test.expected}><bdi dir="ltr">{test.actual ?? (he ? "חריגה מהמערך" : "Out of bounds")}</bdi> {test.actual === test.expected ? "✓" : "✕"}</td></tr>)}</tbody>
          </table>
          {result.correct ? <>
            <p className={styles.note}>{he ? "כל הבדיקות עברו. הנה המשוב לדוגמה על הפונקציה המתוקנת." : "Every check passed. Here is the prepared feedback on the corrected function."}</p>
            <SampleReview lang={lang} band="STRONG" />
          </> : <p role="status">{he ? "בדקו באיזו שורה התוצאה שונה מהצפוי. איזה ערך התחלתי יכסה את המקרה הזה?" : "Find the row where the result differs from the expected value. Which initializer would cover that case?"}</p>}
        </>}
    </section>}
  </>;
}

export function GuestSoftwareDemo(props: Props) {
  return <section className={styles.root} dir={props.lang === "he" ? "rtl" : "ltr"} data-muxi-target={props.station}>
    {props.station === "guest-explain" ? <ExplanationDemo {...props} /> : <CodeDemo {...props} />}
  </section>;
}
