# VSW-008 — Compact bitset / bitmap

**כותרת מקורית:** מימוש מנגנון Bitset / Bitmap קומפקטי

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | Microsoft |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

ממש מחלקה או מבנה המנהל מערך בוליאני של מיליון דגלים (Flags) במינימום זיכרון. תמוך בפעולות `set(index)`, `clear(index)`, ו-`test(index)` בסיבוכיות זמן של $O(1)$.

## Question — English translation

Implement a class or structure that manages a Boolean array of one million flags using minimal memory. Support set(index), clear(index), and test(index) in O(1) time.

## מה בודקים — לפי הטקסט המקורי

מיפוי אינדקסים למערך של `uint32_t`, פעולות מודולו והזזה ברמת המכונה.

## Assessed skills — English translation

Mapping indices into a uint32_t array and using machine-level modulo and shift operations.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר אינדקסים חוקיים מ־0 עד 999999 וטיפול בקלט לא חוקי. המפה עצמה דורשת 1,000,000 ביטים, כלומר 125,000 בייטים בני שמונה ביטים או 31,250 מילים מסוג uint32_t, ללא מטא־נתונים ויישור. יש להגדיר אם הפעולות מקביליות.

## Editorial review notes — separate from the original question

Define valid indices 0 through 999999 and behavior on invalid input. The raw bitmap is 1,000,000 bits = 125,000 eight-bit bytes = 31,250 uint32_t words, excluding metadata and alignment. State whether operations are concurrent.

## Provenance / מקור

Supplied Hebrew collection, software question 8. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
