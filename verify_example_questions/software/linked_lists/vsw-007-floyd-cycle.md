# VSW-007 — Floyd's cycle detection

**כותרת מקורית:** זיהוי מעגל ברשימה מקושרת (Floyd's Cycle Detection)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Linked lists / רשימות מקושרות |
| Company label from supplied text | Qualcomm |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתונה רשימה מקושרת יחידה. קבע האם קיים בה מעגל מבלי לשנות את הרשימה ובסיבוכיות זיכרון של $O(1)$. אם קיים מעגל, מצא את הצומת שבו המעגל מתחיל.

## Question — English translation

Given a singly linked list, determine whether it contains a cycle without modifying the list and using O(1) extra space. If a cycle exists, find the node where it begins.

## מה בודקים — לפי הטקסט המקורי

אלגוריתם שני מצביעים (Tortoise and Hare) וחשיבה מתמטית על מרחקים.

## Assessed skills — English translation

The two-pointer tortoise-and-hare algorithm and mathematical reasoning about distances.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להבהיר שפגישת מצביעים מבוססת על זהות צומת ולא על שוויון הערכים שבו. יש לכלול רשימה ריקה, צומת יחיד ומעגל עצמי ולהסביר עצירה ללא מעגל.

## Editorial review notes — separate from the original question

Specify that node identity, not stored value equality, determines pointer meetings. Include empty, one-node, and self-loop cases, and explain termination when no cycle exists.

## Provenance / מקור

Supplied Hebrew collection, software question 7. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
