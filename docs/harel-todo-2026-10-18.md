# מה נשאר להראל — 18 באוקטובר 2026

נכתב לשקד ולהראל. רשימת הפריטים הפתוחים בצד הממשק, לפי הסדר ששקד רוצה. המקור המלא של כל פריט, כולל החוזה המדויק מול השרת, הוא תור הראל בראש `backend/STATUS.md` (מספרי הפריטים זהים). צד השרת של כולם כבר חי ב־Render; אין כאן שינוי שרת.

| # | מה | למה עכשיו |
|---|---|---|
| 16 | **סוגריים סביב מונחים באנגלית בטקסט עברי** — תיקון ב־`bidi-text.tsx` (הקוד למטה) | באג גלוי בשאלות החיות; שקד ראה אותו היום |
| 11 | תוויות לתג `why`: `map` ו־`same_skill` | מופיעות כמילה גולמית בכרטיס השאלה הבאה |
| 15 | משפט „התשובה לא עוסקת בשאלה, ולכן אין עליה נקודות” כש־`submission.related === false` | השרת כבר מחזיר 0 נקודות; בלי המשפט זה נראה כמו באג |
| 12 | שאלה שנפתחה מתוצאת חיפוש נשלחת עם `source: "search"` | דוחות המסע סופרים אותה כ„מאגר” |
| 13 | כפתור „התחלה” בטבלת התוכנית מעביר את `interview_duration_min` ללובי | הלובי נפתח ב־30 דקות במקום באורך שהתוכנית התאימה ליום |
| 10 | הסרת תג „הועבר מאתמול” והמיון לפיו | השרת לא מעביר עוד פריטים; התג תמיד false |
| 14 | שדות בטיפוסים: `JobType.excluded_skills`, `SkillProgress.expired`, `Submission.related`, `InterviewTurn.related`; ואז הסרתם מ־`PENDING_IN_CLIENT` בבדיקת החוזה | בדיקת החוזה שומרת עליהם רק אחרי שהם בטיפוס |
| 7 | בורר הכניסה של ההרנס (`tools/screenshots/run.mjs` מחפש `.landing`) | ארבעת צילומי הכניסה מדולגים בכל ריצה |
| 9 | אופציונלי: שורת „לא חלק מסוג התפקיד: …” מתוך `JobType.excluded_skills` בהגדרת היעד או במאגר | הסבר למשתמש למה שאלות נעלמו אחרי החלפת תפקיד |

פתוחים מצד הראל עצמו (לא דורשים שרת): שני הדיווחים מהאייפון על ההכתבה (משימה 20), תוכן אמיתי לביקורות (23), בדיקת טלפון אמיתי (13).

**הטיוטות (242 השאלות של 3 באוקטובר):** עמוד לקריאה בלבד, לפי החלטת שקד הן אינן באתר ולא ייכנסו עד שיגיד אחרת. שקד משתף את הקישור כשירצה.

---

## 16 — סוגריים סביב מונחים באנגלית: התיקון המלא

**מה קורה.** הטקסטים במאגר תקינים (כל 68 השאלות, בשתי השפות, עם סוגריים מאוזנים). הבעיה ב־`apps/web/src/components/bidi-text.tsx`: הביטוי הרגולרי פותח „אי” LTR באות הראשונה ומרשה לו להסתיים ב־`)`. לכן `(unsigned)` מתפצל ל־`(` בתוך הריצה העברית ול־`unsigned)` בתוך האי. שני הסוגריים נמצאים בריצות כיווניות שונות, ואחד מהם מצויר הפוך בצד הלא נכון. אותו דבר ב־`[7:0]`, `(A OR B)`, `(0..255)`.

**התיקון.** משאירים את הביטוי הרגולרי ומאזנים את קצוות האי אחרי הפיצול:

```tsx
const RE = /([A-Za-z0-9][\x20-\x7E←-↔−]*[A-Za-z0-9)]|[A-Za-z0-9])/g;
const OPENER: Record<string, string> = { ")": "(", "]": "[" };

function islands(text: string): string[] {
  const parts = text.split(RE);                      // odd indexes are the LTR islands
  for (let i = 1; i < parts.length; i += 2) {
    let island = parts[i];
    // a closing bracket at the end without its opener inside goes back to the surrounding text
    while (island.length > 1 && OPENER[island.at(-1)!] && !island.slice(0, -1).includes(OPENER[island.at(-1)!])) {
      parts[i + 1] = island.at(-1) + parts[i + 1];
      island = island.slice(0, -1);
    }
    // an opening bracket right before the island whose closer is inside is pulled into it
    const before = parts[i - 1], opener = before.at(-1);
    if ((opener === "(" || opener === "[") && island.includes(opener === "(" ? ")" : "]")) {
      parts[i - 1] = before.slice(0, -1);
      island = opener + island;
    }
    parts[i] = island;
  }
  return parts;
}

export function BidiText({ children }: { children?: ReactNode }) {
  return <>{Children.map(children, child => typeof child !== "string" ? child
    : islands(child).map((part, i) => i % 2 ? <bdi key={i} dir="ltr">{part}</bdi> : part))}</>;
}
```

**בדיקות קבלה** (להוסיף ל־`tests/`): זוג סוגריים עוטף נשאר יחד בריצה העברית — `בלי סימן (unsigned) של` → `(` · `unsigned` · `)`; `הקלט [7:0] נכנס` → `[` · `7:0` · `]`; `רמה 3 (מתוך 5)` — ה־`)` נשאר עם העברית. סוגריים של פונקציה נשארים בתוך האי — `NAND(A, B)` שלם; `f(x) = 1` שלם; `Y = (A & B) | C` שלם. ללא שינוי: `AND`, `MSB`, `a, b`, `A→B`.

הרכיב משמש בכל מקום (כותרות, נוסחי שאלות, אפשרויות בחירה, הודעות, סיבות בתוכנית), ולכן מספיק מעבר צילומי מסך אחד על דף שאלה בעברית ברוחב טלפון כדי לאשר.
