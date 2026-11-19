# PREP-347 — פירמידת כוכבים ברוחב בסיס אי־זוגי

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-15-batch20b-05.png)

כתוב פונקציה המקבלת מספר אי־זוגי ומחזירה פירמידה ממורכזת מכוכבים שהמספר הוא רוחב בסיסה. פתרו בשתי דרכים. n=5 נותן שורות של 1,3,5 כוכבים.

## פירמידת כוכבים ברוחב בסיס אי־זוגי

ממשו שתי פונקציות המקבלות רוחב בסיס n, מספר שלם חיובי אי־זוגי, ומחזירות אותה פירמידת כוכבים ממורכזת. בכל שורה מספר כוכבים אי־זוגי, החל באחד ועד n. בחרו דרך אחת שבונה שורה בעזרת חזרות מחרוזת ודרך שנייה שמשתמשת בלולאות תאים. הפלט כולל רווחי הזחה משמאל, ללא רווחי סוף שורה וללא ירידת שורה אחרי השורה האחרונה. עבור n=5 מתקבל

```text
  *
 ***
*****
```

### רמזים

1. כמה שורות יש עד שמגיעים מ־1 ל־n בקפיצות של שתיים?
2. בשורה r שמתחילה באפס יש 2r+1 כוכבים. ההזחה צריכה להשלים את חצי הרוחב שנותר.
3. נסמן h=(n+1)//2. בשורה r כותבים h-r-1 רווחים ואז 2r+1 כוכבים. בדרך התאים הגבול בין רווח לכוכב נמצא בעמודה h-r-1.

### פתרון מוצע

מספר השורות הוא h=(n+1)/2. בשורה r מ־0 עד h−1 יש 2r+1 כוכבים ו־h−r−1 רווחים לפניהם. בכל מעבר מתווסף כוכב מכל צד ולכן מרכז הכוכב העליון נשמר. בשורה האחרונה ההזחה אפס ומספר הכוכבים הוא n.

בדרך הראשונה מחברים שתי חזרות מחרוזת בכל שורה ומחברים את השורות עם ירידת שורה. בדרך השנייה עוברים על העמודות הנכתבות, מוסיפים רווח לפני הגבול וכוכב אחריו. שתיהן מחזירות אותו טקסט בדיוק. אפשר להדפיס באמצעות print(pyramid(n)); ירידת השורה ש־print מוסיפה אינה חלק מערך ההחזרה.

נכתבים Θ(n²) תווים, ולכן זמן ההפקה והזיכרון של מחרוזת התוצאה הם Θ(n²). אם מדפיסים שורה ומיד משליכים אותה, זיכרון העבודה מעבר לפלט יכול להיות O(n). אין פלט מפורש של כל הפירמידה בזמן תת־ריבועי, משום שצריך לכתוב את התווים. קלט זוגי, לא חיובי או שאינו int נדחה.

```python
"""Return a centered pyramid with odd positive base width and no trailing spaces."""


def pyramid(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    return "\n".join(" " * ((width - stars) // 2) + "*" * stars
                     for stars in range(1, width + 1, 2))


def pyramid_by_cells(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    rows = []
    height = (width + 1) // 2
    for row in range(height):
        cells = []
        for column in range(height + row):
            cells.append(" " if column < height - row - 1 else "*")
        rows.append("".join(cells))
    return "\n".join(rows)
```

### הנחות

n הוא int חיובי אי־זוגי. אין צורך ברווחים מימין כדי להראות את הפירמידה.

### מקרה קצה

n=1 מחזיר כוכב יחיד. ערך bool נדחה למרות יחסו ל־int ב־Python.

### טעות נפוצה

פירוש n כגובה במקום כרוחב בסיס, או שימוש ב־n כוכבים בכל שורה.

### סיבוכיות או עלות

Θ(n²) זמן ותווי תוצאה. שתי הגרסאות עומדות בחסם גודל הפלט.

### בדיקות

שתי הגרסאות הושוו לאורקל תאים עצמאי לכל רוחב אי־זוגי מ־1 עד 99 ונבדקו קלטים פסולים.

### תשובה קצרה

גובה הפירמידה (n+1)/2. בשורה r כותבים h-r-1 רווחים ו־2r+1 כוכבים. שתי דרכי הבנייה נבדלות באופן יצירת השורה.

### שאלת המשך

איך מפיקים בלי להחזיק את כל הפלט? מפיקים ומדפיסים שורה בכל פעם, תוך שמירת אותה נוסחת הזחה.

## Centered star pyramid with an odd base width

Implement two functions taking a positive odd integer base width n and returning the same centered star pyramid. Rows contain odd star counts from one through n. One implementation should build each line with string repetition; the other should use cell loops. Include leading indentation, no trailing spaces, and no newline after the final row. For n=5 return

```text
  *
 ***
*****
```

### Hints

1. How many rows take the star count from one to n in steps of two?
2. Zero-based row r has 2r+1 stars. The indentation must fill half the remaining width.
3. Let h=(n+1)//2. Row r contains h-r-1 spaces followed by 2r+1 stars. In the cell approach, the boundary is column h-r-1.

### Proposed solution

The height is h=(n+1)/2. Row r from zero through h−1 contains 2r+1 stars preceded by h−r−1 spaces. Each next row adds a star on both sides, preserving the center. The final row has no indentation and exactly n stars.

The first method joins two repeated strings for each row and then joins rows with newline separators. The second loops through written columns, selecting a space before the boundary and a star after it. Both return exactly the same text. print(pyramid(n)) may display it; the newline added by print is outside the returned string.

There are Θ(n²) output characters, so output time and result storage are Θ(n²). Streaming one row at a time can use O(n) working storage beyond the output. Explicitly writing the entire pyramid cannot take subquadratic time. Reject even, non-positive and non-integer inputs.

```python
"""Return a centered pyramid with odd positive base width and no trailing spaces."""


def pyramid(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    return "\n".join(" " * ((width - stars) // 2) + "*" * stars
                     for stars in range(1, width + 1, 2))


def pyramid_by_cells(width):
    if type(width) is not int or width <= 0 or width % 2 == 0:
        raise ValueError("base width must be an odd positive integer")
    rows = []
    height = (width + 1) // 2
    for row in range(height):
        cells = []
        for column in range(height + row):
            cells.append(" " if column < height - row - 1 else "*")
        rows.append("".join(cells))
    return "\n".join(rows)
```

### Assumptions

n is a positive odd int. Right padding is unnecessary for the required visual shape.

### Edge case

n=1 returns one star. Reject bool even though Python treats it as an int subclass.

### Common mistake

Treating n as the height instead of the base width, or printing n stars on every row.

### Cost

Θ(n²) time and result characters. Both methods meet the output-size lower bound.

### Verification

Compared both methods with an independent cell oracle for every odd width from 1 through 99, and tested invalid inputs.

### Interview answer

Height is (n+1)/2. Row r has h-r-1 leading spaces and 2r+1 stars. The methods differ in how each line is produced.

### Follow-up

How can output be produced without storing it all? Build and print one row at a time using the same indentation formula.

[checks/check_nov15b_software.py](../checks/check_nov15b_software.py)

[checks/prep-347-1115b-verification.json](../checks/prep-347-1115b-verification.json)

[solutions/prep_347_star_pyramid.py](../solutions/prep_347_star_pyramid.py)
