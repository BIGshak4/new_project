# PREP-022 — פרמוטציה אקראית ללא חזרות

## השאלה המקורית

נתון מספר N אי שלילי כלשהו. יש להדפיס פרמוטציה אקראית (סידור כלשהו) של כל המספרים מ־1 עד N בלי לחזור על מספר פעמיים. ממש בצורה היעילה ביותר.
לרשותך הפונקציה rand(m), המחזירה מספר שלם רנדומלי בין 1 ל־m.
א. ניתן לממש זאת בעזרת כל מבנה נתונים.
ב. יש לממש זאת בעזרת מערך בלבד.

![צילום השאלה](../sources/prep-022.png)

## קטגוריות וחברות

תגיות מקור: software, algorithms-software. סיווג נוסף: אלגוריתמים אקראיים, מערכים, פרמוטציות, דגימה אחידה וסיבוכיות. חברות לפי הצילום: Cisco, Samsung, Microsoft, Applied Materials, Apple, Marvell, Intel, Amazon, NVIDIA. תווית ראשית: מארוול. השיוך לא אומת עצמאית.

## רלוונטיות להכנה

עדיפות בינונית: רלוונטית לתרגול Python, מערכים ויצירת בדיקות אקראיות ללא חזרות. זו הערכת הכנה לפי תיאור התפקיד, לא תחזית לשאלה בראיון.

## שלושה רמזים מדורגים

1. אם תגריל שוב ושוב מתוך 1 עד N, עלולים לצאת מספרים שכבר השתמשת בהם. איך אפשר להגריל רק מבין המספרים שעדיין זמינים?

2. החזק במערך את המספרים שנותרו לבחירה. אחרי בחירה, אין צורך להזיז את כל האיברים כדי להסיר את המספר: החלפה עם איבר בקצה יכולה לעזור.

3. חלק את המערך לחלק שכבר נקבע ולחלק שטרם נקבע. בכל צעד בחר באחידות אינדקס בחלק שנותר והחלף אותו עם התא הבא לקיבוע. שים לב ש־rand(m) מחזירה 1 עד m, בעוד אינדקסי פייתון מתחילים ב־0.

## הצעה לפתרון

**הרעיון:** בתחילה כל המספרים זמינים. בכל שלב בוחרים באקראי אחד מהמספרים שנותרו, מקבעים אותו במקום הבא, וממשיכים רק עם השאר. זהו ערבוב Fisher–Yates.

**סעיף א:** מותר כל מבנה נתונים, ולכן מותר גם מערך. מערך מאפשר לבחור באינדקס אקראי ולהחליף שני איברים בזמן קבוע; הוא מספיק לפתרון מיטבי בזמן. אין דרישה להשתמש במבנה אחר מזה שבסעיף ב. אפשר לחשוב על המאגר כעל שק: בוחרים איבר, מחליפים אותו עם האיבר האחרון שעדיין בשק, ומקטינים את גודל השק ב־1. לא מוחקים מאמצע מערך ולא מזיזים את שאר האיברים. רשימה מקושרת רגילה אינה מאפשרת גישה לאינדקס אקראי בזמן קבוע.

**סעיף ב — מערך בלבד:** נאתחל arr=[1,2,...,N]. באיטרציה i התאים שלפני i כבר קבועים, והתאים i עד N−1 מכילים את המספרים שטרם נבחרו. נבחר j=i+rand(N−i)−1 ונחליף arr[i] עם arr[j]. עכשיו arr[i] קבוע ולא נוגעים בו שוב. בסוף מדפיסים את המערך. החלפת הקצה בתחילת החלק הפעיל שקולה לרעיון השק שבסעיף א.

**למה הנוסחה לאינדקס נכונה?** rand(N−i) מחזירה אחד מהמספרים 1..N−i. החסרת 1 נותנת היסט 0..N−i−1; הוספת i נותנת בדיוק את האינדקסים i..N−1. לדוגמה, אם N=5 ו־i=2, נגריל rand(3), ולכן j הוא 2, 3 או 4 בלבד. חייבים לאפשר גם j=i: זו בחירה חוקית שבה הערך הנוכחי נשאר במקומו.

**למה אין כפילויות?** מתחילים עם כל מספר פעם אחת, והחלפות לא יוצרות ולא מוחקות מספרים. בכל שלב מקבעים בדיוק ערך אחד מתוך החלק שנותר. אחרי N−1 בחירות נשאר מספר אחד, והוא כבר נמצא במקום האחרון. אין צורך להגריל אותו.

**למה ההתפלגות אחידה?** נוסח המקור אומר אקראי אך אינו מגדיר אחידות ועצמאות. כדי להבטיח שכל תמורה תתקבל באותה הסתברות, מניחים שכל קריאה ל־rand(m) מחזירה ערך אחיד ב־1..m, באופן בלתי תלוי בקריאות האחרות (די גם באחידות מותנית בכל ההיסטוריה). לכל תמורה מסוימת יש סיכוי 1/N לבחירת האיבר הראשון שלה, 1/(N−1) לבחירת השני מבין הנותרים וכן הלאה. לכן הסיכוי הכולל הוא 1/N!. אם המקור מוטה, עדיין לא יהיו כפילויות, אך אין הבטחה לתמורה אחידה.

**יעילות:** יצירת המערך, הערבוב וההדפסה עולים כל אחד O(N), לכן בסך הכול Θ(N) פעולות על איברים, בהנחת rand וגישה/החלפה במערך בזמן קבוע. זה אופטימלי בזמן כי צריך להפיק N מספרים. נדרשות max(N−1,0) קריאות ל־rand. המערך צורך Θ(N) מקום, והערבוב עצמו דורש O(1) זיכרון עזר מעבר למערך. אין לטעון O(1) זיכרון כולל או מינימום זיכרון מוחלט מבין כל שיטות הייצוג. ספירת זמן זו היא לפי איברים; עלות כתיבת הספרות בפועל תלויה גם באורך המספרים.

**מקרי קצה:** N=0 נותן פלט ריק ואינו קורא ל־rand(0). N=1 מדפיס 1 ללא הגרלה. קוד ההדפסה משתמש במערך יחיד ובמשתני אינדקס בלבד, בלי set או מילון.

**טעויות נפוצות:** הגרלה מחדש לאחר כפילויות היא פתרון עם זמן לא חסום במקרה הגרוע ותוחלת Θ(N log N) הגרלות תחת מקור אחיד; החלפת כל תא עם תא אקראי מכל המערך נותנת בדרך כלל התפלגות מוטה; מחיקה באמצע המערך עלולה להפוך את הפתרון לריבועי; אין לקרוא ל־rand(N−i−1) כשהחלק שנותר כולל N−i איברים.

**מימוש פייתון:** הפרמטר rand הוא הפונקציה הנתונה בשאלה. random_permutation מחזירה את המערך, ו־print_random_permutation מדפיסה את איבריו.

```python
"""Fisher-Yates using the question's inclusive, one-based rand(m) contract."""
from collections.abc import Callable


def random_permutation(n: int, rand: Callable[[int], int]) -> list[int]:
    """Assume independent uniform draws; O(n) time, O(1) space beyond array."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    values = list(range(1, n + 1))
    for i in range(n - 1):
        offset = rand(n - i)
        if not isinstance(offset, int) or not 1 <= offset <= n - i:
            raise ValueError('rand(m) must return an integer in [1, m]')
        j = i + offset - 1
        values[i], values[j] = values[j], values[i]
    return values


def print_random_permutation(n: int, rand: Callable[[int], int]) -> None:
    """Print without constructing a second list or a joined output string."""
    for value in random_permutation(n, rand):
        print(value)
```

## בדיקות

נבדקו כל 5,914 מסלולי ההגרלה ל־N=0..7. בכל גודל התקבלו בדיוק N! תמורות שונות, ללא איברים חסרים או כפולים. נבדקו גם גבולות קריאות rand, שישה תרחישי קצה גדולים וקלטים לא תקינים. אין זו בדיקת איכות מקור האקראיות.

[קוד בדיקה](../checks/check_prep_022.py) · [קוד פתרון](../solutions/prep_022_random_permutation.py)

## תשובה קצרה לראיון

אמלא מערך ב־1 עד N. בכל מקום i אגריל אינדקס רק מתוך התאים שטרם נקבעו: j=i+rand(N−i)−1, ואחליף ביניהם. כך כל מספר נבחר פעם אחת וכל תמורה מתקבלת בהסתברות 1/N! בהנחת הגרלות אחידות. זמן Θ(N), מערך Θ(N) וזיכרון עזר O(1). אותו פתרון עונה על שני הסעיפים.

## English

Given a nonnegative integer N, print a random permutation of all integers from 1 through N without repeating a number, as efficiently as possible. You have rand(m), returning a random integer from 1 through m inclusive. (a) Any data structure may be used. (b) Use only an array.

Hint 1: Repeatedly drawing from 1..N can yield duplicates. How could you draw only from values still available?

Hint 2: Keep the remaining values in an array. Removing a selected value need not shift every element: an exchange with a boundary element can help.

Hint 3: Partition the array into a fixed prefix and an unchosen suffix. Uniformly choose an index in that suffix and swap it into the next fixed slot. Convert the one-based rand(m) result to a zero-based index.

Use Fisher–Yates. Part (a) permits any structure, including an array, so the same optimal-time construction solves both parts. Model unchosen values as a bag: choose an index uniformly, exchange with a boundary element, and shrink the active range without shifting elements.

For part (b), initialize arr=[1,...,N]. At iteration i the prefix before i is fixed and the suffix i..N-1 holds unchosen values. Set j=i+rand(N-i)-1, swap arr[i] and arr[j], and advance i. Perform N-1 iterations; the final remaining value needs no draw. For N=5,i=2, rand(3) gives offsets 1..3, hence j=2,3,4. Allow j=i.

Swaps preserve the multiset and fixing one value per position prevents duplicates. Assuming uniform independent bounded draws (or conditional uniformity given prior draws), each particular permutation has probability 1/N × 1/(N-1) × ... × 1 = 1/N!. The supplied prompt does not explicitly promise uniformity or independence; those are stated assumptions for uniform output, not for avoiding duplicates.

Initialization, shuffle and output take Θ(N) item operations when bounded RNG and array access cost O(1), optimal because N items must be output. There are max(N-1,0) random calls. Total array storage is Θ(N), with O(1) extra shuffle storage. No absolute minimum-memory claim is made. Decimal-character I/O and arbitrary-precision costs are outside the item-operation model. N=0 gives an empty output, N=1 gives [1], and neither calls rand.

Repeated rejection of already-seen values requires Θ(N log N) expected draws and has no finite worst-case draw bound. Swapping each position with a random index from the whole array is generally biased. Deleting from the middle of an array can require O(N) shifts per choice. An ordinary linked list does not provide O(1) access to a uniformly selected index.

Python implementation (rand is the supplied inclusive one-based function):

```python
"""Fisher-Yates using the question's inclusive, one-based rand(m) contract."""
from collections.abc import Callable


def random_permutation(n: int, rand: Callable[[int], int]) -> list[int]:
    """Assume independent uniform draws; O(n) time, O(1) space beyond array."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError('n must be a nonnegative integer')
    values = list(range(1, n + 1))
    for i in range(n - 1):
        offset = rand(n - i)
        if not isinstance(offset, int) or not 1 <= offset <= n - i:
            raise ValueError('rand(m) must return an integer in [1, m]')
        j = i + offset - 1
        values[i], values[j] = values[j], values[i]
    return values


def print_random_permutation(n: int, rand: Callable[[int], int]) -> None:
    """Print without constructing a second list or a joined output string."""
    for value in random_permutation(n, rand):
        print(value)
```

התוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.


### הרחבה: סעיף א עם מבנה שאינו מערך, וסעיף ב עם מערך

הקלט הוא רק N. כל מבנה להלן נוצר על ידינו במהלך הפתרון. אין לדעת מהניסוח מה בדיוק ציפה המראיין; סעיף א מתיר מערך ולא מחייב פתרון אחר. להלן גם פתרון תקף ללא מערך.

**אפשרות טבעית לסעיף א — set:** ניצור קבוצה ריקה של מספרים שהודפסו. נגריל rand(N); אם המספר חדש נדפיס ונכניס לקבוצה, ואם כבר קיים נגריל שוב. כך לא מדפיסים כפילויות. אבל כשהודפסו N−1 מספרים, הסיכוי לקבל את האחרון בכל ניסיון הוא 1/N. בהנחת הגרלות אחידות ועצמאיות ופעולות hash בתוחלת O(1), מספר ההגרלות הצפוי הוא N×(1/N+1/(N−1)+...+1)=Θ(N log N), והמקום O(N). אין חסם סופי למספר ההגרלות במקרה הגרוע. לכן זו אפשרות להסבר ראשוני, לא הבחירה הטובה ביותר לבקשת היעילות בזמן. שימוש ב־set אינו מספק כשלעצמו גישה בזמן קבוע לאיבר במיקום אקראי; המרתו לרשימה בכל צעד מוסיפה עבודה ומערך.

**סעיף א — פתרון יעיל עם מילון (טבלת גיבוב):** המילון ממפה מיקום פעיל למספר שנותר: בהתחלה {1:1,2:2,...,N:N}. המפתחות הפעילים הם בדיוק 1..m. בוחרים r=rand(m), מדפיסים את remaining[r], מעתיקים למפתח r את הערך שבמפתח m, מוחקים את המפתח m ומקטינים את m. כך מוציאים את המספר שנבחר בלי להשאיר חור בטווח המפתחות. אם r=m, ההשמה היא לעצמו ואחריה מוחקים את אותו מפתח — גם זה תקין. בדוגמה N=5, אחרי בחירת מפתח 2 והדפסת 2, המילון הוא {1:1,2:5,3:3,4:4}. עכשיו rand(4) בוחרת רק בין ארבעת המספרים שנותרו.

זמן כולל Θ(N) בתוחלת בהנחת פעולות טבלת גיבוב בתוחלת O(1) ו־rand בזמן קבוע; מקום O(N). זה אינו חסם גרוע־ביותר בלתי מותנה לטבלת גיבוב. המילון משמש כמערך לוגי צפוף של מיקומים, אך מבנה הנתונים בקוד הוא מילון. אין לו כאן יתרון על מערך; הוא מוצג כחלופה שאינה מערך, כפי שהתבקש. בחירת מבנה נתונים מתייחסת להפשטה ולממשק, לא לאופן שבו ספריית Python מממשת פנימית את המילון.

**סעיף ב — מערך:** יוצרים [1,2,...,N]. רק m התאים הראשונים משתתפים בהגרלה. בוחרים j=rand(m)−1, מדפיסים arr[j], מחליפים את arr[j] עם arr[m−1] ומקטינים m. האיבר שנבחר נשאר בחלק הלא פעיל ולא ייבחר שוב. למשל [1,2,3,4,5] הופך אחרי בחירת 2 ל־[1,5,3,4 | 2], ובהמשך אחרי בחירת 3 ל־[1,5,4 | 3,2]. הפלט עד כאן 2,3. אין צורך למחוק פיזית או להזיז את כל האיברים.

זו גרסת קיבוע הסוף של Fisher–Yates, שקולה ברעיון לגרסת קיבוע ההתחלה המקורית שבמאגר. כאן מדפיסים את הבחירות מיד; אין להדפיס שוב את המערך בסיום, כי זה יכפיל את הפלט. זמן Θ(N) ומקום O(N) למערך, עם O(1) זיכרון עזר. עבור אותו רצף מיקומים אקראיים, חלופות המילון והמערך מפיקות בדיוק אותו רצף מספרים.

בשתיהן כל אחד מ־m המספרים שנותרו נבחר בהסתברות 1/m, ולכן כל פרמוטציה מתקבלת בהסתברות 1/N! בהנחת אחידות. N=0 נותן פלט ריק; N=1 דורש רק הדפסת 1. אפשר לחסוך את ההגרלה האחרונה כי נשאר מספר אחד בלבד.

**מימושים בדוקים:** permutation_with_dict ו־permutation_with_array בקובץ הקוד הם מחוללים (yield): הם מפיקים ערך אחד בכל שלב בלי לבנות רשימת פלט נוספת. להדפסה: for value in permutation_with_dict(N, rand): print(value), ובאופן זהה עם פונקציית המערך. החלפת yield chosen ב־print(chosen) נותנת פונקציית הדפסה ישירה. נבדקו כל 5,914 מסלולי ההגרלה ל־N=0..7 עבור שני המימושים, כולל שוויון פלט לכל מסלול, בדיוק N! תמורות לכל גודל, גבולות rand, 12 תרחישי קצה גדולים וקלטים לא תקינים.

[בדיקת החלופות](../checks/check_prep_022_structures.py)

### Extension: non-array part (a), array part (b)

Only N is supplied; every container is constructed by the algorithm. The source does not mandate a non-array structure in (a), nor establish an interviewer expectation. A natural set-of-used-values rejection sampler prints only new rand(N) draws. It is correct under independent uniform draws but takes N H_N = Θ(N log N) expected draws, O(N) space and has no finite worst-case draw bound. A set alone offers no constant-time uniformly indexed element selection.

An efficient non-array alternative uses a hash dictionary mapping active positions to remaining values, initialized as {1:1,...,N:N}. With active keys 1..m, pick r=rand(m), emit remaining[r], assign remaining[r]=remaining[m], delete remaining[m], then decrement m. This keeps the keys dense even when r=m. Expected Θ(N) time assumes expected O(1) hashing and bounded RNG; total storage O(N). It is not an unconditional worst-case hash-table bound. It offers no practical advantage over the array here; it satisfies the requested distinct data-structure example.

For (b), create [1,...,N], maintain active prefix length m, pick j=rand(m)-1, emit arr[j], swap arr[j] and arr[m-1], and decrement m. The emitted value is excluded from future draws without shifting. This is the shrinking-prefix variant of Fisher–Yates and yields exactly the same emitted values as the dictionary variant given identical draw positions. Do not print the complete array again after already emitting choices. Time Θ(N), total array space O(N), extra shuffle space O(1). For either method skip the last draw when m=1; N=0 yields nothing. Uniform conditional draws give each permutation probability 1/N!.

The code provides generators permutation_with_dict and permutation_with_array; iterate and print their yielded values to avoid accumulating another output list. Both were exhaustively checked on 5,914 draw paths for N=0..7, with N! unique outputs per size, identical per-path output, exact RNG bounds, 12 larger boundary cases and invalid-input tests.


## צילום נוסף וגרסת מערך נתון — 18 באוקטובר 2026

נשמרה [גרסה מלאה עם מערך קיים 1–100 וממשק rand_range](prep-022-hundred-array-rand-range-variant.md), כולל מקור, חברות לפי הצילום, שלושה רמזים בכל שפה, פתרון, קוד ואימות. הגרסה משולבת באותה שאלה באתר; היא שונה בממשק הקלט וההגרלה ואינה שאלה נוספת במונה המאגר. נוספו שיוכי Google ו־Mellanox לפי הצילום, ללא שינוי הייחוס למקורות קודמים.


## Additional supplied source — 2026-10-21

יש לך מערך של מספרים. כתוב פונקציה שתסדר אותם בסדר אקראי. אתה יכול להיעזר בפונקציה Rand, שמחזירה מספר אקראי

[Preserved source](../sources/prep-022-additional-2026-10-21.png)

Reported companies: Apple, NVIDIA, Intel, Amazon.

### Hebrew clarification

זו גרסת מערך נתון כללי; סדר והופעות של הערכים נשמרים באמצעות החלפות. הממשק והאחידות של Rand אינם מפורטים במקור ויש להגדיר חוזה הגרלה חסום ואחיד.

### English clarification

General supplied-array variant. Swaps preserve values and multiplicities. Source Rand lacks a bound/distribution contract; uniform bounded draws must be explicitly specified.

### Additional learner prompt and proposed solution



### גרסה נוספת: ערבוב מערך נתון

נתון מערך כללי של ערכים, לאו דווקא ממוינים או שונים זה מזה. כתבו פונקציה שמערבבת את המערך הקיים במקום, בלי לאבד איברים ובלי לשנות את מספר ההופעות של אף ערך. נתונה רק פונקציה בשם `Rand` המחזירה מספר אקראי; הגדירו איזה ממשק טווח ואיזו הבטחת התפלגות נחוצים כדי לקבל ערבוב אחיד. נתחו זמן וזיכרון עזר וטפלו במערך ריק או בן איבר אחד. הבהירו את משמעות האחידות כשיש ערכים חוזרים.


### הרחבת המערך הכללי והופעות חוזרות

אותו Fisher–Yates פועל על מערך נתון מכל סוג ובכל סדר. אין צורך ליצור את 1 עד N, למיין או לייצר ערכים חדשים: רק מחליפים בין תאים. בכל החלפה נשמרים אותם איברים ואותן הופעות. המימוש הקיים `shuffle_in_place` עובד גם על ערכים חוזרים ואף על אובייקטים שאינם ניתנים לגיבוב, משום שאינו מבצע חיפוש או מכניס אותם ל־set.

המילה Rand לבדה אינה מספקת חוזה. לצורך המימוש נדרש מתאם `rand_range(low, high)` המחזיר מספר שלם בכל טווח סגור מבוקש, אחיד בהינתן ההיסטוריה. אם הממשק בפועל הוא `Rand(m)` בטווח `0..m-1`, משתמשים ב־`Rand(i+1)`; אם בטווח `1..m`, משתמשים ב־`Rand(i+1)-1`. מתאם כזה תקף רק אם מקור ההגרלה אכן מקיים את החוזה. אין להניח שניתן להפוך כל מקור מוטה למקור אחיד בהמרה פשוטה, או להשתמש בשארית מודולו בלי לבדוק הטיה. בלי אחידות, החלפות עדיין משמרות איברים אבל אינן מבטיחות התפלגות אחידה.

האחידות הראשונית היא על כל N! התמורות של **זהויות המיקומים המקוריים**. כשערכים חוזרים, כמה תמורות כאלה נראות אותו סדר ערכים. לכל סדר ערכים מובחן יש אותו מספר תמורות אינדקסים: מכפלת העצרת של מספר ההופעות של כל ערך. לכן גם סדרי הערכים המובחנים אחידים בהגרלה אחידה, אך ההסתברות של כל סדר כזה אינה בהכרח 1/N!. לדוגמה, עבור `[A,A,B]` יש שש תמורות אינדקסים ורק שלושה סדרי ערכים; כל סדר מתקבל בשתיים מהתמורות ולכן בהסתברות 1/3, לא 1/6. האיברים המוחזקים אינם משוכפלים או אובדים.

העלות היא Theta(N) פעולות והחלפות ו־O(1) מילות עזר מעבר למערך הקיים, בהנחת גישה והגרלה חסומה בזמן קבוע. מערך ריק או יחיד אינו דורש הגרלה. הבדיקות הנוספות עברו על כל 5,914 מסלולי הבחירה לאורכים 0–7, באמצעות זהויות אובייקטים; שש התמורות של `[A,A,B]` ועשרה מקרי קצה של אובייקטים, כולל ערכים שאינם ניתנים לגיבוב. זו בדיקת האלגוריתם, לא בדיקת איכות סטטיסטית של מחולל אקראי.



### Additional variant: shuffle a supplied array

Given an arbitrary array whose values need not be sorted or distinct, shuffle the existing array in place without losing elements or changing any value’s multiplicity. Only a function named `Rand` returning a random number is supplied; specify the bounded interface and distribution guarantee needed for a uniform shuffle. Analyze time and auxiliary storage and cover empty/singleton arrays. Clarify what uniformity means when values repeat.


### General supplied arrays and repeated values

The same Fisher–Yates method works on an existing array of any values and any initial order. Do not create 1..N, sort or generate replacement values: only swap cells. Every swap preserves the elements and their multiplicities. Existing `shuffle_in_place` also handles repeated values and unhashable objects because it performs no membership lookup or set insertion.

The name Rand alone is not an interface contract. The implementation requires an adapter `rand_range(low, high)` giving a conditionally uniform integer in the requested inclusive interval. If the actual interface is `Rand(m)` over `0..m-1`, use `Rand(i+1)`; if it is over `1..m`, use `Rand(i+1)-1`. Such adapters are valid only if the source satisfies their contract. Do not assume a simple conversion makes an arbitrary biased source uniform, or use modulo reduction without checking bias. Without uniformity, swaps preserve elements but do not promise uniform orders.

Uniformity initially concerns the N! permutations of **original indexed element identities**. With duplicate values, multiple index permutations display the same value order. Every distinct value order has the same number of index permutations: the product of factorials of value multiplicities. Thus distinct observable value orders are also uniform, but each need not have probability 1/N!. For `[A,A,B]`, six index permutations yield three value orders, each represented twice and hence having probability 1/3 rather than 1/6. No held element is duplicated or lost.

Cost is Theta(N) operations/swaps and O(1) auxiliary words beyond the supplied array, assuming constant-time access and bounded draws. Empty/singleton arrays require no draws. Additional checks cover all 5,914 choice paths for lengths 0..7 using object identities, all six index permutations of `[A,A,B]`, and ten boundary cases including unhashable objects. These check the algorithm, not statistical generator quality.

[Additional check](../checks/check_prep_022_generic_array.py)
[Verification evidence](../checks/prep-022-generic-array-verification.json)
