# HW-014 — Overlapping 1011 detector

**כותרת בעברית:** גלאי לרצף חופף 1011

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Difficulty | 5/10 (provisional) |
| Estimated time | 15 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Design a Mealy FSM that consumes one input bit per cycle and detects the suffix 1011. Overlap is allowed. Give state meanings and the full transition/output table. For stream 1011011, identify detections using one-based bit positions. The output is evaluated from the current state and current input before the state update.

## שאלה — עברית

תכננו Mealy FSM הקולט ביט אחד בכל מחזור ומזהה סיומת 1011, כולל חפיפה. הגדירו משמעות לכל מצב וכתבו טבלת מעברים ופלט מלאה. עבור הזרם 1011011 ציינו באילו מיקומי ביט מתרחשים זיהויים, כשהספירה מתחילה ב־1. הפלט מחושב מהמצב והקלט הנוכחיים לפני עדכון המצב.

## Hint — English

Track the longest suffix that is also a prefix of the target.

## רמז — עברית

עקבו אחר הסיומת הארוכה ביותר שהיא גם קידומת של הרצף המבוקש.

## Reference solution — English

States S0,S1,S2,S3 represent matched prefixes empty,1,10,101. On inputs 0/1 respectively, next states are S0/S1, S2/S1, S0/S3, S2/S1. Only S3 with input 1 emits 1. Detections are at positions 4 and 7; keeping S1 after a detection preserves overlap.

## כיוון פתרון — עברית

המצבים S0,S1,S2,S3 מייצגים קידומות ריקה,1,10,101. עבור הקלטים 0/1 המצבים הבאים הם בהתאמה S0/S1, S2/S1, S0/S3, S2/S1. רק במצב S3 עם קלט 1 הפלט הוא 1. הזיהויים במיקומים 4 ו־7; מעבר ל־S1 לאחר זיהוי שומר את החפיפה.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: sequence recognition background](https://hdlbits.01xz.net/wiki/Fsm_hdlc)
