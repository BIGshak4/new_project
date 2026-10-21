# PREP-079 — משחק שלושה שחקנים — מתי כדאי להחטיא בכוונה? / Three-player probability game — when is a deliberate miss better?

מקור שנמסר ב־21.10.2026. פתרון מוצע בסיוע AI; סקירה מקצועית, תרגום וזכויות שימוש ממתינים.

Source supplied 2026-10-21. AI-assisted proposed solution; professional, translation and reuse reviews pending.

[צילום מקור / Original screenshot](../sources/prep-079-source.png)

## הנוסח המקורי / Original text

אתה עומד במעגל עם עוד שני אקדוחנים, לכל אחד אקדח. אתה פוגע ב10% מהמקרים, אקדוחן א פוגע ב50% מהמקרים ואקדוחן ב פוגע ב90% מהמקרים.
המטרה היא להישאר בחיים אחרון.
לצורך הוגנות, הוחלט שסדר הירי הוא לפי אחוזי הדיוק, כך שאתה יורה ראשון, אקדוחן א אחריך ואקדוחן ב אחריו - כך עד שנשאר רק אחד מכם.
מה הטקטיקה שלך? לאן אתה מכוון את היריות?

## עברית

### משחק שלושה שחקנים — מתי כדאי להחטיא בכוונה?

במשחק הסתברותי שלושה שחקנים A,B,C. בתורו כל שחקן בוחר יריב ומנסה להוציאו מהמשחק, או בוחר להחטיא בכוונה. הסתברות ההצלחה בניסיון נגד יריב היא 10% עבור A, 50% עבור B ו־90% עבור C, קבועה ובלתי תלויה בניסיונות אחרים וביריב שנבחר. המטרה של כל שחקן היא להיות השורד היחיד.

סדר התורות מחזורי A→B→C, מדלגים על שחקן שיצא, ו־A מתחיל. ממשיכים עד שנשאר שחקן אחד. מה כדאי ל־A לעשות בתור הראשון ובהמשך כאשר שלושתם עדיין במשחק? נמקו גם את בחירות B,C הרציונליים וחשבו את סיכוי A לזכות.

הבהרות שנוספו בעריכה: תור אחד הוא ניסיון אחד; כישלון או החטאה מכוונת מעבירים תור; מותר להחטיא בכוונה גם בהמשך; אין שיתוף פעולה או שינוי אחוזי הצלחה. בוחנים מדיניות קבועה התלויה במשתתפים שנותרו ובתור הנוכחי. זהו מודל מופשט של חידת המקור, לא הנחיות לאירוע אמיתי.

### שלושה רמזים

1. הוצאה של יריב אינה בהכרח שיפור: מי יקבל את התור הבא ומה יישאר ממנו לעשות?

2. תחילה חשבו סיכוי ניצחון במשחק של שניים, כאשר השחקן החלש מתחיל לעומת כשהוא שני.

3. השוו שלוש אפשרויות של A: ניסיון נגד B, ניסיון נגד C, והחטאה. אם A נמנע, בדקו את תוצאת המאבק בין B,C ואת זהות המתחיל במשחק הזוגי שנוצר.

## הצעה לפתרון

### מתחילים ממשחק של שניים

שחקן בעל הצלחה p מול שחקן q, כאשר הראשון מקבל תור, מנצח בהסתברות U=p+(1−p)(1−q)U. לכן U=p/(p+q−pq). אם היריב מתחיל, ההסתברות היא (1−q)p/(p+q−pq). אלו סכומים של מספר בלתי חסום של סבבים; לא מספיק לחשב רק ניסיון אחד לכל שחקן. כשהיריב יחיד, ניסיון אמיתי עדיף מהחטאה מכוונת: החטאה מוותרת על הסיכוי המיידי ומוסרת תור.

ל־A יש מול B סיכוי 2/11 אם A מתחיל ו־1/11 אם B מתחיל. מול C הסיכויים הם 10/91 אם A מתחיל ו־1/91 אם C מתחיל. ההבדל בסדר התור מהותי.

### המדיניות המוצעת ובדיקת היריבים

כל עוד שלושתם במשחק: A מחטיא בכוונה, B מנסה להוציא את C, ו־C מנסה להוציא את B. כשנותרים שניים, כל אחד מנסה להוציא את היריב. אין להניח אוטומטית שתמיד מוציאים את החזק: צריך לבדוק שזו אכן בחירה רציונלית תחת סדר התורות וההסתברויות.

הטבלה הבאה נותנת לכל שחקן, בתורו כאשר שלושתם קיימים, את סיכוי הניצחון לאחר פעולה אחת ואז חזרה למדיניות המוצעת. כל השברים חושבו ממשוואות המעבר, לא מסימולציית מדגם.

| בתורו של | החטאה מכוונת | נגד A | נגד B | נגד C |
| --- | --- | --- | --- | --- |
| A | 2810/19019 | — | 25499/190190 | 27019/190190 |
| B | 9/209 | 10/209 | — | 90/209 |
| C | 729/1729 | 810/1729 | 1458/1729 | — |

בכל שורה הפעולה המוצעת נותנת את הערך הגדול ביותר. הבדיקה כוללת את בחירות B,C ולא רק את A. פתרון משוואות לכל 26 המדיניות הדטרמיניסטיות הקבועות שבהן לא כולם מחטיאים מצא מדיניות יחידה במחלקה זו ללא שיפור חד־צעד בכל מצב. מדיניות שבה כולם מחטיאים אינה מסתיימת ואינה יכולה להיות מאוזנת: כל שחקן יכול לנסות ולהשיג סיכוי חיובי לניצחון. אין בכך טענה שכל אסטרטגיה מעורבת או תלויה בהיסטוריה הוכחה כיחידה.

### חישוב הסיכוי של A כשהוא מחטיא

אחרי החטאת A מגיע B. במחזור B,C, ההסתברות ש־B יוציא את C לפני ש־C יוציא את B היא

```text
w_B = 0.5 + (0.5*0.1)*w_B = 10/19
w_C = 1-w_B = 9/19
```

ה־0.5*0.1 הוא מצב שבו שניהם לא הצליחו והמצב חוזר אחרי החטאה נוספת של A. בכל יציאה ראשונה של אחד מהם A מקבל את התור הראשון מול השורד: אם B הצליח, C מדולג; אם C הצליח, A הוא הבא ממילא. לכן

```text
V = (10/19)*(2/11) + (9/19)*(10/91)
  = 2810/19019 ≈ 0.14774699 = 14.7747%
```

### השוואה לניסיון אמיתי בתור הראשון

אם A מנסה נגד C ומצליח, B מתחיל את המשחק הזוגי נגד A, שנותר עם סיכוי 1/11. אם A נכשל, התור עובר ל־B ואותה מדיניות נמשכת; זה בדיוק המצב שאליו מגיעים אחרי החטאה מכוונת. לכן ערך הפעולה הוא (1/10)*(1/11)+(9/10)*V=27019/190190≈14.2063%.

אם A מנסה נגד B ומצליח, C מתחיל את המשחק הזוגי וסיכוי A הוא 1/91. הערך הוא (1/10)*(1/91)+(9/10)*V=25499/190190≈13.4071%. שתי האפשרויות קטנות מ־V. התוצאה המפתיעה אינה ״החטאה טובה תמיד״: היא תלויה בשלושה שחקנים, בתורות ובהסתברויות הנתונים. לאחר היציאה הראשונה A כבר צריך לנסות נגד היריב היחיד.

### איך אומת המודל ומה לא נטען

בקוד הפתרון חושבו משוואות מחזוריות בחשבון Fraction מדויק. בדיקה נפרדת בנתה שרשרת מרקוב בתשעה מצבים חולפים — שלושה תורות עם שלושתם ושישה תורות בזוגות — ופתרה משוואות ספיגה באלימינציה גאוסית. הושוו כל שלושת סיכויי הזוכים בכל תור עבור כל 26 המדיניות המסתיימות. נבדקו כל תשע הפעולות האפשריות כסטייה חד־צעד במדיניות המוצעת וששת מצבי התור בזוגות. ההצלחה חיובית וקבועה, ולכן במדיניות זו ההסתברות להמשיך ללא סוף היא 0.

אין מדובר באימות של מצב אמיתי או באישור אנושי. לא נטען אופטימום עבור הסתברויות אחרות, בריתות, ירי בו־זמני, מספר סופי של ניסיונות או תגובות לא רציונליות. הפתרון המוצע שייך רק למשחק המופשט שהוגדר.


### הנחות

- סדר מחזורי A,B,C עם דילוג על יוצאים; A מתחיל, ניסיון אחד בכל תור.
- הצלחות עצמאיות בהסתברויות קבועות 1/10,1/2,9/10 בלי תלות ביריב.
- מותר להחטיא בכוונה; המטרה היא הסתברות שורד יחיד, בלי בריתות או הגבלת מספר ניסיונות.
- נבחנות מדיניות דטרמיניסטיות קבועות לפי הנותרים והתור; אין טענת יחידות לכל אסטרטגיה אפשרית.

### נכונות ועלות

**criterion**: הסתברות הזכייה של A במשחק המופשט ובהמשך הרציונלי שנבדק.

**result**: A מחטיא כל עוד שלושתם; B נגד C ו־C נגד B. סיכוי A הוא 2810/19019≈14.7747%.

**proof**: משוואות זוגיות ומחזוריות נותנות ערכי המשך; כל תשע ההשוואות החד־צעד מעדיפות את המדיניות. כל 26 המדיניות המסתיימות נבדקו במחלקה הקבועה הדטרמיניסטית.

**scope**: אין טענת יחידות של כל שיווי משקל מעורב/תלוי היסטוריה או אופטימום כאשר משנים את כללי המשחק.

### אימות

עברו 26 מדיניות מסתיימות מול מערכת מרקוב עצמאית של תשעה מצבים וחשבון שברים מדויק; כל תשע הפעולות במדיניות המוצעת וששת מצבי הזוגות נבדקו. אין מדגם אקראי, בדיקה אמיתית או אישור מקצועי אנושי.

### מקרי קצה

- כשהנותר השני יחיד, A צריך לנסות נגדו ולא להמשיך להחטיא.
- שני ניסיונות כושלים חוזרים למחזור, ולכן נדרש סכום גאומטרי ולא חישוב סבב יחיד.
- מדיניות שבה כולם מחטיאים אינה נספגת; מודל הניקוד אינו מעניק בה זכייה לאיש.
- אם אסור להחטיא או משתנה סדר התורות, זו שאלה אחרת.

### טעויות נפוצות

- להתעלם מזהות השחקן שמתחיל לאחר ההוצאה הראשונה.
- להניח ש־B,C פועלים באופן רציונלי בלי להשוות את חלופותיהם.
- לסכם רק את סבב הניסיונות הראשון.
- להכליל שהחטאה תמיד עדיפה או שהחלש תמיד בעל הסיכוי הגבוה ביותר.

### תשובה קצרה לראיון

אחטיא בכוונה כששלושתם קיימים, בתנאי היריבים הרציונליים שהוגדרו. B ו־C מעדיפים להוציא זה את זה; לאחר הצלחה של אחד מהם אני מתחיל מול השורד. משוואות הזוגות והמחזור נותנות 2810/19019≈14.77%, יותר מניסיון נגד C≈14.21% או B≈13.41%. כשנשאר יריב אחד אנסה נגדו.

### שאלת המשך

**question**: כיצד בודקים אם החטאה עדיין עדיפה עבור שלוש הסתברויות הצלחה אחרות?

**direction**: חשבו מחדש את הסתברויות הזוגות וסדר התור אחרי כל הצלחה, פתרו משוואות מחזור עבור מדיניות מועמדת והשוו את כל הפעולות לכל שחקן. אין להעתיק את אותן בחירות או את התוצאה 14.77% ללא בדיקה.

**status**: מוכן בתוכן; אינו מחובר לתור המשך אינטראקטיבי.

## English

### Three-player probability game — when is a deliberate miss better?

An abstract probability game has players A,B,C. On a turn, a player either selects an opponent and attempts to eliminate them or deliberately misses. Success probabilities against an opponent are 10% for A, 50% for B and 90% for C, fixed and independent across attempts and targets. Each player's goal is to be the sole survivor.

Turns cycle A→B→C, skipping eliminated players, and A starts. Continue until one player remains. What should A do initially and whenever all three remain? Justify the rational choices of B,C as well and compute A's winning probability.

Editorial clarifications: one attempt per turn; failure or deliberate miss passes the turn; deliberate misses remain available later; there is no cooperation or changing accuracy. Analyze stationary policies depending on surviving players and the current turn. This is an abstract model of the source puzzle, not instructions for a real event.

### Three hints

1. Eliminating an opponent need not help: who acts next, and whom will they face?

2. First calculate two-player winning probabilities when the weaker player starts versus when they act second.

3. Compare A's three choices: attempt B, attempt C, or miss. If A abstains, analyze B versus C and identify who starts the resulting duel.

## Proposed solution

### Start with two players

A player with success p against q, acting first, wins with U=p+(1−p)(1−q)U. Thus U=p/(p+q−pq). If the opponent acts first, the probability is (1−q)p/(p+q−pq). These sum an unbounded number of rounds; considering one attempt per player is insufficient. With only one opponent, attempting is better than deliberately missing, which forfeits the immediate success chance and passes the turn.

A's chance against B is 2/11 if A starts and 1/11 if B starts. Against C it is 10/91 if A starts and 1/91 if C starts. Turn order matters substantially.

### Proposed policy and checking the other players

While all three remain, A deliberately misses, B attempts C and C attempts B. Once only two remain, both attempt the other. Do not assume everyone always targets the strongest: rationality must be checked for the actual turn order and probabilities.

This table gives each player's winning probability at their all-alive turn after taking one action, then returning to the proposed continuation policy. Fractions come from first-step equations rather than sampled simulation.

| Current actor | Deliberate miss | Target A | Target B | Target C |
| --- | --- | --- | --- | --- |
| A | 2810/19019 | — | 25499/190190 | 27019/190190 |
| B | 9/209 | 10/209 | — | 90/209 |
| C | 729/1729 | 810/1729 | 1458/1729 | — |

The proposed action is strictly best in every row. This checks B and C as well as A. Evaluating all 26 terminating deterministic stationary policies finds one policy in that class with no profitable one-step action deviation in any state. All-miss never terminates and cannot be an equilibrium: a player can attempt and gain a positive winning chance. This does not prove uniqueness over all mixed or history-dependent strategies.

### A's probability after deliberately missing

B acts after A's miss. In the B,C cycle, the probability that B eliminates C before C eliminates B is

```text
w_B = 0.5 + (0.5*0.1)*w_B = 10/19
w_C = 1-w_B = 9/19
```

The 0.5*0.1 term means both failed, after which another A miss restores the same state. Whichever player is first eliminated, A acts first against the survivor: C is skipped if B succeeded; A is already next if C succeeded. Hence

```text
V = (10/19)*(2/11) + (9/19)*(10/91)
  = 2810/19019 ≈ 0.14774699 = 14.7747%
```

### Compare a real attempt on the first turn

If A attempts C and succeeds, B starts the duel against A, leaving A a chance of 1/11. If A fails, B acts with all three alive, exactly the continuation after A deliberately misses. The action value is (1/10)*(1/11)+(9/10)*V=27019/190190≈14.2063%.

If A attempts B and succeeds, C starts the duel, leaving A a chance of 1/91. The value is (1/10)*(1/91)+(9/10)*V=25499/190190≈13.4071%. Both are below V. The lesson is not that missing is always good: it relies on these three players, cyclic turns and probabilities. After the first elimination A should attempt the sole remaining opponent.

### Verification and limits

The solution evaluates cyclic recurrences using exact Fraction arithmetic. An independent check builds a nine-transient-state absorbing Markov chain: three all-alive turn states and six two-player turn states. It solves the absorption equations with Gaussian elimination and compares all three winner probabilities from every all-alive turn for all 26 terminating policies. All nine one-step choices at the proposed policy and all six duel turn states were checked. Positive fixed success rates imply that this policy continues forever with probability zero.

This is not a model validated for a real event or a human professional approval. No optimum is claimed for different probabilities, alliances, simultaneous actions, a finite attempt budget or irrational responses. The proposed solution applies only to the specified abstract game.


### Assumptions

- Cyclic A,B,C turns skip eliminated players; A starts and one attempt occurs per turn.
- Independent successes have fixed probabilities 1/10,1/2,9/10 independent of the chosen target.
- Deliberate miss is allowed; maximize sole-survivor probability with no alliances or finite attempt budget.
- Analyze deterministic stationary policies by survivors and turn; no uniqueness claim over every possible strategy.

### Correctness and cost

**criterion**: A's winning probability in the specified abstract game with the checked rational continuation.

**result**: A misses while all three remain; B targets C and C targets B. A wins with 2810/19019≈14.7747%.

**proof**: Duel and cyclic recurrences give continuation values; all nine one-step comparisons favor the policy. All 26 terminating deterministic stationary policies were evaluated.

**scope**: No uniqueness claim for all mixed/history-dependent equilibria or optimum under changed game rules.

### Verification

All 26 terminating policies matched an independent nine-state exact-Fraction Markov linear system; nine action values at the proposed policy and six duel turn states passed. No random sampling, real-world verification or human professional approval.

### Edge cases

- Once a sole opponent remains, A should attempt rather than continue missing.
- Failed attempts repeat cycles, requiring geometric sums rather than one-round calculations.
- All-miss is nonabsorbing and awards no sole-survivor win.
- Forbidding misses or changing turn order creates a different problem.

### Common mistakes

- Ignoring who acts first after the first elimination.
- Assuming rational B,C targets without comparing their alternatives.
- Summing only the first round.
- Generalizing that missing is always better or the weakest always has the highest winning chance.

### Short interview answer

Miss while all three remain under the specified rational continuation. B and C prefer to eliminate each other; after either succeeds I act first against the survivor. Duel/cycle equations give 2810/19019≈14.77%, above attempting C≈14.21% or B≈13.41%. With one opponent left, attempt them.

### Follow-up

**question**: How would you check whether a deliberate miss remains better for three different success probabilities?

**direction**: Recompute duel probabilities and post-success turn order, solve cyclic equations for candidate policies and compare every player's actions. Do not reuse the same targets or 14.77% result without checking.

**status**: Prepared as content; not connected to the interactive follow-up queue.

## קבצים ואימות / Files and checks

- [קוד / Code: prep_079_cyclic_probability_game.py](../solutions/prep_079_cyclic_probability_game.py)

- [בדיקה ניתנת להרצה / Executable check](../checks/check_prep_079.py)

- [תוצאת הבדיקה / Check evidence](../checks/prep-079-verification.json)

שאלת ההמשך מוכנה בתוכן בלבד ואינה מחוברת לתור המשך אינטראקטיבי.

The follow-up is prepared as content only; it is not connected to the interactive follow-up queue.
