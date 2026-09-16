# HW-015 — Credit dispenser state machine

**כותרת בעברית:** מכונת מצבים לצבירת קרדיט

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Difficulty | 4/10 (provisional) |
| Estimated time | 12 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A dispenser costs 3 credits. Each cycle accepts a coin worth 1 or 2, or no coin; these events are mutually exclusive. Track credit 0,1,2. When the current credit plus the coin reaches or exceeds 3, assert dispense for that event, return any excess as change, and return credit to 0. Define a Mealy transition table, including outputs, and trace coins 2,2,1,2 from reset.

## שאלה — עברית

מכונה דורשת 3 יחידות קרדיט. בכל מחזור מתקבל מטבע של 1, מטבע של 2 או שאין מטבע; האירועים זרים זה לזה. עקבו אחר קרדיט 0,1,2. כאשר הקרדיט ועוד המטבע מגיעים לפחות ל־3, הפעילו dispense באותו אירוע, החזירו את העודף ב־change ואפסו את הקרדיט. כתבו טבלת Mealy מלאה עם פלטים ועקבה למטבעות 2,2,1,2 אחרי איפוס.

## Hint — English

Define outputs on transitions that cross the price threshold.

## רמז — עברית

הגדירו את הפלטים במעברים שחוצים את מחיר המוצר.

## Reference solution — English

No coin holds credit and emits (dispense,change)=(0,0). For a coin v, total=c+v: if total<3, next=total and outputs zero; otherwise next=0, dispense=1, change=total-3. The trace of (next credit,dispense,change) is (2,0,0),(0,1,1),(1,0,0),(0,1,0).

## כיוון פתרון — עברית

ללא מטבע שומרים קרדיט ומפיקים (dispense,change)=(0,0). עבור מטבע v מחשבים total=c+v: אם total<3 שומרים את הסכום והפלטים אפס; אחרת עוברים לאפס, מפעילים dispense ומחזירים total-3. העקבה (קרדיט הבא,dispense,change) היא (2,0,0),(0,1,1),(1,0,0),(0,1,0).

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [MIT 6.111: sequential assignments and FSMs](https://classes.csail.mit.edu/6.111/f2006/handouts/L06.pdf)
