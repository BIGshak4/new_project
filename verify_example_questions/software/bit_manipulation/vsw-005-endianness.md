# VSW-005 — Detecting endianness

**כותרת מקורית:** בדיקת Endianness של מערכת

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | Intel |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

כתוב פונקציה קצרה ב-C הבודקת האם המעבד הנוכחי הוא Little-Endian או Big-Endian. כיצד תממש המרה יעילה של 32-bit Integer מ-Little ל-Big Endian (Byte Swap)?

## Question — English translation

Write a short C function that detects whether the current processor is little-endian or big-endian. How would you efficiently convert a 32-bit integer from little-endian to big-endian representation using a byte swap?

## מה בודקים — לפי הטקסט המקורי

הבנת ארגון זיכרון ופוינטרים, המרת טיפוסים (Casting).

## Assessed skills — English translation

Memory organization, pointers, and casting.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר בייט בן שמונה ביטים וזמינות uint32_t, להשתמש בגישה חוקית דרך טיפוס תו לייצוג האובייקט ולהבחין בין byte swap לפרשנות בייטים בסריאליזציה. לא כל ארכיטקטורה אפשרית היא בהכרח little-endian או big-endian טהורה.

## Editorial review notes — separate from the original question

Specify eight-bit bytes and uint32_t availability, use permitted character access to inspect object representation, and distinguish byte swapping from interpreting serialized bytes. Do not assume every possible architecture is purely little- or big-endian.

## Provenance / מקור

Supplied Hebrew collection, software question 5. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
