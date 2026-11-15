# PREP-044 — מימוש סדרת פיבונצ׳י באמצעות חומרה

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## מימוש סדרת פיבונצ׳י באמצעות חומרה

ממשו באמצעות חומרה רכיב שמפיק את סדרת פיבונצ׳י: `F_0=0`, `F_1=1`, וכל איבר נוסף הוא סכום שני קודמיו. הציגו את מבנה המעגל, ערכי האתחול, העדכון בכל חזית שעון ודוגמת ריצה.

לצורך מימוש מוגדר, נניח שעון סינכרוני, שני אוגרים ללא סימן ברוחב `W` ביטים (`W>=1`) ואיפוס סינכרוני שמתחיל את הפלט ב־0. בכל חזית עולה ללא איפוס יתקבל האיבר הבא. יש להסביר את התנהגות המימוש כאשר התוצאה אינה נכנסת ברוחב האוגרים.

הבהרה: המקור מבקש רק לממש פיבונצ׳י בחומרה ואינו מגדיר אינדוקס, רוחב, תזמון או איפוס. אלו הנחות מפורשות לפתרון, וניתן להציע ממשק תקף אחר אם מגדירים אותו בעקביות.

### ניתוח קוד מקור עם enable והשהיית סימולציה
ציירו תרשים רכיבים ודיאגרמת גלים לקוד המצורף והסבירו את הרצף שהוא מפיק. זהו תעתיק השאלה, כולל הכרזה סותרת על Out. זהו את הבעיה ואז נתחו גרסה חוקית שבה מסירים את reg Out ושומרים Out כרשת המוזנת בהשמה רציפה. לצורך ההשהיות הגדירו timescale של1ns/1ps. rst פעיל בנמוך ואסינכרוני.

```verilog
module YYY (
  input wire clk, rst, enable,
  output wire [15:0] Out
);
reg [15:0] X;
reg [15:0] Y;
reg [15:0] Out;
always @(posedge clk or negedge rst)
  if (!rst) X <= #1 16'b0;
  else if (enable == 1'b1) X <= #1 Y;
always @(posedge clk or negedge rst)
  if (!rst) Y <= #1 16'b1;
  else if (enable == 1'b1) Y <= #1 Out;
assign Out = X + Y;
endmodule
```

בגלים הניחו תחילה rst=1, clk=0. הפעילו rst=0 ב־t=1ns ושחררו ב־t=4ns. חזיתות שעון עולות הן5,15,25,35,45ns. enable=1 בשלוש הראשונות,0 ב־35ns ושוב1 ב־45ns. הבדילו בין ערכי לפני חזית לערכים אחרי עדכוני #1.

**פתרון מוצע — שני אוגרים ומחבר**

**מה צריך לזכור?** בסדרת פיבונצ׳י כל איבר הוא סכום שני קודמיו. לכן אין צורך לשמור את כל הסדרה: מספיק לזכור שני איברים סמוכים. נבחר `F_0=0, F_1=1`, כך שהפלט מתחיל `0,1,1,2,3,5,...`. המקור אינו מגדיר אינדוקס, רוחב, שעון או איפוס; אלו הבהרות למימוש שלנו, ולא נתונים מקוריים.

**1. נשמור שני איברים סמוכים.** האוגר `a` מחזיק את האיבר שמוצג כעת, והאוגר `b` מחזיק את הבא אחריו. מיד לאחר איפוס: `a=0, b=1`, והפלט הוא `a`. שני האוגרים ברוחב `W` ביטים ללא סימן, עם `W>=1`.

**2. נתקדם צעד אחד בכל חזית שעון עולה.** האיבר הבא להצגה הוא `b`, והאיבר שאחריו הוא הסכום של `a` ו־`b`. לכן:

```text
a_next = b
b_next = (a + b) mod 2^W
value  = a
```

שני האוגרים מתעדכנים **במקביל מתוך הערכים הישנים**. למשל, מ־`a=2,b=3` עוברים ל־`a=3,b=5`. אם היינו משנים קודם את `a` ואחר כך מחשבים `a+b` מהערך החדש, היינו מקבלים בטעות `b=6`.

**3. החומרה.** נחבר את יציאת `b` לכניסת הנתונים של `a`. יציאות שני האוגרים נכנסות למחבר ברוחב `W`, ו־`W` הביטים הנמוכים של הסכום מחוברים לכניסת `b`. שני האוגרים מקבלים אותו שעון. הפלט הוא יציאת `a`. בשרטוט, חוטים בעלי אותו שם (`a`, `b`, `sum`) מחוברים זה לזה; השמות מאפשרים להציג את המעגל בלי הצטלבויות מבלבלות.

**4. דוגמת ריצה ללא גלישה.** השורה הראשונה היא מצב האתחול, לפני החזית הראשונה ללא איפוס:

```text
k       a=value    b
0          0      1
1          1      1
2          1      2
3          2      3
4          3      5
5          5      8
6          8     13
7         13     21
8         21     34
9         34     55
10        55     89
```

**5. מימוש SystemVerilog.** איפוס סינכרוני פעיל בגבוה קובע את מצב ההתחלה בחזית שעון. יש להחזיק אותו פעיל לפחות בחזית אחת; לא מניחים שאתחול אובייקט במודל פייתון מאתחל מעגל פיזי.

```systemverilog
// W >= 1. Synchronous reset; output after k nonreset edges is F_k mod 2**W.
module hardware_fibonacci #(
    parameter int unsigned W = 16
) (
    input  logic         clk,
    input  logic         rst,
    output logic [W-1:0] value
);
    logic [W-1:0] a, b;

    assign value = a;

    always_ff @(posedge clk) begin
        if (rst) begin
            a <= '0;
            b <= 1;
        end else begin
            a <= b;
            b <= a + b;
        end
    end
endmodule
```

ההשמות הלא חוסמות `<=` מחשבות את שני אגפי ימין מהמצב הישן ורק אז מעדכנות יחד. הפלט בחזית מספר `k` לאחר העדכון הוא `F_k mod 2^W`, כאשר סופרים רק חזיתות מאז האיפוס שאינן מאפסות.

**6. למה זה נכון?** באתחול הזוג הוא `(F_0,F_1)`. אם לפני עדכון הוא `(F_k,F_(k+1))`, לאחריו הוא `(F_(k+1),F_k+F_(k+1))`, כלומר `(F_(k+1),F_(k+2))`. אותו נימוק תקף מודולו `2^W`, ולכן האינווריאנט נשמר בכל מחזור.

**7. רוחב סופי וגלישה.** אין חומרה בעלת מספר ביטים סופי שמפיקה לעד את כל המספרים המדויקים, כי הסדרה גדלה ללא גבול. במימוש הזה הסכום נקטע ל־`W` ביטים, ולכן הפלט הוא פיבונצ׳י מודולו `2^W`. למשל, עבור `W=4` יוצג `0,1,1,2,3,5,8,13,5,2,...`: הערך 21 מיוצג כ־5. אם צריך רק מספר ידוע של איברים מדויקים, בוחרים רוחב שמספיק לערך הגדול ביותר שיש לאחסן, כולל האוגר `b`, או מוסיפים מדיניות גלישה מפורשת. גלישת `b` עשויה להתרחש חזית אחת לפני הופעת האיבר הגולש ב־`a`.

**עלות ותזמון.** הבנייה משתמשת בשני אוגרים בני `W` ביטים ובמחבר אחד ברוחב `W`, בתוספת לוגיקת האיפוס. מתקבל איבר חדש בכל מחזור ללא איפוס. זהו תיאור מימוש, לא הוכחה למינימום שטח או השהיה. תקופת השעון צריכה לאפשר את מסלול האוגר–מחבר–אוגר, כולל זמני הכנה, שעון וניתוב; השהיית המחבר תלויה בארכיטקטורה ובטכנולוגיה.

**תשובה קצרה לראיון:** אשמור שני איברים סמוכים באוגרים מאותחלים ל־0 ול־1. בכל חזית אעביר את השני לראשון ואת סכומם לשני, במקביל, ואוציא את הראשון. אגדיר את רוחב האוגרים ואת התנהגות הגלישה, כי בחומרה סופית אי אפשר לייצר לעד סדרה מדויקת ללא הגבלה.

**אימות:** מודל פייתון נבדק מול אורקל עצמאי שמחשב פיבונצ׳י מדויק בשיטת הכפלה מהירה: 10,260 מצבים ברוחבים 1–17, 32, 64 ו־128, ועוד כל 8,192 עקבות האיפוס באורך 10 ברוחבים 1–8. שש אפשרויות רוחב לא תקינות נדחו. קוד SystemVerilog צורף, אך לא קומפל או הורץ בסימולטור HDL ולא עבר סינתזה או בדיקת תזמון פיזית.


### שני רגיסטרים וסכום רציף
Out הוכרז גם wire וגם reg ומוזן ב־assign. בגרסה החוקית לתרגיל מסירים את הכרזת reg [15:0] Out. שני המשתנים הנשמרים הם X ו־Y, וכל אחד בן16 ביטים. נתיב X מקבל Y ונתיב Y מקבל את סכום X+Y. enable נמוך גורם לשניהם לשמור מצב. בחומרה אפשר לתאר זאת כ־FF עם enable או כבנק מוקסים לפני FF. לשניהם איפוס אסינכרוני פעיל בנמוך, אך X מאופס ל־0 ו־Y נטען ב־1.

השמות לא־חוסמות קוראות את אגף ימין בזמן האירוע. #1 דוחה את עדכון אגף שמאל ביחידת זמן אחת. לכן בחזית פעילה

```text
X_next = Y_old
Y_next = (X_old + Y_old) mod 65536
Out = (X + Y) mod 65536
```

אחרי אירוע האיפוס ב־1ns, עדכוני X,Y מתבצעים ב־2ns ו־Out נעשה1. אחרי שחרור האיפוס, ב־6ns מתקבלים X=1,Y=1,Out=2. ב־16ns מתקבלים1,2,3; ב־26ns מתקבלים2,3,5. החזית ב־35ns אינה משנה מצב. ב־46ns מתקבלים3,5,8. בלי enable חוזר האיבר, והטבלה מתחילה ב־Out=1 לאחר האיפוס, לעומת המימוש המקורי שמציג את רגיסטר האיבר הנוכחי ומתחיל ב־0.

הרצף הוא פיבונאצ׳י בהזחה באינדקס, עם גלישה מודולו2^16. שתי ההשמות משתמשות בערכים הישנים למרות שהן בשני בלוקים. #1 בקוד הוא השהיית סימולציה, ואינו נתון clock-to-Q פיזי. בכלי סינתזה הוא עשוי להידחות או להישמט; גרסת RTL המוצעת מסירה אותו. ניתוח setup/hold פיזי דורש נתוני תאים וניתוב. הכרזות ורגיסטרים חסרי איפוס ידוע מפיקים X בסימולציה עד האיפוס. יש להימנע מאירועי שעון חופפים לעדכון מושהה בתרגיל זה.

```systemverilog
`timescale 1ns/1ps
// Legal simulation transcription. The redundant reg declaration of Out is removed.
module prep044_source(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst)
    if (!rst) X <= #1 16'b0;
    else if (enable == 1'b1) X <= #1 Y;
  always @(posedge clk or negedge rst)
    if (!rst) Y <= #1 16'b1;
    else if (enable == 1'b1) Y <= #1 Out;
  assign Out = X + Y;
endmodule

// Synthesizable intent, preserving the same enable/reset and arithmetic widths.
module prep044_rtl(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst) begin
    if (!rst) begin X <= 16'b0; Y <= 16'b1; end
    else if (enable) begin X <= Y; Y <= X + Y; end
  end
  assign Out = X + Y;
endmodule
```

### אירועי #1 שכבר נקבעו אינם מתבטלים
אם חזית enable קובעת עדכון ל־t+1 ואז rst יורד ב־t+0.2, עדכון הנתונים הישן עדיין יתרחש ב־t+1. עדכון האיפוס יחול ב־t+1.2. לכן ייתכן חולף גם כאשר rst כבר נמוך. זו סמנטיקת ההשהיה של קוד הסימולציה. דיאגרמת הגלים שנבחרה מפרידה אירועים ביותר מננו־שנייה. הבדיקה הילידית בודקת גם את התרחיש החופף הזה.

## Implementing Fibonacci with hardware

Implement a hardware component that generates Fibonacci numbers: `F_0=0`, `F_1=1`, and each later term equals the sum of its two predecessors. Show the datapath, initial values, per-edge update and a trace.

For a defined implementation, assume a common synchronous clock, two unsigned `W`-bit registers (`W>=1`) and synchronous reset starting output at zero. Each nonreset rising edge produces the next term. Explain behavior when a result no longer fits the register width.

Clarification: the source asks only for hardware Fibonacci and does not specify indexing, width, timing or reset. These are explicit solution assumptions; another valid interface is acceptable if defined consistently.

### Analyze source code with enable and simulation delay
Draw the components and waveforms and explain the sequence generated by the listing. This transcription retains a conflicting Out declaration. Identify it, then analyze a legal version removing reg Out and retaining the continuously driven output net. Use timescale1ns/1ps to define delays. rst is asynchronous and active-low.

```verilog
module YYY (
  input wire clk, rst, enable,
  output wire [15:0] Out
);
reg [15:0] X;
reg [15:0] Y;
reg [15:0] Out;
always @(posedge clk or negedge rst)
  if (!rst) X <= #1 16'b0;
  else if (enable == 1'b1) X <= #1 Y;
always @(posedge clk or negedge rst)
  if (!rst) Y <= #1 16'b1;
  else if (enable == 1'b1) Y <= #1 Out;
assign Out = X + Y;
endmodule
```

For the trace initially set rst=1, clk=0. Assert rst=0 at1ns and release at4ns. Rising clock edges occur at5,15,25,35,45ns. enable is1 for the first three,0 at35ns, then1 at45ns. Distinguish values before the edge from values after #1 updates.

**Proposed solution — two registers and an adder**

**What must be remembered?** Each Fibonacci number is the sum of the preceding two. We need not store the entire sequence: two consecutive terms suffice. Choose `F_0=0, F_1=1`, producing `0,1,1,2,3,5,...`. The source leaves indexing, width, clock and reset unspecified; these are explicit implementation clarifications, not original data.

**1. Store two adjacent terms.** Register `a` holds the term currently displayed, and `b` holds the following term. Immediately after reset, `a=0,b=1`, with output `value=a`. Both registers are unsigned and `W` bits wide, where `W>=1`.

**2. Advance on each rising clock edge.** The next displayed term is `b`; the term after it is the sum of old `a` and old `b`:

```text
a_next = b
b_next = (a + b) mod 2^W
value  = a
```

Both registers update **simultaneously from their old values**. For example, `(a,b)=(2,3)` becomes `(3,5)`. Updating `a` first and then using the new value in the sum would incorrectly make `b=6`.

**3. Hardware connections.** Connect output `b` to the data input of `a`. Feed both register outputs into a `W`-bit adder, and connect its low `W` result bits to the data input of `b`. Both registers share the clock. Expose `a` as output. In the schematic, matching net names (`a`, `b`, `sum`) denote connected wires; named nets avoid ambiguous wire crossings.

**4. Trace before overflow.** Row zero is initialization, before the first nonreset edge:

```text
k       a=value    b
0          0      1
1          1      1
2          1      2
3          2      3
4          3      5
5          5      8
6          8     13
7         13     21
8         21     34
9         34     55
10        55     89
```

**5. SystemVerilog implementation.** A synchronous active-high reset establishes the initial state at a clock edge. Assert it across at least one active edge; Python object initialization does not initialize physical registers.

```systemverilog
// W >= 1. Synchronous reset; output after k nonreset edges is F_k mod 2**W.
module hardware_fibonacci #(
    parameter int unsigned W = 16
) (
    input  logic         clk,
    input  logic         rst,
    output logic [W-1:0] value
);
    logic [W-1:0] a, b;

    assign value = a;

    always_ff @(posedge clk) begin
        if (rst) begin
            a <= '0;
            b <= 1;
        end else begin
            a <= b;
            b <= a + b;
        end
    end
endmodule
```

Nonblocking assignments `<=` evaluate both right-hand sides from the old state before updating together. After nonreset edge `k` since initialization, output is `F_k mod 2^W`.

**6. Correctness.** Initialization gives `(F_0,F_1)`. If the stored pair is `(F_k,F_(k+1))`, the next pair is `(F_(k+1),F_k+F_(k+1))=(F_(k+1),F_(k+2))`. The same identity holds modulo `2^W`, preserving the invariant at every edge.

**7. Finite width and overflow.** No fixed finite number of bits can represent all exact Fibonacci terms forever: their values grow without bound. This implementation truncates the sum to `W` bits, giving Fibonacci modulo `2^W`. For `W=4`, for example, output is `0,1,1,2,3,5,8,13,5,2,...`, because 21 is represented as 5. For a bounded number of exact terms, choose a width covering the largest stored value, including register `b`, or specify an overflow policy. Register `b` can overflow one edge before the overflowing term reaches output `a`.

**Cost and timing.** This construction uses two `W`-bit registers and one `W`-bit adder, plus reset logic, and produces one new term per nonreset cycle. This is not an area or delay minimality proof. The clock period must accommodate the register–adder–register path, including setup, clock and routing effects; adder delay depends on architecture and technology.

**Interview answer:** Store two adjacent terms in registers initialized to zero and one. At every rising edge copy the second term into the first register and their old-value sum into the second, in parallel, and expose the first. Define register width and overflow because finite hardware cannot generate an unbounded exact sequence forever.

**Verification:** A Python clock-edge model matched an independent exact fast-doubling Fibonacci oracle at 10,260 states across widths 1–17, 32, 64 and 128, plus all 8,192 length-ten reset traces at widths 1–8. Six invalid widths were rejected. SystemVerilog is supplied but has not been compiled, HDL-simulated, synthesized or physically timed.


### Two registers and a continuous sum
Out is declared both wire and reg and driven by assign. Remove the redundant reg declaration for the legal analyzed version. Stored state is sixteen-bit X and Y. The X input receives Y; the Y input receives X+Y. Low enable holds both, realizable with enabled FFs or feedback MUXes. Both use asynchronous active-low reset, loading X=0 and Y=1.

Nonblocking assignments sample their right sides at the event. #1 defers the left-side update by one time unit. Thus at an enabled edge

```text
X_next = Y_old
Y_next = (X_old + Y_old) mod 65536
Out = (X + Y) mod 65536
```

Reset asserted at1ns updates X/Y at2ns, making Out1. After reset release, at6ns X=1,Y=1,Out=2. At16ns they are1,2,3; at26ns2,3,5. The35ns edge holds state. At46ns the values are3,5,8. Disabling repeats the term. This source output starts at1 after reset, whereas the original current-term-register interface starts at0.

It generates an index-shifted Fibonacci sequence modulo2^16. Both blocks read old values. The source #1 is a simulation delay, not a physical clock-to-Q specification. Synthesis tools may reject or discard it; the supplied synthesizable-intent version removes it. Physical setup/hold needs cell and routing data. State remains unknown in simulation until initialized by reset. The chosen trace avoids clock edges overlapping pending delayed updates.

```systemverilog
`timescale 1ns/1ps
// Legal simulation transcription. The redundant reg declaration of Out is removed.
module prep044_source(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst)
    if (!rst) X <= #1 16'b0;
    else if (enable == 1'b1) X <= #1 Y;
  always @(posedge clk or negedge rst)
    if (!rst) Y <= #1 16'b1;
    else if (enable == 1'b1) Y <= #1 Out;
  assign Out = X + Y;
endmodule

// Synthesizable intent, preserving the same enable/reset and arithmetic widths.
module prep044_rtl(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst) begin
    if (!rst) begin X <= 16'b0; Y <= 16'b1; end
    else if (enable) begin X <= Y; Y <= X + Y; end
  end
  assign Out = X + Y;
endmodule
```

### A scheduled #1 event is not canceled
If an enabled edge schedules a data update for t+1 and reset falls at t+0.2, the pending data update still occurs at t+1. The reset update follows at t+1.2. A transient is therefore possible while rst is already low. This follows the delayed simulation listing’s event semantics. The chosen waveform keeps events more than one nanosecond apart. The native test also checks this overlapping-event case.

[he diagram](../diagrams/prep-044-source-circuit-1115b-he.png)

[en diagram](../diagrams/prep-044-source-circuit-1115b-en.png)

[he diagram](../diagrams/prep-044-source-waves-1115b-he.png)

[en diagram](../diagrams/prep-044-source-waves-1115b-en.png)

[Implementation](../solutions/prep_044_source_fibonacci_1115b.sv)

[Private source](../sources/2026-11-15-batch20b-17.png)
