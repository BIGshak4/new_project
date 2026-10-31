# PREP-214 — מרבב 4:1 משלושה מרבבי 2:1

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-07.png](../sources/2026-10-31-batch20-07.png)

## נוסח המקור / Original wording

בנה MUX 4->1 ע״י MUXים של 2->1. בתרשים המצורף Q3,Q2 מוזנים למרבב העליון, Q1,Q0 לתחתון; S0 בורר בכל אחד מהם ו-S1 בורר במרבב המוצא.

## עברית

בנו מרבב 4:1 בעזרת מרבבי 2:1. לכל מרבב MUX(S,D0,D1), הבחירה S=0 מחזירה D0 והבחירה S=1 מחזירה D1. הסבירו את מספר הרכיבים ועומק מסלול הנתונים.

שמרו תחילה את חיווט איור המקור: במרבב העליון D0=Q3,D1=Q2; בתחתון D0=Q1,D1=Q0; שניהם נבחרים ב־S0. המרבב האחרון נבחר ב־S1 ומקבל את העליון ב־D0 ואת התחתון ב־D1. כתבו את טבלת הבחירה בפועל. לאחר מכן הראו בנפרד חיווט המתאים למוסכמה הרגילה Out=Q[2*S1+S0]. אין להחליף בשקט את סדר המקור.

### רמזים / Hints

1. חלקו ארבע כניסות לשני זוגות; איזה ביט בחירה יכול לבחור בתוך כל זוג?
2. אחרי שלב הזוגות נשארים שני ערכים. מה יבחר ביניהם, ואיזה זוג שייך ל־D0?
3. כתבו U=MUX(S0,Q3,Q2), L=MUX(S0,Q1,Q0), ואז Out=MUX(S1,U,L); עקבו אחר כל צירוף בחירה.

### הצעה לפתרון / Proposed solution

הצעה לפתרון: כל מרבב קטן בוחר אחת משתי אפשרויות. שני מרבבים במקביל בוחרים בתוך הזוגות, ומרבב שלישי בוחר בין התוצאות:

```text
U = MUX(S0,Q3,Q2)
L = MUX(S0,Q1,Q0)
Out = MUX(S1,U,L)
```

| S1 | S0 | נבחר במקור |
|---|---|---|
|0|0|Q3|
|0|1|Q2|
|1|0|Q1|
|1|1|Q0|

למשל S1S0=10 בוחר את המרבב התחתון ואז את D0 שלו, כלומר Q1. הסדר ההפוך אינו משנה את עצם היותו מרבב 4:1; הוא משנה את הקשר בין קוד הבחירה לשמות הנתונים. לחיווט הסטנדרטי בלבד מחליפים את חיבורי הנתונים: U=MUX(S0,Q0,Q1), L=MUX(S0,Q2,Q3), Out=MUX(S1,U,L). כעת 00,01,10,11 בוחרים Q0,Q1,Q2,Q3. אין צורך להפוך את ביטי הבחירה.

ההוכחה היא מעקב בשתי הבחירות; כל קוד בוחר בדיוק כניסה אחת וכל ארבע הכניסות מכוסות. המימוש משתמש בשלושה מרבבים ובשני מפלסי נתונים. תחת מודל רשת MUX2 חסרת משוב, חוטים ובחירות תלויות רק ב־S1,S0, גם זה מינימום במספר הרכיבים: כדי שהפלט יוכל להיות כל אחת מארבע כניסות נתונים עצמאיות, חרוט הנתונים צריך לפחות ארבעה עלים. ברשת בעלת m צמתי MUX בינאריים מחוברים יש לכל היותר m+1 כניסות נתונים עצמאיות, כי בכל צומת מתווסף לכל היותר עלה אחד; לכן m≥3. עומק אחד יכול לבחור לכל היותר שני עלים ולכן נדרשים לפחות שני מפלסים. חסמים אלה מתייחסים למודל הזה, לא לשטח או השהיה פיזיים כלליים.

נבדקו 64 צירופי נתונים ובחירות לכל חיווט בנפרד, מול אינדוקס עצמאי. אין בדיקת תקלות מעבר, השהיה אנלוגית או סינתזה.

### assumptions

[
  "שש כניסות בינאריות יציבות; אין שעון או משוב.",
  "רק MUX2, חוטים ובחירות התלויות בביטי הבחירה; D0 נבחר באפס."
]

### optimality

"שלושה מרבבים ושני מפלסי נתונים. חסם העלים m+1 מוכיח מינימום רכיבים רק ברשת הנתונים הבינארית המוגדרת; עומק אחד מכסה לכל היותר שני עלים."

### verification

"עברו 64 צירופי קלט בחיווט המקור ו־64 בחיווט הסטנדרטי, מול בחירת איבר ברשימה. לא בוצעה בדיקת השהיה פיזית."

### edge_cases

[
  "00 בוחר Q3 במקור, ולא Q0.",
  "כל הנתונים זהים: הבחירה אינה משנה את התוצאה.",
  "שינוי כמה ביטי בחירה יחד עלול לגרום מעבר זמני שלא נבחן במודל."
]

### common_mistakes

[
  "החלפה שקטה של Q3 ו־Q0 מאבדת את משמעות איור המקור.",
  "שרשור כל שלושת המרבבים בטור יוצר עומק מיותר למבנה הזה.",
  "אין לזהות מספר פורט D1 עם קבוע לוגי אחד."
]

### interview_answer

"שני מרבבים עם S0 בוחרים בזוגות, ושלישי עם S1 בוחר זוג. במקור הקוד 00 בוחר Q3; אפשר לקבל סדר רגיל בהחלפת חיווט הנתונים."

### source_ambiguities

[
  "כותרת המקור אומרת 4:1, אך האיור ממספר נתונים בסדר הפוך למוסכמה נפוצה. שני החוזים ניתנים בנפרד."
]

### solution_extensions

{
  "question": "כיצד בונים מרבב 8:1 באותו מודל, ומה מוכיח את ספירת הרכיבים?",
  "direction": "ארבעה מרבבים, שניים ואחד: שבעה רכיבים ושלושה מפלסים. שמונה עלי נתונים דורשים m+1≥8; עומק d מגיע לכל היותר ל־2^d עלים.",
  "integration": "מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי."
}

## English

Build a 4:1 MUX using 2:1 MUXes, with MUX(S,D0,D1) selecting D0 for S=0 and D1 for S=1. Explain component count and data-path depth.

First preserve the source drawing: upper MUX D0=Q3,D1=Q2; lower MUX D0=Q1,D1=Q0; both use S0. The final MUX uses S1, taking the upper result at D0 and lower result at D1. State the actual selection table. Then separately rewire for the conventional Out=Q[2*S1+S0]. Do not silently change the source ordering.

### רמזים / Hints

1. Split four inputs into two pairs. Which select bit chooses within a pair?
2. After pair selection two values remain. What selects between them, and which pair belongs at D0?
3. Write U=MUX(S0,Q3,Q2), L=MUX(S0,Q1,Q0), then Out=MUX(S1,U,L); follow every select combination.

### הצעה לפתרון / Proposed solution

Proposed solution: a small MUX chooses between two possibilities. Two parallel MUXes choose within pairs, then a third chooses between their results:

```text
U = MUX(S0,Q3,Q2)
L = MUX(S0,Q1,Q0)
Out = MUX(S1,U,L)
```

| S1 | S0 | Source-selected input |
|---|---|---|
|0|0|Q3|
|0|1|Q2|
|1|0|Q1|
|1|1|Q0|

For example 10 chooses the lower MUX and then its D0, Q1. Reversed numbering still implements a 4:1 MUX; it changes the association between select code and input name. For conventional numbering only, rewire the data: U=MUX(S0,Q0,Q1), L=MUX(S0,Q2,Q3), Out=MUX(S1,U,L). Codes 00,01,10,11 now select Q0,Q1,Q2,Q3. Select-bit inversion is unnecessary.

Correctness follows by tracing both selections: each code selects exactly one input, and all four inputs are covered. The construction uses three MUXes and two data levels. In an acyclic MUX2 network with wires and selects depending only on S1,S0, the component count is also minimal: the output data cone must reach four independent data leaves. A connected binary-MUX network with m nodes has at most m+1 independent data leaves, since each added node can introduce at most one additional leaf; hence m≥3. One data level reaches at most two leaves, so at least two levels are needed. These bounds concern this declared model, not general physical area/delay.

All 64 data/select tuples passed for each wiring separately against independent indexing. No transition hazards, analog delay or synthesis were tested.

### assumptions

[
  "Six settled binary inputs; no clock or feedback.",
  "Only MUX2 data nodes, wires and selects depending on select bits; D0 is selected at zero."
]

### optimality

"Three MUXes and two data levels. The m+1 leaf bound proves minimum count only for the declared binary data network; one level can reach at most two leaves."

### verification

"Passed 64 source-wiring tuples and 64 standard-wiring tuples against list selection. No physical delay measurement."

### edge_cases

[
  "00 selects Q3 in the source, not Q0.",
  "Equal data inputs make selection irrelevant to the final value.",
  "Simultaneous select changes may cause unmodeled transient behavior."
]

### common_mistakes

[
  "Silently swapping Q3 and Q0 loses the source mapping.",
  "Putting all three MUXes in series adds unnecessary depth for this construction.",
  "Port D1 does not mean constant logic one."
]

### interview_answer

"Two S0 MUXes select within pairs; one S1 MUX selects the pair. The source maps 00 to Q3; rewiring data gives conventional order."

### source_ambiguities

[
  "The source title says 4:1, while the drawing numbers data in the reverse of a common convention. Both contracts are given separately."
]

### solution_extensions

{
  "question": "How do you build an 8:1 MUX in the same model, and justify the count?",
  "direction": "Use layers of four, two and one: seven components and three levels. Eight data leaves require m+1≥8; depth d reaches at most 2^d leaves.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_batch20_combinational.py](../solutions/prep_batch20_combinational.py)
- [diagrams/prep-214-combinational-batch20-he.png](../diagrams/prep-214-combinational-batch20-he.png)
- [diagrams/prep-214-combinational-batch20-en.png](../diagrams/prep-214-combinational-batch20-en.png)
