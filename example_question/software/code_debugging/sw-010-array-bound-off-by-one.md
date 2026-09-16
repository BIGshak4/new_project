# SW-010 — Find an array boundary error

**כותרת בעברית:** איתור שגיאת גבול במערך

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Code debugging / איתור שגיאות בקוד |
| Difficulty | 2/10 (provisional) |
| Estimated time | 5 minutes |
| Format | code |
| Modes | quick |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

The shared C function should sum exactly n int elements. For n>0, a points to at least n valid elements. For n=0, a may be NULL. Assume every partial sum fits in int. Identify and fix the error, explain n=0 and n=1, and state time and extra-space complexity.

## שאלה — עברית

פונקציית C המשותפת אמורה לסכום בדיוק n איברים מסוג int. עבור n>0, המצביע a מצביע לפחות ל־n איברים חוקיים. עבור n=0 מותר ש־a יהיה NULL. הניחו שכל סכום ביניים נכנס ב־int. מצאו ותקנו את השגיאה, הסבירו n=0 ו־n=1 וציינו סיבוכיות זמן וזיכרון נוסף.

## Shared code / קוד משותף

```c
#include <stddef.h>

int sum_samples(const int *a, size_t n) {
    int total = 0;
    for (size_t i = 0; i <= n; ++i) {
        total += a[i];
    }
    return total;
}
```

## Hint — English

Count iterations, not just the starting index.

## רמז — עברית

ספרו את מספר האיטרציות, לא רק את אינדקס ההתחלה.

## Reference solution — English

Replace i<=n with i<n. Valid indices are 0 through n-1. The original reads a[n], and even dereferences a at n=0. Correct code returns 0 without access for n=0 and a[0] for n=1. Time O(n), extra space O(1).

## כיוון פתרון — עברית

מחליפים i<=n ב־i<n. האינדקסים החוקיים הם מ־0 עד n-1. הקוד המקורי קורא a[n] ואף ניגש דרך a כאשר n=0. הקוד המתוקן מחזיר 0 ללא גישה עבור n=0 ואת a[0] עבור n=1. זמן O(n), זיכרון נוסף O(1).

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [SEI CERT C: array bounds](https://cmu-sei.github.io/secure-coding-standards/sei-cert-c-coding-standard/rules/arrays-arr/arr30-c/)
