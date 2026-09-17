# VSW-001 — Population count / Hamming weight

**כותרת מקורית:** ספירת ביטים דולקים (Popcount / Hamming Weight)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | Apple |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

כתוב פונקציה יעילה ב-C המקבלת מספר שלם חיובי של 32 ביט ומחזירה את מספר הביטים שערכם '1'. ממש פתרון של $O(\text{number of set bits})$ באמצעות הטריק של `n & (n - 1)`. כיצד תבצע זאת ב-$O(1)$ באמצעות לוח חיפוש (Lookup Table)?

## Question — English translation

Write an efficient C function that receives a positive 32-bit integer and returns the number of bits equal to 1. Implement an O(number of set bits) solution using n & (n - 1). How would you implement it in O(1) using a lookup table?

## מה בודקים — לפי הטקסט המקורי

שליטה בפעולות בינאריות וטרייד-אוף בין זיכרון לחישוב.

## Assessed skills — English translation

Mastery of binary operations and memory-versus-computation trade-offs.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר טיפוס ללא סימן וטיפול באפס. זמן O(1) עם lookup table מניח רוחב קבוע של 32 ביטים; טבלה בת 256 ערכים דורשת ארבע גישות. יש להתייחס להכנה ולזיכרון הטבלה.

## Editorial review notes — separate from the original question

State unsigned input type and treatment of zero. Lookup-table O(1) assumes fixed 32-bit width; a 256-entry byte table uses four lookups. Account for preprocessing and table memory.

## Provenance / מקור

Supplied Hebrew collection, software question 1. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
