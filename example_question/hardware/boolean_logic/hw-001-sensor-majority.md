# HW-001 — Two-out-of-three sensor vote

**כותרת בעברית:** הכרעת רוב בין שלושה חיישנים

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Boolean logic / אלגברה בוליאנית |
| Difficulty | 2/10 (provisional) |
| Estimated time | 5 minutes |
| Format | truth_table |
| Modes | quick |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Three one-bit sensors A, B, C are 1 when they detect a fault. Assert alarm if at least two sensors are 1. Give all eight truth-table rows and a simplified Boolean expression. Explain why XOR of the three inputs is not sufficient.

## שאלה — עברית

שלושה חיישנים של ביט אחד, A, B, C, מחזירים 1 כאשר הם מזהים תקלה. יש להפעיל alarm כאשר לפחות שני חיישנים מחזירים 1. כתבו את כל שמונה שורות טבלת האמת וביטוי בוליאני מצומצם. הסבירו מדוע XOR של שלושת הקלטים אינו מספיק.

## Hint — English

List the three possible pairs of asserted sensors.

## רמז — עברית

רשמו את שלושת הזוגות האפשריים של חיישנים פעילים.

## Reference solution — English

alarm = (A & B) | (A & C) | (B & C). For ABC from 000 through 111 the outputs are 0,0,0,1,0,1,1,1. XOR detects odd parity, including a single asserted sensor, and rejects two asserted sensors.

## כיוון פתרון — עברית

הביטוי הוא alarm = (A & B) | (A & C) | (B & C). עבור ABC מ־000 עד 111 הפלטים הם 0,0,0,1,0,1,1,1. פעולת XOR מזהה זוגיות אי־זוגית, ולכן מפעילה אזעקה גם לחיישן יחיד ואינה מפעילה אותה לשני חיישנים.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: digital logic topic catalog](https://hdlbits.01xz.net/wiki/Problem_sets)
