"""52 short reasoning cards and 260 bilingual draft quiz cases.

Authored explanations and computed finite-case evidence; no human-review claim.
This producer writes only its three owned content files.
"""

from __future__ import annotations

import itertools
import json
import math
import re
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "backend/seeds/duel_quiz_batches"
SHORT = ROOT / "apps/web/src/content/fundamentals-reasoning-400.json"


def p(he, en=None):
    return {
        lg: re.sub(r",(?=[A-Za-zא-ת])", ", ", str(value))
        for lg, value in (("he", he), ("en", he if en is None else en))
    }


def matchings(edges):
    return [a for a in itertools.product(*edges) if len(set(a)) == len(a)]


def make(n, refs, title, takeaway, cases):
    assert len(cases) == 5
    card = dict(
        id=f"quick-sw-{n}",
        topic="reasoning",
        interviewIds=[f"PREP-{i:03d}" for i in refs],
        title=p(*title),
        prompt=cases[0]["prompt"],
        answer={lg: cases[0]["good"][lg] + ". " + cases[0]["explanation"][lg] for lg in ("he", "en")},
        takeaway=p(*takeaway),
    )
    rows, checks = [], []
    for v, c in enumerate(cases, 1):
        opts = [c["good"], *c["bad"]]
        assert len(opts) == 4 and all(len({o[lg] for o in opts}) == 4 for lg in ("he", "en")), (n, v)
        shift = (n + v) % 4
        opts = opts[-shift:] + opts[:-shift] if shift else opts
        key = f"quick-sw-{n}-v{v}"
        rows.append(
            dict(
                key=key,
                source_key=card["id"],
                variant=v,
                topic="reasoning",
                status="draft",
                prompt=c["prompt"],
                choices=opts,
                correct=shift,
                explanation=c["explanation"],
            )
        )
        checks.append(
            dict(
                key=key,
                method=c["method"],
                inputs=c["inputs"],
                expected=c["good"],
                value=c["value"],
                professional_review="pending",
            )
        )
    return card, rows, checks


def case(prompt, value, explanation, data, method, choices=None):
    if choices is None:
        good = p(value)
        candidates = (
            [F(1, 2), F(1, 3), F(2, 3), F(1, 4), F(3, 4), F(0), F(1)]
            if isinstance(value, F) and 0 < value < 1
            else [value + 1, value - 1, value + 2, value * 2, value + 3, 0]
        )
        bad = []
        for x in candidates:
            if x != value and x >= 0 and p(x) not in bad:
                bad.append(p(x))
            if len(bad) == 3:
                break
    else:
        good, bad = choices[value], [choices[i] for i in range(4) if i != value]
    return dict(
        prompt=p(*prompt),
        good=good,
        bad=bad,
        explanation=p(*explanation),
        inputs=json.loads(json.dumps(data)),
        method=method,
        value=str(value),
    )


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def polygon_class(points):
    n = len(points)
    turns = [cross(points[i], points[(i + 1) % n], points[(i + 2) % n]) for i in range(n)]
    area = sum(
        points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1] for i in range(n)
    )
    if not area:
        return "degenerate"
    for i in range(n):
        for j in range(i + 1, n):
            if j in (i, (i + 1) % n) or i == (j + 1) % n:
                continue
            a, b, c, d = points[i], points[(i + 1) % n], points[j], points[(j + 1) % n]
            if cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0:
                return "crossing"
    nonzero = {1 if x > 0 else -1 for x in turns if x}
    return "concave" if len(nonzero) > 1 else "weak" if 0 in turns else "strict"


def degree_worlds(prefix):
    n = len(prefix) + 1
    pairs = list(itertools.combinations(range(n), 2))
    values = set()
    for edges in itertools.product((0, 1), repeat=len(pairs)):
        deg = [0] * n
        for (a, b), present in zip(pairs, edges, strict=True):
            deg[a] += present
            deg[b] += present
        if deg[:-1] == prefix:
            values.add(deg[-1])
    return values


def build_bundle():
    cards, rows, checks = [], [], []

    def add(*args):
        c, r, k = make(*args)
        cards.append(c)
        rows.extend(r)
        checks.extend(k)

    cases = []
    for edges, old in [
        ([[0, 1], [0]], [0]),
        ([[0, 1], [1, 2], [0]], [0, 1]),
        ([[0, 1], [1, 2], [2, 3], [0]], [0, 1, 2]),
        ([[0, 2], [1], [0]], [0, 1]),
        ([[0, 1, 2], [1, 2], [0]], [0, 1]),
    ]:
        solutions = matchings(edges)
        best = min(sum(a[i] != x for i, x in enumerate(old)) for a in solutions)
        cases.append(
            case(
                (
                    f"כל אדם צריך פריט שונה. רשימות הפריטים המותרים הן {edges}; ההקצאות הנוכחיות לאנשים הראשונים הן {old}, והאחרון ממתין. כמה הקצאות קיימות לפחות חייבות להשתנות כדי לשרת את כולם?",
                    f"Each person needs a different item. Allowed-item lists are {edges}; current assignments for the first people are {old},and the last waits. What minimum number of existing assignments must change to serve everyone?",
                ),
                best,
                (
                    "אפשר להעביר אדם לפריט חלופי ולפנות את הפריט הדרוש לאחר. ממזערים שינויים רק בין הקצאות מלאות חוקיות.",
                    "An alternative item can free the required item for another person. Minimize changes among legal complete assignments.",
                ),
                dict(edges=edges, old=old),
                "enumerate injective complete assignments and relocation cost",
            )
        )
    add(
        126,
        [148],
        ("לפעמים צריך לפנות מקום", "Sometimes an earlier choice must move"),
        (
            "הקצאה קיימת אינה אילוץ קבוע אם מותר לשנותה כדי לפתוח מסלול לאחר.",
            "A previous assignment can move along a reassignment path when the rules allow it.",
        ),
        cases,
    )

    cases = []
    for edges in [
        [[0, 1], [0, 1], [0, 1]],
        [[0], [0], [1], [1]],
        [[0, 1], [1, 2], [0, 2]],
        [[0], [0], [0], [1]],
        [[0, 1], [0, 1], [0, 1], [0, 1]],
    ]:
        deficit = max(
            len(s) - len(set().union(*(set(edges[i]) for i in s)))
            for k in range(1, len(edges) + 1)
            for s in itertools.combinations(range(len(edges)), k)
        )
        cases.append(
            case(
                (
                    f"אנשים צריכים פריטים שונים, ורשימות האפשרויות שלהם הן {edges}. לפי קבוצת האנשים עם המחסור הגדול ביותר בפריטים זמינים, כמה אנשים לפחות בהכרח יישארו ללא פריט?",
                    f"People need distinct items and have allowed lists {edges}. Using the subset with the largest shortage of available items, how many people must remain unserved at minimum?",
                ),
                deficit,
                (
                    "לקבוצה בת k אנשים עם רק m פריטים אפשריים יש מחסור של לפחות k−m. בודקים גם תתי־קבוצות, לא רק את האיחוד הכולל.",
                    "A subset of k people with only m possible items has shortage at least k−m. Inspect subsets, not only the total union.",
                ),
                dict(edges=edges),
                "maximum Hall subset deficit",
            )
        )
    add(
        127,
        [148],
        ("מחסור יכול להסתתר בתת־קבוצה", "A shortage can hide in a subset"),
        (
            "מספיק פריטים בסך הכול אינם מבטיחים מספיק אפשרויות לכל קבוצת אנשים.",
            "Enough items overall do not ensure enough options for every subset of people.",
        ),
        cases,
    )

    cases = []
    for jobs in [
        [(0, 4, 2), (1, 3, 3)],
        [(0, 2, 4), (3, 5, 3)],
        [(0, 5, 1), (1, 4, 2), (2, 3, 3)],
        [(0, 3, 2), (1, 4, 2), (2, 5, 1)],
        [(0, 6, 2), (2, 4, 5), (3, 5, 1)],
    ]:
        peak = max(sum(w for a, b, w in jobs if a <= t < b) for t in range(max(b for _, b, _ in jobs)))
        cases.append(
            case(
                (
                    f"משימות (התחלה,סיום,עובדים): {jobs}. משימה פעילה מההתחלה ועד לפני הסיום ודורשת עובדים לכל משכה. עובדים זהים ופנויים יכולים לעבור בין משימות. כמה עובדים נדרשים בשעת העומס?",
                    f"Jobs (start,end,workers): {jobs}. Each is active from start until just before end and needs workers throughout. Workers are interchangeable and reusable. How many are required at the busiest time?",
                ),
                peak,
                (
                    "סוכמים את הדרישות של המשימות הפעילות יחד, ולא רק את מספר המשימות או את כל הדרישות לאורך היום.",
                    "Add simultaneous worker demands, rather than counting jobs or summing demands across the entire day.",
                ),
                dict(jobs=jobs),
                "enumerate occupancy demand at every unit interval",
            )
        )
    add(
        128,
        [149],
        ("משימה אחת יכולה לדרוש כמה עובדים", "One job can require several workers"),
        (
            "עומס משוקלל הוא סכום הדרישות הפעילות, ולא ספירת האירועים בלבד.",
            "Weighted concurrency sums active demands rather than merely counting events.",
        ),
        cases,
    )

    cases = []
    for need, have in [
        ([2, 0], [1, 1]),
        ([1, 1], [2, 0]),
        ([2, 1], [2, 1]),
        ([0, 3], [2, 1]),
        ([2, 2], [3, 0]),
    ]:
        missing = sum(max(0, n - h) for n, h in zip(need, have, strict=True))
        cases.append(
            case(
                (
                    f"שתי מיומנויות A ו־B אינן ניתנות להחלפה. משימות בו־זמניות צריכות {need} עובדים בהתאמה; זמינים {have}, וכל עובד שייך למיומנות אחת בלבד. כמה עובדים מתאימים נוספים נדרשים?",
                    f"Skills A and B are not interchangeable. Simultaneous jobs need {need} workers respectively; available counts are {have}, each worker holding only one skill. How many additional appropriately skilled workers are needed?",
                ),
                missing,
                (
                    "עודף במיומנות אחת אינו מפצה על מחסור באחרת. חסם לפי מספר העובדים הכולל מניח שהם ניתנים להחלפה.",
                    "A surplus of one skill cannot repair a shortage of another. A total-headcount sufficiency claim assumes interchangeable workers.",
                ),
                dict(need=need, have=have),
                "sum independent skill deficits",
            )
        )
    add(
        129,
        [149],
        ("מספיק אנשים אך לא מספיק מיומנויות", "Enough people but the wrong skills"),
        (
            "חסם עומס הופך להבטחת ביצוע רק כשהנחות הכשירות וההחלפה מתקיימות.",
            "A load bound guarantees feasibility only under the required qualification and interchangeability assumptions.",
        ),
        cases,
    )

    modal = [
        p("אין כמות יחידה שנקבעת", "No unique count is determined"),
        p("500"),
        p("400"),
        p("אין חבילה העומדת בדרישות", "No compliant pack exists"),
    ]
    cases = []
    for allowed in [[400, 500], [500], [400], [], [200, 250, 500]]:
        value = 3 if not allowed else 1 if allowed == [500] else 2 if allowed == [400] else 0
        cases.append(
            case(
                (
                    f"דרישות המוצר מאפשרות בדיוק את כמויות הדפים {allowed}. איזו כמות יחידה ניתן להסיק עבור חבילה שעומדת בדרישות,אם בכלל? אין מפרט נוסף.",
                    f"The product requirements permit exactly these sheet counts: {allowed}. What unique count can be inferred for a compliant pack,if any? There is no additional specification.",
                ),
                value,
                (
                    "מחליטים לפי המפרט הנתון. אין להמציא כמות מקובלת; רשימה ריקה אינה מפרט בר־מימוש.",
                    "Use the stated requirements rather than inventing a customary pack size. An empty allowed set is infeasible.",
                ),
                dict(allowed=allowed),
                "finite specification uniquely inferred value",
                modal,
            )
        )
    add(
        130,
        [159],
        ("מפרט לפני בדיקת קבלה", "A specification before acceptance"),
        (
            "בדיקת קבלה צריכה קריטריון נתון; מנהג משוער אינו דרישה.",
            "Acceptance testing needs an actual criterion; an assumed convention is not a requirement.",
        ),
        cases,
    )

    cases = []
    for low, high in [(209, 211), (296, 298), (8, 12), (19, 20), (4, 4)]:
        good = (low - 1, low, high, high + 1)
        choices = [
            p(str(good)),
            p(str((low, low, high, high))),
            p(str((low - 2, low - 1, high + 1, high + 2))),
            p(str((low, low + 1, high, high))),
        ]
        cases.append(
            case(
                (
                    f"אורך דף נמדד ביחידות שלמות. המפרט מקבל כל ערך בין {low} ל־{high}, כולל הקצוות. איזו רביעיית בדיקות מכסה לכל גבול את הערך המותר ואת השכן האסור הקרוב?",
                    f"A sheet dimension uses integer units. Values from {low} through {high}, inclusive, are accepted. Which four-test tuple covers each allowed boundary and its nearest forbidden neighbor?",
                ),
                0,
                (
                    "לכל גבול בודקים את הקצה עצמו ואת היחידה הצמודה שמחוץ לטווח. אין להחליף אותם בדגימות פנימיות בלבד.",
                    "Test each boundary itself and its immediately adjacent outside value, rather than sampling only interior values.",
                ),
                dict(low=low, high=high),
                "inclusive integer boundary neighborhoods",
                choices,
            )
        )
    add(
        131,
        [159],
        ("שני צדדים לכל גבול", "Both sides of each boundary"),
        (
            "בדיקות גבול מכסות גם צד מותר וגם צד אסור של תנאי הקבלה.",
            "Boundary tests cover the accepted and rejected sides of the acceptance condition.",
        ),
        cases,
    )

    verdict = [
        p("עומד בדרישה", "Accept"),
        p("נכשל בדרישה", "Reject"),
        p("אין הכרעה בטווח האי־ודאות", "Inconclusive under uncertainty"),
        p("לא נדרשת מדידה", "No measurement required"),
    ]
    cases = []
    for limit, reading, error in [(10, 10, 1), (10, 8, 1), (10, 12, 1), (20, 19, 1), (20, 21, 2)]:
        v = 0 if reading + error <= limit else 1 if reading - error > limit else 2
        cases.append(
            case(
                (
                    f"נדרש אורך שאינו עולה על {limit}. מכשיר מדווח {reading} עם שגיאה חסומה של ±{error}; כל ערך בטווח אפשרי. איזו החלטה ודאית מותרת?",
                    f"Length must not exceed {limit}. An instrument reports {reading} with bounded error ±{error}; every value in that interval is possible. Which certain decision is justified?",
                ),
                v,
                (
                    "מאשרים רק אם כל הטווח מותר, ודוחים בוודאות רק אם כולו אסור. טווח שחוצה את הסף דורש הכרעה נוספת.",
                    "Accept only if the entire interval passes; reject with certainty only if it entirely fails. A straddling interval is inconclusive.",
                ),
                dict(limit=limit, reading=reading, error=error),
                "quantify over every possible measurement value",
                verdict,
            )
        )
    add(
        132,
        [159],
        ("המדידה אינה ערך מדויק", "A measurement is not exact"),
        (
            "החלטה ודאית צריכה להתאים לכל הערכים המותרים על ידי שגיאת המדידה.",
            "A certain verdict must hold for every value permitted by measurement error.",
        ),
        cases,
    )

    cases = []
    for expected, observed in [
        ([1, 0], [1, 1]),
        ([1, 0], [1, 0]),
        ([1, 0], [0, 0]),
        ([1, 0], [0, 1]),
        ([1, 0, 0], [1, 1, 1]),
    ]:
        bad = sum(a != b for a, b in zip(expected, observed, strict=True))
        cases.append(
            case(
                (
                    f"בודקים דוגמאות בקרה שידוע אם עליהן לעבור: {expected}, כאשר 1 הוא עובר ו־0 נכשל. הבודק החזיר {observed}. כמה תוצאות בקרה סותרות את הידוע?",
                    f"Control samples have known expected verdicts {expected}, where 1 means pass and 0 fail. The tester returns {observed}. How many control results contradict their known truth?",
                ),
                bad,
                (
                    "גם קבלה של דוגמה פגומה היא כשל של הבודק. מעבר של דוגמה תקינה לבדו אינו מוכיח שהבדיקה מגלה פגמים.",
                    "Accepting a known defective sample is also a tester failure. Passing a good sample alone does not establish defect detection.",
                ),
                dict(expected=expected, observed=observed),
                "compare positive and negative control outcomes",
            )
        )
    add(
        133,
        [159],
        ("גם דוגמה פגומה היא בקרה", "A defective sample is a control too"),
        (
            "בדקו שהבדיקה מצליחה לדחות כשל ידוע, ולא רק לקבל מוצר תקין.",
            "Check rejection of a known defect as well as acceptance of a known good product.",
        ),
        cases,
    )

    cases = []
    for total, covers in [
        (3, [[0], [0], [1]]),
        (4, [[0, 1], [2, 3]]),
        (4, [[0], [1], [1]]),
        (2, [[0, 1], [0, 1]]),
        (5, [[0, 2], [2, 4]]),
    ]:
        missing = total - len(set().union(*(set(x) for x in covers)))
        cases.append(
            case(
                (
                    f"יש {total} דרישות שמספריהן מתחילים ב־0. הבדיקות מכסות את קבוצות הדרישות {covers}. כמה דרישות לא כוסו, גם אם כל הבדיקות עברו?",
                    f"There are {total} requirements numbered from 0. Tests cover these requirement sets: {covers}. How many requirements remain uncovered even if every test passes?",
                ),
                missing,
                (
                    "סופרים דרישות שונות שכוסו, לא את מספר הבדיקות. בדיקות חוזרות לאותו סעיף אינן מכסות סעיף חסר.",
                    "Count distinct covered requirements, not the number of tests. Repeated checks of one requirement do not cover a missing one.",
                ),
                dict(total=total, covers=covers),
                "requirement-to-test coverage union",
            )
        )
    add(
        134,
        [159],
        ("הרבה בדיקות אינן בהכרח כיסוי", "Many tests do not imply coverage"),
        (
            "קשרו כל בדיקה לדרישה; כמות בדיקות אינה תחליף למפת כיסוי.",
            "Trace each test to a requirement; test count does not replace a coverage map.",
        ),
        cases,
    )

    cases = []
    for pairs in [
        [(1, 0), (1, 1)],
        [(0, 0), (1, 1)],
        [(0, 1), (1, 0)],
        [(1, 1), (0, 1), (0, 0)],
        [(1, 0), (0, 0), (1, 0)],
    ]:
        bad = sum(a != b for a, b in pairs)
        cases.append(
            case(
                (
                    f"בדיקת חבילה אמורה להיות אדישה לסדר הדפים. בכל זוג מוצגות תוצאות לפני ואחרי שינוי סדר של אותם דפים: {pairs}; 1 הוא עובר. כמה זוגות מפרים את האינווריאנט?",
                    f"A pack test must ignore sheet order. Each pair gives results before and after reordering the same sheets: {pairs}; 1 means pass. How many pairs violate this invariant?",
                ),
                bad,
                (
                    "תוצאה ששונה לאחר שינוי שאינו אמור להשפיע חושפת חוסר עקביות, גם בלי לדעת איזו תוצאה היא הנכונה.",
                    "A verdict changed by an irrelevant transformation exposes inconsistency even without knowing which verdict is correct.",
                ),
                dict(pairs=pairs),
                "metamorphic permutation-invariance check",
            )
        )
    add(
        135,
        [159],
        ("לגלות כשל בלי לדעת את התשובה", "Find inconsistency without the true answer"),
        (
            "שינוי שאמור לשמר תוצאה מספק בדיקת עקביות גם ללא אורקל מלא.",
            "An outcome-preserving transformation provides a consistency check without a complete oracle.",
        ),
        cases,
    )

    cases = []
    for a, b, q in [(100, 200, 7), (80, 80, 10), (60, 150, 0), (90, 40, 4), (30, 70, 6)]:
        cases.append(
            case(
                (
                    f"כוס A התחילה עם {a} מ״ל אדום וכוס B עם {b} מ״ל כחול. העבירו נפח כלשהו מ־A ל־B ואז אותו נפח בחזרה, ללא אובדן. בסוף ב־A יש {q} מ״ל כחול. כמה אדום יש ב־B?",
                    f"A initially held {a} ml red and B {b} ml blue. Transfer some volume A→B,then the same volume back,without loss. A finally contains {q} ml blue. How much red is in B?",
                ),
                q,
                (
                    "נפח A חזר לערכו המקורי. כל מיליליטר כחול שנשאר בה מחליף מיליליטר אדום שנשאר בכוס השנייה.",
                    "A returns to its original volume. Each blue millilitre remaining there replaces one red millilitre left in the other cup.",
                ),
                dict(a=a, b=b, q=q),
                "final-volume and color conservation",
            )
        )
    add(
        136,
        [143],
        ("נפח זר מול נפח זר", "Foreign volume against foreign volume"),
        (
            "נפחים זרים שווים נובעים משימור נפח סופי, גם בלי ערבוב אחיד.",
            "Equal foreign volumes follow from restored cup volume,even without perfect mixing.",
        ),
        cases,
    )

    fraction_order = [
        p("השיעור ב־A גדול יותר", "The fraction in A is larger"),
        p("השיעור ב־B גדול יותר", "The fraction in B is larger"),
        p("שיעורים חיוביים שווים", "Equal positive fractions"),
        p("שניהם אפס", "Both are zero"),
    ]
    cases = []
    for a, b, q in [(100, 200, 5), (200, 100, 5), (100, 100, 5), (100, 200, 0), (30, 90, 3)]:
        v = 3 if q == 0 else 0 if a < b else 1 if b < a else 2
        cases.append(
            case(
                (
                    f"אחרי העברת כפות הלוך וחזור נשארו {q} מ״ל זרים בכל כוס. הנפחים הסופיים הם A={a},B={b} מ״ל. השוו את שיעור הנוזל הזר בכל כוס.",
                    f"After equal spoon transfers out and back,each cup holds {q} ml foreign liquid. Final volumes are A={a},B={b} ml. Compare their foreign-liquid fractions.",
                ),
                v,
                (
                    "מחלקים אותה כמות זרה בנפח הכולל של כל כוס. שוויון בכמות אינו מבטיח שוויון בשיעור.",
                    "Divide the same foreign amount by each cup's total volume. Equal amounts need not mean equal fractions.",
                ),
                dict(a=a, b=b, q=q),
                "compare exact foreign-volume fractions",
                fraction_order,
            )
        )
    add(
        137,
        [143],
        ("אותה כמות אך שיעור אחר", "Same amount,different fraction"),
        (
            "בהשוואת שיעורים בדקו גם את המכנה ולא רק את הכמות המשותפת.",
            "When comparing fractions,check the denominator as well as the shared numerator.",
        ),
        cases,
    )

    speed_labels = [
        p("אפשר במהירות חזרה סופית חיובית", "Achievable with a finite positive return speed"),
        p("רק גבול כאשר המהירות שואפת לאינסוף", "Only approached as return speed tends to infinity"),
        p("מעל החסם ולכן בלתי אפשרי", "Above the upper bound and impossible"),
        p("כל מהירות חזרה חיובית מתאימה", "Every positive return speed works"),
    ]
    cases = []
    for u, g in [(10, 20), (10, 15), (10, 25), (10, 10), (10, 19)]:
        v = 0 if g < 2 * u else 1 if g == 2 * u else 2
        cases.append(
            case(
                (
                    f"נוסעים מרחק חיובי במהירות {u} וחוזרים אותו מרחק במהירות חיובית ללא עצירה. סווגו יעד של מהירות ממוצעת {g} לכל הנסיעה.",
                    f"Travel a positive distance at speed {u},then the same distance back at a positive speed,without stops. Classify a target whole-trip average of {g}.",
                ),
                v,
                (
                    "ההלוך כבר צורך זמן d/u. לחזרה סופית נדרש זמן חיובי נוסף, ולכן הממוצע קטן ממש מ־2u.",
                    "The outward leg already takes d/u. A finite return requires additional positive time,so the average is strictly below 2u.",
                ),
                dict(u=u, g=g),
                "strict total-time lower bound",
                speed_labels,
            )
        )
    add(
        138,
        [146],
        ("ממוצע שרק מתקרבים אליו", "An average only approached"),
        (
            "גבול מושג במגמה אינו בהכרח ערך שאפשר להשיג בפעולה סופית.",
            "A limiting value need not be attainable by a finite action.",
        ),
        cases,
    )

    cases = []
    for u, g in [(6, 8), (10, 12), (3, 4), (8, 12), (10, 5)]:
        needed = F(u * g, 2 * u - g)
        cases.append(
            case(
                (
                    f"מרחק ההלוך והחזור שווה ואין עצירות. מהירות ההלוך {u}, והמהירות הממוצעת המבוקשת {g}. איזו מהירות חזרה חיובית דרושה?",
                    f"Outward and return distances are equal,with no stops. Outward speed is {u} and the desired whole-trip average is {g}. What positive return speed is required?",
                ),
                needed,
                (
                    "משווים את זמן ההלוך והחזור לזמן הכולל המבוקש: v=u·g/(2u−g). אין לחשב 2g−u.",
                    "Equate total leg time with the target time: v=u·g/(2u−g). The arithmetic-mean shortcut 2g−u is invalid.",
                ),
                dict(u=u, g=g),
                "invert the total-distance divided by total-time equation",
            )
        )
    add(
        139,
        [146],
        ("לתכנן את מהירות החזרה", "Plan the return speed"),
        (
            "פתרו יעד ממוצע דרך תקציב הזמן שנותר, ולא דרך ממוצע חשבוני של מהירויות.",
            "Solve an average-speed target through remaining time,rather than arithmetic averaging of speeds.",
        ),
        cases,
    )

    cases = []
    for hot, cold, cc, cm in [(80, 20, 3, 1), (80, 20, 1, 3), (90, 10, 1, 1), (70, 30, 2, 1), (60, 20, 1, 4)]:
        result = F(cc * hot + cm * cold, cc + cm)
        cases.append(
            case(
                (
                    f"מערבבים מיד,ללא אובדן חום: קפה בטמפרטורה {hot} וקיבול חום {cc}, וחלב בטמפרטורה {cold} וקיבול חום {cm}. מה טמפרטורת התערובת? הקיבולים קבועים.",
                    f"Mix instantaneously without heat loss: coffee at {hot} with heat capacity {cc},and milk at {cold} with heat capacity {cm}. What is the mixture temperature? Capacities are constant.",
                ),
                result,
                (
                    "משמרים אנרגיה: טמפרטורת התערובת היא סכום מכפלות הטמפרטורות בקיבולים,חלקי סכום הקיבולים.",
                    "Conserve energy: divide the sum of temperature-times-capacity products by total heat capacity.",
                ),
                dict(hot=hot, cold=cold, cc=cc, cm=cm),
                "heat-capacity-weighted energy balance",
            )
        )
    add(
        140,
        [126],
        ("המשקל של כל טמפרטורה", "Each temperature has a weight"),
        (
            "ממוצע פיזיקלי משוקלל לפי הכמות שנשמרת; ממוצע פשוט דורש משקלים שווים.",
            "A physical average is weighted by the conserved quantity;simple averaging requires equal weights.",
        ),
        cases,
    )

    cooling = [
        p("להוסיף מוקדם נותן חם יותר", "Early addition is warmer"),
        p("להוסיף מאוחר נותן חם יותר", "Late addition is warmer"),
        p("התוצאה שווה", "Equal final temperature"),
        p("אין מספיק מידע", "Insufficient information"),
    ]
    cases = []
    for cc, cm, a, b in [(3, 1, 1, None), (3, 1, 1, 1), (3, 1, 1, F(3, 4)), (3, 1, 1, F(1, 2)), (1, 1, 2, 3)]:
        delta = None if b is None else b - F(cc, cc + cm) * a
        v = 3 if delta is None else 1 if delta > 0 else 0 if delta < 0 else 2
        cases.append(
            case(
                (
                    f"משווים הוספת חלב בתחילת דקה להוספתו בסופה. קיבולי החום הם קפה={cc},חלב={cm}; החלב נשמר בטמפרטורה קבועה. הקפה לבדו מתקרר {a} מעלות לדקה; התערובת {b if b is not None else 'לא ידוע'}. איזה סיום חם יותר?",
                    f"Compare adding milk before versus after one minute. Heat capacities: coffee={cc},milk={cm}; milk stays at fixed temperature. Coffee alone cools {a} degrees/minute; mixture rate is {b if b is not None else 'unknown'}. Which finishes warmer?",
                ),
                v,
                (
                    "משווים קירור של התערובת למשקל קירור הקפה לבדו בתערובת. בלי קצב התערובת לא ניתן להכריע; עצם הלינאריות אינה מגדירה אותו.",
                    "Compare mixture cooling with the coffee's weighted cooling contribution. Without the mixture rate,the comparison is undetermined;linearity alone does not specify it.",
                ),
                dict(cc=cc, cm=cm, a=a, b=None if b is None else str(b)),
                "compare two explicitly defined affine cooling schedules",
                cooling,
            )
        )
    add(
        141,
        [126],
        ("לינארי אינו מפרט קצב חדש", "Linear does not specify the new rate"),
        (
            "אחרי שינוי המערכת יש להגדיר מחדש את פרמטרי המודל, ולא רק לשמר את שם החוק.",
            "After changing a system,specify its new model parameters rather than retaining only the law's name.",
        ),
        cases,
    )

    cases = []
    for height, up, down in [(4, 3, 1), (3, 2, 1), (2, 3, 1), (5, 3, 1), (10, 2, 1)]:
        cycles = max(0, math.ceil(F(height - up, up - down)))
        time = 2 * cycles + F(height - cycles * (up - down), up)
        cases.append(
            case(
                (
                    f"מטפס מתחיל בגובה 0. במשך דקה הוא עולה במהירות {up} יחידות לדקה,ובדקת המנוחה יורד {down}. הדפוס חוזר,והתנועה רציפה. מתי בדקות ייגע לראשונה בגובה {height}? עוצרים מיד במגע.",
                    f"A climber starts at height 0,climbs at {up} units/minute for one minute,then slips {down} during a one-minute rest. The cycle repeats continuously. At what time in minutes first reach height {height}? Stop immediately at contact.",
                ),
                time,
                (
                    "סופרים מחזורים מלאים רק לפני העלייה האחרונה. בעלייה שבה נוגעים ביעד אין מנוחה נוספת,ואפשר להגיע באמצע הדקה.",
                    "Count full cycles only before the final ascent. No rest follows first contact,and the target may be reached partway through a minute.",
                ),
                dict(height=height, up=up, down=down),
                "piecewise-linear first-passage calculation",
            )
        )
    add(
        142,
        [129],
        ("עוצרים בזמן המגע הראשון", "Stop at the first contact"),
        (
            "יעד שמסיים תהליך מבטל את השלבים שהיו אמורים לבוא אחריו.",
            "A terminating target removes the stages that would otherwise follow it.",
        ),
        cases,
    )

    tick_options = [p("0"), p("1"), p("2"), p("אין מפגש בזמן שלם", "No integer-time meeting")]
    cases = []
    for left, right, a, b in [(0, 10, 2, 3), (0, 11, 2, 3), (1, 9, 2, 2), (3, 3, 1, 1), (0, 3, 2, 1)]:
        t = F(right - left, a + b)
        v = int(t) if t.denominator == 1 else 3
        cases.append(
            case(
                (
                    f"בודקים רק בטיקים שלמים t=0,1,2,... . מצביע שמאל מתחיל ב־{left} ומתקדם {a} בכל טיק; ימין מתחיל ב־{right} ויורד {b}. באיזה טיק הם באותו אינדקס?",
                    f"Observe only integer ticks t=0,1,2,... . Left starts at {left} and advances {a} per tick; right starts at {right} and decreases {b}. At which tick do they occupy the same index?",
                ),
                v,
                (
                    "פותרים left+a·t=right−b·t,ואז דורשים t שלם ולא שלילי. חצייה בין טיקים אינה מפגש נצפה.",
                    "Solve left+a·t=right−b·t,then require a nonnegative integer t. Crossing between ticks is not an observed meeting.",
                ),
                dict(left=left, right=right, a=a, b=b),
                "integer lattice intersection rather than continuous crossing",
                tick_options,
            )
        )
    add(
        143,
        [158],
        ("חוצים אך לא נפגשים בטיק", "Crossing without a sampled meeting"),
        (
            "פתרון בזמן רציף חייב להשתייך גם לרשת הזמנים שהמערכת אכן בודקת.",
            "A continuous-time solution must also belong to the time grid actually observed.",
        ),
        cases,
    )

    cases = []
    for prefix, rule in [
        ([100, 98, 95], None),
        ([100, 98, 95], "growing"),
        ([100, 98, 95], "alternating"),
        ([100, 98, 96], "constant"),
        ([100, 98, 95], "decreasing"),
    ]:
        result = None if rule in (None, "decreasing") else prefix[-1] - (4 if rule == "growing" else 2)
        desc = p(
            "לא נמסר כלל"
            if rule is None
            else {
                "growing": "ההפרשים הם 2,3,4,...",
                "alternating": "מחסרים 2,3 לסירוגין",
                "constant": "מחסרים תמיד 2",
                "decreasing": "נדרש רק סדר יורד ממש",
            }[rule],
            "no rule is given"
            if rule is None
            else {
                "growing": "subtract 2,3,4,...",
                "alternating": "alternate subtracting 2 and 3",
                "constant": "always subtract 2",
                "decreasing": "only strict decrease is required",
            }[rule],
        )
        opts = [p("לא נקבע מספר יחיד", "No unique next number"), p("91"), p("93"), p("94")]
        v = 0 if result is None else {91: 1, 93: 2, 94: 3}[result]
        cases.append(
            case(
                (
                    f"סדרה מתחילה {prefix}; {desc['he']}. מה מוכרח להיות האיבר הבא?",
                    f"A sequence begins {prefix}; {desc['en']}. What must the next term be?",
                ),
                v,
                (
                    "קידומת סופית לבדה אינה חוק. כשנמסר כלל מפורש מפעילים אותו; אחרת המשכים שונים יכולים להתאים לאותו עבר.",
                    "A finite prefix is not a rule. Apply an explicit recurrence when supplied;otherwise different continuations can share the same past.",
                ),
                dict(prefix=prefix, rule=rule),
                "construct distinct valid continuations or apply a supplied rule",
                opts,
            )
        )
    add(
        144,
        [133],
        ("דוגמאות אינן מגדירות את ההמשך", "Examples do not define the continuation"),
        (
            "לפני חיזוי המשך הבדילו בין נתונים שנצפו לבין כלל שבאמת הובטח.",
            "Before extrapolating,distinguish observed data from a rule actually guaranteed.",
        ),
        cases,
    )

    properties = [
        p("רק הסכומים שווים", "Only the sums are equal"),
        p("רק השטחים שווים", "Only the areas are equal"),
        p("שניהם שווים", "Both are equal"),
        p("אף אחד אינו שווה", "Neither is equal"),
    ]
    cases = []
    for sums, areas in [
        ([26, 26, 26], [1, 2, 1]),
        ([25, 26, 27], [2, 2, 2]),
        ([26, 26, 26], [2, 2, 2]),
        ([25, 26, 27], [1, 2, 3]),
        ([10, 10, 10], [1, 3, 2]),
    ]:
        eqs = len(set(sums)) == 1
        eqa = len(set(areas)) == 1
        v = 2 if eqs and eqa else 0 if eqs else 1 if eqa else 3
        cases.append(
            case(
                (
                    f"דף חולק לשלושה אזורים. סכומי המספרים בהם הם {sums},ושטחיהם הם {areas}. איזה סוג של שוויון מתקיים?",
                    f"A sheet is split into three regions. Their label sums are {sums},and their areas are {areas}. Which type of equality holds?",
                ),
                v,
                (
                    "סכום מספרים ושטח הם גדלים שונים. יש לבדוק כל דרישה בפני עצמה,בלי להסיק אחת מהשנייה.",
                    "Label sum and geometric area are different quantities. Check each requirement independently rather than inferring one from the other.",
                ),
                dict(sums=sums, areas=areas),
                "independent numeric and geometric objectives",
                properties,
            )
        )
    add(
        145,
        [165],
        ("סכום שווה אינו שטח שווה", "Equal sums are not equal areas"),
        (
            "הגדירו איזה גודל צריך להשתוות; שוויון בתוויות אינו קובע גאומטריה.",
            "Specify which quantity must match;equal label sums do not determine geometry.",
        ),
        cases,
    )

    cases = []
    for count, bad in [(4, [0, 2]), (5, [0, 2]), (6, [0, 2, 4]), (6, [0, 1, 3]), (5, [0, 2, 3])]:
        size = len(bad)
        good = [list(range(size)), list(range(1, size + 1)), list(range(count - size, count))]
        candidates = [bad, *good]
        cases.append(
            case(
                (
                    f"על מעגל מסומנים 0 עד {count - 1} בסדרם. מבין הקבוצות {candidates},איזו אינה יכולה להיות כל הסימונים בכיפה המבודדת בחיתוך ישר יחיד שאינו עובר על סימון?",
                    f"A circle has labels 0 through {count - 1} in order. Among {candidates},which set cannot be exactly the labels in a cap isolated by one straight cut avoiding labels?",
                ),
                0,
                (
                    "כיפה של קו ישר פוגשת קשת רציפה אחת. קבוצת סימונים עם פער פנימי ושאר סימונים משני צדדיו אינה כיפה אחת.",
                    "A straight-cut cap meets one contiguous circular arc. An interleaved label set cannot form one cap.",
                ),
                dict(count=count, candidates=candidates),
                "enumerate contiguous circular arcs",
                [p(str(x)) for x in candidates],
            )
        )
    add(
        146,
        [165],
        ("חלוקה מספרית צריכה גם להתאפשר במישור", "A numeric partition must fit the geometry"),
        (
            "אילוץ גאומטרי מגביל אילו קבוצות מספרים אפשר באמת לבודד.",
            "Geometric constraints restrict which numeric groups can actually be isolated.",
        ),
        cases,
    )

    legality = [
        p("מהלך היריב חוקי והזוג אינו חופף", "Opponent legal; reflected pair disjoint"),
        p("מהלך היריב אינו חוקי אך הזוג אינו חופף", "Opponent illegal; reflected pair disjoint"),
        p("מהלך היריב אינו חוקי וגם הזוג חופף", "Opponent illegal; reflected pair overlaps"),
        p("מהלך היריב חוקי אך הזוג חופף", "Opponent legal; reflected pair overlaps"),
    ]
    cases = []
    for radius, distance in [(1, 2), (1, 1), (1, 0), (2, 3), (2, 4)]:
        legal = distance >= 2 * radius
        overlap = 2 * distance < 2 * radius
        v = (0 if legal else 1) if not overlap else (3 if legal else 2)
        cases.append(
            case(
                (
                    f"על שולחן עגול יש רק מטבע מרכזי ברדיוס {radius}. יריב מניח זהה במרחק {distance},והתגובה ממול. כל המיקומים בגבולות השולחן; מגע מותר. האם מהלך היריב חוקי והאם זוג המטבעות החדשים חופף?",
                    f"A circular table holds only a radius-{radius} central coin. An equal opponent coin is {distance} from center;reply at its opposite point. All positions fit table boundaries;tangency is allowed. Is the opponent move legal,and does the new pair overlap?",
                ),
                v,
                (
                    "המרכז דורש מרחק לפחות 2r ממהלך היריב. בין מיקום היריב למיקומו הנגדי המרחק כפול.",
                    "Avoiding the central coin requires distance at least 2r. Opposite positions are twice that distance apart.",
                ),
                dict(radius=radius, distance=distance),
                "exact central exclusion and half-turn pair distance",
                legality,
            )
        )
    add(
        147,
        [166],
        ("המרכז מגן על התגובה הסימטרית", "The center protects the symmetric reply"),
        (
            "בהוכחת אסטרטגיית שיקוף בדקו גם חפיפה בין המהלך החדש לבין תגובתו.",
            "A symmetry strategy must also avoid collision between the new move and its reply.",
        ),
        cases,
    )

    cases = []
    for table, coin in [(3, 1), (5, 2), (4, 1), (2, 2), (7, 2)]:
        bound = (table * table) // (coin * coin)
        cases.append(
            case(
                (
                    f"מטבעות עגולים ברדיוס {coin} מונחים בשלמותם ללא חפיפת פנים על שולחן עגול ברדיוס {table}. מהו החסם העליון השלם ההדוק ביותר שנובע מהשוואת שטחים בלבד,ללא טענת אריזה מיטבית?",
                    f"Radius-{coin} circular coins lie wholly on a radius-{table} circular table without interior overlap. What is the tightest integer upper bound from area alone,without claiming optimal packing?",
                ),
                bound,
                (
                    "שטח כל מטבע חיובי. סכום השטחים אינו עולה על שטח השולחן,ולכן K≤floor(R²/r²). החסם אינו בהכרח ניתן להשגה.",
                    "Each coin has positive area. Total coin area cannot exceed table area,so K≤floor(R²/r²). The bound need not be attainable.",
                ),
                dict(table=table, coin=coin),
                "positive-area packing bound",
            )
        )
    add(
        148,
        [166],
        ("חסם שטח מוכיח שהמשחק יסתיים", "An area bound proves the game ends"),
        (
            "חסם סופי מספיק להוכחת סיום,גם כשאינו מתאר את האריזה המרבית.",
            "A finite bound proves termination even without solving maximum packing.",
        ),
        cases,
    )

    levels = [
        p("המפלס יורד", "Level falls"),
        p("המפלס אינו משתנה", "Level unchanged"),
        p("המפלס עולה", "Level rises"),
        p("הצפיפות חסרה ולכן אין הכרעה", "Density missing; undetermined"),
    ]
    cases = []
    for rho, water in [(2, 1), (F(1, 2), 1), (1, 1), (None, 1), (3, 2)]:
        v = 3 if rho is None else 0 if rho > water else 1
        cases.append(
            case(
                (
                    f"חפץ מוצק אינרטי נזרק מסירה צפה לבריכה סגורה ללא גלישה. צפיפות המים {water},וצפיפות החפץ {rho if rho is not None else 'לא ידועה'}. הסירה נשארת צפה. מה קורה למפלס לאחר התייצבות?",
                    f"An inert solid is thrown from a floating boat into a closed pool without spill. Water density is {water}; object density is {rho if rho is not None else 'unknown'}. The boat remains afloat. What happens to settled water level?",
                ),
                v,
                (
                    "בסירה החפץ דחה מים לפי משקלו. אם הוא שוקע הוא דוחה רק את נפחו,ואם הוא צף דחייתו נשארת לפי אותו משקל.",
                    "While carried,the object displaced water by weight. Sinking leaves only its volume;floating retains the same weight-based displacement.",
                ),
                dict(rho=None if rho is None else str(rho), water=water),
                "whole-system displacement before and after unloading",
                levels,
            )
        )
    add(
        149,
        [167],
        ("צריך להפחית גם את עומס הסירה", "Also remove the boat's old load"),
        (
            "השוו את כל המערכת לפני ואחרי,ולא רק את החפץ שנכנס למים.",
            "Compare the whole system before and after,rather than only the newly immersed object.",
        ),
        cases,
    )

    cases = []
    for a, b in [(1, 99), (2, 8), (8, 2), (5, 5), (3, 17)]:
        chance = F(1, 2 * a)
        cases.append(
            case(
                (
                    f"בוחרים תיבה בסיכוי 1/2 לכל אחת,ואז כדור אחיד מתוכה. גדלי התיבות הם A={a},B={b}. מה הסיכוי לבחור כדור מסוים שסומן ב־A?",
                    f"Choose either urn with probability 1/2,then a uniform ball within it. Urn sizes are A={a},B={b}. What is the probability of selecting one particular marked ball in A?",
                ),
                chance,
                (
                    "מסלול הבחירה של הכדור עובר דרך A: מכפילים 1/2 ב־1/|A|. הכדורים אינם בהכרח שווי־סיכוי בכל התיבות יחד.",
                    "The marked ball's path goes through A: multiply 1/2 by 1/|A|. Balls across different-sized urns need not be equally likely.",
                ),
                dict(a=a, b=b),
                "two-stage individual-outcome probability",
            )
        )
    add(
        150,
        [169],
        ("תיבה אחידה אינה כדור אחיד מכל המאגר", "Uniform urns are not uniform balls"),
        (
            "סדר ההגרלה וגודל הקבוצה משנים את הסיכוי של פריט בודד.",
            "Selection order and group size affect the probability of an individual item.",
        ),
        cases,
    )

    change = [
        p("הסיכוי לאדום עולה", "Red probability increases"),
        p("הסיכוי אינו משתנה", "Probability unchanged"),
        p("הסיכוי לאדום יורד", "Red probability decreases"),
        p("ההחלפה אינה מוגדרת בתיבה ריקה", "Swap undefined for an empty urn"),
    ]
    cases = []
    for total, size in [(100, 2), (100, 50), (100, 80), (100, 0), (10, 3)]:
        v = 3 if size == 0 else 0 if 2 * size < total else 1 if 2 * size == total else 2
        cases.append(
            case(
                (
                    f"מחלקים {total} כדורים לשתי תיבות,A בגודל {size}. בוחרים תיבה אחיד ואז כדור אחיד. רוצים להחליף לבן ב־A באדום מ־B; כששתיהן לא ריקות מובטח ששני הכדורים קיימים. הגדלים נשמרים. איך ההחלפה משפיעה על סיכוי אדום,או שאינה מוגדרת?",
                    f"Split {total} balls into urns,A having size {size}. Choose an urn uniformly,then a ball uniformly. Exchange a white in A for a red in B,keeping sizes fixed. Both balls are guaranteed when both urns are nonempty. What changes,or is the exchange undefined?",
                ),
                v,
                (
                    "השינוי הוא חצי כפול (1/|A|−1/|B|). העברת אדום לתיבה הקטנה משתלמת יותר מאובדנו בתיבה הגדולה.",
                    "The change is half of (1/|A|−1/|B|). Moving a red into the smaller urn gains more than losing it from the larger urn.",
                ),
                dict(total=total, size=size),
                "exchange argument with fixed denominators",
                change,
            )
        )
    add(
        151,
        [169],
        ("החלפה שמוכיחה כיוון לשיפור", "An exchange proves a direction of improvement"),
        (
            "אפשר להוכיח שיפור מקומי תוך שמירת האילוצים,לפני חיפוש האופטימום הכולל.",
            "Prove a constraint-preserving local improvement before optimizing the whole allocation.",
        ),
        cases,
    )

    cases = []
    for coins, directions in [(9, [-1, 1]), (9, [-1]), (12, [-1, 1]), (3, [1]), (5, [-1, 1])]:
        states = coins * len(directions)
        desc = p(
            "קל או כבד,ולא ידוע איזה"
            if len(directions) == 2
            else "קל בוודאות"
            if directions[0] < 0
            else "כבד בוודאות",
            "lighter or heavier,unknown which"
            if len(directions) == 2
            else "known lighter"
            if directions[0] < 0
            else "known heavier",
        )
        cases.append(
            case(
                (
                    f"בין {coins} מטבעות יש בדיוק מזויף אחד,שהוא {desc['he']}. כמה השערות נפרדות של (מיקום,כיוון שוני) צריך פתרון מלא להבחין ביניהן?",
                    f"Among {coins} coins,exactly one is counterfeit and is {desc['en']}. How many distinct (position,direction) hypotheses must a complete solution distinguish?",
                ),
                states,
                (
                    "לכל מיקום סופרים בנפרד כל כיוון משקל שמותר לפי ההבטחה. כיוון ידוע מסיר אפשרויות,לא מטבעות פיזיים.",
                    "For each position,count every weight direction allowed by the promise. Knowing direction removes hypotheses,not physical coins.",
                ),
                dict(coins=coins, directions=directions),
                "enumerate coin-position and deviation-direction worlds",
            )
        )
    add(
        152,
        [49, 168],
        ("המטבע וכיוון השוני הם שני נתונים", "Position and deviation direction are separate facts"),
        (
            "סופרים מצבים שיש להבחין ביניהם,ולא רק עצמים פיזיים.",
            "Count distinguishable hypotheses rather than merely physical objects.",
        ),
        cases,
    )

    cases = []
    for bottles in [4, 7, 8, 15, 16]:
        bits = math.ceil(math.log2(bottles + 1))
        cases.append(
            case(
                (
                    f"יש {bottles} בקבוקים,ולכל היותר אחד מורעל; גם היעדר רעל אפשרי. בדיקות תערובת מקבילות מחזירות ביט אמין. כמה בדיקות לפחות דרושות לזיהוי ודאי,כולל הבחנה במצב שאין רעל?",
                    f"There are {bottles} bottles,at most one poisoned; none is also possible. Parallel pooled tests return reliable bits. What minimum test count distinguishes every bottle and the no-poison case?",
                ),
                bits,
                (
                    "יש N+1 מצבים. תבנית האפס שמורה להיעדר רעל,וכל בקבוק מקבל קוד לא־אפס שונה.",
                    "There are N+1 states. Reserve the all-zero pattern for no poison and give every bottle a distinct nonzero code.",
                ),
                dict(bottles=bottles),
                "reserve zero and count injective nonzero binary codes",
            )
        )
    add(
        153,
        [73],
        ("כשגם אין רעל הוא מצב אפשרי", "When no poison is a possible state"),
        (
            "הוספת מצב אפשרי מחייבת להבחין גם בו; קוד ריק כבר אינו פנוי לבקבוק.",
            "An added possible state needs its own signature;the empty code is no longer free for a bottle.",
        ),
        cases,
    )

    cases = []
    for bottles, start, delay, observe in [
        (4, 0, 24, 23),
        (4, 0, 24, 24),
        (8, 3, 24, 24),
        (8, 3, 24, 27),
        (2, 0, 1, 0),
    ]:
        patterns = bottles if observe >= start + delay else 1
        cases.append(
            case(
                (
                    f"בדיוק אחד מ־{bottles} בקבוקים מורעל. לכל בקבוק קוד בדיקות ייחודי. כל הבדיקות מתחילות בזמן {start},ותוצאה מופיעה בדיוק {delay} שעות אחר כך. כמה תבניות נצפות שונות ייתכנו בזמן {observe}? לפני הופעת תוצאה כולם שליליים.",
                    f"Exactly one of {bottles} bottles is poisoned,each with a unique test code. All tests start at time {start}; outcomes appear exactly {delay} hours later. How many distinct observable patterns are possible at time {observe}? Before then all results are negative.",
                ),
                patterns,
                (
                    "לפני רגע התוצאה כל עולמות הרעל נראים זהים. מרגע הופעתה אפשר לראות את הקודים השונים.",
                    "Before the result instant,all poisoned-bottle worlds look identical. At that instant,the distinct codes become observable.",
                ),
                dict(bottles=bottles, start=start, delay=delay, observe=observe),
                "time-indexed observation equivalence classes",
            )
        )
    add(
        154,
        [73],
        ("מידע שטרם הגיע אינו זמין", "Information not yet received is unavailable"),
        (
            "חסם זמן נבחן לפי מועד הופעת המידע,כולל משמעות נקודת הסיום.",
            "A deadline must account for when information appears,including its endpoint semantics.",
        ),
        cases,
    )

    cases = []
    for people in [1000, 10, 11, 8, 9]:
        leaders = people // 3
        safe = people - leaders
        cases.append(
            case(
                (
                    f"מחלקים {people} חובשי כובעים לקבוצות של 3; שארית של 1 או 2 מצרפים לשלישייה האחרונה. בכל קבוצה הראשון משדר זוגיות וכל האחרים יודעים בוודאות את צבעם. כמה נכונים מובטחים בלי לסמוך על המובילים?",
                    f"Split {people} hat wearers into groups of 3;merge a remainder of 1 or 2 into the final group. Each leader signals parity and every follower knows their color. How many correct answers are guaranteed without counting leaders?",
                ),
                safe,
                (
                    "מספר הקבוצות הוא floor(N/3),ולכן מאבדים בהבטחה לכל היותר מוביל אחד לכל קבוצה. שארית אינה נשארת מבודדת.",
                    "There are floor(N/3) groups,each losing at most one guaranteed answer. The remainder is not left isolated.",
                ),
                dict(people=people),
                "construct groups of three with one final four/five block",
            )
        )
    add(
        155,
        [96],
        ("שארית שלא זורקים", "Do not abandon the remainder"),
        (
            "הבטחה יחסית במספר שלם מחייבת גם עיגול נכון וגם בנייה שמטפלת בשארית.",
            "An integral fractional guarantee needs correct rounding and a construction handling the remainder.",
        ),
        cases,
    )

    cases = []
    for people in [3, 2, 4, 5, 8]:
        cases.append(
            case(
                (
                    f"יש {people} חובשי כובעים בינאריים ללא מכסה. מדברים מאחור לפנים; כל אחד רואה רק לפניו ושומע תשובות קודמות. מותר תיאום,ורק מילת צבע אחת לכל אדם. מה המספר המרבי של נכונים שאפשר להבטיח לכל חלוקת צבעים?",
                    f"There are {people} binary-hat wearers with no color quota. They speak rear-to-front;each sees only ahead and hears earlier answers. Prior coordination is allowed;each says one color word. What maximum correct-answer count can be guaranteed for every coloring?",
                ),
                people - 1,
                (
                    "זוגיות מהראשון מאפשרת לכל האחרים להסיק את צבעם. אי אפשר להבטיח את כולם: החלפת כובע הראשון אינה משנה שום מידע שזמין לו.",
                    "The first speaker's parity lets every follower decode their color. Guaranteeing all is impossible:flipping only the first hat leaves that speaker's information unchanged.",
                ),
                dict(people=people),
                "parity construction plus indistinguishable-world upper bound",
            )
        )
    add(
        156,
        [96],
        ("בנייה וחסם נותנים הבטחה הדוקה", "A construction and bound give a tight guarantee"),
        (
            "מקסימום מובטח דורש גם אסטרטגיה שמשיגה אותו וגם חסם שמונע יותר.",
            "A tight guarantee needs both an attaining strategy and a bound excluding any larger guarantee.",
        ),
        cases,
    )

    color_options = [p("0"), p("1"), p("2"), p("אי אפשר לקבוע", "Cannot determine")]
    cases = []
    for checksum, known in [(2, [1]), (0, [1, 1]), (1, [2]), (2, [0, 1]), (0, [1, 2])]:
        color = (checksum - sum(known)) % 3
        cases.append(
            case(
                (
                    f"שלושה צבעי כובעים מקודדים 0,1,2. הודעה אמינה אומרת שסכום קבוצת הכובעים מודולו 3 הוא {checksum}. כל תרומות הקבוצה פרט לכובעך ידועות: {known}. מה צבעך המקודד?",
                    f"Three hat colors are encoded 0,1,2. A reliable message says the group's color sum modulo 3 is {checksum}. Every contribution except your hat is known: {known}. What is your encoded color?",
                ),
                color,
                (
                    "מחסרים מהשארית הכוללת את התרומות הידועות ולוקחים שוב מודולו 3. זוגיות בינארית בלבד אינה מבחינה בין שלושה צבעים.",
                    "Subtract known contributions from the checksum and reduce modulo 3. A binary parity bit alone cannot distinguish three colors.",
                ),
                dict(checksum=checksum, known=known),
                "solve a single unknown in a ternary checksum",
                color_options,
            )
        )
    add(
        157,
        [96],
        ("שלושה צבעים דורשים שלוש שאריות", "Three colors need three residues"),
        (
            "בחרו אלפבית קוד שמתאים למספר הערכים האפשריים,לא רק לכלי הבינארי המוכר.",
            "Match the coding alphabet to possible values rather than always using binary parity.",
        ),
        cases,
    )

    cases = []
    for colors, offsets in [(2, [0, 1]), (2, [0, 0]), (3, [0, 1, 2]), (3, [0, 1, 1]), (4, [0, 1, 2, 3])]:
        guaranteed = min(offsets.count(r) for r in range(colors))
        cases.append(
            case(
                (
                    f"יש {colors} אנשים ו־{colors} צבעים 0..{colors - 1}. כל אחד רואה את האחרים בלבד ומנחש במקביל (היסט פחות סכום הנראים) מודולו {colors}. ההיסטים הם {offsets}. כמה נכונים מובטחים לכל חלוקת צבעים?",
                    f"There are {colors} people and {colors} colors 0..{colors - 1}. Each sees only others and simultaneously guesses (offset minus visible sum) modulo {colors}. Offsets are {offsets}. How many correct guesses are guaranteed for every coloring?",
                ),
                guaranteed,
                (
                    "אדם צודק בדיוק כשההיסט שלו שווה לסכום כל הכובעים מודולו מספר הצבעים. ההבטחה היא הריבוי המזערי של שארית בין ההיסטים.",
                    "A person is correct exactly when their offset equals the total hat-sum residue. The guarantee is the smallest residue multiplicity among offsets.",
                ),
                dict(colors=colors, offsets=offsets),
                "enumerate distributed local guesses over every coloring",
            )
        )
    add(
        158,
        [127],
        ("תפקידים משלימים בלי לשמוע תשובות", "Complementary roles without hearing answers"),
        (
            "אסטרטגיות מקומיות שונות יכולות לכסות יחד את כל העולמות האפשריים.",
            "Different local strategies can jointly cover every possible world.",
        ),
        cases,
    )

    cases = []
    for couples, degree in [(5, 0), (5, 8), (5, 2), (4, 1), (3, 2)]:
        partner = 2 * couples - 2 - degree
        cases.append(
            case(
                (
                    f"במפגש {couples} זוגות אין לחיצות עם עצמך או בן זוג. מלבד השואל,כל האחרים דיווחו מספרים שונים 0..{2 * couples - 2}. אדם דיווח {degree}. כמה לחיצות ביצע בן זוגו,לפי קילוף זוגות הקיצון?",
                    f"At a gathering of {couples} couples,nobody shakes themselves or a spouse. Everyone except the questioner reports distinct counts 0..{2 * couples - 2}. One reports {degree}. How many handshakes did their spouse make,by extreme-pair elimination?",
                ),
                partner,
                (
                    "מי שלחץ לכולם חוץ מבן זוגו חייב להיות בן זוגו של המדווח אפס. מסירים אותם וחוזרים; מספרי בני הזוג משלימים ל־2n−2.",
                    "The maximum-count respondent must be married to the zero-count respondent. Remove that pair and repeat;spouse counts complement to 2n−2.",
                ),
                dict(couples=couples, degree=degree),
                "recursive extreme-pair elimination in a spouse-excluded handshake graph",
            )
        )
    add(
        159,
        [114],
        ("הקיצונים חייבים להיות זוג", "The extremes must be spouses"),
        (
            "אילוצי קשרים יכולים לזהות זוג קיצון,ואז לצמצם את אותה בעיה לגודל קטן יותר.",
            "Relationship constraints can identify an extreme pair and reduce to a smaller instance.",
        ),
        cases,
    )

    cases = []
    for red in [3, 1, 2, 4, 5]:
        cases.append(
            case(
                (
                    f"יש {red} כובעים אדומים בפועל. כל אדם רואה את האחרים בלבד. פורסם לפחות אדום אחד; כולם מסיקים בהיגיון ושומעים גם שתיקה בסבבים סימולטניים. אדם מכריז אדום רק כשבטוח. הסבב הראשון הוא 1. באיזה סבב תישמע ההכרזה הראשונה?",
                    f"Actually {red} hats are red. Each reasoner sees only others. At least one red is publicly announced;everyone reasons logically and hears silence in simultaneous rounds. A person declares red only when certain. Rounds start at 1. In which round is the first declaration?",
                ),
                red,
                (
                    "אדום יחיד היה יודע מיד. כשיש יותר,כל סבב שקט שולל את האפשרות שיש אדום אחד פחות. ההודעה הפומבית מתחילה את האינדוקציה המשותפת.",
                    "One red would know immediately. Each silent round rules out one fewer red. The public announcement starts this shared induction.",
                ),
                dict(red=red),
                "finite public-announcement possible-world elimination",
            )
        )
    add(
        160,
        [113],
        ("מידע פומבי מתחיל שרשרת מסקנות", "Public information starts a reasoning cascade"),
        (
            "פרסום משנה גם מה כל אחד יודע שהאחרים יודעים,ולא רק עובדה פרטית.",
            "A public announcement changes knowledge about others' knowledge,not merely a private fact.",
        ),
        cases,
    )

    cases = []
    for loads in [3, 1, 2, 4, 5]:
        crossings = 2 * loads - 1
        cases.append(
            case(
                (
                    f"גמל מעביר מלאי המחייב {loads} מטענים לאורך קטע קצר. בכל הלוך הוא נושא מטען,וחוזר רק כדי להביא את הבא; אחרי המטען האחרון אינו חוזר. הוא אוכל בננה לכל יחידת דרך. כמה בננות נצרכות ליחידת התקדמות?",
                    f"A camel moves inventory requiring {loads} loads along a short segment. It goes forward with each load and returns only to collect the next;there is no final return. It eats one banana per distance unit. How many bananas per unit of progress?",
                ),
                crossings,
                (
                    "יש k מעברי הלוך ו־k−1 חזרות. משלמים גם על דרך החזרה,ולא רק על המרחק שבו המלאי מתקדם.",
                    "There are k forward traversals and k−1 returns. Return travel also consumes food even though inventory makes no net progress then.",
                ),
                dict(loads=loads),
                "enumerate loaded forward legs and necessary empty returns",
            )
        )
    add(
        161,
        [121],
        ("הדרך חזרה צורכת מלאי", "The return trip consumes inventory"),
        (
            "עלות לוגיסטית נמדדת בכל המעברים,כולל אלה שאינם מקדמים את המטען.",
            "Logistical cost includes every traversal,including those with no net cargo progress.",
        ),
        cases,
    )

    cases = []
    for stock, capacity in [(3000, 1000), (2500, 1000), (2000, 1000), (1500, 1000), (1200, 500)]:
        loads = math.ceil(F(stock, capacity))
        rate = 2 * loads - 1
        distance = F(stock - (loads - 1) * capacity, rate)
        cases.append(
            case(
                (
                    f"יש {stock} בננות וקיבולת גמל {capacity}. כרגע דרושים {loads} מטענים,בעלות {rate} בננות ליחידת התקדמות. כמה דרך עוברים עד שהמלאי מספיק בדיוק ל־{loads - 1} מטענים ואפשר להפחית את העלות?",
                    f"There are {stock} bananas and camel capacity {capacity}. Currently {loads} loads cost {rate} bananas per progress unit. How far until stock fits exactly {loads - 1} loads and the cost can decrease?",
                ),
                distance,
                (
                    "נקודת השינוי היא כפולה של הקיבולת. מחלקים את המלאי שמעל אותה נקודה בקצב הצריכה הנוכחי,ולא משתמשים באותו קצב לכל המסלול.",
                    "The breakpoint is a capacity multiple. Divide inventory above it by the current consumption rate rather than keeping that rate for the whole journey.",
                ),
                dict(stock=stock, capacity=capacity),
                "piecewise resource-rate breakpoint",
            )
        )
    add(
        162,
        [121],
        ("העלות משתנה בנקודת קיבולת", "Cost changes at a capacity breakpoint"),
        (
            "כשהמשאב חוצה סף שמשנה את מספר הפעולות,פצלו את החישוב למקטעים.",
            "Split a calculation where a resource threshold changes the number of required operations.",
        ),
        cases,
    )

    geometry = [
        p("פשוט וקמור", "Simple and convex"),
        p("פשוט וקעור", "Simple and concave"),
        p("נחתך בעצמו; בדיקת פניות אינה מספיקה", "Self-crossing; turn signs alone are insufficient"),
        p("מנוון ללא שטח", "Degenerate with zero area"),
    ]
    cases = []
    for pts in [
        [[0, 3], [2, -3], [-3, 1], [3, 1], [-2, -3]],
        [[0, 0], [3, 0], [3, 3], [0, 3]],
        [[0, 0], [3, 0], [1, 1], [3, 3], [0, 3]],
        [[0, 3], [3, 3], [3, 0], [0, 0]],
        [[0, 0], [1, 0], [2, 0]],
    ]:
        cls = polygon_class(pts)
        v = {"strict": 0, "weak": 0, "concave": 1, "crossing": 2, "degenerate": 3}[cls]
        cases.append(
            case(
                (
                    f"מחברים את הנקודות בסדר הנתון וסוגרים לראשונה: {pts}. איזה סיווג מוצדק? פניות באותו סימן לבדן אינן מבטיחות שאין חיתוך עצמי.",
                    f"Connect these vertices in order and close back to the first: {pts}. Which classification is justified? Equal-sign local turns alone do not establish absence of self-intersection.",
                ),
                v,
                (
                    "קודם מוודאים גבול פשוט ושטח לא־אפס. רק אז סימני הפניות יכולים לשמש מבחן קמירות של מצולע מסודר.",
                    "First establish a simple boundary and nonzero area. Only then can turn signs test convexity of the ordered polygon.",
                ),
                dict(points=pts),
                "exact segment-intersection and oriented-turn classification",
                geometry,
            )
        )
    add(
        163,
        [108],
        ("בודקים גם שהגבול פשוט", "Check that the boundary is simple"),
        (
            "תנאי מקומי אינו מחליף הנחה גלובלית שעליה נשענת ההוכחה.",
            "A local condition does not replace the global precondition required by its proof.",
        ),
        cases,
    )

    convexity = [
        p("קמור ממש", "Strictly convex"),
        p("קמור חלש אך לא ממש", "Weakly convex but not strict"),
        p("קעור", "Concave"),
        p("מנוון", "Degenerate"),
    ]
    cases = []
    for pts in [
        [[0, 0], [1, 0], [2, 0], [2, 2], [0, 2]],
        [[0, 0], [2, 0], [0, 2]],
        [[0, 0], [3, 0], [1, 1], [3, 3], [0, 3]],
        [[0, 0], [1, 0], [2, 0]],
        [[0, 0], [2, 0], [2, 1], [2, 2], [0, 2]],
    ]:
        cls = polygon_class(pts)
        v = {"strict": 0, "weak": 1, "concave": 2, "degenerate": 3}[cls]
        cases.append(
            case(
                (
                    f"נקודות גבול מסודרות: {pts}. קמירות ממש דורשת פניות לא־אפס מאותו סימן; קמירות חלשה מתירה פנייה אפס לאורך צלע. איך מסווגים את הגבול?",
                    f"Ordered boundary vertices: {pts}. Strict convexity requires same-sign nonzero turns;weak convexity permits zero turns along an edge. How is this boundary classified?",
                ),
                v,
                (
                    "קודקוד נוסף על צלע ישרה יכול לשמר קמירות חלשה אבל מפר קמירות ממש. קודקוד שפונה פנימה יוצר קעירות.",
                    "An extra vertex on a straight edge preserves weak convexity but violates strict convexity. An inward turn makes the polygon concave.",
                ),
                dict(points=pts),
                "separate collinearity from inward turns and zero area",
                convexity,
            )
        )
    add(
        164,
        [108],
        ("קמירות חלשה וממש אינן אותה דרישה", "Weak and strict convexity differ"),
        (
            "מקרה שוויון יכול להיות חוקי בהגדרה אחת ופסול באחרת; הגדירו אותו מראש.",
            "An equality case may be valid under one definition and invalid under another;define it explicitly.",
        ),
        cases,
    )

    cases = []
    for count, survivor, offset in [(5, 2, 1), (6, 4, 3), (7, 3, 5), (4, 0, 2), (8, 7, 1)]:
        label = (survivor + offset) % count
        cases.append(
            case(
                (
                    f"במעגל {count} אנשים עם תוויות 0..{count - 1},תהליך הדחה יחסי הסתיים בשורד {survivor}. מחליפים כל תווית x ב־(x+{offset}) מודולו {count},בלי לשנות אנשים,סדר פיזי או נקודת התחלה. מה תווית אותו שורד כעת?",
                    f"A relative-position elimination process on {count} people labeled 0..{count - 1} leaves survivor {survivor}. Relabel every x as (x+{offset}) modulo {count},keeping physical people,order,and start unchanged. What is that survivor's new label?",
                ),
                label,
                (
                    "שינוי קואורדינטות אינו משנה את האדם ששרד. מפעילים את ההעתקה רק על תוויתו,כולל גלישה מודולרית.",
                    "Changing coordinates does not change the surviving person. Apply the relabeling map to their label,including modular wraparound.",
                ),
                dict(count=count, survivor=survivor, offset=offset),
                "rotation-equivariant relabeling of a fixed elimination trace",
            )
        )
    add(
        165,
        [12],
        ("מספר חדש לאותו אדם במעגל", "A new label for the same person"),
        (
            "הפרידו בין מצב פיזי לבין התוויות שבהן מייצגים אותו.",
            "Separate the physical state from the labels used to represent it.",
        ),
        cases,
    )

    orbit_labels = [
        p("סיבוב יכול להפוך את הראשון לשני", "A rotation can transform the first into the second"),
        p("מספר הדלוקים שונה", "The numbers of ON switches differ"),
        p("אותו מספר דלוקים אך אין סיבוב מתאים", "Same ON count but no matching rotation"),
        p("ללא כיוון מוחלט אי אפשר לבדוק זאת", "Absolute orientation is required to decide"),
    ]
    cases = []
    for a, b in [("1100", "1010"), ("1100", "0110"), ("1000", "1100"), ("1001", "1100"), ("0000", "0000")]:
        rotations = {a[i:] + a[:i] for i in range(4)}
        v = 0 if b in rotations else 1 if a.count("1") != b.count("1") else 2
        cases.append(
            case(
                (
                    f"ארבעה מתגים מסודרים סביב שולחן ריבועי. 1 הוא דלוק. שני תיאורים הם {a} ו־{b},באותו כיוון סריקה. מותר רק סיבוב ברבעי סיבוב,לא שיקוף. האם הם אותו מצב עד כדי סיבוב?",
                    f"Four switches surround a square table;1 means ON. Two descriptions are {a} and {b},read in the same direction. Only quarter-turn rotations,not reflections,are allowed. Are they the same state up to rotation?",
                ),
                v,
                (
                    "סיבוב שומר גם את דפוס השכנות ולא רק את מספר הדלוקים. שני דלוקים סמוכים אינם שני דלוקים מנוגדים.",
                    "Rotation preserves adjacency patterns as well as ON count. Adjacent ON switches are not opposite ON switches.",
                ),
                dict(a=a, b=b),
                "enumerate the four cyclic rotations",
                orbit_labels,
            )
        )
    add(
        166,
        [8],
        ("שני דלוקים אינם תמיד אותו מצב", "Two ON switches need not be one state"),
        (
            "תיאור שאינו משתנה בסיבוב עדיין יכול לאבד מידע חשוב על שכנות.",
            "A rotation-invariant summary can still lose important adjacency information.",
        ),
        cases,
    )

    cases = []
    for schedule in [[0, 1], [0, 0], [1, 0], [0, 1, 0, 1], []]:
        survivors = 0
        for initial in (0, 1):
            pos = initial
            alive = True
            for check in schedule:
                if pos == check:
                    alive = False
                    break
                pos = 1 - pos
            survivors += alive
        cases.append(
            case(
                (
                    f"מטרה מסתתרת באחד משני שיחים 0,1. אחרי כל חיפוש שמחטיא היא חייבת לעבור לשיח השני. סדר החיפושים הוא {schedule}. כמה מיקומי התחלה יכולים להתחמק מכל החיפושים? אם נתפסה התהליך נגמר.",
                    f"A target starts in bush 0 or 1. After each missed search it must switch bushes. Search order is {schedule}. How many initial positions can avoid every search? Capture ends the process.",
                ),
                survivors,
                (
                    "מעדכנים את מקום המטרה אחרי כל החטאה. ביקור בכל מקום אינו הוכחה שהמטרה הנעה הייתה שם בזמן הביקור.",
                    "Update target position after every miss. Visiting every location does not establish that the moving target was there at that time.",
                ),
                dict(schedule=schedule),
                "enumerate both moving-target histories",
            )
        )
    add(
        167,
        [29],
        ("בדקת כל מקום אך המטרה זזה", "Every location checked,but the target moved"),
        (
            "בחיפוש דינמי עקבו אחר המצבים בזמן הבדיקה,לא רק אחר המקומות שכבר נסרקו.",
            "In dynamic search,track states at observation time rather than only locations previously visited.",
        ),
        cases,
    )

    cases = []
    for a, b, c, d in [(1, 2, 5, 10), (1, 4, 5, 10), (2, 3, 4, 9), (1, 3, 5, 8), (2, 4, 9, 12)]:
        best = min(a + 3 * b + d, 2 * a + b + c + d)
        cases.append(
            case(
                (
                    f"זמני ארבעה חוצים הם a={a},b={b},c={c},d={d}. שני לוחות זמנים חוקיים עם לפיד עולים A=a+3b+d ו־B=2a+b+c+d. מה העלות הקטנה מבין שני הלוחות האלה? אין טענת מינימום על כל לוח אפשרי.",
                    f"Four crossing times are a={a},b={b},c={c},d={d}. Two legal torch schedules cost A=a+3b+d and B=2a+b+c+d. What is the lower cost of these two schedules? No global-optimality claim is assumed.",
                ),
                best,
                (
                    "משווים את הלוחות השלמים,כולל חזרות. שימוש קבוע בחוזר המהיר ביותר אינו בהכרח זול יותר משילוח שני האיטיים יחד.",
                    "Compare complete schedules including returns. Always using the fastest returner can cost more than sending the two slowest together.",
                ),
                dict(a=a, b=b, c=c, d=d),
                "compare two explicitly feasible bridge schedules",
            )
        )
    add(
        168,
        [39],
        ("החוזר הכי מהיר אינו כל האסטרטגיה", "The fastest returner is not the whole strategy"),
        (
            "בחירה מקומית מהירה יכולה ליצור יותר עלות במעברים האחרים.",
            "A locally fast choice may increase the cost of the remaining trips.",
        ),
        cases,
    )

    cases = []
    schedules = [
        [("AB", 1), ("AC", 1)],
        [("AB", 1), ("A", -1), ("AC", 1)],
        [("AB", 1), ("A", -1), ("BC", 1)],
        [("A", 1), ("A", -1), ("BC", 1), ("B", -1), ("AB", 1)],
        [("AB", 1), ("B", -1), ("BC", 1)],
    ]
    for schedule in schedules:
        positions = {x: 0 for x in "ABC"}
        torch = 0
        bad = 0
        for i, (group, direction) in enumerate(schedule, 1):
            start = 0 if direction == 1 else 1
            if torch != start or any(positions[x] != start for x in group):
                bad = i
                break
            for x in group:
                positions[x] = 1 - start
            torch = 1 - start
        printed = [g + ("→" if d == 1 else "←") for g, d in schedule]
        cases.append(
            case(
                (
                    f"A,B,C והלפיד מתחילים משמאל. כל מעבר של אדם או זוג דורש שכולם והלפיד באותו צד. הלוח הוא {printed}; → הוא ימינה. מה מספר המעבר הבלתי חוקי הראשון? החזירו 0 אם כולם חוקיים.",
                    f"A,B,C and the torch start left. A solo/pair crossing requires all participants and the torch on its starting side. Schedule: {printed}; → means right. What is the first illegal move number? Return 0 if all are legal.",
                ),
                bad,
                (
                    "יש לעקוב גם אחר צד הלפיד וגם אחר צד כל חוצה. סכום זמנים יפה אינו מכשיר מעבר כשאדם או הלפיד אינם בנקודת היציאה.",
                    "Track the torch and every person's side. An attractive time total cannot legalize a trip whose people or torch are on the wrong side.",
                ),
                dict(schedule=schedule),
                "stateful torch and participant-location feasibility",
            )
        )
    add(
        169,
        [39],
        ("לפיד אינו משאב שנמצא בשני הצדדים", "The torch cannot be on both sides"),
        (
            "בדקו שלוח זמנים אפשרי לפני שמחשבים אם הוא מהיר.",
            "Check schedule feasibility before evaluating its speed.",
        ),
        cases,
    )

    cases = []
    for x, y in [(1, 2), (1, 3), (2, 4), (3, 4), (3, 5)]:
        mask = x | y
        cases.append(
            case(
                (
                    f"בדיקות תערובת מחזירות חיובי אם קיבלו רעל כלשהו. לשני בקבוקים מורעלים יש קודים בינאריים שמספריהם {x} ו־{y}. איזה מספר מתקבל מתבנית התוצאות,אם מאחדים את הקודים ב־OR סיביתי?",
                    f"Pooled tests are positive if they receive any poison. Two poisoned bottles have binary code numbers {x} and {y}. What number does the outcome pattern encode,using bitwise OR of the codes?",
                ),
                mask,
                (
                    "כל ביט שהופיע באחד משני הקודים נדלק. התוצאה יכולה להיות קוד חוקי של בקבוק אחר,ולכן קידוד חד־רעל אינו בהכרח מגלה רעל מרובה.",
                    "Every bit present in either code becomes positive. The result can be another valid bottle's code,so a single-poison code need not detect multiple poisons.",
                ),
                dict(x=x, y=y),
                "union of test pools versus a single-poison code",
            )
        )
    add(
        170,
        [73],
        ("שני מקורות יכולים לחקות מקור אחר", "Two sources can mimic a third"),
        (
            "חתימות ייחודיות לעצם יחיד אינן מבטיחות ייחודיות לצירופים של עצמים.",
            "Unique singleton signatures do not guarantee unique signatures for combinations.",
        ),
        cases,
    )

    decision = [
        p("לנסות לפגוע", "Attempt the hit"),
        p("להחטיא בכוונה", "Deliberately miss"),
        p("שווה בשתי הפעולות", "Both actions have equal value"),
        p("לא ניתן להשוות", "Cannot compare"),
    ]
    cases = []
    for prob, hit, miss in [
        (F(1, 2), F(1, 4), F(3, 4)),
        (F(1, 2), F(3, 4), F(1, 4)),
        (F(1, 2), F(1, 2), F(1, 2)),
        (F(1, 4), F(1, 10), F(4, 5)),
        (F(0), F(1), F(0)),
    ]:
        attempted = prob * hit + (1 - prob) * miss
        v = 0 if attempted > miss else 1 if attempted < miss else 2
        cases.append(
            case(
                (
                    f"מטרתך לנצח בסוף. ניסיון פגיעה מצליח בסיכוי {prob}. לאחר הצלחה סיכוי הניצחון העתידי שלך {hit},ולאחר החטאה {miss}. החטאה מכוונת מובילה לאותו המשך של החטאה. איזו פעולה עדיפה?",
                    f"Your goal is eventual victory. An attempted hit succeeds with probability {prob}. After a hit your continuation win chance is {hit};after a miss it is {miss}. Deliberately missing gives the same miss continuation. Which action is better?",
                ),
                v,
                (
                    "משקללים את סיכויי ההמשך של כל תוצאה. הצלחה מקומית יכולה להוביל למצב עתידי גרוע יותר.",
                    "Weight the continuation values of each outcome. A local success can lead to a worse future state.",
                ),
                dict(prob=str(prob), hit=str(hit), miss=str(miss)),
                "one-step expected continuation-value comparison",
                decision,
            )
        )
    add(
        171,
        [79],
        ("פגיעה אינה בהכרח ניצחון", "A hit is not necessarily a win"),
        (
            "אופטימיזציה נמדדת ביעד הסופי,לא בהצלחת הפעולה הקרובה בלבד.",
            "Optimize the final objective rather than merely the next action's success.",
        ),
        cases,
    )

    cases = []
    for predictions in [
        [(10, 10), (12, 15), (8, 8), (6, 6)],
        [(2, 3), (4, 4), (8, 8), (5, 5)],
        [(1, 1), (2, 2), (3, 3), (4, 7)],
        [(5, 5), (8, 8), (9, 10), (6, 6)],
        [(4, 4), (2, 5), (7, 7), (9, 9)],
    ]:
        informative = next(i + 1 for i, (a, b) in enumerate(predictions) if a != b)
        cases.append(
            case(
                (
                    f"נותרו שתי רשתות נגדים אפשריות. ארבע מדידות מועמדות מנבאות עבורן זוגות התנגדות אלה,לפי הסדר: {predictions}. המדידה אידאלית. איזה מספר מדידה מפריד ביניהן בוודאות? המספור מתחיל ב־1.",
                    f"Two candidate resistor networks remain. Four possible measurements predict these resistance pairs for the candidates,in order: {predictions}. Measurement is ideal. Which measurement number certainly distinguishes them? Numbering starts at 1.",
                ),
                informative,
                (
                    "בוחרים מדידה שהתחזיות שלה שונות בין האפשרויות. מדידה מדויקת עם אותה תחזית בשתיהן אינה מזהה את הרשת.",
                    "Choose a measurement with different predictions across candidates. Even an exact measurement with the same prediction cannot identify the network.",
                ),
                dict(predictions=predictions),
                "active experiment separating remaining model candidates",
            )
        )
    add(
        172,
        [154],
        ("למדוד היכן שהתחזיות נפרדות", "Measure where the predictions differ"),
        (
            "בחרו ניסוי לפי יכולתו להפריד בין ההסברים שנותרו,לא רק לפי דיוקו.",
            "Choose an experiment by its ability to separate remaining explanations,not only its precision.",
        ),
        cases,
    )

    cases = []
    for ar, aw, br, bw in [(1, 0, 49, 50), (1, 1, 1, 3), (2, 0, 1, 1), (1, 3, 3, 1), (2, 2, 2, 2)]:
        la = F(ar, ar + aw)
        lb = F(br, br + bw)
        posterior = la / (la + lb)
        cases.append(
            case(
                (
                    f"בוחרים תיבה A או B בסיכוי 1/2 ואז כדור אחיד. כמויות (אדומים,לבנים): A=({ar},{aw}),B=({br},{bw}). נצפה אדום. מה הסיכוי שנבחרה A?",
                    f"Choose urn A or B with probability 1/2,then a uniform ball. Counts (red,white): A=({ar},{aw}),B=({br},{bw}). A red was observed. What is the probability A was chosen?",
                ),
                posterior,
                (
                    "לאחר אדום משווים את משקלי מסלולי הבחירה האדומים. ההסתברות ל־A היא סיכוי אדום בה חלקי סכום סיכויי האדום בשתי התיבות.",
                    "Condition on the red-selection paths. A's posterior is its red likelihood divided by the sum of both urns' red likelihoods.",
                ),
                dict(ar=ar, aw=aw, br=br, bw=bw),
                "reverse two-stage conditioning by exact joint probability",
            )
        )
    add(
        173,
        [169],
        ("תוצאה משנה את הסיכוי למקורה", "An outcome updates its source probability"),
        (
            "הסתברות של תוצאה בהינתן מקור שונה מהסתברות המקור אחרי התוצאה.",
            "An outcome given a source differs from the source probability after observing the outcome.",
        ),
        cases,
    )

    parity = [
        p("זוגי", "Even"),
        p("אי־זוגי", "Odd"),
        p("שתי הזוגיויות אפשריות", "Either parity is possible"),
        p("אין גרף לחיצות מתאים", "No matching handshake graph"),
    ]
    cases = []
    for prefix in [[1, 1, 1], [2, 2, 2], [0, 1, 1], [3, 3, 3], [0, 0, 3]]:
        possible = degree_worlds(prefix)
        parities = {x % 2 for x in possible}
        v = 3 if not possible else next(iter(parities)) if len(parities) == 1 else 2
        cases.append(
            case(
                (
                    f"ארבעה אנשים לוחצים ידיים; כל זוג לכל היותר פעם אחת וללא עצמם. שלושת הראשונים דיווחו {prefix}. איזו זוגיות חייבת להיות למספר הלחיצות של הרביעי,או שהדיווחים אינם אפשריים?",
                    f"Four people shake hands,each pair at most once and never themselves. The first three report {prefix}. What parity must the fourth person's count have,or are the reports impossible?",
                ),
                v,
                (
                    "סכום הדרגות הוא פעמיים מספר לחיצות הידיים. לכן מספר הדרגות האי־זוגיות זוגי; נוסף לכך צריך שהדיווחים יתאימו לגרף כלשהו.",
                    "Degree sum is twice the number of handshakes,so the number of odd degrees is even. Reports must also be realizable by a graph.",
                ),
                dict(prefix=prefix),
                "enumerate all simple four-person handshake graphs",
                parity,
            )
        )
    add(
        174,
        [114],
        ("גם בלי לדעת את מספר הלחיצות", "Even without the exact handshake count"),
        (
            "אילוץ זוגיות גלובלי יכול לקבוע תכונה גם כשהערך המדויק נשאר לא ידוע.",
            "A global parity constraint can determine a property while leaving the exact value unknown.",
        ),
        cases,
    )

    cases = []
    for total, pan in [(9, 1), (9, 3), (9, 4), (8, 3), (7, 2)]:
        worst = max(pan, total - 2 * pan)
        cases.append(
            case(
                (
                    f"בין {total} מטבעות יש מזויף יחיד שידוע כקל. בשקילה הראשונה שמים {pan} מול {pan}. כמה מועמדים לכל היותר יישארו בענף הגדול ביותר? שקילה נוספת אחת מבחינה לכל היותר בשלוש תוצאות.",
                    f"Among {total} coins,one counterfeit is known lighter. First weigh {pan} against {pan}. How many candidates remain in the largest outcome branch? One further weighing has at most three outcomes.",
                ),
                worst,
                (
                    "בהטיה נשארים מועמדים בצד הקל,ובאיזון הלא־נשקלים. אם נשארים יותר מ־3 מועמדים,אי אפשר להכריע בשקילה היחידה שנותרה. מתכננים לפי הענף הגרוע.",
                    "A tilt leaves the lighter pan's candidates;balance leaves the unweighed. More than 3 candidates cannot be resolved in the single remaining weighing. Plan for the worst branch.",
                ),
                dict(total=total, pan=pan),
                "partition known-lighter hypotheses by first-weighing outcomes",
            )
        )
    add(
        175,
        [168],
        ("משאירים ענף שאפשר לסיים", "Leave a branch that can be finished"),
        (
            "תכנון בדיקות צריך להתאים את כל ענפי ההמשך לתקציב שנותר.",
            "A test plan must fit every remaining branch within the remaining budget.",
        ),
        cases,
    )

    cases = []
    for initial, events in [
        (0, ["RA", "RB", "WA", "WB"]),
        (0, ["RA", "WA", "RB", "WB"]),
        (5, ["RB", "RA", "WB", "WA"]),
        (5, ["RB", "WB", "RA", "WA"]),
        (1, ["RA", "RB", "WB", "WA"]),
    ]:
        shared = initial
        local = {}
        for event in events:
            if event[0] == "R":
                local[event[1]] = shared
            else:
                shared = local[event[1]] + 1
        cases.append(
            case(
                (
                    f"מונה משותף מתחיל ב־{initial}. לכל A ו־B שתי פעולות: R קוראת את המונה לעותק מקומי,W כותבת העותק+1. סדר הפעולות הוא {events}. מה הערך הסופי? הקריאה והכתיבה אינן פעולה אטומית יחד.",
                    f"A shared counter starts at {initial}. Each of A and B performs R to read a local copy,and W to write that copy+1. Event order is {events}. What is the final counter? Read and write together are not atomic.",
                ),
                shared,
                (
                    "כתיבה משתמשת בעותק שנקרא קודם. אם שני הצדדים קראו אותו ערך,כתיבה מאוחרת יכולה לדרוס עדכון במקום להוסיף עליו.",
                    "A write uses the earlier local snapshot. If both read the same value,a later write can overwrite rather than accumulate the other update.",
                ),
                dict(initial=initial, events=events),
                "interleaved local snapshots and shared writes",
            )
        )
    add(
        176,
        [161],
        ("שתי הגדלות שלא בהכרח מצטברות", "Two increments may not accumulate"),
        (
            "פעולות נכונות בנפרד עלולות לאבד מידע כאשר רצפי הקריאה והכתיבה משתלבים.",
            "Individually correct operations can lose information when read/write sequences interleave.",
        ),
        cases,
    )

    cases = []
    for outcomes in [[(0, 1), (4, 1)], [(1, 1), (3, 1)], [(2, 1)], [(0, 1), (3, 9)], [(2, 9), (5, 1)]]:
        guaranteed = min(k for k, w in outcomes if w > 0)
        cases.append(
            case(
                (
                    f"במשחק כובעים,מדיניות נתונה מניבה את האפשרויות (מספר נכונים,משקל הסתברות חיובי): {outcomes}. מחלקים את המשקלים בסכומם. כמה נכונים מובטחים בכל משחק,בלי להחליף את ההבטחה בתוחלת?",
                    f"In a hats game,a policy has outcomes (correct answers,positive probability weight): {outcomes}. Normalize weights by their sum. How many correct answers are guaranteed in every game,rather than merely expected?",
                ),
                guaranteed,
                (
                    "הבטחה נקבעת לפי המינימום בין כל התוצאות האפשריות. גם תוצאה נדירה עם משקל קטן מונעת הבטחה גדולה יותר.",
                    "A guarantee is the minimum over all possible outcomes. Even a rare low outcome prevents a larger certainty guarantee.",
                ),
                dict(outcomes=outcomes),
                "minimum supported payoff versus probability-weighted expectation",
            )
        )
    add(
        177,
        [96],
        ("תוחלת אינה רצפת הצלחה", "Expectation is not a guaranteed floor"),
        (
            "להבטחת מקרה גרוע בודקים גם אפשרויות בעלות הסתברות קטנה,לא רק את הממוצע.",
            "A worst-case guarantee includes low-probability possibilities rather than only the average.",
        ),
        cases,
    )

    assert len(cards) == 52 and len(rows) == len(checks) == 260
    return cards, rows, checks


def build():
    _, rows, checks = build_bundle()
    return rows, checks


if __name__ == "__main__":
    cards, rows, checks = build_bundle()
    SHORT.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, value in (("reasoning_400.json", rows), ("reasoning_400.checks.json", checks)):
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cards)} short cards and {len(rows)} draft MCQ cases.")
