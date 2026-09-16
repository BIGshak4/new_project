# HW-003 — Compare only enabled bits

**כותרת בעברית:** השוואת ביטים לפי מסכה

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Boolean logic / אלגברה בוליאנית |
| Difficulty | 3/10 (provisional) |
| Estimated time | 7 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A, B, and M are four-bit vectors. M[i]=1 means bit i must be compared; M[i]=0 means ignore it. Produce equal=1 exactly when every selected bit matches. Give a Boolean or HDL expression. Determine the result for A=1010, B=1001, M=1100, and explain M=0000.

## שאלה — עברית

הווקטורים A, B, M הם ברוחב ארבעה ביטים. כאשר M[i]=1 יש להשוות את הביט i, וכאשר M[i]=0 מתעלמים ממנו. הפיקו equal=1 אם ורק אם כל הביטים שנבחרו זהים. כתבו ביטוי בוליאני או קוד תיאור חומרה. חשבו את התוצאה עבור A=1010, B=1001, M=1100, והסבירו את המקרה M=0000.

## Hint — English

First compute the mismatch vector.

## רמז — עברית

התחילו מווקטור המציין היכן הביטים שונים.

## Reference solution — English

equal = ~|((A ^ B) & M), where ~| is reduction NOR. The example gives 1. A zero mask selects no mismatches, so equal=1. Bitwise inversion alone would return a vector rather than the required single bit.

## כיוון פתרון — עברית

הביטוי הוא equal = ~|((A ^ B) & M), כאשר ~| הוא reduction NOR. בדוגמה מתקבל 1. מסכה של אפסים אינה בוחרת אף אי־התאמה ולכן equal=1. היפוך ביטי רגיל בלבד היה מחזיר וקטור במקום ביט יחיד.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: equality comparator background](https://hdlbits.01xz.net/wiki/Mt2015_eq2)
