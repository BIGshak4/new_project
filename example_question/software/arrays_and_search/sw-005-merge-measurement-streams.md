# SW-005 — Merge sorted measurement lists

**כותרת בעברית:** מיזוג רשימות מדידות ממוינות

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Arrays and search / מערכים וחיפוש |
| Difficulty | 3/10 (provisional) |
| Estimated time | 10 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Two integer arrays of lengths n and m are sorted in nondecreasing order. Merge them into a new sorted array, preserving every occurrence, in O(n+m) time without calling sort. Explain auxiliary space separately from output storage. Show the result for [1,4,4] and [2,4,7], and handle an empty input.

## שאלה — עברית

שני מערכי שלמים באורכים n ו־m ממוינים בסדר לא יורד. מזגו אותם למערך חדש ממוין, תוך שמירת כל המופעים, בזמן O(n+m) וללא קריאה למיון. הפרידו בין זיכרון עזר לזיכרון הפלט. הציגו תוצאה עבור [1,4,4] ו־[2,4,7], וטפלו בקלט ריק.

## Hint — English

Use one cursor per array.

## רמז — עברית

השתמשו בסמן נפרד לכל מערך.

## Reference solution — English

Advance two indices, append the smaller current value, then append the remaining suffix. On equality either side may go first but neither occurrence is discarded. Result: [1,2,4,4,4,7]. Output uses O(n+m); auxiliary state beyond output is O(1).

## כיוון פתרון — עברית

מקדמים שני אינדקסים, מוסיפים בכל צעד את הערך הנוכחי הקטן יותר ולבסוף את השארית. בשוויון אפשר לבחור כל צד תחילה אך אין להשמיט מופע. התוצאה: [1,2,4,4,4,7]. הפלט דורש O(n+m) והמצב הנוסף מעבר לפלט הוא O(1).

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: merging sorted inputs](https://docs.python.org/3/library/heapq.html#heapq.merge)
