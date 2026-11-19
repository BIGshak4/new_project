# PREP-030 — additional sections

## he

רכיב מיון מקבל שני ערכים `(a,b)` ומחזיר `(max(a,b), min(a,b))` בסדר עליון־תחתון.

א. בנו ממנו רשת הממיינת ארבעה מספרים בסדר יורד.

ב. ייתכן שאין תקלה, וייתכן שרכיב אחד בלבד תקול באופן קבוע. רכיב תקול מחזיר תמיד `(b,a)` — החלפה של הכניסות ללא מיון. מותר להזין וקטורים של ארבעה מספרים ולקרוא את כל ארבעת הפלטים. מצאו בדיקות שמבדילות בין מערכת תקינה לבין כל מיקום אפשרי של התקלה ברשת שבניתם.

### וריאציה עם שני סוגי תקלה לבחירה
השתמשו באותה רשת בת חמישה תאים. לכל היותר תא אחד תקול. מראש ידוע שהתקלה הקבועה בו היא אחת משתיים, אך לא ידוע איזו: העברה ישרה (a,b) או הצלבה (b,a), ללא תלות בגודל. ייתכן שהמערכת תקינה. מצאו סדרת בדיקות שקובעים מראש ומזהה גם את התא וגם את סוג התקלה באמצעות ארבע היציאות בלבד. השתמשו בערכים שונים והראו מינימום מספר בדיקות קבועות לרשת הזאת.
**הנחות ומספור:** נבחר מוצא ממוין בסדר יורד כדי להתאים לרכיב שבצילום: הכניסה העליונה a והתחתונה b, והמוצא העליון Max(a,b), התחתון Min(a,b). נסמן ארבעה חוטים מלמעלה למטה w1,w2,w3,w4. כשרכיב תקול הוא תמיד מחזיר (b,a) במקום (max,min), ללא תלות בערכים. זו אינה תקלה ש״מחליפה בין פלטי max/min״ ואינה זהות (a,b); מודל שגוי כאן משנה את הפתרון. התקלה קבועה, יש אפס או רכיב תקול אחד, ניתן להזין כל ארבעה מספרים ולראות את כל ארבעת הפלטים, והקלטים בני השוואה בסדר מלא (ללא NaN). אין צורך בגישה לחוטים פנימיים. מותר שערוך חוטים והסתעפויות כרגיל בתרשים קומבינטורי.

**א. בניית המערכת — חמישה רכיבים בשלוש שכבות:**

| שכבה | רכיב | זוג החוטים | פעולה תקינה |
|---|---|---|---|
| 1 | C1 | w1,w2 | הגדול ל־w1, הקטן ל־w2 |
| 1 | C2 | w3,w4 | הגדול ל־w3, הקטן ל־w4 |
| 2 | C3 | w1,w3 | הגדול ל־w1, הקטן ל־w3 |
| 2 | C4 | w2,w4 | הגדול ל־w2, הקטן ל־w4 |
| 3 | C5 | w2,w3 | הגדול ל־w2, הקטן ל־w3 |

C1,C2 פועלים במקביל, וגם C3,C4. הפלט הוא (w1,w2,w3,w4) בסדר יורד. אחרי השכבה הראשונה w1,w3 הם גדולי הזוגות ו־w2,w4 קטני הזוגות. C3 ממקם את המקסימום הכללי ב־w1, ו־C4 ממקם את המינימום הכללי ב־w4. נשאר רק למיין את שני האמצעיים, ו־C5 עושה זאת. במודל רשת השוואה, חמישה רכיבים הם מינימום: ארבעה מספרים שונים מאפשרים 4!=24 סדרים יחסיים, וכל השוואה מספקת עד ביט אחד; ארבע השוואות נותנות לכל היותר 16 תוצאות, ולכן לא מספיקות. חמישה מספיקים כפי שנבנה. שלוש שכבות הן מינימום לרשת של ארבעה חוטים עם השוואות מקבילות על זוגות זרים: בשתי שכבות אפשר לכל היותר ארבע השוואות. אין זו טענת שטח/השהיה פיזית של רכיב נתון.

**ב. וקטור בדיקה אחד מספיק:** הזן (4,3,2,1) על w1..w4. כל ערך שונה והמערך כבר ממוין בסדר הרצוי. ברשת תקינה כל רכיב מקבל זוג יורד ולכן אינו מחליף אותו. רכיב תקול, לעומת זאת, מחליף אותו בהכרח. עקוב אחרי ההשפעה עד הפלט, גם דרך הרכיבים התקינים שבהמשך.

| מצב | פלט מלא |
|---|---|
| הכול תקין | (4,3,2,1) |
| C1 תקול | (3,4,2,1) |
| C2 תקול | (4,3,1,2) |
| C3 תקול | (2,4,3,1) |
| C4 תקול | (4,2,1,3) |
| C5 תקול | (4,2,3,1) |

כל שש החתימות שונות, ולכן וקטור יחיד גם מגלה שיש תקלה וגם מזהה את הרכיב. זה המינימום במספר וקטורי הבדיקה: בלי אף מדידה לא ניתן להבדיל בין שש האפשרויות. קביעה זו מותנית ברשת ובמודל התקלה המפורשים, ואינה אומרת שכל רשת מיון ארבעה ערכים תיתן אותן חתימות. לכל קלט יורד ממש a>b>c>d מתקבלות אותן תבניות מיקומים; הערכים 4,3,2,1 הם בחירה פשוטה.

**דוגמה למעקב:** אם C3 תקול, אחרי השכבה הראשונה עדיין (4,3,2,1). C3 מחליף את w1,w3, ומתקבל (2,3,4,1). C4 התקין משווה 3 ו־1 ולכן אינו משנה. C5 משווה את האמצעיים 3,4 ומחליף אותם: הפלט (2,4,3,1), חתימה ייחודית ל־C3. חשוב לא להסתפק במוצא של הרכיב התקול, כי צריך להמשיך להעביר את הערכים דרך שאר הרשת.

**איך מגיעים לוקטור?** מגדירים קודם מה התקלה עושה, בוחרים קלט שמעורר הבדל לעומת הרכיב התקין, ואז בודקים שההבדל מגיע לפלט ושאינו זהה לחתימה של תקלה אחרת. קלט עולה a<b גורם לרכיב תקין להחליף בדיוק כמו התקול ולכן עלול להסתיר אותו. ערכים שווים גם עלולים להסתיר החלפה. מתחילים בירידה ממש, יוצרים טבלה של כל ששת המצבים ובודקים ייחודיות. ״הפלט לא ממוין״ לבדו מזהה חריגה אך לא בהכרח איזה רכיב; כאן משתמשים ברביעיית הערכים המלאה. פלט שאינו בטבלה, עבור קלט הבדיקה המדויק, מצביע שהנחותינו אינן מתאימות (למשל תקלה אחרת, כמה תקלות, חיווט שונה), ולא על אבחנה מאולצת.

**בדיקות:** הרשת התקינה הושוותה למיון עבור 256 קלטים עם ערכים −1,0,1,2 וכל 16 הקלטים הבינאריים. שש חתימות התקלה נבדקו במדויק; נבדקו כל 24 סדרי הקלטים השונים ושלושה וקטורים יורדים עם ערכים אחרים. הוכחת המינימום ברכיבים היא חסם ההשוואות; מינימום וקטורים נובע מקיום וקטור מבחין יחיד. זו בדיקת מודל פונקציונלי בפייתון ולא סימולציית HDL, תזמון פיזי או בדיקת כל מודלי התקלות האפשריים.

החיווט נשמר C1(1,2),C2(3,4),C3(1,3),C4(2,4),C5(2,3), עם MAX על החוט בעל האינדקס הקטן. יש 11 השערות: תקינה ועוד חמישה מיקומים כפול שני מצבים. לכל השערה מריצים את שלושת הקלטים (1,2,3,4),(1,3,2,4),(4,3,2,1). טבלת החתימות המלאה מופיעה בשרטוט ובמודל. כל 11 שלשות הפלט שונות, ולכן שלוש בדיקות מספיקות. בתצפית אמת משווים את כל שלושת הווקטורים לשורה אחת בטבלה.

למינימום בדיקות קבועות, כל השוואה ברשת תלויה רק בסדר הערכים. קיימות 24 תמורות של ארבעה ערכים שונים. המודל מונה את חתימות כל 11 ההשערות לכל 24 התמורות ואת כל 276 זוגות הבדיקות. באף בדיקה יחידה או זוג קבוע אין 11 חתימות שונות. בשלישייה המוצעת יש. לכן המינימום הוא שלוש בדיקות קבועות בתחום הזה. גם ערכים שווים אינם משפרים את המינימום: ניתן לחדד כל קלט עם שוויונות לסדר קפדני, ואחר כך למפות את הפלט חזרה באמצעות פונקציה מונוטונית; חידוד יכול לשמר או להוסיף מידע, לא להקטין אותו.

הוכחת המינימום מתייחסת לבדיקות שקובעים מראש. בדיקות אדפטיביות דורשות ניתוח עץ החלטות נפרד. מודל התקלה המקורי של הצלבה בלבד עדיין נפתר בווקטור אחד כפי שנכתב בחלק הקודם; מספר הבדיקות גדל כאן בגלל הרחבת קבוצת התקלות. פלט שלא מתאים לאף שורה מצביע על הפרת הנחות כגון חיווט שונה או כמה תקלות.

```python
"""Five MAX/MIN cells with either straight or crossing single faults."""
from itertools import combinations, permutations

NETWORK = ((0, 1), (2, 3), (0, 2), (1, 3), (1, 2))
HYPOTHESES = (None,) + tuple((index, mode) for index in range(5)
                           for mode in ("straight", "cross"))
TESTS = ((1, 2, 3, 4), (1, 3, 2, 4), (4, 3, 2, 1))


def run(values, hypothesis=None):
    wires = list(values)
    if len(wires) != 4 or hypothesis not in HYPOTHESES:
        raise ValueError("four wires and one declared hypothesis required")
    for index, (upper, lower) in enumerate(NETWORK):
        a, b = wires[upper], wires[lower]
        if hypothesis == (index, "straight"):
            pair = a, b
        elif hypothesis == (index, "cross"):
            pair = b, a
        else:
            pair = (a, b) if a >= b else (b, a)
        wires[upper], wires[lower] = pair
    return tuple(wires)


def signatures():
    return {hypothesis: tuple(run(test, hypothesis) for test in TESTS)
            for hypothesis in HYPOTHESES}


def diagnose(observed):
    observed = tuple(map(tuple, observed))
    matches = [hypothesis for hypothesis, signature in signatures().items()
               if observed == signature]
    if len(matches) != 1:
        raise ValueError("observation violates this single-fault model")
    return matches[0]


def minimum_fixed_test_count():
    probes = tuple(permutations((1, 2, 3, 4)))
    outputs = [tuple(run(probe, hypothesis) for hypothesis in HYPOTHESES)
               for probe in probes]
    assert all(len(set(row)) < 11 for row in outputs)
    assert all(len(set(zip(outputs[i], outputs[j]))) < 11
               for i, j in combinations(range(24), 2))
    assert len(set(signatures().values())) == 11
    return 3
```

## en

A sorting cell receives `(a,b)` and outputs `(max(a,b), min(a,b))` from top to bottom.

A. Build a four-input network with descending output.

B. There may be no fault or one permanently faulty cell. A faulty cell always outputs `(b,a)`: an unconditional swap of its raw inputs, without sorting. You may apply four-value input vectors and observe all four outputs. Find tests distinguishing the healthy system from every possible faulty-cell location in your network.

### Variant with either of two fault modes
Use the same five-cell network. At most one cell is faulty, permanently passing its inputs straight through as (a,b), or crossing them as (b,a), independently of their sizes. The mode is unknown and the network may be healthy. Find a fixed, nonadaptive test sequence identifying both the cell and mode from all four final outputs, using distinct values. Establish the minimum number of predetermined tests for this network.
Use descending output, matching the pictured cell: upper output max(a,b), lower min(a,b). Wires w1..w4 run top to bottom. A faulty cell unconditionally outputs (b,a), not swapped sorted outputs or straight-through identity. Assume at most one permanent fault, total-order values, arbitrary inputs, and observation of all four final outputs without internal probes.

Network: layer 1 C1(w1,w2),C2(w3,w4); layer 2 C3(w1,w3),C4(w2,w4); layer 3 C5(w2,w3). Each healthy cell puts the larger value on the smaller-indexed wire. After pair sorting, C3 selects the global max, C4 the global min, and C5 sorts the middle values. Five comparators are minimal because 4!=24 distinct orders require at least ceil(log2 24)=5 comparisons. Three layers are minimal for ordinary disjoint-pair sorting-network layers: two layers allow at most four comparisons. This is not physical cell-area/timing optimality.

One test vector (4,3,2,1) suffices for full diagnosis. Final outputs by hypothesis: healthy (4,3,2,1); C1 (3,4,2,1); C2 (4,3,1,2); C3 (2,4,3,1); C4 (4,2,1,3); C5 (4,2,3,1). All six signatures differ. The healthy descending input does not need swapping at any cell; any forced crossing activates a fault. Continue propagating through later healthy cells, which may change the visible pattern. For C3, its crossing yields (2,3,4,1), then C5 sorts the middle into (2,4,3,1). Zero tests cannot identify six possibilities, so one is minimum for this chosen network/fault model. Any four strictly descending values yield corresponding positional patterns.

Equal values or an ordering where healthy sorting already crosses can mask faults. Full output values, not just a sorted/not-sorted Boolean, are used. Unlisted output under the exact test vector indicates a violated model rather than a forced diagnosis. Checked 256 signed/repeated-value inputs and all 16 binary inputs for sorting; all six fault outputs, all 24 distinct ordering classes and three other strictly descending vectors. Functional Python model only; no HDL or physical fault experiment.

Keep C1(1,2), C2(3,4), C3(1,3), C4(2,4), C5(2,3), with MAX on the smaller-indexed wire. There are eleven hypotheses: healthy plus five fault locations in two modes. Apply (1,2,3,4), (1,3,2,4), and (4,3,2,1). The complete signature table is shown in the diagram and executable model. All eleven triples of output vectors differ, so three tests suffice. Match the complete observed triple to one table row.

For a minimum fixed test count, only input order matters. Enumerate the 24 permutations of four distinct ranks, each under all eleven hypotheses, and all 276 pairs of tests. No single test or pair gives eleven different signatures. The proposed triple does. Thus three is the minimum nonadaptive count in this model. Ties cannot improve it: refine each tied input into a strict order and monotonically map the resulting outputs back to the tied ranks. Refinement preserves or adds information, so a distinguishing tied pair would imply a distinguishing strict pair.

This optimum is for predetermined tests. Adaptive decision-tree depth needs separate analysis. The earlier crossing-only contract still admits its one-vector diagnosis; the extra tests here address the expanded fault set. An observed triple absent from the table indicates assumptions such as topology or single-fault behavior were violated.

```python
"""Five MAX/MIN cells with either straight or crossing single faults."""
from itertools import combinations, permutations

NETWORK = ((0, 1), (2, 3), (0, 2), (1, 3), (1, 2))
HYPOTHESES = (None,) + tuple((index, mode) for index in range(5)
                           for mode in ("straight", "cross"))
TESTS = ((1, 2, 3, 4), (1, 3, 2, 4), (4, 3, 2, 1))


def run(values, hypothesis=None):
    wires = list(values)
    if len(wires) != 4 or hypothesis not in HYPOTHESES:
        raise ValueError("four wires and one declared hypothesis required")
    for index, (upper, lower) in enumerate(NETWORK):
        a, b = wires[upper], wires[lower]
        if hypothesis == (index, "straight"):
            pair = a, b
        elif hypothesis == (index, "cross"):
            pair = b, a
        else:
            pair = (a, b) if a >= b else (b, a)
        wires[upper], wires[lower] = pair
    return tuple(wires)


def signatures():
    return {hypothesis: tuple(run(test, hypothesis) for test in TESTS)
            for hypothesis in HYPOTHESES}


def diagnose(observed):
    observed = tuple(map(tuple, observed))
    matches = [hypothesis for hypothesis, signature in signatures().items()
               if observed == signature]
    if len(matches) != 1:
        raise ValueError("observation violates this single-fault model")
    return matches[0]


def minimum_fixed_test_count():
    probes = tuple(permutations((1, 2, 3, 4)))
    outputs = [tuple(run(probe, hypothesis) for hypothesis in HYPOTHESES)
               for probe in probes]
    assert all(len(set(row)) < 11 for row in outputs)
    assert all(len(set(zip(outputs[i], outputs[j]))) < 11
               for i, j in combinations(range(24), 2))
    assert len(set(signatures().values())) == 11
    return 3
```


[Private source](../sources/2026-11-15-batch20-20.png)
[he diagram](../diagrams/prep-030-two-fault-modes-nov15-he.png)
[en diagram](../diagrams/prep-030-two-fault-modes-nov15-en.png)
