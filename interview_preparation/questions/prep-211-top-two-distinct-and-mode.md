# PREP-211 — שני הערכים הגדולים השונים והשכיח במערך לא ממוין

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-03.png](../sources/2026-10-31-batch20-03.png)

## נוסח המקור / Original wording

מקבלים מערך שאינו ממוין, המכיל מספרים (טווח המספרים אינו ידוע). א. יש לפלוט את שני המספרים הגדולים ביותר במערך וכמה פעמים הם מופיעים בו. ב. כעת יש לפלוט את המספר שמופיע הכי הרבה פעמים במערך.

## עברית

נתון מערך לא ממוין של מספרים שלמים שטווחם אינו ידוע. א. החזירו את שני הערכים השונים הגדולים ביותר ואת מספר ההופעות של כל אחד. ב. החזירו ערך שמופיע בתדירות מרבית ואת תדירותו. נתחו זמן וזיכרון והסבירו מה ההבדל בין שתי המשימות. אין לשנות את המערך.

השלמות עריכה: “שני הגדולים” פירושו שני ערכים שונים, ולא שני מקומות המכילים אותו מקסימום. חלק א מחזיר זוג תוצאות בסדר יורד; תוצאה חסרה מסומנת None. מערך ריק מחזיר (None,None), וערך שונה יחיד מחזיר ((value,count),None). בחלק ב, בשוויון תדירויות בוחרים בערך המספרי הקטן ביותר; במערך ריק מחזירים None. אין הבטחה שקיים רוב של יותר מחצי. העלות נמדדת בפעולות השוואה ומפה רגילות.

### רמזים / Hints

1. בחלק א, אחרי שראיתם קידומת, איזה מספר קטן וקבוע של מועמדים מספיק לשמור?
2. כשמגיע מקסימום חדש, המקסימום הקודם הופך לשני בגודלו יחד עם המונה שכבר צבר. הופעה חוזרת אינה יוצרת מועמד שני.
3. לשכיח אין די בשני הערכים הגדולים. ספרו הופעות לכל ערך במפה, ועדכנו מועמד מוביל לפי תדירות ואחריה הערך הקטן בשוויון.

### הצעה לפתרון / Proposed solution

### חלק א: שני מקומות עם אינווריאנט לקידומת
נשמור first ו־second, שני הערכים השונים הגדולים ביותר בקידומת שעובדה, ואת המונים שלהם. None מציין מקום שלא התמלא; הוא אינו סף מספרי ולכן עובד גם כשהמספרים שליליים או גדולים מאוד. אם איבר חדש שווה ל־first, נגדיל רק את המונה הראשון. אם הוא גדול ממנו, נעביר את first והמונה שלו אל second, ונציב את האיבר החדש ב־first עם מונה אחת. אחרת נטפל בהופעה נוספת של second או בערך גדול ממנו, ונזניח ערך קטן משני המועמדים.

הוכחת האינווריאנט באינדוקציה: בקידומת ריקה שני המקומות חסרים. איבר שווה משנה תדירות בלבד. מקסימום חדש דוחק את המקסימום הקודם למקום השני, וכל שאר הערכים קטנים ממנו. ערך שבין שני המועמדים מחליף רק את השני, וערך נמוך יותר אינו יכול להשפיע על שתי התוצאות. מונה של ערך שמקודם נשמר במלואו. ערך שנדחה בעבר אינו יכול פתאום להפוך לאחד משני הגדולים, כי הסף השני אינו יורד. לכן בסיום גם הערכים וגם המונים מדויקים.

### חלק ב: מספרי הופעות, לא סדר מספרי
לשכיח צריך לעקוב אחר תדירויות כל הערכים השונים. נשתמש במפת counts; על כל איבר נגדיל את ספירתו. רק ספירה זו השתנתה, ולכן מספיק להשוות את אותו ערך אל best: תדירות גבוהה יותר מנצחת; בשוויון הערך הקטן יותר מנצח. זה שומר באינדוקציה על השכיח של כל קידומת לפי כלל השוויון שנבחר. במערך ריק לא קיים שכיח, והתשובה None.

בדוגמה [5,5,4,4,2] שתי התוצאות של חלק א הן (5,2) ו־(4,2). בשכיח יש תיקו בין 4 לבין 5, ולכן חלק ב מחזיר (4,2). בדוגמה [-4,-2,-4,-2], הערך הגדול הוא -2 והשני -4; השכיח שנבחר הוא דווקא -4. כך רואים ששני החלקים מודדים דברים שונים.

### עלות וחלופות
חלק א עושה מעבר יחיד, O(n) זמן ו־O(1) זיכרון נוסף. Ω(n) זמן נדרש במקרה הגרוע: איבר שלא נקרא עשוי להיות מקסימום חדש או לשנות את מונה המקסימום. לכן הזמן Θ(n) אופטימלי. חלק ב מבצע O(n) פעולות מפה בתוחלת תחת הנחת hash רגילה, ושומר O(k) רשומות עבור k ערכים שונים; זוהי טענת תוחלת, לא חסם זמן גרוע קבוע לכל hash. ערכים שלמים ארוכים עדיין כרוכים בעלות השוואה וחישוב hash התלויה באורך הביטים אם מנתחים מודל ביטים.

חלופה דטרמיניסטית היא למיין עותק ולסרוק רצפים, עם O(n log n) השוואות ו־O(n) מקום לעותק השומר על המקור; אפשר גם עץ מאוזן עם O(n log k) פעולות ו־O(k) זיכרון. אי אפשר להקצות מערך תדירויות לפי טווח שלא הוגדר. Boyer–Moore מוצא מועמד לרוב חמור של יותר מחצי, אם קיים; הוא אינו אלגוריתם כללי לשכיח. לדוגמה, ברשימה [1,1,2,2,3] שכיחים 1 ו־2 אך אין רוב, והמועמד של ביטול זוגות יכול להיות 3. גם אימות שמועמד אינו רוב לא מחזיר את השכיח.

### בדיקה, טעויות והמשך
10,046 מערכים נבדקו מול אורקל עצמאי של מיון ערכים שונים וספירות: כל 9,841 המערכים מעל -2,0,3 באורכים אפס עד שמונה, 200 דגימות קבועות זרע ועוד חמישה מקרי גבול. נבדקו תיקו, ערך שונה יחיד, שליליים, מספרים ברוחב מאות ביטים ושמירת הקלט. אין בכך הוכחה לכיול קושי או לביקורת אנושית.

תשובה קצרה: “לשני הגדולים אשמור שני ערכים שונים ומונים במעבר אחד ובזיכרון קבוע. לשכיח אספור כל ערך במפה, ואבחר לפי תדירות ואחריה הערך הקטן ביותר.” בהמשך: אם מובטח רוב של יותר מחצי, אפשר Boyer–Moore במעבר ובזיכרון קבוע, ואז מעבר אימות כשנדרש. ההבטחה החדשה היא שמאפשרת את החיסכון.

```python
"""Nonmutating algorithms for an unsorted array of integers of unknown range."""


def top_two_distinct(values):
    """Return ((largest, count), (second_distinct, count)); missing = None."""
    first = second = None
    first_count = second_count = 0
    for value in values:
        if first is not None and value == first:
            first_count += 1
        elif first is None or value > first:
            second, second_count = first, first_count
            first, first_count = value, 1
        elif second is not None and value == second:
            second_count += 1
        elif second is None or value > second:
            second, second_count = value, 1
    return ((first, first_count) if first is not None else None,
            (second, second_count) if second is not None else None)


def mode_with_count(values):
    """Return (mode, frequency), ties resolved to the smallest integer; empty=None."""
    counts = {}
    best = None
    best_count = 0
    for value in values:
        count = counts.get(value, 0) + 1
        counts[value] = count
        if count > best_count or (count == best_count and (best is None or value < best)):
            best, best_count = value, count
    return (best, best_count) if best is not None else None
```


### assumptions

[
  "קלט של מספרים שלמים, לא ממוין וללא טווח ידוע; אין לשנותו.",
  "שני ערכים גדולים שונים; תוצאה חסרה None; לשכיח בשוויון בוחרים את הערך הקטן. אין הבטחת רוב."
]

### optimality

"שני הגדולים: Θ(n) זמן ו־O(1) מקום, עם חסם תחתון של קריאת הקלט. שכיח במפה: O(n) זמן צפוי ו־O(k) רשומות; אין כאן טענה לחסם גרוע של O(n) עבור hash."

### verification

"בוצעו 10,046 בדיקות: 9,841 מערכים ממצים באורך 0..8 מעל שלושה ערכים, 200 דגימות ו־5 גבולות. אורקל מיון וספירה עצמאי בדק ערכים, מונים, תיקו ואי־שינוי קלט."

### edge_cases

[
  "מערך ריק; איבר יחיד; כל האיברים שווים; בדיוק שני ערכים שונים.",
  "מספרים שליליים ואפס; מקסימום חדש אחרי הופעות רבות של הקודם; תיקו בין שכיחים; מספרים גדולים מאוד."
]

### common_mistakes

[
  "להחזיר את אותו מקסימום בשני המקומות.",
  "לאבד את המונה כשהמקסימום הקודם עובר למקום שני.",
  "לאתחל מקסימום לאפס ולשבור מערך שלילי.",
  "להניח טווח קטן למערך ספירות; לבלבל שכיח עם רוב Boyer–Moore; למיין את המקור למרות איסור שינוי."
]

### interview_answer

"שני ערכים שונים ומונים מספיקים לשני הגדולים במעבר יחיד. לשכיח צריך תדירויות לכל הערכים במפה; בתיקו אבחר את הקטן. אציין תוצאות חסרות ותוחלת hash."

### source_ambiguities

[
  "המקור אינו מגדיר אם “שני הגדולים” שונים, מה קורה במערך ריק או בשוויון שכיחים. אלו השלמות עריכה מפורשות.",
  "המקור אינו מתיר שינוי במפורש ואינו מגביל טווח; נבחר חוזה משמר־קלט ללא מערך תדירויות ישיר."
]

### solution_extensions

{
  "question": "אם מובטח שערך אחד מופיע יותר ממחצית הפעמים, האם אפשר פחות זיכרון?",
  "direction": "Boyer–Moore שומר מועמד ומאזן ביטולים ב־O(1) מקום. אם ההבטחה אינה אמינה, מעבר שני מאמת רוב; הוא לא מוצא שכיח כללי כשאין רוב.",
  "integration": "מוכן בתוכן; לא מחובר לתור המשך אינטראקטיבי."
}

## English

Given an unsorted array of integers whose range is unknown: (a) return the two largest distinct values and the frequency of each; (b) return a most frequent value and its frequency. Explain the difference between the tasks and analyze time and space. Do not modify the array.

Editorial completions: “two largest” means distinct values, rather than two positions containing the same maximum. Part(a) returns two descending result slots, using None for an absent value: an empty array returns (None,None), and one distinct value returns ((value,count),None). For part(b), break frequency ties by choosing the smallest numeric value; return None on empty input. No strict majority is promised. Costs count ordinary comparison/map operations.

### רמזים / Hints

1. In part(a), how many candidates suffice after processing a prefix?
2. A new maximum promotes the previous maximum, including its accumulated count, to second place. Repeating a maximum does not create a second distinct value.
3. The mode is unrelated to the two numerically largest values. Count every distinct value in a map and compare candidates by frequency, then by smaller value.

### הצעה לפתרון / Proposed solution

### Part(a): two slots with a prefix invariant
Maintain first and second, the two largest distinct values in the processed prefix, together with their counts. None denotes an absent slot rather than a numeric threshold, so negatives and very large integers work. If a new element equals first, increment only its count. If it exceeds first, promote the old first and its entire count into second, then set first to the new value with count one. Otherwise increment second when equal, replace second when exceeded, or discard an element below both candidates.

Prove the invariant by induction. Both slots are absent in the empty prefix. Equality changes only a frequency. A new maximum makes the old maximum second-largest, above all other values. A value between the candidates changes only second; a lower value cannot affect either result. Counts travel with promoted values. A value discarded earlier cannot later become a top-two candidate because the second-place threshold never decreases. Thus both final values and their counts are correct.

### Part(b): frequencies rather than numeric rank
The mode needs frequency information for all distinct values. Maintain a counts map and increment the current element. Only its count changed, so compare it against best: larger frequency wins; equal frequency chooses the smaller integer. By induction best is the prefix mode under the declared tie rule. An empty array has no mode, so return None.

For [5,5,4,4,2], part (a) returns (5,2) and (4,2). Values 4 and 5 tie for the mode, so part (b) returns (4,2). For [-4,-2,-4,-2], the largest value is -2 and second-largest is -4, while the selected mode is -4. Numeric rank and frequency rank are different tasks.

### Cost and alternatives
Part(a) takes one pass, O(n) time and O(1) additional space. Worst-case Ω(n) time is necessary because an unread element might be a new maximum or change a returned frequency. Therefore Θ(n) time is optimal. Part(b) performs expected O(n) map operations under ordinary hashing and stores O(k) entries for k distinct values; this is an expected-time claim rather than a worst-case constant-time guarantee for every hash table. In a bit-cost model, comparisons and hashing of arbitrary-width integers also depend on their bit lengths.

A deterministic alternative sorts a copy and scans equal-value runs, taking O(n log n) comparisons and O(n) space for the copy that preserves the input. A balanced tree offers O(n log k) operations and O(k) storage. Do not allocate a direct-address frequency array for an unstated numeric range. Boyer–Moore finds a strict-majority candidate when a value occurs more than half the time; it is not a general mode algorithm. For [1,1,2,2,3], values 1 and 2 are modes, no majority exists, and pair cancellation can leave candidate 3. Discovering that the candidate is not a majority still does not find the mode.

### Verification, pitfalls and continuation
10,046 arrays were checked against an independent sorted-distinct/count oracle: all 9,841 arrays over -2,0,3 of lengths 0..8, 200 reproducible samples and five boundary arrays. Coverage includes ties, a single distinct value, negatives, integers hundreds of bits wide and unchanged input. This does not establish calibrated difficulty or human review.

Short answer: “Keep two distinct maxima and their counts in one pass and constant space. For the mode, count all values in a map and choose by frequency, then by smallest value.” Follow up by adding a strict-majority promise: Boyer–Moore then uses constant space, with a verification pass when needed. That new promise enables the saving.

```python
"""Nonmutating algorithms for an unsorted array of integers of unknown range."""


def top_two_distinct(values):
    """Return ((largest, count), (second_distinct, count)); missing = None."""
    first = second = None
    first_count = second_count = 0
    for value in values:
        if first is not None and value == first:
            first_count += 1
        elif first is None or value > first:
            second, second_count = first, first_count
            first, first_count = value, 1
        elif second is not None and value == second:
            second_count += 1
        elif second is None or value > second:
            second, second_count = value, 1
    return ((first, first_count) if first is not None else None,
            (second, second_count) if second is not None else None)


def mode_with_count(values):
    """Return (mode, frequency), ties resolved to the smallest integer; empty=None."""
    counts = {}
    best = None
    best_count = 0
    for value in values:
        count = counts.get(value, 0) + 1
        counts[value] = count
        if count > best_count or (count == best_count and (best is None or value < best)):
            best, best_count = value, count
    return (best, best_count) if best is not None else None
```


### assumptions

[
  "Unsorted integer input of unknown range; preserve the array.",
  "Two largest distinct values; missing result=None; choose the smallest value in a mode tie. No majority promise."
]

### optimality

"Top two:Θ(n) time and O(1) space, matching an input-inspection lower bound. Map mode:expected O(n) time and O(k) entries; no worst-case linear hashing guarantee is asserted."

### verification

"10,046 executed cases: 9,841 exhaustive arrays of length 0..8 over three values, 200 samples and 5 boundaries. Independent sorting/counting checked values, frequencies, ties and input preservation."

### edge_cases

[
  "Empty input; one element; all values equal; exactly two distinct values.",
  "Negatives and zero; a new maximum after many old-maximum repeats; mode ties; very wide integers."
]

### common_mistakes

[
  "Returning the same maximum twice.",
  "Losing the count when promoting the previous maximum to second.",
  "Initializing a maximum to zero and failing on negative arrays.",
  "Assuming a small range for direct counts; confusing a mode with a Boyer–Moore majority; sorting the original despite input preservation."
]

### interview_answer

"Two distinct candidates and counts suffice for the top two in one pass. A general mode needs frequencies for all values in a map; choose the smaller value in a tie. State missing results and expected hash costs."

### source_ambiguities

[
  "Distinctness, empty arrays and mode ties are unspecified in the source and explicitly completed editorially.",
  "The source does not explicitly allow mutation or bound the range; the edited contract preserves input and avoids direct-address counting."
]

### solution_extensions

{
  "question": "Can space be reduced if one value is promised to occur more than half the time?",
  "direction": "Boyer–Moore stores one candidate and cancellation balance in O(1) space. If the promise is uncertain, verify in a second pass; absence of a majority does not solve the general mode problem.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_211_top_two_and_mode.py](../solutions/prep_211_top_two_and_mode.py)
- [diagrams/prep-211-algorithms-batch20-he.png](../diagrams/prep-211-algorithms-batch20-he.png)
- [diagrams/prep-211-algorithms-batch20-en.png](../diagrams/prep-211-algorithms-batch20-en.png)
