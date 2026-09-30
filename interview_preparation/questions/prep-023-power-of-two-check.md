# PREP-023 — זיהוי חזקה של 2

## השאלה המקורית

בהינתן מספר, איך אפשר לדעת אם הוא חזקה שלמה של 2 תוך שימוש ב־O(1) פעולות חישוב.

![צילום המקור](../sources/prep-023.png)

## קטגוריות וחברות

תגית מקור: software. סיווג נוסף: פעולות על ביטים, ייצוג בינארי, חזקות של 2 וסיבוכיות. חברות לפי התמונה בלבד: Amazon, MaxLinear, NVIDIA, Qualcomm, Valens, Apple, Intel. השיוך לא אומת עצמאית. התגיות tag-2 ו־2312313 נשמרו ללא סיווג כי משמעותן אינה ברורה. אין תווית חברה ראשית נפרדת בצילום.

## רלוונטיות להכנה

עדיפות גבוהה לתרגול קצר של יסודות ביטים ומקרי קצה, המשלבים חשיבה בחומרה ובתוכנה. זו הערכת הכנה לפי תיאור המשרה, לא תחזית לראיון.

## שלושה רמזים מדורגים

1. נסה לכתוב בבינארי את המספרים 1, 2, 4, 8 ו־16. איזו תכונה משותפת מופיעה בכל הייצוגים?

2. קח מספר שהוא חזקה של 2 והשווה בבינארי בינו לבין המספר שקטן ממנו באחד. באילו מקומות נמצאים האחדים בכל אחד מהם?

3. בדוק מה מתקבל מ־AND ביטי בין n לבין n−1. נסה גם מספר שאינו חזקה של 2, ואל תשכח לבדוק בנפרד את 0 ואת 1.

## הצעה לפתרון

**הנחה:** הקלט מספר שלם. בודקים אם הוא 2^k עבור k שלם אי־שלילי, ולכן 1=2^0 נחשב חזקה של 2; אפס ומספרים שליליים לא. נוסח המקור אינו מגדיר סוג מספר או רוחב, ולכן ההנחה מצוינת במפורש. אם הכוונה גם לשברים כמו 1/2 או למעריכים שליליים, זו בעיה עם מודל קלט אחר.

**הפתרון:**

```python
def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0
```

& הוא AND ביטי בין הביטים של שני המספרים; and מחבר את שני התנאים הבוליאניים. מניחים שהפונקציה מקבלת int, ולא float. אין כאן שימוש בלוגריתם או בלולאה.

**איך מגיעים לזה?** חזקות של 2 נראות בבינארי כך: 1, 10, 100, 1000, 10000. בכל אחת בדיוק ביט 1 אחד. כאשר מחסירים 1 מחזקה של 2, ה־1 היחיד הופך ל־0 וכל האפסים שמימינו הופכים ל־1. למשל:

```text
8     = 1000
8 - 1 = 0111
AND   = 0000
```

לא נשאר אף מקום שבו שני המספרים מכילים 1, לכן תוצאת AND היא אפס.

**למה זה שולל גם מספרים שאינם חזקות?** לכל n חיובי, הפעולה n & (n−1) מכבה בדיוק את ה־1 הימני ביותר (הפחות משמעותי) ומשאירה את כל הביטים שמשמאלו כפי שהיו. חיסור 1 מאפס את ה־1 הימני והופך את האפסים שמימינו לאחדים; ה־AND מאפס את אותם מקומות כי ב־n הם היו אפסים. הביטים הגבוהים נשארים. אם היה בדיוק 1 אחד, לא נשאר דבר. אם היו שניים או יותר, לפחות אחד עדיין נשאר ולכן התוצאה אינה אפס. למשל 12=1100 ו־11=1011 נותנים AND=1000, ולכן 12 אינו חזקה של 2.

**למה התנאי n>0 נחוץ?** ללא התנאי, 0 & (0−1) מחזיר 0 בפייתון והיינו מקבלים את אפס בטעות. התנאי גם שולל קלטים שליליים. 1 מתקבל כי 1>0 וגם 1 & 0=0.

**יעילות ודיוק O(1):** מספר הפעולות בקוד קבוע: בדיקת חיוביות, חיסור אחד, AND והשוואה לאפס. עבור מספר שלם ברוחב מכונה קבוע, במודל שבו הפעולות הללו בסיסיות, הזמן והזיכרון הנוסף O(1). בפייתון int יכול לגדול ללא גבול: לפעולות על L ביטים יש עלות התלויה ב־L (במקרה הגרוע לינארית במספר הביטים/מילות הייצוג), ומוקצים ערכי ביניים. לכן מספר פעולות ברמת הקוד קבוע, אבל אין הבטחת זמן או זיכרון O(1) עבור מספרים באורך בלתי מוגבל. אין כאן טענה לזמן פיזי קבוע או למינימום מספר הוראות מעבד. הביטוי עונה לדרישת מספר פעולות קבוע תחת המודל המקובל, בלי להמציא רוחב שלא ניתן.

**מקרי קצה:** 0→False, 1→True, 2→True, 3→False, 12→False, 16→True. מספר שלילי תמיד False. לוגריתם בנקודה צפה עלול להוביל לשגיאות עיגול ואין צורך בו; חלוקה חוזרת ב־2 או ספירת ביטים בלולאה אינן מספר קבוע של פעולות עבור רוחב משתנה.

**בדיקה:** הביטוי הושווה לקבוצת חזקות שנוצרה בנפרד לכל 131,073 המספרים מ־‎−65,536 עד 65,536. נבדקו גם 32 מקרי קצה סביב חזקות עם מעריכים 31,32,63,64,127,128,1024,4096. זו בדיקת נכונות, לא מדידת זמן קבוע של BigInt.

[קוד](../solutions/prep_023_power_of_two.py) · [בדיקות](../checks/check_prep_023.py)

## תשובה לראיון

לחזקה חיובית של 2 יש בדיוק ביט 1 אחד. הפעולה n & (n−1) מכבה את ה־1 הימני ביותר, ולכן אבדוק n>0 וגם תוצאה אפס. כך 1 מתקבל, ואפס ושליליים נדחים. זה O(1) למילה ברוחב קבוע; בפייתון עם מספרים בלתי מוגבלים עלות הפעולות תלויה באורך.

## חפיפה למאגרים קיימים

השאלה מופיעה בגרסה עם קלט uint32 מפורש ב־[SW-002](../../example_question/software/bit_manipulation/sw-002-power-of-two-check.md), ובשאלה משולבת ב־[VSW-002](../../verify_example_questions/software/bit_manipulation/vsw-002-power-two-msb.md). זו הרשומה הראשונה שלה במאגר ההכנה הנוכחי; נשמרו המקור החדש והנחותיו בנפרד.

## English

Given a number, how can you determine whether it is an integer power of 2 using O(1) computation operations?

Hint 1: Write 1, 2, 4, 8 and 16 in binary. What feature do they share?

Hint 2: Compare a power of two with one less than it in binary. Where are their set bits?

Hint 3: Examine the bitwise AND of n and n-1, also for a non-power. Handle zero and one explicitly.

Assume an integer input and test n=2^k for integer k>=0, including 1=2^0 and excluding zero/negatives. The source does not specify numeric type or width. Fractions and negative exponents would require a different input contract.

Python: return n > 0 and (n & (n - 1)) == 0. The & operator is bitwise AND; and combines Boolean conditions. For every positive n, n & (n-1) clears exactly its least significant set bit. Subtraction flips that bit to zero and the lower zeros to ones, leaving higher bits unchanged; AND clears the changed lower portion while preserving higher bits. Thus the result is zero precisely when n originally contained one set bit, exactly the positive powers of two. Example: 8=1000, 7=0111, AND=0000. Counterexample: 12=1100, 11=1011, AND=1000. The positivity guard prevents accepting zero and excludes negatives. One is accepted because 1 & 0 is zero.

There is a constant number of word-level operations and O(1) extra space for fixed-width machine integers. Python's arbitrary-size int operations cost time and intermediate space dependent on bit length, so a constant number of source-level operations is not an unconditional constant-time/space claim for unbounded integers. No claim of physically constant timing or minimum instruction count is made. Repeated division/scanning takes width-dependent steps; floating-point logarithms introduce unnecessary rounding concerns.

Checked all 131073 integers in [-65536,65536] against an independently generated powers set, plus 32 large boundary cases around powers with exponents 31,32,63,64,127,128,1024,4096. This verifies results, not BigInt timing.

התוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.
