# SW-007 — Fixed-capacity circular queue

**כותרת בעברית:** תור מעגלי בקיבולת קבועה

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Data structures / מבני נתונים |
| Difficulty | 4/10 (provisional) |
| Estimated time | 12 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Implement a single-threaded FIFO queue of capacity 4 using an array, a head index, and a size counter. Enqueue on a full queue must fail without overwriting; dequeue on empty must fail. Define the insertion index and updates. Trace enqueue 10,20,30; dequeue twice; enqueue 40,50,60. Give logical contents, head, and size, starting from head=0,size=0.

## שאלה — עברית

ממשו תור FIFO לתהליכון יחיד בקיבולת 4 באמצעות מערך, אינדקס head ומונה size. הכנסה לתור מלא נכשלת ללא דריסה; הוצאה מתור ריק נכשלת. הגדירו את אינדקס ההכנסה והעדכונים. עקבו אחרי הכנסת 10,20,30; שתי הוצאות; הכנסת 40,50,60. תנו תוכן לוגי, head ו־size, החל מ־head=0,size=0.

## Hint — English

The count distinguishes full and empty even when indices wrap.

## רמז — עברית

המונה מבדיל בין מלא לריק גם כשהאינדקסים נכרכים.

## Reference solution — English

Insert at (head+size)%4, then increment size if not full. Remove at head, set head=(head+1)%4 and decrement size if nonempty. Final logical contents [30,40,50,60], head=2,size=4; physical array [50,60,30,40]. Both operations are O(1).

## כיוון פתרון — עברית

מכניסים ב־(head+size)%4 ומגדילים size אם התור אינו מלא. מוציאים מ־head, מעדכנים head=(head+1)%4 ומקטינים size אם אינו ריק. לבסוף התוכן הלוגי [30,40,50,60], עם head=2,size=4; המערך הפיזי [50,60,30,40]. שתי הפעולות O(1).

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [OpenDSA: list representations](https://opendsa.org/OpenDSA/Books/Catalog/html/ListIntro.html)
