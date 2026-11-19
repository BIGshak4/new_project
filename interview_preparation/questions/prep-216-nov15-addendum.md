# PREP-216 — additional sections

## he

ממשו באמצעות פליפ-פלופים מחלק תדר ב־2 ומחלק ב־4. הראו חיבורי שעון, לוגיקת D, איפוס ודיאגרמת מצבים או תזמון. הנחה מפורשת: נשתמש בשני DFF בעלי חזית עולה, בשעון מקור משותף ובאיפוס סינכרוני ל־00; היציאות הן רמות מחזוריות ולא פולס enable.

### חלוקה בשתיים, ארבע ושמונה ובחירה ללא פעימה קצרה
הרחיבו את המונה לשלוש סיביות והפיקו f/2,f/4,f/8. בקר req בוחר אחת משלוש היציאות. לשם בחירה בטוחה, req מסונכרן ויציב סביב חזית הירידה של השעון הראשי. מותר לעכב שינוי בחירה עד שכל שלוש היציאות נמוכות. אתחול מאפס את המונה ואת הבחירה. מצאו מימוש משותף חסכוני, והסבירו את המחיר בהשהיית החלפה.
הרעיון הוא לספור חזיתות במקום לבנות שעון חדש עבור כל שלב. פליפ-פלופ D שכניסתו היא NOT Q מחליף ערך בכל חזית מקור: שתי חזיתות מחזירות אותו לאותו ערך, ולכן Q0 מחלק ב־2. הביט Q1 מתהפך רק כאשר Q0 הישן הוא 1; שתי ההשמות מתבצעות בו־זמנית.

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

אימות RTL שבוצע בפועל: SystemVerilog קומפל והורץ בהצלחה מול assertions ל־128 חזיתות ול־4 פאזות איפוס. זהו היקף נפרד מבדיקת Python בת 1,024 חזיתות. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

שלושת FF המונה נדגמים בחזית עולה משותפת. המשוואות הן D0=~q0, ‏D1=q1 XOR q0, ‏D2=q2 XOR (q1 AND q0). סיביות q0,q1,q2 מחזירות בהתאמה f/2,f/4,f/8 במחזור עבודה של 50% בין פעולות איפוס. שלושה FF הם מינימום למצב מחלק סינכרוני בעל מחזור שמונה חזיתות.

שמרו active ברגיסטר בחירה בן שתי סיביות. בחזית ירידה של השעון הראשי, אם count=000, טענו active=req עבור req חוקי. שאר הזמן active מוחזק. הציגו y=q[active], עם req=0,1,2 המייצג חלוקה ב־2,4,8. כשהבחירה מתעדכנת, כל שלוש הכניסות למוקס הן אפס והיו יציבות מאז החזית העולה הקודמת. לכן שינוי הבחירה אינו יוצר חזית בפלט. החזית האפשרית הבאה נוצרת בחזית שעון ראשי מאוחרת. זה מונע פולס קצר במודל האידאלי.

ההחלפה יכולה להתעכב עד שמונה מחזורי מקור, ויש להביא בחשבון את חזית הדגימה של req. אין הבטחת רציפות פאזה או אורך מחזור קבוע במהלך המעבר. שלושת FF של מחלק התדר אינם כוללים את שתי סיביות active. אם req אסינכרוני נדרשת העברה מסודרת של קוד הבקשה בין תחומי שעון, נוסף על עמידה בתזמון הלוגיקה והשעונים המחולקים במימוש פיזי. בקוד חומרה אפשר להחזיק מונה בעלייה ובחירה בירידה, אך יש לבדוק מסלולי חצי מחזור בין המונה לבקר.

```python
"""Source-edge phase model of three taps and common-low selection."""


def rising(count):
    if type(count) is not int or not 0 <= count < 8:
        raise ValueError("three-bit counter state required")
    q0, q1, q2 = count & 1, (count >> 1) & 1, (count >> 2) & 1
    return ((q2 ^ (q1 & q0)) << 2) | ((q1 ^ q0) << 1) | (1-q0)


def falling(count, active, requested):
    if active not in (0, 1, 2) or requested not in (0, 1, 2):
        raise ValueError("tap code must be zero, one or two")
    return requested if count == 0 else active


def output(count, active):
    return (count >> active) & 1
```

## en

Implement divide-by-two and divide-by-four using flip-flops. Show clock wiring, D-input logic, reset and timing or states. Additional definition: use two positive-edge DFFs driven by the same source clock, synchronous reset to 00, and periodic level outputs rather than enable pulses.

### Divide by two, four and eight with safe selection
Extend the counter to three bits to produce f/2,f/4,f/8. Synchronous req selects a tap and is stable around the source-clock falling edge. A selection change may wait until all three taps are low. Initialization clears counter and selection. Give an economical shared realization and explain switching latency.
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

Actual RTL validation: SystemVerilog compiled and completed self-checking simulation for 128 edges and 4 reset phases. This scope is distinct from the 1,024-edge Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

All three counter FFs share the rising source edge: D0=~q0, D1=q1 XOR q0 and D2=q2 XOR (q1 AND q0). Taps q0,q1,q2 produce f/2,f/4,f/8 with 50% duty between resets. Three state FFs are a lower bound for a synchronous divider cycling through eight source-edge states.

Retain a two-bit active selector. On a source falling edge, update active=req only when count=000 and req is valid. Hold it otherwise. Output y=q[active], with codes 0,1,2 selecting division by 2,4,8. During a selector update every MUX input is zero and has been stable since the preceding rising edge. Selection therefore causes no output transition; the next possible transition comes at a later source rising edge. This prevents a shortened pulse in the ideal timing model.

Switching can wait up to eight source periods, depending on request-sampling phase. Phase continuity and a constant transition-period length are not promised. The three divider FFs exclude the extra two selector bits. An asynchronous request needs a proper multi-bit transfer protocol in addition to physical divided-clock and half-cycle timing checks.

```python
"""Source-edge phase model of three taps and common-low selection."""


def rising(count):
    if type(count) is not int or not 0 <= count < 8:
        raise ValueError("three-bit counter state required")
    q0, q1, q2 = count & 1, (count >> 1) & 1, (count >> 2) & 1
    return ((q2 ^ (q1 & q0)) << 2) | ((q1 ^ q0) << 1) | (1-q0)


def falling(count, active, requested):
    if active not in (0, 1, 2) or requested not in (0, 1, 2):
        raise ValueError("tap code must be zero, one or two")
    return requested if count == 0 else active


def output(count, active):
    return (count >> active) & 1
```


[Private source](../sources/2026-11-15-batch20-14.png)
[he diagram](../diagrams/prep-216-divide-select-nov15-he.png)
[en diagram](../diagrams/prep-216-divide-select-nov15-en.png)
