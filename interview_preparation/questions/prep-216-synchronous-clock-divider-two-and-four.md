# PREP-216 — מחלק תדר סינכרוני ב־2 וב־4

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-08.png](../sources/2026-10-31-batch20-08.png)

## נוסח המקור / Original wording

מימוש מחלק תדר 2:1 ואז מחלק תדר 4:1

## עברית

ממשו באמצעות דלגלגים מחלק תדר ב־2 ומחלק ב־4. הראו חיבורי שעון, לוגיקת D, איפוס ודיאגרמת מצבים או תזמון. הבהרה שנוספה בעריכה: נשתמש בשני DFF בעלי חזית עולה, בשעון מקור משותף ובאיפוס סינכרוני ל־00; היציאות הן רמות מחזוריות ולא פולס enable.

### רמזים / Hints

1. מה צריך לקרות למוצא דלגלג בכל חזית כדי שמחזור היציאה יימשך שתי תקופות מקור?
2. במונה בינארי, מתי הביט הגבוה מחליף ערך? בדקו את הביט הנמוך לפני החזית.
3. נסו D0=NOT Q0 ו־D1=Q1 XOR Q0, עם אותו clk לשניהם. עקבו מ־00 לאורך ארבע חזיתות.

### הצעה לפתרון / Proposed solution

הרעיון הוא לספור חזיתות במקום לבנות שעון חדש עבור כל שלב. דלגלג D שכניסתו היא NOT Q מחליף ערך בכל חזית מקור: שתי חזיתות מחזירות אותו לאותו ערך, ולכן Q0 מחלק ב־2. הביט Q1 מתהפך רק כאשר Q0 הישן הוא 1; שתי ההשמות מתבצעות בו־זמנית.

```text
D0 = ~Q0
D1 = Q1 ^ Q0
div2 = Q0; div4 = Q1
```

| מספר חזיתות מאז האיפוס | Q1 Q0 | div2 | div4 |
|---|---|---|---|
| 0 | 00 | 0 | 0 |
| 1 | 01 | 1 | 0 |
| 2 | 10 | 0 | 1 |
| 3 | 11 | 1 | 1 |
| 4 | 00 | 0 | 0 |

שני DFF מקבלים את אותו clk. האיפוס קובע פאזה התחלתית ידועה; חזית עם reset פעיל אינה נספרת. אם n חזיתות נספרו, באינדוקציה Q0=n mod 2 ו־Q1=floor(n/2) mod 2. לכן תקופות היציאות הן 2T ו־4T, ותדריהן f/2 ו־f/4. במודל אידאלי היציאות גבוהות ונמוכות למספר שווה של תקופות מקור, ולכן יחס המחזור הוא 50%. איפוס באמצע תקופה יכול לקטוע אותה, והשהיות clk-to-Q בעולם הפיזי אינן אפס.

העלות כאן היא שני DFF, אינוורטר ו־XOR, מלבד לוגיקת איפוס. אם רוצים רק חלוקה ב־2 מספיק DFF אחד. חלוקה ב־4 היא מחזור בן ארבעה מצבים ולכן מימוש אוטונומי סינכרוני עם FF בינאריים צריך לפחות שני ביטי מצב; זו אינה הוכחה למינימום טרנזיסטורים או הספק.

חלופה נפרדת היא ripple: DFF שני שמקבל את Q0 כשעון. הוא יכול לחלק שוב ב־2, אבל זהו שעון נגזר, עם חזית ופאזה התלויות בחיבור ועם השהיה מצטברת. הוא דורש אילוצי שעון וניתוח תזמון נפרדים. אין לחבר כך את השרטוט ובו־זמנית לטעון שכל השלבים סינכרוניים לשעון המקור. בתוך לוגיקה סינכרונית רגילה לעיתים עדיף להפיק enable מדי שתיים/ארבע חזיתות ולהשאיר את כל ה־FF על clk; enable כזה אינו יציאת שעון בעלת duty של 50%.

קוד RTL מלא מצורף במודול prep216_divide. 1,024 חזיתות נבדקו מול מספר חזיתות עצמאי, ונבדק איפוס מכל ארבעת המצבים. זהו היקף בדיקת מודל Python; לא בוצעה מדידת תדר בחומרה.

אימות RTL שבוצע בפועל: SystemVerilog קומפל והורץ בהצלחה מול assertions ל־128 חזיתות ול־4 פאזות איפוס. זהו היקף נפרד מבדיקת Python בת1,024 חזיתות. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

### assumptions

[
  "שני DFF בחזית עולה, clk משותף; איפוס סינכרוני ל־00; מדידת תדר במצב יציב לאחר האיפוס."
]

### optimality

"שני ביטי מצב נדרשים למחזור סינכרוני בן ארבעה מצבים. במימוש הנתון: 2 DFF, NOT ו־XOR, מלבד reset; אין אופטימום הספק/טרנזיסטורים."

### verification

"1,024 חזיתות מול מונה עצמאי ואיפוס מכל 4 מצבים; מודל Python, ללא בדיקת חומרה פיזית. אימות RTL שבוצע בפועל: SystemVerilog קומפל והורץ בהצלחה מול assertions ל־128 חזיתות ול־4 פאזות איפוס. זהו היקף נפרד מבדיקת Python בת1,024 חזיתות. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה."

### edge_cases

[
  "reset פעיל מספר חזיתות; פאזה לאחר reset; עצירת clk; תקופה מקוצרת סביב reset; enable לעומת שעון."
]

### common_mistakes

[
  "להשתמש ב־Q0 החדש לחישוב Q1 באותה חזית.",
  "לחבר ripple ולנתח כאילו שני ה־FF על clk המקורי.",
  "לטעון ש־enable חד־מחזורי הוא שעון בחלוקה עם duty של 50%."
]

### interview_answer

"אני משתמש בשני DFF על אותו clk: הנמוך מתהפך בכל חזית והגבוה מתהפך כשהנמוך הישן הוא 1. מתקבל 00,01,10,11 ותדרים f/2 ו־f/4."

### source_ambiguities

[
  "המקור אינו מגדיר חזית, reset, duty או אם מותר clk נגזר; הפתרון הראשי בוחר clk משותף ומפריד חלופת ripple."
]

### solution_extensions

{
  "question": "כיצד מפיקים enable פעם בארבע חזיתות?",
  "direction": "מפענחים מצב מונה יחיד, למשל 11 לפני החזית. הפולס נמשך מחזור מקור אחד; כל הלוגיקה נשארת על clk.",
  "integration": "מוכן בתוכן; אינו מחובר לתור אינטראקטיבי."
}

## English

Implement divide-by-two and divide-by-four using flip-flops. Show clock wiring, D-input logic, reset and timing or states. Editorial completion: use two positive-edge DFFs driven by the same source clock, synchronous reset to 00, and periodic level outputs rather than enable pulses.

### רמזים / Hints

1. What must a flip-flop output do on each edge to repeat every two source periods?
2. When does the high bit of a binary counter toggle? Inspect the low bit before the edge.
3. Try D0=NOT Q0 and D1=Q1 XOR Q0, with a shared clk. Trace four edges from 00.

### הצעה לפתרון / Proposed solution

Count source edges instead of creating a new clock at each stage. A DFF with D=NOT Q toggles every source edge, returning to its original value after two edges, so Q0 divides by two. Q1 toggles only when the OLD Q0 is one. Both registers update simultaneously.

```text
D0 = ~Q0
D1 = Q1 ^ Q0
div2 = Q0; div4 = Q1
```

| Edges after reset | Q1 Q0 | div2 | div4 |
|---|---|---|---|
| 0 | 00 | 0 | 0 |
| 1 | 01 | 1 | 0 |
| 2 | 10 | 0 | 1 |
| 3 | 11 | 1 | 1 |
| 4 | 00 | 0 | 0 |

Both DFFs use the same clk. Reset fixes the initial phase; an edge with reset asserted is not counted. Inductively after n counted edges, Q0=n mod 2 and Q1=floor(n/2) mod 2. The output periods are 2T and 4T, giving f/2 and f/4. Ideal high and low durations are equal numbers of source periods, giving 50% duty. A reset during a period can truncate it; physical clk-to-Q delays are nonzero.

This realization uses two DFFs, one inverter and one XOR, apart from reset logic. Divide-by-two alone needs one DFF. A divide-by-four autonomous synchronous binary-state circuit has a four-state cycle and therefore needs at least two state bits. That is not a minimum transistor-count or power proof.

A separate ripple alternative clocks the second DFF from Q0 and divides by two again. Its clock edge and phase depend on the wiring and its delay accumulates; it needs derived-clock constraints and separate timing analysis. Do not draw this connection while claiming a common-source synchronous implementation. In ordinary synchronous logic, an enable every second/fourth edge can keep every register on clk, but that enable pulse is not a 50%-duty divided clock.

Full RTL is provided as prep216_divide. The Python model was checked against an independent edge counter for 1,024 edges and reset from all four states. This is the Python model scope; no physical frequency measurement was performed.

Actual RTL validation: SystemVerilog compiled and completed self-checking simulation for128 edges and4 reset phases. This scope is distinct from the1,024-edge Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

### assumptions

[
  "Two positive-edge DFFs, shared clk; synchronous reset to 00; steady-state frequencies after reset."
]

### optimality

"Two state bits are necessary for the four-state synchronous cycle. The shown realization uses 2 DFFs, NOT and XOR plus reset; no power/transistor optimum is asserted."

### verification

"1,024 edges against an independent counter and reset from all 4 states; Python model, no physical hardware test. Actual RTL validation: SystemVerilog compiled and completed self-checking simulation for128 edges and4 reset phases. This scope is distinct from the1,024-edge Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed."

### edge_cases

[
  "Reset across multiple edges; phase after reset; stopped clk; truncated period around reset; enable versus clock."
]

### common_mistakes

[
  "Using the new Q0 to update Q1 on the same edge.",
  "Drawing ripple wiring but analyzing a shared-source clock.",
  "Calling a one-cycle enable a 50%-duty divided clock."
]

### interview_answer

"Use two DFFs on clk: toggle the low bit every edge and the high bit when the old low bit is one. States 00,01,10,11 give f/2 and f/4."

### source_ambiguities

[
  "The source omits clock edge, reset, duty and permission for a derived clock; the main design chooses shared clk and separates ripple."
]

### solution_extensions

{
  "question": "How do you produce an enable every fourth edge?",
  "direction": "Decode one counter state, for example pre-edge 11. The pulse lasts one source cycle and all logic stays on clk.",
  "integration": "Prepared in content; not connected to the interactive queue."
}

## קבצים / Files

- [solutions/prep_216_220_sequential.py](../solutions/prep_216_220_sequential.py)
- [solutions/prep_216_220_sequential.sv](../solutions/prep_216_220_sequential.sv)
- [solutions/prep_216_220_sequential_tb.sv](../solutions/prep_216_220_sequential_tb.sv)
- [diagrams/prep-216-batch20-sequential.png](../diagrams/prep-216-batch20-sequential.png)
- [diagrams/prep-216-batch20-sequential-he.png](../diagrams/prep-216-batch20-sequential-he.png)
