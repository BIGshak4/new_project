"use client";

import { useState } from "react";
import { Monitor, Smartphone, ExternalLink } from "lucide-react";
import styles from "./lab.module.css";
import { studioDirections } from "../studio-preview/directions";

const originalDirections = [
  { id: "studio", name: "סטודיו", description: "מרחב לימוד חם ושקט. לבן שבור וירוק מרווה, עם מקום נדיב לשאלה ולמחשבה.", tradeoff: "מתאים לתרגול יומי רגוע; מציג פחות מידע בבת אחת." },
  { id: "play", name: "מגרש אימונים", description: "אופי קליל וחי. ירוק ליים, צורות רכות וניסוי לוגי קטן שמגיב למגע.", tradeoff: "מתאים לתרגולים קצרים ולהרגל יומי; פחות רשמי באופי שלו." },
  { id: "index", name: "הספרייה", description: "המידע מוביל. ארגמן, טיפוגרפיה עריכתית ורשימת שאלות רחבה שקל לסרוק.", tradeoff: "מתאים למי שיודע מה הוא מחפש; פחות מכוון את הלומד לצעד הבא." },
  { id: "focus", name: "פוקוס", description: "השאלה וסביבת הפתרון באותו מסך. רקע בהיר, סגול מאופק ומינימום הסחות.", tradeoff: "מתאים לתרגול ארוך ומעמיק; פחות מדגיש את חוויית הקהילה וההתקדמות." },
  { id: "trail", name: "הדרך", description: "מסלול לימוד אישי במרכז. משמש, ירוק יער וצעדים שמזמינים להמשיך.", tradeoff: "מתאים לליווי לאורך זמן; דורש תוכנית למידה טובה מאחורי העיצוב." },
];

export default function DesignLab() {
  const [collection, setCollection] = useState<"studio" | "original">("studio");
  const [selected, setSelected] = useState(0);
  const [phone, setPhone] = useState(false);
  const [motion, setMotion] = useState(true);
  const [current, setCurrent] = useState(false);
  const directions = collection === "studio" ? studioDirections : originalDirections;
  const direction = directions[selected] ?? directions[0];
  const url = current ? "/?view=library" : `/${collection === "studio" ? "studio-preview" : "design-preview"}?variant=${direction.id}&motion=${motion ? "1" : "0"}`;
  function changeCollection(next: "studio" | "original") { setCollection(next); setSelected(0); setCurrent(false); }
  return <main className={styles.lab}>
    <div className={styles.controls}>
      <div className={styles.heading}><div><h1>{collection === "studio" ? "עשרה כיוונים חדשים לסטודיו" : "חמש ההצעות הראשונות"}</h1><p>בחרו עיצוב, נסו אותו והשוו גם בטלפון. האתר הראשי עדיין בעיצוב הקיים.</p></div><a href="/?view=library">חזרה לאתר</a></div>
      <nav className={styles.collections} aria-label="סדרת עיצובים"><button aria-pressed={collection === "studio"} onClick={() => changeCollection("studio")}>סדרת הסטודיו · 10 חדשים</button><button aria-pressed={collection === "original"} onClick={() => changeCollection("original")}>סטודיו המקורי וההצעות הקודמות</button></nav>
      <nav className={styles.picker} aria-label="בחירת עיצוב">{directions.map((item, i) => <button key={item.id} type="button" aria-pressed={!current && i === selected} onClick={() => { setSelected(i); setCurrent(false); }}>{item.name}</button>)}</nav>
      <div className={styles.detail}><div><p>{current ? "האתר הפעיל שלכם — עם החשבון והנתונים האמיתיים. פעולות כאן נשמרות כרגיל." : direction.description}</p><p className={styles.tradeoff}>{current ? "בחרו אחד מהעיצובים כדי לחזור להדמיה." : direction.tradeoff}</p></div><div className={styles.tools}>
        <button type="button" aria-pressed={!phone} aria-label="תצוגת מחשב" onClick={() => setPhone(false)}><Monitor size={18} /></button>
        <button type="button" aria-pressed={phone} aria-label="תצוגת טלפון ברוחב 390 פיקסלים" onClick={() => setPhone(true)}><Smartphone size={18} /></button>
        <label><input type="checkbox" checked={motion} onChange={e => setMotion(e.target.checked)} /> תנועה</label>
        <label><input type="checkbox" checked={current} onChange={e => setCurrent(e.target.checked)} /> האתר הקיים</label>
        <a href={url} target="_blank" rel="noreferrer">מסך מלא <ExternalLink size={15} /></a>
      </div></div>
    </div>
    <div className={`${styles.stage} ${phone ? styles.phone : ""}`}>
      <iframe key={`${direction.id}-${motion}-${current}`} title={`${current ? "האתר הקיים" : `הדמיית ${direction.name}`}${phone ? " — טלפון" : ""}`} src={url} />
    </div>
    <p className={styles.caption}>{current ? "זה האתר הפעיל, עם החשבון והנתונים האמיתיים שלכם. פעולות כאן נשמרות כרגיל." : "אפשר לסנן שאלות, לפתוח תרגול לדוגמה ולנסות את הרכיב הלוגי. כל התוכן וההתקדמות בהדמיות הם להמחשה בלבד; דבר לא נשמר בחשבון."}</p>
  </main>;
}
