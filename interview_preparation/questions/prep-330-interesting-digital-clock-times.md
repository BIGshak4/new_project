# PREP-330 — נקודות זמן בשעון המשתמשות בשתי ספרות לכל היותר

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-15-batch20-03.png)

Count interesting HH:MM:SS timestamps between S and T inclusive on one day. A timestamp is interesting when at most two different digits occur. Implement class Solution { public int solution(String S, String T); }.

## נקודות זמן בשעון המשתמשות בשתי ספרות לכל היותר

כתבו פונקציה המקבלת S ו־T בפורמט HH:MM:SS בשעון של 24 שעות, באותו יום ועם S≤T. ספרו את נקודות הזמן בטווח הכולל את שני הקצוות שבהן שש הספרות מכילות לכל היותר שתי ספרות שונות. השעות בין 00 ל־23 והדקות והשניות בין 00 ל־59. הנקודתיים אינן ספרות, ואפסים מובילים משתתפים בספירה. עבור 15:15:00 עד 15:15:12 התוצאה 1. עבור 22:22:21 עד 22:22:23 התוצאה 3. כתבו גם מימוש Java עם חתימה public int solution(String S, String T). הקלט מובטח תקין.

### רמזים

1. כמה נקודות זמן לכל היותר יש ביום אחד?
2. המירו שעה למספר שניות מאז חצות וסרקו את הטווח הכולל.
3. לכל שנייה בנו בדיוק שש ספרות עם אפסים מובילים, והוסיפו לספירה אם קבוצת הספרות בגודל לכל היותר 2.

### פתרון מוצע

יום מכיל 86,400 שניות בלבד, ולכן אפשר לבדוק כל נקודה. נמיר h:m:s לערך 3600h+60m+s. נסרוק מההתחלה עד הסוף כולל ונפרק כל ערך חזרה לשש הספרות. קבוצת ספרות בגודל 1 או 2 עוברת את התנאי. לחלופין ב־Java מסכת ביטים של עשרה ביטים מסמנת אילו ספרות נראו; Integer.bitCount(mask) נותנת את מספרן.

בדוגמה הראשונה רק 15:15:11 משתמשת ב־1 וב־5 בלבד. בדוגמה השנייה שלוש הנקודות משתמשות בזוג הספרות {1,2}, בספרה {2}, ובזוג {2,3}, בהתאמה. לכל נקודה יש ייצוג של שנייה אחת, והסריקה מבקרת בכל שנייה בטווח פעם אחת בדיוק, ולכן הספירה נכונה. עבור K נקודות הזמן עולה Θ(K) זמן ו־O(1) מקום עזר, משום שגודל קבוצת הספרות חסום בעשר. אחרי הכנה חד־פעמית של סכומי קידומת ליום אפשר לענות על הרבה שאילתות ב־O(1) לשאילתה. המימוש שלהלן זמין להרצה ב־Python, וקובץ Java המצורף מממש אותה בדיקה באמצעות מסכה.

```python
"""Count inclusive same-day timestamps with at most two decimal digits."""
def clock_seconds(value):
    if not isinstance(value, str) or len(value) != 8 or value[2] != ":" or value[5] != ":":
        raise ValueError("HH:MM:SS required")
    digits = value[:2] + value[3:5] + value[6:]
    if not all("0" <= c <= "9" for c in digits):
        raise ValueError("ASCII decimal digits required")
    h, m, s = int(value[:2]), int(value[3:5]), int(value[6:])
    if h >= 24 or m >= 60 or s >= 60:
        raise ValueError("Invalid time")
    return h * 3600 + m * 60 + s


def count_interesting_times(start, end):
    first, last = clock_seconds(start), clock_seconds(end)
    if first > last:
        raise ValueError("Same-day ordered interval required")
    count = 0
    for second in range(first, last + 1):
        h, remainder = divmod(second, 3600)
        m, s = divmod(remainder, 60)
        text = f"{h:02d}{m:02d}{s:02d}"
        if len(set(text)) <= 2:
            count += 1
    return count
```

### הנחות

זמני הקלט חוקיים באותו יום, בפורמט ASCII קבוע. השעות כוללות אפסים מובילים.

### מקרה קצה

00:00:00 עד אותה שעה מחזיר 1; גבול דקה, גבול שעה ו־23:59:59 נכללים כרגיל.

### טעות נפוצה

ספירת הנקודתיים, השמטת אפסים מובילים או עצירה לפני T משנים את התנאי.

### סיבוכיות או עלות

Θ(K) זמן ו־O(1) זיכרון נוסף לסריקה הראשית. K≤86400 תחת חוזה של יום אחד.

### בדיקות

סריקת כל היום והשוואת תנאי המסכה לבדיקה בלתי תלויה באמצעות קבוצת ספרות. נבדקו גם שני קצוות זהים והדוגמאות.

### תשובה קצרה

אעבור על השניות בטווח ואספור רק זמנים בעלי לכל היותר שתי ספרות שונות.

### שאלת המשך

כיצד תענו על מיליון שאילתות לאותו יום? בנו prefix[second+1] כסכום האינדיקטורים. תשובת [a,b] היא prefix[b+1]−prefix[a].

## Digital clock times containing at most two digits

Given valid same-day 24-hour times S and T in HH:MM:SS format with S≤T, count timestamps in the inclusive interval whose six displayed decimal digits use at most two distinct digits. Hours range from 00 to 23 and minutes/seconds from 00 to 59. Ignore colons and retain leading zeroes. The answer for 15:15:00 through 15:15:12 is 1. The answer for 22:22:21 through 22:22:23 is 3. Also provide Java method public int solution(String S, String T). Inputs are guaranteed valid.

### Hints

1. How many timestamps can occur during one day?
2. Convert both times into seconds since midnight and scan the inclusive interval.
3. Reconstruct exactly six digits with leading zeroes for each second and count it when the digit set has size at most two.

### Proposed solution

A day contains only 86,400 seconds. Convert h:m:s into 3600h+60m+s and iterate through both endpoints. For each second reconstruct its six decimal digits, including leading zeroes. Accept digit sets of size one or two. The Java version uses a ten-bit mask and Integer.bitCount(mask).

Only 15:15:11 qualifies in the first example. In the second, the three digit sets are {1,2}, {2}, and {2,3}. Every displayed time corresponds to exactly one second and the loop visits each second in the requested interval exactly once, so the result counts precisely the qualifying times. For K timestamps this costs Θ(K) time and O(1) extra space, since the digit set has size at most ten. For many queries, one prefix-count array for the day reduces each query to O(1). The runnable Python reference below and attached Java implementation use the same contract.

```python
"""Count inclusive same-day timestamps with at most two decimal digits."""
def clock_seconds(value):
    if not isinstance(value, str) or len(value) != 8 or value[2] != ":" or value[5] != ":":
        raise ValueError("HH:MM:SS required")
    digits = value[:2] + value[3:5] + value[6:]
    if not all("0" <= c <= "9" for c in digits):
        raise ValueError("ASCII decimal digits required")
    h, m, s = int(value[:2]), int(value[3:5]), int(value[6:])
    if h >= 24 or m >= 60 or s >= 60:
        raise ValueError("Invalid time")
    return h * 3600 + m * 60 + s


def count_interesting_times(start, end):
    first, last = clock_seconds(start), clock_seconds(end)
    if first > last:
        raise ValueError("Same-day ordered interval required")
    count = 0
    for second in range(first, last + 1):
        h, remainder = divmod(second, 3600)
        m, s = divmod(remainder, 60)
        text = f"{h:02d}{m:02d}{s:02d}"
        if len(set(text)) <= 2:
            count += 1
    return count
```

### Assumptions

Valid fixed-width ASCII times on the same day, including leading zeroes.

### Edge case

A singleton interval 00:00:00 returns 1. Minute/hour boundaries and 23:59:59 remain valid endpoints.

### Common mistake

Counting colons, dropping leading zeroes or excluding T changes the stated test.

### Cost

Θ(K) scan time and O(1) extra space. K≤86400 under the same-day contract.

### Verification

Every second of the day was compared using independent mask and digit-set predicates, together with both examples and singleton boundaries.

### Interview answer

Visit each second and count exactly those six-digit displays containing at most two distinct digits.

### Follow-up

How would you answer a million queries for the same day? Precompute prefix[second+1]. Then [a,b] has prefix[b+1]−prefix[a] interesting displays.

[checks/check_nov15_software.py](../checks/check_nov15_software.py)

[checks/prep-330-1115-verification.json](../checks/prep-330-1115-verification.json)

[solutions/prep_330_interesting_clock.py](../solutions/prep_330_interesting_clock.py)

[Java implementation](../solutions/prep_330_interesting_clock.java)
