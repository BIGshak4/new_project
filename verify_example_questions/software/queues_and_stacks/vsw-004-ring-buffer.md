# VSW-004 — Ring buffer / circular queue

**כותרת מקורית:** מימוש תור מעגלי (Ring Buffer / Circular Queue)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Queues and stacks / תורים ומחסניות |
| Company label from supplied text | Amazon (Annapurna Labs) |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

ממש Circular Queue יעיל ב-C מעל מערך סטטי עבור תקשורת בין Producer ל-Consumer (ללא שימוש ב-Modulo `%` כדי למנוע חילוק חומרתי איטי – רמז: גודל מערך שהוא חזקה של 2 ומסכת ביטים `size - 1`).

## Question — English translation

Implement an efficient circular queue in C over a static array for communication between a producer and a consumer. Do not use the modulo operator (%) in order to avoid slow hardware division. Hint: use a power-of-two array size and the bit mask size - 1.

## מה בודקים — לפי הטקסט המקורי

כתיבת קוד Low-Level אופטימלי לדרייברים ו-Firmware.

## Assessed skills — English translation

Low-level code optimized for drivers and firmware.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר שימוש חד־תהליכוני או מקבילי, מספר יצרנים וצרכנים, טיפול במלא וריק, קיבולת וכללי גלישה. קוד C מקבילי דורש מודל סנכרון וסדר זיכרון. מודולו בחזקה קבועה של שתיים אינו חייב להפוך לחילוק חומרתי.

## Editorial review notes — separate from the original question

Specify single-threaded versus concurrent use, producer/consumer count, full/empty behavior, capacity convention, and overflow rules. Concurrent C code needs a defined synchronization/memory-order model. Modulo by a compile-time power of two need not compile to hardware division.

## Provenance / מקור

Supplied Hebrew collection, software question 4. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
