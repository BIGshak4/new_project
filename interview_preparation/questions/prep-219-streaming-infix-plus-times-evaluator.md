# PREP-219 — מחשב זרם ביטוי infix עם חיבור וכפל

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-17.png](../sources/2026-10-31-batch20-17.png)

## נוסח המקור / Original wording

הקלט: מערך n של מספרים, כאשר בין כל 2 מספרים יש כפל או חיבור ובתא האחרון יש אופרטור "=". לכתוב תוכנית שתשמור את התוצאה. לבנות מכונת מצבים לתוכנית

## עברית

נתון מערך/זרם של n מספרים שביניהם + או *, ובסוף =. תכננו אלגוריתם, מסלול נתונים ובקר שמחזירים תוצאה. ההשלמה העריכתית היא קדימות רגילה: כפל לפני חיבור, ללא סוגריים או מינוס אונרי, לפחות מספר אחד, והחלפה תקינה בין מספר לאופרטור. האופרנדים הם מילים ללא סימן ברוחב W≥1 וכל החשבון מודולו 2^W. הגדירו reset, קבלת token, תוקף תוצאה וזמן הפעולות. הסבירו בנפרד מה משתנה אם דורשים חישוב משמאל לימין.

### רמזים / Hints

1. כפל מחבר מספרים לאותו איבר של סכום. איזה מידע צריך לשמור כל עוד לא הגיע +?
2. שמרו סכום של איברים שכבר הסתיימו ומכפלה של האיבר הנוכחי. אל תחברו אותו מוקדם מדי.
3. אחרי + הוסיפו את המכפלה לסכום; אחרי * הכפילו אותה במספר הבא. ב־= סיימו גם את האיבר האחרון. בקר expect_number בודק את סדר הטוקנים.

### הצעה לפתרון / Proposed solution

זהו infix: האופרטור נמצא בין האופרנדים. אין כאן זרם postfix ולכן אין צורך במחסנית של פתרון PREP-123. נפרק את הביטוי לסכום של רצפי כפל. נשמור S, סכום האיברים הסגורים, ו־P, מכפלת רצף הכפל הנוכחי. בקר בן expect_number ו־pending_mul מציין אם צפוי מספר ואם צריך להכפילו ב־P.

| מצב | טוקן מתקבל | פעולה | מצב הבא |
|---|---|---|---|
| NUMBER ראשון/אחרי + | מספר x | P←x | OP |
| NUMBER אחרי * | מספר x | P←P*x | OP |
| OP | + | S←S+P | NUMBER, ללא כפל ממתין |
| OP | * | ללא שינוי S/P | NUMBER, כפל ממתין |
| OP | = | result←S+P; result_valid←1; איפוס S/P | תחילת ביטוי הבא |

reset קובע S=P=0, מצפה למספר, וללא כפל ממתין. token_valid AND token_ready הוא קבלה. במימוש המצורף ready=1 והחיבור/הכפל הם צירופיים המסתיימים לפני החזית הבאה; הפלט result_valid הוא פולס אחרי חזית המקבלת = והתוצאה מחזיקה עד תוצאה חדשה/reset. במחזור idle הבקר והמצברים נשמרים ופולס התוצאה יורד. טוקן לא חוקי מפיק error ומחזיר לתחילת ביטוי; אין להחזיר תוצאה חלקית כאילו הושלם ביטוי.

ב־2+3*4= נקבל P=2; ב־+ נרשום S=2; המספר3 יתחיל P=3; אחרי * המספר4 יעדכן P=12; וב־= התוצאה14. חישוב עיוור משמאל לימין היה נותן20. אם זה החוזה הרצוי אפשר לשמור accumulator ואופרטור ממתין ולעדכן בכל מספר; זו חלופה סמנטית, לא מימוש שווה־ערך לקדימות רגילה.

נכונות: אחרי כל מספר P הוא מכפלת האיבר הפעיל ו־S הוא סכום כל האיברים שכבר הסתיימו. * מאריך רק את האיבר הפעיל; + סוגר אותו, ו־= מוסיף את האחרון. לכן S+P הוא ערך הביטוי בקדימות שנבחרה. כל ההשמות נחתכות ל־W ביט; שימור שקילות מודולו 2^W בחיבור ובכפל מוכיח שהתוצאה היא ערך הביטוי השלם מודולו 2^W גם אם הייתה גלישה באמצע.

עבור n מספרים יש O(n) קבלות ו־O(1) מילים, כלומר O(W) ביטי אחסון למצברים ובקר קטן; רישום התוצאה מוסיף עוד W ביט. העלות האריתמטית תלויה ב־W ובמכפיל. אם מכפל לוקח L מחזורים, יש לשמור את האופרנדים/אופרטור, להוריד ready בזמן busy ולהמתין ל־done לפני קבלת טוקן תלוי. אי אפשר להשאיר ready=1 ללא אחסון או pipeline מתאים. מספר המצבים הפיזי גדול אך סופי כאשר W קבוע; אין טענה ש־FSM בעלת זיכרון קבוע מחשבת ערכים שלמים מדויקים ובלתי חסומים.

38,130 ביטויים באורכים עד5 אופרנדים וברוחבים1,2,4 נבדקו מול אורקל עצמאי שמפצל לסכום מכפלות, כולל idle, גלישות, אפס, reset וחמש דוגמאות תחביר פסול. קוד Python ו־RTL מצורפים. זהו היקף בדיקת המודל; אין הוכחת שהיית מכפל פיזי.

אימות RTL שבוצע בפועל: המימוש ברוחב8 קומפל והורץ מול assertions ל־256 ביטויים בני6 אופרנדים, עם idle, תחביר, reset ודוגמת הקדימות. הבדיקה הגדולה ברוחבים1,2,4 היא בדיקת Python נפרדת. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

### assumptions

[
  "קדימות * לפני +; אין סוגריים/מינוס; n≥1; מספרים ללא סימן W ביט; חשבון מודולו2^W; token_valid/ready; מימוש ראשי בעל פעולות צירופיות במחזור."
]

### optimality

"O(n) טוקנים ו־O(1) מילים/O(W) אחסון; שני מצברים W ביט ותוצאת W ביט עם בקר קטן. זמן/שטח המכפל תלויי מימוש, ואין אופטימום שערים או exact בלתי חסום."

### verification

"38,130 ביטויים מול פירוק עצמאי לסכום מכפלות; רוחבים1,2,4 ועד5 מספרים, גלישה/idle/reset/5 רצפים פסולים; 2+3*4=14. מודל Python. אימות RTL שבוצע בפועל: המימוש ברוחב8 קומפל והורץ מול assertions ל־256 ביטויים בני6 אופרנדים, עם idle, תחביר, reset ודוגמת הקדימות. הבדיקה הגדולה ברוחבים1,2,4 היא בדיקת Python נפרדת. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה."

### edge_cases

[
  "מספר יחיד; אפס במכפלה; רק חיבורים/כפלים; גלישה; = לפני מספר; אופרטורים רצופים; reset באמצע; ביטויים צמודים; idle."
]

### common_mistakes

[
  "חישוב משמאל לימין ללא הבהרת קדימות.",
  "שימוש במחסנית postfix עבור זרם infix.",
  "שכחת האיבר האחרון ב־=.",
  "טענה לאריתמטיקה מדויקת בלתי חסומה ב־FSM קבועה.",
  "קבלת קלט בזמן שמכפל רב־מחזורי תפוס ללא אחסון."
]

### interview_answer

"אשמור סכום S של איברים סגורים ומכפלה P של האיבר הפעיל. * מאריך את P, + מצרף אותו ל־S, ו־= מוציא S+P. הבקר בודק מספר/אופרטור; נגדיר רוחב, גלישה ו־ready לפי המכפל."

### source_ambiguities

[
  "המקור אינו מגדיר קדימות, רוחב, סימן, גלישה, זמן מכפל או handshake; נבחרו קדימות רגילה ומילים ללא סימן מודולריות, וחלופת left-fold מוסברת."
]

### solution_extensions

{
  "question": "איך תומכים בסוגריים?",
  "direction": "צריך לשמור הקשרים מקוננים במחסנית או להגביל עומק במפורש. עומק שרירותי אינו נתמך בבקר בעל אחסון קבוע; מנתח shunting-yard הוא כיוון מתאים.",
  "integration": "מוכן בתוכן; אינו מחובר לתור אינטראקטיבי."
}

## English

An array/stream contains n numbers separated by + or *, followed by =. Design the algorithm, datapath and controller returning the result. Editorial completion uses standard precedence (multiplication before addition), no parentheses or unary minus, at least one operand, and valid number/operator alternation. Operands are unsigned W-bit words with W≥1 and arithmetic modulo 2^W. Define reset, token acceptance, result validity and operator latency. Separately explain a left-to-right interpretation.

### רמזים / Hints

1. Multiplication joins operands into one sum term. What must remain pending until + arrives?
2. Keep the sum of completed terms and the product of the current term. Do not add it too early.
3. At + commit the product; at * multiply by the next operand. At = commit the final term. An expect_number controller checks token order.

### הצעה לפתרון / Proposed solution

This is infix: operators occur between operands. It is not the postfix stream of PREP-123 and needs no operand stack. Partition the expression into a sum of multiplication runs. Keep S, the sum of completed terms, and P, the product of the active term. Controller bits expect_number and pending_mul record whether a number is expected and whether it must multiply P.

| State | Accepted token | Action | Next state |
|---|---|---|---|
| NUMBER first/after + | number x | P←x | OP |
| NUMBER after * | number x | P←P*x | OP |
| OP | + | S←S+P | NUMBER, no pending multiply |
| OP | * | keep S/P | NUMBER, pending multiply |
| OP | = | result←S+P; result_valid←1; clear S/P | next expression start |

Reset sets S=P=0, expects a number and clears pending multiply. Acceptance is token_valid AND token_ready. The supplied realization has ready=1 and combinational addition/multiplication completing before the next edge. result_valid pulses after the edge accepting =; result holds until the next result/reset. Idle holds controller/accumulators and clears the result pulse. A malformed token emits error and returns to expression start; a partial result is not declared complete.

For 2+3*4=, first P=2; + commits S=2; operand3 starts P=3; after * operand4 makes P=12; = outputs14. A blind left fold gives20. If left-to-right is the desired contract, one accumulator and a pending operator can update at each number. That is a different interpretation, not an equivalent standard-precedence implementation.

Correctness invariant: after each number P is the active term's product and S is the sum of all closed terms. A multiply only extends P; plus closes it, and equals adds the final term. Thus S+P evaluates the specified precedence. Each assignment truncates to W bits. Congruence modulo 2^W is preserved by addition and multiplication, so the output equals exact expression evaluation modulo 2^W even when intermediate operations overflow.

For n operands this needs O(n) acceptances and O(1) words: O(W) accumulator storage plus a small controller. Registering the result adds W bits. Arithmetic cost depends on W and the multiplier. With an L-cycle multiplier, retain the operands/operator, deassert ready while busy and wait for done before accepting a dependent token. Keeping ready=1 requires appropriate buffering/pipelining. Fixed W gives a finite, potentially large state space; constant finite memory does not evaluate arbitrary unbounded exact integers.

38,130 expressions with up to5 operands at widths1,2,4 were checked against an independent sum-of-products oracle, including idle, overflow, zero, reset and five malformed sequences. Python and RTL are provided. These are model checks, without a physical multiplier timing proof.

Actual RTL validation: the width8 design compiled and passed assertions on256 six-operand expressions plus idle, grammar, reset and precedence cases. The larger width1,2,4 enumeration is a separate Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

### assumptions

[
  "Times before plus; no parentheses/unary minus; n≥1; unsigned W-bit operands; modulo2^W; token_valid/ready; main implementation has single-cycle combinational operations."
]

### optimality

"O(n) tokens and O(1) words/O(W) storage: two W-bit accumulators, a W-bit result and small controller. Multiplier time/area are implementation-dependent; no gate optimum or unbounded exact arithmetic claim."

### verification

"38,130 expressions versus independent multiplication-run partitioning; widths1,2,4 up to5 numbers, overflow/idle/reset/5 malformed sequences; 2+3*4=14. Python model. Actual RTL validation: the width8 design compiled and passed assertions on256 six-operand expressions plus idle, grammar, reset and precedence cases. The larger width1,2,4 enumeration is a separate Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed."

### edge_cases

[
  "Single number; zero product; only plus/times; overflow; equals before a number; consecutive operators; mid-expression reset; back-to-back expressions; idle."
]

### common_mistakes

[
  "Left folding without specifying precedence.",
  "Using a postfix stack for this infix stream.",
  "Forgetting the last term at equals.",
  "Claiming unbounded exact arithmetic in a fixed FSM.",
  "Accepting data while a multicycle multiplier is busy without storage."
]

### interview_answer

"Keep sum S of closed terms and product P of the active term. Times extends P, plus adds it to S, and equals outputs S+P. Control checks number/operator alternation; width, overflow and multiplier readiness are explicit."

### source_ambiguities

[
  "Precedence, width, signedness, overflow, multiplier latency and handshake are absent. Standard precedence with unsigned modular words is chosen; left-fold semantics are separately explained."
]

### solution_extensions

{
  "question": "How would you support parentheses?",
  "direction": "Retain nested contexts in a stack or explicitly bound the nesting depth. Arbitrary depth needs growing memory; shunting-yard parsing is one direction.",
  "integration": "Prepared in content; not connected to the interactive queue."
}

## קבצים / Files

- [solutions/prep_216_220_sequential.py](../solutions/prep_216_220_sequential.py)
- [solutions/prep_216_220_sequential.sv](../solutions/prep_216_220_sequential.sv)
- [solutions/prep_216_220_sequential_tb.sv](../solutions/prep_216_220_sequential_tb.sv)
- [diagrams/prep-219-batch20-sequential.png](../diagrams/prep-219-batch20-sequential.png)
- [diagrams/prep-219-batch20-sequential-he.png](../diagrams/prep-219-batch20-sequential-he.png)
