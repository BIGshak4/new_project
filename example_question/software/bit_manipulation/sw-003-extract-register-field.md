# SW-003 — Extract a register field

**כותרת בעברית:** חילוץ שדה מתוך אוגר

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Difficulty | 4/10 (provisional) |
| Estimated time | 8 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Write C code or precise pseudocode to extract width consecutive bits from uint32_t reg, starting at bit lsb (bit 0 is least significant), returning them right-aligned. Valid inputs satisfy 1<=width<=32, 0<=lsb<=31, and lsb+width<=32. Avoid any shift by 32. Evaluate reg=0xD6, lsb=2, width=3 and the full-width case.

## שאלה — עברית

כתבו קוד C או פסאודו־קוד מדויק לחילוץ width ביטים רצופים מתוך uint32_t reg, החל מביט lsb, כאשר ביט 0 הוא הנמוך ביותר. החזירו אותם מיושרים לימין. קלט חוקי מקיים 1<=width<=32, 0<=lsb<=31, lsb+width<=32. הימנעו מהזזה ב־32. חשבו עבור reg=0xD6, lsb=2, width=3, וכן במקרה של רוחב מלא.

## Hint — English

Handle the full-width boundary before constructing the mask.

## רמז — עברית

טפלו במקרה של רוחב מלא לפני יצירת המסכה.

## Reference solution — English

For width==32 return reg (validity implies lsb==0). Otherwise mask=(UINT32_C(1)<<width)-1 and return (reg>>lsb)&mask. The example returns 5 (101). A uint64_t intermediate mask is another valid approach. Full-width output equals reg.

## כיוון פתרון — עברית

אם width==32 מחזירים reg; חוקיות הקלט מחייבת אז lsb==0. אחרת מחשבים mask=(UINT32_C(1)<<width)-1 ומחזירים (reg>>lsb)&mask. בדוגמה מתקבל 5, כלומר 101. גם מסכה המחושבת במשתנה uint64_t היא פתרון תקין. ברוחב מלא מוחזר reg.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [SEI CERT C: valid shift counts](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/integers-int/int34-c/)
