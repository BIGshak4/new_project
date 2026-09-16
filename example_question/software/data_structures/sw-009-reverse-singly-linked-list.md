# SW-009 — Reverse a linked list in place

**כותרת בעברית:** היפוך רשימה מקושרת במקום

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

Given the head of a finite, acyclic singly linked list, reverse the links in place and return the new head. Use O(n) time and O(1) extra space without recursion or new nodes. Show pointer updates and explain empty and one-node lists. Preserve all nodes.

## שאלה — עברית

נתון ראש של רשימה מקושרת חד־כיוונית, סופית וללא מעגלים. הפכו את הקישורים במקום והחזירו את הראש החדש. השתמשו בזמן O(n) ובזיכרון נוסף O(1), ללא רקורסיה או צמתים חדשים. הציגו עדכון מצביעים והסבירו רשימה ריקה ורשימה של צומת אחד. יש לשמר את כל הצמתים.

## Hint — English

Preserve access to the remaining list before reversing a link.

## רמז — עברית

שמרו גישה לשאר הרשימה לפני הפיכת הקישור.

## Reference solution — English

Initialize prev=null,curr=head. Repeatedly save next=curr.next, assign curr.next=prev, then prev=curr and curr=next. Return prev. Saving next before overwriting the link preserves the unprocessed suffix. Empty returns null; one node returns that node with next=null.

## כיוון פתרון — עברית

מאתחלים prev=null,curr=head. בכל צעד שומרים next=curr.next, מבצעים curr.next=prev ואז prev=curr ו־curr=next. מחזירים prev. שמירת next לפני דריסת הקישור שומרת גישה לשאר הרשימה. רשימה ריקה מחזירה null; צומת יחיד מוחזר עם next=null.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [OpenDSA: list representations](https://opendsa.org/OpenDSA/Books/Catalog/html/ListIntro.html)
