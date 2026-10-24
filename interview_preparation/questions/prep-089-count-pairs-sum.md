# PREP-089 — כמה זוגות במערך מסתכמים ל־S?

פתרון מוצע בסיוע AI; ביקורת מקצועית אנושית ממתינה. הקושי לא כויל.

## מקור

[צילום המקור](../sources/prep-089-source.png)

שאלת תכנות פשוטה — בהינתן מערך איך ניתן למצוא כמה זוג מספרים שסכומם הוא S=5 נתון כלשהו

שיוכי החברות בצילום מדווחים ולא אומתו באופן עצמאי: NVIDIA.

## נוסח ערוך

כמה זוגות במערך מסתכמים ל־S?

נתון מערך של מספרים שלמים ויעד S. החזירו את מספר זוגות האינדקסים השונים i<j שעבורם a[i]+a[j]=S. אין צורך להחזיר את הזוגות עצמם. תארו פתרון יעיל, נמקו נכונות ונתחו זמן וזיכרון.

מותרות חזרות, אפסים ומספרים שליליים. כל זוג אינדקסים נספר פעם אחת; הופעות שונות של אותו ערך הן איברים שונים. לדוגמה, עבור [1,4,1,4,2,3] ו־S=5 התשובה היא 5. אין להשתמש באותו איבר פעמיים ואין לשנות את הקלט.

המקור אינו מגדיר כיצד לספור חזרות; כאן נבחרה במפורש ספירת זוגות אינדקסים. אם הכוונה לזוגות ערכים ייחודיים, זו שאלה אחרת שיש להבהיר עם המראיין.

### שלושה רמזים

1. לכל ערך x דרוש בן זוג שערכו S−x. מה צריך לזכור על האיברים שכבר עברנו?
2. לא מספיק לזכור אם המשלים הופיע: צריך לזכור כמה פעמים. כל הופעה קודמת יוצרת זוג חדש עם האיבר הנוכחי.
3. לכל x הוסיפו לתשובה את התדירות הקודמת של S−x, ורק אחר כך הגדילו את התדירות של x. כך אין זוג של איבר עם עצמו ואין ספירה כפולה.

### הצעה לפתרון

### הרעיון: האיבר השני סוגר את הזוג
עוברים על המערך משמאל לימין ומחזיקים מילון תדירויות בשם seen. לפני הטיפול באיבר הנוכחי, המילון מכיל רק את האיברים שכבר עברנו. אם כרגע קראנו 4 והיעד 5, כל 1 שכבר ראינו יוצר איתו זוג נוסף. אם ראינו שני מופעים של 1, נוסיף 2 ולא 1.

לכל x מבצעים שתי פעולות בסדר הזה:
1. מוסיפים לספירה את seen.get(S−x, 0).
2. מגדילים את seen[x] באחד.

הסדר חשוב: עבור [2] ויעד 4 אין זוג. אם נכניס את ה־2 למילון לפני הבדיקה, נספור בטעות את האיבר עם עצמו.

### דוגמה שאפשר לעקוב אחריה
למערך [1,4,1,4,2,3] עם יעד 5:

| האיבר הנוכחי | כמה משלימים כבר ראינו? | סך הזוגות |
| --- | --- | --- |
| 1 | אפס מופעים של 4 | 0 |
| 4 | מופע אחד של 1 | 1 |
| 1 | מופע אחד של 4 | 2 |
| 4 | שני מופעים של 1 | 4 |
| 2 | אפס מופעים של 3 | 4 |
| 3 | מופע אחד של 2 | 5 |

יש ארבעה זוגות בין שני מופעי 1 לשני מופעי 4, ועוד זוג של 2 ו־3. אלו חמישה זוגות אינדקסים, אף שקיימים רק שני זוגות ערכים שונים.

### למה זה נכון?
קחו זוג תקין כלשהו i<j. כאשר מגיעים ל־j, המופע שב־i כבר במילון ולכן הזוג נספר. הוא לא נספר קודם, כי j עוד לא הופיע, ולא ייספר שוב, כי רק האיבר המאוחר בזוג מוסיף אותו. כך כל זוג תקין נספר פעם אחת בדיוק, ושום זוג לא תקין אינו מתווסף: מוסיפים רק משלימים שסכומם עם האיבר הנוכחי הוא S.

הפתרון מטפל גם במשלימים שווים: [2,2,2] עם יעד 4 מוסיף 0 ואז 1 ואז 2, בסך הכול 3 זוגות. אין צורך במקרה מיוחד.

### עלות והגדרת הספירה
במילון גיבוב, זמן הריצה הוא O(n) צפוי או ממוצע בהנחת פעולות מילון בעלות קבועה צפויה; אין זו הבטחת זמן לינארי גרוע ביותר לכל טבלת גיבוב. נשמרות O(k) רשומות, כאשר k מספר הערכים השונים שכבר נקראו, ועד O(n) במקרה הגרוע. מספיק מעבר יחיד ולכן גם זרם קלט מתאים. הקוד משתמש בשלמים של Python; בשפה ברוחב קבוע יש להגן גם על חישוב S−x וגם על מונה שעשוי להגיע ל־n(n−1)/2.

אם המראיין רוצה זוגות ערכים ייחודיים, [1,4,1,4] צריך להחזיר 1 ולא 4. דרך נפרדת היא לבנות תדירויות ולספור ערכי x שעבורם x<S−x והמשלים קיים; אם 2x=S, נדרשים לפחות שני מופעים וסופרים את זוג הערכים פעם אחת. יש להבהיר גם אם רצויים מספר הזוגות או הרשימה עצמה. החזרת כל זוגות האינדקסים יכולה לדרוש פלט בגודל Θ(n²).

```python
"""Count unordered distinct-index pairs, retaining multiplicity of equal values."""
from collections.abc import Iterable


def count_pairs(values: Iterable[int], target: int) -> int:
    seen: dict[int, int] = {}
    total = 0
    for value in values:
        total += seen.get(target - value, 0)
        seen[value] = seen.get(value, 0) + 1
    return total
```

## English edition

How many array pairs sum to S?

Given an integer array and target S, return the number of distinct index pairs i<j satisfying a[i]+a[j]=S. Return only the count, not the pairs. Give an efficient algorithm, justify correctness and analyze time and storage.

Duplicates, zeros and negative values are allowed. Count each index pair once; separate occurrences of one value are distinct elements. For [1,4,1,4,2,3] and S=5, the answer is 5. Do not reuse one element as both endpoints or modify the input.

The source does not define duplicate counting. This edition explicitly chooses index-pair multiplicity; counting unique value pairs is a different contract to clarify with the interviewer.

### Three hints

1. A value x needs a partner S−x. What information about preceding elements is useful?
2. Existence alone is insufficient: remember how many times the complement occurred. Each preceding occurrence forms a new pair with the current element.
3. For x, add the prior frequency of S−x before incrementing x's own frequency. This avoids pairing an element with itself and avoids counting either index pair twice.

### Proposed solution

### The later element completes the pair
Scan left to right while keeping a frequency dictionary, seen, containing only previously processed elements. If the current value is 4 and the target is 5, every preceding 1 contributes another pair. Two earlier ones contribute two pairs, not one.

For each x, do these steps in this order:
1. Add seen.get(S−x, 0) to the total.
2. Increment seen[x].

Order matters: [2] with target 4 has no pair. Inserting 2 before the lookup would incorrectly pair that occurrence with itself.

### Walk through an example
For [1,4,1,4,2,3] and target 5:

| Current value | Complements already seen | Running total |
| --- | --- | --- |
| 1 | no fours | 0 |
| 4 | one one | 1 |
| 1 | one four | 2 |
| 4 | two ones | 4 |
| 2 | no threes | 4 |
| 3 | one two | 5 |

The two ones and two fours form four index pairs, followed by one pair of 2 and 3. That is five index pairs but only two distinct value pairs.

### Why is it correct?
Consider any valid i<j. When j is processed, the occurrence at i is already in seen, so that pair contributes one. It could not have been counted earlier because j was absent, and it cannot be counted later because only its later endpoint adds it. Every valid pair is therefore counted exactly once. An invalid pair is never added because lookups use precisely the required complement S−x.

Equal complements work too: [2,2,2] with target 4 adds zero, then one, then two, totaling three. No special branch is needed.

### Cost and the counting contract
A hash dictionary gives O(n) expected or average time under expected constant-cost dictionary operations, not a worst-case linear guarantee for every hash table. Storage is O(k) dictionary entries for k distinct values seen, up to O(n). A single pass also supports streams. Python uses exact integers; fixed-width implementations must handle overflow in both S−x and a count as large as n(n−1)/2.

If unique value pairs are requested, [1,4,1,4] should yield one rather than four. A separate method builds frequencies, then counts x with x<S−x and a present complement; when 2x=S, require at least two occurrences and count that value pair once. Also clarify count versus enumeration: listing all index pairs may require Θ(n²) output.

```python
"""Count unordered distinct-index pairs, retaining multiplicity of equal values."""
from collections.abc import Iterable


def count_pairs(values: Iterable[int], target: int) -> int:
    seen: dict[int, int] = {}
    total = 0
    for value in values:
        total += seen.get(target - value, 0)
        seen[value] = seen.get(value, 0) + 1
    return total
```

## חומר משלים דו־לשוני / Bilingual supporting material

```json
{
  "assumptions": {
    "he": [
      "מספרים שלמים; חזרות, אפס ושליליים מותרים.",
      "סופרים זוגות אינדקסים לא מסודרים i<j עם ריבוי, לא זוגות ערכים ייחודיים.",
      "הקלט אינו משתנה; מותר מילון עזר. S=5 הוא דוגמה בלבד."
    ],
    "en": [
      "Integer input; duplicates, zero and negatives are allowed.",
      "Count unordered distinct-index pairs i<j with multiplicity, not unique value pairs.",
      "Read-only input; an auxiliary dictionary is allowed. S=5 is only an example."
    ]
  },
  "optimality": {
    "he": {
      "time": "O(n) צפוי בהנחת גיבוב מתאים; Θ(n²) להשוואת כל הזוגות ללא גיבוב.",
      "space": "O(k) רשומות עבור k ערכים שונים, עד O(n).",
      "scope": "נדרש לבדוק את הקלט במקרה הגרוע; אין טענת חסם גרוע ביותר לינארי לטבלת גיבוב או מינימום זיכרון לכל חלופה."
    },
    "en": {
      "time": "O(n) expected under suitable hashing; Θ(n²) for direct pair enumeration.",
      "space": "O(k) entries for k distinct values, at most O(n).",
      "scope": "Input inspection is needed in the worst case; no worst-case linear hash-table or universal minimum-space claim."
    }
  },
  "edge_cases": {
    "he": [
      "מערך ריק או איבר יחיד: אפס זוגות.",
      "[0,0,0] עם S=0: שלושה זוגות.",
      "[2,2,2] עם S=4: שלושה זוגות; [2] מחזיר אפס.",
      "גם מספרים שליליים ויעד שלילי חוקיים.",
      "המונה יכול להיות n(n−1)/2."
    ],
    "en": [
      "Empty or singleton input has zero pairs.",
      "[0,0,0] with S=0 has three pairs.",
      "[2,2,2] with S=4 has three pairs; [2] has none.",
      "Negative values and negative targets are valid.",
      "The count can reach n(n−1)/2."
    ]
  },
  "common_mistakes": {
    "he": [
      "שימוש ב־set מאבד את מספר המופעים של המשלים.",
      "הוספת x למילון לפני החיפוש עלולה לספור איבר עם עצמו.",
      "ספירת (i,j) וגם (j,i).",
      "בלבול בין זוגות אינדקסים לזוגות ערכים או בין ספירה להחזרת רשימה.",
      "הנחה שזמן גיבוב צפוי הוא חסם גרוע ביותר, או הזנחת גלישת המונה."
    ],
    "en": [
      "A set loses complement multiplicity.",
      "Inserting x before looking up can count an element with itself.",
      "Counting both (i,j) and (j,i).",
      "Confusing index pairs, unique value pairs and listing versus counting.",
      "Treating expected hash time as worst-case or overlooking count overflow."
    ]
  },
  "interview_answer": {
    "he": "עוברים פעם אחת עם מילון תדירויות. לכל x מוסיפים את מספר מופעי S−x שכבר נראו, ורק אז מוסיפים את x למילון. כל זוג נספר בדיוק כשמגיעים לאינדקס המאוחר שלו. זמן צפוי O(n), זיכרון O(k).",
    "en": "Scan once with a frequency dictionary. For x, add the number of preceding occurrences of S−x, then insert x. Each pair is counted exactly at its later endpoint. Expected O(n) time and O(k) storage."
  },
  "source_ambiguities": {
    "he": [
      "בצילום לא נקבע אם חזרות נספרות לפי אינדקסים או לפי ערכים; הנוסח הערוך בוחר בראשונה ומפרט את החלופה.",
      "תחום המספרים, אי־שינוי הקלט והרשאה למילון הם הבהרות עריכה.",
      "התגיות hardware ו־verification הן תגיות מקור; הדרישה המהותית היא אלגוריתם תוכנה."
    ],
    "en": [
      "The screenshot does not specify index multiplicity versus unique values; the edited contract chooses the former and explains the alternative.",
      "Integer domain, input immutability and permission for a dictionary are editorial clarifications.",
      "Hardware and verification are source tags; the substantive task is a software algorithm."
    ]
  },
  "verification": {
    "he": "עברו 615,857 מקרי מערך/יעד ממצים, 400 דגימות עם אורקל בלתי תלוי המונה ישירות i<j, קלט זרם, אי־שינוי קלט ואי־תלות בסדר ובהזזה. מקרה של 10,000 אפסים אימת 49,995,000 זוגות. ללא בדיקת ביצועי גיבוב או הידור ברוחב קבוע.",
    "en": "Passed 615,857 exhaustive array/target cases and 400 seeded cases against independent direct i<j enumeration; also streams, immutability, permutation and translation invariance. Ten thousand zeros confirmed 49,995,000 pairs. No hash-performance benchmark or fixed-width compilation."
  },
  "relationship_note": {
    "he": "קשורה ל־PREP-040 ולדוגמת Two Sum, אך כאן מחזירים את מספר כל הזוגות עם ריבוי. מציאת זוג יחיד או בדיקת קיום אינה פותרת את החוזה הזה.",
    "en": "Related to PREP-040 and Two Sum examples, but returns the count of all pairs with multiplicity. Finding one pair or deciding existence does not satisfy this contract."
  },
  "solution_extensions": {
    "he": {
      "question": "מה משתנה אם מבקשים זוגות ערכים ייחודיים או את כל זוגות האינדקסים?",
      "direction": "לייחודיות סופרים כל x<y פעם אחת ובודקים שני מופעים כש־x=y. בהחזרת כל זוגות האינדקסים יש להביא בחשבון פלט שיכול להיות ריבועי.",
      "status": "מוכן בתוכן; אינו מחובר לתור שאלות ההמשך."
    },
    "en": {
      "question": "What changes for unique value pairs or for listing all index pairs?",
      "direction": "For uniqueness, count each x<y once and require two occurrences when x=y. Listing all index pairs must account for potentially quadratic output.",
      "status": "Prepared in content; not connected to the interactive follow-up queue."
    }
  }
}
```
