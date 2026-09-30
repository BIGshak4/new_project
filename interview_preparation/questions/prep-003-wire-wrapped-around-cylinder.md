# PREP-003 — אורך חוט המלופף סביב גליל

## השאלה המקורית

גליל שגובהו 150 מ' והיקפו 40 מ'. חוט מתלפף מסביב לגליל ומקיף אותו ב-5 ליפופים(סיבובים) מהתחתית עד לראשה.

בהנחה שהחוט אחיד וצמוד באופן רצוף לאורך הגליל במרווחים זהים-מה אורכו של החוט?

## English translation

A cylinder is 150 m tall and has a circumference of 40 m. A wire wraps around it for 5 turns from the bottom to the top. Assuming the wire is uniform, remains continuously in contact with the cylinder, and its turns are evenly spaced, what is the length of the wire?

## נושאים

- תגית במקור: hardware.
- סיווג נוסף שלנו: גאומטריה וחשיבה מרחבית.

## חברות המופיעות במקור

Arm, NVIDIA, Conduit.

בתמונה מופיעה גם תווית ״Nvidia״. השיוך מתועד כפי שסופק, ללא אימות עצמאי.

## מקור

[צילום השאלה והתגיות](../sources/prep-003.png), התקבל ב־24 בספטמבר 2026.

רמת קושי וזמן פתרון: טרם הוערכו.

## מצב הלמידה

לבקשת הראל נוספו שלושה רמזים מדורגים ופתרון מלא. הפתרון במצב `proposed`, ללא טענה לבדיקת מומחה.

## שלושה רמזים מדורגים

1. דמיין שחותכים את מעטפת הגליל לאורך קו אנכי ופורסים אותה על שולחן. איזו צורה מתקבלת, ואיך נראה עליה קטע החוט של ליפוף אחד?
2. בכל סיבוב החוט מתקדם מרחק של היקף אחד סביב הגליל ועולה בחמישית מגובהו. בפריסה למישור, שתי ההתקדמויות האלה מאונכות. חשב את העלייה האנכית לסיבוב.
3. בפריסה, ליפוף אחד הוא יתר במשולש ישר־זווית שניצביו 40 מטר ו־150/5=30 מטר. השתמש במשפט פיתגורס כדי לחשב את אורכו, ואז כפל במספר הליפופים.

## Progressive hints — English

1. Imagine cutting the cylinder's lateral surface along a vertical line and laying it flat. What shape do you get, and what does one turn of the wire look like on it?
2. Each turn travels one circumference around the cylinder and rises by one fifth of its height. These displacements are perpendicular in the flat development. Calculate the vertical rise per turn.
3. In the flat development, one turn is the hypotenuse of a right triangle with legs 40 m and 150/5=30 m. Apply the Pythagorean theorem and multiply the resulting length by the number of turns.

## הנחות

מפרשים את הליפוף האחיד כסליל בעל עלייה קבועה ביחס לזווית הסיבוב על גליל ישר ועגול.
יש בדיוק חמישה סיבובים מלאים מהתחתית עד הראש, ללא קצוות חוט נוספים, ועובי החוט זניח.

## הצעה לפתרון

אורך החוט הוא **250 מטר**.

פריסת מעטפת הגליל למישור שומרת על אורכים. בליפוף אחיד, כל סיבוב של החוט הופך לקטע ישר:
הוא מתקדם אופקית היקף אחד, 40 מטר, ועולה אנכית בחמישית מהגובה, כלומר `150/5=30` מטר.

לכן אורך ליפוף אחד הוא היתר במשולש ישר־זווית:

`l = sqrt(40^2 + 30^2) = sqrt(2500) = 50 m`.

חמשת הליפופים זהים באורכם:

`L = 5 * 50 = 250 m`.

אפשר גם לפרוס את כל חמשת הסיבובים ברצף במישור. ההתקדמות האופקית המצטברת היא
`5*40=200` מטר והאנכית היא 150 מטר:

`L = sqrt(200^2 + 150^2) = sqrt(62500) = 250 m`.

בכלליות, עבור גובה `H`, היקף `C` ומספר סיבובים `N`:

`L = sqrt(H^2 + (N*C)^2)`.

זו תשובת אורך מדויקת למסלול הנתון; אין כאן צורך באופטימיזציה אלגוריתמית.

## Proposed solution — English

The wire is **250 m** long. Developing the lateral surface into a plane preserves lengths.
Each turn travels 40 m horizontally and rises `150/5=30` m vertically, so its length is
`sqrt(40^2+30^2)=50` m. Five turns give `5*50=250` m.
Equivalently, unroll all five turns consecutively: `L=sqrt((5*40)^2+150^2)=250` m.
In general, `L=sqrt(H^2+(N*C)^2)` for a uniform helix of height H, circumference C and N turns.

## בדיקה ומקרי גבול

שתי דרכי החישוב חושבו בפועל באמצעות `Math.Sqrt` ב־PowerShell והחזירו 250 מטר.
העלייה לליפוף התקבלה כ־30 מטר ואורך הליפוף כ־50 מטר.

- ללא סיבובים, `N=0`, הנוסחה נותנת קטע אנכי באורך `H`.
- בגבול של אפס עלייה, `H=0`, מתקבל אורך מסלול `N*C`, כולל ספירה חוזרת של הסיבובים.

## טעויות נפוצות

- שימוש בגובה המלא, 150 מטר, עם היקף יחיד של 40 מטר.
- חיבור חשבוני של הגובה והמרחק ההיקפי במקום משפט פיתגורס.
- פירוש 40 מטר כרדיוס או כקוטר, כאשר נתון שזה ההיקף.

## תשובה קצרה לראיון

״אפרוס את מעטפת הגליל למישור; הפריסה שומרת על אורך החוט. בכל ליפוף החוט מתקדם 40 מטר סביב הגליל ועולה 30 מטר. לכן כל ליפוף הוא יתר במשולש 30–40–50, וחמישה ליפופים נותנים 250 מטר.״
