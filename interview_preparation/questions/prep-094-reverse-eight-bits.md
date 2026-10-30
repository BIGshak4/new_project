# PREP-094 — היפוך סדר שמונה סיביות — ללא מערך

פתרון מוצע בסיוע AI; ביקורת מקצועית אנושית ממתינה. הקושי לא כויל.

## מקור

[צילום המקור](../sources/prep-094-source.png)

כתוב פונקציה המקבלת מספר המורכב משמונה ביטים, ומחזירה את המספר בסידור הפוך של ביטים, ללא שימוש במערך. לדוגמא, עבור הקלט 01101011 יוחזר 11010110

שיוכי החברות בצילום מדווחים ולא אומתו באופן עצמאי: Marvell, Intel.

## נוסח ערוך

היפוך סדר שמונה סיביות — ללא מערך

כתבו פונקציה שמקבלת מספר שלם לא־מסומן בן שמונה סיביות, בטווח 0 עד 255, ומחזירה את המספר המתקבל מהיפוך סדר כל שמונה הסיביות. לדוגמה, 01101011 הופך ל־11010110. אין להשתמש במערך, ברשימה, במחרוזת או בטבלת חיפוש לצורך ההיפוך. הסבירו את האלגוריתם ונתחו את עלותו.

רוחב הקלט קבוע: אפסים מובילים הם חלק מהייצוג. למשל 00000001 הופך ל־10000000. נדרש היפוך סדר הסיביות, לא היפוך ערכי 0/1 ולא סיבוב מעגלי. מותר מספר קבוע של משתנים שלמים.

### שלושה רמזים

1. הסיבית הימנית ביותר של הקלט צריכה להיות השמאלית ביותר בפלט. איך מבודדים אותה בפעולת ביטים?
2. התחילו מתוצאה אפס. הזיזו אותה שמאלה והוסיפו מימין את הסיבית שחילצתם; לאחר מכן הזיזו את הקלט ימינה.
3. בצעו בדיוק שמונה איטרציות: result=(result<<1)|(value&1), ואז value>>=1. אל תעצרו כאשר value נהיה אפס, כי עדיין ייתכנו אפסים מובילים שיש לעבד.

### הצעה לפתרון

### קוראים מימין ומרכיבים משמאל
דמיינו שתי שורות של סיביות. בכל צעד לוקחים את הסיבית הימנית ביותר של הקלט ומצרפים אותה לקצה הימני של תוצאת הביניים. את תוצאת הביניים מזיזים שמאלה לפני כל צירוף, כך שהסיבית הראשונה שקראנו תגיע בסוף לצד השמאלי ביותר.

שלוש פעולות מספיקות:
1. value & 1 מחלץ את הסיבית הימנית ביותר: התוצאה היא 0 או 1.
2. result << 1 מפנה מקום בצד ימין; OR עם הסיבית מכניס אותה למקום שהתפנה.
3. value >>= 1 מסיר את הסיבית שכבר קראנו ומביא את הבאה לקצה הימני.

### עוקבים אחרי הדוגמה
לקלט 01101011, קוראים מימין לשמאל את הסיביות 1,1,0,1,0,1,1,0:

| צעד | הסיבית שנקראה | result, מוצג תמיד בשמונה סיביות |
| --- | --- | --- |
| התחלה | — | 00000000 |
| 1 | 1 | 00000001 |
| 2 | 1 | 00000011 |
| 3 | 0 | 00000110 |
| 4 | 1 | 00001101 |
| 5 | 0 | 00011010 |
| 6 | 1 | 00110101 |
| 7 | 1 | 01101011 |
| 8 | 0 | 11010110 |

### למה חייבים בדיוק שמונה צעדים?
המספר 1 מיוצג כאן בתור 00000001. אחרי צעד אחד נקבל result=1 והקלט שנותר הוא אפס. אם נעצור שם, נחזיר 1 במקום 128. שבעת האפסים שנותרו הם חלק משמונה הסיביות המקוריות; כל אחד מהם מזיז את ה־1 בתוצאה עוד מקום שמאלה. לכן הלולאה תלויה ברוחב שמונה, לא בשאלה אם ערך הקלט עדיין חיובי.

### נכונות ועלות
לאחר k צעדים, k הסיביות הנמוכות של result הן היפוך הסדר של k הסיביות הנמוכות מהקלט המקורי, והקלט שנותר הוא המקור מוזז ימינה ב־k. הצעד הבא משמר את הטענה: הוא מזיז את התוצאה ומצרף את הסיבית הבאה. ב־k=8 כל הסיביות טופלו ולכן מתקבל ההיפוך המלא.

עבור רוחב שמונה קבוע, מספר הפעולות והזיכרון הם O(1), עם שמונה צעדים ומספר קבוע של משתנים. להכללה לרוחב w שמוכנס במילת מכונה: O(w) צעדים ו־O(1) מילים; רוחב המספרים עצמו הוא O(w) ביטים. אין מערך עזר, מחרוזת או טבלת המרה בקוד הפתרון. מסכות רחבות והזזות בשפה אחרת דורשות טיפוס לא־מסומן וכללי רוחב מוגדרים. הפונקציה שלהלן דוחה ערכים שאינם מספר שלם בתחום, במקום לחתוך אותם בשקט לבייט.

היפוך סדר אינו פעולת NOT: הוא משאיר את מספר סיביות ה־1 ללא שינוי. הוא גם אינו סיבוב מעגלי, אף שלפעמים התוצאות חופפות במקרה. בדוגמה 01101011, סיבוב מעגלי שמאלה במקום אחד נותן במקרה את אותה תוצאה 11010110. כדי לראות את ההבדל, קחו 00000001: היפוך הסדר נותן 10000000, ואילו סיבוב מעגלי שמאלה במקום אחד נותן 00000010. לכן התאמה לדוגמה אחת אינה מספיקה לבדיקת האלגוריתם.

```python
"""Reverse exactly eight bits using scalar bit operations, without an array."""


def reverse_byte(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValueError("value must be an integer in 0..255")
    result = 0
    for _ in range(8):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result
```

## English edition

Reverse eight bits without an array

Write a function taking an unsigned eight-bit integer in 0..255 and returning the integer obtained by reversing all eight bit positions. For example, 01101011 becomes 11010110. Do not use an array, list, string or lookup table to perform the reversal. Explain the algorithm and its cost.

Width is fixed: leading zeros belong to the representation. Thus 00000001 becomes 10000000. Reverse bit order rather than complementing bits or performing a cyclic rotation. A constant number of integer variables is allowed.

### Three hints

1. The input's rightmost bit must become the output's leftmost bit. How can a bitwise operation isolate it?
2. Start with result zero. Shift it left and append the extracted bit on the right; then shift the input right.
3. Run exactly eight iterations: result=(result<<1)|(value&1), then value>>=1. Do not stop when value becomes zero: fixed-width leading zeros still need processing.

### Proposed solution

### Read from the right and build toward the left
Imagine an input bit row and an initially empty result. Repeatedly take the input's rightmost bit and append it to the right of the partial result. Shifting the result left before each append eventually moves the first bit read to the leftmost output position.

Three operations are enough:
1. value & 1 isolates the rightmost bit, yielding zero or one.
2. result << 1 opens a position on the right; OR appends the extracted bit there.
3. value >>= 1 discards the bit just read and exposes the next one.

### Follow the example
For 01101011, the bits read from right to left are 1,1,0,1,0,1,1,0:

| Step | Bit extracted | result, always displayed as eight bits |
| --- | --- | --- |
| Initial | — | 00000000 |
| 1 | 1 | 00000001 |
| 2 | 1 | 00000011 |
| 3 | 0 | 00000110 |
| 4 | 1 | 00001101 |
| 5 | 0 | 00011010 |
| 6 | 1 | 00110101 |
| 7 | 1 | 01101011 |
| 8 | 0 | 11010110 |

### Why exactly eight iterations?
The integer one means 00000001 here. After one step result=1 and the remaining input is zero. Stopping then would return one rather than 128. The remaining seven zero bits still belong to the original byte: each shifts the result's one bit another position to the left. The loop must therefore follow the fixed width, not whether the remaining value is positive.

### Correctness and cost
After k iterations, the low k bits of result are the reversal of the original input's low k bits; the remaining input is the original shifted right by k. The next step preserves this invariant by shifting the result and appending the next input bit. At k=8 all positions have been processed, giving the complete reversal.

With fixed width eight, time and storage are O(1): eight steps and a constant number of scalar variables. Generalizing to width w that fits a machine word gives O(w) steps and O(1) words; the scalar bit width itself is O(w). The solution uses no auxiliary array, string or conversion table. Other languages need an unsigned type and explicit width and shift semantics. The implementation rejects noninteger or out-of-range arguments rather than silently truncating them to a byte.

Reversal is not bitwise NOT: it preserves the number of set bits. It is also not a cyclic rotation, although their outputs can coincide accidentally. For the given 01101011 example, rotating left by one position happens to produce the same 11010110 result. To distinguish them, use 00000001: reversal gives 10000000, whereas a left rotation by one gives 00000010. Matching one example is therefore insufficient to validate the algorithm.

```python
"""Reverse exactly eight bits using scalar bit operations, without an array."""


def reverse_byte(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValueError("value must be an integer in 0..255")
    result = 0
    for _ in range(8):
        result = (result << 1) | (value & 1)
        value >>= 1
    return result
```

## חומר משלים דו־לשוני / Bilingual supporting material

```json
{
  "assumptions": {
    "he": [
      "קלט שלם לא־מסומן בטווח 0..255; רוחב שמונה סיביות כולל אפסים מובילים.",
      "אין מערך, רשימה, מחרוזת או טבלת חיפוש בפתרון; משתנים שלמים מותרים.",
      "הפלט הוא מספר; כתיבה בשמונה סיביות משמשת להסבר בלבד."
    ],
    "en": [
      "Unsigned integer input in 0..255; exactly eight bits, including leading zeros.",
      "No array, list, string or lookup table in the solution; scalar integers are allowed.",
      "Return an integer; eight-bit display is explanatory only."
    ]
  },
  "optimality": {
    "he": {
      "time": "שמונה איטרציות: O(1) לרוחב הקבוע. להכללה לרוחב w: O(w) צעדי ביט, בהנחה שהמילה מכילה את הערך.",
      "space": "O(1) משתנים/מילים; בהכללה הרוחב הכולל הוא O(w) ביטים.",
      "scope": "אין טענת מינימום הוראות או עדיפות על פקודת חומרה ייעודית. החלפות במסכות יכולות לתת חלופה לרוחב קבוע."
    },
    "en": {
      "time": "Eight iterations: O(1) for the fixed width. For width w: O(w) bit steps assuming the value fits the word.",
      "space": "O(1) scalar variables/words; generalized scalar width is O(w) bits.",
      "scope": "No minimum-instruction or superiority-to-dedicated-hardware claim. Masked swaps are an alternative at fixed width."
    }
  },
  "edge_cases": {
    "he": [
      "0 ו־255 נשארים ללא שינוי.",
      "1 הופך ל־128 ו־128 ל־1.",
      "אפסים מובילים חייבים לעבור לתוצאה.",
      "01101011 הופך ל־11010110, כלומר 107 ל־214.",
      "הקוד דוחה קלט מחוץ לתחום וגם ערכים שאינם שלמים."
    ],
    "en": [
      "Zero and 255 are unchanged.",
      "One maps to 128 and 128 to one.",
      "Leading zeros must be processed.",
      "01101011 becomes 11010110, or 107 becomes 214.",
      "The implementation rejects out-of-range and noninteger input."
    ]
  },
  "common_mistakes": {
    "he": [
      "לולאת while value שמפסיקה לפני שכל שמונה הסיביות עובדו.",
      "היפוך ערכי הסיביות באמצעות NOT במקום היפוך הסדר.",
      "סיבוב סיביות במקום היפוך סדרן.",
      "שימוש במחרוזת, במערך או בטבלת חיפוש למרות ההגבלה.",
      "התעלמות מרוחב וסימן בהזזה בשפה ברוחב קבוע."
    ],
    "en": [
      "A while-value loop stops before all eight positions are processed.",
      "Complementing bit values with NOT instead of reversing order.",
      "Rotating instead of reversing.",
      "Using a string, array or lookup table despite the constraint.",
      "Ignoring width and signed-shift behavior in fixed-width languages."
    ]
  },
  "interview_answer": {
    "he": "אתחל result=0. חזור שמונה פעמים: הזז את result שמאלה, צרף עם OR את value&1, והזז את value ימינה. הסיבית הראשונה שנקראה נודדת שמאלה עד לקצה. שמונה צעדים קבועים, בלי מערך עזר.",
    "en": "Initialize result=0. Repeat eight times: shift result left, OR in value&1, then shift value right. The first extracted bit moves left until it reaches the far end. Eight fixed steps and no auxiliary array."
  },
  "source_ambiguities": {
    "he": [
      "המקור אומר מספר בן שמונה ביטים וללא מערך; הנוסח מבהיר טווח לא־מסומן, עיבוד אפסים מובילים ואיסור שימוש במחרוזת כתחליף למערך.",
      "תגיות המקור כוללות Intel ו־Marvell; השיוך מדווח ולא אומת עצמאית."
    ],
    "en": [
      "The source specifies eight bits and no array; the edition clarifies the unsigned range, leading-zero handling and no string workaround.",
      "Intel and Marvell are source-reported attributions, not independently verified."
    ]
  },
  "verification": {
    "he": "אומתו כל 256 הקלטים מול אורקל בלתי תלוי של היפוך מחרוזת בת שמונה תווים, 2,048 בדיקות מיקום סיבית, היפוך כפול, שימור מספר אחדים, התאמה למשלים ושבע דחיות של קלט לא תקין. מחרוזות משמשות באורקל בלבד. ללא הידור לשפה ברוחב קבוע או מדידת ביצועים.",
    "en": "Verified all 256 inputs against independent fixed-width string reversal, 2,048 individual bit positions, reversal involution, set-bit preservation, complement compatibility and seven invalid-input rejections. Strings are used only in the oracle. No fixed-width language compilation or benchmark."
  },
  "relationship_note": {
    "he": "קשורה לתרגילי הזזה וסיבוב, אך היפוך סדר שמונה הסיביות הוא פעולה אחרת; בפרט אין לשנות את הרוחב לפי גודל המספר.",
    "en": "Related to shift and rotation exercises, but reversing all eight positions is a different operation; the width must not shrink to the numerical bit length."
  },
  "solution_extensions": {
    "he": {
      "question": "איך אפשר להפוך שמונה סיביות בשלושה שלבי החלפה במסכות?",
      "direction": "מחליפים סיביות שכנות במסכות 0x55/0xAA, אחר כך זוגות ב־0x33/0xCC ולבסוף רביעיות ב־0x0F/0xF0. יש להוכיח בנפרד את כיווני ההזזה ולשמור על רוחב שמונה.",
      "status": "מוכן בתוכן; אינו מחובר לתור שאלות ההמשך."
    },
    "en": {
      "question": "How can three masked-swap stages reverse a byte?",
      "direction": "Swap neighboring bits using 0x55/0xAA, then pairs using 0x33/0xCC, then nibbles using 0x0F/0xF0. Separately justify shift directions and retain eight-bit width.",
      "status": "Prepared in content; not connected to the interactive follow-up queue."
    }
  }
}
```


## מקורות נוספים — 24.10.2026, מקבץ 20

- [צילום 1](../sources/2026-10-24-batch20-01.png) — Marvell, Intel; דיווח מקור לא מאומת.

המזהה, היסטוריית התרגול והאישורים האנושיים אינם מוחלפים בעקבות קליטת מקור. הנוסח, שלושת הרמזים והפתרון הטכני נשמרו.


## מקורות נוספים — 25.10.2026, מקבץ20

נוסף צילום מקור במקבץ20 עם הרחבה דו־לשונית; הנוסח, הרמזים והפתרון הקודמים נשמרו. ההרחבה מופיעה גם בחומר המשלים באתר.


## מקור נוסף — 30.10.2026, מקבץ40, צילום 16

[צילום פרטי](../sources/2026-10-30-batch40-16.png)

נוספה הרחבה דו־לשונית, בלי למחוק את התוכן והרמזים הקודמים.
