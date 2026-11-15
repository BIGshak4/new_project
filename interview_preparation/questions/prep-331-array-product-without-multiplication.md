# PREP-331 — מכפלת מערך ב־C בלי אופרטור כפל

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-15-batch20-04.png)

לכתוב פונקציה ב־C שמקבלת מערך של מספרים חיוביים ומוציאה את תוצאת המכפלה ללא פעולת כפל, ולהתאים למספרים שאינם בהכרח חיוביים.

## מכפלת מערך ב־C בלי אופרטור כפל

ממשו ב־C11 פונקציה המכפילה את איברי מערך מספרים חיוביים ללא שימוש באופרטור כפל חשבוני. לאחר מכן תמכו גם באפס ובשליליים. בחוזה המלא האיברים הם int32_t והפלט int64_t. החזירו false אם התוצאה אינה ניתנת לייצוג או אם מצביע נדרש הוא NULL. בכשל אל תשנו את פלט הלקוח. גודל המערך ידוע והמצביע מצביע לאחסון קריא בגודל זה. המכפלה הריקה היא 1. עבור [1,2,3,4,5] נקבל 120. מותר להשתמש בחיבור, חיסור, פעולות ביטים ובדיקות. אין להשתמש בכפל או בחילוק כדי לחשב את המכפלה.

### רמזים

1. אפשר לחבר מספר שוב ושוב, אבל איזו משמעות יש לכל ביט במכפיל?
2. סרקו את ביטי הגודל החיובי של המכפיל. ביט דלוק בוחר כפולה שהיא חזקה של שתיים.
3. קבעו מראש את סימן המכפלה ובדקו אפס. צברו גדלים unsigned בגבול המתאים לסימן, ובדקו כל חיבור באמצעות limit−sum.

### פתרון מוצע

חיבור חוזר נותן פתרון בסיסי אך תלוי בערך המכפיל. פירוקו לביטים נותן כפל באמצעות חיבור והכפלה בשתיים בלבד. בכל סבב bit 0 בוחר אם להוסיף את a לסכום, מזיזים את b ימינה, ואם נשארו ביטים מכפילים את a בשתיים בחיבור a+a. האינווריאנט הוא sum+a·b שווה למכפלה המבוקשת; הכפל בנוסחה משמש להוכחה בלבד.

במעבר מקדים נזהה אפס ואת זוגיות מספר השליליים. אפס קובע תוצאה 0 גם כשקידומת לא־אפס הייתה גולשת. אחר כך נכפיל גדלים חיוביים בלבד. הרחבה ל־int64_t לפני שלילת int32_t מאפשרת לטפל ב־INT32_MIN. הגבול למכפלה חיובית הוא INT64_MAX, ולשלילית מותר גודל 2^63. לפני הוספה נדרוש a≤limit−sum; לפני הכפלה בשתיים נדרוש a≤limit−a. אין להשתמש ב־abs על INT32_MIN בטיפוס int32_t. אם המכפלה השלילית בגודל 2^63 נחזיר את INT64_MIN במפורש.

ללא אפס כל הגורמים בגודל לפחות 1, ולכן קידומת שכבר חורגת מהגבול לא יכולה להצטמצם בהמשך. המימוש שומר את *out רק לאחר הצלחה. בזמן O(nW), כאשר W=32 עבור המכפיל, ובמקום O(1), מתקבל הפלט המדויק או דיווח גלישה. בטיפוסים קבועי רוחב זהו זמן לינארי באורך המערך.

```c
/* C11. Readable int32_t array, count known. No arithmetic multiplication. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <limits.h>

static bool add_shift_product(uint64_t a, uint64_t b, uint64_t limit, uint64_t *out) {
    uint64_t sum = 0;
    while (b != 0) {
        if ((b & UINT64_C(1)) != 0) {
            if (a > limit - sum) return false;
            sum += a;
        }
        b >>= 1;
        if (b != 0) {
            if (a > limit - a) return false;
            a += a;
        }
    }
    *out = sum;
    return true;
}

bool array_product(const int32_t *values, size_t count, int64_t *out) {
    if (out == NULL || (count != 0 && values == NULL)) return false;
    bool negative = false;
    bool has_zero = false;
    for (size_t i = 0; i < count; ++i) {
        if (values[i] == 0) has_zero = true;
        if (values[i] < 0) negative = !negative;
    }
    if (has_zero) { *out = 0; return true; }
    uint64_t limit = negative ? (UINT64_C(1) << 63) : (uint64_t)INT64_MAX;
    uint64_t result = 1;
    for (size_t i = 0; i < count; ++i) {
        int64_t x = values[i];
        uint64_t magnitude = x < 0 ? (uint64_t)(-x) : (uint64_t)x;
        if (!add_shift_product(result, magnitude, limit, &result)) return false;
    }
    if (!negative) *out = (int64_t)result;
    else if (result == (UINT64_C(1) << 63)) *out = INT64_MIN;
    else *out = -(int64_t)result;
    return true;
}
```

### הנחות

int32_t, int64_t ו־uint64_t קיימים. האחסון תקף והגודל ידוע.

### מקרה קצה

[] נותן 1. [INT32_MIN,−1] ניתן לייצוג ב־int64_t. גם אפס אחרי קידומת גדולה מחייב להחזיר 0.

### טעות נפוצה

גלישה של signed int היא התנהגות לא מוגדרת. מעבר ל־unsigned לבדו מספק שארית מודולרית, שאינה המכפלה המדויקת שנדרשה.

### סיבוכיות או עלות

O(nW) זמן ו־O(1) מקום עזר עבור רוחב קבוע. אין טענת אופטימליות של מספר פעולות הביטים.

### בדיקות

המימוש קומפל והושווה למכפלת שלמים בלתי חסומים, כולל אפס, סימנים וגבולות טיפוס.

### תשובה קצרה

אחשב סימן ואפס תחילה, ואז אכפיל גדלים ב־shift-and-add עם בדיקת גבול לפני כל חיבור.

### שאלת המשך

איך תפיקו מכפלה מודולרית במילה unsigned? בחרו חוזה מודולו 2^W ותנו לחיבור unsigned להצטמצם בהתאם; זה משנה את משמעות הפלט.

## C array product without arithmetic multiplication

Implement a C11 function returning the product of positive array entries without arithmetic multiplication. Extend it to zero and negative entries. In the complete contract inputs are int32_t and output is int64_t. Return false on overflow or a required NULL pointer, leaving the output unchanged on failure. The known-size array must refer to readable live storage. The empty product is one. [1,2,3,4,5] gives 120. Addition, subtraction, bit operations and comparisons are allowed. Do not use multiplication or division to calculate the product.

### Hints

1. Repeated addition works, but what does each multiplier bit represent?
2. Scan a nonnegative multiplier bit by bit. Each set bit selects a power-of-two multiple.
3. Determine sign and detect zero first, then accumulate unsigned magnitudes with a sign-dependent limit and pre-addition overflow checks.

### Proposed solution

Repeated addition is a basic solution whose time depends on the multiplier value. Binary decomposition replaces it with shifts and addition. When b's low bit is set, add a to sum. Shift b right and double a by a+a only if another bit remains. The proof invariant sum+a·b equals the desired product; multiplication in that equation is only mathematical notation.

First scan for zero and the parity of negative entries. Zero determines an exact zero result even when a nonzero prefix would overflow. Otherwise multiply magnitudes. Widen int32_t into int64_t before negation, making INT32_MIN safe. A positive result is bounded by INT64_MAX, while a negative result permits magnitude 2^63. Before adding require a≤limit−sum; before doubling require a≤limit−a. Handle negative magnitude 2^63 by returning INT64_MIN explicitly.

Without zero, every magnitude is at least one, so an already overflowing prefix cannot shrink later. Commit *out only on success. The method costs O(nW) time, with W=32 multiplier bits, and O(1) extra memory. Fixed machine widths make this linear in array length.

```c
/* C11. Readable int32_t array, count known. No arithmetic multiplication. */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <limits.h>

static bool add_shift_product(uint64_t a, uint64_t b, uint64_t limit, uint64_t *out) {
    uint64_t sum = 0;
    while (b != 0) {
        if ((b & UINT64_C(1)) != 0) {
            if (a > limit - sum) return false;
            sum += a;
        }
        b >>= 1;
        if (b != 0) {
            if (a > limit - a) return false;
            a += a;
        }
    }
    *out = sum;
    return true;
}

bool array_product(const int32_t *values, size_t count, int64_t *out) {
    if (out == NULL || (count != 0 && values == NULL)) return false;
    bool negative = false;
    bool has_zero = false;
    for (size_t i = 0; i < count; ++i) {
        if (values[i] == 0) has_zero = true;
        if (values[i] < 0) negative = !negative;
    }
    if (has_zero) { *out = 0; return true; }
    uint64_t limit = negative ? (UINT64_C(1) << 63) : (uint64_t)INT64_MAX;
    uint64_t result = 1;
    for (size_t i = 0; i < count; ++i) {
        int64_t x = values[i];
        uint64_t magnitude = x < 0 ? (uint64_t)(-x) : (uint64_t)x;
        if (!add_shift_product(result, magnitude, limit, &result)) return false;
    }
    if (!negative) *out = (int64_t)result;
    else if (result == (UINT64_C(1) << 63)) *out = INT64_MIN;
    else *out = -(int64_t)result;
    return true;
}
```

### Assumptions

int32_t, int64_t and uint64_t exist; the declared storage extent is valid.

### Edge case

[] gives one. [INT32_MIN,−1] fits int64_t. Zero after a large prefix must still return zero.

### Common mistake

Signed overflow is undefined. Unsigned wrap alone computes a modular result and does not report an exact overflowing product.

### Cost

O(nW) time and O(1) auxiliary space, with fixed operand width. No minimum-bit-operation claim.

### Verification

Compiled C was compared with unbounded-integer multiplication, including zero, sign combinations and type boundaries.

### Interview answer

Determine sign and zero first, then use bounded shift-and-add multiplication of magnitudes.

### Follow-up

How would a fixed-width modular product differ? Choose output modulo 2^W and use unsigned arithmetic with its defined wrap behavior.

[checks/check_nov15_software.py](../checks/check_nov15_software.py)

[checks/prep-331-1115-verification.json](../checks/prep-331-1115-verification.json)

[solutions/prep_331_product_without_multiply.c](../solutions/prep_331_product_without_multiply.c)
