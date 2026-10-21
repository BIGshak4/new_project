# PREP-080 — ספירת ראשוניים עד n בעזרת נפת ארטוסתנס / Count primes up to n with the Sieve of Eratosthenes

מקור שנמסר ב־21.10.2026. פתרון מוצע בסיוע AI; סקירה מקצועית, תרגום וזכויות שימוש ממתינים.

Source supplied 2026-10-21. AI-assisted proposed solution; professional, translation and reuse reviews pending.

[צילום מקור / Original screenshot](../sources/prep-080-source.png)

## הנוסח המקורי / Original text

כתוב קוד כמה שיותר יעיל, שמקבל מספר שלם וקובע כמה מספרים ראשוניים קיימים מ1 עד n.

## עברית

### ספירת ראשוניים עד n בעזרת נפת ארטוסתנס

כתבו פונקציה יעילה שמקבלת מספר שלם אי־שלילי n ומחזירה כמה מספרים ראשוניים יש בתחום 1..n, כולל n. מספר ראשוני הוא שלם גדול מ־1 שמתחלק רק ב־1 ובעצמו. עבור n<2 מחזירים 0.

הסבירו איך נמנעים מבדיקת כל מחלק לכל מספר, מדוע מותר להתחיל לסמן מכפולות ב־p², ומה סיבוכיות הזמן והמקום. הבהרות שנוספו בעריכה: מבוקשת ספירה, לא בדיקת ראשוניות של n בלבד; מותר מערך עזר כאשר הוא נכנס בזיכרון. אין דרישה לאלגוריתם המהיר ביותר לכל גודל n או לחשבון מקורב.

### שלושה רמזים

1. במקום לבדוק כל מספר מחדש, אפשר לזכור אילו מספרים כבר ידוע שאינם ראשוניים.

2. כאשר p טרם נפסל, סמנו את כל הכפולות שלו. איזו כפולה ראשונה עדיין יכולה להיות חדשה?

3. לכל פריק יש מחלק ראשוני שאינו גדול מהשורש שלו. סמנו p*p,p*p+p,... ורק עבור p שעדיין מסומן כראשוני.

## הצעה לפתרון

### עוברים מבדיקות חוזרות לסימון משותף

בדיקת כל מספר k באמצעות מחלקים עד √k היא התחלה נכונה, אבל חוזרת שוב ושוב על אותה עבודה. בנפה שומרים byte לכל מספר: בהתחלה 2..n הם מועמדים. 0 ו־1 אינם ראשוניים, ולכן מאפסים אותם. כשמגיעים למועמד p שעדיין מסומן, הוא ראשוני; מסמנים את מכפלותיו כפריקות.

### למה מתחילים ב־p² ועוצרים ב־√n?

מכפלה p*k שבה 2≤k<p כבר נפסלה בגלל מחלק ראשוני של k, שהוא קטן מ־p. לכן המכפלה הראשונה שיכולה להוסיף מידע היא p*p. אם m פריק, אפשר לכתוב m=u*v עם 2≤u≤v, ולכן u≤√m. ל־u יש מחלק ראשוני שאינו גדול ממנו. מכאן שכל פריק עד n ייפסל עד שמסיימים לטפל ב־p≤√n. שימוש ב־isqrt נותן שורש שלם מדויק בלי עיגול של float.

### מימוש פייתון

```python
"""Count primes in the inclusive interval [1,n] with Eratosthenes' sieve."""

from math import isqrt


def count_primes(n: int) -> int:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if n < 2:
        return 0
    prime = bytearray(b"\x01") * (n + 1)
    prime[0] = prime[1] = 0
    for p in range(2, isqrt(n) + 1):
        if prime[p]:
            for multiple in range(p * p, n + 1, p):
                prime[multiple] = 0
    return sum(prime)

```

בדוגמה n=10 מאפסים 0,1. עבור p=2 מסמנים 4,6,8,10; עבור p=3 מסמנים 9. נותרו 2,3,5,7 ולכן התוצאה 4. כאשר n=2 מוחזר 1; כאשר n=1 מוחזר 0. זהו תחום כולל: n ראשוני עצמו נספר.

### נכונות

לא נמחק ראשוני: כל מספר שסומן הוא מכפלה p*k כאשר k≥p≥2, ולכן פריק. כל פריק נמחק: בחרו את המחלק הראשוני הקטן ביותר p שלו. מתקיים p≤√m≤√n ו־m≥p²; כשהנפה מטפלת ב־p היא מגיעה ל־m. לכן בסיום מסומנים בדיוק הראשוניים, וסכום הבתים הוא מספרם.

### עלות והיקף המילה ״יעיל״

אתחול וספירה עולים O(n). סימון הכפולות עולה O(n log log n) פעולות במודל גישה למערך וחשבון בגודל מילה; סיבוכיות הנפה הכוללת היא O(n log log n), עם O(n) בתים לאחסון bytearray. כל תא כאן הוא בית, לא ביט אחד. בנפה דחוסה אפשר להגיע לכ־n ביטים, אך זה אינו המימוש שסופק. אינדקסים ולולאות מוסיפים רק מספר קבוע של משתני עבודה; אין מערך נוסף באורך n, וגם אין השמת slice שמייצרת זמנית רצף גדול.

אין לטעון שהנפה היא תמיד האלגוריתם המהיר ביותר לספירת ראשוניים: עבור n עצום יש שיטות ספירה מתקדמות, ועבור מגבלת זיכרון יש נפה במקטעים. כאן זהו פתרון מדויק, מקובל וברור לתחום שמערך בגודלו נכנס בזיכרון. הקצאה עלולה להיכשל אם n גדול מדי.

הקוד הושווה לאורקל עצמאי המבצע חילוק בניסיון לכל n מ־0 עד 2000, כולל גבולות וריבועי ראשוניים. נוספו נקודות בדיקה π(10)=4, π(100)=25, π(1000)=168, π(10000)=1229, π(100000)=9592, וחמש דחיות קלט לא תקין. אלו בדיקות דטרמיניסטיות סופיות; לא מבחן ביצועים או אישור אנושי.


### הנחות

- n שלם אי־שלילי מדויק; bool אינו קלט מספרי תקין; סופרים בתחום כולל 1..n.
- מערך של n+1 בתים מותר כשהוא נכנס בזיכרון; הפונקציה אינה משנה קלט.
- ניתוח הזמן משתמש במודל חשבון אינדקסים בגודל מילה וגישה קבועה למערך.

### נכונות ועלות

**criterion**: זמן ומקום של נפת ארטוסתנס המסופקת.

**result**: O(n log log n) פעולות; O(n) בתים.

**proof**: עבודה ליניארית לאתחול וספירה, ועוד סימון כפולות של ראשוניים בלבד החל בריבועיהם. כל פריק נפסל דרך מחלק ראשוני עד השורש שלו.

**scope**: זו אינה טענת מינימום גלובלי לספירת ראשוניים או זמן מעשי עבור כל n.

### אימות

עברו כל 2001 גבולות התחום 0..2000 מול חילוק בניסיון עצמאי, חמש נקודות ספירה ידועות עד 100000 וחמש דחיות קלט. הקוד רץ בפייתון. אין מדידת ביצועים או סקירה אנושית.

### מקרי קצה

- n=0 או 1: 0; n=2: 1.
- ראשוני בקצה התחום נספר; ריבוע של ראשוני מסומן כפריק.
- n שלילי או לא שלם נדחה; n גדול מדי עלול לא להיכנס בזיכרון.

### טעויות נפוצות

- לספור את 1 כראשוני או להשתמש בתחום לא כולל n.
- להתחיל סימון ב־p עצמו ולמחוק ראשוני.
- להפעיל סימון מחדש גם עבור p שכבר פריק.
- לטעון bytearray צורך ביט אחד לתא או שהנפה היא תמיד המהירה ביותר.

### תשובה קצרה לראיון

אצור דגלים ל־0..n, אאפס את 0 ו־1, ולכל p שעדיין ראשוני עד √n אסמן מכפולות החל מ־p². כל פריק מחזיק מחלק ראשוני עד השורש ולכן יימחק, ואף ראשוני לא יימחק. אסכם את הדגלים: O(n log log n) זמן ו־O(n) בתים במימוש הזה.

### שאלת המשך

**question**: איך סופרים ראשוניים עד n כשמערך בגודל n אינו נכנס לזיכרון?

**direction**: הפיקו ראשוניים עד √n ואז עבדו בנפה במקטעים [L,R]. לכל p סמנו החל מ־max(p²,ceil(L/p)*p). סכמו בלי לשמור את כל הראשוניים; הגבילו את גודל המקטע וסמנו נכון 0 ו־1.

**status**: מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי.

## English

### Count primes up to n with the Sieve of Eratosthenes

Write an efficient function taking a nonnegative integer n and returning the number of primes in the inclusive interval 1..n. A prime is an integer greater than one divisible only by one and itself. Return zero for n<2.

Explain how to avoid testing every divisor for every number, why marking may start at p², and the time/space costs. Editorial clarifications: count all primes through n, rather than only testing n; an auxiliary array is allowed when it fits memory. No claim of the globally fastest algorithm for every n or an approximate answer is required.

### Three hints

1. Rather than rechecking every number from scratch, remember numbers already known to be composite.

2. When p has not been ruled out, mark its multiples. Which is the first multiple that can still be new?

3. Every composite has a prime divisor no larger than its square root. Mark p*p,p*p+p,... only for p still flagged prime.

## Proposed solution

### Share work by marking composites

Testing each k by trial divisors through √k is a valid starting point, but repeats work. A sieve keeps one byte per number. Initially 2..n are candidates; clear zero and one because neither is prime. When a candidate p remains flagged, it is prime, so clear its composite multiples.

### Why start at p² and stop at √n?

A multiple p*k with 2≤k<p has already been cleared by a prime divisor of k smaller than p. Thus p*p is the first multiple that may add information. A composite m=u*v with 2≤u≤v has u≤√m; u has a prime divisor no larger than u. Therefore every composite through n is cleared after processing p≤√n. isqrt computes an exact integer square root without floating-point rounding.

### Python implementation

```python
"""Count primes in the inclusive interval [1,n] with Eratosthenes' sieve."""

from math import isqrt


def count_primes(n: int) -> int:
    if type(n) is not int or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if n < 2:
        return 0
    prime = bytearray(b"\x01") * (n + 1)
    prime[0] = prime[1] = 0
    for p in range(2, isqrt(n) + 1):
        if prime[p]:
            for multiple in range(p * p, n + 1, p):
                prime[multiple] = 0
    return sum(prime)

```

For n=10, clear zero and one. At p=2 mark 4,6,8,10; at p=3 mark nine. Flags remain for 2,3,5,7, so return four. n=2 returns one; n=1 returns zero. The upper endpoint is inclusive, so prime n itself counts.

### Correctness

No prime is removed: every cleared number is p*k with k≥p≥2 and is composite. Every composite is removed: take its smallest prime divisor p. Then p≤√m≤√n and m≥p², so the marking loop for p visits m. Exactly the primes remain; summing the bytes counts them.

### Cost and the scope of efficiency

Initialization and counting cost O(n). Marking multiples takes O(n log log n) operations in a word-size arithmetic and random-access array model, giving O(n log log n) total time and O(n) bytes for this bytearray. A flag here uses one byte, not one bit. A packed implementation can approach n bits, but that is not this code. Loop/index variables are constant in number; there is no second length-n array or large temporary slice-assignment buffer.

Do not claim the sieve is always the fastest way to count primes. Very large n admits more advanced counting algorithms; memory constraints can motivate a segmented sieve. This is an exact standard solution for a range whose array fits memory. Allocation may fail when n is too large.

Executed checks compare every endpoint 0..2000 with independent trial division, including boundaries and prime squares. Additional checkpoints are π(10)=4, π(100)=25, π(1000)=168, π(10000)=1229, π(100000)=9592, plus five invalid-input rejections. These are finite deterministic correctness tests, not a performance benchmark or human approval.


### Assumptions

- n is an exact nonnegative integer; bool is rejected; count the inclusive interval 1..n.
- A byte array of n+1 entries is allowed when it fits memory; input is not mutated.
- Time analysis uses word-sized index arithmetic and constant-time array access.

### Correctness and cost

**criterion**: Time and storage of the supplied Eratosthenes implementation.

**result**: O(n log log n) operations and O(n) bytes.

**proof**: Linear initialization/counting plus marking multiples of primes starting at their squares. Each composite is cleared by a prime divisor through its square root.

**scope**: Not a global lower-bound/fastest-prime-counting claim or a practical runtime promise for every n.

### Verification

All 2001 endpoints 0..2000 matched independent trial division, plus five prime-count checkpoints through 100000 and five invalid-input rejections. Python executed; no performance benchmark or human review.

### Edge cases

- n=0 or 1 returns zero; n=2 returns one.
- A prime endpoint is counted; a prime square is marked composite.
- Negative/noninteger n is rejected; a huge n may exceed available memory.

### Common mistakes

- Counting one as prime or excluding endpoint n.
- Starting at p itself and deleting a prime.
- Repeating marking for already-composite p.
- Claiming bytearray stores one bit per entry or that this sieve is always fastest.

### Short interview answer

Flag 0..n, clear zero and one, and for each still-prime p through √n clear multiples starting at p². Every composite has a prime divisor through its square root, and no prime is removed. Sum flags: O(n log log n) time and O(n) bytes in this implementation.

### Follow-up

**question**: How can primes through n be counted when an n-sized array does not fit memory?

**direction**: Generate base primes through √n, then sieve segments [L,R]. For each p mark from max(p²,ceil(L/p)*p). Accumulate counts without retaining all primes; choose a bounded segment and handle zero/one correctly.

**status**: Prepared as content; not connected to the interactive follow-up queue.

## קבצים ואימות / Files and checks

- [קוד / Code: prep_080_count_primes_sieve.py](../solutions/prep_080_count_primes_sieve.py)

- [בדיקה ניתנת להרצה / Executable check](../checks/check_prep_080.py)

- [תוצאת הבדיקה / Check evidence](../checks/prep-080-verification.json)

שאלת ההמשך מוכנה בתוכן בלבד ואינה מחוברת לתור המשך אינטראקטיבי.

The follow-up is prepared as content only; it is not connected to the interactive follow-up queue.
