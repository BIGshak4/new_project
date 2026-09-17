# VHW-007 — Memory control / FIFO controller

**כותרת מקורית:** תכנון מכונת בקרת זיכרון / FIFO Controller

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Company label from supplied text | NVIDIA |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

תכנן מכונת מצבים לבקרת תור מעגלי (Synchronous FIFO). הגדר את המצבים עבור Empty, Full, Normal, Overflow ו-Underflow. כיצד תוודא שה-FSM לא נכנס למצב תקוע (Deadlock) במקרה של Soft Error (Bit flip)?

## Question — English translation

Design a state machine to control a circular queue (a synchronous FIFO). Define states for Empty, Full, Normal, Overflow, and Underflow. How would you ensure that the FSM does not become stuck in a deadlock after a soft error such as a bit flip?

## מה בודקים — לפי הטקסט המקורי

ארכיטקטורת FSM חסינה, Safe State Encoding (One-Hot vs. Gray vs. Binary), וטיפול בחריגות.

## Assessed skills — English translation

Robust FSM architecture, safe state encoding (one-hot versus Gray versus binary), and exception handling.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר עומק FIFO, קריאה וכתיבה בו־זמנית, האם שגיאות הן פולסים או דגלים נשמרים, ומודל תקלה. Empty/Full הם לעיתים דגלים נגזרים ולא מצבים נשמרים נפרדים. יש להגדיר אם התאוששות רשאית לאבד נתונים.

## Editorial review notes — separate from the original question

Define FIFO depth, simultaneous read/write behavior, whether overflow/underflow are pulses or sticky errors, and the fault model. Empty/full are often derived flags rather than separate stored FSM states. Specify whether recovery may discard buffered data.

## Provenance / מקור

Supplied Hebrew collection, hardware question 7. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
