# PREP-138 — הדפסת int חתום בפונקציה עם פרמטר יחיד

[צילום המקור](../sources/2026-11-14-batch30-05.png)

ממש בעזרת שפת C פונקציה המקבלת מספר int בלבד ומדפיסה את המספר בבינארי.

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

## הדפסת int חתום בפונקציה עם פרמטר יחיד

ממשו גם void print_binary(int value) בשפת C. הדפיסו ל־stdout סימן מינוס אם נחוץ ואת ספרות גודל המספר בבסיס שתיים, ללא אפסים מובילים וללא שורה חדשה. הדפיסו 0 עבור אפס. אסור להניח רוחב int מסוים.

1. להדפסה ישירה אפשר להתחיל מהסיבית המשמעותית הגבוהה ביותר.
2. למספר שלילי קבעו תחילה סימן וגודל ללא חישוב ‎−INT_MIN בטיפוס int.
3. ממירים ל־unsigned ואז הופכים את הסימן בחשבון לא־חתום.

עבור מספר שלילי מדפיסים מינוס. המרה ל־unsigned int מוגדרת מודולו UINT_MAX+1, ולכן החיסור 0u−(unsigned)value מחזיר בדיוק את גודלו גם עבור INT_MIN. הביטוי ‎−value בטיפוס int עלול לגלוש. מתחילים במסכה 1 ומכפילים אותה בשתיים כל עוד היא לכל היותר חצי מהגודל. כך ההזזה לעולם אינה גולשת, ובסיום המסכה מצביעה על הסיבית הדולקת הגבוהה ביותר; באפס היא נשארת 1. יורדים בסיביות ומדפיסים כל ביט פעם אחת. למשל, ‎−13 מודפס כ־‎−1101. מספר הספרות הוא k ולכן הזמן Θ(k) וזיכרון העזר O(1). אם מתכוונים לתבנית הביטים הגולמית של int יש להגדיר בנפרד רוחב וייצוג.

```c
#include <stdio.h>

void print_binary(int value) {
    unsigned int magnitude = (unsigned int)value;
    if (value < 0) {
        putchar('-');
        magnitude = 0u - magnitude;
    }
    unsigned int mask = 1u;
    while (mask <= magnitude / 2u) {
        mask <<= 1;
    }
    do {
        putchar((magnitude & mask) ? '1' : '0');
        mask >>= 1;
    } while (mask != 0u);
}
```

## Printing a signed int with one parameter

Also implement void print_binary(int value) in C. Write a minus sign if needed followed by the magnitude in binary to stdout, without leading zeros or a trailing newline. Zero prints as 0. Assume no particular int width.

1. For direct printing, start with the highest significant bit.
2. Separate the sign and magnitude while avoiding signed negation of INT_MIN.
3. Convert to unsigned and then negate the value using unsigned arithmetic.

For a negative value write the minus sign. Conversion to unsigned int is defined modulo UINT_MAX+1; subtracting the converted value from 0u therefore produces the magnitude even for INT_MIN. Evaluating −value as an int could overflow. Start a mask at one and double it while it is at most half the magnitude. This avoids overflow and leaves the highest set bit selected, or one for zero. Shift the mask down, writing a digit for every position. For example, −13 prints as −1101. For k digits this takes Θ(k) time and O(1) auxiliary space. A raw signed bit pattern would require a separate width and representation contract.

```c
#include <stdio.h>

void print_binary(int value) {
    unsigned int magnitude = (unsigned int)value;
    if (value < 0) {
        putchar('-');
        magnitude = 0u - magnitude;
    }
    unsigned int mask = 1u;
    while (mask <= magnitude / 2u) {
        mask <<= 1;
    }
    do {
        putchar((magnitude & mask) ? '1' : '0');
        mask >>= 1;
    } while (mask != 0u);
}
```

[solutions/prep_138_print_signed_binary.c](../solutions/prep_138_print_signed_binary.c)

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-138-1114-verification.json](../checks/prep-138-1114-verification.json)
