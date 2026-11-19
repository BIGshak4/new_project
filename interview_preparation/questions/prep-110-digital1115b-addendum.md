# PREP-110 — משווה ביט אחד והרחבה למשווה ארבעה ביטים

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## משווה ביט אחד והרחבה למשווה ארבעה ביטים

א. ממשו בשערים רכיב עם שתי כניסות ביט a,b ושלוש יציאות: G המציינת a>b, E המציינת a=b ו־L המציינת a<b. הציגו טבלת אמת ומשוואות.
ב. בעזרת ארבעה רכיבים כאלה ולוגיקה משלימה, השוו שתי מילים A[3:0],B[3:0] ללא סימן. החזירו את שלוש תוצאות ההשוואה והסבירו איזה ביט קובע כאשר כמה ביטים שונים.

הנחות והגדרות: באיור המקור מסומנים a>b, a==b, b<a. הסימון השלישי זהה לראשון, ולכן אינו נותן שלוש אפשרויות השוואה שונות; כאן הוא מתוקן במפורש ל־a<b. אם מפרשים את האיור מילולית, שתי יציאותיו הקיצוניות הן אותו אות. הקלטים בגרסה הערוכה הם בינאריים וללא סימן, ביט 3 הוא המשמעותי ביותר. זהו רכיב קומבינטורי; אין שעון או מחזורי השהיה מוגדרים. מותרות לוגיקה בסיסית וחיווט. אין דרישה למספר שערים מינימלי.

גרסה כללית: שתי כניסות unsigned A,B ברוחב N≥1. הפיקו G=1 אם ורק אם A>B, ואפס אחרת, באמצעות שערים ומוקסים. השוויון מחזיר אפס.

השוואת שני ביטים: הגדירו A,B ככניסות של ביט יחיד, X=(A>B), Y=(A<B), ובשוויון X=Y=0.

### השוואת שתי מילים בנות שני ביטים באמצעות מוקסים
ממשו G=(A>B) עבור שתי מילים לא־מסומנות בנות שני ביטים. השתמשו רק במוקסי 2 ל־1, חיווט וקבועים0,1. שוויון מחזיר0. כתבו חיבורי רכיבים והציעו בדיקת תקינות. בסעיף הבדיקה הראשי יש להוכיח את הטבלה של קופסה צירופית בינארית שרירותית, שרואים רק את כניסותיה ואת G. הסבירו מה אפשר להסיק מבדיקת קלטים ומה דורש מודל תקלות פנימי.

### למה ביט גבוה קודם לביט נמוך?
במספר ללא סימן, משקל ביט גבוה גדול מסכום משקלי כל הביטים שמתחתיו. לכן הביט הגבוה הראשון שבו A ו־B שונים מכריע את כל ההשוואה. אם כל הביטים שווים, המספרים שווים. למשל 1000 גדול מ־0111, למרות שבמספר הימני יש יותר אחדים.

### רכיב של ביט אחד
| a | b | G: a>b | E: a=b | L: a<b |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 0 |
| 0 | 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 0 |

המשוואות הן g=a AND NOT b, ‏e=NOT(a XOR b), ‏l=NOT a AND b. בדיוק יציאה אחת דולקת בכל קלט חוקי. שער XNOR הוא דרך ישירה לשוויון, ואפשר לפרקו לשערים בסיסיים אם הספרייה דורשת זאת. אלו אינן יציאות מספריות בנות כמה ביטים, אלא שלושה דגלים.

### ארבעה רכיבים ולוגיקת קדימות
לכל זוג Ai,Bi בונים רכיב ומקבלים gi,ei,li. מתחילים ב־G=0,E=1,L=0, כלומר עדיין לא נבדק הבדל. עוברים i=3,2,1,0 ומעדכנים בו־זמנית לפי הערכים הישנים:

```text
G_next = G OR (E AND gi)
L_next = L OR (E AND li)
E_next = E AND ei
```

אם כבר נמצא הבדל גבוה, E=0 ושום ביט נמוך אינו משנה G או L. אם הגבוהים שווים, E=1 והביט הנוכחי רשאי להכריע. אין כאן שעון: 'עוברים' מתאר חיבור מדורג של ארבעה מקטעים קומבינטוריים. בקוד זהו חישוב המודל.

אפשר גם לפרוש משוואה: G=g3 OR(e3 AND g2) OR(e3 AND e2 AND g1) OR(e3 AND e2 AND e1 AND g0). ל־L אותה משוואה עם li, ו־E=e3 AND e2 AND e1 AND e0. הפירוק מראה מדוע OR של כל gi ללא תנאי שוויון אינו נכון: ביט נמוך לא רשאי לבטל הכרעה גבוהה הפוכה.

### הוכחת נכונות ועלות
אחרי כל תחילית ביטים, שלושת האותות משווים בדיוק את התחיליות שנבדקו. אם התחיליות כבר שונות, הביטים הבאים אינם מכריעים. אם הן שוות, ההשוואה החדשה היא זו של הביט הבא. בסיס הריק הוא שוויון, ולכן באינדוקציה ההשוואה הסופית נכונה. הקלטים 0000,1111, השוויון וההבדל בביט התחתון נכללים באותו כלל.

לרוחב n, שרשרת משתמשת ב־n תאי ביט וב־O(n) לוגיקת צירוף, ועומק לוגי O(n) בספריית שערים בעלת מניפה קבועה. אפשר לשלב קבוצות של (G,E,L) בעץ מאוזן ולקבל O(log n) עומק עם O(n) תאים וצירופים. אין טענה למינימום שטח, הספק או זמן בספרייה פיזית. עבור ארבעה ביטים העלות קבועה.

### תיקון המקור והגבול לחתומים
האיור המקורי מכיל שתי תוויות זהות במשמעות. התיקון מפורש; לא מתיימרים שהמקור כבר ביקש L נפרד. במספרים חתומים במשלים לשתיים, אי אפשר להפעיל השוואה ללא סימן על כל המילה: למשל 1111 הוא 15 ללא סימן אך ‎-1 בחתום. כשביטי הסימן שונים, הסימן מכריע; כשזהים אפשר להשתמש בהשוואת הביטים המתאימה. זו הרחבה, לא החוזה הראשי.

### מה נבדק?
המודל הורץ מול השוואת שלמים עצמאית בכל 5,460 זוגות הקלט לרוחבים 1..6, ובפרט כל 256 הזוגות של ארבעה ביטים. אומתו גם ארבע שורות תא הביט, תנאי בדיוק־אחד ודחיית קלט לא תקין. זו בדיקת לוגיקה בינארית בפייתון, ללא HDL, סינתזה או בדיקת תזמון פיזי.

```python
"""Two-state gates and most-significant-first unsigned comparator cascade."""


def compare_bit(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")
    return a & (b ^ 1), (a ^ b) ^ 1, (a ^ 1) & b


def compare_words(a, b, width=4):
    if type(width) is not int or width < 1:
        raise ValueError("positive width required")
    if any(type(v) is not int or not 0 <= v < (1 << width) for v in (a, b)):
        raise ValueError("unsigned words outside width")
    greater, equal, less = 0, 1, 0
    for i in range(width - 1, -1, -1):
        gi, ei, li = compare_bit((a >> i) & 1, (b >> i) & 1)
        greater, less = greater | (equal & gi), less | (equal & li)
        equal &= ei
    return greater, equal, less
```



### הצעה לפתרון לגרסת N הסיביות
נבנה בהדרגה את ההשוואה של A[i:0] ו־B[i:0]. מתחילים g[-1]=0, כי שתי מחרוזות ריקות שוות ואינן מקיימות גדול־ממש. לכל i מהנמוך לגבוה נגדיר d_i=Ai XOR Bi ו־g[i]=MUX(d_i,g[i−1],Ai). אם שתי הסיביות שוות, הן אינן משנות את היחס ולכן המוקס מחזיר את ההשוואה הנמוכה. אם הן שונות, זו הסיבית הגבוהה ביותר שנוספה: Ai=1 קובע גדול, ו־Ai=0 קובע שאינו גדול. האינדוקציה על i מוכיחה g[N−1]=(A>B). למשל A=1000,B=0111 מחזיר אחד, גם אם כל הביטים הנמוכים נוטים לכיוון ההפוך. כש־A=B כל d_i אפס והאתחול אפס נשמר.

המבנה משתמש ב־N שערי XOR ו־N מוקסים ועומק ליניארי במסלול ההכרעה. חלופת שערים מאוזנת מייצגת כל מקטע בזוג (G,E), כאשר G מציין גדול ו־E שווה. עבור מקטע גבוה H ונמוך L משלבים G=G_H OR (E_H AND G_L), E=E_H AND E_L. מתחילים בכל סיבית ב־G_i=Ai AND NOT Bi ו־E_i=NOT(Ai XOR Bi), ומשלבים עץ של מקטעים סמוכים עד המילה המלאה. ההוכחה זהה: הגבוה מכריע אם אינו שווה, ורק בשוויון ניגשים לנמוך. עלות ישירה O(N) צמתים ועומק O(log N), בלי טענת מינימום פיזי או תזמון מספרי ללא ספריית שערים.

### השוואת שני ביטים
A,B הם ביט יחיד. X מסמן A>B ו־Y מסמן A<B; בשוויון שני הפלטים אפס.

| A | B | X | Y |
|---|---|---|---|
|0|0|0|0|
|0|1|0|1|
|1|0|1|0|
|1|1|0|0|

לכן X=A AND NOT B ו־Y=NOT A AND B. כל פלט דורש זוג אחד בלבד מטבלת האמת, והם לעולם אינם אחד יחד. אם נדרש גם פלט שוויון, E=NOT(X OR Y).

נבדקו ממצה כל 87,380 זוגות unsigned ברוחבים 1..8 בכל אחד משני מימושי ההשוואה, כולל כל השוויונות, וארבע שורות ההשוואה החד־ביטית. הבדיקות הן מודלים עצמאיים של אמת לוגית, ללא RTL או בדיקת השהיה פיזית.

### בונים לפי הביט שמכריע
נסמן M(s,u,v) מוקס שבוחר u כאשר s=0 ואת v כאשר s=1. ההשוואה הנמוכה היא L=A0 AND NOT B0. בונים אותה בשני מוקסים. לאחר מכן מפצלים לפי A1. אם A1=0, אז B1=1 מכריע שהפלט0, ואחרת התוצאה L. אם A1=1, אז B1=0 מכריע1, ואחרת התוצאה L.

```text
nB0 = M(B0,1,0)
L = M(A0,0,nB0)
Z = M(B1,L,0)
O = M(B1,1,L)
G = M(A1,Z,O)
```

אלו חמישה מוקסים, ובעומק המרבי עוברים דרך ארבעה מהם. זו בנייה ישירה לפי פירוק שאנון, ללא טענת מינימום רכיבים. בדיקת כל A,B בתחום0..3 כוללת16 וקטורים. משווים בכל אחד לתנאי האריתמטי A>B, כולל ארבעת מקרי השוויון.

כדי להוכיח את כל טבלת האמת של קופסה שרירותית נדרשים כל16 הווקטורים. אם משמיטים קלט v, אפשר לבנות פונקציה שגויה השונה מהנכונה רק במינטרם של v. היא תעבור כל בדיקה שנבחרה. זהו חסם תחתון בתצפית על G בלבד. הוא אינו מוכיח שכל מוקס פנימי נקי מתקלות. תקלה פנימית שאינה משנה פונקציה נצפית אינה ניתנת לזיהוי בדרך זו. עבור stuck-at או תקלות תאים מוגדרות, יש לחשב עוררות והפצת תקלה מתוך הנטליסט. ייתכן שאז מספיק סט קטן יותר לכיסוי אותו מודל מסוים.

```systemverilog
// Every ternary conditional below denotes one two-to-one multiplexer.
module prep110_mux(input wire [1:0] a,b, output wire greater);
  wire not_b0 = b[0] ? 1'b0 : 1'b1;
  wire low_greater = a[0] ? not_b0 : 1'b0;
  wire when_a1_zero = b[1] ? 1'b0 : low_greater;
  wire when_a1_one = b[1] ? low_greater : 1'b1;
  assign greater = a[1] ? when_a1_one : when_a1_zero;
endmodule
```

## One-bit comparator and a four-bit unsigned cascade

A. Build a gate-level component with input bits a,b and outputs G for a>b, E for a=b and L for a<b. Give its truth table and equations.
B. Using four such cells and combining logic, compare unsigned words A[3:0],B[3:0]. Produce the three comparison results and explain which bit decides when several bit positions differ.

Assumptions and definitions: the source diagram labels a>b, a==b and b<a. The last is identical to the first, not a third comparison outcome; this edition explicitly corrects it to a<b. A literal implementation of the source would simply duplicate the first output. Inputs are binary and unsigned; bit 3 is most significant. The circuit is combinational, without a clock or specified cycle latency. Basic combining logic and wires are allowed. No minimum gate-count requirement is claimed.

General-width variant: unsigned inputs A,B have width N≥1. Produce G=1 exactly when A>B, and zero otherwise, using gates and multiplexers. Equality returns zero.

One-bit comparison: A,B are single-bit inputs. Define X=(A>B), Y=(A<B), with X=Y=0 on equality.

### Compare two-bit words using multiplexers
Implement G=(A>B) for unsigned two-bit A and B using only2-to-1 MUXes, wiring and constants0,1. Equality returns0. Give cell connections and a correctness test. The primary test contract must establish the truth table of an arbitrary deterministic binary combinational black box, observing only its inputs and G. Explain what input testing establishes and what requires an internal fault model.

### Why do higher bits take priority?
For unsigned numbers, a high bit outweighs the sum of every lower bit. Therefore the highest differing bit decides the comparison. If no bit differs, the words are equal. For example, 1000 exceeds 0111 even though the latter contains more ones.

### A one-bit cell
| a | b | G: a>b | E: a=b | L: a<b |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 0 |
| 0 | 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 0 |

Use g=a AND NOT b, e=NOT(a XOR b), l=NOT a AND b. Exactly one output is high for every valid input. XNOR directly provides equality, or may be decomposed when the gate library requires it. These are three Boolean flags, not wider numeric outputs.

### Four cells and priority logic
Build one cell for each Ai,Bi, yielding gi,ei,li. Initialize G=0,E=1,L=0: no difference has yet been seen. Process i=3,2,1,0, updating simultaneously from the old signals:

```text
G_next = G OR (E AND gi)
L_next = L OR (E AND li)
E_next = E AND ei
```

Once a higher difference exists, E=0 and lower bits cannot change the decision. While the higher bits remain equal, E=1 and the current bit may decide. This is a combinational cascade, not four clock cycles; the loop only evaluates its logical model.

Equivalently, G=g3 OR(e3 AND g2) OR(e3 AND e2 AND g1) OR(e3 AND e2 AND e1 AND g0). Replace gi with li for L; E=e3 AND e2 AND e1 AND e0. Simply ORing all gi is wrong because a lower bit must not override an opposite higher-bit decision.

### Correctness and cost
After each prefix, G,E,L compare precisely the processed prefixes. Different prefixes preserve their higher decision; equal prefixes delegate to the next bit. The empty prefix is equal, proving the recurrence by induction. All-zero, all-one, equal words and a difference only at the lowest bit follow the same rule.

An n-bit chain uses n bit cells and O(n) combining logic with O(n) depth in a bounded-fan-in gate library. Combining groups of (G,E,L) in a balanced tree gives O(log n) depth using O(n) cells and combinations. No minimum physical area, power or delay is claimed. Four-bit width has constant cost.

### Source correction and signed values
The source diagram repeats one comparison under two labels. The correction is explicit rather than attributed to the original. Signed two's-complement comparison is a separate contract: 1111 is unsigned 15 but signed -1. Different sign bits decide immediately; matching signs permit the appropriate remaining comparison. The unsigned circuit is not automatically a signed comparator.

### Verification
The actual model was compared with an independent integer-comparison oracle on all 5,460 input pairs for widths 1..6, including all 256 four-bit pairs. Checks also cover all four bit-cell rows, exactly-one output and invalid-input rejection. These are two-state Python checks, not HDL simulation, synthesis or physical timing analysis.

```python
"""Two-state gates and most-significant-first unsigned comparator cascade."""


def compare_bit(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")
    return a & (b ^ 1), (a ^ b) ^ 1, (a ^ 1) & b


def compare_words(a, b, width=4):
    if type(width) is not int or width < 1:
        raise ValueError("positive width required")
    if any(type(v) is not int or not 0 <= v < (1 << width) for v in (a, b)):
        raise ValueError("unsigned words outside width")
    greater, equal, less = 0, 1, 0
    for i in range(width - 1, -1, -1):
        gi, ei, li = compare_bit((a >> i) & 1, (b >> i) & 1)
        greater, less = greater | (equal & gi), less | (equal & li)
        equal &= ei
    return greater, equal, less
```



### Proposed solution for the N-bit variant
Build the comparison of A[i:0] and B[i:0] incrementally. Start g[-1]=0: two empty strings are equal, so strict greater-than is false. From low bits to high, define d_i=Ai XOR Bi and g[i]=MUX(d_i,g[i−1],Ai). Equal current bits do not change the lower comparison, so the MUX retains g[i−1]. Different current bits are the highest pair added: Ai=1 means greater, Ai=0 means not greater. Induction on i proves g[N−1]=(A>B). For A=1000,B=0111 the result is one despite the opposite tendency of every lower bit. When A=B all d_i are zero and the zero initialization survives.

This uses N XOR gates and N MUXes with a linear decision path. A balanced gate alternative represents each block by (G,E), denoting greater and equal. Combine high block H and low block L as G=G_H OR (E_H AND G_L), E=E_H AND E_L. Initialize each bit with G_i=Ai AND NOT Bi and E_i=NOT(Ai XOR Bi), then combine adjacent blocks in a tree. Correctness follows because the high block decides unless equal, in which case the lower block decides. A direct construction has O(N) nodes and O(log N) depth, without physical-optimality or numerical timing claims absent a gate library.

### One-bit comparison
A,B are single-bit inputs. X denotes A>B and Y denotes A<B; equality makes both outputs zero.

| A | B | X | Y |
|---|---|---|---|
|0|0|0|0|
|0|1|0|1|
|1|0|1|0|
|1|1|0|0|

Thus X=A AND NOT B and Y=NOT A AND B. Each output recognizes just one input row, and they can never both be one. If equality is also required, E=NOT(X OR Y).

Exhaustive checks covered all 87,380 unsigned operand pairs across widths 1..8 for both comparator implementations, including every equality, plus the four one-bit comparison rows. These are independent Boolean models, without RTL compilation or physical-delay testing.

### Branch on the deciding bit
Let M(s,u,v) select u for s=0 and v for s=1. First build the low-bit comparison L=A0 AND NOT B0 using two MUXes. For A1=0, B1=1 forces0; otherwise use L. For A1=1, B1=0 forces1; otherwise use L.

```text
nB0 = M(B0,1,0)
L = M(A0,0,nB0)
Z = M(B1,L,0)
O = M(B1,1,L)
G = M(A1,Z,O)
```

This uses five MUXes with maximum depth four. It is a Shannon-expansion construction without a minimum-cell claim. Exhaust A,B in0..3, covering16 vectors and four equality cases, and compare with arithmetic A>B.

All16 vectors are necessary to establish an arbitrary black box’s complete truth table from G alone. If a vector v is omitted, an incorrect Boolean function differing only at v passes the chosen tests. That is a lower bound for this observation model. It does not prove individual internal MUXes fault-free. An internal fault preserving the observed function cannot be detected at G. For specified stuck-at or cell-fault models, derive excitation and propagation from the netlist; a smaller suite may cover that narrower model.

```systemverilog
// Every ternary conditional below denotes one two-to-one multiplexer.
module prep110_mux(input wire [1:0] a,b, output wire greater);
  wire not_b0 = b[0] ? 1'b0 : 1'b1;
  wire low_greater = a[0] ? not_b0 : 1'b0;
  wire when_a1_zero = b[1] ? 1'b0 : low_greater;
  wire when_a1_one = b[1] ? low_greater : 1'b1;
  assign greater = a[1] ? when_a1_one : when_a1_zero;
endmodule
```

[he diagram](../diagrams/prep-110-mux-1115b-he.png)

[en diagram](../diagrams/prep-110-mux-1115b-en.png)

[Implementation](../solutions/prep_110_mux_comparator_1115b.sv)

[Private source](../sources/2026-11-15-batch20b-12.png)
