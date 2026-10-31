# PREP-070 — מימוש שער AND באמצעות MUX 2:1 יחיד

## מקור שנמסר

ממש שער AND מ MUX2:1

[צילום המקור הפנימי](../sources/prep-070.png)

סטטוס: פתרון מוצע בסיוע AI; בדיקה מקצועית אנושית ממתינה. השיוך לחברות הוא דיווח מהצילום בלבד.

## מימוש שער AND באמצעות MUX 2:1 יחיד

ממשו Y=A AND B בעזרת מרבב MUX 2:1 יחיד. ציינו את חיבורי D0,D1,S ושרטטו את המעגל.

הבהרות: הכניסות בינאריות, המרבב בוחר D0 כאשר S=0 ו־D1 כאשר S=1. מותר לחבר קבוע לוגי 0 וחוטים, אך אין להשתמש בשער לוגי נוסף. זהו מעגל צירופי ללא שעון.

### רמזים

1. בחרו אחת הכניסות כבוררת ובדקו מה הפלט צריך להיות בכל אחד משני ערכיה.
2. כאשר A=0 הפלט תמיד 0; כאשר A=1 הפלט שווה ל־B.
3. חברו A לבחירה S. קבעו איזה אות צריך להופיע ב־D0 ואיזה ב־D1 לפי שתי השורות האלה.

### הצעה לפתרון

### חושבים לפי הבחירה של המרבב

מרבב אינו דורש ששתי כניסות הנתונים יהיו קבועות. אפשר לחבר אחת מהן לאות B. נבחר את A כבורר:

```text
S  = A
D0 = 0
D1 = B
Y  = MUX(S,D0,D1)
```

בשרטוט החץ של A נכנס ל־S בתחתית. הקבוע 0 נכנס ל־D0 העליון, ו־B נכנס ל־D1 התחתון. המספרים 0 ו־1 הם מספרי פורטי הנתונים הנבחרים לפי S; אין הכוונה לחבר קבוע 1 ל־D1.

### למה החיבור הזה עובד?

כאשר A=0 המרבב בוחר D0=0, בדיוק כמו AND עם אחת הכניסות אפס. כאשר A=1 הוא בוחר D1=B, בדיוק כמו AND עם כניסה אחת 1. בנוסחת המרבב:

```text
Y = (NOT S AND D0) OR (S AND D1)
  = (NOT A AND 0) OR (A AND B)
  = A AND B
```

| A | B | פורט נבחר | Y |
| --- | --- | --- | --- |
| 0 | 0 | D0 | 0 |
| 0 | 1 | D0 | 0 |
| 1 | 0 | D1 | 0 |
| 1 | 1 | D1 | 1 |

גם החיבור הסימטרי S=B,D0=0,D1=A תקף. אין צורך במהפך, דלגלג או שעון. מספר הרכיבים הוא MUX אחד וקבוע אפס. תחת מודל שמותר בו רק חוטים וקבועים בלי שום רכיב פונקציונלי, אי אפשר להפיק AND באמצעות אפס מרבבים: חוט יחיד נותן A,B או קבוע, ואף אחד מהם אינו פונקציית AND לכל הקלטים. לכן אחד הוא המינימום במודל הזה; אין בכך הוכחה לשטח מינימלי בספריית תאים אחרת.

נבדקו כל 8 שורות פונקציית המרבב, 4 שורות AND ו־4 שורות החיבור הסימטרי. אלה בדיקות לוגיות מלאות של המודל, ללא סינתזה או מדידת השהיה. הפתרון מוצע וממתין לביקורת מקצועית.

![מרבב יחיד עם שמות פורטים וכיוון אותות](../diagrams/prep-070-and-mux-he.png)

### assumptions

[
  "מרבב אידאלי בוחר D0 ב־S=0 ו־D1 ב־S=1.",
  "קבוע אפס וחוטים מותרים; אין שער נוסף או שעון."
]

### optimality

{
  "criterion": "מספר מרבבים כשמותר רק חיווט וקבועים לצדם.",
  "result": "מרבב אחד נחוץ ומספיק.",
  "proof": "בלי רכיב פונקציונלי אפשר לקבל רק כניסה או קבוע, ולא AND; המימוש משתמש באחד.",
  "scope": "אין טענת שטח או השהיה מינימליים בספריית שערים כללית."
}

### verification

"עברו כל 8 שורות המרבב, כל 4 שורות AND ו־4 שורות המימוש הסימטרי בפייתון. לא בוצעה סינתזה או בדיקת חומרה."

### edge_cases

[
  "A=0 קובע אפס בלי תלות ב־B.",
  "A=1 מעביר B, כולל B=0.",
  "אם ספריית הרכיבים משתמשת במוסכמת בחירה הפוכה יש להתאים את שמות הפורטים.",
  "החלפת D0,D1 בלי להחליף תנאי בחירה נותנת פונקציה אחרת."
]

### common_mistakes

[
  "לחבר D1 לקבוע 1 במקום ל־B, וכך להחזיר רק A.",
  "להחליף בין פורט הבחירה לפורט נתונים.",
  "להוסיף שער AND וכך לעקוף את השאלה.",
  "לצייר חוטים ללא מספרי הפורטים ולכן לא להגדיר מה נבחר."
]

### interview_answer

"אבחר A כ־S, אחבר D0=0 ו־D1=B. כאשר A=0 נקבל 0 וכאשר A=1 נקבל B, ולכן בדיוק A AND B. מספיק מרבב אחד, ללא שעון או שער נוסף."

### solution_extensions

{
  "question": "כיצד תממשו OR בעזרת אותו סוג מרבב יחיד?",
  "direction": "בחרו S=A,D0=B,D1=1: כאשר A=0 צריך B וכאשר A=1 צריך תמיד 1. נדרש קבוע 1 מותר בגרסת ההמשך.",
  "status": "מוכן בתוכן; לא מחובר לתור המשך חי."
}

## Implement AND with one 2:1 MUX

Implement Y=A AND B with one 2:1 multiplexer. Specify D0,D1,S and draw the circuit.

Clarifications: binary signals; the MUX chooses D0 for S=0 and D1 for S=1. Constant logic zero and wires are allowed, but no additional logic gate. This is combinational, with no clock.

### Hints

1. Choose one input as select and ask what the output must be for each select value.
2. When A=0 the output is always zero; when A=1 it equals B.
3. Wire A to S. Choose D0 and D1 from those two cases.

### Proposed solution

### Reason by the select cases

MUX data inputs need not both be constants: one can carry B. Choose A as select:

```text
S  = A
D0 = 0
D1 = B
Y  = MUX(S,D0,D1)
```

In the diagram A enters the bottom S port. Constant zero enters upper D0 and B enters lower D1. The digits in D0/D1 identify selected data ports; D1 is not tied to constant one.

### Why it works

At A=0 the MUX selects constant zero, matching AND with one zero input. At A=1 it selects B, matching AND with one input held high. Algebraically:

```text
Y = (NOT S AND D0) OR (S AND D1)
  = (NOT A AND 0) OR (A AND B)
  = A AND B
```

| A | B | Selected port | Y |
| --- | --- | --- | --- |
| 0 | 0 | D0 | 0 |
| 0 | 1 | D0 | 0 |
| 1 | 0 | D1 | 0 |
| 1 | 1 | D1 | 1 |

The symmetric S=B,D0=0,D1=A also works. No inverter, storage or clock is needed: one MUX and a zero constant suffice. With only wires and constants and no functional component, zero MUXes can output only A,B or a constant, none equal to AND on every input. Therefore one is minimal in this restricted component model, not a minimum physical-area result for other cell libraries.

Checks covered all eight MUX rows, four AND rows and four symmetric-wiring rows. These are exhaustive logical-model checks, not synthesis or propagation-delay measurements. Independent professional review is pending.

![One MUX with numbered ports and signal arrows](../diagrams/prep-070-and-mux-en.png)

### assumptions

[
  "Ideal MUX chooses D0 at S=0 and D1 at S=1.",
  "Zero constant and wires allowed; no additional gate or clock."
]

### optimality

{
  "criterion": "MUX count with only wires and constants otherwise.",
  "result": "One MUX is necessary and sufficient.",
  "proof": "With no functional component only a primary input or constant is possible, not AND; construction uses one.",
  "scope": "No minimum physical area/delay claim for a general cell library."
}

### verification

"Passed all eight MUX rows, four AND rows and four symmetric-implementation rows in Python. No synthesis or hardware tests."

### edge_cases

[
  "A=0 forces zero independently of B.",
  "A=1 forwards B, including B=0.",
  "A library with reversed select convention needs corresponding port mapping.",
  "Swapping D0 and D1 without changing selection gives a different function."
]

### common_mistakes

[
  "Tying D1 high instead of B, which outputs only A.",
  "Confusing select and data ports.",
  "Adding an AND gate and bypassing the constraint.",
  "Omitting port numbers so select behavior remains ambiguous."
]

### interview_answer

"Use S=A,D0=0,D1=B. Select zero returns zero; select one returns B, exactly A AND B. One MUX suffices with no clock or extra gate."

### solution_extensions

{
  "question": "How would you implement OR with one such MUX?",
  "direction": "Use S=A,D0=B,D1=1: when A=0 return B; when A=1 return one. This follow-up explicitly permits a high constant.",
  "status": "Prepared in content, not connected to the live follow-up queue."
}

## Files

- [Code](../solutions/prep_070_and_mux.py)
- [Verification](../checks/check_prep_070.py)
- [Evidence](../checks/prep-070-verification.json)

## קליטה נוספת — 31.10.2026 / Additional intake

- מקור 11: [sources/2026-10-31-batch20-11.png](../sources/2026-10-31-batch20-11.png)

תממש בעזרת MUX(2:1) את השערים: And, Or, Xor, Nand

התוכן הבא הוא הרחבה מוצעת בסיוע AI; הוא אינו אישור אנושי לפתרון המקורי או החדש.

### he — הרחבה / Extension



וריאציית מקור נוספת, 31.10.2026: ממשו בעזרת MUX 2:1 את AND, OR, XOR ו־NAND. בגרסה זו מותרים הקבועים 0 ו־1 וכן יצירת משלים באמצעות MUX; ציינו אם משלים זמין חינם או דורש רכיב. השתמשו במוסכמה MUX(S,D0,D1), עם בחירת D0 באפס. הגרסה המקורית של AND נשמרת, והקלה זו אינה משנה את אילוצי הקבוע־אפס בלבד של PREP-031.

#### רמזים להרחבה / Variant hints

1. לגרסת ארבעת השערים, בחרו A כבורר והשוו את התוצאה כאשר A אפס וכאשר הוא אחד.
2. בגרסה הנוספת XOR דורש B כאשר A אפס ומשלים B כאשר A אחד; גם NAND משתמש במשלים.
3. כתבו זוג D0,D1 לכל שער. אם אין משלים מוכן, חפשו MUX שבוחר בין 1 ל־0 לפי B.

#### הצעה לפתרון / Proposed solution



### הצעה לפתרון לגרסת ארבעת השערים
פירוק לפי A הוא דרך שיטתית: לכל שער שואלים מה נשאר מהפונקציה כאשר A=0 וכאשר A=1, ואז מחברים את שתי התשובות ל־D0,D1.

```text
nB   = MUX(B,1,0)
AND  = MUX(A,0,B)
OR   = MUX(A,B,1)
XOR  = MUX(A,B,nB)
NAND = MUX(A,1,nB)
```

כאשר A=0, AND חייב להיות אפס, OR ו־XOR הם B, ו־NAND הוא אחד. כאשר A=1, AND הוא B, OR הוא אחד, ו־XOR ו־NAND הם NOT B. אלו בדיוק שני ענפי כל מרבב, ולכן שתי קבוצות המקרים מוכיחות את כל ארבע הפונקציות. לדוגמה A=B=1 נותן AND=OR=1 אך XOR=NAND=0.

ל־AND ול־OR דרוש מרבב אחד כל אחד במודל הזה. XOR או NAND דורשים מרבב פונקציה ומשלים B: אם המשלים אינו זמין, מרבב היפוך נוסף מייצר אותו. כאשר בונים את כל ארבעת הפלטים יחד ניתן לשתף nB, ולכן המבנה הנתון משתמש בחמישה מרבבים בסך הכול, או ארבעה אם nB כבר מסופק ללא עלות. זו ספירת הבנייה שהוצגה, ללא טענת מינימום משותף בין כל הרשתות. שום שער נוסף לא מסתתר בסימון NOT: הוא מומש ב־MUX.

עברו ארבעת צירופי A,B, כלומר 20 השוואות פונקציה כולל יצירת nB. זוהי בדיקת ערכים יציבים; לא נבדקו תקלות מעבר, עומס, השהיה או סינתזה.

#### assumptions

[
  "לגרסה הנוספת בלבד מותרים שני הקבועים ומרבב היוצר משלים; מוסכמת D0 באפס."
]

#### optimality

"בנייה לכל ארבעת השערים: ארבעה מרבבי פונקציה ועוד מהפך MUX משותף אם nB אינו זמין. אין הוכחת מינימום משותף."

#### verification

"גרסת 2026-10-31 עברה ארבע שורות קלט ו־20 השוואות פונקציה; ללא סינתזה."

#### edge_cases

[
  "A=B=1: XOR ו־NAND אפס.",
  "A=0: NAND אחד ללא תלות ב־B.",
  "משלים משותף נחוץ לשני פלטים, ולא צריך לשכפלו במודל אידאלי."
]

#### common_mistakes

[
  "אין להשמיט את עלות המשלים בלי להצהיר שהוא מסופק.",
  "אסור להחיל רשות להשתמש בקבוע 1 על שאלת PREP-031 בעלת אילוצים אחרים."
]

#### interview_answer

"אבחר A כבורר, אכתוב את שני ענפי כל פונקציה ואשתף NOT B שנוצר מ־MUX(B,1,0)."

#### source_ambiguities

[
  "צילום 11 מוסיף ארבע פונקציות אך אינו מציין זמינות קבועים או משלים; ההרשאות ועלות המשלים מפורשות בעריכה."
]

#### solution_extensions

{
  "question": "אם B ו־NOT B כבר זמינים, כמה מרבבים צריך לבנייה המוצגת וכמה מפלסים יש?",
  "direction": "ארבעה מרבבים במקביל ומפלס אחד לכל פלט. בלי משלים מוכן למסלול XOR/NAND יש עוד מפלס היפוך.",
  "integration": "מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי."
}

### en — הרחבה / Extension



Additional source variant, 31 October 2026: implement AND, OR, XOR and NAND with 2:1 MUXes. This variant permits constants 0 and 1 and a complement generated by another MUX. State whether a complement is already free or requires a component. MUX(S,D0,D1) selects D0 at zero. The original AND problem is preserved; this permission does not change PREP-031's zero-only restrictions.

#### רמזים להרחבה / Variant hints

1. For the four-gate variant, choose A as select and compare the A=0 and A=1 cases.
2. The added XOR variant needs B at A=0 and complemented B at A=1; NAND also uses that complement.
3. Write D0,D1 for each gate. If no complement is available, make a MUX choose between 1 and 0 using B.

#### הצעה לפתרון / Proposed solution



### Proposed solution for the four-gate variant
Splitting on A is systematic: ask what remains at A=0 and A=1, then connect those functions to D0,D1.

```text
nB   = MUX(B,1,0)
AND  = MUX(A,0,B)
OR   = MUX(A,B,1)
XOR  = MUX(A,B,nB)
NAND = MUX(A,1,nB)
```

At A=0, AND is zero, OR/XOR equal B, and NAND is one. At A=1, AND equals B, OR is one, and XOR/NAND equal NOT B. These are precisely the two branches of each MUX, proving all four functions. For A=B=1, AND/OR are one while XOR/NAND are zero.

AND and OR each use one MUX in this model. XOR or NAND uses its function MUX plus complemented B: if unavailable, an additional inverter MUX generates it. Building all four outputs together permits sharing nB, so the displayed construction uses five MUXes, or four when nB is supplied without cost. This counts the shown construction without claiming a globally minimal shared network. NOT hides no extra gate; it is implemented with a MUX.

All four A,B rows passed, giving twenty function assertions including nB. These are settled Boolean checks, without hazards, loading, timing or synthesis.

#### assumptions

[
  "The added variant permits both constants and a MUX-generated complement; D0 is selected at zero."
]

#### optimality

"Displayed four-gate construction: four function MUXes plus one shared inverter MUX unless nB is free. No shared-network minimum proof."

#### verification

"The 2026-10-31 variant passed four input rows and twenty function assertions; no synthesis."

#### edge_cases

[
  "A=B=1 makes XOR and NAND zero.",
  "A=0 forces NAND high regardless of B.",
  "The complement can be shared by two outputs in the ideal model."
]

#### common_mistakes

[
  "Do not omit complement cost without declaring it supplied.",
  "Do not transfer permission for constant one to PREP-031's different restrictions."
]

#### interview_answer

"Use A as select, write both cofactors for each function and share NOT B from MUX(B,1,0)."

#### source_ambiguities

[
  "Screenshot eleven adds four functions but omits constant/complement availability; permissions and complement cost are explicit editorial assumptions."
]

#### solution_extensions

{
  "question": "If B and NOT B are already available, how many MUXes and levels does the shown construction use?",
  "direction": "Four parallel MUXes with one level per output. Without the supplied complement, XOR/NAND paths include another inverter level.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

- [solutions/prep_batch20_combinational.py](../solutions/prep_batch20_combinational.py)
- [diagrams/prep-070-combinational-batch20-he.png](../diagrams/prep-070-combinational-batch20-he.png)
- [diagrams/prep-070-combinational-batch20-en.png](../diagrams/prep-070-combinational-batch20-en.png)
