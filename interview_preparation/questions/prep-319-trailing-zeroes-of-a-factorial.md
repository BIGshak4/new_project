# PREP-319 — כמה אפסים מסיימים את 100! ואת 200!?

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-14-batch30-28.png)

א. כמה אפסים יש ב־100!? ב. וב־200!?

## כמה אפסים מסיימים את 100! ואת 200!?

בלי לחשב את העצרת עצמה, מצאו כמה אפסים רצופים מופיעים בסוף הכתיב העשרוני של 100! ושל 200!. הסבירו כיצד לחשב את התשובה עבור כל מספר שלם n≥0.

### רמזים

1. מה תורם אפס אחד בסוף מספר עשרוני?
2. כל גורם 10 מורכב מ־2 ומ־5. איזה מהם נדיר יותר בעצרת?
3. כל כפולה של 25 תורמת גורם 5 נוסף שכבר לא נספר בספירת הכפולות של 5. ומה תורמת כפולה של 125?

### פתרון מוצע

מספר האפסים בסוף הוא מספר הזוגות 2·5 שאפשר להוציא מהמכפלה. בעצרת יש לפחות גורמי 2 כמספר גורמי 5: לכל k≥1 יש לפחות אותו מספר כפולות של 2ᵏ כמו כפולות של 5ᵏ. לכן די לספור את כל גורמי 5.

כל כפולה של 5 תורמת לפחות אחד, כל כפולה של 25 תורמת עוד אחד, וכל כפולה של 125 מוסיפה עוד אחד, וכן הלאה. לכן Z(n)=⌊n/5⌋+⌊n/25⌋+⌊n/125⌋+… עד שהמנה אפס. מתקבל Z(100)=20+4=24 ו־Z(200)=40+8+1=49. במימוש מחלקים את n שוב ושוב בחמש בחלוקה שלמה ומחברים את המנות; אין צורך ליצור את n! או להעלות את 5 בחזקות עולות.

```python
def trailing_zeroes(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    zeros = 0
    while n >= 5:
        n //= 5
        zeros += n
    return zeros
```

### הנחות

בסיס 10; סופרים רק אפסים רצופים בקצה הימני.

### מקרה קצה

0!=1 ולכן אין אפסים בסוף. גם עבור n<5 התוצאה אפס.

### טעות נפוצה

ספירת כפולות של חמש בלבד מחמיצה את הגורמים הנוספים בכל כפולה של 25 ושל חזקות גבוהות יותר.

### סיבוכיות או עלות

O(log₅(n+1)) חלוקות שלמות ומספר קבוע של משתנים. עלות חלוקה תלויה בגודל המספר בחשבון ללא מגבלת רוחב.

### בדיקות

בדיקה מחשבת עצרות בגודל סופי וסופרת את האפסים ישירות בכתיב העשרוני, כולל בדיקת 24 ו־49.

### תשובה קצרה

אני סופר את גורמי החמש לפי שכבות. ל־100! יש 24 אפסים בסוף ול־200! יש 49.

### שאלת המשך

מה משתנה בבסיס 12? פרקו 12=2²·3. אם v₂ ו־v₃ הם מספרי הגורמים בעצרת, מספר האפסים הוא min(⌊v₂/2⌋,v₃).

## How many zeros end 100! and 200!?

Without evaluating the factorial itself, find the number of consecutive trailing decimal zeros in 100! and 200!. Explain how to compute it for any integer n≥0.

### Hints

1. What factor creates one trailing decimal zero?
2. Each 10 is a pair of factors 2 and 5. Which factor is scarcer in a factorial?
3. Each multiple of 25 contributes another 5 beyond the one counted among the multiples of five. What about multiples of 125?

### Proposed solution

The trailing zero count is the number of pairs 2·5 that can be taken out of the product. A factorial contains at least as many factors of two as factors of five: for every k≥1, there are at least as many multiples of 2ᵏ as of 5ᵏ. Count all factors of five.

Every multiple of 5 contributes at least one, every multiple of 25 contributes one more, every multiple of 125 contributes yet another, and so on. Thus Z(n)=⌊n/5⌋+⌊n/25⌋+⌊n/125⌋+… until the quotient is zero. Z(100)=20+4=24 and Z(200)=40+8+1=49. Repeatedly divide n by five with integer division and sum the quotients. Neither n! nor growing powers of five need to be constructed.

```python
def trailing_zeroes(n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    zeros = 0
    while n >= 5:
        n //= 5
        zeros += n
    return zeros
```

### Assumptions

Use base ten and count only consecutive zeros at the right-hand end.

### Edge case

0!=1 has no trailing zeros. All n<5 also give zero.

### Common mistake

Counting multiples of five just once misses extra factors from multiples of 25 and higher powers.

### Cost

O(log₅(n+1)) integer divisions and a constant number of variables. Unbounded-integer division cost depends on operand width.

### Verification

A finite check evaluates factorials and directly counts ending characters in their decimal notation, including 24 and 49.

### Interview answer

I count factors of five in layers. There are 24 trailing zeros in 100! and 49 in 200!.

### Follow-up

How would the answer change in base 12? Factor 12=2²·3. If v₂ and v₃ count those prime factors in the factorial, the result is min(⌊v₂/2⌋,v₃).

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-319-1114-verification.json](../checks/prep-319-1114-verification.json)

[solutions/prep_319_factorial_zeroes.py](../solutions/prep_319_factorial_zeroes.py)
