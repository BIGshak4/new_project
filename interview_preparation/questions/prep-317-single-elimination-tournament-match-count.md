# PREP-317 — כמה משחקים בטורניר של 125 שחקנים?

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-14-batch30-25.png)

ישנו טורניר פינג פונג עם 125 משתתפים, בכל סיבוב מנצח יחיד (בהנחה ויש מספר אי זוגי של משתתפים בשלב, אחד עולה לשלב הבא), אם בכל משחק משחקים 2 אנשים, כמה משחקים ישוחקו בכל הטורניר עד להכרזת המנצח?

## כמה משחקים בטורניר של 125 שחקנים?

בטורניר טניס שולחן משתתפים 125 שחקנים. בכל משחק שני שחקנים, המפסיד מודח והמנצח ממשיך. כשיש מספר אי־זוגי של שחקנים בסיבוב, אחד עולה לסיבוב הבא ללא משחק. כמה משחקים נערכים עד שנותר מנצח אחד? הסבירו מדוע מספר העליות החופשיות אינו משנה את התוצאה.

### רמזים

1. מה משתנה במספר המתחרים בכל משחק שמסתיים?
2. כמה שחקנים מסיימים את הטורניר בהפסד?
3. קשרו כל משחק לשחקן היחיד שהודח בו.

### פתרון מוצע

מתחילים עם 125 מתחרים פעילים ומסיימים עם אחד. בכל משחק מודח בדיוק מתחרה אחד. לכן יש להדיח 124 מתחרים, והמספר הדרוש הוא 124 משחקים. מתחרה שקיבל עלייה חופשית נשאר פעיל ואינו משנה את הספירה.

אפשר לבדוק לפי סיבובים: 62, 31, 16, 8, 4, 2 ו־1 משחקים, יחד 124. עבור n≥1 אותו טיעון נותן n−1.

### הנחות

משחק מסתיים במנצח ומפסיד יחידים; אין משחקי דירוג חוזרים.

### מקרה קצה

שחקן יחיד זוכה בלי משחק. טורניר ללא שחקנים אינו מוכתר במנצח.

### טעות נפוצה

עיגול כלפי מעלה של מספר המשחקים בסיבוב אי־זוגי סופר בטעות את העלייה החופשית כמשחק.

### סיבוכיות או עלות

O(1) פעולות חשבון גם עבור n שחקנים.

### בדיקות

סימולציה סופרת זוגות בכל סיבוב ומשווה ל־n−1 במגוון גדלים, כולל 125.

### תשובה קצרה

124 שחקנים חייבים להיות מודחים, ולכל אחד משחק הפסד אחד.

### שאלת המשך

מה אם מוסיפים משחק על המקום השלישי? זהו משחק נוסף בין שני מודחים שאינו קובע מי נשאר בתחרות על התואר. בטורניר הזה הסך נעשה 125.

## How many matches for 125 tournament players?

A table-tennis tournament has 125 players. Each match pairs two players; its loser is eliminated and its winner advances. When a round has an odd number of players, one advances without a match. How many matches are played before one champion remains? Explain why the number of byes does not affect the answer.

### Hints

1. What changes in the active-player count when a match ends?
2. How many players finish the tournament with a loss?
3. Associate each played match with its one eliminated player.

### Proposed solution

The active count starts at 125 and ends at one. A match eliminates exactly one player. Eliminating 124 players therefore takes exactly 124 matches. A bye keeps its recipient active and has no effect on this count.

As a check, the rounds contain 62, 31, 16, 8, 4, 2 and 1 matches, summing to 124. For any n≥1 the same argument gives n−1.

### Assumptions

Every match has exactly one loser and one winner. There are no additional placement games.

### Edge case

One player wins without a match. An empty tournament has no champion.

### Common mistake

Rounding the match count up in an odd round counts a bye as a played match.

### Cost

O(1) arithmetic operations for any n players.

### Verification

A round simulation counts pairs and checks the n−1 formula over a range of sizes, including 125.

### Interview answer

There are 124 eliminated players and each has precisely one losing match.

### Follow-up

What if a third-place match is added? It is an extra match between two already eliminated players. This tournament would then have 125 matches.

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-317-1114-verification.json](../checks/prep-317-1114-verification.json)
