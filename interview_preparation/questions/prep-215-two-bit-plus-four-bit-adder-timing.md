# PREP-215 — חיבור מספר בן שתי סיביות למספר בן ארבע

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-12.png](../sources/2026-10-31-batch20-12.png)

## נוסח המקור / Original wording

השאלה חולקה למספר סעיפים. א. כאשר מחברים מספר המיוצג ע״י 2 סיביות a1-a2 ומספר המיוצג ע״י 4 סיביות b1-b4 בכמה סיביות התוצאה תיוצג? ב. בהינתן FA בלבד, ממש מכונה שעושה את החיבור עבור שני המספרים הנתונים. ג. בהינתן כעת שהדילאיי של כל FA הוא 1ns, מה הדילאיי הכולל של המכונה? ד. בהינתן מוקס בלי דילאיי, האם ניתן לייעל את המימוש? אם כן ממש אותו, מהו הדילאיי החדש? אם לא הסבר.

## עברית

א. מחברים מספר A המיוצג בשתי סיביות ומספר B המיוצג בארבע סיביות. מהו רוחב התוצאה המינימלי ששומר את הסכום המלא?
ב. בהינתן רכיבי FA בלבד, ממשו את החיבור.
ג. אם לכל FA השהיה של 1 ns, מהי השהיית המימוש?
ד. אם מוסיפים מרבבים בעלי השהיה אפס, האם אפשר לשפר, ומהי משמעות בקשה להשהיה מינימלית?

הבהרות: A,B הם unsigned, אין carry-in חיצוני, וחוטים וקבועי 0/1 אינם עולים בזמן. כל אחד משני פלטי FA מתקבל 1 ns לאחר האחרון מקלטיו. יש להבחין בין שיפור לארכיטקטורת FA מוגדרת לבין המודל המילולי שבו מספר מרבבים חסרי השהיה אינו מוגבל. המקור לא מגביל את האחרון.

### רמזים / Hints

1. חשבו קודם את הערך הגדול ביותר של כל אופרנד; אין צורך לנחש לפי סכום רוחבי הקלט.
2. הרחיבו את A באפסים וחשבו איך carry עובר בין ארבע עמדות FA. איזה מסלול הוא הארוך ביותר?
3. לשיפור עם מרבבים הכינו מראש תוצאה לשתי אפשרויות carry. אבל שאלו גם: מה אפשר לממש ממרבבים וקבועים בלבד אם ההשהיה שלהם באמת אפס?

### הצעה לפתרון / Proposed solution

הצעה לפתרון: A≤3 ו־B≤15 ולכן A+B≤18. ארבע סיביות מחזיקות רק עד 15, וחמש עד 31; לפיכך רוחב התוצאה המינימלי הוא **5 סיביות**, לא 6. 3+15=18=10010 הוא מקרה שמחייב את הסיבית החמישית.

מרחיבים את A ל־00A1A0. מציבים ארבעה FA בעמדות 0..3, עם C0=0. בכל עמדה FA(Ai,Bi,Ci) מחזיר Si,Ci+1; בעמדות 2,3 הכניסה Ai היא אפס. התוצאה היא C4S3S2S1S0. אין FA חמישי עבור C4: זהו פלט ה־carry של האחרון. אין צורך ב־FA כדי לייצר את שני האפסים של ההרחבה.

זהות כל FA היא A_i+B_i+C_i=S_i+2*C_{i+1}. כופלים כל זהות ב־2^i ומחברים; האיברים הפנימיים של carry מתבטלים ונשארת זהות הסכום המלא. זה מוכיח נכונות לכל זוג קלטים. במודל ההשהיה המוצהר זמני Si,Ci+1 הם max(tAi,tBi,tCi)+1. מכניסות וקבועים בזמן אפס מתקבלות הגעות 1,2,3,4 ns, ולכן ארבעת ה־FA בטור נותנים השהיה מרבית של 4 ns. המסלול יכול להיות פעיל: B2=B3=1 מאפשר ל־carry מהחלק הנמוך להתפשט דרך החלק הגבוה. אין להסיק מכך מינימום פיזי של כל מחבר.

שיפור שאינו טריוויאלי: carry-select בחלוקה 2+2. שני FA מחשבים את שני הביטים הנמוכים ואת C2 בזמן 2 ns. במקביל, שתי שרשראות נפרדות של שני FA מחשבות מראש את החלק הגבוה עבור C2=0 ועבור C2=1. שלושה מרבבים בוחרים את S2,S3,C4 לפי C2. המועמדים והבורר מוכנים עד 2 ns, והמרבבים חסרי השהיה, לכן המבנה המוגדר משתמש בשישה FA ושלושה מרבבים ומסתיים ב־2 ns. זו חלופה שממחישה החלפת שטח בזמן; אין כאן הוכחת אופטימום בין כל הארכיטקטורות.

**המלכודת במילה מינימום:** אם באמת מותר מספר בלתי מוגבל של מרבבי אפס־השהיה וקבועים, הם מסוגלים לממש כל פונקציה בוליאנית באמצעות פירוק לפי משתנה: F=MUX(x,F|x=0,F|x=1). אפשר לבנות לכל אחת מחמש סיביות הסכום עץ בחירה על שש סיביות הקלט, עם עלים קבועים מטבלת 64 הצירופים. אין בו שום רכיב בעל השהיה חיובית, ולכן השהיית המודל היא 0 ns. מכיוון שהשהיות אינן שליליות, זהו המינימום במודל הבלתי מוגבל. תשובה חיובית כגון 2 ns דורשת להצהיר על מגבלה ארכיטקטונית המונעת מימוש מלא במרבבים; אין מגבלה כזו במקור. בחומרה ממשית למרבבים ולחוטים יש השהיה, ולכן אפס זה הוא מסקנת המודל בלבד.

נבדקו כל שמונה שורות FA וכל 64 זוגות האופרנדים בשלוש החלופות מול חיבור מספרי עצמאי. זמני 4/2/0 ns נבדקו במודל ההגעה המוצהר, ללא HDL, סינתזה או מדידת חומרה.

### assumptions

[
  "Unsigned A בן שתי סיביות ו־B בן ארבע; בלי carry-in חיצוני; נדרש סכום ללא איבוד מידע.",
  "חוטים וקבועים חופשיים; כל פלט FA מגיע 1 ns אחרי הקלט המאוחר ביותר.",
  "בחלופה המילולית מספר מרבבי אפס־השהיה אינו מוגבל, ולכן גם מימוש מלא במרבבים מותר."
]

### optimality

"רוחב מינימלי: 5 כי הערך המרבי 18. שרשרת ארבעה FA: 4 ns; carry-select מוגדר עם שישה FA: 2 ns, ללא טענת אופטימום חיובי. במודל MUX בלתי מוגבל חסר השהיה המינימום הוא 0 ns, עם בנייה וחסם אי־שליליות."

### verification

"עברו שמונה שורות FA ו־64 זוגות אופרנדים לכל אחת משלוש ארכיטקטורות. נבדקו רוחב 5 וזמני 4/2/0 ns במודל שהוצהר; לא בוצעה סינתזה."

### edge_cases

[
  "3+15=18 דורש את הסיבית החמישית.",
  "0+0=0; אין carry-in חבוי.",
  "carry-out הוא סיבית תוצאה ולא רכיב FA נוסף.",
  "אפסי הרחבה הם חוטי קבוע, ללא השהיית FA."
]

### common_mistakes

[
  "2+4 אינו חישוב רוחב נכון; רוחב חיבור נקבע מהטווח ולא מסכום הרוחבים.",
  "לספור FA חמישי עבור carry-out מוסיף רכיב מיותר.",
  "לטעון ל־2 ns כמינימום בלי להגביל מרבבי אפס־השהיה מתעלם מהאוניברסליות שלהם.",
  "אין להעתיק את זמני המודל לתא פיזי בלי ספריית השהיות."
]

### interview_answer

"הסכום מגיע עד 18 ולכן צריך חמש סיביות. ארבעה FA עם הרחבת אפס נותנים 4 ns. carry-select מוגדר יכול לתת 2 ns, אבל מרבבי אפס בלתי מוגבלים מאפשרים 0 ns ולכן צריך לברר את מגבלת הארכיטקטורה."

### source_ambiguities

[
  "הצילום לא מגדיר signed, carry-in, השהיות חוטים, זמני פלטי FA או מגבלת מרבבים; ההנחות כאן מפורשות.",
  "המקור שואל על שיפור בעזרת מרבבים, אך אינו שולל מימוש אוניברסלי מלא בהם."
]

### solution_extensions

{
  "question": "אם כל מרבב מוסיף השהיה d>0, מתי חלופת carry-select של 2+2 מהירה מהשרשרת?",
  "direction": "בארכיטקטורה המוצהרת החלקים מוכנים ב־2 ns והבחירה מוסיפה d, כלומר 2+d<4 ולכן d<2 ns. אין בכך הוכחה לאופטימום בכל הארכיטקטורות.",
  "integration": "מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי."
}

## English

a. Add unsigned A represented by two bits to B represented by four bits. What minimum output width retains the complete sum?
b. Implement addition using only full adders (FAs).
c. Each FA has 1 ns delay; what is the implementation delay?
d. If zero-delay MUXes are added, can the design improve, and what does minimum delay mean?

Contract: no external carry-in; wires and 0/1 constants take no time. Each FA output arrives 1 ns after the latest of its inputs. Distinguish improvement within a declared FA architecture from the literal model allowing unlimited zero-delay MUXes, which the source does not restrict.

### רמזים / Hints

1. Find the largest value of each operand before guessing from input widths.
2. Zero-extend A and follow carry through four FA positions. Which path is longest?
3. With MUXes, precompute both carry possibilities. Also ask what MUXes/constants alone can implement if their delay truly is zero.

### הצעה לפתרון / Proposed solution

Proposed solution: A≤3 and B≤15, so A+B≤18. Four bits reach only 15 and five reach 31; the minimum full-result width is **5 bits**, not 6. The case 3+15=18=10010 requires the fifth bit.

Zero-extend A to 00A1A0. Use four FAs at positions 0..3 with C0=0. FA(Ai,Bi,Ci) produces Si,Ci+1; Ai is zero at positions 2 and 3. The result is C4S3S2S1S0. C4 is already the last FA's carry output and needs no fifth FA. Zero-extension constants also require no FAs.

Each FA satisfies A_i+B_i+C_i=S_i+2*C_{i+1}. Multiply each identity by 2^i and sum: internal carry terms cancel, leaving the complete addition identity. This proves correctness for all operand pairs. In the stated delay model each Si,Ci+1 arrives at max(tAi,tBi,tCi)+1. With inputs/constants at zero, arrivals are 1,2,3,4 ns, giving 4 ns worst-case delay for this ripple implementation. A path can be sensitized: B2=B3=1 allows carry from the lower section to propagate through the upper section. This is not a minimum physical-delay claim over all adders.

A nontrivial improvement is 2+2 carry-select. Two FAs compute the low bits and C2 in 2 ns. In parallel, two separate two-FA chains precompute the high section for C2=0 and C2=1. Three MUXes select S2,S3,C4 using C2. Candidates and select arrive by 2 ns; zero-delay MUXes therefore give 2 ns using six FAs and three MUXes. This illustrates an area/time tradeoff, without proving an optimum among every architecture.

**The minimum-delay trap:** if unlimited zero-delay MUXes and constants really are allowed, they can implement any Boolean function by splitting on a variable: F=MUX(x,F|x=0,F|x=1). Each of the five sum bits can be a selection tree over the six input bits with constant leaves from the 64-row truth table. There is no positive-delay component, so model delay is 0 ns. Nonnegative delays give a matching lower bound, making zero the minimum in this unrestricted model. A positive answer such as 2 ns requires an explicit architectural restriction preventing a complete MUX-only implementation; the source supplies none. Actual MUXes and wires have delay, so zero is only a consequence of the ideal model.

All eight FA rows and all 64 operand pairs passed independent arithmetic checks for three architectures. The declared arrival model checks 4/2/0 ns; no HDL compilation, synthesis or hardware timing was performed.

### assumptions

[
  "Unsigned two-bit A and four-bit B; no external carry-in; retain the entire sum.",
  "Wires/constants are free; every FA output arrives 1 ns after its latest input.",
  "The literal alternative has unlimited zero-delay MUXes, so a complete MUX-only implementation is allowed."
]

### optimality

"Minimum width is five because the maximum is eighteen. Four-FA ripple takes 4 ns; the declared six-FA carry-select takes 2 ns without a positive-optimum claim. Unlimited zero-delay MUXes permit 0 ns, with a construction and nonnegativity lower bound."

### verification

"Eight FA rows and 64 operand pairs per architecture passed for three architectures. Verified five-bit width and declared 4/2/0 ns model delays; no synthesis."

### edge_cases

[
  "3+15=18 requires the fifth bit.",
  "0+0=0; no hidden carry-in.",
  "Carry-out is a result bit, not an extra FA.",
  "Zero-extension uses constant wires, not FA delay."
]

### common_mistakes

[
  "2+4 is not the output-width rule; use numeric ranges, not the sum of widths.",
  "A fifth FA for carry-out is unnecessary.",
  "Claiming a 2 ns minimum without restricting zero-delay MUXes ignores their universality.",
  "Do not transfer ideal model timing to physical cells without a delay library."
]

### interview_answer

"The maximum sum is eighteen, needing five bits. Four zero-extended ripple FAs give 4 ns. A declared carry-select gives 2 ns, but unrestricted zero-delay MUXes allow 0 ns, so the architecture must be specified."

### source_ambiguities

[
  "The source omits signedness, carry-in, wire delay, FA output timing and MUX limits; the assumptions here are explicit.",
  "The source asks about MUX improvement but does not exclude a complete universal MUX implementation."
]

### solution_extensions

{
  "question": "If each MUX has delay d>0, when is the 2+2 carry-select alternative faster than ripple?",
  "direction": "For the declared architecture, candidates and select arrive in 2 ns and the final MUX adds d: 2+d<4, hence d<2 ns. This does not prove a global architectural optimum.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_batch20_combinational.py](../solutions/prep_batch20_combinational.py)
- [diagrams/prep-215-combinational-batch20-he.png](../diagrams/prep-215-combinational-batch20-he.png)
- [diagrams/prep-215-combinational-batch20-en.png](../diagrams/prep-215-combinational-batch20-en.png)
