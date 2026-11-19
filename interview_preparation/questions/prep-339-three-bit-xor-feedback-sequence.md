# PREP-339 — אוגר הזזה בן שלוש סיביות עם משוב XOR

פתרון מוצע.

## he

בשרטוט נתון אוגר S0,S1,S2 שמתחיל ב־001, כאשר y=S2. בכל חזית עולה S0 מקבל S1 XOR S2, ‏S1 מקבל את S0 הישן ו־S2 מקבל את S1 הישן. ציירו את המצבים ואת y לפני החזית הראשונה ואחרי כל אחת משבע החזיתות הבאות. מצאו את המחזור והסבירו את התנהגות מצב 000. כל הסיביות מתעדכנות יחד.

1. עקבו אחרי סדר הסיביות כפי שמופיע בשרטוט.
2. ערך כל כניסה מחושב מן המצב הישן; אין לעדכן במקום משמאל לימין.
3. לאחר 001 מתקבל 100, ולאחריו 010. המשיכו עד שהמצב חוזר.

### מעקב אחר שלושה ערכים ישנים
המשוואות הן S0′=S1 XOR S2, ‏S1′=S0, ‏S2′=S1. לכן עבור מספר חזיתות k=0..7 נקבל

| k | S0 S1 S2 | y |
|---|---|---|
|0|001|1|
|1|100|0|
|2|010|0|
|3|101|1|
|4|110|0|
|5|111|1|
|6|011|1|
|7|001|1|

שבעה מצבים שונים עוברים לפני החזרה, ולכן המחזור מן האתחול הוא שבע חזיתות. גם רצף y מחזורי באורך שבע, מפני שאינו קבוע ושבע הוא ראשוני. סדרת המחזור לפני החזרה היא 1,0,0,1,0,1,1. לא מוסיפים את y של k=7 פעמיים כשכותבים מחזור אחד.

המצב 000 עובר לעצמו. אף מצב לא־אפס אינו נכנס אליו: אם המצב הבא אפס, אז S0=S1=0 וגם S1 XOR S2=0 ולכן S2=0. שבעת המצבים הלא־אפסיים שנמנו הם כל השאר. זו הוכחת התקופה של המימוש המסוים. שלושה FF ושער XOR מממשים אותו; החלפת כיוון ההזזה או נקודות המשוב משנה את הסדרה. האוגר אינו מקור אקראיות קריפטוגרפי.

```python
"""State order follows the printed S0,S1,S2 order."""


def step(state):
    if len(state) != 3 or any(bit not in (0, 1) for bit in state):
        raise ValueError("three binary stages are required")
    s0, s1, s2 = state
    return s1 ^ s2, s0, s1


def trace(edges, initial=(0, 0, 1)):
    if edges < 0:
        raise ValueError("nonnegative edge count required")
    state = tuple(initial)
    rows = [(0, state, state[2])]
    for edge in range(1, edges + 1):
        state = step(state)
        rows.append((edge, state, state[2]))
    return rows
```

## en

The illustrated register has state S0,S1,S2 initially 001 and output y=S2. On each rising edge S0 receives S1 XOR S2, S1 receives the old S0, and S2 receives the old S1. List state and y before the first edge and after the next seven edges, find the period and explain state 000. All stages update simultaneously.

1. Keep the bit ordering printed in the figure.
2. Compute every next bit from the old state, without in-place left-to-right updates.
3. 001 becomes 100 and then 010. Continue until the initial state returns.

### Compute all inputs from the old state
The equations are S0′=S1 XOR S2, S1′=S0 and S2′=S1. For edge counts k=0..7 the state/output pairs are

| k | S0 S1 S2 | y |
|---|---|---|
|0|001|1|
|1|100|0|
|2|010|0|
|3|101|1|
|4|110|0|
|5|111|1|
|6|011|1|
|7|001|1|

Seven different states occur before the return, establishing a seven-edge period. The y period is also seven because the sequence is nonconstant and seven is prime. One cycle is 1,0,0,1,0,1,1. Do not duplicate the repeated k=7 sample when listing one cycle.

000 is a fixed point. If the next state is zero, the shift equations give S0=S1=0 and the XOR then gives S2=0, so no nonzero state enters zero. The seven listed states exhaust the remaining codes. Three DFFs and one XOR realize this specific recurrence; reversing shift direction or changing taps changes the sequence. This is a deterministic sequence generator.

```python
"""State order follows the printed S0,S1,S2 order."""


def step(state):
    if len(state) != 3 or any(bit not in (0, 1) for bit in state):
        raise ValueError("three binary stages are required")
    s0, s1, s2 = state
    return s1 ^ s2, s0, s1


def trace(edges, initial=(0, 0, 1)):
    if edges < 0:
        raise ValueError("nonnegative edge count required")
    state = tuple(initial)
    rows = [(0, state, state[2])]
    for edge in range(1, edges + 1):
        state = step(state)
        rows.append((edge, state, state[2]))
    return rows
```

[Executable model](../solutions/prep_339_hardware1115.py)
[Checks](../checks/check_hardware1115.py)
[Results](../checks/hardware1115-verification.json)

[Private source](../sources/2026-11-15-batch20-02.png)
[he diagram](../diagrams/prep-339-given-nov15-he.png)
[en diagram](../diagrams/prep-339-given-nov15-en.png)
[he diagram](../diagrams/prep-339-solution-nov15-he.png)
[en diagram](../diagrams/prep-339-solution-nov15-en.png)
