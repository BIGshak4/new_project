# PREP-335 — שלושה תיקונים של תו אחד ללולאה

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-15-batch20-10.png)

שנה את for(i=0;i<n;--i){printf("-");} בהוספה או שינוי תו אחד כך שיודפסו 20 סימנים. תן שלושה פתרונות.

## שלושה תיקונים של תו אחד ללולאה

לכל הרצה הגדירו int n=20 ו־int i. התחילו בלולאה for(i=0;i<n;--i){printf("-");}. הציעו שלוש גרסאות שכל אחת שונה מהמקור בהוספה או בהחלפה של תו אחד בלבד, ומדפיסה בדיוק 20 תווי מקף. כל גרסה מתחילה מחדש מאותו מקור ומאותו n=20. אין לערוך את המחרוזת או להסתמך על גלישת int. הסבירו את תנאי העצירה.

### רמזים

1. הגוף מוריד את i לכיוון השלילי. איזה תנאי יפסיק אחרי הערך −19?
2. תנאי C הוא כל ביטוי שלם שאינו אפס. אפשר גם לשנות איזה משתנה מוקטָן.
3. בדקו בנפרד −i<n, את הביטוי i+n, והקטנת n במקום i.

### פתרון מוצע

המקור אינו לולאה סופית תקינה עבור signed int. i הולך וקטן, i<n נשאר אמת, ולבסוף ההקטנה עלולה לגלוש באופן לא מוגדר. שלוש עריכות חוקיות הן אלה.

א. להוסיף '-' לפני i בתנאי ולקבל -i<n. ערכי i בגוף הם 0,−1,…,−19. ב־i=−20 התנאי 20<20 שקר, ולכן יש בדיוק 20 הדפסות.

ב. להחליף '<' ב־'+' ולקבל i+n. הביטוי מקבל 20,19,…,1 בתחילת 20 האיטרציות, ואחר כך 0 ומסיים. ערך התנאי עצמו אינו חייב להיות 0 או 1.

ג. להחליף את i בביטוי העדכון --i ב־n ולקבל --n. i נשאר 0, n עובר 20,…,1 בגוף, וכאשר n=0 התנאי 0<0 שקר. אין גישה לא מוגדרת ואין גלישה בגרסאות הללו. n מסתיים ב־0 רק בגרסה השלישית; אם ערכו צריך להישמר זו דרישה נוספת. החלפת -- ב־++ צורכת שתי החלפות ולכן אינה אחת משלוש העריכות המותרות.

```c
/* C11. Each loop starts with fresh int i and n=20. */
#include <stdio.h>

int main(void) {
    int i, n = 20;
    for (i = 0; -i < n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i + n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i < n; --n) { printf("-"); }
    putchar('\n');
    return 0;
}
```

### הנחות

C11, משתני int, n מאותחל ל־20 בתחילת כל הרצה.

### מקרה קצה

יש להחזיר n ל־20 לפני כל גרסה. שימוש ב־unsigned משנה את הניתוח המקורי.

### טעות נפוצה

פלט של 20 מקפים כשמשתמשים בשתי עריכות אינו עומד בחוזה. אין להסיק שתנאי for חייב להיות השוואה.

### סיבוכיות או עלות

20 איטרציות לכל גרסה ו־O(1) מקום עזר.

### בדיקות

קוד C קומפל והורץ. הפלט אומת כשלוש שורות שכל אחת מכילה בדיוק 20 מקפים.

### תשובה קצרה

אשנה את התנאי ל־-i<n או ל־i+n, או אקטין את n במקום i. כל גרסה עוצרת אחרי 20 הדפסות.

### שאלת המשך

איזו גרסה שומרת את n? שתי הראשונות. השלישית צורכת את המונה n.

## Three one-character repairs of a loop

Each independent run declares int n=20 and int i. Start from for(i=0;i<n;--i){printf("-");}. Produce three versions, each using exactly one character insertion or replacement and printing exactly twenty hyphens. Reset n=20 for every version. Do not edit the string or rely on signed overflow. Explain termination.

### Hints

1. i moves into negative values. What condition stops after the body uses −19?
2. A C condition can be any scalar expression with a nonzero value. The decrement can target another variable.
3. Consider -i<n, the expression i+n, and decrementing n instead of i.

### Proposed solution

The original is not a valid terminating signed-int loop: i<n remains true as i decreases and decrementing eventually risks undefined overflow. Three legal edits follow.

A. Insert '-' before i in the condition, producing -i<n. Body values are 0,−1,…,−19. At −20 the condition 20<20 fails, after twenty prints.

B. Replace '<' with '+', producing i+n. The condition takes values 20,19,…,1 for the twenty iterations, then zero. A condition need not itself return only zero or one.

C. Replace i in --i with n, producing --n. i remains zero while n takes 20,…,1 in the body. When n becomes zero, 0<0 fails. These executions are finite without overflow. Only C consumes n. Replacing -- with ++ takes two character substitutions and fails the edit budget.

```c
/* C11. Each loop starts with fresh int i and n=20. */
#include <stdio.h>

int main(void) {
    int i, n = 20;
    for (i = 0; -i < n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i + n; --i) { printf("-"); }
    putchar('\n');
    n = 20;
    for (i = 0; i < n; --n) { printf("-"); }
    putchar('\n');
    return 0;
}
```

### Assumptions

C11 signed int variables, with n reset to twenty before every run.

### Edge case

Reset n to twenty each time. Unsigned declarations change the original arithmetic analysis.

### Common mistake

A version using two edits fails the contract even if its output has twenty hyphens. A for condition need not be a comparison.

### Cost

Twenty iterations per version and O(1) extra storage.

### Verification

Compiled C output was checked as three lines of exactly twenty hyphens each.

### Interview answer

Use -i<n, i+n, or --n as three separate one-character edits.

### Follow-up

Which versions preserve n? The first two. The third consumes it.

[checks/check_nov15_software.py](../checks/check_nov15_software.py)

[checks/prep-335-1115-verification.json](../checks/prep-335-1115-verification.json)

[solutions/prep_335_twenty_hyphens.c](../solutions/prep_335_twenty_hyphens.c)
