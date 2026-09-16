# HW-004 — Build an eight-input multiplexer

**כותרת בעברית:** בניית מרבב בעל שמונה קלטים

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Combinational circuits / מעגלים קומבינטוריים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Build an 8-to-1, one-bit MUX from 2-to-1 MUX cells only. Input D[k] must be selected when the three-bit select equals k. Draw or describe the tree, count cells, and identify the select bit used at each level. Assume equal cell delay t and ignore wire delays; what is the maximum input-to-output delay?

## שאלה — עברית

בנו MUX מסוג 8 ל־1, עם קלטים של ביט אחד, באמצעות תאי MUX מסוג 2 ל־1 בלבד. הקלט D[k] נבחר כאשר אות הבחירה בן שלושת הביטים שווה ל־k. תארו או ציירו את העץ, ספרו תאים וציינו איזה ביט בחירה משמש בכל רמה. הניחו השהיה t לכל תא והזניחו חיווט; מהי השהיית הקלט־פלט המרבית?

## Hint — English

Pair adjacent data inputs before combining pairs.

## רמז — עברית

חברו תחילה זוגות של קלטים סמוכים.

## Reference solution — English

Use four first-level cells controlled by s[0], two second-level cells by s[1], and one final cell by s[2]. Total 7 cells and 3t maximum data-path delay, assuming stable select signals.

## כיוון פתרון — עברית

ארבעה תאים ברמה הראשונה נשלטים בידי s[0], שניים ברמה השנייה בידי s[1], ותא אחרון בידי s[2]. בסך הכול שבעה תאים והשהיה מרבית של 3t במסלול הנתונים, כאשר אותות הבחירה יציבים.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: multiplexer background](https://hdlbits.01xz.net/wiki/Mux2to1)
