# SW-006 — Find two distinct matching indices

**כותרת בעברית:** מציאת שני אינדקסים שונים שסכומם נתון

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

Given an unsorted integer array and target T, return any two distinct indices whose values sum to T, or indicate no solution. Assume arithmetic does not overflow. Aim for expected O(n) time using a hash map and state the space cost. Explain [6,6] with T=12 and [6] with T=12. Do not reuse the same element.

## שאלה — עברית

נתונים מערך שלמים לא ממוין ויעד T. החזירו שני אינדקסים שונים כלשהם שערכיהם מסתכמים ל־T, או ציינו שאין פתרון. הניחו שאין גלישה חשבונית. שאפו לזמן צפוי O(n) באמצעות hash map וציינו עלות זיכרון. הסבירו את [6,6] עם T=12 ואת [6] עם T=12. אסור להשתמש באותו איבר פעמיים.

## Hint — English

Search for the complement before recording the current element.

## רמז — עברית

חפשו את הערך המשלים לפני שמירת האיבר הנוכחי.

## Reference solution — English

For each (i,x), look for T-x among earlier values before inserting x->i. Return its stored index and i on a match. [6,6] returns (0,1); [6] has no pair. Expected O(n) time under ordinary hash assumptions and O(n) space; worst-case hashing can be worse.

## כיוון פתרון — עברית

לכל (i,x) מחפשים T-x בין הערכים הקודמים לפני הכנסת x->i. בהתאמה מחזירים את האינדקס שנשמר ואת i. עבור [6,6] מוחזר (0,1); עבור [6] אין זוג. הזמן הצפוי O(n) בהנחות הגיבוב הרגילות והזיכרון O(n); במקרה הגרוע גיבוב עשוי להיות איטי יותר.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: stacks, queues, and dictionaries](https://docs.python.org/3/tutorial/datastructures.html)
