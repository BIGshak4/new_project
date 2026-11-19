# PREP-316 — איזו חזקה גדולה יותר?

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-14-batch30-23.png)

מה יותר גדול בלי שימוש במחשבון: 16 בחזקת 18 או 18 בחזקת 16

## איזו חזקה גדולה יותר?

השוו בלי מחשבון בין 16¹⁸ ל־18¹⁶. הציגו נימוק מדויק בלי לחשב את שתי החזקות במלואן.

### רמזים

1. אפשר להשוות בסיסים חיוביים אם כותבים את שני המספרים באותה חזקה חיצונית.
2. שני המעריכים זוגיים. אפשר גם לכתוב 16 כחזקה של 2.
3. כתבו 16¹⁸ בתור 2⁷². איזו חזקה שמינית נותנת כל אחד מהמספרים?

### פתרון מוצע

נכתוב 16=2⁴, ולכן 16¹⁸=2⁷²=(2⁹)⁸=512⁸. במקביל 18¹⁶=(18²)⁸=324⁸. מאחר ש־512>324, והעלאה בחזקה שמינית שומרת על סדר בין מספרים חיוביים, מתקבל 16¹⁸>18¹⁶.

החזקה החיצונית המשותפת מאפשרת להחליף השוואה בין שני מספרים גדולים בהשוואה בין שני מספרים תלת־ספרתיים בלבד.

### הנחות

מותר להשתמש בזהויות חזקות של מספרים שלמים חיוביים.

### מקרה קצה

חשוב שהבסיסים אחרי הפירוק חיוביים. למשל, העלאה בחזקה זוגית אינה שומרת סדר בכל הישר הממשי.

### טעות נפוצה

השוואת המעריכים בלבד או הבסיסים בלבד אינה מכריעה כששניהם משתנים.

### סיבוכיות או עלות

מספר קבוע של פעולות חשבון מדויקות לנתונים המבוקשים.

### בדיקות

חשבון שלמים מדויק מאמת את שתי הזהויות ואת כיוון האי־שוויון.

### תשובה קצרה

אלה 512 ו־324 בחזקה שמינית, ולכן 16¹⁸ גדולה יותר.

### שאלת המשך

כיצד תשוו באותה דרך 8⁶ ו־6⁸? שתיהן ריבועים: השוו 8³=512 עם 6⁴=1296. הפעם 6⁸ גדולה יותר.

## Which power is larger?

Compare 16¹⁸ and 18¹⁶ without a calculator. Give an exact argument without evaluating the two full powers.

### Hints

1. Can you express both numbers as positive bases raised to one common outer power?
2. Both exponents are even. Also write 16 as a power of two.
3. Write 16¹⁸ as 2⁷². Which eighth power represents each number?

### Proposed solution

Since 16=2⁴, we have 16¹⁸=2⁷²=(2⁹)⁸=512⁸. Also 18¹⁶=(18²)⁸=324⁸. Because 512>324 and the eighth power preserves order on positive numbers, 16¹⁸>18¹⁶.

The common outer exponent reduces the comparison to two three-digit integers.

### Assumptions

Use exponent identities for positive integers.

### Edge case

Positivity matters: raising to an even power does not preserve order over the entire real line.

### Common mistake

Comparing only the bases or only the exponents ignores that both change.

### Cost

A constant number of exact arithmetic operations for this specific instance.

### Verification

Exact integer arithmetic verifies both identities and the final inequality.

### Interview answer

They are the eighth powers of 512 and 324, so 16¹⁸ is larger.

### Follow-up

Can you compare 8⁶ and 6⁸ in the same way? Both are squares. Compare 8³=512 with 6⁴=1296, giving 6⁸ as the larger one.

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-316-1114-verification.json](../checks/prep-316-1114-verification.json)
