# HW-012 — Load and serial shift priorities

**כותרת בעברית:** עדיפויות בטעינה ובהזזה טורית

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Sequential circuits / מעגלים סינכרוניים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | hdl |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A four-bit register has synchronous active-high reset, parallel load, and shift-right enable. Priority is reset, then load, then shift, then hold. A shift inserts serial_in at bit 3. Write next-state logic. Starting from q=1010, apply a shift with serial_in=1, then load=1 and shift=1 with data=0110, then hold. Give the three resulting values.

## שאלה — עברית

לאוגר בן ארבעה ביטים יש איפוס סינכרוני פעיל בגבוה, טעינה מקבילית והפעלת הזזה ימינה. סדר העדיפויות הוא איפוס, טעינה, הזזה, שמירה. בהזזה מוכנס serial_in לביט 3. כתבו לוגיקת מצב הבא. החל מ־q=1010 בצעו הזזה עם serial_in=1, אחר כך load=1 וגם shift=1 עם data=0110, ואז שמירה. תנו את שלושת הערכים; האיפוס אינו פעיל בעקבה.

## Hint — English

Write the priority chain before describing the shift.

## רמז — עברית

כתבו את שרשרת העדיפויות לפני מימוש ההזזה.

## Reference solution — English

Use if/else priority and q_next={serial_in,q[3:1]} for a shift. The resulting values are 1101,0110,0110. Simultaneous load and shift performs only the load.

## כיוון פתרון — עברית

משתמשים בסדר if/else ובהזזה q_next={serial_in,q[3:1]}. התוצאות הן 1101,0110,0110. כאשר טעינה והזזה פעילות יחד, מתבצעת טעינה בלבד.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: rotation background](https://hdlbits.01xz.net/wiki/Rotate100)
