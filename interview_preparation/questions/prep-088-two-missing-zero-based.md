# PREP-088 — שני חסרים בטווח 0 עד n+1 — ללא מערך עזר

פתרון מוצע בסיוע AI; ביקורת מקצועית אנושית ממתינה. הקושי לא כויל.

## מקור

[צילום המקור](../sources/prep-088-source.png)

ישנו מערך באורך n שאינו ממוין וללא חזרה, היכול להכיל מספרים בין 0 ל־n+1, כיצד ניתן לדעת מי הם שני המספרים בין 0 ל־n+1 שאינם מופיעים במערך? פתרו ללא מערך עזר.

תגיות המקור: hardware,logic,nvidia. שיוך NVIDIA מדווח ולא אומת עצמאית.

## נוסח ערוך

נתון מערך לא ממוין באורך n, המכיל n מספרים שלמים שונים מתוך הטווח הכולל 0 עד n+1. בדיוק שני מספרים מהטווח אינם מופיעים. מצאו את שניהם ללא מערך עזר. תארו את הדרך, נמקו נכונות ונתחו זמן וזיכרון.

הבהרות: n יכול להיות אפס; נתוני הקלט מובטחים תקינים. מותר לקרוא את המערך יותר מפעם אחת, אך אין לשנותו. נדרש מספר קבוע של מילים נוספות; שני ערכי הפלט מותרים. השתמשו בפעולות ביטים על שלמים לא־שליליים. בקוד Python המערך הוא רצף שאפשר לעבור עליו שוב, ולא איטרטור חד־פעמי. הבחינו בין ספירת מילים לבין ספירת ביטים.

## שלושה רמזים

1. חפשו פעולה שמבטלת ערך שמופיע פעמיים, בלי לסמן אילו ערכים ראיתם במערך עזר.
2. XOR של כל הטווח ושל כל איברי המערך משאיר a XOR b. איזו סיבית מוכרחה להיות שונה בשני החסרים?
3. בחרו סיבית דלוקה של a XOR b וחלקו לפיה גם את הטווח וגם את המערך. ביטול ה־XOR בכל קבוצה משאיר חסר אחד, גם אם השני הוא אפס.

## הצעה לפתרון

### מבטלים את מה שכבר מופיע
נסמן את שני החסרים a,b. מבצעים XOR של כל המספרים בטווח 0..n+1 ושל כל איברי הקלט. כל ערך קיים מופיע בדיוק פעמיים ומתבטל; נשאר combined=a XOR b. זו אינה תשובה מספקת בפני עצמה: היא מקשרת בין שני הערכים אך לא מפרידה אותם.

### מפרידים באמצעות סיבית שונה
מכיוון ש־a ו־b שונים, combined אינו אפס. בוחרים את הסיבית הדלוקה הנמוכה ביותר באמצעות combined & -combined. באותה סיבית אחד מהחסרים מכיל 1 והשני 0. עוברים שוב על הטווח ועל הקלט, ובכל אחד משני הצדדים מחשבים XOR רק לערכים השייכים לקבוצה המתאימה. כל ערך קיים מגיע פעמיים לאותה קבוצה ומתבטל. כל חסר שייך לקבוצה אחרת, ולכן בכל קבוצה נשאר בדיוק חסר אחד.

אין צורך ליצור את הקבוצות: תנאי על הסיבית מנתב את הערך לאחד משני משתנים בלבד. אין מערך סימונים, קבוצה, מילון או מיון. הטווח כולל גם אפס; אסור להעתיק בטעות לולאה שמתחילה ב־1.

### דוגמה ואפס כחסר
עבור n=5 והמערך [6,0,3,1,4], הטווח הוא 0..6 והחסרים 2,5. ה־XOR הכולל הוא 7; הסיבית הנמוכה היא 1. ביטול בקבוצת הזוגיים משאיר 2 ובקבוצת האי־זוגיים 5. חלוקה לזוגי ואי־זוגי היא רק דוגמה: באופן כללי בוחרים סיבית לפי combined, כי שני החסרים יכולים להיות שניהם זוגיים.

אפס הוא ערך חוקי ולא סימון ל״לא נמצא״. למשל [3,1,2] משאיר את 0 ואת 4; בחירת הסיבית 4 מפרידה גם אותם. עבור מערך ריק הטווח הוא 0..1, והתשובה (0,1).

### נכונות ועלות
ה־XOR הראשון מבטל את כל הערכים הקיימים, והסיבית הנבחרת מפרידה בוודאות בין החסרים. אותו ביט משייך כל הופעה של ערך קיים לאותה קבוצה, כך שהביטול נשמר גם במעבר השני. שתי הקבוצות ממצות את הטווח, ולכן שני המשתנים הסופיים הם בדיוק שני החסרים.

מספר קבוע של מעברים נותן O(n) פעולות במודל word-RAM, ו־O(1) מילים נוספות כשהערכים נכנסים למילה. במונחי ביטים נדרשים O(log(n+2)) ביטים למשתנים; ב־Python רוחב הפעולות גדל עם n ואין הבטחת זמן קבוע לכל שלם שרירותי. מספר קבוע של משתנים אינו מספר קבוע של ביטים. לא ניתן להבטיח פתרון על קלט כללי לא ממוין בלי לבדוק לינארית את הנתונים במודל הגישה הזה. הפתרון אינו משנה את הקלט.

הקוד מניח קלט תקין ואינו מוסיף בדיקת ייחודיות בעזרת set, שתפר את מגבלת הזיכרון. לולאות על הטווח אינן מערך עזר. בטיפוסים ברוחב קבוע כדאי להשתמש בטיפוס לא־מסומן ולהגדיר במפורש את פעולת חילוץ הסיבית; אין להסתמך על גלישה מסומנת.

```python
"""PREP-088: two omitted values, no auxiliary array, no input mutation.

Promise: values is a repeatable sequence of n distinct integers in 0..n+1.
Exactly two domain values are absent. Validation of that promise is not included.
Cost: O(n) word operations and O(1) auxiliary machine words, not constant bits.
"""
from collections.abc import Sequence


def missing_two_zero_based(values: Sequence[int]) -> tuple[int, int]:
    combined = 0
    for value in range(len(values) + 2):
        combined ^= value
    for value in values:
        combined ^= value
    split_bit = combined & -combined
    first = second = 0
    for value in range(len(values) + 2):
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    for value in values:
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    return (first, second) if first < second else (second, first)
```


## English

An unsorted array of length n contains n distinct integers from the inclusive domain 0 through n+1. Exactly two domain values are absent. Find both without an auxiliary array. Explain the method, correctness, time and storage.

Clarifications: n may be zero and input validity is promised. Multiple scans are allowed, but do not modify the input. Use only a constant number of auxiliary words; the two output values are allowed. Use bitwise operations on nonnegative integers. The Python input is a repeatable sequence rather than a one-shot iterator. Distinguish word storage from bit storage.

### Hints

1. Look for an operation that cancels a value appearing twice without recording visited values in an auxiliary array.
2. XOR the whole domain and all array entries to obtain a XOR b. Which bit must differ between the two missing values?
3. Choose a set bit of a XOR b and partition both domain and input by it. XOR cancellation leaves one omission in each group, even when one omission is zero.

### Cancel values already present
Let a,b be the omissions. XOR every value in 0..n+1 and every array entry. Each present value appears exactly twice and cancels, leaving combined=a XOR b. That alone relates the two unknown values without separating them.

### Separate them by a differing bit
Because a and b differ, combined is nonzero. Select its lowest set bit with combined & -combined. One omission has that bit set and the other does not. Scan both domain and input again, accumulating XOR separately for the two bit groups. Every present value enters the same group twice and cancels; each group contains exactly one omission, so its final XOR is that omission.

Do not materialize the groups. A bit test routes each value into one of two scalar accumulators. No marking array, set, dictionary or sorting is used. Include zero in the domain loops rather than copying a loop beginning at one.

### Example and a missing zero
For n=5 and [6,0,3,1,4], the domain is 0..6 and the omissions are 2,5. Combined XOR is 7 and its lowest set bit is 1. Cancellation in the even group leaves 2 and in the odd group leaves 5. This particular example uses parity; in general choose the bit from combined, since both omissions can be even.

Zero is a valid answer, not a not-found marker. For [3,1,2], omissions 0 and 4 are separated by bit 4. An empty input has domain 0..1 and answer (0,1).

### Correctness and cost
The first XOR removes all present values and the selected bit necessarily separates the omissions. The same bit assigns both occurrences of every present value to the same group, preserving cancellation in the second pass. The groups partition the domain, so the final scalars are exactly the two omissions.

A constant number of scans costs O(n) word-RAM operations and O(1) auxiliary words when values fit a word. In bits, scalars require O(log(n+2)) storage; Python integer-operation costs grow with width. Constant many variables do not mean constant many bits. Reading linearly many entries is necessary in the worst case for arbitrary unsorted promised inputs in this access model. The input is unchanged.

The code assumes valid input and does not add a uniqueness set that would violate the space constraint. Iterating a range does not allocate an auxiliary array. In a fixed-width implementation, prefer an unsigned type and explicitly defined low-bit extraction rather than signed-overflow assumptions.

```python
"""PREP-088: two omitted values, no auxiliary array, no input mutation.

Promise: values is a repeatable sequence of n distinct integers in 0..n+1.
Exactly two domain values are absent. Validation of that promise is not included.
Cost: O(n) word operations and O(1) auxiliary machine words, not constant bits.
"""
from collections.abc import Sequence


def missing_two_zero_based(values: Sequence[int]) -> tuple[int, int]:
    combined = 0
    for value in range(len(values) + 2):
        combined ^= value
    for value in values:
        combined ^= value
    split_bit = combined & -combined
    first = second = 0
    for value in range(len(values) + 2):
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    for value in values:
        if value & split_bit:
            first ^= value
        else:
            second ^= value
    return (first, second) if first < second else (second, first)
```


## assumptions

{
  "he": [
    "n ערכים שונים בטווח הכולל 0..n+1; בדיוק שני חסרים. n≥0 וקלט תקין מובטח.",
    "המערך ניתן לקריאה חוזרת ואינו משתנה; אין מערך עזר, set או מיון.",
    "O(1) מילים נוספות במודל המילה; שני ערכי פלט מותרים."
  ],
  "en": [
    "n distinct values in inclusive 0..n+1; exactly two omissions. n≥0 and validity is promised.",
    "Input is repeatable and read-only; no auxiliary array, set or sorting.",
    "O(1) auxiliary words in the word model; two output values are allowed."
  ]
}

## optimality

{
  "he": {
    "time": "O(n) פעולות מילה; מספר קבוע של סריקות.",
    "space": "O(1) מילים נוספות, O(log(n+2)) ביטים לסקלרים.",
    "scope": "זמן לינארי מיטבי במקרה הגרוע במודל קריאה של מערך לא ממוין; אין טענת קבועי זמן או מינימום מעברים."
  },
  "en": {
    "time": "O(n) word operations, with a constant number of scans.",
    "space": "O(1) auxiliary words, O(log(n+2)) bits for scalars.",
    "scope": "Worst-case linear time is optimal for reading arbitrary unsorted arrays; no constant-factor or minimum-pass claim."
  }
}

## edge_cases

{
  "he": [
    "n=0: הפלט 0,1.",
    "אפס, n+1 או שניהם חסרים.",
    "שני החסרים באותה זוגיות: סיבית ההפרדה אינה בהכרח הסיבית הנמוכה במספרים עצמם.",
    "רצף חד־פעמי או קלט עם כפילויות אינם מקיימים את החוזה."
  ],
  "en": [
    "n=0 returns0,1.",
    "Zero, n+1 or both may be missing.",
    "Same-parity omissions require a distinguishing bit that need not be the low bit of the numbers themselves.",
    "A one-shot iterator or duplicate input does not satisfy the contract."
  ]
}

## common_mistakes

{
  "he": [
    "להחזיר רק a XOR b במקום שני הערכים.",
    "לחלק תמיד לזוגי ולאי־זוגי בלי לבדוק את combined.",
    "להשתמש במערך סימונים או set למרות האיסור.",
    "לסמן אפס כ״חסר לא ידוע״ או לשכוח את n+1.",
    "לקרוא איטרטור שנגמר פעמיים ולצפות לאותן דגימות."
  ],
  "en": [
    "Returning only a XOR b rather than both values.",
    "Always splitting by parity instead of a set bit of combined.",
    "Using a marking array or set despite the constraint.",
    "Using zero as an unknown-answer marker or omitting n+1.",
    "Scanning an exhausted one-shot iterator twice."
  ]
}

## interview_answer

{
  "he": "אבצע XOR של הטווח ושל המערך כדי לקבל a XOR b. אבחר בו סיבית דלוקה ואחשב XOR בנפרד לשתי הקבוצות לפי אותה סיבית. הקיימים יתבטלו והחסרים ייפרדו; O(n) זמן ו־O(1) מילים, ללא שינוי המערך.",
  "en": "XOR the domain and array to get a XOR b. Choose a set bit and accumulate XOR separately in its two groups. Present values cancel and omissions separate, giving O(n) time and O(1) auxiliary words without mutation."
}

## solution_extensions

{
  "he": {
    "question": "מה משתנה אם הקלט הוא זרם שאפשר לקרוא פעם אחת בלבד?",
    "direction": "הקוד הדו־מעברי אינו מתאים כמו שהוא. אפשר לבחון סכום וסכום ריבועים בשלמים מדויקים ולפתור עבור שני החסרים; יש לנתח רוחב מספרים וגלישה.",
    "status": "מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי."
  },
  "en": {
    "question": "What changes for an input stream that can be read only once?",
    "direction": "The supplied two-pass input method no longer applies unchanged. Exact sums and sums of squares can recover both omissions, with explicit arithmetic width and overflow analysis.",
    "status": "Prepared in content; not connected to the interactive follow-up queue."
  }
}

## source_ambiguities

{
  "he": [
    "האיסור על מערך עזר מפורש במקור. קריאה חוזרת, אי־שינוי הקלט ומודל מילת הזיכרון הובהרו בעריכה.",
    "זו וריאציה מקושרת ל־PREP-041; פתרון הדגלים שם אינו עומד באילוץ החדש, אך עקרון ה־XOR מתאים."
  ],
  "en": [
    "The source explicitly forbids an auxiliary array. Repeatability, read-only input and the word-space model are editorial clarifications.",
    "This is a linked variant of PREP-041. Its marking-array alternative violates the new constraint, while the XOR principle applies."
  ]
}

## verification

{
  "he": "עברו 2,907 מקרי זוג חסרים וסדר קלט, 2,956 תמורות ממצות באורכים קטנים ו־300 מקרים מדגמיים עד אורך 5,000. הושווה לאורקל נפרד המבוסס על סכומים, סכומי ריבועים ושורש שלם; נבדק שהקלט נשאר זהה. מודל Python בלבד, קלט תקין מובטח; לא benchmark או קומפילציה ברוחב קבוע.",
  "en": "Passed 2,907 missing-pair/order cases, 2,956 exhaustive small permutations and 300 seeded cases up to length 5,000. Compared with an independent exact sum/sum-of-squares integer-root oracle and checked input immutability. Python on promised inputs only; no benchmark or fixed-width compilation."
}

## relationship_note

{
  "he": "וריאציה מחמירה מקושרת ל־PREP-041: טווח שמתחיל באפס ואיסור מפורש על מערך עזר, תוך שימור השאלה הקודמת והחלופות שכבר נבדקו בה.",
  "en": "Linked stricter variant of PREP-041: a zero-based domain and explicit no-auxiliary-array constraint, while retaining the older question and its reviewed alternatives."
}

[קוד](../solutions/prep_088_two_missing_zero_based.py) · [בדיקה](../checks/check_prep_088.py) · [תוצאות](../checks/prep-088-verification.json) · [שאלה קשורה](prep-041-one-two-missing-values.md)
