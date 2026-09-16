# HW-010 — Unsigned saturating addition

**כותרת בעברית:** חיבור ללא סימן עם רוויה

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Binary arithmetic / אריתמטיקה בינארית |
| Difficulty | 4/10 (provisional) |
| Estimated time | 8 minutes |
| Format | hdl |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Design an eight-bit unsigned saturating adder: y=min(a+b,255). Provide pseudocode or HDL and the width of the intermediate sum. Evaluate (250,12), (120,80), and (255,0). Explain why inspecting only an eight-bit wrapped result is insufficient.

## שאלה — עברית

תכננו מחבר רוויה ללא סימן ברוחב שמונה ביטים: y=min(a+b,255). כתבו פסאודו־קוד או קוד תיאור חומרה וציינו את רוחב סכום הביניים. חשבו עבור (250,12), (120,80), (255,0). הסבירו מדוע בדיקת תוצאה שנקטעה לשמונה ביטים אינה מספיקה.

## Hint — English

Preserve the carry before choosing the final output.

## רמז — עברית

שמרו את הנשא לפני בחירת הפלט הסופי.

## Reference solution — English

Use a nine-bit sum formed by zero-extending both operands. If sum[8]=1 output 255, otherwise sum[7:0]. Results are 255,200,255. Truncation loses carry and can make an overflowing sum appear small.

## כיוון פתרון — עברית

מחשבים סכום בן תשעה ביטים לאחר הרחבת שני הקלטים באפס. אם sum[8]=1 מחזירים 255, אחרת את sum[7:0]. התוצאות הן 255,200,255. קיטוע מאבד את הנשא ועלול להפוך סכום שגלש לערך קטן.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: full adder background](https://hdlbits.01xz.net/wiki/Fadd)
- [HDLBits: signed overflow background](https://hdlbits.01xz.net/wiki/Exams/ece241_2014_q1c)
