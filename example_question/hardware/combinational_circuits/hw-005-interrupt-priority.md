# HW-005 — Interrupt priority with a valid flag

**כותרת בעברית:** קידוד עדיפות לפסיקות

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Combinational circuits / מעגלים קומבינטוריים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | hdl |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Four interrupt requests are req[3:0], with req[3] highest priority. Design a combinational encoder returning a two-bit index and valid. If no request is active, require valid=0 and index=0. Give logic or HDL, and outputs for req=0101, 1010, and 0000.

## שאלה — עברית

ארבע בקשות פסיקה מופיעות ב־req[3:0], כאשר req[3] בעלת העדיפות הגבוהה ביותר. תכננו מקודד קומבינטורי המחזיר index בן שני ביטים ואות valid. אם אין בקשה פעילה, נדרש valid=0 וגם index=0. כתבו לוגיקה או קוד תיאור חומרה וחשבו פלט עבור req=0101, 1010, 0000.

## Hint — English

An ordered if/else chain makes priority explicit.

## רמז — עברית

שרשרת if/else מסודרת מגדירה את העדיפות במפורש.

## Reference solution — English

Check bits in order 3,2,1,0 and default both outputs to zero. The outputs (valid,index) are (1,2), (1,3), (0,0). valid distinguishes no request from a request on bit 0.

## כיוון פתרון — עברית

בודקים לפי הסדר 3,2,1,0 ומגדירים ברירת מחדל אפס לשני הפלטים. הזוגות (valid,index) הם (1,2), (1,3), (0,0). אות valid מבדיל בין היעדר בקשה לבין בקשה בביט 0.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: priority encoder background](https://hdlbits.01xz.net/wiki/Always_case2)
