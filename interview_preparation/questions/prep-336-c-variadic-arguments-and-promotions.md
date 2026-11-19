# PREP-336 — פונקציה ב־C עם מספר ארגומנטים משתנה

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-15-batch20-12.png)

איך מממשים פונקציות עם מספר לא קבוע של ארגומנטים ב־C, כמו printf למשל?

## פונקציה ב־C עם מספר ארגומנטים משתנה

הסבירו כיצד C11 מממשת פונקציה שמספר הארגומנטים שלה משתנה, כגון printf. כתבו bool sum_doubles(double *out,size_t count,...) שמחברת בדיוק count ארגומנטים מטיפוס double. הקורא חייב להעביר את הכמות והטיפוסים הנכונים, ו־out חייב להצביע ל־double הניתן לכתיבה. תמכו ב־count=0 ובהעברת va_list לפונקציית עזר בלי לצרוך את הרשימה של הקורא. הסבירו את קידומי ברירת המחדל ואת תוצאותיה של אי־התאמה בטיפוסים.

### רמזים

1. איך הפונקציה תדע כמה ארגומנטים לקרוא ומה הטיפוס של כל אחד?
2. stdarg.h מספקת va_list, va_start, va_arg ו־va_end. אין ערך סיום אוטומטי לארגומנטים.
3. קראו double בדיוק count פעמים. float מקודם ל־double, בעוד int אינו הופך ל־double דרך שלוש נקודות. השתמשו ב־va_copy לסריקה נפרדת.

### פתרון מוצע

כותבים ארגומנטים רגילים ואחריהם ... ומשתמשים במאקרואים של stdarg.h. ב־C11 va_start מקבלת את הפרמטר הנקוב האחרון, כאן count. va_arg(values,double) קוראת את הארגומנט הבא בהתאם לטיפוס המבוקש. va_end מסיימת כל רשימה שנפתחה, גם במסלול כשל לאחר האתחול. count=0 מחזיר 0.0 בלי לקרוא מהאזור המשתנה.

אין מידע כללי שמגלה לפונקציה את מספר הארגומנטים או את טיפוסיהם. כאן count והחוזה קובעים זאת; printf משתמשת במחרוזת הפורמט. ארגומנטים אחרי ... עוברים integer promotions, ו־float מקודם ל־double. char ו־short לרוב מקודמים ל־int. int נשאר int, ולכן sum_doubles(&x,1,7) שגוי לעומת sum_doubles(&x,1,7.0). קריאת טיפוס שאינו תואם לארגומנט המקודם, או קריאה מעבר למספר שנמסר, עלולות לגרום להתנהגות לא מוגדרת. אין להשתמש ב־va_arg(values,float).

va_list עשויה להיות טיפוס תלוי־מימוש. כדי לעבור שוב או לתת לעזר לעבור באופן עצמאי יש ליצור va_copy ולסיים את העותק ב־va_end. אין להניח שהשמה רגילה או מניפולציית מצביעים לאוגרים ולמחסנית היא מימוש נייד. בקוד המוצע העזר צורך עותק בלבד. הזמן O(count) ומקום העזר קבוע. בדיקת NULL אינה מגלה מצביע לא תקף, ותקינות count אינה ניתנת לאימות כללי על ידי הפונקציה עצמה.

```c
/* C11. count must equal the number of following double arguments.
   The output pointer must address live writable double storage. */
#include <stdbool.h>
#include <stddef.h>
#include <stdarg.h>

bool sum_doubles(double *out, size_t count, ...) {
    if (out == NULL) return false;
    va_list values;
    va_start(values, count);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(values, double);
    va_end(values);
    *out = sum;
    return true;
}

bool sum_doubles_forwarded(double *out, size_t count, va_list values) {
    if (out == NULL) return false;
    va_list copy;
    va_copy(copy, values);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(copy, double);
    va_end(copy);
    *out = sum;
    return true;
}
```

### הנחות

כל ארגומנט משתנה נקרא כ־double אחרי promotions והכמות נכונה. overflow מספרי אינו חלק מחוזה דיוק הסכימה.

### מקרה קצה

count=0, ערכי double שליליים, float שמקודם ל־double, ושתי סריקות של אותה רשימה דרך עותקים.

### טעות נפוצה

שליחת int במקום double אינה המרה אוטומטית אחרי ... . גם מספר פרמטרים לא נכון אינו שגיאה שהפונקציה יכולה לאתר באופן כללי.

### סיבוכיות או עלות

O(count) זמן ו־O(1) זיכרון נוסף לסכימה.

### בדיקות

קומפלו והרוצו דוגמאות נכונות, count=0 והעברת רשימה עם va_copy. בכוונה לא הורצו קריאות בעלות התנהגות לא מוגדרת.

### תשובה קצרה

אשתמש ב־stdarg ובחוזה שמגדיר כמות וטיפוסים. כל va_start או va_copy יקבלו va_end.

### שאלת המשך

מדוע printf יכולה לזהות חלק מאי־ההתאמות בזמן קומפילציה? מהדר יכול להכיר פונקציה ופורמט קבוע ולהתריע. זו בדיקה נוספת שאינה מוסיפה מטא־מידע כללי לכל קריאת varargs.

## C variadic functions and default promotions

Explain variable-argument functions in C11, such as printf. Implement bool sum_doubles(double *out,size_t count,...) summing exactly count double arguments. The caller must supply the correct count/types and a valid writable double pointer. Support count=0 and a va_list helper that leaves the caller's list unconsumed. Explain default promotions and mismatched argument types.

### Hints

1. How does the function know how many arguments to read and their types?
2. stdarg.h supplies va_list, va_start, va_arg and va_end. There is no automatic argument-list sentinel.
3. Read double exactly count times. float promotes to double, while int does not become double through an ellipsis. Use va_copy for a separate traversal.

### Proposed solution

Declare named parameters followed by ... and use stdarg.h. In C11 va_start takes the last named parameter, count here. va_arg(values,double) retrieves the next argument using its required promoted type. Match each va_start or va_copy with va_end, including exits after initialization. For zero count, return 0.0 without reading unnamed arguments.

A variadic function generally cannot discover the number or types of its arguments. This interface uses count and a fixed-type promise; printf uses its format string. Unnamed arguments undergo integer promotions, and float becomes double. char and short usually promote to int. An int remains int, so sum_doubles(&x,1,7) violates the contract, whereas sum_doubles(&x,1,7.0) satisfies it. A mismatched va_arg type or reading past supplied arguments can cause undefined behavior. Do not retrieve float with va_arg.

va_list is implementation-dependent. Create independent traversals with va_copy and finish each copy with va_end. Ordinary assignment or assumptions about physical stack/register layout are not portable substitutes. The helper consumes its own copy. Time is O(count), with constant auxiliary storage. A NULL test cannot validate an arbitrary pointer, and the function cannot generally verify the supplied count.

```c
/* C11. count must equal the number of following double arguments.
   The output pointer must address live writable double storage. */
#include <stdbool.h>
#include <stddef.h>
#include <stdarg.h>

bool sum_doubles(double *out, size_t count, ...) {
    if (out == NULL) return false;
    va_list values;
    va_start(values, count);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(values, double);
    va_end(values);
    *out = sum;
    return true;
}

bool sum_doubles_forwarded(double *out, size_t count, va_list values) {
    if (out == NULL) return false;
    va_list copy;
    va_copy(copy, values);
    double sum = 0.0;
    for (size_t i = 0; i < count; ++i) sum += va_arg(copy, double);
    va_end(copy);
    *out = sum;
    return true;
}
```

### Assumptions

Correct count and argument types after promotions. Floating-point numerical overflow is outside this summation contract.

### Edge case

Zero count, negative double values, a float promoted to double, and independent copied-list traversals.

### Common mistake

An int is not automatically converted to double after an ellipsis. Wrong argument counts cannot generally be detected by the callee.

### Cost

O(count) time and O(1) additional space.

### Verification

Compiled valid examples, count=0 and va_copy forwarding. Calls with undefined behavior were deliberately excluded.

### Interview answer

Use stdarg under an explicit count/type contract, pairing va_start and va_copy with va_end.

### Follow-up

Why can a compiler diagnose some printf mismatches? It can recognize a known function and constant format. This diagnostic does not add generic runtime metadata to every variadic call.

[checks/check_nov15_software.py](../checks/check_nov15_software.py)

[checks/prep-336-1115-verification.json](../checks/prep-336-1115-verification.json)

[solutions/prep_336_variadic_sum.c](../solutions/prep_336_variadic_sum.c)
