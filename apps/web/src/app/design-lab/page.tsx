"use client";

import { useState } from "react";
import { Monitor, Smartphone, ExternalLink } from "lucide-react";
import styles from "./lab.module.css";
import { studioDirections } from "../studio-preview/directions";
import { conceptDirections } from "../concept-preview/directions";
import { siteDirections, type Screen } from "../site-preview/data";

const originalDirections = [
  {
    id: "studio",
    name: "סטודיו",
    description:
      "מרחב לימוד חם ושקט. לבן שבור וירוק מרווה, עם מקום נדיב לשאלה ולמחשבה.",
    tradeoff: "מתאים לתרגול יומי רגוע; מציג פחות מידע בבת אחת.",
  },
  {
    id: "play",
    name: "מגרש אימונים",
    description:
      "אופי קליל וחי. ירוק ליים, צורות רכות וניסוי לוגי קטן שמגיב למגע.",
    tradeoff: "מתאים לתרגולים קצרים ולהרגל יומי; פחות רשמי באופי שלו.",
  },
  {
    id: "index",
    name: "הספרייה",
    description:
      "המידע מוביל. ארגמן, טיפוגרפיה עריכתית ורשימת שאלות רחבה שקל לסרוק.",
    tradeoff: "מתאים למי שיודע מה הוא מחפש; פחות מכוון את הלומד לצעד הבא.",
  },
  {
    id: "focus",
    name: "פוקוס",
    description:
      "השאלה וסביבת הפתרון באותו מסך. רקע בהיר, סגול מאופק ומינימום הסחות.",
    tradeoff:
      "מתאים לתרגול ארוך ומעמיק; פחות מדגיש את חוויית הקהילה וההתקדמות.",
  },
  {
    id: "trail",
    name: "הדרך",
    description:
      "מסלול לימוד אישי במרכז. משמש, ירוק יער וצעדים שמזמינים להמשיך.",
    tradeoff: "מתאים לליווי לאורך זמן; דורש תוכנית למידה טובה מאחורי העיצוב.",
  },
];

export default function DesignLab() {
  const [collection, setCollection] = useState<
    "full" | "concept" | "studio" | "original"
  >("full");
  const [selected, setSelected] = useState(0);
  const [screen, setScreen] = useState<Screen>("home");
  const [phone, setPhone] = useState(false);
  const [motion, setMotion] = useState(true);
  const [current, setCurrent] = useState(false);
  const directions =
    collection === "full"
      ? siteDirections
      : collection === "concept"
        ? conceptDirections
        : collection === "studio"
          ? studioDirections
          : originalDirections;
  const direction = directions[selected] ?? directions[0];
  const url = current
    ? "/?view=library"
    : collection === "full"
      ? `/site-preview?style=${direction.id}&screen=${screen}&motion=${motion ? "1" : "0"}`
      : `/${collection === "concept" ? "concept-preview" : collection === "studio" ? "studio-preview" : "design-preview"}?variant=${direction.id}&motion=${motion ? "1" : "0"}`;
  function changeCollection(next: "full" | "concept" | "studio" | "original") {
    setCollection(next);
    setSelected(0);
    setCurrent(false);
  }
  return (
    <main className={styles.lab}>
      <div className={styles.controls}>
        <div className={styles.heading}>
          <div>
            <h1>
              {collection === "full"
                ? "חמישה סגנונות. כל חוויית האתר."
                : collection === "concept"
                  ? "עשרה עיצובים. עשרה עולמות."
                  : collection === "studio"
                    ? "הווריאציות הקודמות של הסטודיו"
                    : "חמש ההצעות הראשונות"}
            </h1>
            <p>
              {collection === "full"
                ? "עברו בין המסכים ונסו את התרגול. כל הפעולות מקומיות, ללא חיבור לשרת."
                : "צבע, טיפוגרפיה וחוויה שונים בכל כיוון. פתחו במסך מלא כדי להרגיש את העיצוב."}
            </p>
          </div>
          <a href="/?view=library">חזרה לאתר</a>
        </div>
        <nav className={styles.collections} aria-label="סדרת עיצובים">
          <button
            aria-pressed={collection === "full"}
            onClick={() => changeCollection("full")}
          >
            האתר המלא · 5
          </button>
          <button
            aria-pressed={collection === "concept"}
            onClick={() => changeCollection("concept")}
          >
            עולמות חדשים · 10
          </button>
          <button
            aria-pressed={collection === "studio"}
            onClick={() => changeCollection("studio")}
          >
            ניסויי הסטודיו הקודמים
          </button>
          <button
            aria-pressed={collection === "original"}
            onClick={() => changeCollection("original")}
          >
            חמש ההצעות הראשונות
          </button>
        </nav>
        <nav
          className={`${styles.picker} ${collection === "full" ? `${styles.colorPicker} ${styles.fullPicker}` : collection === "concept" ? styles.colorPicker : ""}`}
          aria-label="בחירת עיצוב"
        >
          {directions.map((item, i) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={!current && i === selected}
              onClick={() => {
                setSelected(i);
                setCurrent(false);
              }}
            >
              {"palette" in item && (
                <span className={styles.swatches} aria-hidden="true">
                  {item.palette.map((color) => (
                    <i key={color} style={{ background: color }} />
                  ))}
                </span>
              )}
              {item.name}
            </button>
          ))}
        </nav>
        <div className={styles.detail}>
          <div>
            <p>
              {current
                ? "האתר הפעיל שלכם — עם החשבון והנתונים האמיתיים. פעולות כאן נשמרות כרגיל."
                : direction.description}
            </p>
            <p className={styles.tradeoff}>
              {current
                ? "בחרו אחד מהעיצובים כדי לחזור להדמיה."
                : direction.tradeoff}
            </p>
          </div>
          <div className={styles.tools}>
            <button
              type="button"
              aria-pressed={!phone}
              aria-label="תצוגת מחשב"
              onClick={() => setPhone(false)}
            >
              <Monitor size={18} />
            </button>
            <button
              type="button"
              aria-pressed={phone}
              aria-label="תצוגת טלפון ברוחב 390 פיקסלים"
              onClick={() => setPhone(true)}
            >
              <Smartphone size={18} />
            </button>
            <label>
              <input
                type="checkbox"
                checked={motion}
                onChange={(e) => setMotion(e.target.checked)}
              />{" "}
              תנועה
            </label>
            {collection !== "full" && (
              <label>
                <input
                  type="checkbox"
                  checked={current}
                  onChange={(e) => setCurrent(e.target.checked)}
                />{" "}
                האתר הקיים
              </label>
            )}
            {collection === "full" && (
              <label className={styles.screenPicker}>
                פתיחת מסך
                <select
                  aria-label="פתיחת מסך בסימולציה"
                  value={screen}
                  onChange={(e) => setScreen(e.target.value as Screen)}
                >
                  {[
                    ["home", "דף הבית"],
                    ["today", "היום שלי"],
                    ["library", "מאגר השאלות"],
                    ["practice", "פתרון שאלה"],
                    ["interview", "ראיון מדומה"],
                    ["progress", "התקדמות"],
                    ["history", "היסטוריה"],
                    ["saved", "שמורים"],
                    ["goal", "בחירת מטרה"],
                    ["profile", "פרופיל"],
                    ["auth", "כניסה והרשמה"],
                    ["help", "עזרה"],
                  ].map(([id, label]) => (
                    <option key={id} value={id}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <a href={url} target="_blank" rel="noreferrer">
              מסך מלא <ExternalLink size={15} />
            </a>
          </div>
        </div>
      </div>
      <div className={`${styles.stage} ${phone ? styles.phone : ""}`}>
        <iframe
          key={`${collection}-${direction.id}-${screen}-${motion}-${current}`}
          title={`${current ? "האתר הקיים" : `הדמיית ${direction.name}`}${phone ? " — טלפון" : ""}`}
          src={url}
        />
      </div>
      <p className={styles.caption}>
        {current
          ? "זה האתר הפעיל, עם החשבון והנתונים האמיתיים שלכם. פעולות כאן נשמרות כרגיל."
          : collection === "full"
            ? "סימולציה שלמה: ניווט, חיפוש, טיוטות, רמזים, קוד, מעגלים, תמונות ומשוב לדוגמה. המידע נשאר בדפדפן ומתאפס ברענון. באפשרות יון בהיר–כהה, כפתור השמש והירח נמצא בסרגל העליון."
            : "אפשר לבחור נושא, לפתוח תרגול לדוגמה ולנסות את הרכיב האינטראקטיבי. כל התוכן וההתקדמות בהדמיות הם להמחשה בלבד; דבר לא נשמר בחשבון."}
      </p>
    </main>
  );
}
