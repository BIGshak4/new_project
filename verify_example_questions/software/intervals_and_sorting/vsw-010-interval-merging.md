# VSW-010 — Interval overlap and merging

**כותרת מקורית:** בדיקת חפיפת טווחים (Interval Overlap & Merging)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Intervals and sorting / טווחים ומיון |
| Company label from supplied text | Google |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתונה רשימה של מקטעי זיכרון מוקצים המיוצגים כצמדי `[start, end]`. כתוב אלגוריתם הממזג את כל המקטעים החופפים. מהי סיבוכיות הזמן והמקום, ומדוע מיון מוקדם הוא הגישה האופטימלית?

## Question — English translation

You are given allocated memory regions represented as pairs [start, end]. Write an algorithm that merges all overlapping regions. What are its time and space complexities, and why is sorting first the optimal approach?

## מה בודקים — לפי הטקסט המקורי

ניהול זיכרון, עבודה עם מערכים ומיון, וטיפול יסודי במקרי קצה (מקטעים נושקים או מוכלים).

## Assessed skills — English translation

Memory management, arrays and sorting, and careful handling of boundary cases such as touching or contained intervals.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר טווחים סגורים או חצי פתוחים, איחוד טווחים נושקים, סדר הפלט ושינוי הקלט. מיון וסריקה הם גישה כללית בזמן O(n log n); טענת אופטימליות דורשת הנחות, ובקלט שכבר ממוין אפשר לסרוק בזמן ליניארי.

## Editorial review notes — separate from the original question

Define closed versus half-open intervals, whether touching intervals merge, output ordering, and whether input may be mutated. Sort-and-scan is a general O(n log n) approach; optimality requires assumptions and already sorted input admits a linear scan.

## Provenance / מקור

Supplied Hebrew collection, software question 10. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
