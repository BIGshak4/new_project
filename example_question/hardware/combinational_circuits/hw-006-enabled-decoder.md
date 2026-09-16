# HW-006 — Enabled one-hot decoder

**כותרת בעברית:** מפענח עם אות הפעלה

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Combinational circuits / מעגלים קומבינטוריים |
| Difficulty | 2/10 (provisional) |
| Estimated time | 5 minutes |
| Format | construct |
| Modes | quick |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Design a 2-to-4 decoder with enable E. For E=1 exactly one bit of Y[3:0] is 1, at index A[1:0]; for E=0 all outputs are 0. Give four equations and the outputs for A=10 at both enable values. Can two output bits be 1 for a stable valid input?

## שאלה — עברית

תכננו מפענח 2 ל־4 עם אות הפעלה E. כאשר E=1 בדיוק ביט אחד ב־Y[3:0] הוא 1, באינדקס A[1:0]; כאשר E=0 כל הפלטים אפס. כתבו ארבע משוואות ואת הפלט עבור A=10 בשני ערכי ההפעלה. האם שני ביטי פלט יכולים להיות 1 עבור קלט חוקי ויציב?

## Hint — English

Write one minterm for each address.

## רמז — עברית

כתבו minterm אחד לכל כתובת.

## Reference solution — English

Y0=E&~A1&~A0; Y1=E&~A1&A0; Y2=E&A1&~A0; Y3=E&A1&A0. A=10 gives 0100 when enabled and 0000 otherwise. Terms are mutually exclusive for stable binary inputs; this does not claim glitch-free transitions.

## כיוון פתרון — עברית

המשוואות: Y0=E&~A1&~A0; Y1=E&~A1&A0; Y2=E&A1&~A0; Y3=E&A1&A0. עבור A=10 מתקבל 0100 כשההפעלה פעילה ו־0000 אחרת. התנאים זרים זה לזה בקלטים בינאריים יציבים; אין בכך הבטחה להיעדר גליצ׳ים בזמן מעבר.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: digital logic topic catalog](https://hdlbits.01xz.net/wiki/Problem_sets)
