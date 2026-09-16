# HW-007 — Rotate versus logical shift

**כותרת בעברית:** סיבוב לעומת הזזה לוגית

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Combinational circuits / מעגלים קומבינטוריים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 7 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

An eight-bit combinational unit performs either rotate-right or logical shift-right by k, where 0<=k<=7. For x=10110100 and k=3, give both outputs. Describe a MUX-stage implementation for variable k and explain where the discarded bits go in each mode.

## שאלה — עברית

יחידה קומבינטורית ברוחב שמונה ביטים מבצעת rotate-right או logical shift-right במספר מקומות k, כאשר 0<=k<=7. עבור x=10110100 ו־k=3, חשבו את שני הפלטים. תארו מימוש באמצעות שלבי MUX עבור k משתנה והסבירו מה קורה לביטים שיוצאים מצד ימין בכל מצב.

## Hint — English

Separate the three low bits from the remaining five.

## רמז — עברית

הפרידו את שלושת הביטים הנמוכים מחמשת הביטים האחרים.

## Reference solution — English

Rotate gives 10010110; logical shift gives 00010110. Three conditional stages shift/rotate by 1,2,4 under k[0],k[1],k[2]. Rotation wraps low bits into the high positions; logical shift inserts zeros.

## כיוון פתרון — עברית

סיבוב נותן 10010110; הזזה לוגית נותנת 00010110. שלושה שלבים מותנים מבצעים הזזה או סיבוב ב־1,2,4 לפי k[0],k[1],k[2]. בסיבוב הביטים הנמוכים חוזרים לצד הגבוה; בהזזה לוגית נכנסים אפסים.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: rotation background](https://hdlbits.01xz.net/wiki/Rotate100)
