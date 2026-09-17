# VSW-006 — Stack with constant-time minimum

**כותרת מקורית:** מימוש מחסנית עם תמיכה ב-Min ב-$O(1)$ (Min-Stack)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Queues and stacks / תורים ומחסניות |
| Company label from supplied text | Mobileye |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

ממש מבנה נתונים של מחסנית (Stack) התומך בפעולות `push`, `pop`, ו-`getMin` כולן בסיבוכיות זמן של $O(1)$. כיצד תמזער את תקורה הזיכרון (Memory Overhead)?

## Question — English translation

Implement a stack supporting push, pop, and getMin, all in O(1) time. How would you minimize memory overhead?

## מה בודקים — לפי הטקסט המקורי

הבנה של מבני נתונים בסיסיים ושימוש במחסנית עזר או קידוד הפרשים.

## Assessed skills — English translation

Fundamental data structures and the use of an auxiliary stack or difference encoding.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר פעולות על מחסנית ריקה, מינימום שחוזר והנחות הקצאת זיכרון עבור O(1) במקרה הגרוע לעומת משוערך. קידוד הפרשים דורש טיפול בגלישה או טיפוס רחב יותר.

## Editorial review notes — separate from the original question

Define empty-stack behavior, duplicate minima, and allocation assumptions for worst-case versus amortized O(1). Difference encoding needs explicit overflow handling or a wider type.

## Provenance / מקור

Supplied Hebrew collection, software question 6. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
