# PREP-217 — זיהוי חופף של הרצף 101101: FSM לעומת אוגר הזזה

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-15.png](../sources/2026-10-31-batch20-15.png)

## נוסח המקור / Original wording

נתון רצף 101101. בנה קופסה שמקבלת ביט כל מחזור שעון, וכאשר היא קיבלה את הרצף שביקשו אז שהקופסה תוציא 1. פתרתי את זה במכונת מצבים ואז לפני הטבלאות הוא עצר אותי ושאל איך אפשר לפתור את זה בעוד דרך (רעיון הפתרון מצורף). סעיף ב׳ - מה תופס יותר שטח הפתרון השני או הפתרון הראשון. סעיף ג׳ - מה החסרון המרכזי של הפתרון הראשון לעומת השני. סעיף ד׳ - אמר משהו על פייפ אבל נגמר הזמן.

## עברית

תכננו גלאי סינכרוני המקבל ביט אחד בכל מחזור ומוציא 1 אחרי קליטת הסיומת 101101. אפשרו חפיפות: ברצף 101101101 יש זיהויים בביטים 6 ו־9. הציגו FSM ומימוש חלופי, השוו FF, לוגיקה, השהיה, הספק וגמישות. המקור אינו משלים את סעיף ההספק; אין לייחס לו ניסוח שהומצא. נניח reset למצב התחלה ויציאה אחרי החזית שקלטה את הביט האחרון.

### רמזים / Hints

1. מה צריך לזכור על סוף הקלט כדי לדעת אילו ביטים יכולים להשלים את התבנית?
2. כל מצב יכול לציין את אורך הקידומת הארוכה ביותר של 101101 שהיא גם סיומת של הקלט שכבר נקלט.
3. אחרי זיהוי מלא אל תאבדו את הסיומת 101. לחלופה שמרו את ששת הביטים האחרונים והשוו לקבוע.

### הצעה לפתרון / Proposed solution

ב־FSM אין צורך לשמור את כל ששת הביטים; זוכרים כמה ביטים מתחילת התבנית עדיין מתאימים לסוף הקלט. במכונת Moore נגדיר S0..S6 לפי האורכים 0..6; S6 הוא זיהוי מלא והמוצא בו 1, ובכל יתר המצבים 0. האיפוס הוא S0.

| מצב / קידומת שנזכרה | קלט 0 | קלט 1 | מוצא |
|---|---|---|---|
| S0 / ריקה | S0 | S1 | 0 |
| S1 / 1 | S2 | S1 | 0 |
| S2 / 10 | S0 | S3 | 0 |
| S3 / 101 | S2 | S4 | 0 |
| S4 / 1011 | S5 | S1 | 0 |
| S5 / 10110 | S0 | S6 | 0 |
| S6 / 101101 | S2 | S4 | 1 |

למשל מ־S6 עם 1 הסוף הוא 1011011 והקידומת הארוכה המתאימה היא 1011, ולכן עוברים ל־S4. מחיקה ל־S0 אחרי זיהוי מפספסת חפיפות. באינדוקציה, מעבר שבוחר את הקידומת הארוכה שהיא סיומת משמר את הגדרת המצב; S6 מתקבל בדיוק כאשר שש הכניסות האחרונות הן 101101. ברצף 101101101 המצבים הם 1,2,3,4,5,6,4,5,6, ולכן הפלט עולה בביטים 6 ו־9.

אפשר גם Mealy עם שישה מצבי קידומת 0..5: ב־S5 וקלט 1 פולטים 1 וחוזרים ל־S3, כי 101 היא סיומת שכבר תואמת. גם כאן דרושים 3 ביטי מצב בקידוד בינארי. פלט Mealy צירופי תלוי בקלט ובתזמונו; רישום פלט האירוע מוסיף FF. Moore בן שבעה מצבים דורש 3 FF ופענוח S6. אם יש מחזורים לא תקפים, state נשמר ופלט Moore עשוי להישאר 1; פלט אירוע חד־מחזורי דורש חוזה/דגל נוסף. השאלה הראשית מניחה ביט בכל מחזור.

החלופה היא אוגר הזזה בן 6 ביטים: window_next={window[4:0],bit}; אחרי החזית detected=(window==6'b101101). זו השוואה לקבוע, שניתנת לצמצום לרשת AND של ביטים ישרים ומהופכים. יש 6 FF ועוד לוגיקת השוואה. reset לאפס מונע זיהוי מזויף בששת מחזורי ההתחלה: התבנית מתחילה ב־1 והאפסים שנותרו מצד שמאל מונעים שוויון עד שהחלון מלא. עבור תבנית אחרת שמתחילה באפס ייתכן צורך במונה מילוי או valid.

FSM חוסכת ביטי מצב כאן (3 מול 6) אך דורשת לוגיקת מעבר ופענוח, ועל שינוי תבנית צריך בדרך כלל לייצר מחדש טבלה. אוגר הזזה מאפשר השוואה לתבנית הניתנת לתכנות ולעיתים קל יותר לתזמן ולבדוק. אין מנצח כללי בשטח כולל, תדר מרבי או הספק בלי ספריית תאים, מיפוי, fanout, תדר ופעילות מיתוג. FF נוספים מעלים קיבול שעון, ולוגיקה עמוקה/גליצ'ים יכולים לשנות הספק; clock-enable עשוי לעזור כשאין נתון. pipeline של המשווה מוסיף השהיה ולכן משנה את חוזה היציאה.

90,114 קידומות מתוך כל 8,191 הרצפים באורכים 0..12 הושוו לאורקל חיפוש סיומת, בשלושה מודלים: Moore, Mealy וחלון. זו בדיקה ממצה בתחום הזה בלבד. קוד Python ו־RTL מצורפים; אין כאן הוכחת תזמון או הספק.

אימות RTL שבוצע בפועל: Moore ואוגר הזזה קומפלו והורצו מול assertions בכל511 הרצפים באורכים0..8, שהם3,586 קידומות, ובדוגמת החפיפה101101101 עם זיהויים6,9. טווח Python הגדול יותר וגרסת Mealy נבדקו בנפרד במודל בלבד. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

### assumptions

[
  "התבנית קבועה 101101; קלט סינכרוני אחד בכל מחזור; חפיפות מותרות; מוצא אחרי קליטת הביט האחרון; reset ל־S0/חלון אפס."
]

### optimality

"Moore: שבעה מצבי קידומת ו־3 FF; Mealy: שישה ו־3 FF, ועוד FF אם רושמים פלט; חלון:6 FF. אין טענה לאופטימום שטח תאים/תדר/הספק."

### verification

"כל 8,191 הרצפים באורכים 0..12: 90,114 בדיקות קידומת מול אורקל סיומת, בשלושה מודלים; חפיפות 6,9; reset ו־hold. מודל Python. אימות RTL שבוצע בפועל: Moore ואוגר הזזה קומפלו והורצו מול assertions בכל511 הרצפים באורכים0..8, שהם3,586 קידומות, ובדוגמת החפיפה101101101 עם זיהויים6,9. טווח Python הגדול יותר וגרסת Mealy נבדקו בנפרד במודל בלבד. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה."

### edge_cases

[
  "פחות משישה ביטים; רצף אפסים/אחדות; חפיפות; reset באמצע תבנית; מחזור ללא נתון והבחנה בין פלט מצב לפולס אירוע."
]

### common_mistakes

[
  "איפוס ל־S0 לאחר זיהוי מפסיד חפיפה.",
  "ספירת 6 מצבי Moore במקום 7 כולל ההתחלה וההתאמה המלאה.",
  "לטעון ש־FSM תמיד מהירה יותר או שאוגר תמיד צורך יותר הספק."
]

### interview_answer

"אשמור את אורך קידומת 101101 שהיא סיומת הקלט: שבעה מצבי Moore, שלושה FF. חלופה היא שישה FF ומשווה. חפיפות מחייבות מעברי fallback; שטח ותדר בפועל דורשים סינתזה."

### source_ambiguities

[
  "המקור אינו מציין Moore/Mealy, חפיפות או תזמון; הושלם חוזה מפורש. סעיף ההספק נקטע, ולכן מוצג רק דיון הנדסי נפרד."
]

### solution_extensions

{
  "question": "כיצד תומכים בתבנית הניתנת לתכנות?",
  "direction": "אוגר הזזה ומשווה לרגיסטר תבנית הם בסיס פשוט; יש להגדיר אורך, valid למילוי ושינוי תבנית אטומי. FSM ניתנת להגדרה דרך טבלת מעבר, במחיר אחסון ושליטה.",
  "integration": "מוכן בתוכן; אינו מחובר לתור אינטראקטיבי."
}

## English

Design a synchronous detector accepting one bit per cycle and outputting one after suffix 101101 is received. Allow overlaps: 101101101 matches at bits 6 and 9. Give an FSM and another implementation; compare FFs, logic, delay, power and flexibility. The source leaves its power question unfinished. Assume reset to the initial state and output after the edge accepting the final bit.

### רמזים / Hints

1. What summary of the input suffix tells you which next bits can complete the pattern?
2. Let a state be the longest prefix of 101101 that is also a suffix of the accepted input.
3. After a full match retain the suffix 101. Alternatively store the last six bits and compare to the constant.

### הצעה לפתרון / Proposed solution

An FSM need not retain all six bits: remember how much of the pattern's beginning still matches the input suffix. A Moore machine has S0..S6 for matched lengths 0..6, with output one only in S6 and reset S0.

| State / retained prefix | Input 0 | Input 1 | Output |
|---|---|---|---|
| S0 / empty | S0 | S1 | 0 |
| S1 / 1 | S2 | S1 | 0 |
| S2 / 10 | S0 | S3 | 0 |
| S3 / 101 | S2 | S4 | 0 |
| S4 / 1011 | S5 | S1 | 0 |
| S5 / 10110 | S0 | S6 | 0 |
| S6 / 101101 | S2 | S4 | 1 |

From S6 on one, suffix 1011011 retains longest matching prefix 1011, so the next state is S4. Clearing to S0 after a match loses overlaps. Inductively, choosing the longest pattern prefix that is a suffix preserves the state definition, and S6 occurs exactly when the latest six inputs are 101101. Input 101101101 visits 1,2,3,4,5,6,4,5,6, matching at bits 6 and 9.

A Mealy alternative uses the six prefix states 0..5. At S5 on one it outputs one and returns to S3, preserving suffix 101. Binary encoding still uses 3 state FFs. A combinational Mealy output depends on input timing; registering the event adds an FF. Seven-state Moore needs 3 FFs and S6 decoding. If invalid cycles exist, state holds and its Moore output may stay high; a one-cycle event pulse requires an additional contract/flag. The main question accepts a bit every cycle.

The other implementation is a six-bit shift register: window_next={window[4:0],bit}; after the edge detected=(window==6'b101101). Comparison to this constant reduces to an AND network of true and inverted bits. It uses 6 FFs plus comparison logic. Resetting the window to zero prevents startup false matches here: the pattern begins with one, so leading reset zeros prevent equality before six inputs have arrived. A different pattern beginning with zero may need a fill counter or valid.

The FSM saves state bits here (3 versus 6) but needs next-state/decode logic and generally a regenerated table when the pattern changes. A shift register supports a programmable comparison pattern and may be easier to time or inspect. Total area, maximum frequency and power have no universal winner without a cell library, mapping, fanout, frequency and activity. More FFs add clock capacitance, while deep logic/glitches affect switching power; enables can help when no data arrive. Pipelining the comparator changes the output latency contract.

Three models (Moore, Mealy and window) were compared with an independent suffix oracle for 90,114 prefixes of all 8,191 streams of lengths 0..12. Exhaustiveness is limited to that range. Python and RTL are provided; no timing or power result is claimed.

Actual RTL validation: Moore and shift-register implementations compiled and passed assertions on all511 streams of lengths0..8 (3,586 prefixes), plus overlap101101101 at positions6,9. The larger Python range and Mealy alternative were separately model-checked. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

### assumptions

[
  "Fixed pattern 101101; one synchronous bit per cycle; overlaps allowed; output after the final bit is accepted; reset S0/zero window."
]

### optimality

"Moore: seven prefix states and 3 FFs; Mealy: six and 3 FFs plus an FF for registered output; window: 6 FFs. No mapped-area/frequency/power optimum is claimed."

### verification

"All 8,191 streams of lengths 0..12: 90,114 prefix comparisons against a suffix oracle in three models; overlap 6,9; reset/hold. Python model. Actual RTL validation: Moore and shift-register implementations compiled and passed assertions on all511 streams of lengths0..8 (3,586 prefixes), plus overlap101101101 at positions6,9. The larger Python range and Mealy alternative were separately model-checked. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed."

### edge_cases

[
  "Fewer than six bits; all zeros/ones; overlap; reset mid-pattern; idle cycles and state-level versus event-pulse output."
]

### common_mistakes

[
  "Resetting to S0 after detection loses overlaps.",
  "Counting six Moore states instead of seven including empty and full match.",
  "Claiming an FSM is always faster or a shift register always uses more power."
]

### interview_answer

"Track the longest prefix of 101101 that is an input suffix: seven Moore states, three FFs. Alternatively use six FFs and a comparator. Fallback transitions preserve overlap; real area/timing require synthesis."

### source_ambiguities

[
  "The source omits Moore/Mealy choice, overlap and output timing; an explicit contract is added. Its power section is unfinished, so only a separate engineering discussion is supplied."
]

### solution_extensions

{
  "question": "How would you support a programmable pattern?",
  "direction": "Use a shift register and comparator against a pattern register; define length, fill validity and atomic updates. A programmable transition table is another storage/control tradeoff.",
  "integration": "Prepared in content; not connected to the interactive queue."
}

## קבצים / Files

- [solutions/prep_216_220_sequential.py](../solutions/prep_216_220_sequential.py)
- [solutions/prep_216_220_sequential.sv](../solutions/prep_216_220_sequential.sv)
- [solutions/prep_216_220_sequential_tb.sv](../solutions/prep_216_220_sequential_tb.sv)
- [diagrams/prep-217-batch20-sequential.png](../diagrams/prep-217-batch20-sequential.png)
- [diagrams/prep-217-batch20-sequential-he.png](../diagrams/prep-217-batch20-sequential-he.png)
