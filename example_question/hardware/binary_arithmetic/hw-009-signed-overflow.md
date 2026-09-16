# HW-009 — Carry and signed overflow

**כותרת בעברית:** נשא וגלישה בחיבור מספרים מסומנים

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Binary arithmetic / אריתמטיקה בינארית |
| Difficulty | 3/10 (provisional) |
| Estimated time | 5 minutes |
| Format | short_answer |
| Modes | quick |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Add four-bit words and keep only four result bits. For 0110+0101 and 1110+1111, give the result bits, carry-out, and signed-overflow flag. Interpret each input and result as two's complement. Give a sign-bit rule for signed overflow.

## שאלה — עברית

חברו מילים של ארבעה ביטים ושמרו ארבעה ביטים בתוצאה. עבור 0110+0101 ועבור 1110+1111, תנו את ביטי התוצאה, הנשא החוצה ודגל הגלישה המסומנת. פרשו קלטים ותוצאות במשלים ל־2. כתבו כלל המבוסס על ביטי הסימן לזיהוי גלישה.

## Hint — English

Four-bit two's complement represents -8 through 7.

## רמז — עברית

טווח משלים ל־2 בארבעה ביטים הוא מ־‎-8 עד 7.

## Reference solution — English

6+5 gives 1011 (-5), carry=0, overflow=1. (-2)+(-1) gives 1101 (-3), carry=1, overflow=0. Overflow occurs when inputs have the same sign and the result has the opposite sign.

## כיוון פתרון — עברית

החיבור 6+5 נותן 1011, כלומר ‎-5, עם carry=0 ו־overflow=1. החיבור ‎(-2)+(-1) נותן 1101, כלומר ‎-3, עם carry=1 ו־overflow=0. גלישה מתרחשת כשהקלטים בעלי אותו סימן והתוצאה בעלת סימן הפוך.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: signed overflow background](https://hdlbits.01xz.net/wiki/Exams/ece241_2014_q1c)
