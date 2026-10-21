# PREP-064 — מונה עולה ויורד בן שלושה ביטים — שערים ודלגלגים בלבד

## מקור ומצב ביקורת

[צילום המקור](../sources/prep-064.png)

צריך לממש קופסא בעלת שתי כניסות inc ו־dec, ויציאה בעלת 3 ביטים. אם inc=1 ו־dec=0 מוסיפים ליציאה אחד, אם inc=0 ו־dec=1 מחסירים אחד, אחרת לא משנים המספר ביציאה. לא ניתן להשתמש ב־F.A או H.A, רק שערים לוגיים ופליפלופים.

מקור מדווח: NVIDIA. שיוך מצילום בלבד, לא אימות עצמאי. פתרון מוצע בסיוע AI; ביקורת מקצועית, שקילות שפות וזכויות שימוש ממתינות. אין כאן רשומות פעילות למידה.

## שאלה בעברית

תכננו רכיב בעל שתי כניסות בקרה inc,dec ופלט בינארי בן שלושה ביטים. בכל חזית שעון, אם inc=1 ו־dec=0 מוסיפים 1 למספר שבפלט; אם inc=0 ו־dec=1 מפחיתים 1; אם שני אותות הבקרה שווים הפלט נשמר. מותר להשתמש רק בשערים לוגיים ובדלגלגים. אין להשתמש ברכיבי מחבר מלא או מחבר למחצה, או בבלוק סוכם או מחסר מוכן.

הבהרות שנוספו למקור: שלושת הדלגלגים משתמשים באותה חזית עולה. אותות הבקרה סינכרוניים ועומדים בזמני ההכנה וההחזקה. הפלט הוא מספר ללא סימן בטווח 0–7 והספירה מעגלית מודולו 8: הגדלת 7 נותנת 0 והקטנת 0 נותנת 7. איפוס סינכרוני פעיל בגבוה קובע 000 וגובר על שתי הבקרות. התוצאה מתעדכנת יחד אחרי החזית; אין להשתמש במוצא דלגלג כשעון של דלגלג אחר. הציגו משוואות, מעגל וטבלת מעברים.

### שלושה רמזים

1. במקום לחשב סכום, בדקו אילו ביטים מתהפכים בכל הוספה או חיסור של אחד. מתי הביט הנמוך מתהפך?
2. בספירה למעלה ביט גבוה מתהפך כאשר כל הביטים שמתחתיו הם 1; בספירה למטה הוא מתהפך כשכולם 0. הפרידו בין פקודת עלייה בלבד לפקודת ירידה בלבד.
3. צרו U=inc AND NOT dec ו־D=dec AND NOT inc. הגדירו לכל ביט אות T שאומר אם להפוך אותו. כניסת דלגלג D יכולה להיות q XOR T; אות T הגבוה צריך לבדוק גם את q1 וגם את q0.

## הצעה לפתרון

### חושבים על היפוך ביטים, לא על רכיב מחבר

נחזיק את המצב בשלושה דלגלגי D. נסמן q2 כביט המשמעותי ו־q0 כביט הנמוך. תחילה ניצור שתי פקודות שאינן יכולות להיות פעילות יחד:

```text
U = inc AND NOT dec
D = dec AND NOT inc
```

U מסמן עלייה בלבד, ו־D מסמן ירידה בלבד. כאן D הוא שם פקודת הירידה; D0,D1,D2 בהמשך הם כניסות הנתונים לדלגלגים. כאשר הבקרות 00 או 11, שתי הפקודות אפס ולכן נחזיק את המצב.

### מתי כל ביט מתהפך?

הביט q0 מתהפך בכל ספירה, למעלה או למטה. הביט q1 מתהפך בעלייה אם q0 הישן הוא 1, משום שהוספת אחד מאפסת את הביט הנמוך ומעבירה נשא. בירידה הוא מתהפך אם q0 הישן הוא 0, משום שנדרשת השאלה מן הביט הבא. אלה הסברים מתמטיים לדפוס הביטים, לא רכיבי נשא או מחסר שהוספנו.

q2 מתהפך בעלייה רק אם הזוג הנמוך הוא 11; בירידה רק אם הוא 00. במקרים האחרים הזוג הנמוך סופג את השינוי בלי להפוך את q2. לכן אותות ההיפוך הם:

```text
T0 = U OR D
T1 = (U AND q0) OR (D AND NOT q0)
T2 = (U AND q1 AND q0) OR (D AND NOT q1 AND NOT q0)
```

### מחברים לשלושה דלגלגים

שער XOR מעביר את q ללא שינוי אם T=0, והופך אותו אם T=1. לכן:

```text
D0 = q0 XOR T0
D1 = q1 XOR T1
D2 = q2 XOR T2
```

מחברים כל Di לכניסת הנתונים של הדלגלג המתאים. כל שלושת הדלגלגים מקבלים את אותו clk ואת אותו rst הסינכרוני. באיפוס שומרים 000; אחרת כל דלגלג שומר את Di שלו. אפשר להשתמש גם בדלגלגי T עם אותות T האלה, בתנאי שמגדירים אותה התנהגות שעון ואיפוס. אין כאן מחבר מלא או מחבר למחצה: הפונקציות מורכבות משערי AND,OR,NOT,XOR. אין צורך לחסום את השעון.

בשרטוט, החוט הסגול החוזר מכל Q לשער XOR הוא משוב נתונים. הוא אינו שעון. כניסות U,D ושמות q החוזרים בשרטוט הם אותות מאותו מעגל. בקופסאות חישוב T מופיעות משוואות שערים מפורשות. הספירה סינכרונית; תנאי היפוך של ביט גבוה תלוי בביטים הישנים של אותה חזית, ולא בביטים לאחר שכבר התעדכנו.

### טבלת מעברים מלאה

| q לפני החזית | inc=0,dec=0 | inc=0,dec=1 | inc=1,dec=0 | inc=1,dec=1 |
| --- | --- | --- | --- | --- |
| 000 | 000 | 111 | 001 | 000 |
| 001 | 001 | 000 | 010 | 001 |
| 010 | 010 | 001 | 011 | 010 |
| 011 | 011 | 010 | 100 | 011 |
| 100 | 100 | 011 | 101 | 100 |
| 101 | 101 | 100 | 110 | 101 |
| 110 | 110 | 101 | 111 | 110 |
| 111 | 111 | 110 | 000 | 111 |

איפוס פעיל גובר על כל תא בטבלה ומחזיר 000.

### שתי דוגמאות שמסבירות את הביט הגבוה

בספירה מ־011 למעלה: U=1,D=0, ושלושת אותות T הם 1 כי q0=1 ו־q1=1. שלושת הביטים מתהפכים יחד ומקבלים 100.

בספירה מ־100 למטה: U=0,D=1. הביט q0 מתהפך, q1 מתהפך כי q0 הישן אפס, ו־q2 מתהפך כי שני הביטים הנמוכים הישנים אפס. מתקבל 011. אם משתמשים בטעות ב־q0 החדש בחישוב q1, תתקבל תוצאה שגויה.

### נכונות, עלות וגבולות

בעלייה, כל רצף האחדים הנמוכים הופך לאפס והאפס הראשון מעליו הופך לאחד; בדיוק אלה הביטים שהמשוואות הופכות. בירידה מתרחש הדפוס הסימטרי עבור רצף אפסים. כשאין פקודה בלעדית כל T אפס. מכאן שהמימוש מקיים את ארבעת מקרי הבקרה, כולל המעברים 111 ל־000 ו־000 ל־111 מודולו 8.

נדרשים שלושה ביטי זיכרון כדי לייצג שמונה מצבים שונים, ושלושה דלגלגים מספיקים. זו טענת מינימום לזיכרון בלבד, לא למספר השערים, לשטח או להשהיה. יש להתאים את תקופת השעון למסלול הלוגי ולפיצול החוטים.

האימות בפייתון השווה משוואות שערים לאורקל אריתמטי נפרד: כל 32 מעברי מצב ובקרה, כל 32 מקרי עדיפות איפוס, כל 43,688 רצפי הבקרה באורכים 0–6 מכל מצב התחלתי, ו־32,768 רצפי בקרה ואיפוס באורך 4. קוד SystemVerilog צורף אך לא קומפל או הורץ בסימולטור HDL. זו הצעה בסיוע AI הממתינה לביקורת מקצועית.

![מעגל](../diagrams/prep-064-gate-counter-he.png)

![טבלה](../diagrams/prep-064-transition-table-he.png)

## English question

Design a component with controls inc,dec and a three-bit binary output. At each clock edge, inc=1,dec=0 increments the output by one; inc=0,dec=1 decrements it by one; equal controls hold the output. Use logic gates and flip-flops only, with no full-adder, half-adder or prebuilt adder/subtractor blocks.

Clarifications added to the source: all three flip-flops share the same rising edge; synchronous controls meet setup/hold. Output is unsigned 0..7 and wraps modulo eight: incrementing seven gives zero, decrementing zero gives seven. Synchronous active-high reset loads 000 and overrides both controls. Bits update together after the edge; do not clock one flip-flop from another output. Give equations, a circuit and a transition table.

### Three hints

1. Instead of calculating a sum, ask which bits toggle when adding or subtracting one. When does the lowest bit toggle?
2. Counting up toggles a higher bit when all lower bits are one; counting down toggles it when all lower bits are zero. Separate up-only from down-only commands.
3. Create U=inc AND NOT dec and D=dec AND NOT inc. Let each T signal indicate a bit toggle. A DFF input can be q XOR T; the highest toggle must test both q1 and q0.

## Proposed solution

### Think in toggles rather than adder blocks

Store state in three D flip-flops, with q2 the MSB and q0 the LSB. First decode two mutually exclusive commands:

```text
U = inc AND NOT dec
D = dec AND NOT inc
```

U means up only and D means down only. Here D names the down command; D0,D1,D2 below name the flip-flop data inputs. For controls 00 or 11 both commands are zero, so hold state.

### When does each bit toggle?

q0 toggles on every count. Counting up toggles q1 when old q0=1 because the low bit wraps; counting down toggles q1 when old q0=0 because the low bit borrows. These are explanations of bit patterns, not added carry or subtractor components.

q2 toggles upward only when the old low pair is 11, or downward only when it is 00. Otherwise the low pair absorbs the step. Thus:

```text
T0 = U OR D
T1 = (U AND q0) OR (D AND NOT q0)
T2 = (U AND q1 AND q0) OR (D AND NOT q1 AND NOT q0)
```

### Connect three flip-flops

XOR retains q at T=0 and inverts it at T=1, so:

```text
D0 = q0 XOR T0
D1 = q1 XOR T1
D2 = q2 XOR T2
```

Connect each Di to its DFF. All three receive the same clock and synchronous reset. Reset stores 000; otherwise each stores its Di. T flip-flops with these toggle inputs are also valid under the same edge/reset contract. There are no full/half adders: AND,OR,NOT,XOR gates implement the specified Boolean functions. Clock gating is unnecessary.

In the diagram purple feedback runs from Q to XOR as DATA, never as a clock. Repeated U,D and q net names denote the same circuit signals. Each toggle box states its actual gate equations. All decisions use the pre-edge bits simultaneously, not bits already updated during that edge.

### Complete transition table

| Pre-edge q | inc=0,dec=0 | inc=0,dec=1 | inc=1,dec=0 | inc=1,dec=1 |
| --- | --- | --- | --- | --- |
| 000 | 000 | 111 | 001 | 000 |
| 001 | 001 | 000 | 010 | 001 |
| 010 | 010 | 001 | 011 | 010 |
| 011 | 011 | 010 | 100 | 011 |
| 100 | 100 | 011 | 101 | 100 |
| 101 | 101 | 100 | 110 | 101 |
| 110 | 110 | 101 | 111 | 110 |
| 111 | 111 | 110 | 000 | 111 |

Active reset overrides every table entry and returns 000.

### Examples exposing the high-bit behavior

Incrementing 011: U=1,D=0, and all toggles are one because q0=q1=1. The three bits invert together to 100.

Decrementing 100: U=0,D=1. q0 toggles, q1 toggles because old q0 is zero, and q2 toggles because both old low bits are zero. Result is 011. Using the newly computed q0 in q1 logic would be incorrect.

### Correctness, cost and limits

Incrementing inverts the trailing ones and the first zero above them; the equations toggle exactly those positions. Decrementing is symmetric for trailing zeros. Without an exclusive command every toggle is zero. Thus all four control cases are correct, including 111-to-000 and 000-to-111 modulo eight.

Eight distinguishable output states require three memory bits, and three flip-flops suffice. This proves minimum logical storage only, not minimum gates, area or delay. Clock period must accommodate logic and fanout.

Python gate equations were compared with an independent arithmetic oracle: all 32 state/control transitions, 32 reset-priority cases, all 43,688 control streams of lengths zero through six from every initial state, and 32,768 length-four control/reset streams. SystemVerilog is supplied but not compiled or HDL-simulated. AI-assisted proposed solution; independent professional review pending.

![Circuit](../diagrams/prep-064-gate-counter-en.png)

![Table](../diagrams/prep-064-transition-table-en.png)

## חומר משלים בשתי השפות / Bilingual technical material

### assumptions

```json
{
  "he": [
    "פלט ללא סימן בן שלושה ביטים; ספירה מודולו 8, לא רוויה.",
    "כל הדלגלגים משתמשים באותה חזית עולה; הבקרות עומדות בזמני ההכנה וההחזקה.",
    "איפוס סינכרוני פעיל בגבוה מחזיר 000 וגובר על inc,dec. אות האיפוס נוסף כהבהרת תכנון.",
    "שתי בקרות שוות, כולל שתיהן 1, גורמות להחזקה. שערי XOR מותרים; רכיבי FA/HA וסוכם או מחסר מוכנים אסורים."
  ],
  "en": [
    "Unsigned three-bit output wraps modulo eight rather than saturating.",
    "All flip-flops share one rising clock edge; controls meet setup/hold.",
    "Synchronous active-high reset loads 000 and overrides inc/dec; reset was added as an explicit engineering convention.",
    "Equal controls, including both one, hold. XOR gates are allowed; FA/HA and prebuilt arithmetic blocks are forbidden."
  ]
}
```

### optimality

```json
{
  "he": {
    "criterion": "זיכרון הדרוש לייצוג כל שמונת ערכי המונה.",
    "result": "שלושה דלגלגים מספיקים ונחוצים; לוגיקה צירופית של אותות היפוך ושערי XOR.",
    "proof": "מונה העובר בין שמונה ערכי פלט שונים חייב להבחין בשמונה מצבים, ולכן נדרשים לפחות שלושה ביטי זיכרון. המימוש משתמש בדיוק בשלושה.",
    "scope": "אין הוכחה למינימום שערים, שטח, הספק או השהיה; האיפוס ולוגיקת הספרייה משפיעים על המימוש הפיזי."
  },
  "en": {
    "criterion": "Storage required to represent all eight counter values.",
    "result": "Three flip-flops are necessary and sufficient, with combinational toggle logic and XOR gates.",
    "proof": "Eight distinguishable output values require at least three state bits; this construction uses exactly three.",
    "scope": "No minimum gate-count, area, power or delay proof; reset and cell-library choices affect physical implementation."
  }
}
```

### verification

```json
{
  "he": "עברו 32 מעברי מצב ובקרה ועוד 32 מקרי עדיפות איפוס. נבדקו כל 43,688 רצפי הבקרה באורכים 0–6 מכל שמונת המצבים, הכוללים 247,584 חזיתות, וכל 32,768 רצפי הבקרה והאיפוס באורך 4, הכוללים 131,072 חזיתות. משוואות השערים הושוו לאורקל אריתמטי עצמאי. מודל פייתון בלבד; ללא קומפילציית HDL, סימולציה, סינתזה או תזמון פיזי.",
  "en": "Passed 32 state/control transitions and 32 reset-priority cases. Checked all 43,688 control streams of lengths zero through six from eight starting states, covering 247,584 edges, and all 32,768 length-four control/reset streams covering 131,072 edges. Gate equations were compared with an independent arithmetic oracle. Python models only; no HDL compilation/simulation, synthesis or physical timing."
}
```

### edge_cases

```json
{
  "he": [
    "111 בעלייה עובר ל־000; 000 בירידה עובר ל־111.",
    "inc=dec=1 מחזיק בדיוק כמו inc=dec=0.",
    "איפוס פעיל יחד עם פקודת ספירה מחזיר אפס.",
    "בהיעדר חזית שעון הפלט אינו משתנה; ללא איפוס או אתחול ידוע אין להניח מצב התחלתי פיזי.",
    "011 בעלייה ו־100 בירידה הופכים שלושה ביטים יחד לפי המצב הישן."
  ],
  "en": [
    "111 increment wraps to 000; 000 decrement wraps to 111.",
    "Both controls one hold exactly as both zero do.",
    "Reset together with a count command returns zero.",
    "No clock edge means no output update; without reset or known initialization, hardware starting state is not guaranteed.",
    "011 up and 100 down toggle all three bits using the old state."
  ]
}
```

### common_mistakes

```json
{
  "he": [
    "לתת עדיפות ל־inc כאשר שתי הבקרות 1; המקור דורש החזקה.",
    "להשתמש בבלוק סוכם או מחסר למרות איסור FA/HA.",
    "להשתמש בביט שכבר התעדכן בחישוב הביט הבא באותה חזית.",
    "לחבר q0 לשעון של הדלגלג הבא או לחסום שעון בשער פשוט.",
    "לדרוש רוויה ב־0 וב־7 בלי לציין שזה שינוי מן ההנחה של מודולו 8."
  ],
  "en": [
    "Prioritizing inc when both controls are one; the source requires hold.",
    "Using an adder/subtractor block despite the FA/HA restriction.",
    "Using already-updated low bits to compute higher bits at the same edge.",
    "Clocking a later flip-flop from q0 or gating the clock with a plain gate.",
    "Silently saturating at zero/seven instead of the declared modulo-eight convention."
  ]
}
```

### interview_answer

```json
{
  "he": "אצור פקודות עלייה וירידה בלעדיות. הביט הנמוך מתהפך בכל ספירה. ביט 1 מתהפך בעלייה אם q0=1 ובירידה אם q0=0; ביט 2 מתהפך בעלייה אם q1q0=11 ובירידה אם הם 00. לכל דלגלג D אחבר q XOR T. כך שלושה דלגלגים באותו שעון מממשים ספירה מעגלית, ושתי בקרות שוות מחזיקות.",
  "en": "Decode exclusive up/down requests. The low bit toggles on every count; bit one toggles up at q0=1 or down at q0=0; bit two toggles up at low pair 11 or down at 00. Feed each DFF with q XOR T. Three same-clock flip-flops implement the wrapping counter, while equal controls hold."
}
```

### solution_extensions

```json
{
  "he": {
    "question": "כיצד תשנו את המעגל למונה רווי שאינו עובר מ־7 ל־0 או מ־0 ל־7?",
    "direction": "זהו מפרט אחר. חסמו את U כאשר כל שלושת q הם 1 ואת D כאשר כולם 0, ואז השתמשו באותה לוגיקת היפוך. בדקו במפורש את שני הגבולות ואת מצב שתי הבקרות יחד.",
    "status": "שאלת המשך מוכנה בתוכן; אינה מחוברת לתור ההמשך החי."
  },
  "en": {
    "question": "How would you change this to a saturating counter that does not wrap at zero/seven?",
    "direction": "This changes the contract. Block U when all three q bits are one and D when all are zero, then reuse the toggle logic. Explicitly test both boundaries and simultaneous controls.",
    "status": "Follow-up prepared in content; not connected to the interactive follow-up queue."
  }
}
```

## Code and verification

- [Python model](../solutions/prep_064_three_bit_up_down.py)
- [SystemVerilog](../solutions/prep_064_three_bit_up_down.sv)
- [Checks](../checks/check_prep_064.py)
- [Evidence](../checks/prep-064-verification.json)
