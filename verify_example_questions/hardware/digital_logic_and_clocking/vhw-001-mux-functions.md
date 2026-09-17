# VHW-001 — Implementing functions with multiplexers

**כותרת מקורית:** מימוש פונקציות באמצעות Multiplexer

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Digital logic and clocking / לוגיקה ספרתית ושעונים |
| Company label from supplied text | NVIDIA |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

ממש שער XOR של 2 כניסות ($A, B$) תוך שימוש ב-MUX 2:1 אחד בלבד, ללא שערים נוספים (ניתן להשתמש בערכים קבועים '0' ו-'1' או במשתנים ככניסות נתונים ובקרת). כיצד תממש שער Full Adder באמצעות צמד רכיבי MUX 4:1?

## Question — English translation

Implement a two-input XOR gate (A, B) using only one 2:1 MUX and no additional gates. Constants 0 and 1, or the variables, may be used as data and select inputs. How would you implement a full adder using a pair of 4:1 MUX components?

## מה בודקים — לפי הטקסט המקורי

יכולת פישוט בוליאני, תפיסת MUX כטבלת אמת חומרתית, ויעילות שטח.

## Assessed skills — English translation

Boolean simplification, understanding a MUX as a hardware truth table, and area efficiency.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

החלק הראשון אינו ניתן למימוש ב־MUX רגיל 2:1 ללא פלט מהופך, כאשר כל פין יכול לקבל רק A, B, 0 או 1. בדיקה ממצה של כל 64 השמות הקלט מאשרת זאת. יש לאפשר קלט מהופך או רכיב נוסף, או לבקש במפורש הוכחת אי־אפשרות. גם בחלק על שני רכיבי MUX 4:1 יש להגדיר אם קלטים מהופכים זמינים.

## Editorial review notes — separate from the original question

The first part is not realizable with a standard non-inverting 2:1 MUX whose pins can receive only A, B, 0, or 1. Exhaustive enumeration of all 64 pin assignments confirms this. Allow an inverted input or another component, or explicitly ask the candidate to prove impossibility. The two-4:1-MUX full-adder part also needs a clear rule about availability of complemented inputs.

## Provenance / מקור

Supplied Hebrew collection, hardware question 1. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
