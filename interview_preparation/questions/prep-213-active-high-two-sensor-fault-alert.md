# PREP-213 — התראה משני חיישני תקלה

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-02.png](../sources/2026-10-31-batch20-02.png)

## נוסח המקור / Original wording

נדרש לתכנן בקר עבור רכב בעל שני חיישנים - גלאי חום וגלאי שמן. הבקר מתריע על הדממת הרכב כאשר אחד מהגלאים (שמן או חום) מופעל.

## עברית

תכננו מעגל צירופי לבקר המתראה על הדממת רכב כאשר חיישן חום או חיישן שמן מופעל. הגדירו את קוטביות האותות, כתבו טבלת אמת ומשוואה, ושרטטו מימוש.

הבהרת עריכה: H=1 מציין שחיישן החום מדווח תקלה, O=1 מציין שחיישן השמן מדווח תקלה, ו־E=1 הוא פלט התראה פונקציונלי. גם כאשר שני החיישנים פעילים חייבת להיות התראה. זהו תרגיל לוגי בינארי; אין בנוסח מפרט בטיחות, פקודת בלימה או רשות לתכנן מערכת בטיחות ממשית.

### רמזים / Hints

1. התחילו מארבעת הצירופים האפשריים של שני חיישנים, בלי לבחור שער מראש.
2. מה ההבדל בין לפחות חיישן אחד פעיל לבין בדיוק חיישן אחד פעיל?
3. רק השורה שבה שני החיישנים אפס אינה דורשת התראה. חפשו שער שמתאים לתבנית הזו.

### הצעה לפתרון / Proposed solution

הצעה לפתרון: קודם מתרגמים את המילה 'או' לדרישה התנהגותית. החיישנים אינם מבטלים זה את זה: כאשר שניהם פעילים יש עדיין סיבה להתראה. לכן E=H OR O.

| H | O | E |
|---|---|---|
|0|0|0|
|0|1|1|
|1|0|1|
|1|1|1|

מחברים את H ואת O לכניסות שער OR בעל שתי כניסות ואת מוצאו ל־E. לדוגמה, H=0,O=1 מפיק E=1; גם H=1,O=1 מפיק E=1. הטבלה מכסה את כל תחום הקלט ולכן מוכיחה שהמשוואה מתאימה לדרישה בכל קלט בינארי. העלות הלוגית היא שער OR אחד ועומק שער אחד. אם ספרייה מאפשרת רק חוטים וקבועים ללא רכיב פונקציונלי, אי אפשר לממש את הפונקציה באפס שערים: כל חוט יחיד נותן רק H,O או קבוע, ואף אחד מהם אינו טבלת OR. זהו מינימום רק במודל הזה.

קוטביות היא חלק מהחוזה: בחיישנים פעילים באפס צריך לשנות את המשוואה ולא להעתיק את החיווט. הבדיקה הממצה מאמתת ארבע שורות לוגיות בלבד; אין כאן אבחון נתק חיישן, רעידות, סינון, זיכרון התראה או פעולה על רכב. הפתרון מוצע וממתין לביקורת מקצועית.

### assumptions

[
  "שני אותות בינאריים יציבים; אחד פירושו תקלה; ההתראה פעילה באחד.",
  "ללא זיכרון, סינון או פעולה פיזית; מותר שער OR בעל שתי כניסות."
]

### optimality

"שער OR אחד ועומק אחד; אי אפשר באפס שערים במודל חוטים וקבועים בלבד. אין טענת בטיחות או שטח פיזי."

### verification

"עברו כל ארבע שורות הקלט מול any עצמאי. בדיקת מודל בינארי בלבד, ללא חומרה או בדיקת בטיחות."

### edge_cases

[
  "שני החיישנים אפס: אין התראה.",
  "שניהם אחד: יש התראה.",
  "חיישן פעיל באפס דורש חוזה אחר."
]

### common_mistakes

[
  "XOR שגוי כי הוא מכבה התראה כאשר שתי תקלות פעילות.",
  "אין להניח שהפעלת חיישן פירושה ערך אפס בלי לציין זאת.",
  "טבלת אמת אינה תכן של מערכת בטיחות לרכב."
]

### interview_answer

"אסמן אחד כתקלה ואוציא OR של שני החיישנים. רק כששניהם אפס אין התראה, וגם שתי תקלות יחד מתריעות."

### source_ambiguities

[
  "הצילום אינו מגדיר קוטביות או את משמעות פלט ההדממה. העריכה מגדירה פלט התראה פונקציונלי בלבד.",
  "אין מקור לדרישות בטיחות, בלימה, תזמון או שימור מצב."
]

### solution_extensions

{
  "question": "כיצד משתנה הפלט אם שני החיישנים פעילים באפס אך ההתראה פעילה באחד?",
  "direction": "E=NOT(H AND O), כלומר NAND. כתבו שוב את ארבע השורות; אחד בשני החיישנים פירושו כעת שאין תקלה.",
  "integration": "מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי."
}

## English

Design a combinational controller that issues a vehicle-shutdown alert when either the heat sensor or the oil sensor activates. Define signal polarity, give a truth table and equation, and draw an implementation.

Editorial contract: H=1 means a reported heat fault, O=1 a reported oil fault, and E=1 is a functional alert output. Simultaneous faults must still assert it. This is a binary logic exercise; the source provides no safety specification or brake-actuation command and does not establish a real safety-control design.

### רמזים / Hints

1. Start with all four sensor combinations before choosing a gate.
2. How does at least one active sensor differ from exactly one active sensor?
3. Only the row with both sensors zero needs no alert. Match a gate to that pattern.

### הצעה לפתרון / Proposed solution

Proposed solution: first translate 'or' into behavior. The sensors do not cancel each other: two active faults still require an alert. Therefore E=H OR O.

| H | O | E |
|---|---|---|
|0|0|0|
|0|1|1|
|1|0|1|
|1|1|1|

Connect H and O to a two-input OR gate and its output to E. H=0,O=1 gives E=1, and H=1,O=1 also gives E=1. The table covers the entire binary input domain and proves the equation satisfies the stated behavior. Logical cost is one OR gate and one gate level. If the library otherwise permits only wires/constants, zero functional gates cannot implement OR: a single wire produces only H,O or a constant, each differing from the required table. This is a minimum only in that restricted model.

Polarity is part of the contract: active-low sensors require a changed equation. Four exhaustive Boolean rows were checked; this does not diagnose broken sensors, chatter, filtering, stored alerts or vehicle actuation. The solution remains proposed and awaits professional review.

### assumptions

[
  "Two settled binary signals; one denotes fault; alert is active high.",
  "No memory, filtering or physical actuation; a two-input OR gate is allowed."
]

### optimality

"One OR gate and one level; zero gates are impossible with only wires/constants. No safety or physical-area claim."

### verification

"All four input rows passed an independent any oracle. Binary model only; no hardware or safety validation."

### edge_cases

[
  "Both sensors zero: no alert.",
  "Both one: alert remains asserted.",
  "An active-low sensor requires a different contract."
]

### common_mistakes

[
  "XOR is wrong because two faults would clear the alert.",
  "Do not silently assume an activated sensor has value zero.",
  "A truth table is not a vehicle safety-system design."
]

### interview_answer

"Define one as a fault and OR the sensors. Only two zeros suppress the alert; two simultaneous faults still assert it."

### source_ambiguities

[
  "The screenshot omits polarity and shutdown-output semantics. The edited exercise defines only a functional alert.",
  "No safety, braking, timing or state-retention requirements are supplied."
]

### solution_extensions

{
  "question": "How does the equation change if both sensors are active low but the alert is active high?",
  "direction": "E=NOT(H AND O), a NAND. Rebuild all four rows: both sensor ones now mean no fault.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_batch20_combinational.py](../solutions/prep_batch20_combinational.py)
- [diagrams/prep-213-combinational-batch20-he.png](../diagrams/prep-213-combinational-batch20-he.png)
- [diagrams/prep-213-combinational-batch20-en.png](../diagrams/prep-213-combinational-batch20-en.png)
