# SW-004 — First element at least a target

**כותרת בעברית:** האיבר הראשון שאינו קטן מהיעד

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Arrays and search / מערכים וחיפוש |
| Difficulty | 4/10 (provisional) |
| Estimated time | 12 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Given a nondecreasing integer array a of length n, return the first index i with a[i]>=target, or n if none exists. Implement it without a library search in O(log n) time and O(1) extra space. For a=[2,4,4,9], evaluate targets 4,8,10. Explain empty input and repeated values.

## שאלה — עברית

נתון מערך שלמים a באורך n, ממוין בסדר לא יורד. החזירו את האינדקס הראשון i שעבורו a[i]>=target, או n אם אין כזה. ממשו ללא חיפוש ספרייה בזמן O(log n) ובזיכרון נוסף O(1). עבור a=[2,4,4,9] בדקו יעדים 4,8,10. הסבירו טיפול במערך ריק ובערכים חוזרים.

## Hint — English

On equality, keep looking to the left.

## רמז — עברית

גם במציאת שוויון ממשיכים לחפש שמאלה.

## Reference solution — English

Maintain half-open interval [lo,hi), initially [0,n). While lo<hi, mid=lo+(hi-lo)//2; if a[mid]<target set lo=mid+1, otherwise hi=mid. Return lo. Results: 1,3,4; empty input returns 0.

## כיוון פתרון — עברית

מחזיקים טווח חצי פתוח [lo,hi), המתחיל ב־[0,n). כל עוד lo<hi מחשבים mid=lo+(hi-lo)//2; אם a[mid]<target מעדכנים lo=mid+1, אחרת hi=mid. מחזירים lo. התוצאות: 1,3,4; במערך ריק מוחזר 0.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: binary search and insertion points](https://docs.python.org/3/library/bisect.html)
