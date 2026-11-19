# PREP-176 — Setup ו־Hold — חלון יציבות ושני כיווני תקלה

פתרון מוצע.

[מקור פנימי](../sources/2026-11-15-batch20b-03.png)

## he

הסבירו מה הם setup ו־hold של Flip-Flop, ומה עושים כדי לפתור הפרת setup. הציגו נתיב בין שני אוגרים, משוואות זמן וההשפעה של skew. הסבירו גם מה צריך לבדוק אחרי התיקון.

נבחר נתיב חד־מחזורי בין אוגרים באותו שעון ובאותה קוטביות חזית. T הוא המחזור; skew=s פירושו שחזית הלכידה מגיעה מאוחר יותר ב־s ביחס לחזית השיגור. זמני CQ ולוגיקה ניתנים במינימום ובמקסימום, ונפריד אי־ודאות setup ו־hold. אין כאן CDC, שעונים לא קשורים או הרשאה להכריז multicycle ללא שינוי חוזה פונקציונלי.

### שלושה מסלולי נתונים המתכנסים ל־OR
שלושה אוגרי שיגור R0,R1,R2 מזינים ענפי לוגיקה שונים, שיציאותיהם נכנסות לשער OR ולאוגר קליטה C. נתחו setup ו־hold לכל ענף ואת השפעת skew חיובי ושלילי. הוסיפו השהיה משותפת אחרי ה־OR והשוו לשינוי מחזור השעון.

דוגמה שנבחרה, בננו־שניות ובאי־ודאות אפס. T=2, זמן הגעת שעון C הוא 0.10, setup=0.15, hold=0.10. לכל אוגר CQmin=0.05,CQmax=0.10. זמני שעוני השיגור הם 0,0.10,−0.05. השהיות לוגיקה min/max הכוללות גם את שער ה־OR הן בהתאמה (0.05,1.40),(0.08,1.30),(0.10,1.60). כל מסלול בר־רגישות כאשר שתי כניסות ה־OR האחרות אפס.

1. setup שואל אם הנתון הגיע מספיק מוקדם לפני חזית הלכידה; hold שואל אם נתון חדש מגיע מוקדם מדי אחריה. התייחסו לכל אוגר שיגור כמקור למסלול נפרד, עם אותו אוגר קליטה.
2. ל־setup השתמשו ב־CQ ולוגיקה מקסימליים; ל־hold במינימליים. מה קורה כשהלכידה מאוחרת יותר? הגדירו לכל ענף s_i=Cclk−Lclk_i. מינימום נתונים קובע hold ומקסימום קובע setup.
3. הדרישות הן CQmax+Dmax+setup+Us ≤ T+s, ו־CQmin+Dmin ≥ hold+Uh+s. הגדלת T משפיעה רק על הראשונה. השוו את שלושת מרווחי ה־hold. השהיה אחרי ה־OR מתווספת לכל ענף, ואילו הגדלת T משנה רק את setup.

### חלון שבו הכניסה צריכה להישאר יציבה
setup הוא משך הזמן הנדרש שבו D יציב לפני החזית הפעילה; hold הוא משך היציבות הנדרש אחריה. אלו מגבלות תא ותנאי עבודה, לא מספר קבוע לכל אוגר. הפרה עשויה ליצור דגימה שגויה או מטא־יציבות, אך התוצאה אינה חייבת להיכשל באותו אופן בכל הרצה.

נמקם חזית שיגור בזמן 0. הנתון המאוחר ביותר מגיע ב־CQmax+Dmax; חזית הלכידה הבאה היא T+s. לכן:

```text
setup_slack = T + s - Us - setup - CQmax - Dmax
hold_slack  = CQmin + Dmin - s - Uh - hold
```

slack שלילי הוא הפרה במודל. ל־hold מסתכלים על חזית הלכידה של אותו מחזור: הנתון החדש שנשלח ב־0 לא רשאי להגיע לפני s+hold+Uh. skew חיובי נותן יותר זמן לנתון המאוחר, אבל מאריך את החלון שבו הנתון הישן חייב להישמר. זו הסיבה שהוא עוזר ל־setup ומקשה על hold. סימן skew חייב להיות מוגדר לפני שימוש בנוסחה.

לדוגמה T=2 ns, CQmax=0.2 ns, Dmax=1.7 ns, setup=0.15 ns, Us=0.03 ns, s=0 נותנים setup slack=−0.08 ns. CQmin=0.08 ns, Dmin=0.05 ns, hold=0.1 ns, Uh=0.02 ns נותנים hold slack=0.01 ns. הגדלת המחזור ב־0.1 ns מתקנת את setup במודל ואינה משנה את hold.

### מתקנים את הסיבה, ואז בודקים את שני הקצוות
אפשר לקצר עומק לוגיקה, לפשט ביטויים, לבחור תאים מהירים יותר, להקטין fanout, לשנות placement/routing או לחזק נתיב כשהעומס הוא הגורם. כל בחירה עולה בשטח, הספק או חיווט. צינור נוסף מחלק נתיב אבל משנה latency ודורש התאמת מסלולים, בקרה ופרוטוקול. הורדת תדר עוזרת ל־setup אם מותר לשנות ביצועים. useful skew דורש תכנון שעון מבוקר ובדיקה בכל הפינות.

אין להוסיף השהיית data כדי לפתור setup; השהיית hold מכוונת לתקלה אחרת. אין לסמן false path או multicycle רק כדי להעלים דוח: החריגה צריכה לנבוע מהפונקציה ומהפרוטוקול. לאחר תיקון בודקים setup וגם hold, כל פינות PVT, אי־ודאות ושעונים, וכן פונקציונליות אם שונתה ארכיטקטורה. הגדלת T לבדה אינה פותרת הפרת hold של הנתיב הזה.

[AMD מתארת בדיקת timing slack כחלק מסגירת תזמון](https://docs.amd.com/r/en-US/ug1388-acap-system-integration-validation-methodology/Reviewing-Timing-Slack). משוואות החלון כאן נגזרו מחזיתות ההגדרה. 54 קומבינציות נבדקו מול זמני הגעה מוחלטים ומול שינוי תקופה; זה אינו STA signoff.

```python
"""Same-clock, same-edge, one-cycle path budgets in one consistent time unit."""

from math import isfinite


def timing_slacks(
    period, cq_min, cq_max, logic_min, logic_max, setup, hold, skew=0, setup_uncertainty=0, hold_uncertainty=0
):
    values = (
        period,
        cq_min,
        cq_max,
        logic_min,
        logic_max,
        setup,
        hold,
        skew,
        setup_uncertainty,
        hold_uncertainty,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("finite timing values required")
    if (
        period <= 0
        or min(cq_min, logic_min, setup, hold, setup_uncertainty, hold_uncertainty) < 0
        or cq_max < cq_min
        or logic_max < logic_min
    ):
        raise ValueError("invalid timing contract")
    # Positive skew means that the capture clock arrives LATER.
    setup_slack = period + skew - setup_uncertainty - setup - cq_max - logic_max
    hold_slack = cq_min + logic_min - skew - hold_uncertainty - hold
    return setup_slack, hold_slack
```


נסמן dmin_i,dmax_i את כל לוגיקת הנתונים בענף, כולל ה־OR. משוואות הענף הן setup_i=T+s_i−setup−CQmax_i−dmax_i ו־hold_i=CQmin_i+dmin_i−s_i−hold. אין לבחור ענף איטי אחד ולדלג על המהיר.

| ענף | skew | setup slack | hold slack |
|---|---|---|---|
|R0|0.10|0.45|−0.10|
|R1|0.00|0.45|0.03|
|R2|0.15|0.30|−0.10|

הדוגמה עומדת ב־setup ונכשלת ב־hold בענפים R0,R2. תוספת השהיה קבועה של 0.10 ns אחרי ה־OR מביאה את hold לאפס בשני הענפים האלה ומקטינה כל מרווח setup ב־0.10 ns. זהו גבול במודל. בתא אמיתי משתמשים בתוספות מינימום ומקסימום מאופיינות ובמרווחי אי־ודאות, ובודקים שוב את כל הפינות. הגדלת T ב־0.10 ns משפרת כל setup באותה כמות ומשאירה hold ללא שינוי.

skew חיובי כפי שהוגדר כאן עוזר ל־setup ומקשה על hold. במערכת מרובת שיגורים הוא שונה בכל ענף, גם אם כל האוגרים משתמשים במקור שעון משותף. ה־OR עשוי לייצר גליצ'ים כשכמה כניסות משתנות. משוואות הקצה הן גבולות סטטיים למסלולים בני רגישות, ואינן הוכחת היעדר גליצ'ים או מטסטביליות.

```python
"""Three sensitizable OR paths use separate signed capture-minus-launch skews."""
from math import isfinite


def budgets(period, capture, setup, hold, paths):
    if len(paths) != 3:
        raise ValueError("exactly three launch paths required")
    common = (period, capture, setup, hold)
    if not all(isfinite(v) for v in common) or period <= 0 or min(setup, hold) < 0:
        raise ValueError("invalid common timing values")
    result = []
    for launch, cq_min, cq_max, logic_min, logic_max in paths:
        values = (launch, cq_min, cq_max, logic_min, logic_max)
        if (not all(isfinite(v) for v in values) or min(cq_min, logic_min) < 0
                or cq_max < cq_min or logic_max < logic_min):
            raise ValueError("invalid path bounds")
        skew = capture - launch
        result.append({"skew": skew,
                       "setup": period + skew - setup - cq_max - logic_max,
                       "hold": cq_min + logic_min - skew - hold})
    return result
```

## en

Define flip-flop setup and hold and explain ways to fix a setup violation. Draw a register-to-register path, give timing equations and explain clock skew. What must be rechecked after a repair?

Choose a one-cycle path with the same clock and edge polarity. T is the period; positive skew s means capture arrives later than launch. CQ and logic delays have minimum/maximum bounds; setup and hold uncertainties are separate. CDC, unrelated clocks and unsupported multicycle exceptions are outside this contract.

### Three data paths reconverging at OR
Launch registers R0,R1,R2 feed separate logic branches whose outputs drive an OR and capture register C. Analyze setup and hold separately for every branch and explain positive/negative skew. Compare inserting common data delay after OR with increasing the period.

Chosen zero-uncertainty example, in ns. T=2, C clock arrival 0.10, setup=0.15, hold=0.10. Every launch register has CQmin=0.05,CQmax=0.10. Launch clock arrivals are 0,0.10,−0.05. Branch minimum/maximum data delays, including the OR, are (0.05,1.40),(0.08,1.30),(0.10,1.60). Each branch is sensitizable with the other OR inputs zero.

1. Setup asks whether data arrives early enough before capture; hold asks whether new data arrives too soon afterward. Treat every launch register as the source of a separate path with one shared capture register.
2. Use maximum CQ/logic for setup and minimum delays for hold. What does later capture do to each? For branch i define s_i=Cclk−Lclk_i. Earliest data sets hold and latest data sets setup.
3. Require CQmax+Dmax+setup+Us ≤ T+s and CQmin+Dmin ≥ hold+Uh+s. Increasing T helps only the first. Compare the three hold slacks. Delay after OR affects every branch, while increasing T changes setup alone.

### Data must be stable around the capture edge
Setup is the required stable-D interval before the active capture edge; hold is the stable interval afterward. Values depend on the cell and operating conditions. A violation can cause an incorrect sample or metastability; it does not imply one deterministic failure on every run.

Set launch time to zero. Latest arrival is CQmax+Dmax and next capture is T+s:

```text
setup_slack = T + s - Us - setup - CQmax - Dmax
hold_slack  = CQmin + Dmin - s - Uh - hold
```

Negative slack violates the model. Hold compares new data from the launch at zero with the same-cycle capture edge: arrival must be no earlier than s+hold+Uh. Positive skew allows more late-data time but extends how long old data must remain. It helps setup and hurts hold under this sign convention.

For T=2 ns, CQmax=0.2 ns, Dmax=1.7 ns, setup=0.15 ns, Us=0.03 ns, s=0, setup slack is−0.08 ns. With CQmin=0.08 ns, Dmin=0.05 ns, hold=0.1 ns, Uh=0.02 ns, hold slack is 0.01 ns. Increasing T by 0.1 ns fixes this setup budget without changing hold.

### Repair the cause, then recheck both ends
Reduce logic depth, simplify expressions, use faster cells, reduce fanout or improve placement/routing. Buffering may help a load-dominated path but adds its own delay. Choices trade area, power and wires. Pipelining divides a path but changes latency and requires aligned paths, control and protocol. Lowering frequency helps setup when the performance contract permits it. Useful skew requires controlled clock design and all-corner checking.

Adding data delay does not fix setup; hold-delay insertion addresses the other direction. False-path or multicycle exceptions require a functional/protocol basis, not merely an unpleasant report. Recheck setup and hold, operating corners, clock uncertainty and functional changes. Increasing period alone does not fix hold on this path.

[AMD discusses slack review in timing closure](https://docs.amd.com/r/en-US/ug1388-acap-system-integration-validation-methodology/Reviewing-Timing-Slack). The window equations above follow the defined edge times.54 parameter combinations were checked against absolute arrivals and period changes; this is not STA signoff.

```python
"""Same-clock, same-edge, one-cycle path budgets in one consistent time unit."""

from math import isfinite


def timing_slacks(
    period, cq_min, cq_max, logic_min, logic_max, setup, hold, skew=0, setup_uncertainty=0, hold_uncertainty=0
):
    values = (
        period,
        cq_min,
        cq_max,
        logic_min,
        logic_max,
        setup,
        hold,
        skew,
        setup_uncertainty,
        hold_uncertainty,
    )
    if not all(isfinite(value) for value in values):
        raise ValueError("finite timing values required")
    if (
        period <= 0
        or min(cq_min, logic_min, setup, hold, setup_uncertainty, hold_uncertainty) < 0
        or cq_max < cq_min
        or logic_max < logic_min
    ):
        raise ValueError("invalid timing contract")
    # Positive skew means that the capture clock arrives LATER.
    setup_slack = period + skew - setup_uncertainty - setup - cq_max - logic_max
    hold_slack = cq_min + logic_min - skew - hold_uncertainty - hold
    return setup_slack, hold_slack
```


Let dmin_i,dmax_i include all branch data logic and the OR. The branch equations are setup_i=T+s_i−setup−CQmax_i−dmax_i and hold_i=CQmin_i+dmin_i−s_i−hold. One slow path cannot stand in for the fastest path.

| Branch | skew | setup slack | hold slack |
|---|---|---|---|
|R0|0.10|0.45|−0.10|
|R1|0.00|0.45|0.03|
|R2|0.15|0.30|−0.10|

The example passes setup and fails hold on R0,R2. Adding exactly 0.10 ns of common data delay after OR moves their hold slack to zero and reduces every setup slack by 0.10 ns. Zero is the model boundary. A real cell uses characterized added minimum/maximum delays, uncertainties and all-corner rechecks. Increasing T by 0.10 ns instead improves every setup slack by that amount and leaves hold unchanged.

Positive capture-minus-launch skew helps setup and hurts hold. Different launch arrivals create different skews despite a shared clock source. Reconvergent OR inputs can glitch. Endpoint equations bound sensitizable static paths and do not establish glitch freedom or metastability immunity.

```python
"""Three sensitizable OR paths use separate signed capture-minus-launch skews."""
from math import isfinite


def budgets(period, capture, setup, hold, paths):
    if len(paths) != 3:
        raise ValueError("exactly three launch paths required")
    common = (period, capture, setup, hold)
    if not all(isfinite(v) for v in common) or period <= 0 or min(setup, hold) < 0:
        raise ValueError("invalid common timing values")
    result = []
    for launch, cq_min, cq_max, logic_min, logic_max in paths:
        values = (launch, cq_min, cq_max, logic_min, logic_max)
        if (not all(isfinite(v) for v in values) or min(cq_min, logic_min) < 0
                or cq_max < cq_min or logic_max < logic_min):
            raise ValueError("invalid path bounds")
        skew = capture - launch
        result.append({"skew": skew,
                       "setup": period + skew - setup - cq_max - logic_max,
                       "hold": cq_min + logic_min - skew - hold})
    return result
```

[Executable reference](../solutions/three_launch_timing1115b.py)
[Checks](../checks/check_sta1115b.py)
[Verification](../checks/sta1115b-verification.json)
[he diagram](../diagrams/prep-176-sta-given-1115b-he.png)
[en diagram](../diagrams/prep-176-sta-given-1115b-en.png)
[he diagram](../diagrams/prep-176-sta-solution-1115b-he.png)
[en diagram](../diagrams/prep-176-sta-solution-1115b-en.png)
