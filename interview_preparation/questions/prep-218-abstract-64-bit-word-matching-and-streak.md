# PREP-218 — התאמת ערכי 64 ביט ושתי התאמות רצופות

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-16.png](../sources/2026-10-31-batch20-16.png)

## נוסח המקור / Original wording

היום קורא טביעות אצבע שמקבל 64 ביטים. הקורא מפעיל את Valid ברגע שמתחיל לפעול. א. בנה מערכת שמוציאה אחד אם טביעת האצבע זהה לטביעה ששמורה במערכת ו0 אחרת. ב. כעת בנה מערכת שמבצעת את אותו הדבר אך הפעם היא צריכה לקבל 2 טביעות אצבע (אחת אחרי השנייה) שזהות זו לזו ורק אז יתקבל 1. ג. בשמורות במערכת 2 טביעות אצבע אקראיות, הצע מכונה עם מינימום עלות וזמן שבודקת האם הטביעה הוא אחת מהאצבעות ששמורות במערכת ואם הוא זהה לאחת מהן תוציא 1.

## עברית

ערך קלט בן 64 ביטים מלווה ב־Valid. א. הפיקו 1 אם דגימה תקפה זהה לערך שנשמר. ב. דרשו שתי דגימות תקפות רצופות שתואמות לאותו ערך שמור. ג. כששמורים שני ערכים שונים, בדקו אם דגימה תקפה שווה לאחד מהם והשוו עלות מול זמן. הכינוי טביעת אצבע הוא הקשר מקור בלבד: ננתח מילים בינאריות מדויקות, ולא זיהוי ביומטרי אמיתי. החוזה שנוסף: Valid מציין נתון יציב שנקלט בחזית, לא תחילת חישוב; מחזורים לא תקפים מדולגים ואינם שוברים רצף.

### רמזים / Hints

1. איזה רכיב בודק שוויון של שתי מילים? מה מונע מ־0 לא מאותחל להיחשב ערך רשום?
2. לשתי התאמות רצופות אין צורך לשמור שוב את כל הדגימה הקודמת: איזה ביט מידע עליה מספיק?
3. שמרו previous_hit. בדגימה תקפה הפלט הוא hit AND previous_hit; בשני ערכים השוו במקביל וחברו OR, או שתפו משווה בשני צעדים.

### הצעה לפתרון / Proposed solution

א. נשמור ref בן 64 ביטים ודגל occupied. נחשב hit=occupied AND (sample==ref). השוויון הוא AND של 64 תוצאות XNOR, והפלט יירשם בחזית שקולטת sample כאשר Valid=1. במחזור ללא קבלה הפלט 0. ערך 0 הוא נתון חוקי; occupied=0 מציין שאין ערך רשום גם אם ביטי ref אופסו. איפוס מלא במימוש המצורף מוחק גם את התפוסה ואת הערכים הרשומים; יש לרשום אותם מחדש לפני אימות. בחוזה חומרה מרובה מחזורים חייבים להפריד start, ready ו־done; השם Valid לבדו אינו מוכיח שהדגימה מוכנה.

ב. נשמור previous_hit, תחילה 0. בכל דגימה תקפה: matched_next=hit AND previous_hit; previous_hit_next=hit. כך שתי התאמות רצופות ברצף הדגימות התקפות מפיקות 1 בקבלה השנייה. אי־התאמה מאפסת את previous_hit. מחזור לא תקף אינו משנה אותו, אבל פלט האירוע הוא 0. ברצף של שלוש התאמות נפיק 1 בשנייה ובשלישית (זוגות חופפים). אם רוצים זוגות לא חופפים או כשל בעקבות idle צריך לשנות במפורש את הבקר.

| previous_hit | hit נוכחי | matched בגרסת זוג | previous_hit הבא |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 1 |
| 1 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 |

האינווריאנט הוא previous_hit=האם הדגימה התקפה האחרונה התאימה; האתחול וההשמה משמרים אותו, ולכן AND עם ההתאמה הנוכחית מוכיח את התנאי. אין צורך ב־64 ביטים נוספים לדגימה הקודמת, כי שוויונה לערך הקבוע כבר סוכם בביט.

ג. נממש שני רגיסטרים בני 64 ביט עם occupied לכל אחד. שני משווי שוויון במקביל ו־OR נותנים hit=(have0 && sample==ref0)||(have1 && sample==ref1) באותה קבלה. נדרשים 128 ביטי נתונים, שני דגלי תפוסה ובקר/פלט לפי הממשק. לחלופה זולה יותר בלוגיקת השוואה נשתמש במשווה אחד, נבחר ref0 ואחריו ref1, ונשמור את הדגימה ותוצאת הבדיקה הראשונה. זה מוסיף רגיסטר דגימה, בקר ולרוב השהיה/הגבלת קצב. ממשק ready מונע דריסת דגימה בזמן בדיקה; אין לטעון שהחלופה חוסכת שטח כולל בלי לספור את האחסון הנוסף.

ה־128 ביטים הם עלות האחסון הישיר של שני ערכים שרירותיים. חסם מידע נכון ליכולת לאכלס 0,1 או 2 ערכים מתוך M=2^64 הוא 1+M+C(M,2)=2^127+2^63+1>2^127, ולכן נדרשים לפחות 128 ביטי מצב כדי להבחין בכל הקבוצות האלה. החסם כולל מידע תפוסה; הוא אינו מוכיח ששני רגיסטרים ועוד דגלים הם אופטימליים בכל קידוד. אם מובטח בדיוק זוג לא־מסודר של ערכים שונים, C(M,2)=2^127−2^63, ולכן אותו נימוק לבדו נותן רק 127 ביטים. אין לטעון בטעות שהביטוי גדול מ־2^127.

קוד RTL מצורף עם טעינת ref0/ref1 בזמן תצורה; תצורה קודמת לדגימה ומאפסת את רצף ההתאמות, ו־pair_mode נשאר קבוע בעסקת אימות. בדיקות Python כיסו 138,240 קידומות של שלוש דגימות ברוחב 3, עם 45 קבוצות שמורות כולל ריק וכפילויות, וכן 2,003 ערכי 64 ביט. אין הוכחת אבטחה ביומטרית, סינתזה או אופטימום פיזי.

אימות RTL שבוצע בפועל: המימוש בן64 ביט קומפל והורץ מול assertions ל־512 דגימות תקפות בשני המצבים, עם ערכי קצה, idle, רישום ו־reset. אלה בדיקות trace מוגבלות, בנוסף לבדיקה הממצה של מודל Python ברוחב3. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

### assumptions

[
  "64 ביטים ללא סימן; השוואה מדויקת למילים מופשטות; Valid מסמן קבלה בחזית; idle מדולג; תצורה קודמת לקלט ומאפסת רצף; global reset מוחק רישום ותפוסה."
]

### optimality

"אחסון ישיר: 64 או 128 ביטי נתונים ועוד תפוסה/בקר. שתי השוואות במקביל נותנות השהיה קטנה יותר ממשווה משותף סדרתי באותו חוזה; אין אופטימום כללי. חסם 128 ביטים לקבוצות בגודל עד2 כולל מידע תפוסה."

### verification

"138,240 בדיקות קידומת ברוחב3, 45 קבוצות שמורות, idle/reset ו־2,003 מקרי64 ביט; בדיקת חסם במספרים שלמים. מודל Python. אימות RTL שבוצע בפועל: המימוש בן64 ביט קומפל והורץ מול assertions ל־512 דגימות תקפות בשני המצבים, עם ערכי קצה, idle, רישום ו־reset. אלה בדיקות trace מוגבלות, בנוסף לבדיקה הממצה של מודל Python ברוחב3. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה."

### edge_cases

[
  "ערך רשום0 לעומת מקום ריק; שני ערכים זהים; התאמה ראשונה בלבד; hit,idle,hit; hit,miss,hit; שלושה hits; reset/תצורה באמצע רצף."
]

### common_mistakes

[
  "לא לשמור דגל תפוסה.",
  "לשמור 64 ביטים קודמים כשמספיק previous_hit.",
  "לספור Valid של תחילת פעולה כאילו הנתון כבר יציב.",
  "לטעון לחיסכון כולל רק מפני שמספר המשווים קטן."
]

### interview_answer

"אשווה דגימה תקפה לרגיסטר תפוס. לשתי התאמות אוסיף previous_hit אחד; idle מדולג. לשני ערכים אשווה במקביל ואחבר OR, או אשתף משווה תוך הגדרת זמן ו־ready וספירת רגיסטר הדגימה."

### source_ambiguities

[
  "Valid במקור מתואר בתחילת פעולת הקורא, ולא ברור אם הנתון יציב. סדרת דגימות, אופן רישום הערכים, חפיפת זוגות ומדד מינימום אינם נתונים; נבחר חוזה מפורש."
]

### solution_extensions

{
  "question": "מה משתנה אם idle צריך לשבור רצף?",
  "direction": "מאפסים previous_hit בכל מחזור ללא קבלה. השוו hit,idle,hit: בחוזה המקורי יש התאמה זוגית, ובחוזה החדש אין.",
  "integration": "מוכן בתוכן; אינו מחובר לתור אינטראקטיבי."
}

## English

A 64-bit input word has Valid. (a) Output one when an accepted sample equals the stored word. (b) Require two consecutive accepted samples matching that same stored word. (c) With two different stored words, determine whether an accepted sample matches either; compare cost and time. The source calls these fingerprints; treat them as exact abstract binary words, not a real biometric system. Added contract: Valid marks stable data accepted on the edge, not operation start; invalid cycles skip and do not break the accepted-sample streak.

### רמזים / Hints

1. Which circuit compares words? How do you distinguish an unoccupied slot from an enrolled zero?
2. For two consecutive matches, what single bit about the previous accepted sample is sufficient?
3. Keep previous_hit. On acceptance output hit AND previous_hit; for two stored words OR parallel comparisons, or share one comparator across two steps.

### הצעה לפתרון / Proposed solution

(a) Keep a 64-bit ref register and an occupied flag. Compute hit=occupied AND (sample==ref). Equality is an AND of 64 XNOR results; register the output at the edge accepting a sample with Valid=1. With no accepted sample the event output is zero. Zero is valid data: occupied=0 means unenrolled even if ref bits reset to zero. Global reset in the supplied implementation clears occupancy and enrolled values, so enroll again before matching. A multicycle reader must distinguish start, ready and done; a signal named Valid does not alone establish data readiness.

(b) Keep previous_hit, initially zero. On each accepted sample set matched_next=hit AND previous_hit and previous_hit_next=hit. The second of two consecutive matching accepted samples produces one. A mismatch clears previous_hit. Invalid cycles leave it unchanged but output zero. Three matches produce outputs on the second and third (overlapping pairs). Nonoverlapping pairs or idle-breaking semantics require an explicit controller change.

| previous_hit | current hit | pair matched | next previous_hit |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| 0 | 1 | 0 | 1 |
| 1 | 0 | 0 | 0 |
| 1 | 1 | 1 | 1 |

The invariant is that previous_hit describes the last accepted sample. Initialization and the update preserve it, so AND with the current hit proves the pair condition. Another 64-bit previous-sample register is unnecessary because its equality to the fixed reference is summarized by one bit.

(c) Use two 64-bit registers, each with occupied. Two parallel equality comparators plus OR give hit=(have0 && sample==ref0)||(have1 && sample==ref1) on the same acceptance. This uses 128 data bits plus two occupancy flags and interface/controller/output state. A shared comparator can select ref0 and then ref1, retaining the sample and first comparison. It adds a sample register and controller and typically latency/throughput restrictions. A ready contract prevents overwrite while busy; do not claim lower total area without counting added storage.

128 bits is the direct storage cost of two arbitrary words. A correct information bound for storing zero, one or two values from M=2^64 possibilities counts 1+M+C(M,2)=2^127+2^63+1>2^127, so at least 128 state bits are needed to distinguish all these sets. That bound includes occupancy information; it does not prove that two raw registers plus flags are optimal under every encoding. If exactly two distinct unordered values are guaranteed, C(M,2)=2^127−2^63, and that argument alone only establishes 127 bits. It is incorrect to claim this binomial coefficient exceeds 2^127.

The RTL supplies configuration loads for ref0/ref1. Configuration takes priority over samples and flushes the match streak; pair_mode stays fixed during a transaction. Python checks covered 138,240 three-sample prefix cases at width 3 across 45 stored collections including empty/duplicate values, plus 2,003 64-bit cases. No biometric security, synthesis or physical optimum is claimed.

Actual RTL validation: the64-bit design compiled and passed assertions on512 accepted samples across single/pair modes, including edge values, idle, enrollment and reset. These bounded traces supplement the exhaustive width3 Python model checks. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

### assumptions

[
  "Unsigned 64-bit abstract values; exact equality; Valid marks edge acceptance; idle skips; configuration precedes sampling and flushes the streak; global reset clears enrollment/occupancy."
]

### optimality

"Direct storage: 64 or 128 data bits plus occupancy/control. Parallel comparison reduces latency relative to serial reuse under the same interface, not a global optimum. The 128-bit bound for sets of size at most two includes occupancy information."

### verification

"138,240 width-3 prefix checks, 45 stored collections, idle/reset and 2,003 64-bit cases; integer information-bound check. Python model. Actual RTL validation: the64-bit design compiled and passed assertions on512 accepted samples across single/pair modes, including edge values, idle, enrollment and reset. These bounded traces supplement the exhaustive width3 Python model checks. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed."

### edge_cases

[
  "Enrolled zero versus empty slot; duplicate entries; only one hit; hit,idle,hit; hit,miss,hit; three hits; reset/configuration during a streak."
]

### common_mistakes

[
  "Omitting occupancy.",
  "Storing the whole previous 64-bit sample when previous_hit suffices.",
  "Treating an operation-start Valid as stable data.",
  "Claiming total savings solely from fewer comparators."
]

### interview_answer

"Compare an accepted word against an occupied reference. Add previous_hit for two matches, skipping idle. For two references OR parallel comparisons, or share a comparator while defining latency/ready and counting sample storage."

### source_ambiguities

[
  "Source Valid is described at reader start, so stable-data timing is unclear. Sampling, enrollment, pair overlap and the minimum metric are unspecified; an explicit contract is chosen."
]

### solution_extensions

{
  "question": "What changes if idle must break a streak?",
  "direction": "Clear previous_hit on every unaccepted cycle. For hit,idle,hit the original contract matches the pair; the revised contract does not.",
  "integration": "Prepared in content; not connected to the interactive queue."
}

## קבצים / Files

- [solutions/prep_216_220_sequential.py](../solutions/prep_216_220_sequential.py)
- [solutions/prep_216_220_sequential.sv](../solutions/prep_216_220_sequential.sv)
- [solutions/prep_216_220_sequential_tb.sv](../solutions/prep_216_220_sequential_tb.sv)
- [diagrams/prep-218-batch20-sequential.png](../diagrams/prep-218-batch20-sequential.png)
- [diagrams/prep-218-batch20-sequential-he.png](../diagrams/prep-218-batch20-sequential-he.png)
