# PREP-077 — החלפת שני מספרים ללא משתנה עזר — גם ב־8 ביט / Swap two numbers without a temporary — including 8-bit values

מקור שנמסר ב־21.10.2026. פתרון מוצע בסיוע AI; סקירה מקצועית, תרגום וזכויות שימוש ממתינים.

Source supplied 2026-10-21. AI-assisted proposed solution; professional, translation and reuse reviews pending.

[צילום מקור / Original screenshot](../sources/prep-077-source.png)

## הנוסח המקורי / Original text

א.נתונים 2 מספרים a, b. כתוב תוכנית המחליפה בין ערכיהם ללא שימוש במשתנה עזר.
ב. כעת ידוע כי גודל שני המספרים הוא 8 ביט כל אחד, לכן פעולת חיבור או חיסור יכולות לגרום לגלישה. ממש כעת את ההחלפה של ערכם.

## עברית

### החלפת שני מספרים ללא משתנה עזר — גם ב־8 ביט

א. נתונים שני משתני מספר שלם a ו־b. החליפו את ערכיהם בלי משתנה עזר המחזיק אחד מערכי הקלט. התחילו בחשבון שלמים מדויק ללא מגבלת רוחב.

ב. כעת a ו־b הם שני תאי אחסון נפרדים של 8 ביט ללא סימן, 0–255. מותרות פעולות ביטים; פעולות חשבון מחזירות ערך מודולו 256 בעת ההשמה לתא. הציגו פתרון שאינו תלוי בנשיאה, והסבירו האם גלישה מונעת בהכרח פתרון של חיבור וחיסור.

הבהרות שנוספו בעריכה: יש לשמור בדיוק את שתי תבניות הביטים המקוריות בהחלפה. אם הממשק משתמש בהפניות שעלולות להצביע לאותו תא, ההחלפה עם עצמו צריכה להשאירו ללא שינוי. אין להשתמש בטריק החלפה מובנה המסתיר משתנה עזר. הבדילו בין שלמים מדויקים, גלישה מודולרית מוגדרת וגלישת מספר signed בשפה שבה היא אינה מוגדרת.

### שלושה רמזים

1. אפשר לשנות את שני התאים כמה פעמים. איזה מידע על הזוג מאפשר לשחזר כל אחד מן הערכים?

2. בחשבון מדויק אפשר לשמור סכום באחד התאים. בפעולות ביטים חפשו פעולה שבה x עם עצמו מתבטל.

3. עבור XOR השתמשו בזהות (x XOR y) XOR y=x. אחרי כל השמה כתבו את ערך התא בסימנים x,y המקוריים; בדקו בנפרד הפניות לאותו תא.

## הצעה לפתרון

### קודם מגדירים מה פירוש ״ללא משתנה עזר״

הכוונה היא שאין תא שלישי לשמירת אחד מערכי הקלט. המעבד עדיין עשוי להשתמש ברגיסטרים זמניים למימוש פקודה; זו אינה דרישה לארכיטקטורת מעבד ללא משאבים פנימיים. a ו־b הם משתנים נפרדים, או שהממשק בודק שזהות כתובתם שונה. בקוד אמיתי החלפה רגילה באמצעות משתנה זמני בדרך כלל ברורה יותר.

### סעיף א: חיבור וחיסור בחשבון מדויק

```text
a = a + b
b = a - b
a = a - b
```

נסמן את הערכים המקוריים x,y. אחרי השורה הראשונה (a,b)=(x+y,y). אחרי השנייה (x+y,x), ואחרי השלישית (y,x). למשל 7,12 נעשים 19,12 ואז 19,7 ואז 12,7. בפייתון השלמים מדויקים, ולכן אותה הוכחה תקפה גם לערכים שליליים או גדולים מאוד. אין להסיק מכך שהביטוי a+b בטוח עבור signed int ב־C++.

### סעיף ב: שלוש פעולות XOR

```text
a = a XOR b
b = a XOR b
a = a XOR b
```

אחרי הצעד הראשון a=x XOR y. אחר כך b=(x XOR y) XOR y=x. לבסוף a=(x XOR y) XOR x=y. זהות x XOR x=0 יחד עם x XOR 0=x מוכיחה את התוצאה בכל ביט בנפרד. אין נשיאה או הרחבת רוחב. ערכים שווים הם מקרה חוקי: התא הראשון זמנית 0, אך הערכים משוחזרים כל עוד אלה שני תאים שונים.

### גם חיבור וחיסור מודולריים תקפים

המקור מזכיר גלישה אך אינו מגדיר טיפוס. ברכיבי 8 ביט ללא סימן עם wrap מודולו 256, החיבור/חיסור עדיין עובדים: a=(x+y) mod 256, אחר כך b=(a−y) mod 256=x, ולבסוף a=(a−x) mod 256=y. למשל 250,10 נעשים 4,10 ואז 4,250 ואז 10,250. לכן הטענה ״ב־8 ביט רק XOR עובד״ שגויה.

להלן C++ עם uint8_t כאשר הטיפוס זמין. בהמרות החשבון ל־int הסכום לכל היותר 510 וההפרש לפחות ‎-255, ולכן הביניים נכנסים גם לטווח int המינימלי התקני. המרה מפורשת חזרה ל־uint8_t מגדירה את השארית מודולו 256. אין כאן הרצת signed overflow. המימוש סופק ולא קומפל בסביבת הבדיקה.

```cpp
#include <cstdint>
#include <memory>

// Distinct references or a same-location no-op. No auxiliary value variable.
void xor_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a ^= b;
    b ^= a;
    a ^= b;
}

// Integral promotions precede arithmetic; conversion back to uint8_t is modulo
// 256. Promoted addition is at most 510 and subtraction at least -255, so these
// intermediates fit even the minimum standard range of int.
void modular_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a = static_cast<std::uint8_t>(a + b);
    b = static_cast<std::uint8_t>(a - b);
    a = static_cast<std::uint8_t>(a - b);
}

```

### למה צריך בדיקת זהות כתובות?

אם a ו־b הן שתי הפניות לאותו תא, כבר a^=b מבצע x XOR x ומאפס את הערך המקורי. שוויון ערכים אינו זהות כתובת: שני תאים שונים שערכם 9 מותרים. בדיקת הכתובת הופכת החלפה עם עצמו לפעולת זהות, בלי לשמור משתנה עזר של ערך. אין לכתוב את שלוש ההשמות בביטוי משורשר שהסדר שלו תלוי בשפה.

### עלות ואימות

שלוש פעולות והשמות למילים ברוחב קבוע: O(1) זמן ומספר קבוע של תאים; אין טענת מינימום מוחלט של פקודות או מהירות מעבד. על מספרים בלתי חסומים עלות פעולה תלויה באורך הביטים. רצף XOR תוכנתי הוא שלוש השמות סדרתיות; אין לחבר משוב קומבינטורי כאילו כל שלוש המשוואות פועלות בו־זמנית.

נבדקו בפייתון כל 65,536 זוגות הבתים בכל ארבעת המודלים: XOR, חשבון מודולרי, חשבון מדויק ועדכון תאים נפרדים. כל 256 ההחלפות עם עצמו נבדקו עם guard, לצד דוגמת הכשל ללא guard. נבדקו גם ארבעה זוגות שלמים שליליים/גדולים. אלו מודלי קוד ובדיקה ממצה לתחום הבתים, לא קומפילציה של C++, בדיקת חומרה או אישור אנושי.


### הנחות

- בסעיף א שלמים מדויקים; בסעיף ב שני תאים נפרדים בני 8 ביט ללא סימן עם פעולות ביטים.
- החשבון המודולרי ממיר תוצאות מודולו 256 בעת ההשמה; אין להסתמך על signed overflow שאינו מוגדר.
- אין משתנה עזר לערך קלט; בדיקת זהות כתובות מותרת כדי להשאיר החלפה עם עצמו ללא שינוי.

### נכונות ועלות

**criterion**: עלות ברוחב מילה קבוע ללא תא עזר לערך.

**result**: שלוש פעולות והשמות, O(1) זמן ותאים קבועים.

**proof**: חוקי XOR או ביטול מודולרי משחזרים בסדר הפוך את x,y לאחר שלוש השמות.

**scope**: אין טענת מינימום פקודות או יתרון ביצועים; שלמים בלתי חסומים מוסיפים עלות אורך ביטים.

### אימות

עברו כל 65,536 זוגות הבתים בכל ארבעת המודלים, 256 מקרי alias עם guard וארבעה זוגות שלמים גדולים/שליליים. פייתון רץ; C++ סופק ולא קומפל. אין אימות חומרה או אישור אנושי.

### מקרי קצה

- 0 מול 255; סכום העולה על 255; שני תאים שווי ערך.
- שתי הפניות לאותו תא מחייבות no-op לפני רצף XOR.
- signed int עלול להיכנס לגלישה לא מוגדרת; Python מדויק אינו מוגבל ל־8 ביט.

### טעויות נפוצות

- לטעון שגלישה מודולרית מבטלת את הוכחת החיבור/חיסור.
- לבלבל ערכים שווים עם הפניות לאותו תא.
- להשתמש ב־tuple swap כאשר האילוץ אוסר משתנה עזר סמוי.
- לכתוב את שלוש ההשמות בבת אחת כמעגל קומבינטורי עם משוב.

### תשובה קצרה לראיון

בחשבון מדויק אפשר שלוש השמות חיבור/חיסור. ברוחב 8 ביט נוח לבצע a^=b; b^=a; a^=b: כל ביט מתבטל פעמיים. גם חיבור/חיסור מודולריים תקפים בטיפוס מתאים. אברר טיפוס וגלישה, ואגן מפני שתי הפניות לאותו תא.

### שאלת המשך

**question**: האם XOR swap בהכרח מהיר יותר מהחלפה רגילה באמצעות משתנה זמני?

**direction**: לא. יש תלות סדרתית בין שלוש הפעולות, והקומפיילר עשוי לייעל החלפה רגילה. יש למדוד על הארכיטקטורה ולהעדיף בהירות בלי מגבלה מלאכותית.

**status**: מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי.

## English

### Swap two numbers without a temporary — including 8-bit values

(a) Swap two integer variables a,b without an auxiliary variable holding an input value. Begin with exact unbounded integer arithmetic.

(b) Now a,b occupy distinct unsigned 8-bit storage locations, holding 0..255. Bitwise operations are allowed; arithmetic converts modulo 256 on assignment. Give a solution independent of carry, and explain whether overflow necessarily invalidates addition/subtraction swapping.

Editorial clarifications: preserve and exchange the exact original bit patterns. If references may alias one storage location, swapping a location with itself must leave it unchanged. Do not use a built-in swap hiding a temporary value. Distinguish exact arithmetic, defined modular wrap and signed overflow in languages where it is undefined.

### Three hints

1. You may overwrite both locations repeatedly. What information about the pair allows either original value to be recovered?

2. With exact arithmetic one location can hold the sum. For bitwise operations, look for an operation under which a value cancels itself.

3. For XOR use (x XOR y) XOR y=x. After every assignment express both locations in terms of the original x,y; handle same-location references separately.

## Proposed solution

### Define the no-temporary constraint

The restriction forbids a third location holding an input value. A processor may still use internal registers to implement an operation; the question does not prohibit such architectural resources. a,b are separate variables, or an interface checks address identity. An ordinary temporary-based swap is generally clearer in production code.

### Part (a): exact arithmetic

```text
a = a + b
b = a - b
a = a - b
```

Let x,y be the original values. The pairs after successive lines are (x+y,y), (x+y,x), (y,x). For example 7,12 become 19,12 then 19,7 then 12,7. Python's exact integers make the argument valid for negative or arbitrarily large values too. This does not imply that a+b is safe for signed int in C++.

### Part (b): three XOR updates

```text
a = a XOR b
b = a XOR b
a = a XOR b
```

After the first update a=x XOR y. Then b=(x XOR y) XOR y=x. Finally a=(x XOR y) XOR x=y. The identities x XOR x=0 and x XOR 0=x prove the result independently at every bit; no carry or widening is required. Equal values are valid: the first location temporarily becomes zero, but both originals are recovered if the locations are distinct.

### Modular addition/subtraction works as well

The source mentions overflow without naming a type. For unsigned 8-bit arithmetic wrapping modulo 256, add/subtract swapping remains valid: a=(x+y) mod 256, then b=(a−y) mod 256=x, then a=(a−x) mod 256=y. For 250,10 the pairs become 4,10 then 4,250 then 10,250. Thus claiming that only XOR can work at eight bits is incorrect.

The following C++ uses uint8_t where available. Integral promotions produce an int sum of at most 510 and a difference of at least -255, which fit even the standard minimum int range. Explicit conversion back to uint8_t defines modulo-256 reduction. No signed overflow is executed. The supplied C++ was not compiled in this environment.

```cpp
#include <cstdint>
#include <memory>

// Distinct references or a same-location no-op. No auxiliary value variable.
void xor_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a ^= b;
    b ^= a;
    a ^= b;
}

// Integral promotions precede arithmetic; conversion back to uint8_t is modulo
// 256. Promoted addition is at most 510 and subtraction at least -255, so these
// intermediates fit even the minimum standard range of int.
void modular_swap(std::uint8_t& a, std::uint8_t& b) {
    if (std::addressof(a) == std::addressof(b)) return;
    a = static_cast<std::uint8_t>(a + b);
    b = static_cast<std::uint8_t>(a - b);
    a = static_cast<std::uint8_t>(a - b);
}

```

### Why address identity matters

If both references denote one location, the first a^=b computes x XOR x and destroys the original value. Equal values are different from identical storage: two separate locations holding nine are valid. An address guard makes a self-swap a no-op without storing an auxiliary input value. Do not compress the three updates into a chained expression with language-dependent evaluation order.

### Cost and verification

Three fixed-width operations and assignments take O(1) time with a constant number of locations. This is not a proof of minimum instruction count or processor speed. Arbitrary-size integer operations also depend on bit length. These are sequential software assignments, not simultaneous combinational feedback equations.

Python checks covered every one of 65,536 byte pairs across four models: XOR, modular arithmetic, exact arithmetic and distinct-location updates. All 256 self-swaps were verified with the guard, and the unguarded destruction was exhibited. Four signed/large exact-integer pairs were checked too. These are executed models and exhaustive byte-domain tests, not C++ compilation, hardware verification or human approval.


### Assumptions

- Part (a) uses exact integers; part (b) uses two distinct unsigned 8-bit locations with bitwise operations.
- The modular variant reduces modulo 256 on assignment; it does not rely on undefined signed overflow.
- No auxiliary input-value variable; address identity may be checked to make a self-swap a no-op.

### Correctness and cost

**criterion**: Fixed-word cost without an auxiliary input-value location.

**result**: Three operations and assignments: O(1) time and constant storage.

**proof**: XOR cancellation or modular cancellation recovers x,y in exchanged order after three updates.

**scope**: No minimum-instruction or performance claim; unbounded integers incur bit-length costs.

### Verification

All 65,536 byte pairs passed across four models, plus 256 guarded alias cases and four large/signed exact-integer pairs. Python executed; C++ supplied but not compiled. No hardware or human approval.

### Edge cases

- Zero versus 255; sums above 255; equal values in distinct locations.
- Two aliases to one location require a no-op before the XOR sequence.
- Signed int may encounter undefined overflow; Python exact integers are not limited to eight bits.

### Common mistakes

- Claiming modular wrap invalidates add/subtract cancellation.
- Confusing equal values with aliases to one location.
- Using tuple swap when the contract forbids a hidden temporary value.
- Treating the sequential updates as simultaneous combinational feedback equations.

### Short interview answer

Exact arithmetic permits three add/subtract assignments. At eight bits use a^=b; b^=a; a^=b, cancelling each bit twice. Properly defined modular add/subtract also works. Clarify types and overflow, and guard aliases to one location.

### Follow-up

**question**: Is XOR swap necessarily faster than an ordinary temporary-based swap?

**direction**: No. Its three updates are serially dependent, and a compiler may optimize an ordinary swap. Measure on the target architecture; prefer clarity when no artificial restriction applies.

**status**: Prepared as content; not connected to the interactive follow-up queue.

## קבצים ואימות / Files and checks

- [קוד / Code: prep_077_swap_without_temp.py](../solutions/prep_077_swap_without_temp.py)
- [קוד / Code: prep_077_swap_without_temp.cpp](../solutions/prep_077_swap_without_temp.cpp)

- [בדיקה ניתנת להרצה / Executable check](../checks/check_prep_077.py)

- [תוצאת הבדיקה / Check evidence](../checks/prep-077-verification.json)

שאלת ההמשך מוכנה בתוכן בלבד ואינה מחוברת לתור המשך אינטראקטיבי.

The follow-up is prepared as content only; it is not connected to the interactive follow-up queue.


## מקור נוסף — 24.10.2026

[דיווח נוסף על החלפה ללא משתנה עזר](../sources/prep-077-additional-2026-10-24.png), עם שיוכי Apple ו־Rafael מהצילום בלבד. הנוסח, הרמזים, הפתרונות והמזהה נשמרו; אין אישור אנושי חדש או פעילות משתמש.
