# VHW-010 — Gray-code counter and state machine

**כותרת מקורית:** מונה Gray Code ומכונת מצבים

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Company label from supplied text | Marvell |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

תכנן FSM המייצר מונה Gray Code של 3 ביט. מדוע קוד גרי קריטי לתקשורת בין שעונים וב-Asynchronous FIFOs?

## Question — English translation

Design an FSM that generates a three-bit Gray-code counter. Why is Gray code critical for communication across clock domains and in asynchronous FIFOs?

## מה בודקים — לפי הטקסט המקורי

הבנת תופעת ה-Meta-stability במעבר ריבוי ביטים, ותכנון לוגי מותאם CDC.

## Assessed skills — English translation

Understanding metastability during multibit crossings and designing CDC-aware logic.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

קוד Gray אינו מבטל metastability. יש להפריד בין תכונת שינוי ביט יחיד לבין סנכרון ואילוצי הפרשי השהיה בין ביטים. לא כל מעבר של bus בין שעונים דורש קוד Gray.

## Editorial review notes — separate from the original question

Gray coding does not eliminate metastability. Distinguish the one-bit-change property from synchronization and bus-skew constraints. Not every multibit clock-domain crossing should use Gray code.

## Provenance / מקור

Supplied Hebrew collection, hardware question 10. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
