# PREP-338 — מונה שחור בן שמונה מצבים שסופר מאחת עד חמש

פתרון מוצע.

## he

נתונה קופסת מונה מודולו שמונה עם יציאה q[2:0]. השתמשו בה כדי להפיק במחזור את הערכים 1,2,3,4,5. כתבו טבלת מעברים, צמצמו את פענוח הבקרה והסבירו סכנת מימוש.

ממשק שנבחר לתרגיל: בכל חזית עולה load=1 טוען את d[2:0], אחרת המונה מתקדם מודולו שמונה. מותר להוסיף שערים וחיווט. אתחלו באמצעות טעינה של 1. מצב לא חוקי 0,6,7 חייב להתאושש ל־1 בחזית הבאה. דונו בנפרד בקופסה שמספקת רק clk ו־q, ובפענוח שמפעיל reset אסינכרוני.

1. מה צריך לקרות לאחר 5 כדי לדלג על 6 ו־7?
2. השתמשו באפשרות הטעינה של הקופסה במקום לשנות את השעון.
3. קבעו d=001 ופענחו את 5 וגם את המצבים הלא חוקיים. רשמו את כל שמונה השורות לפני צמצום.

### אותה קופסה, מחזור מקוצר
חברו d=001. בחזית האתחול כפו load=1. אחר כך הגדירו load=(q>=5). במצב 0 אין צורך לטעון, כי ההגדלה הרגילה מחזירה 1. טבלת המעברים לכל שמונת המצבים היא 0→1, 1→2, 2→3, 3→4, 4→5, 5→1, 6→1, 7→1. ב־1..4 הקופסה עצמה מבצעת את ההגדלה. לכן הרצף החוקי סגור ומכיל בדיוק חמישה מצבים.

אם נסמן q=(a,b,c), הפענוח המצומצם המלא הוא L=a AND (b OR c). המשוואה מסמנת בדיוק את 101,110,111. במצב 000 פלט ההגדלה 001 כבר נותן את ההתאוששות הנדרשת. אם מתחייבים לאתחול תקין ולשימור המצבים החוקיים, אפשר לבחור את המצבים הלא חוקיים כ־don’t care ולקבל L=a AND c. זה מאתר 5 במהלך המחזור, אך ב־6 הוא מאפשר מעבר ל־7 ורק אחר כך מתאושש. צמצום זה משנה את דרישת ההתאוששות ולכן אינו המימוש הראשי.

הבקרה חייבת להתייצב לפני חזית השעון לפי setup/hold של כניסת load. פענוח שמשתנה מעט אחרי החזית תקין כאשר עומדים באילוצים האלה. לעומת זאת חיבור אותו פענוח ל־reset אסינכרוני עלול לייצר פעימות שווא במעברים מרובי סיביות, וגם יש לבדוק רוחב reset, recovery ו־removal. החזרת המונה ל־0 מוסיפה 0 לרצף אם הפלט אמור להיות q עצמו.

אם הקופסה חושפת רק clk ו־q ומתקדמת חופשי, שום פונקציה צירופית קבועה f(q) אינה יכולה להפיק רצף בעל מחזור יסודי חמש. מכיוון ש־q חוזר אחרי שמונה חזיתות, גם f(q) חוזר אחרי שמונה. נדרשת אפשרות לטעון/לאפס בסנכרון, או זיכרון ובקרה חיצוניים שמשנים את החוזה. חמישה מצבים דורשים לפחות שלוש סיביות קידוד, אך אין כאן הוכחת מינימום שערים.

```python
"""Synchronous-load modulo-eight box, reused without changing its internals."""


def load_decode(q):
    if type(q) is not int or not 0 <= q < 8:
        raise ValueError("q must be a three-bit unsigned value")
    a, b, c = (q >> 2) & 1, (q >> 1) & 1, q & 1
    return a & (b | c)


def step(q, initialize=False):
    load = load_decode(q) or initialize
    return 1 if load else (q + 1) & 7


def reduced_legal_cycle_decode(q):
    return ((q >> 2) & 1) & (q & 1)
```

## en

A black-box modulo-eight counter exposes q[2:0]. Reuse it to emit the repeating values 1,2,3,4,5. Give its transition table, simplify the control decode and explain an implementation hazard.

Chosen interface: on each rising edge load=1 loads d[2:0]; otherwise the box increments modulo eight. Gates and wiring may be added. Initialize by loading 1. Illegal states 0,6,7 must recover to 1 on the next edge. Separately discuss a box exposing only clk/q and a decoded asynchronous reset.

1. What must happen after five to skip six and seven?
2. Use the box load capability while retaining the original clock.
3. Tie d to 001 and decode five plus illegal states. Write all eight rows before minimizing.

### Reuse the state and shorten its cycle
Tie d=001. Force load=1 for initialization, then use load=(q>=5). State zero naturally increments to one and needs no load. The complete transition table is 0→1, 1→2, 2→3, 3→4, 4→5, 5→1, 6→1, 7→1. For 1..4 the supplied counter performs the increment. Induction gives exactly the closed five-state legal cycle.

Write q=(a,b,c). A simplified complete decoder is L=a AND (b OR c), selecting exactly 101,110,111; 000 recovers by normal increment. If valid initialization and continued legal operation are promised, treating illegal codes as don’t-cares permits L=a AND c. This detects five on the legal cycle but lets six advance to seven before recovery. That reduced decoder changes the required recovery behavior and is therefore a separate variant.

Meet setup/hold at load before the shared rising edge. A decoded asynchronous reset can glitch during multi-bit output transitions and also requires valid reset width, recovery and removal. Resetting to zero would introduce zero if q itself is the required output.

With only clk/q and a free-running modulo-eight box, a memoryless f(q) repeats after eight edges. It cannot have fundamental period five. Synchronous load/reset access or additional external state/control is required. Five states require at least three binary state bits. The decoder is an explicit realization without a global gate-minimum claim.

```python
"""Synchronous-load modulo-eight box, reused without changing its internals."""


def load_decode(q):
    if type(q) is not int or not 0 <= q < 8:
        raise ValueError("q must be a three-bit unsigned value")
    a, b, c = (q >> 2) & 1, (q >> 1) & 1, q & 1
    return a & (b | c)


def step(q, initialize=False):
    load = load_decode(q) or initialize
    return 1 if load else (q + 1) & 7


def reduced_legal_cycle_decode(q):
    return ((q >> 2) & 1) & (q & 1)
```

[Executable model](../solutions/prep_338_hardware1115.py)
[Checks](../checks/check_hardware1115.py)
[Results](../checks/hardware1115-verification.json)

[Private source](../sources/2026-11-15-batch20-01.png)
[he diagram](../diagrams/prep-338-given-nov15-he.png)
[en diagram](../diagrams/prep-338-given-nov15-en.png)
[he diagram](../diagrams/prep-338-solution-nov15-he.png)
[en diagram](../diagrams/prep-338-solution-nov15-en.png)
