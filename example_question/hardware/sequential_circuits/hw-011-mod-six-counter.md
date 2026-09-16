# HW-011 — Enabled modulo-six counter

**כותרת בעברית:** מונה מודולו שש עם הפעלה

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Sequential circuits / מעגלים סינכרוניים |
| Difficulty | 4/10 (provisional) |
| Estimated time | 10 minutes |
| Format | hdl |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Design a positive-edge counter q that cycles 0,1,2,3,4,5,0 while enable=1 and holds while enable=0. Reset is synchronous, active high, and has priority. If q somehow equals 6 or 7, recover to 0 at the next edge even when enable=0. Give next-state logic and the trace from q=4 for enable samples 1,0,1,1 with reset=0.

## שאלה — עברית

תכננו מונה q הפועל בחזית עולה ועובר בין 0,1,2,3,4,5,0 כאשר enable=1, ושומר ערך כאשר enable=0. האיפוס סינכרוני, פעיל בגבוה ובעל עדיפות. אם q מגיע ל־6 או 7, יש לחזור ל־0 בחזית הבאה גם אם enable=0. כתבו לוגיקת מצב הבא ואת העקבה החל מ־q=4 עבור ערכי enable של 1,0,1,1 כאשר reset=0.

## Hint — English

Treat invalid states separately from normal counting.

## רמז — עברית

הפרידו טיפול במצבים לא חוקיים מהספירה הרגילה.

## Reference solution — English

Use three flip-flops. Priority: reset -> 0; q>=6 -> 0; enabled -> (q==5 ? 0 : q+1); otherwise hold. Values after the four edges are 5,5,0,1. Recovery is above enable in priority.

## כיוון פתרון — עברית

נדרשים שלושה flip-flops. סדר העדיפויות: איפוס לאפס; התאוששות לאפס אם q>=6; אם מופעל, מעבר לאפס מ־5 או הגדלה באחד; אחרת שמירה. הערכים אחרי ארבע החזיתות הם 5,5,0,1. ההתאוששות קודמת להפעלה.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: bounded counter background](https://hdlbits.01xz.net/wiki/Count10)
