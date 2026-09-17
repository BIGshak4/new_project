# VHW-006 — Overlapping and non-overlapping sequence detection

**כותרת מקורית:** גלאי רצף (Sequence Detector) חופף ולא חופף

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Company label from supplied text | Intel |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

תכנן מכונת מצבים (FSM) שמזהה את הרצף `1011` בסדרת ביטים טורית. השווה בין מימוש Mealy למימוש Moore במונחי מספר המצבים, זמני התגובה, והרגישות לגליצ'ים בכניסה.

## Question — English translation

Design a finite state machine (FSM) that detects the sequence 1011 in a serial bit stream. Compare Mealy and Moore implementations in terms of state count, response timing, and sensitivity to input glitches.

## מה בודקים — לפי הטקסט המקורי

הבחנה ברורה בין Mealy ל-Moore, זיהוי חפיפות ברצפים, ותרגום נכון לטבלת מעברים.

## Assessed skills — English translation

A clear distinction between Mealy and Moore machines, recognition of overlapping sequences, and correct construction of a transition table.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

הכותרת מזכירה זיהוי חופף ולא חופף, אך גוף השאלה אינו דורש במפורש את שניהם. יש להגדיר מדיניות חפיפה ומועד דגימת הפלט לפני השוואת זמן תגובה ומספר מצבים.

## Editorial review notes — separate from the original question

The heading mentions overlapping and non-overlapping detection, but the prompt does not explicitly request both. Specify overlap policy and exactly when outputs are sampled before comparing latency and state count.

## Provenance / מקור

Supplied Hebrew collection, hardware question 6. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
