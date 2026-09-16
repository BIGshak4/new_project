# HW-008 — Compose a full adder

**כותרת בעברית:** הרכבת מחבר מלא

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Binary arithmetic / אריתמטיקה בינארית |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Construct a one-bit full adder using two half adders and one OR gate. Its inputs are A, B, Cin and outputs S, Cout. Derive both output equations and explain why the two intermediate carry signals cannot both be 1. Check A=B=Cin=1.

## שאלה — עברית

בנו full adder של ביט אחד באמצעות שני half adders ושער OR אחד. הקלטים הם A, B, Cin והפלטים S, Cout. גזרו משוואות לשני הפלטים והסבירו מדוע שני אותות הנשא הביניים אינם יכולים להיות 1 יחד. בדקו A=B=Cin=1.

## Hint — English

Use the sum from the first half adder as input to the second.

## רמז — עברית

העבירו את הסכום של המחבר הראשון לקלט של המחבר השני.

## Reference solution — English

First half adder: p=A^B and c1=A&B. Second: S=p^Cin and c2=p&Cin. Cout=c1|c2. c1=1 implies p=0, hence c2=0. For all inputs 1, S=1 and Cout=1.

## כיוון פתרון — עברית

המחבר הראשון מפיק p=A^B ו־c1=A&B. השני מפיק S=p^Cin ו־c2=p&Cin. הנשא הוא Cout=c1|c2. אם c1=1 אז p=0 ולכן c2=0. עבור שלושה קלטים של 1 מתקבלים S=1 ו־Cout=1.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: full adder background](https://hdlbits.01xz.net/wiki/Fadd)
