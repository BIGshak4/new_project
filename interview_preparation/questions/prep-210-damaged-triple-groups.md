# PREP-210 — זיהוי הערך של שלשה שנמחקו ממנה שני איברים

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-01.png](../sources/2026-10-31-batch20-01.png)

## נוסח המקור / Original wording

ישנו מערך בעל 255 תאים ובו מספרים מסודרים בשלשות (יכולות להיות כפילויות בשלשות, לדוגמא - 1,1,1,5,5,5,1,1,1), והוצאנו שני מספרים השייכים לאותה השלשה. כיצד נדע איזה מספר נותר בודד?

## עברית

במערך היו 255 איברים: שרשור של 85 קבוצות, שבכל אחת שלושה עותקים שווים של מספר שלם. מחקו בדיוק שני עותקים מאותה קבוצה, ולכן נותרו 253 איברים בסדר היחסי המקורי. החזירו את ערך העותק שנותר מאותה קבוצה. מותר לאותו ערך להופיע בקבוצות סמוכות או בקבוצות נפרדות; המערך אינו בהכרח ממוין. למשל, מותר שרשור של הקבוצות 1,5,1. הציעו פתרון, הוכיחו נכונות ונתחו זמן וזיכרון בלי לשנות את הקלט.

הבהרת עריכה: “בודד” מתאר את הקבוצה שנפגעה, ולא מבטיח שהערך מופיע פעם אחת בכל המערך. הניתוח מוכלל ל־g קבוצות, כלומר אורך 3g−2 אחרי המחיקה; המקרה המקורי הוא g=85. מניחים קלט שמקיים את ההבטחה, וגישה אקראית והשוואת מספרים בעלות יחידה במודל העלות.

### רמזים / Hints

1. איזה מידע נשמר בסדר האיברים גם אם אותה ספרה חוזרת בכמה שלשות?
2. קבוצות סמוכות בעלות אותו ערך מתמזגות לרצף שוויון ארוך. מה אורכו של רצף תקין מודולו שלוש?
3. רצף שלא נפגע מכיל 3r איברים. הרצף שבתוכו המחיקה מכיל 3r−2, ולכן השארית שלו היא אחת. סרקו רצפים מקסימליים.

### הצעה לפתרון / Proposed solution

### הרעיון: סופרים רצפים, לא מספרים ייחודיים
אין צורך שכל שלשה תהיה שונה משאר השלשות. נחלק את המערך הנותר לרצפים מקסימליים של ערך שווה. רצף כזה נוצר מכמה שלשות סמוכות של אותו ערך. כל עוד לא נפגע, אורכו כפולה של שלוש. בדיוק ברצף אחד חסרים שני איברים, ולכן אורכו הוא 3r−2 ושאריתו בחלוקה לשלוש היא אחת. ערכו הוא התשובה.

נסרוק באמצעות start ו־end: נרחיב את end כל עוד הערך שווה לערך בתחילת הרצף, נבדוק את אורך הרצף מודולו שלוש, ונעבור לרצף הבא. המימוש מסיים את כל הסריקה ומוודא שיש בדיוק רצף אחד עם שארית אחת; בדיקות אלו הן הגנה נוספת ואינן הופכות אותו למאמת של כל היסטוריית המקור. אין שמירת מפה ואין שינוי בקלט.

### דוגמה והוכחה
ניקח חמש קבוצות שערכיהן 1,5,1,1,2. אחרי שמוחקים שני איברים מאחת משתי קבוצות ה־1 הסמוכות, אורכי הרצפים הם 3,3,4,3, עם הערכים 1,5,1,2. דווקא הרצף שאורכו ארבע מגלה שערך הקבוצה הפגועה הוא 1. הערך הזה מופיע שבע פעמים במערך כולו, ולכן חיפוש ערך שמופיע פעם אחת היה נכשל. בדוגמת המקור יש 85 קבוצות ולא חמש, אך ההוכחה זהה.

המחיקה משאירה לפחות איבר אחד בקבוצה שנפגעה, ולכן אינה מעלימה מחיצה בין ערכים שונים ואינה מאחדת רצפים שקודם הופרדו בערך אחר. כל רצף נותר איחוד של r קבוצות שוות: 3r איברים אם לא נפגע, ו־3r−2 אם נפגע. רק אחד נפגע. לכן הסריקה מסמנת בדיוק את הרצף הנכון, ומחזירה את ערכו גם כשאותו ערך מופיע ברצפים אחרים.

### עלות ומדוע אין חיפוש בינארי כללי
לכל איבר יש מספר קבוע של גישות; הזמן Θ(n) והזיכרון הנוסף O(1) מילות מכונה. המימוש מבצע לכל היותר 2n−1 קריאות איבר. האופטימליות היא בזמן במקרה הגרוע במודל קריאות למערך: חשבו על g−1 קבוצות אפס וקבוצה פגועה שערכה 1 או 2, במיקום לא ידוע. אחרי המחיקה רק תא אחד שונה מאפס, ויכול להימצא בכל אחת מ־g עמדות של התחלת קבוצה. אם לא בודקים עמדה מועמדת, לא ניתן להבדיל בין ערך 1 לערך 2 בה. לכן במקרה הגרוע דרושות Ω(g)=Ω(n) קריאות. זו הוכחה כללית, בנפרד מהבדיקות הסופיות.

הכיתוב “מסודרים בשלשות” אינו אומר ממוין. בחירת חצי לפי ערכים או לפי השוואת שני איברים בלי אינווריאנט מונוטוני אינה חיפוש בינארי תקף כאשר קבוצות שוות עשויות להתמזג. XOR גם אינו מבטל שלשה: x XOR x XOR x = x. חלופה תקפה היא ספירת תדירויות במפה והחזרת הערך שספירתו שווה לאחת מודולו שלוש, בזמן צפוי O(n) וב־O(k) זיכרון. בחוזה של מילים ברוחב קבוע אפשר גם לספור כל ביט מודולו שלוש, עם טיפול מפורש בסימן; אין להניח רוחב או ייצוג שלא ניתנו.

### אימות והמשך
6,015 תצורות ממצות כיסו את כל ערכי הקבוצות מעל 0,1,2 עבור אחת עד שש קבוצות ואת כל מיקומי המחיקה; אורקל עצמאי ספר תדירויות גלובליות. עוד 255 בדיקות כיסו את כל 85 מיקומי המחיקה בשלוש משפחות באורך המקורי 253. נבדקו אי־שינוי הקלט וחסם 2n−1 הקריאות. הבדיקה אינה תחליף להוכחה או לביקורת אנושית.

תשובה קצרה לראיון: “אסרוק רצפים שווים; שלשות סמוכות שוות יוצרות כפולות של שלוש, וברצף הפגוע האורך הוא אחת מודולו שלוש. אחזיר את ערכו בזמן ליניארי ובזיכרון קבוע.” בהמשך אפשר לשאול מה משתנה אם סדר האיברים אינו נשמר: ספירת תדירויות עדיין עובדת, אך הוכחת רצפי השוויון נעלמת.

```python
"""Equality-run solution; values may recur in separate or adjacent groups.

Contract: concatenate nonempty three-equal groups, then delete two elements
from one group. This accepts the resulting array and returns its damaged value.
Full run validation is optional robustness and does not infer global sorting.
"""


def damaged_value(values):
    n = len(values)
    if n == 0 or n % 3 != 1:
        raise ValueError('Expected a nonempty array of length 3*g-2')
    found = False
    answer = None
    start = 0
    while start < n:
        value = values[start]
        end = start + 1
        while end < n and values[end] == value:
            end += 1
        remainder = (end - start) % 3
        if remainder == 1:
            if found:
                raise ValueError('More than one damaged run')
            answer, found = value, True
        elif remainder != 0:
            raise ValueError('Invalid run length')
        start = end
    if not found:
        raise ValueError('No damaged run')
    return answer
```


### assumptions

[
  "במקור 85 קבוצות רצופות של שלושה מספרים שלמים שווים; מחיקה של שני איברים מאותה קבוצה; נשמר הסדר.",
  "אותו ערך מותר בקבוצות סמוכות ונפרדות; אין מיון גלובלי; גישה והשוואה בעלות יחידה במודל העלות."
]

### optimality

"Θ(n) זמן במקרה הגרוע ו־O(1) מילות זיכרון; לכל היותר 2n−1 קריאות במימוש. קבוצה פגועה שערכה לא ידוע בין קבוצות אפס מוכיחה חסם תחתון Ω(n)."

### verification

"בוצעו 6,270 בדיקות: 6,015 תצורות קבוצות/מיקום ממצות ועוד 255 מקרי אורך 253, מול ספירת תדירויות עצמאית, כולל שמירת הקלט וחסם קריאות. ביקורת אנושית ממתינה."

### edge_cases

[
  "קבוצה יחידה לאחר ההכללה; מחיקה מהקבוצה הראשונה או האחרונה.",
  "כל 85 הקבוצות בעלות אותו ערך: רצף יחיד באורך 253.",
  "קבוצות סמוכות שוות; ערך פגוע המופיע גם ברצף מרוחק; אפס ומספרים שליליים."
]

### common_mistakes

[
  "לפרש “בודד” כהופעה יחידה בכל המערך.",
  "להניח מיון ולהפעיל חיפוש בינארי בלי תכונה מונוטונית.",
  "להשתמש ב־XOR כאילו שלושה עותקים מתבטלים.",
  "לספור רק רצפים באורך אחת ולפספס רצף באורך ארבע או שבע."
]

### interview_answer

"אסרוק רצפי שוויון מקסימליים ואחזיר את הערך של הרצף שאורכו אחת מודולו שלוש; רצפים תקינים הם כפולות של שלוש. הזמן Θ(n) והזיכרון הנוסף קבוע."

### source_ambiguities

[
  "המקור אינו מגדיר טיפוס מספרי או מדד עלות; בחרנו מספרים שלמים ומודל השוואות/גישות.",
  "המקור מתיר חזרת ערכים בשלשות. אין לפרש זאת כהבטחת שלשות שונות או מיון. נשמר הנוסח המקורי בנפרד."
]

### solution_extensions

{
  "question": "מה משתנה אם המערך עורבב אחרי המחיקה?",
  "direction": "ספירת תדירויות מודולו שלוש עדיין מזהה את הערך. סריקת רצפים כבר אינה תקפה; נדרש זיכרון O(k) במפה או חוזה ביטים מוגדר לחלופה.",
  "integration": "מוכן בתוכן; לא מחובר לתור המשך אינטראקטיבי."
}

## English

An array originally had 255 elements: 85 consecutive groups, each containing three equal copies of an integer. Exactly two copies from the same group were deleted, leaving 253 elements in their original relative order. Return the value of the remaining member of that damaged group. Values may recur in adjacent groups or in separate groups; the array is not necessarily sorted. For example, group values 1,5,1 are allowed. Give an algorithm, prove it correct, and analyze time and extra space without changing the input.

Editorial clarification: “single” refers to the damaged group; the value need not occur only once globally. Generalize to g groups and length 3g−2 after deletion; the source has g=85. Assume promise-valid input and unit-cost array access/integer comparison in the stated cost model.

### רמזים / Hints

1. What ordering information survives even when a value belongs to several triples?
2. Adjacent equal-valued groups merge into one equality run. What is an undamaged run length modulo three?
3. An undamaged run has 3r elements; the damaged run has 3r−2, hence remainder one. Scan maximal equal-value runs.

### הצעה לפתרון / Proposed solution

### Count runs rather than globally unique values
Different triples need not have different values. Partition the surviving array into maximal equality runs. Each run consists of several adjacent triples of the same value. An undamaged run has length divisible by three. Exactly one run lost two members, so its length is 3r−2, congruent to one modulo three. Its value is the answer.

Scan with start and end. Advance end while values equal the first value of the run; inspect the run-length residue; then continue at the next run. The implementation completes the scan and checks that exactly one run has residue one. These are defensive checks, not a reconstruction or validation of the entire source history. No frequency map is stored and the input is unchanged.

### Example and correctness
Take five groups with values 1,5,1,1,2. Deleting two members from one of the adjacent 1 groups produces runs of lengths 3,3,4,3 and values 1,5,1,2. The length-four run identifies value 1. That value occurs seven times globally, so searching for a globally unique value would fail. The source has 85 groups rather than five; the proof is identical.

Deletion leaves at least one member of the damaged group. It therefore cannot erase a separator of a different value and merge runs previously separated by another value. Each surviving run still contains r equal-valued groups: 3r members if undamaged and 3r−2 if damaged. Exactly one run is damaged. Thus the scan selects precisely the right run and returns its value, including when that value also occurs in other runs.

### Cost and why general binary search does not follow
Each element incurs a constant number of accesses: Θ(n) time and O(1) additional machine words. This implementation reads at most 2n−1 elements. Worst-case time is optimal in the array-access model: consider g−1 zero groups and one damaged group whose value is either 1 or 2 at an unknown group position. After deletion only one element is nonzero, and it may occupy any of g possible group-start positions. Leaving one candidate uninspected cannot distinguish value 1 from value 2 there. The worst case requires Ω(g)=Ω(n) accesses. This is a general lower bound, separate from finite test coverage.

“Arranged in triples” does not imply global sorting. Halving by values, or by an adjacent comparison without a monotone invariant, does not justify binary search when equal groups can coalesce. XOR does not cancel a triple either: x XOR x XOR x = x. A valid alternative counts global frequencies and returns the value with count congruent to one modulo three, taking expected O(n) time and O(k) space under hashing. Under an explicitly fixed-width word contract, per-bit counts modulo three are another alternative with defined signed reconstruction; do not assume an unstated width or representation.

### Verification and continuation
6,015 exhaustive configurations cover every 1..6-group sequence over 0,1,2 and every damaged position; an independent oracle uses global frequencies. Another 255 cases cover all 85 damage positions in three source-sized families of length 253. Input preservation and the 2n−1 access bound were checked. Finite execution does not replace the proof or human review.

Short interview answer: “Scan equal-value runs. Coalesced intact triples have lengths divisible by three; the damaged run has residue one. Return its value in linear time and constant space.” A follow-up asks what happens if the order is lost: a frequency map remains valid, while the run proof no longer applies.

```python
"""Equality-run solution; values may recur in separate or adjacent groups.

Contract: concatenate nonempty three-equal groups, then delete two elements
from one group. This accepts the resulting array and returns its damaged value.
Full run validation is optional robustness and does not infer global sorting.
"""


def damaged_value(values):
    n = len(values)
    if n == 0 or n % 3 != 1:
        raise ValueError('Expected a nonempty array of length 3*g-2')
    found = False
    answer = None
    start = 0
    while start < n:
        value = values[start]
        end = start + 1
        while end < n and values[end] == value:
            end += 1
        remainder = (end - start) % 3
        if remainder == 1:
            if found:
                raise ValueError('More than one damaged run')
            answer, found = value, True
        elif remainder != 0:
            raise ValueError('Invalid run length')
        start = end
    if not found:
        raise ValueError('No damaged run')
    return answer
```


### assumptions

[
  "Initially 85 consecutive groups of three equal integers; delete two members of one group and preserve order.",
  "Values may recur in adjacent and separate groups; no global sorting; unit-cost access/comparison in the cost model."
]

### optimality

"Worst-case Θ(n) time, O(1) extra words and at most 2n−1 element reads in this implementation. An unknown-valued damaged group hidden among zero groups gives an Ω(n) lower bound."

### verification

"6,270 executed checks: 6,015 exhaustive group/damage configurations and 255 length-253 cases, against independent frequency counts, including input preservation and the access bound. Human review pending."

### edge_cases

[
  "One group in the generalized problem; damage in the first or last group.",
  "All 85 groups have one value: a single length-253 run.",
  "Adjacent equal groups; the damaged value also appears in a distant run; zero and negative integers."
]

### common_mistakes

[
  "Interpreting “single” as globally unique.",
  "Assuming sorting and using binary search without a monotone property.",
  "Using XOR as though three equal copies cancel.",
  "Looking only for length-one runs and missing lengths four or seven."
]

### interview_answer

"Scan maximal equality runs and return the value whose run length is one modulo three; intact runs have lengths divisible by three. Time is Θ(n), extra space constant."

### source_ambiguities

[
  "The source does not specify numeric type or cost model; integer values and access/comparison costs are explicit editorial assumptions.",
  "The source permits repeated group values. Distinct triples and sorting are not promised. Original text is preserved separately."
]

### solution_extensions

{
  "question": "What changes if the surviving array is shuffled?",
  "direction": "Global counts modulo three still identify the value. Run scanning no longer applies; use O(k) map storage or an explicitly defined bit-word alternative.",
  "integration": "Prepared in content; not connected to an interactive follow-up queue."
}

## קבצים / Files

- [solutions/prep_210_damaged_triple_groups.py](../solutions/prep_210_damaged_triple_groups.py)
- [diagrams/prep-210-algorithms-batch20-he.png](../diagrams/prep-210-algorithms-batch20-he.png)
- [diagrams/prep-210-algorithms-batch20-en.png](../diagrams/prep-210-algorithms-batch20-en.png)
