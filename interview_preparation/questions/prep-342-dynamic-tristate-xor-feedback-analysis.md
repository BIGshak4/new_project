# PREP-342 — ניתוח משוב עם שני חוצצים תלת־מצביים

פתרון מוצע.

## he

נתון השרטוט בעל שני חוצצים ומשוב. לצורך ניתוח חד־משמעי, השתמשו ברשת הערוכה המצוירת כאן: T1 מעביר b לצומת n כאשר a=0; ‏T2 מעביר n ל־y כאשר e=a AND (b XOR y). בחוצץ כבוי היציאה Z. שני הצמתים n,y מחזיקים ערך בקיבול אידאלי כשהם מנותקים, לפרק הזמן של הניסוי בלבד. אין משוב סטטי שמחדש מטען.

כתבו טבלת פעולות עבור a,b והערך הקודם של y. האם קיימת טבלת אמת רגילה y=f(a,b)? עקבו אחרי a העולה מ־0 ל־1 כאשר b יציב סביב המעבר, והשוו למצב שבו b משתנה במהלך a=1. הסבירו אילו הנחות נדרשות כדי לפרש זאת כאחסון דינמי. שרטוט המקור אינו מגדיר סמלי חוצצים או נתוני תזמון באופן מלא; זו פרשנות נבחרת ללימוד.

1. צומת שמחובר ל־Z אינו מקבל בהכרח אפס.
2. כאשר a=0 מי מתעדכן ומי שומר את הערך הקודם?
3. בסיום שלב a=0 מתקיים n=b. בעלייה, אם y שונה מ־b נפתח החוצץ השני ומעתיק את n.

### הטבלה מתארת פעולה עם זיכרון
נסמן q את y לפני ההתייצבות. כאשר a=0, ‏T1 פעיל ולכן n←b, ואילו e=0 ולכן y מחזיק q. כאשר a=1, ‏T1 כבוי ולכן n נשמר. אם b=q, אז e=0 ו־y נשאר q. אם b≠q, אז e=1 ו־T2 מנסה להציב y=n. משום ש־e תלוי ב־y, יש לעדכן אותו שוב אחרי השינוי.

| a | b | q | n | פעולת y |
|---|---|---|---|---|
|0|0 או 1|0 או 1|מתעדכן ל־b|החזקת q|
|1|0|0|נשמר|החזקת 0|
|1|0|1|נשמר|העברת n|
|1|1|0|נשמר|העברת n|
|1|1|1|נשמר|החזקת 1|

הטבלה אינה y=f(a,b): ב־a=0 אפשר לשמור y=0 או y=1 עבור אותו b. יש צורך בהיסטוריה ובמצב האתחול. בלי הנחת שמירת מטען, צומת מנותק הוא Z או ערך חשמלי בלתי מובטח, ולכן אין להחליף אותו ב־FF אידאלי ללא הסבר.

נניח שהשלב הנמוך ארוך דיו לקביעת n=b, וש־b נשאר יציב סביב עליית a. לפני העלייה n=b. אם y=b אין צורך בעדכון. אם y≠b, החוצץ השני נפתח ו־y עובר ל־n=b; אז XOR מתאפס והחוצץ נסגר. במודל זה y מקבל את b של המעבר. במהלך a=1, ‏n נשאר הדגימה; שינוי מאוחר של b עשוי לפתוח או לסגור את T2 אך אינו משנה את הנתון שהוא מעביר, ולכן y נשאר n אחרי דגימה תקינה.

לדוגמה התחלנו n=0,y=0. ב־a=0,b=1 מתקבל n=1,y=0. בעליית a מתקבל y=1 ו־T2 נסגר. אם b יורד אחר כך, T2 נפתח אך מעביר שוב n=1. רק השלב הנמוך הבא יכול לעדכן n.

במימוש ממשי יש קיבולים סופיים, דליפה, charge sharing, זמני פתיחה וסגירה, רוחב פולס משוב ו־setup/hold. סימני Z לבדם אינם מוכיחים רכיב אחסון סטטי תקין. נדרש תא דינמי מתוכנן ובדיקת תזמון/מטען. המודל כאן בודק לוגיקה וערכים שמורים בלבד.

```python
"""Ideal retained binary nodes, not a transistor/charge simulation."""


def settle(a, b, n, y):
    if any(bit not in (0, 1) for bit in (a, b, n, y)):
        raise ValueError("binary model requires known initial node values")
    if not a:
        n = b
    elif b ^ y:
        y = n
    enable = a & (b ^ y)
    return n, y, enable
```

## en

Analyze the illustrated feedback circuit using this explicit edited netlist: T1 drives b onto node n when a=0. T2 drives n onto y when e=a AND (b XOR y). A disabled buffer outputs Z. Nodes n and y retain their last binary values on ideal capacitance while undriven, only for this experiment; no static keeper restores charge.

Give the action table for a,b and previous y. Is y=f(a,b) an ordinary combinational truth table? Trace a rising from zero to one while b is stable around the transition, then compare a change of b during a=1. Explain the assumptions required for a dynamic-storage interpretation. The original sketch leaves buffer symbols and timing incomplete; this exercise declares one chosen interpretation.

1. A node driven by Z does not automatically become zero.
2. For a=0, which node updates and which retains its prior value?
3. At the end of a=0, n=b. On the rise, unequal y/b enables the second buffer to copy n.

### The table describes stateful actions
Let q be y before settling. When a=0, T1 is enabled so n←b; e=0 leaves y retaining q. When a=1, T1 is disabled and n retains its value. If b=q then e=0 and y stays q. If b differs from q then T2 drives y=n. Recompute e after y changes because the enable itself depends on feedback.

| a | b | q | n | y action |
|---|---|---|---|---|
|0|0 or 1|0 or 1|load b|retain q|
|1|0|0|retain|retain 0|
|1|0|1|retain|drive n|
|1|1|0|retain|drive n|
|1|1|1|retain|retain 1|

There is no memoryless y=f(a,b): during a=0 the same b can coexist with either retained y. History and initialization are needed. Without the declared charge-retention abstraction, an undriven node is Z or physically unspecified. It cannot silently be treated as an ideal static FF.

Assume the low phase is long enough to establish n=b, and b stays stable around a rising. Then n=b before the rise. If y=b, no update is needed. Otherwise T2 enables and drives y=n=b, clearing the XOR and disabling T2. In this ideal model y therefore samples b at the rise. During a=1, n retains that sample; a later b change can alter the enable but the driven datum remains n, so y stays at its sampled value after a valid acquisition.

For example start n=0,y=0. With a=0,b=1, n becomes one while y stays zero. At a rising, y becomes one and T2 closes. If b later falls, T2 opens but again drives the stored n=1. Only the next low phase updates n.

Physical use requires finite retention, leakage, charge sharing, buffer enable timing, feedback-pulse width and setup/hold analysis. A Z symbol alone establishes no robust static storage. A designed dynamic cell and timing/charge verification are needed. The executable model checks only ideal logic with retained binary values.

```python
"""Ideal retained binary nodes, not a transistor/charge simulation."""


def settle(a, b, n, y):
    if any(bit not in (0, 1) for bit in (a, b, n, y)):
        raise ValueError("binary model requires known initial node values")
    if not a:
        n = b
    elif b ^ y:
        y = n
    enable = a & (b ^ y)
    return n, y, enable
```

[Executable model](../solutions/prep_342_hardware1115.py)
[Checks](../checks/check_hardware1115.py)
[Results](../checks/hardware1115-verification.json)

[Private source](../sources/2026-11-15-batch20-01.png)
[he diagram](../diagrams/prep-342-given-nov15-he.png)
[en diagram](../diagrams/prep-342-given-nov15-en.png)
[he diagram](../diagrams/prep-342-solution-nov15-he.png)
[en diagram](../diagrams/prep-342-solution-nov15-en.png)
