# PREP-058 — ממוצע שני מספרים בהפרש שתיים באמצעות שערים בלבד

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## ממוצע שני מספרים בהפרש שתיים באמצעות שערים בלבד

שני קלטים ללא סימן ברוחב N ביטים מקיימים בדיוק את הקשר המתמטי: המספר השני שווה לראשון ועוד 2. בנו מעגל צירופי המחזיר את הממוצע החשבוני שלהם, באמצעות שערים לוגיים בלבד, ללא מחבר, מחסר, מכפל או יחידת חשבון מוכנה. שרטטו והסבירו את המעגל.

הבהרות שנוספו למקור: N גדול או שווה 2; שני הקלטים מייצגים מספרים שלמים בין 0 לבין 2 בחזקת N פחות 1; הקשר מתקיים ללא גלישה. לכן הממוצע הוא מספר שלם שניתן לייצג באותו רוחב. אפשר להשתמש בבוררים רק כשהם ממומשים בשערים. אין דרישה למספר שערים מינימלי. מספרים עם סימן וקשר מודולרי הם וריאציות אחרות.

### סכום מלא כאשר a+2 עובר את רוחב המילה
הרחיבו את התרגיל כך ש־a היא מילה לא־מסומנת בת N ביטים, N≥1, ו־b=a+2 הוא הסכום המתמטי המלא ברוחב N+1. קבעו פלט ממוצע ברוחב N+1, בלי לאבד את הנשא העליון. בנו את נתיב הממוצע משערים בלבד. בסעיף נוסף מותר לפצל את b למילה בת N ביטים ולכניסת carry נפרדת. הסבירו מה יקרה אם הנשא יושמט.

**פתרון מוצע — מנצלים את הקלט השני כדי להימנע מחישוב נשא.**

נסמן את הקלט הראשון ב־a ואת השני ב־b. לפי ההנחה, הממוצע הוא a+1. אי אפשר פשוט לומר ״נוסיף אחד״ כי מחבר אסור; צריך להראות שערים שמפיקים את הביטים.

שני הקלטים באותה זוגיות, כי ההפרש ביניהם שתיים. נבחן את הביט הנמוך של a:

**אם הוא 0**, a זוגי. הוספת אחד רק הופכת את הביט הנמוך ל־1, בלי לשנות את שאר הביטים. לכן מעתיקים את הביטים העליונים של a.

**אם הוא 1**, a אי־זוגי. גם b אי־זוגי, והממוצע הוא b−1. הורדת אחד ממספר אי־זוגי רק הופכת את הביט הנמוך מ־1 ל־0, בלי לשנות את העליונים. לכן מעתיקים את הביטים העליונים של b. זו הוכחה; אין במעגל מחסר שמבצע את הפעולה.

```text
s = a[0]
y[0] = NOT s
y[i] = ((NOT s) AND a[i]) OR (s AND b[i]),  i = 1..N-1
```

כל ביט עליון מקבל בורר: כש־s=0 הוא בוחר את a וכש־s=1 הוא בוחר את b. כל בורר ממומש בשני שערי AND ושער OR, והיפוך s משותף לכל הביטים וגם משמש כביט המוצא הנמוך. התרשים מציג בנק של N−1 בוררים כדי שהאוטובוסים יישארו קריאים; המשוואה מפרטת את מימושם בשערים.

דוגמה זוגית:

```text
a = 0110  (6)
b = 1000  (8)
s = 0
y = 0111  (7)   # upper bits from a, low bit inverted
```

דוגמה אי־זוגית, שבה יש שרשרת נשא אם מנסים לחשב a+1:

```text
a = 0111  (7)
b = 1001  (9)
s = 1
y = 1000  (8)   # upper bits from b, low bit inverted
```

במקום לחשב את שרשרת הנשא, השתמשנו בביטים של b שכבר ניתנו לנו. יש מספר קבוע של רמות שערים לכל ביט, O(N) שערים בספרייה אידאלית ו־O(N) חיווט. בפועל הפצת אות הבחירה והעומס משפיעים על התזמון; אין כאן טענה למינימום שערים או להשהיה פיזית בלתי תלויה ברוחב.

הפתרון מסתמך על הקשר המדויק ללא גלישה. למשל קלטים 1110 ו־0000 ברוחב ארבעה אינם מקיימים אותו כשלמים, ולכן אינם מקרה קלט תקין. אין להחיל את ההוכחה אוטומטית על ממוצע עם סימן או על חשבון מודולרי.

בקוד SystemVerilog המצורף נתיב הנתונים מכיל רק היפוך, AND, OR, שכפול וחיתוך ביטים. החיבור והחלוקה מופיעים רק באורקל המתמטי שבבדיקות, לא במעגל המוצע.

### בוחרים את הביטים שכבר חושבו
הזהות מהמקרה המקורי נשארת נכונה גם עם נשא מלא. שני המספרים בעלי אותה זוגיות. כאשר a0=0, הממוצע a+1 מתקבל בהיפוך הביט הנמוך של a ובהעתקת יתר ביטיו, עם אפס כהרחבה עליונה. כאשר a0=1, b אי־זוגי ולכן b−1 מתקבל באיפוס הביט הנמוך של b ובהעתקת כל הביטים הגבוהים, כולל הנשא.

```text
s = a[0]
y[0] = NOT s
y[i] = ((NOT s) AND a_ext[i]) OR (s AND b[i]), 1<=i<=N
a_ext = {0,a}
```

למשל N=4, a=1111 הוא15, ו־b=10001 הוא17. מתקבל y=10000, כלומר16. אם שומרים רק b[3:0]=0001, מקבלים בטעות0000. לעומת זאת a=1110 הוא14, b=10000 הוא16, והזוגיות בוחרת את הביטים הגבוהים של a לקבלת01111, כלומר15.

בממשק המפוצל מחברים b={carry,low_sum}, ושאר נתיב השערים זהה. בנסח זה carry הוא ביט ההרחבה של הסכום הנתון, לא סיבית שרירותית. סכום מודולרי ללא נשא הוא חוזה שונה. עבור a המרבי הממוצע הוא2^N, ולכן באמת נדרש ביט פלט נוסף. העלות לינארית ברוחב והמפלס האידאלי של כל בורר קבוע. יצירת b מתבצעת מחוץ לנתיב הממוצע המוגבל לשערים.

```systemverilog
// b is the FULL W+1-bit sum a+2; carry must be preserved by the caller.
// Only bitwise gates implement the mean datapath.
module prep058_full_mean #(parameter W=4)
  (input wire [W-1:0] a,
   input wire [W:0] b,
   output wire [W:0] mean);
  wire parity = a[0];
  wire [W:0] a_ext = {1'b0,a};
  assign mean[0] = ~parity;
  assign mean[W:1] = ({W{~parity}} & a_ext[W:1])
                    | ({W{parity}} & b[W:1]);
endmodule
```

## Average two numbers differing by two using only logic gates

Two unsigned N-bit inputs satisfy the exact mathematical relation b=a+2. Build a combinational circuit returning their arithmetic mean using only logic gates, with no adder, subtractor, multiplier or prebuilt arithmetic unit. Draw and explain the circuit.

Clarifications added to the terse source: N>=2, both inputs lie in 0..2^N-1 and the relation holds without overflow. Their mean is an integer representable at the same width. Muxes may be used only as gate-built selectors. Minimum gate count is not required. Signed and modular variants are different contracts.

### Preserve the full carry when a+2 exceeds the word width
Extend the exercise to unsigned N-bit a, N≥1, with b=a+2 supplied as the full mathematical N+1-bit sum. Produce an N+1-bit mean while preserving the top carry. Build the mean datapath using gates only. A further interface may split b into its low N bits and a separate carry input. Explain the consequence of dropping carry.

**Proposed solution — use the second supplied input instead of calculating a carry.**

The mean is a+1 because b=a+2. Merely saying “increment a” is insufficient when adders are forbidden; specify the output bits instead.

The inputs have equal parity. If a[0]=0, a is even, so a+1 only changes its low bit from zero to one. Copy the upper bits from a.

If a[0]=1, both inputs are odd. The mean is also b−1, which changes only the low bit of odd b from one to zero. Copy the upper bits from b. This subtraction is a mathematical argument, not a subtractor in the implementation.

```text
s = a[0]
y[0] = NOT s
y[i] = ((NOT s) AND a[i]) OR (s AND b[i]),  i = 1..N-1
```

Each upper bit uses a selector: s=0 selects a, s=1 selects b. Implement each selector with two AND gates and one OR gate, sharing the inversion of s across the bank and the low output bit. The diagram groups N−1 selectors into a readable bus block; the equation specifies their gate-only implementation.

Even example:

```text
a = 0110  (6)
b = 1000  (8)
s = 0
y = 0111  (7)   # upper bits from a, low bit inverted
```

Odd example, where directly incrementing a would propagate a carry:

```text
a = 0111  (7)
b = 1001  (9)
s = 1
y = 1000  (8)   # upper bits from b, low bit inverted
```

Instead of calculating the carry chain, use the already-supplied bits of b. This construction has O(N) gates/wiring and bounded ideal logical depth per output bit. Real fanout, buffering and load affect timing; no minimum gate count or width-independent physical delay is claimed.

The exact no-overflow relation matters. Four-bit 1110 and 0000 do not satisfy b=a+2 over integers and are outside the contract. Do not automatically apply this proof to signed averages or modular inputs.

The attached SystemVerilog datapath uses only inversion, AND, OR, replication and bit slicing. Addition/division appears in the independent mathematical test oracle, not the proposed hardware.

### Select bits that are already available
The original parity identity remains valid when carry is retained. The inputs have equal parity. For a0=0, mean=a+1 follows by toggling a’s low bit and copying its upper bits with zero extension. For a0=1, b is odd, so b−1 clears its low bit while preserving every higher bit, including carry.

```text
s = a[0]
y[0] = NOT s
y[i] = ((NOT s) AND a_ext[i]) OR (s AND b[i]), 1<=i<=N
a_ext = {0,a}
```

At N=4, a=1111 is15 and b=10001 is17. The result is10000, or16. Keeping only low b=0001 would incorrectly produce0000. For a=1110, b=10000, parity instead selects a’s upper bits, producing01111, or15.

For the split interface reconnect b={carry,low_sum}; the gate datapath is unchanged. Here carry is the extension bit of the supplied sum, not an arbitrary bit. Modular addition without carry is a different contract. Maximum a yields mean2^N, so one extra output bit is genuinely needed. Gate count is linear in width with bounded ideal selector depth. The given b is generated outside the gate-restricted mean datapath.

```systemverilog
// b is the FULL W+1-bit sum a+2; carry must be preserved by the caller.
// Only bitwise gates implement the mean datapath.
module prep058_full_mean #(parameter W=4)
  (input wire [W-1:0] a,
   input wire [W:0] b,
   output wire [W:0] mean);
  wire parity = a[0];
  wire [W:0] a_ext = {1'b0,a};
  assign mean[0] = ~parity;
  assign mean[W:1] = ({W{~parity}} & a_ext[W:1])
                    | ({W{parity}} & b[W:1]);
endmodule
```

[he diagram](../diagrams/prep-058-full-carry-given-1115b-he.png)

[en diagram](../diagrams/prep-058-full-carry-given-1115b-en.png)

[he diagram](../diagrams/prep-058-full-carry-solution-1115b-he.png)

[en diagram](../diagrams/prep-058-full-carry-solution-1115b-en.png)

[Implementation](../solutions/prep_058_full_carry_mean_1115b.sv)

[Private source](../sources/2026-11-15-batch20b-16.png)
