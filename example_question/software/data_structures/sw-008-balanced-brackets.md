# SW-008 — Validate nested brackets

**כותרת בעברית:** בדיקת תקינות סוגריים מקוננים

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Data structures / מבני נתונים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 10 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A string contains only (), [], and {} characters. Determine whether it is correctly nested. The empty string is valid. Give an algorithm and time/space complexity. Evaluate "([]{})", "([)]", and "]". Explain why counting opening and closing brackets alone is insufficient.

## שאלה — עברית

מחרוזת מכילה רק תווי סוגריים מסוג (), [], {}. קבעו אם הקינון תקין; מחרוזת ריקה תקינה. תנו אלגוריתם וסיבוכיות זמן וזיכרון. בדקו "([]{})", "([)]", "]". הסבירו מדוע ספירת סוגריים פותחים וסוגרים בלבד אינה מספיקה.

## Hint — English

The most recent unmatched opener must close first.

## רמז — עברית

הסוגר הפותח האחרון שעדיין לא נסגר צריך להיסגר ראשון.

## Reference solution — English

Push opening brackets onto a stack. A closing bracket must match the top; reject an empty stack or mismatch. Accept only if the stack is empty at the end. Results true,false,false. Time O(n), worst-case space O(n). Counts miss nesting order.

## כיוון פתרון — עברית

דוחפים סוגר פותח למחסנית. סוגר סוגר חייב להתאים לראש המחסנית; מחסנית ריקה או אי־התאמה גוררות דחייה. מקבלים רק אם המחסנית ריקה בסוף. התוצאות true,false,false. זמן O(n), זיכרון במקרה הגרוע O(n). ספירה אינה בודקת סדר קינון.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: stacks, queues, and dictionaries](https://docs.python.org/3/tutorial/datastructures.html)
