# PREP-022 — גרסה נוספת: ערבוב מערך נתון עם rand_range

צילום שנמסר ב־18 באוקטובר 2026. תגיות חברות לפי המקור בלבד: NVIDIA, Google, Apple, Mellanox. תג החברה הראשית Mellanox; תג נושא logic. ייחוס לא מאומת עצמאית. סיווג האתר נשאר אלגוריתמים ומערכים; אין ראיה לדירוג קושי.

## מקור ללא שינוי

![מקור](../sources/prep-022-hundred-array-rand-range-2026-10-18.png)

נתון מערך ממוין מ 1 עד 100.
נתונה הפונקציה rand_range(min,max)
אשר מחזירה ערך שלם רנדומלי בין min ל max.
צריך לכתוב תכנית אשר תפזר את המספרים באופן רנדומלי במערך. ללא חזרות (כפילויות) וללא איבוד מספרים.

## נוסח לאתר

נתון מערך המכיל את המספרים `1` עד `100`, כל אחד פעם אחת, בסדר עולה. נתונה הפונקציה `rand_range(min, max)` שמחזירה מספר שלם אקראי בטווח המבוקש.

כתבו תוכנית שמערבבת את האיברים **בתוך המערך הנתון**, ללא כפילויות וללא איבוד מספרים. נתחו זמן וזיכרון עזר והסבירו מתי כל סידור מתקבל באותה הסתברות.

הבהרת ממשק לצורך המימוש: שני גבולות הטווח כלולים. אחידות של כל התמורות מניחה שההגרלות אחידות בהינתן תוצאות ההגרלות הקודמות; המקור אומר ״רנדומלי״ ואינו מבטיח זאת במפורש. הסדר הממוין המקורי הוא גם סידור אפשרי תקף; אין דרישה שכל תא ישנה את ערכו.

## רמזים

1. עדיף לבחור מחדש סדר לאיברים שכבר נמצאים במערך, במקום להגריל מאה ערכים ולטפל בכפילויות. איזו פעולה משנה סדר בלי ליצור או למחוק ערכים?
2. חלקו את המערך לאזור שעדיין משתתף בהגרלה ולאזור שכבר קבוע. בכל צעד בחרו איבר מהאזור הפעיל והעבירו אותו לקצה שלו.
3. עברו מהאינדקס האחרון לכיוון ההתחלה. עבור אינדקס i, הגרילו j בטווח הסגור 0..i והחליפו בין התאים i ו־j. לאחר מכן הקטינו את האזור הפעיל באחד.

## הצעה לפתרון

### גרסת המערך הנתון והפונקציה עם שני הגבולות

כאן לא צריך ליצור מערך חדש: `arr` כבר מכיל בדיוק את הערכים הנדרשים. החלפה בין שני תאים שומרת על כל הערכים ועל מספר ההופעות שלהם. לכן בוחרים סדר באמצעות החלפות, במקום להגריל ערכים חדשים.

מתחילים בתא האחרון, אינדקס `99`. בוחרים באקראי אינדקס מתוך `0..99` ומחליפים את האיבר שנבחר עם התא האחרון. כעת קיבענו איבר אחד, ובשלבים הבאים לא נוגעים בו. עבור התא `98` מגרילים רק מתוך `0..98`, וכן הלאה עד התא `1`. התא הראשון נותר עם האיבר האחרון שלא קובע.

```text
for i = 99 down to 1:
    j = rand_range(0, i)
    swap(arr[i], arr[j])
```

כך נראית דוגמה קטנה עם חמישה איברים. הקו מפריד בין החלק הפעיל לחלק שכבר קבוע:

```text
[1, 2, 3, 4, 5]
i=4, j=1: [1, 5, 3, 4 | 2]
i=3, j=0: [4, 5, 3 | 1, 2]
i=2, j=2: [4, 5 | 3, 1, 2]
i=1, j=0: [5 | 4, 3, 1, 2]
```

מותר ש־`j=i`: זו בחירה חוקית שמשאירה את התא במקומו. בדוגמה באיטרציה `i=2` התא הוחלף עם עצמו. אם אוסרים בחירה זו, לא מקבלים את כל התמורות באותה הסתברות; עצם העובדה שהסדר השתנה אינה הוכחה לערבוב אחיד.

**נכונות:** החלפות משמרות את אוסף האיברים, ולכן לא נוצרות כפילויות ולא אובדים מספרים. בתחילת כל צעד, הסיומת שאחרי i כבר קבועה והקידומת `0..i` מכילה בדיוק את האיברים שנותרו לבחירה. החלפת איבר מהקידומת עם התא i מקבעת איבר נוסף ושומרת את הטענה לצעד הבא. בסוף כל התאים נקבעים.

**אחידות:** בתנאי שמקור ההגרלה אחיד בהינתן ההיסטוריה, כל אחד מ־100 האיברים נבחר לתא האחרון בסיכוי `1/100`. אחרי הבחירה, לכל אחד מ־99 הנותרים יש סיכוי `1/99` לתא הבא, וכן הלאה. לכל תמורה מסוימת יש רצף בחירות יחיד והסתברות `1/100!`. אם מקור ההגרלה מוטה, שימור הערכים עדיין מובטח אך אחידות התמורות אינה מובטחת.

**עלות:** עבור מערך כללי באורך n יש `n-1` הגרלות והחלפות: זמן `Theta(n)` ו־`O(1)` מילות זיכרון עזר מעבר למערך הקיים, בהנחת הגרלה וגישה לתא בזמן קבוע. עבור 100 איברים מבצעים בדיוק 99 הגרלות. זהו סדר גודל מיטבי בזמן כאשר נדרשת אפשרות לכל תמורה: גם תמורה שמשנה מספר לינארי של תאים חייבת להיות אפשרית, וכתיבתה דורשת מספר לינארי של פעולות. הקלט עצמו תופס `Theta(n)` מקום; זיכרון העזר הוא הקבוע. אין טענה למינימום מדויק של מספר ביטים אקראיים או של קריאות אקראיות בכל מודל אפשרי.

**הבדל מהממשק הקודם:** כאן קוראים ישירות ל־`rand_range(0, i)`. הממשק הישן `rand(m)` החזיר ערך ב־`1..m`, ולכן המקבילה בו היא `rand(i+1)-1`. אין להפחית 1 מתוצאת הממשק החדש. אם ספרייה מסוימת אינה כוללת את הגבול העליון, צריך להתאים את הקריאה ל־`rand_range(0, i+1)`; הנחה זו חייבת להיות מפורשת.

**מימוש:** הפונקציה משנה את המערך שסופק ומחזירה `None`. אין לאתחל בתוכה רשימה חלופית ואין צורך בקבוצה של מספרים שנבחרו. אחרי הגדרת הפונקציה, הקריאה היא `shuffle_in_place(arr, rand_range)`.

```python
"""Shuffle the supplied array in place using inclusive rand_range(min, max)."""
from collections.abc import Callable, MutableSequence


def shuffle_in_place(values: MutableSequence[int], rand_range: Callable[[int, int], int]) -> None:
    """O(n) swaps and O(1) auxiliary words; uniform if bounded draws are conditionally uniform."""
    for i in range(len(values) - 1, 0, -1):
        j = rand_range(0, i)
        if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j <= i:
            raise ValueError("rand_range(min, max) must return an integer within both inclusive bounds")
        values[i], values[j] = values[j], values[i]
```

**מקרי קצה וטעויות:** מערך ריק או בן איבר אחד אינו דורש הגרלה. תוצאה ממיינת או תא שנשאר במקומו אינם שגיאה. הגרלת ערכים חדשים עלולה ליצור כפילויות. החלפת כל תא עם אינדקס מכל המערך בכל שלב משמרת ערכים אך בדרך כלל נותנת התפלגות מוטה. ערבוב במקום גם משמר כל מערך נתון אחר; המיון ההתחלתי אינו דרוש לאלגוריתם.

**תשובה קצרה לראיון:** אערבב את המערך הקיים במקום: מהסוף להתחלה אבחר אינדקס אחיד בין 0 לאינדקס הנוכחי, אחליף ביניהם ואקבע את התא האחרון באזור הפעיל. החלפות שומרות על האיברים, וכל בחירה היא מתוך האיברים שנותרו. בהנחת מקור אחיד מתקבלת כל תמורה בהסתברות שווה, בזמן לינארי ובזיכרון עזר קבוע.

## שאלת המשך מוכנה

שאלת המשך מוכנה: אם צריך לבחור רק 10 מספרים שונים מהמערך, האם חייבים לערבב את כולו? כיוון: מבצעים רק 10 צעדי קיבוע; עשרת התאים בסיומת הם בחירה ללא חזרות. בהנחת מקור אחיד זו דגימה אחידה ללא החזרה. זמן O(k) עבור k בחירות מתוך מערך קיים; לא כולל יצירת המערך. ההמשך טרם חובר לתור האינטראקטיבי.

## English

An existing array contains every integer from `1` through `100` exactly once, in ascending order. The function `rand_range(min, max)` returns a random integer in the requested range.

Shuffle the elements **within the supplied array**, without duplicates or lost values. Analyze running time and auxiliary space, and explain when every permutation has the same probability.

Interface clarification for the implementation: both endpoints are inclusive, so `min <= result <= max`. Uniform permutations require draws to be uniform conditional on earlier draws; the source only says “random” and does not explicitly promise this. The original sorted order is a valid possible outcome; not every cell must change.

### Hints

1. Reorder the values already present instead of drawing a hundred new values and handling duplicates. Which operation changes order without creating or deleting values?
2. Split the array into an active region and an already fixed region. At each step choose from the active region and move the chosen value to its boundary.
3. Work backward from the last index. For position i, draw j uniformly from inclusive range 0..i, swap positions i and j, then shrink the active region by one.

### Existing-array variant with a two-bound random function

The supplied array already contains every required value exactly once. Swapping cells changes order while preserving the multiset, so reorder existing values instead of generating new ones.

Start at index 99. Choose an index from inclusive range 0..99 and swap the chosen value into the final cell. That cell is now fixed. For index 98 choose only from 0..98, and continue down to index 1. The first cell is left with the final unchosen value.

```text
for i = 99 down to 1:
    j = rand_range(0, i)
    swap(arr[i], arr[j])
```

A five-value trace, with the fixed suffix to the right of the divider:

```text
[1, 2, 3, 4, 5]
i=4, j=1: [1, 5, 3, 4 | 2]
i=3, j=0: [4, 5, 3 | 1, 2]
i=2, j=2: [4, 5 | 3, 1, 2]
i=1, j=0: [5 | 4, 3, 1, 2]
```

Allow `j=i`. Swapping a cell with itself is valid and is necessary for this algorithm to reach all permutations uniformly. Requiring the order to change is not a correct uniformity criterion.

**Correctness:** swaps preserve every value and its multiplicity. Before each step, cells after i are fixed and prefix 0..i contains exactly the remaining values. Swapping a chosen prefix value into i fixes one additional cell while preserving the invariant. At termination the complete array is a permutation of the input.

**Uniformity:** assuming each bounded draw is uniform conditional on prior draws, every value has probability 1/100 of filling the last cell, then each remaining value has probability 1/99 for the next, and so on. Every complete permutation corresponds to a unique choice path with probability `1/100!`. Biased draws still preserve values but need not produce uniform permutations.

**Cost:** for general length n, there are n-1 draws/swaps: Theta(n) time and O(1) auxiliary machine words beyond the existing array, assuming constant-time bounded RNG and indexed access. Length 100 uses exactly 99 draws. Linear order of growth is necessary when all permutations must be possible: some change linearly many cells and require linearly many writes. The input array itself occupies Theta(n) storage. This does not establish a minimum number of random bits or RNG calls over all computational models.

**Interface distinction:** use `rand_range(0, i)` directly. The older one-argument inclusive API would use `rand(i+1)-1`. Do not subtract one from the new API's result. If a library excludes its upper endpoint, adapt the call to `rand_range(0, i+1)` and state that different contract.

**Implementation:** the function mutates the supplied array and returns None. It allocates no replacement array or used-values set. Call `shuffle_in_place(arr, rand_range)` after defining it.

```python
"""Shuffle the supplied array in place using inclusive rand_range(min, max)."""
from collections.abc import Callable, MutableSequence


def shuffle_in_place(values: MutableSequence[int], rand_range: Callable[[int, int], int]) -> None:
    """O(n) swaps and O(1) auxiliary words; uniform if bounded draws are conditionally uniform."""
    for i in range(len(values) - 1, 0, -1):
        j = rand_range(0, i)
        if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j <= i:
            raise ValueError("rand_range(min, max) must return an integer within both inclusive bounds")
        values[i], values[j] = values[j], values[i]
```

**Edges and mistakes:** empty/singleton arrays need no draws. A sorted result or unchanged cell is valid. Generating new random values can duplicate or lose inputs. Swapping each position with a random index from the entire array at every step preserves values but is generally biased. Initial sorted order is not needed; the algorithm preserves any supplied input multiset.

**Interview answer:** work backward, draw uniformly from the remaining prefix, swap the chosen value to its boundary and shrink the prefix. Swaps preserve values, and choosing uniformly among remaining values makes every permutation equally likely. Linear time and constant extra space.

Prepared follow-up: must the entire array be shuffled to choose only 10 distinct values? Direction: perform just 10 boundary-fixing steps; the suffix holds a sample without replacement. Uniform draws give a uniform sample. O(k) steps for k selections from an existing array, excluding its construction. Not yet wired into the interactive follow-up queue.

## בדיקות ושילוב

[קוד פתרון](../solutions/prep_022_rand_range_shuffle.py) · [בדיקה ממצה](../checks/check_prep_022_rand_range.py) · [תוצאות](../checks/prep-022-rand-range-verification.json). כל 5,914 המסלולים עברו. הגרסה מקושרת ל־[PREP-022](prep-022-random-permutation.md) ונכללת באותה רשומת אתר, בלי להגדיל את מספר השאלות. נשמרו המקור הקודם, הפתרונות הקודמים, המזהה והיסטוריית התרגול. התוכן נוצר בסיוע AI וממתין לסקירה מקצועית; שאלת ההמשך מוכנה אך אינה מחוברת לתור האינטראקטיבי.

## פרסום ובדיקת האתר

- הגרסה נוספה לרשומה הקיימת במסד, במזהה `5251ab26-03f1-490e-8472-d028fcc88f70`. קריאה חוזרת אימתה את הנוסח, הפתרונות, החומר הנוסף והשיוכים בשתי השפות. נוספו Google ו־Mellanox לפי המקור; מזהה השאלה, גרסתה, קישורי המיומנויות ומצב הביקורת נשמרו. אין כתיבה להתקדמות משתמשים.
- קוד הפתרון החדש וצילום המקור הועלו לאחסון פרטי ואומתו לפי גיבוב. צילום המקור אינו מוצג ללומדים; קוד הפתרון זמין לאחר חשיפה מורשית.
- עברו 45 בדיקות שרת ממוקדות ו־15 בדיקות דפדפן מקומיות עם רכיבי התצוגה האמיתיים: נוכחות הגרסה בשתי השפות, פתיחת סעיפים, החלפת שפה ושני גדלי מסך. אין שגיאות דפדפן או גלילה אופקית של העמוד. ראיות מקומיות תחת `.impeccable/review/prep-022-rand-range/browser/` (מחוץ לגיט).
- גבולות הבדיקה: לא בוצעה בדיקת לחיצות בחשבון באתר החי ולא נבדק טלפון פיזי. רמת הקושי אינה מכוילת והפתרון עדיין ממתין לסקירה מקצועית.
- בדיקה ידנית: היכנסו לאתר ← ״מאגר״ ← חפשו ״פרמוטציה״ ← פתחו ״פרמוטציה אקראית ללא חזרות״. בגוף השאלה חפשו את הכותרת ״גרסה נוספת: מערך נתון מ־1 עד 100״. ודאו שהממשק הוא rand_range עם שני גבולות, ושבדף המלא מופיעות Google ו־Mellanox. חשפו את הפתרון, גללו לסעיף ״גרסת המערך הנתון והפונקציה עם שני הגבולות״ ופתחו את קובץ הקוד החדש. עברו לאנגלית וחזרו לעברית כדי לבדוק גם את הנוסח וההסבר של גרסה זו.
