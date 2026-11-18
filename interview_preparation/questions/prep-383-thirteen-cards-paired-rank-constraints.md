# PREP-383 — שלושה־עשר קלפים וארבע דרגות

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-18-batch21-16.png)

13 קלפים בחפיסה. בחפיסה נמצאים מלכים, מלכות, אסים ונסיכים. יש לפחות 1 מכל סוג. הכמות של כל סוג היא שונה. ידוע שמספר המלכים והמלכות בחפיסה הוא 5. ידוע שמספר הנסיכים והמלכות בחפיסה הוא 6. מאיזה סוג בחפיסה יש רק 2 קלפים?

## שלושה־עשר קלפים וארבע דרגות

בערימה 13 קלפים מארבע דרגות בלבד — מלכים, מלכות, נסיכים ואסים. כל דרגה מופיעה לפחות פעם אחת, וארבע הכמויות שונות זו מזו. מלכים ומלכות יחד מונים 5, ונסיכים ומלכות יחד מונים 6. ייתכנו יותר מארבעה קלפים מאותה דרגה. אם ידוע שדרגה כלשהי מופיעה פעמיים, איזו דרגה זו? האם קיומה של דרגה כזו מתחייב גם בלי המידע הנוסף?

### רמזים

1. בחרו משתנה לכמות המלכות, שמופיעה בשני הנתונים.
2. אם יש q מלכות, כמה מלכים וכמה נסיכים יש? השלימו את מספר האסים מתוך הסך 13.
3. נסו את כל הערכים החיוביים ל־q שמשאירים לפחות מלך אחד. פסלו כל שורה שבה שתי כמויות שוות.

### פתרון מוצע

### מתחילים בדרגה שמופיעה בשתי המשוואות
נסמן ב־q את מספר המלכות. יש `5−q` מלכים, `6−q` נסיכים ו־`2+q` אסים לאחר השלמה ל־13. מכיוון שיש לפחות מלכה אחת ומלך אחד, q יכול להיות 1, 2, 3 או 4.

| מלכות | מלכים | נסיכים | אסים | הכמויות שונות? |
| --- | --- | --- | --- | --- |
| 1 | 4 | 5 | 3 | כן |
| 2 | 3 | 4 | 4 | לא |
| 3 | 2 | 3 | 5 | לא |
| 4 | 1 | 2 | 6 | כן |

בשורה האחרונה יש בדיוק שני **נסיכים**. זו השורה החוקית היחידה שבה דרגה מופיעה פעמיים. גם השורה הראשונה חוקית ובה אין אף דרגה שמופיעה פעמיים. מכאן שהשאלה האחרונה אכן מוסיפה מידע.

### הנחות

הערימה יכולה לכלול מספר חופשי של עותקים מאותה דרגה. כל קלף שייך לדרגה אחת.

### מקרה קצה

אם דורשים להשתמש בחפיסה רגילה אחת ובה לכל היותר ארבעה קלפים מכל דרגה, שתי החלוקות החוקיות נפסלות.

### טעות נפוצה

לעצור ברגע שנמצאה חלוקה עם שני נסיכים, בלי לבדוק אם הנתונים מחייבים שבכלל יהיו שניים מדרגה כלשהי.

### סיבוכיות או עלות

בדיקת ארבע אפשרויות למספר המלכות ממצה את כל החלוקות.

### בדיקות

נמנו כל ההרכבים החיוביים של 13 לארבע דרגות ונבדקו כל האילוצים בנפרד.

### תשובה קצרה

יש שתי חלוקות חוקיות. אחת כוללת שני נסיכים ובשנייה אף דרגה אינה מופיעה פעמיים. אם מובטח שיש זוג בדרגה מסוימת, אלו הנסיכים.

### שאלת המשך

מה קורה אם משמיטים את הדרישה שהכמויות שונות זו מזו? נוספות שתי השורות האמצעיות. אז גם מלכות או מלכים יכולים להופיע פעמיים.

## Thirteen cards and four ranks

A pile contains 13 cards, all kings, queens, jacks or aces. Each rank occurs at least once, and all four counts are different. The kings and queens together total 5, and the jacks and queens together total 6. More than four copies of a rank are allowed. If some rank occurs exactly twice, which rank is it? Do the other clues alone guarantee that any rank occurs twice?

### Hints

1. Choose a variable for the rank shared by both pair totals.
2. If there are q queens, how many kings and jacks are there? Use the total of 13 to obtain the number of aces.
3. Try each positive value of q that leaves at least one king. Discard any row with two equal counts.

### Proposed solution

### Start with the rank in both equations
Let q be the number of queens. There are `5−q` kings, `6−q` jacks and hence `2+q` aces after subtracting from 13. Since there is at least one queen and at least one king, the possible values of q are 1, 2, 3 and 4.

| Queens | Kings | Jacks | Aces | Distinct counts? |
| --- | --- | --- | --- | --- |
| 1 | 4 | 5 | 3 | Yes |
| 2 | 3 | 4 | 4 | No |
| 3 | 2 | 3 | 5 | No |
| 4 | 1 | 2 | 6 | Yes |

The final row has exactly two **jacks**. It is the only valid row containing a two. The first row also satisfies all the original clues and has no count of two, so the existence of such a rank adds information.

### Assumptions

The pile can contain any number of copies of each rank, and each card has one rank.

### Edge case

If the cards must come from one standard deck with at most four of each rank, both otherwise valid rows are ruled out.

### Common mistake

Stopping at a valid assignment with two jacks without checking whether a twice-occurring rank is guaranteed.

### Cost

Checking the four possible queen counts exhausts every feasible assignment.

### Verification

Every positive composition of 13 into four rank counts was enumerated and checked against each clue.

### Interview answer

Two assignments satisfy the clues. One has two jacks and the other has no rank occurring twice. If a rank is guaranteed to occur twice, it is jacks.

### Follow-up

Which ranks could occur twice if the counts no longer had to differ? The middle two rows become valid. Queens or kings could then also occur twice.

[checks/check_1118b_cylinder_cards_hourglasses.py](../checks/check_1118b_cylinder_cards_hourglasses.py)

[checks/prep-383-1118b-verification.json](../checks/prep-383-1118b-verification.json)
