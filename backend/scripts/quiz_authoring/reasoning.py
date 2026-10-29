"""Authored bilingual reasoning cases; deterministic calculations and case evidence.

This is AI-assisted editorial work, not a human-review attestation.
Run directly to rebuild this shard. The production seed is assembled separately.
"""

from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROWS = []
CHECKS = []


def pair(value):
    return value if isinstance(value, tuple) else (str(value), str(value))


def add(n, v, he, en, good, bad, eh, ee, method, inputs=None):
    assert len(bad) == 3
    options = [pair(good), *map(pair, bad)]
    assert all(len(set(c[i] for c in options)) == 4 for i in (0, 1)), (n, v, options)
    shift = (n + v) % 4
    options = options[-shift:] + options[:-shift] if shift else options
    key = f"quick-sw-{n:02d}-v{v}"
    ROWS.append(
        dict(
            key=key,
            source_key=f"quick-sw-{n:02d}",
            variant=v,
            topic="reasoning",
            status="draft",
            prompt=dict(he=he, en=en),
            choices=[dict(he=a, en=b) for a, b in options],
            correct=shift,
            explanation=dict(he=eh, en=ee),
        )
    )
    CHECKS.append(
        dict(key=key, method=method, inputs=inputs or {}, expected=dict(he=pair(good)[0], en=pair(good)[1]))
    )


def num(n, v, he, en, result, eh, ee, method, inputs=None, wrong=None):
    if wrong is None:
        candidates = [result + 1, result - 1, result + 2, result * 2, result + 3, 0]
        wrong = []
        for c in candidates:
            if c != result and c >= 0 and c not in wrong:
                wrong.append(c)
            if len(wrong) == 3:
                break
    add(n, v, he, en, str(result), list(map(str, wrong)), eh, ee, method, inputs)


def fraction(n, v, he, en, value, eh, ee, method, inputs=None):
    pool = [
        Fraction(0),
        Fraction(1, 2),
        Fraction(1, 3),
        Fraction(1, 4),
        Fraction(2, 3),
        Fraction(3, 4),
        Fraction(1),
        Fraction(1, 8),
        Fraction(7, 8),
    ]
    num(n, v, he, en, value, eh, ee, method, inputs, [x for x in pool if x != value][:3])


def build_basic():
    # A finite location model: rotate box names, enumerate all three states.
    for v, names in enumerate(
        [("A", "B", "C"), ("P", "Q", "R"), ("X", "Y", "Z"), ("D", "E", "F"), ("K", "L", "M")], 1
    ):
        a, b, c = names
        valid = [x for x in names if sum([x != a, x == a, x != b]) == 1]
        assert valid == [b]
        add(
            1,
            v,
            f"מטבע נמצא באחת הקופסאות {a}, {b}, {c}. על הראשונה כתוב ״לא ב־{a}״, על השנייה ״ב־{a}״ ועל השלישית ״לא ב־{b}״. בדיוק משפט אחד נכון. היכן המטבע?",
            f"A coin is in one of boxes {a}, {b}, {c}. Their statements, respectively, are 'not in {a}', 'in {a}', and 'not in {b}'. Exactly one is true. Where is the coin?",
            b,
            [a, c, ("אין מצב מתאים", "No location satisfies the conditions")],
            f"רק מיקום ב־{b} נותן משפט נכון אחד; כל מיקום אחר נותן שניים.",
            f"Only {b} gives exactly one true statement; each other location gives two.",
            "exhaustive location truth counts",
            dict(names=names, counts=[2, 1, 2]),
        )
    for v, order in enumerate(["DABC", "CABD", "BDAC", "ACDB", "DCBA"], 1):
        a, b, c, d = order
        good = ", ".join(order)
        bad = [", ".join(x) for x in [order[::-1], b + a + c + d, a + c + b + d]]
        valid = [
            p for p in itertools.permutations(order) if p[0] == a and p.index(b) < p.index(c) < p.index(d)
        ]
        assert valid == [tuple(order)]
        add(
            4,
            v,
            f"ארבעה אנשים {', '.join(sorted(order))} עומדים בטור. {a} ראשון, {b} לפני {c}, ו־{c} לפני {d}. מה הסדר מהראשון לאחרון?",
            f"Four people {', '.join(sorted(order))} stand in a line. {a} is first, {b} is before {c}, and {c} is before {d}. What is the order from first to last?",
            good,
            bad,
            "המקום הראשון והשרשרת הנתונה קובעים את כל המקומות.",
            "The fixed first position and the given chain determine every position.",
            "enumerate all 24 permutations",
            dict(valid=valid),
        )
    for v, (distance, a, b) in enumerate(
        [(60, 30, 60), (120, 40, 80), (30, 20, 60), (100, 50, 100), (90, 30, 90)], 1
    ):
        time = Fraction(distance, a) + Fraction(distance, b)
        result = 2 * distance / time
        assert result * time == 2 * distance
        num(
            6,
            v,
            f"נוסעים {distance} ק״מ במהירות {a} קמ״ש וחוזרים באותו מרחק במהירות {b} קמ״ש, ללא עצירות. מה המהירות הממוצעת בקמ״ש?",
            f"Travel {distance} km at {a} km/h and return the same distance at {b} km/h, without stops. What is the average speed in km/h?",
            result,
            f"מחלקים את המרחק הכולל בזמן הכולל: {2 * distance} חלקי {time}.",
            f"Divide total distance by total time: {2 * distance} divided by {time}.",
            "sum segment times and recombine distance",
            dict(distance=distance, speeds=[a, b]),
        )
    for v, (a, b) in enumerate([(6, 10), (4, 6), (8, 12), (9, 15), (5, 7)], 1):
        result = next(k for k in range(1, a * b + 1) if k % a == k % b == 0)
        assert result == math.lcm(a, b)
        num(
            7,
            v,
            f"שתי נורות מהבהבות כל {a} ו־{b} שניות, בהתאמה. שתיהן הבהבו בזמן 0. אחרי כמה שניות יבהבו יחד לראשונה שוב?",
            f"Two lights flash every {a} and {b} seconds, respectively. Both flashed at time 0. After how many seconds will they first flash together again?",
            result,
            f"מחפשים את הכפולה החיובית המשותפת הקטנה ביותר: {result}.",
            f"The smallest positive common multiple is {result}.",
            "enumerate positive common multiples; compare lcm",
            dict(periods=[a, b]),
        )
    for v, stairs in enumerate([3, 4, 5, 6, 7], 1):

        def ways(k):
            return 1 if k < 2 else ways(k - 1) + ways(k - 2)

        result = ways(stairs)
        enumerated = sum(
            sum(seq) == stairs
            for length in range(1, stairs + 1)
            for seq in itertools.product([1, 2], repeat=length)
        )
        assert result == enumerated
        num(
            8,
            v,
            f"מטפסים בדיוק {stairs} מדרגות, בצעדים של מדרגה אחת או שתיים בלבד. אין ירידה ואין מעבר לפסגה. כמה סדרות צעדים שונות יש, כאשר הסדר חשוב?",
            f"Climb exactly {stairs} stairs using steps of one or two stairs only. No downward steps or overshooting are allowed. How many move sequences are there, counting different orders separately?",
            result,
            f"מספר הדרכים הוא סכום מספרי הדרכים לשתי המדרגות הקודמות; מתקבל {result}.",
            f"Add the counts for the previous two stairs; the result is {result}.",
            "recursive recurrence checked by sequence enumeration",
            dict(stairs=stairs),
        )
    for v, (a, b, years) in enumerate([(8, 13, 5), (6, 15, 10), (12, 19, 4), (3, 11, 7), (20, 32, 8)], 1):
        assert (b + years) - (a + years) == b - a
        num(
            10,
            v,
            f"שני אחים בני {a} ו־{b} היום. מה יהיה הפרש הגילים ביניהם בעוד {years} שנים?",
            f"Two siblings are {a} and {b} years old today. What will their age difference be in {years} years?",
            b - a,
            "מוסיפים לשני הגילים אותו מספר, ולכן ההפרש נשמר.",
            "Adding the same number to both ages preserves their difference.",
            "age difference invariant",
            dict(ages=[a, b], years=years),
        )
    for v, (count, minimum) in enumerate([(2, 1), (3, 1), (3, 2), (4, 1), (4, 3)], 1):
        outcomes = list(itertools.product([0, 1], repeat=count))
        kept = [x for x in outcomes if sum(x) >= minimum]
        result = Fraction(sum(sum(x) == count for x in kept), len(kept))
        fraction(
            13,
            v,
            f"מטילים {count} מטבעות הוגנים ועצמאיים ושומרים רק תוצאות עם לפחות {minimum} פעמים עץ. מה ההסתברות שכל המטבעות הראו עץ, מבין התוצאות שנשמרו?",
            f"Toss {count} fair independent coins and retain only outcomes with at least {minimum} heads. Among retained outcomes, what is the probability that all coins showed heads?",
            result,
            f"נותרת תוצאה אחת של עץ בלבד מתוך {len(kept)} תוצאות שוות הסתברות.",
            f"There is one all-heads outcome among {len(kept)} equally likely retained outcomes.",
            "enumerate conditioned binary sample space",
            dict(coins=count, minimum_heads=minimum, retained=len(kept)),
        )
    for v, (gap, front, rear) in enumerate([(4, 1, 3), (12, 2, 5), (15, 1, 4), (8, 3, 5), (20, 4, 9)], 1):
        t = Fraction(gap, rear - front)
        assert rear * t == gap + front * t
        num(
            16,
            v,
            f"שני רובוטים נעים באותו כיוון במהירויות קבועות. הקדמי נע ב־{front} מטר לשנייה, האחורי ב־{rear}, והפער ההתחלתי הוא {gap} מטרים. אחרי כמה שניות ייפגשו?",
            f"Two robots move in the same direction at constant speeds. The front robot moves at {front} m/s, the rear at {rear} m/s, and their initial gap is {gap} m. After how many seconds do they meet?",
            t,
            f"מהירות סגירת הפער היא {rear - front}; מחלקים את הפער במהירות זו.",
            f"The closing speed is {rear - front}; divide the gap by this speed.",
            "solve and substitute both positions",
            dict(gap=gap, speeds=[front, rear]),
        )

    for v, size in enumerate([4, 6, 8, 10, 12], 1):
        counts = [
            sum(
                (x + y) % 2 == color
                for x in range(size)
                for y in range(size)
                if (x, y) not in [(0, 0), (size - 1, size - 1)]
            )
            for color in (0, 1)
        ]
        assert abs(counts[0] - counts[1]) == 2
        add(
            19,
            v,
            f"מסירים את הפינה השמאלית העליונה והימנית התחתונה מלוח שחמט בגודל {size}×{size}. מדוע אי אפשר לכסות את היתר באבני דומינו, שכל אחת מכסה שתי משבצות סמוכות בצלע?",
            f"Remove the top-left and bottom-right corners of a {size}×{size} checkerboard. Why can the remainder not be tiled with dominoes covering edge-adjacent squares?",
            ("נותרו כמויות שונות של שני הצבעים", "The two colors have unequal remaining counts"),
            [
                ("מספר המשבצות שנותר אי־זוגי", "An odd number of squares remains"),
                ("כל אבן מכסה שני ריבועים מאותו צבע", "Each domino covers two squares of the same color"),
                ("בכל לוח זוגי אין כיסוי בדומינו", "Every even-sized board is impossible to tile"),
            ],
            "שתי הפינות באותו צבע, וכל דומינו מכסה משבצת אחת מכל צבע.",
            "The corners share a color, while each domino covers one square of each color.",
            "enumerate checkerboard color counts",
            dict(size=size, color_counts=counts),
        )
    for v, boxes in enumerate([4, 5, 8, 9, 16], 1):
        result = (boxes - 1).bit_length()
        assert 2 ** (result - 1) < boxes <= 2**result
        num(
            20,
            v,
            f"מפתח נמצא באחת מ־{boxes} קופסאות. מותר לשאול שאלות אמת של כן/לא על כל קבוצת קופסאות, ולבחור כל שאלה לפי התשובות הקודמות. כמה שאלות דרושות לכל היותר בשיטה מיטבית כדי לזהות את הקופסה בוודאות?",
            f"A key is in one of {boxes} boxes. You may ask truthful yes/no questions about any subset and adapt later questions to earlier answers. What is the optimal worst-case number of questions to identify the box?",
            result,
            f"צריך לפחות {boxes} דפוסי תשובה. {result} שאלות נותנות עד {2**result} דפוסים, וניתן לפצל את האפשרויות בכל שלב.",
            f"At least {boxes} answer patterns are needed. {result} questions allow {2**result} patterns, achieved by splitting the remaining possibilities.",
            "binary decision-tree capacity lower and upper bounds",
            dict(boxes=boxes),
        )
    for v, (coins, target) in enumerate([(10, 9), (8, 5), (12, 11), (6, 3), (14, 7)], 1):
        assert target % 2 == 1
        add(
            21,
            v,
            f"מתחילים עם {coins} מטבעות שכולם פלי. בכל מהלך הופכים בדיוק שני מטבעות שונים. איזה נימוק מוכיח שאי אפשר להגיע בדיוק ל־{target} מטבעות עץ?",
            f"Start with {coins} coins all showing tails. Each move flips exactly two different coins. Which argument proves that exactly {target} heads cannot be reached?",
            ("זוגיות מספר מטבעות העץ נשמרת", "The parity of the heads count is invariant"),
            [
                ("מספר העץ תמיד גדל בדיוק בשניים", "The heads count always increases by exactly two"),
                ("אפשר להפוך כל מטבע רק פעם אחת", "Each coin can be flipped only once"),
                ("מספר העץ לעולם אינו משתנה", "The heads count never changes"),
            ],
            "המספר משתנה ב־2, ב־0 או ב־‎−2, ולכן הוא נשאר זוגי.",
            "The count changes by 2, 0, or −2, so it remains even.",
            "enumerate the three possible heads-count changes",
            dict(coins=coins, target=target, changes=[-2, 0, 2]),
        )
    for v, colors in enumerate([3, 4, 5, 6, 7], 1):
        num(
            22,
            v,
            f"במגירה גרביים ב־{colors} צבעים, ויש לפחות שתי גרביים מכל צבע. כמה שליפות ללא הסתכלות מבטיחות זוג גרביים באותו צבע?",
            f"A drawer has socks in {colors} colors, with at least two socks of each color. How many blind draws guarantee two socks of the same color?",
            colors + 1,
            "במקרה הגרוע שולפים תחילה גרב אחת מכל צבע; השליפה הבאה בהכרח חוזרת על צבע.",
            "In the worst case the first draws use every color once; the next draw must repeat a color.",
            "pigeonhole upper bound and distinct-color lower-bound witness",
            dict(colors=colors),
        )
    for v, (short, long) in enumerate([(4, 7), (5, 9), (3, 8), (7, 12), (6, 11)], 1):
        result = long - short
        num(
            23,
            v,
            f"מפעילים יחד שעוני חול של {short} ושל {long} דקות. מתחילים למדוד כשהקצר מתרוקן ומסיימים כשהארוך מתרוקן. כמה דקות נמדדו?",
            f"Start {short}-minute and {long}-minute hourglasses together. Begin the measurement when the shorter glass empties and end when the longer glass empties. How many minutes were measured?",
            result,
            "שתי נקודות הסיום נמדדות מאותה התחלה, ולכן מחסרים את משכי השעונים.",
            "Both emptying times share the same start, so subtract their durations.",
            "subtract event timestamps",
            dict(empty_times=[short, long]),
        )
    for v, position in enumerate([2, 3, 4, 5, 6], 1):
        num(
            24,
            v,
            f"במרוץ ללא הקפות עקפת זה עתה את הרץ שהיה במקום {position}. מה מקומך מיד אחרי העקיפה?",
            f"In a race with no lapping, you have just passed the runner who was in position {position}. What is your position immediately afterward?",
            position,
            "תופסים את המקום של הרץ שנעקף; הרצים שהיו לפניו עדיין לפנים.",
            "You take the passed runner's position; the runners ahead remain ahead.",
            "swap adjacent race ranks",
            dict(passed_rank=position),
        )

    fruits = [
        ("תפוחים", "אגסים", "apples", "pears"),
        ("תפוזים", "לימונים", "oranges", "lemons"),
        ("שזיפים", "אפרסקים", "plums", "peaches"),
        ("דובדבנים", "תותים", "cherries", "strawberries"),
        ("בננות", "תמרים", "bananas", "dates"),
    ]
    for v, (ah, bh, ae, be) in enumerate(fruits, 1):
        arrangements = [
            p
            for p in itertools.permutations(["A", "B", "M"])
            if all(x != y for x, y in zip(p, ["A", "B", "M"], strict=True))
        ]
        assert len(arrangements) == 2 and all(p[2] != "M" for p in arrangements)
        add(
            25,
            v,
            f"שלוש קופסאות מכילות רק {ah}, רק {bh}, ותערובת של שניהם. כל שלוש התוויות שגויות. מאיזו קופסה כדאי להוציא פרי אחד, בלי להציץ פנימה, כדי לזהות את תכולת כולן?",
            f"Three boxes contain only {ae}, only {be}, and a mixture of both. All three labels are wrong. From which labeled box should you draw one fruit, without looking inside, to determine all contents?",
            ("מהקופסה המסומנת ״תערובת״", "The box labeled 'mixed'"),
            [
                (f"מהקופסה המסומנת ״{ah}״", f"The box labeled '{ae}'"),
                (f"מהקופסה המסומנת ״{bh}״", f"The box labeled '{be}'"),
                ("אין דרך לזהות באמצעות פרי אחד", "No single-fruit draw can identify the contents"),
            ],
            "הקופסה המסומנת כתערובת מכילה סוג אחד בלבד. הפרי מזהה אותו, ושתי התוויות השגויות הנותרות קובעות את השאר.",
            "The mixed-labeled box is pure. Its fruit identifies it, and the other two wrong labels determine the rest.",
            "enumerate all derangements of the three labels",
            dict(valid_arrangements=arrangements),
        )
    for v, (a, b, c) in enumerate(
        [("A", "B", "C"), ("P", "Q", "R"), ("X", "Y", "Z"), ("D", "E", "F"), ("K", "L", "M")], 1
    ):
        assert len({-1, 0, 1}) == 3
        add(
            26,
            v,
            f"בין המטבעות {a}, {b}, {c} יש בדיוק מטבע כבד אחד, והאחרים שווים. שוקלים את {a} מול {b} והמאזניים מאוזנים. איזה מטבע כבד?",
            f"Among coins {a}, {b}, {c}, exactly one is heavy and the others weigh the same. Weighing {a} against {b} balances. Which coin is heavy?",
            c,
            [a, b, ("אי אפשר לקבוע גם עם המידע הזה", "It is still impossible to determine")],
            "האיזון שולל את שני המטבעות שעל המאזניים, ולכן השלישי כבד.",
            "Balance rules out both weighed coins, so the third is heavy.",
            "three heavy-coin hypotheses and balance signature",
            dict(weighed=[a, b], unweighed=c),
        )
    for v, (small, large) in enumerate([(3, 5), (4, 7), (5, 9), (2, 7), (6, 10)], 1):
        num(
            27,
            v,
            f"ממלאים כלי בנפח {large} ליטרים, ואז מוזגים ממנו לכלי ריק בנפח {small} ליטרים עד שהקטן מלא. כמה ליטרים נשארו בגדול, בלי לשפוך מים בדרך?",
            f"Fill a {large}-liter container, then pour into an empty {small}-liter container until the smaller one is full. How many liters remain in the larger container, assuming no spills?",
            large - small,
            "נפח המים נשמר; נפח הכלי הקטן נגרע מהכלי המלא.",
            "Water volume is conserved; subtract the smaller container's capacity.",
            "volume conservation",
            dict(capacities=[small, large]),
        )
    for v, players in enumerate([8, 12, 16, 7, 20], 1):
        num(
            28,
            v,
            f"בטורניר הדחה של {players} שחקנים, כל משחק מדיח בדיוק מפסיד אחד. אין פרישות או משחקי דירוג. כמה משחקים דרושים כדי שיישאר אלוף יחיד?",
            f"In a knockout tournament with {players} players, each game eliminates exactly one loser. There are no withdrawals or placement games. How many games leave one champion?",
            players - 1,
            "צריך להדיח את כל השחקנים מלבד אחד, וכל משחק מבצע הדחה אחת.",
            "Every player except the champion must be eliminated, once per game.",
            "count eliminations invariant",
            dict(players=players),
        )
    for v, people in enumerate([4, 5, 6, 7, 8], 1):
        result = len(list(itertools.combinations(range(people), 2)))
        assert result == people * (people - 1) // 2
        num(
            29,
            v,
            f"נפגשים {people} אנשים, וכל זוג לוחץ ידיים בדיוק פעם אחת. כמה לחיצות ידיים יש?",
            f"There are {people} people, and each pair shakes hands exactly once. How many handshakes occur?",
            result,
            "סופרים זוגות לא מסודרים, כדי לא לספור כל לחיצה פעמיים.",
            "Count unordered pairs, so each handshake is counted once.",
            "enumerate all unordered pairs",
            dict(people=people),
        )

    cases = [
        ("מתכנת", "חולצה כחולה", "a programmer", "a blue shirt"),
        ("רופא", "תג ירוק", "a doctor", "a green badge"),
        ("חבר מועדון", "כרטיס", "a club member", "a card"),
        ("שחיין", "כובע", "a swimmer", "a cap"),
        ("מדריך", "מפתח", "a guide", "a key"),
    ]
    for v, (ah, bh, ae, be) in enumerate(cases, 1):
        add(
            30,
            v,
            f"בקבוצה מסוימת כל מי שהוא {ah} מחזיק {bh}. דני בקבוצה ומחזיק {bh}. איזו מסקנה מתחייבת?",
            f"In a certain group, everyone who is {ae} has {be}. Danny is in the group and has {be}. Which conclusion is justified?",
            (f"אי אפשר לקבוע אם דני {ah}", f"It cannot be determined whether Danny is {ae}"),
            [
                (f"דני בהכרח {ah}", f"Danny must be {ae}"),
                (f"דני בהכרח אינו {ah}", f"Danny cannot be {ae}"),
                ("הנתונים סותרים זה את זה", "The facts contradict each other"),
            ],
            "הכלל פועל בכיוון אחד בלבד; גם מי שאינו שייך לקבוצה המקצועית יכול להחזיק בפריט.",
            "The implication works in only one direction; a nonmember of the profession may also have the item.",
            "implication countermodel",
            dict(possible_profession_values=[False, True]),
        )

    for v, (right, up) in enumerate([(2, 1), (3, 1), (2, 2), (4, 1), (3, 2)], 1):
        result = math.comb(right + up, up)
        assert result == sum(sum(x) == up for x in itertools.product([0, 1], repeat=right + up))
        num(
            40,
            v,
            f"צריך להגיע {right} צעדים ימינה ו־{up} צעדים למעלה. בכל צעד נעים יחידה אחת רק ימינה או למעלה. כמה מסלולים שונים יש אם סדר הצעדים חשוב?",
            f"Reach a point {right} steps right and {up} steps up. Each move is one unit right or up only. How many routes are possible when step order matters?",
            result,
            f"בוחרים אילו {up} מתוך {right + up} המקומות ברצף יהיו צעדים למעלה.",
            f"Choose which {up} of the {right + up} sequence positions are upward steps.",
            "binomial coefficient checked by binary-sequence enumeration",
            dict(right=right, up=up),
        )
    for v, (shirts, trousers) in enumerate([(2, 3), (3, 4), (4, 5), (2, 6), (5, 3)], 1):
        result = len(list(itertools.product(range(shirts), range(trousers))))
        num(
            41,
            v,
            f"יש {shirts} חולצות שונות ו־{trousers} זוגות מכנסיים שונים. כל שילוב מותר. כמה תלבושות אפשר ליצור מחולצה אחת ומזוג מכנסיים אחד?",
            f"There are {shirts} different shirts and {trousers} different pairs of trousers. Every combination is allowed. How many outfits use one shirt and one pair of trousers?",
            result,
            "לכל חולצה יש כל אפשרויות המכנסיים, ולכן מכפילים את מספרי הבחירות.",
            "Each shirt allows every trouser choice, so multiply the choice counts.",
            "enumerate Cartesian product",
            dict(counts=[shirts, trousers]),
        )


def build_basic_rest():
    # Vary which generation appears in the photograph, keeping the kinship chain explicit.
    relatives = [
        (
            "אני בנו היחיד של אבי. אביה של האישה שבתמונה הוא אבי.",
            "I am my father's only son. The photographed woman's father is my father.",
            ("אחיה של האישה", "The woman's brother"),
            [
                ("אביה של האישה", "The woman's father"),
                ("בנה של האישה", "The woman's son"),
                ("סבה של האישה", "The woman's grandfather"),
            ],
            "לאישה ולדובר אותו אב, ולכן הדובר הוא אחיה.",
            "The photographed person is another child of the same father, so the speaker is their brother.",
        ),
        (
            "אני בנו היחיד של אבי. אביו של הילד בתמונה הוא בנו של אבי.",
            "I am my father's only son. The photographed boy's father is my father's son.",
            ("אביו של הילד", "The boy's father"),
            [
                ("סבו של הילד", "The boy's grandfather"),
                ("אחיו של הילד", "The boy's brother"),
                ("בנו של הילד", "The boy's son"),
            ],
            "בנו היחיד של האב הוא הדובר עצמו.",
            "The father's only son is the speaker himself.",
        ),
        (
            "אני בנו היחיד של אבי. המצולם הוא אביו של אבי.",
            "I am my father's only son. The photographed man is my father's father.",
            ("נכדו של המצולם", "The photographed man's grandchild"),
            [
                ("בנו של המצולם", "The photographed man's son"),
                ("אביו של המצולם", "The photographed man's father"),
                ("אחיו של המצולם", "The photographed man's brother"),
            ],
            "אביו של האב הוא הסב, והדובר הוא נכדו.",
            "The father's father is the grandfather; the speaker is his grandchild.",
        ),
        (
            "אני בנו היחיד של אבי. המצולם הוא בנו של בני.",
            "I am my father's only son. The photographed boy is my son's son.",
            ("סבו של הילד", "The boy's grandfather"),
            [
                ("אביו של הילד", "The boy's father"),
                ("אחיו של הילד", "The boy's brother"),
                ("בנו של הילד", "The boy's son"),
            ],
            "הילד נמצא שני דורות מתחת לדובר.",
            "The boy is two generations below the speaker.",
        ),
        (
            "אין לי אחים. בתמונה מופיע אביו של בנו היחיד של אבי.",
            "I have no siblings. The photograph shows the father of my father's only son.",
            ("בנו של המצולם", "The photographed man's son"),
            [
                ("אביו של המצולם", "The photographed man's father"),
                ("אחיו של המצולם", "The photographed man's brother"),
                ("סבו של המצולם", "The photographed man's grandfather"),
            ],
            "הבן היחיד הוא הדובר, ואביו הוא המצולם.",
            "The only son is the speaker; the photographed man is his father.",
        ),
    ]
    for v, (he, en, g, b, eh, ee) in enumerate(relatives, 1):
        add(
            42,
            v,
            he + " מה הקשר של הדובר לאדם שבתמונה?",
            en + " How is the speaker related to the photographed person?",
            g,
            b,
            eh,
            ee,
            "explicit family-tree substitution",
            dict(case=v),
        )
    for v, (truth, _asked) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (0, 0)], 1):
        # Door labels are exchanged in the fifth case rather than merely renaming a guard.
        labels = ["A", "B"] if v < 5 else ["Left", "Right"]
        trap = labels[1 - truth]
        answers = []
        for honest in [False, True]:
            other_answer = 1 - truth if honest else truth
            answer = other_answer if honest else 1 - other_answer
            answers.append(labels[answer])
        assert answers == [trap, trap]
        add(
            43,
            v,
            f"שני שומרים יודעים איזו משתי הדלתות {labels[0]}, {labels[1]} היא יציאה. אחד תמיד משקר ואחד תמיד דובר אמת, ולא ידוע מי מהם נשאל. השומר נשאל איזו דלת השומר האחר יצביע עליה כיציאה, ומשיב ״{trap}״. באיזו דלת בוחרים?",
            f"Two guards know which of doors {labels[0]}, {labels[1]} is the exit. One always lies and one always tells the truth; you do not know which you asked. Asked which door the other guard would identify as the exit, the guard answers '{trap}'. Which door should you choose?",
            labels[truth],
            [
                trap,
                ("חייבים לשאול את שניהם", "You must ask both guards"),
                ("אין דרך להחליט מהתשובה", "The answer provides no way to decide"),
            ],
            "שני השומרים מצביעים בתשובה המקוננת על המלכודת; בוחרים בדלת האחרת.",
            "Both guards identify the trap in the nested answer; choose the other door.",
            "enumerate honest and lying respondent models",
            dict(exit=labels[truth], nested_answer=trap, respondents=answers),
        )
    for v, (total, gap) in enumerate([(10, 2), (18, 4), (20, 6), (25, 5), (30, 8)], 1):
        a, b = (total + gap) // 2, (total - gap) // 2
        assert a + b == total and a - b == gap
        add(
            44,
            v,
            f"לשני ילדים יחד {total} גולות. לראשון יש {gap} יותר מהשני. כמה יש לכל אחד, בסדר ראשון ואז שני?",
            f"Two children have {total} marbles in total. The first has {gap} more than the second. How many does each have, first then second?",
            f"{a}, {b}",
            [f"{b}, {a}", f"{a + 1}, {b - 1}", f"{a + gap}, {b}"],
            f"מחסרים את ההפרש, מחלקים בשניים ומחזירים אותו לראשון: {a}, {b}.",
            f"Subtract the difference, halve the rest, then return the difference to the first: {a}, {b}.",
            "substitute both sum-and-difference constraints",
            dict(total=total, difference=gap, solution=[a, b]),
        )
    for v, (rows, columns) in enumerate([(2, 3), (3, 3), (2, 5), (3, 4), (4, 4)], 1):
        count = rows * columns
        num(
            45,
            v,
            f"חפיסת שוקולד היא רשת של {rows}×{columns} ריבועים. בכל שבירה מפצלים חתיכה אחת לשתיים לאורך קו רשת, בלי לערום חתיכות. כמה שבירות דרושות להפרדת כל הריבועים?",
            f"A chocolate bar is a {rows}×{columns} grid. Each break splits one piece into two along a grid line, without stacking pieces. How many breaks separate every square?",
            count - 1,
            "כל שבירה מוסיפה חתיכה אחת, ומתחילים בחתיכה אחת.",
            "Each break adds one piece, starting from one piece.",
            "piece-count invariant with constructive row/column cuts",
            dict(rows=rows, columns=columns),
        )
    for v, (boxes, minimum, maximum) in enumerate(
        [(10, 2, 3), (6, 1, 4), (8, 3, 5), (5, 2, 6), (7, 1, 3)], 1
    ):
        claim = boxes * maximum + 1
        num(
            46,
            v,
            f"ב־{boxes} קופסאות יש בין {minimum} ל־{maximum} כדורים בכל קופסה. כדי לשלול טענה שיש בסך הכול {claim} כדורים, מהו החסם העליון הכולל שמספיק לחשב?",
            f"There are {boxes} boxes, each with between {minimum} and {maximum} balls. To refute a claimed total of {claim}, what total upper bound is sufficient?",
            boxes * maximum,
            "גם אם כל קופסה מלאה עד המקסימום, אי אפשר לעבור את מכפלת מספר הקופסאות בחסם לכל קופסה.",
            "Even if every box reaches its maximum, the total cannot exceed the number of boxes times that maximum.",
            "sum of independent per-box upper bounds",
            dict(boxes=boxes, bounds=[minimum, maximum], claim=claim),
        )
    for v, (a, b, c, d) in enumerate(
        [(9, 12, 11, 14), (8, 13, 10, 12), (10, 15, 12, 17), (7, 11, 9, 13), (13, 18, 14, 17)], 1
    ):
        start, end = max(a, c), min(b, d)
        assert end > start
        num(
            47,
            v,
            f"נועה פנויה מ־{a:02d}:00 עד {b:02d}:00 ודנה מ־{c:02d}:00 עד {d:02d}:00 באותו יום. מה אורך הפגישה הארוכה ביותר בשעות, אם שתיהן חייבות להיות פנויות לכל אורכה?",
            f"Noa is free from {a:02d}:00 to {b:02d}:00 and Dana from {c:02d}:00 to {d:02d}:00 on the same day. What is the longest meeting length in hours if both must be free throughout?",
            end - start,
            f"חלון החפיפה הוא מ־{start:02d}:00 עד {end:02d}:00.",
            f"The overlap is from {start:02d}:00 to {end:02d}:00.",
            "interval intersection",
            dict(intervals=[[a, b], [c, d]]),
        )
    weekdays = [
        ("שני", "Monday"),
        ("שלישי", "Tuesday"),
        ("רביעי", "Wednesday"),
        ("חמישי", "Thursday"),
        ("שישי", "Friday"),
        ("שבת", "Saturday"),
        ("ראשון", "Sunday"),
    ]
    for v, (day, offset) in enumerate([(0, 10), (2, 15), (4, 9), (6, 11), (1, 20)], 1):
        result = (day + offset) % 7
        add(
            48,
            v,
            f"היום יום {weekdays[day][0]}. איזה יום יהיה בעוד {offset} ימים? מחר נחשב יום אחד קדימה.",
            f"Today is {weekdays[day][1]}. What day will it be in {offset} days? Tomorrow counts as one day ahead.",
            weekdays[result],
            [weekdays[(result + i) % 7] for i in [1, 2, 3]],
            "כל שבעה ימים חוזרים לאותו יום, ולכן מתקדמים לפי השארית בחלוקה לשבע.",
            "Every seven days returns to the same weekday; advance by the remainder modulo seven.",
            "iterate weekday cycle and modulo",
            dict(start=day, days=offset, result=result),
        )
    for v, (ending, divisor, candidates) in enumerate(
        [
            (2, 4, [12, 22, 32, 52]),
            (4, 8, [24, 14, 64, 104]),
            (5, 10, [15, 20, 30, 40]),
            (6, 4, [16, 26, 36, 56]),
            (8, 16, [48, 18, 80, 128]),
        ],
        1,
    ):
        bad = [x for x in candidates if x % 10 == ending and x % divisor != 0]
        assert len(bad) == 1
        num(
            49,
            v,
            f"איזה מספר הוא דוגמה נגדית לטענה ״כל מספר חיובי שמסתיים בספרה {ending} מתחלק ב־{divisor}״?",
            f"Which number is a counterexample to 'every positive integer ending in {ending} is divisible by {divisor}'?",
            bad[0],
            f"{bad[0]} מסתיים בספרה הנדרשת אך אינו מתחלק ב־{divisor}.",
            f"{bad[0]} has the required final digit but is not divisible by {divisor}.",
            "evaluate premise and conclusion for all four candidates",
            dict(ending=ending, divisor=divisor, candidates=candidates),
            [x for x in candidates if x != bad[0]],
        )
    for v, factor in enumerate([2, 3, 4, 5, 6], 1):
        num(
            50,
            v,
            f"מכפילים את אורך כל צלע בריבוע פי {factor}. פי כמה גדל השטח?",
            f"Multiply every side length of a square by {factor}. By what factor does its area increase?",
            factor**2,
            "שטח תלוי במכפלת שני אורכים, ולכן גורם ההגדלה מוכפל בעצמו.",
            "Area multiplies two lengths, so the scale factor is squared.",
            "area ratio algebra",
            dict(linear_factor=factor),
            [factor, factor**3, factor**2 + 1],
        )
    for v, generations in enumerate([3, 4, 5, 6, 7], 1):
        fathers = generations - 1
        num(
            51,
            v,
            f"משפחה כוללת שרשרת של {generations} דורות: בכל דור אדם אחד, וכל אדם מלבד הראשון הוא בנו של הקודם. כמה אנשים שונים יש, אף שיש {fathers} תפקידי אב ו־{fathers} תפקידי בן?",
            f"A family forms a chain of {generations} generations, with one person per generation and each person after the first being the previous person's son. How many distinct people are there, although there are {fathers} father roles and {fathers} son roles?",
            generations,
            "בני הדורות האמצעיים ממלאים גם תפקיד אב וגם תפקיד בן, ולכן אין לחבר את מספרי התפקידים.",
            "Middle generations each have both roles, so role counts must not be added to count people.",
            "distinct vertices versus parent/child roles in a path",
            dict(generations=generations, father_roles=fathers, son_roles=fathers),
        )
    for v, (colors, threshold) in enumerate([(2, 3), (3, 3), (2, 4), (4, 3), (3, 4)], 1):
        result = colors * (threshold - 1) + 1
        num(
            52,
            v,
            f"כובעים יכולים להיות באחד מ־{colors} צבעים בלבד. מה מספר האנשים הקטן ביותר שמבטיח לפחות {threshold} כובעים באותו צבע?",
            f"Hats can have only {colors} possible colors. What is the smallest number of people guaranteeing at least {threshold} hats of one color?",
            result,
            f"בלי {threshold} מאותו צבע אפשר לשים לכל היותר {threshold - 1} בכל צבע; אדם נוסף מכריח חזרה.",
            f"Avoiding {threshold} of one color allows at most {threshold - 1} per color; one more person forces the threshold.",
            "pigeonhole bound with balanced extremal witness",
            dict(colors=colors, threshold=threshold),
        )
    for v, keys in enumerate([3, 4, 5, 6, 7], 1):
        num(
            53,
            v,
            f"יש {keys} מפתחות ורק אחד פותח מנעול. כל ניסיון קובע בוודאות אם המפתח מתאים. כמה ניסיונות דרושים במקרה הגרוע כדי לזהות את המפתח, כשאין חובה לפתוח בפועל?",
            f"There are {keys} keys and exactly one opens a lock. Each trial definitively reveals whether that key fits. What is the worst-case number of trials needed to identify the key, without actually having to open the lock?",
            keys - 1,
            "אם כל המפתחות שנוסו נכשלו, המפתח האחרון מזוהה בלי ניסיון נוסף.",
            "If all tested keys fail, the final untested key is identified without another trial.",
            "adversarial sequence of failures and remaining-candidate count",
            dict(keys=keys),
        )
    for v, (a, b, target) in enumerate([(3, 5, 7), (4, 7, 10), (3, 7, 8), (5, 8, 12), (4, 9, 14)], 1):
        reachable = {i * a + j * b for i in range(target // a + 1) for j in range(target // b + 1)}
        assert target not in reachable
        candidates = [target, a + b, 2 * a, 2 * b]
        assert len(set(candidates)) == 4
        num(
            54,
            v,
            f"מתחילים ב־0. בכל מהלך מותר להוסיף רק {a} או {b}, בלי חיסור. איזה סכום מבין האפשרויות אינו ניתן להשגה?",
            f"Start at 0. Each move adds only {a} or {b}, with no subtraction. Which listed total cannot be reached?",
            target,
            f"בדיקת כל הצירופים עד {target} אינה נותנת את הסכום הזה; האחרים מתקבלים במהלך אחד או שניים.",
            f"No nonnegative combination reaches {target}; every other listed value is a sum of one or two allowed moves.",
            "enumerate nonnegative linear combinations up to target",
            dict(steps=[a, b], target=target),
            candidates[1:],
        )
    for v, duration in enumerate([60, 40, 90, 50, 120], 1):
        num(
            55,
            v,
            f"חבל נשרף לגמרי בתוך {duration} דקות כשמציתים קצה אחד. הקצב לאורך החבל אינו אחיד, אך זמן השריפה של כל קטע זהה משני הכיוונים. חזיתות האש אינן משפיעות זו על זו לפני המפגש. שני הקצוות מוצתים יחד. כמה דקות נדרשות לשריפה מלאה בהצתת שני הקצוות?",
            f"A rope burns completely in {duration} minutes when lit at one end. Its burn rate along its length is nonuniform, but each segment takes the same burn time from either direction. The fronts do not interact before meeting. Both ends are lit together. How many minutes does complete burning then take?",
            Fraction(duration, 2),
            "שתי חזיתות האש צורכות יחד את זמן השריפה הכולל בקצב כפול; אין צורך שייפגשו באמצע האורך.",
            "The two fronts consume the total burn-time measure at twice the rate; they need not meet at the midpoint in length.",
            "additive burn-time measure from both ends",
            dict(single_end_minutes=duration),
        )
    for v, (sides, divisor) in enumerate([(6, 2), (8, 2), (6, 3), (10, 5), (12, 3)], 1):
        favorable = [x for x in range(1, sides + 1) if x % divisor == 0]
        fraction(
            56,
            v,
            f"מטילים קובייה הוגנת שמסומנת במספרים 1 עד {sides}. מה ההסתברות לתוצאה שמתחלקת ב־{divisor}?",
            f"Roll a fair die numbered 1 through {sides}. What is the probability of a result divisible by {divisor}?",
            Fraction(len(favorable), sides),
            f"יש {len(favorable)} תוצאות מתאימות מתוך {sides} שוות הסתברות.",
            f"There are {len(favorable)} favorable outcomes among {sides} equally likely outcomes.",
            "enumerate die outcomes",
            dict(sides=sides, divisor=divisor, favorable=favorable),
        )
    for v, (light, heavy) in enumerate([(1, 3), (2, 7), (3, 8), (4, 10), (2, 9)], 1):
        num(
            57,
            v,
            f"על כף אחת של מאזניים שמים משקולת של {heavy} ק״ג. על השנייה משקולת של {light} ק״ג ומוסיפים חומר עד לאיזון. מה מסת החומר בק״ג, בלי לחשב את מסת הכלים?",
            f"Place a {heavy}-kg weight on one balance pan. On the other place a {light}-kg weight and gradually add material until balanced. What is the material's mass in kg, ignoring container masses?",
            heavy - light,
            "באיזון מסות שתי הכפות שוות, ולכן מסת החומר היא הפרש המשקולות.",
            "At balance the pan masses are equal, so the material's mass is the weight difference.",
            "balance mass equation",
            dict(weights=[light, heavy]),
        )
    for v, weighings in enumerate([1, 2, 3, 4, 5], 1):
        sequences = list(itertools.product([-1, 0, 1], repeat=weighings))
        num(
            58,
            v,
            f"לכל שקילה במאזניים יש שלוש תוצאות אפשריות. מבצעים {weighings} שקילות ורושמים את התוצאות לפי הסדר. מהו המספר המרבי של רצפי תוצאות שונים? אין טענה שכל חידת מטבעות ניתנת לפתרון כך.",
            f"Each balance weighing has three possible outcomes. Perform {weighings} weighings and record the outcomes in order. What is the maximum number of different outcome sequences? This does not claim that every coin puzzle is solvable this way.",
            len(sequences),
            "לכל רצף קצר יש שלוש הרחבות אפשריות בשקילה הבאה.",
            "Each shorter sequence has three possible extensions in the next weighing.",
            "enumerate ternary outcome strings",
            dict(weighings=weighings),
        )
    for v, (claim_he, claim_en, good, bad) in enumerate(
        [
            ("כל מספר ראשוני אי־זוגי", "Every prime number is odd", 2, [3, 5, 7]),
            ("כל מספר זוגי מתחלק ב־4", "Every even number is divisible by 4", 6, [4, 8, 12]),
            ("כל ריבוע מושלם זוגי", "Every perfect square is even", 9, [4, 16, 36]),
            ("כל מספר שמתחלק ב־3 מתחלק ב־6", "Every multiple of 3 is a multiple of 6", 9, [6, 12, 18]),
            (
                "כל מספר שלם חיובי גדול מ־1 אינו ריבוע שלם",
                "Every positive integer greater than 1 is not a perfect square",
                4,
                [2, 3, 5],
            ),
        ],
        1,
    ):
        num(
            59,
            v,
            f"איזה מספר מפריך לבדו את הטענה ״{claim_he}״?",
            f"Which number alone refutes the claim '{claim_en}'?",
            good,
            "דוגמה נגדית אחת מספיקה להפריך טענה שמנוסחת על כל המספרים בתחום.",
            "One counterexample is enough to refute a universal claim.",
            "explicit premise-and-conclusion counterexample",
            dict(claim=claim_en, witness=good),
            bad,
        )
    for v, (red, blue) in enumerate([(1, 3), (2, 5), (3, 1), (4, 6), (5, 2)], 1):
        fraction(
            60,
            v,
            f"שק מכיל רק כדורים אדומים וכחולים, לפחות אחד מכל צבע, אך מספריהם אינם ידועים. שולפים כדור אחד באקראי, כך שלכל כדור הסתברות שווה. איזו הסתברות לאדום יכולה להתאים להרכב אפשרי של {red} אדומים ו־{blue} כחולים, ולכן מדגימה שההסתברות אינה בהכרח חצי?",
            f"A bag has only red and blue balls, at least one of each, with unspecified counts. Draw one ball uniformly at random, so each ball is equally likely. What red probability is possible for {red} red and {blue} blue balls, illustrating that the probability need not be one half?",
            Fraction(red, red + blue),
            "הסיכוי הוא מספר האדומים חלקי מספר הכדורים הכולל, והוא תלוי בהרכב.",
            "The probability is red count divided by total count, and depends on the composition.",
            "finite uniform sample space",
            dict(red=red, blue=blue),
        )


def build_expansion():
    test_cases = [
        ("B", "A", "C", "D", (1, 0)),
        ("B", "A", "C", "D", (0, 1)),
        ("B", "A", "C", "D", (0, 0)),
        ("B", "A", "C", "D", (1, 1)),
        ("C", "D", "B", "A", (1, 0)),
    ]
    for v, (b, a, c, d, observed) in enumerate(test_cases, 1):
        mapping = {a: (0, 0), b: (1, 0), c: (0, 1), d: (1, 1)}
        good = next(k for k, value in mapping.items() if value == observed)
        words_he = ["שלילית", "חיובית"]
        words_en = ["negative", "positive"]
        add(
            62,
            v,
            f"בדיוק אחד מהבקבוקים A, B, C, D מזוהם. בדיקה חיובית אם ורק אם יש בדגימה זיהום. בודקים במקביל תערובות {b}+{d} ו־{c}+{d}, בסדר זה. התקבלו {words_he[observed[0]]} ואז {words_he[observed[1]]}. איזה בקבוק מזוהם?",
            f"Exactly one of bottles A, B, C, D is contaminated. A test is positive if and only if its pool contains contamination. Simultaneously test pools {b}+{d} and {c}+{d}, in that order. Results are {words_en[observed[0]]}, then {words_en[observed[1]]}. Which bottle is contaminated?",
            good,
            [x for x in mapping if x != good],
            "כל בקבוק יוצר זוג תוצאות שונה; מתאימים את הזוג שנצפה לבקבוק.",
            "Each bottle has a distinct result pair; match the observed pair to its bottle.",
            "enumerate pooled-test signatures",
            dict(signatures=mapping, observed=observed),
        )
    for v, (gap, moves) in enumerate(
        [(5, [1, 2, -1]), (8, [3, -2, 4]), (12, [-1, -1, 5]), (7, [2, 2, -3]), (20, [-4, 6, 1])], 1
    ):
        positions = [sum(moves), gap + sum(moves)]
        assert positions[1] - positions[0] == gap
        num(
            63,
            v,
            f"שני רובוטים מתחילים במרחק {gap} מטרים על קו אינסופי. אין להם סמנים או חיישנים, הכיוון שלהם זהה, ובכל רגע הם מבצעים יחד אותה תנועה. לאחר שכל אחד ביצע היסטים של {', '.join(map(str, moves))} מטרים, מה המרחק ביניהם?",
            f"Two robots start {gap} meters apart on an infinite line. They have no markers or sensors, share the same orientation, and always execute identical moves simultaneously. After each makes displacements {', '.join(map(str, moves))} meters, what is their separation?",
            gap,
            "שניהם מוסיפים למיקום אותו היסט מצטבר, ולכן הפרש המיקומים נשמר.",
            "Both positions receive the same cumulative displacement, so their difference is preserved.",
            "translation invariance checked with signed displacements",
            dict(initial_gap=gap, moves=moves),
        )
    for v, (people, bound) in enumerate([(3, 10), (4, 20), (5, 50), (2, 100), (6, 1000)], 1):
        add(
            64,
            v,
            f"יש {people} מבקרים. מובטח שכל אחד ייבחר לביקור אינסוף פעמים בהמשך, אך אין מגבלה נוספת על סדר הבחירה. מדוע אין בכך הבטחה שכולם יבקרו בתוך {bound} הביקורים הראשונים?",
            f"There are {people} visitors. Each is guaranteed to be chosen infinitely often eventually, with no further scheduling restriction. Why does this not guarantee that all will visit within the first {bound} visits?",
            (
                f"אפשר לבחור אדם אחד {bound} פעמים ואז להתחיל סבב הוגן",
                f"One person may be chosen {bound} times before a fair cycle begins",
            ),
            [
                (
                    "ביקורים אינסופיים מחייבים שכל הביקורים יהיו יחד",
                    "Infinitely many visits require simultaneous visits",
                ),
                ("כל אדם יכול להיבחר רק פעם אחת", "Each person can be chosen only once"),
                ("ההבטחה שוללת ביקורים חוזרים", "The guarantee forbids repeated visits"),
            ],
            "קידומת ארוכה ככל שנרצה אינה מפרה את הוגנות ההמשך.",
            "An arbitrarily long unfair prefix does not violate eventual infinite visitation.",
            "construct an arbitrary finite prefix followed by periodic fair schedule",
            dict(people=people, prefix_length=bound),
        )
    for v, (total, heads, chosen_heads) in enumerate(
        [(12, 3, 1), (15, 4, 2), (20, 5, 0), (18, 6, 4), (10, 2, 2)], 1
    ):
        after = heads - chosen_heads
        assert after == (heads - chosen_heads)
        num(
            65,
            v,
            f"בין {total} מטבעות יש בדיוק {heads} מטבעות עץ. בוחרים בדיוק {heads} מטבעות; בפועל היו ביניהם {chosen_heads} מטבעות עץ, אף שלא רואים זאת. הופכים את כל הנבחרים. כמה מטבעות עץ יהיו בכל קבוצה אחרי ההיפוך?",
            f"Among {total} coins, exactly {heads} show heads. Select exactly {heads} coins; in this case the selection contains {chosen_heads} heads, though their faces cannot be seen. Flip every selected coin. How many heads will each group then contain?",
            after,
            f"מחוץ לקבוצה יש {heads - chosen_heads} מטבעות עץ; בקבוצה ההיפוך הופך את {heads - chosen_heads} מטבעות הפלי לעץ.",
            f"The unselected group has {heads - chosen_heads} heads; flipping turns the selection's {heads - chosen_heads} tails into heads.",
            "heads conservation before flip and complement after flip",
            dict(total=total, total_heads=heads, selected_count=heads, selected_heads=chosen_heads),
        )
    for v, (people, signals) in enumerate([(3, 3), (4, 4), (5, 5), (6, 6), (8, 8)], 1):
        add(
            66,
            v,
            f"מונה ראה {signals} אותות באור משותף שמצבו ההתחלתי ידוע וכבוי. יש {people} משדרים, והמונה אוסף כל אות פעם אחת. איזה כלל מאפשר להסיק מהספירה שכל המשדרים כבר השתתפו?",
            f"A counter observed {signals} signals on a shared light initially known to be off. There are {people} senders, and each signal is collected exactly once. Which rule makes the count certify that all senders participated?",
            (
                "כל משדר רשאי לשלוח אות אחד בלבד בכל התהליך",
                "Each sender may send at most one signal in the entire process",
            ),
            [
                ("כל משדר רשאי לשלוח בכל ביקור", "Each sender may signal on every visit"),
                ("כל משדר רשאי לשלוח ללא הגבלה", "Each sender may signal without limit"),
                ("האות נחשב מחדש בכל ביקור של המונה", "The same signal is recounted on every counter visit"),
            ],
            "עם מכסה של אות אחד לאדם, מספר אותות כזה דורש את כל האנשים השונים.",
            "With a lifetime limit of one signal per person, that many signals require all distinct senders.",
            "sender-capacity counting bound",
            dict(senders=people, signals=signals, max_per_sender=1),
        )
    for v, (path, length) in enumerate([("123", 4), ("1234", 5), ("2456", 5), ("13579", 6), ("248", 4)], 1):
        edges = list(zip(path, path[1:], strict=False))
        assert length > len(path)
        add(
            67,
            v,
            f"מותרות רק זוגות הספרות הסמוכות {', '.join(a + b for a, b in edges)}. המחרוזת חייבת להתחיל ב־{path[0]}. מדוע אי אפשר לבנות מחרוזת באורך {length}?",
            f"The only allowed adjacent digit pairs are {', '.join(a + b for a, b in edges)}. The string must start with {path[0]}. Why can no string of length {length} be built?",
            (
                f"המסלול נתקע בספרה {path[-1]}, שאין ממנה מעבר מותר",
                f"The path ends at digit {path[-1]}, which has no allowed outgoing transition",
            ),
            [
                (
                    "הספרה ההתחלתית אינה מאפשרת שום מעבר",
                    "The starting digit has no allowed outgoing transition",
                ),
                ("מספר זוגות אי־זוגי תמיד מונע מחרוזת", "An odd number of pairs always prevents a string"),
                ("כל זוג מותר מבטיח מחרוזת בכל אורך", "Any allowed pair guarantees strings of all lengths"),
            ],
            "מעברים חוקיים מקומית אינם מבטיחים שאפשר להמשיך את המסלול.",
            "Locally legal transitions do not guarantee that the path can continue.",
            "trace deterministic acyclic adjacency graph",
            dict(edges=edges, required_length=length),
        )
    for v, (maximum, target, multiple) in enumerate(
        [(3, 12, 1), (2, 12, 2), (4, 20, 1), (3, 20, 2), (2, 15, 1)], 1
    ):
        start = target - multiple * (maximum + 1)

        def win(x, target=target, maximum=maximum):
            return any(x + i == target or not win(x + i) for i in range(1, maximum + 1) if x + i <= target)

        assert not win(start)
        add(
            68,
            v,
            f"הסכום כעת {start}. שני שחקנים מוסיפים בתורם מספר שלם מ־1 עד {maximum}; הגעה בדיוק ל־{target} מנצחת ואסור לעבור אותו. איזו תגובה קבועה מאפשרת ליריב לנצח מול כל תוספת x של השחקן שבתור?",
            f"The total is {start}. Players alternate adding an integer from 1 to {maximum}; reaching exactly {target} wins and overshooting is forbidden. Which reply lets the opponent force a win after every move x by the current player?",
            f"{maximum + 1} − x",
            [f"{maximum + 2} − x", f"{maximum} + x", f"{maximum + 1} + x"],
            f"כל זוג תורות מוסיף {maximum + 1}, והיריב שומר כך על מרחק שהוא כפולה שלו מהיעד.",
            f"Each pair of turns adds {maximum + 1}, so the opponent preserves a multiple of this distance from the target.",
            "full recursive minimax of finite game",
            dict(start=start, target=target, max_add=maximum),
        )
    for v, (fast, slow) in enumerate([(2, 7), (1, 5), (3, 8), (4, 9), (2, 11)], 1):
        num(
            69,
            v,
            f"אדם A חוצה מנהרה ב־{fast} דקות ו־B ב־{slow}. הם חוצים יחד בקצב האיטי, ואז A חוזר לבדו עם הפנס. כמה דקות עברו בסך הכול?",
            f"A crosses a tunnel in {fast} minutes and B in {slow}. They cross together at the slower pace, then A returns alone with the torch. How many minutes elapse in total?",
            slow + fast,
            "החצייה המשותפת נמשכת כמו האדם האיטי; מוסיפים את זמן החזרה של המהיר.",
            "The shared crossing takes the slower person's time; add the faster person's return time.",
            "maximum simultaneous duration plus serial return",
            dict(individual_times=[fast, slow]),
        )
    for v, (short, long) in enumerate([(1, 4), (2, 5), (3, 7), (2, 8), (4, 9)], 1):
        short_total = 2 * short + long
        long_total = 2 * long + short
        assert short_total < long_total
        num(
            70,
            v,
            f"מכונה אחת מבצעת שתי עבודות של {short} ו־{long} דקות, ללא הפסקות. שתיהן זמינות בזמן 0. מה סכום זמני הסיום הקטן ביותר, כאשר מודדים את שני זמני הסיום מזמן 0?",
            f"One machine performs jobs lasting {short} and {long} minutes without interruption. Both are available at time 0. What is the smallest sum of their completion times, measuring both from time 0?",
            short_total,
            f"הקצרה תחילה: זמני הסיום הם {short} ו־{short + long}, וסכומם {short_total}.",
            f"Short first: completion times are {short} and {short + long}, totaling {short_total}.",
            "enumerate both job orders",
            dict(durations=[short, long], totals=[short_total, long_total]),
        )
    for v, tosses in enumerate([2, 3, 4, 5, 6], 1):
        states = list(itertools.product([0, 1], repeat=tosses))
        result = Fraction(sum(any(x) for x in states), len(states))
        assert result == 1 - Fraction(1, 2**tosses)
        fraction(
            71,
            v,
            f"מטילים מטבע הוגן {tosses} פעמים באופן עצמאי. מה ההסתברות לקבל לפחות פעם אחת עץ?",
            f"Toss a fair coin independently {tosses} times. What is the probability of at least one head?",
            result,
            "מחסרים מאחת את הסיכוי שכל ההטלות יהיו פלי.",
            "Subtract the probability of all tails from one.",
            "enumerate all binary outcomes and check complementary event",
            dict(tosses=tosses),
        )
    for v, p in enumerate(
        [Fraction(1, 4), Fraction(1, 3), Fraction(2, 3), Fraction(3, 4), Fraction(1, 5)], 1
    ):
        prob = p * (1 - p)
        assert prob == (1 - p) * p
        fraction(
            72,
            v,
            f"למטבע הסתברות קבועה {p} לעץ, וההטלות עצמאיות. מטילים פעמיים. מה ההסתברות לכל אחד מהרצפים עץ־פלי ופלי־עץ, כך שאפשר לקבל מהם ביט הוגן אחרי דחיית זוגות שווים?",
            f"A coin has fixed heads probability {p}, with independent tosses. Toss it twice. What is the probability of each of heads-tails and tails-heads, allowing a fair bit after discarding equal pairs?",
            prob,
            "שני סדרי ההטלות מכילים עץ אחד ופלי אחד, ולכן בשניהם מכפלת ההסתברויות זהה.",
            "Both orders contain one head and one tail, so their probability products are equal.",
            "compare independent ordered-pair probabilities",
            dict(heads_probability=str(p)),
        )
    # Logical knowledge cases ask what ignorance rules out, varying colors and front/rear roles.
    colors = [
        ("לבן", "שחור", "white", "black"),
        ("אדום", "כחול", "red", "blue"),
        ("ירוק", "צהוב", "green", "yellow"),
        ("סגול", "כתום", "purple", "orange"),
        ("אפור", "חום", "gray", "brown"),
    ]
    for v, (common_h, rare_h, common_e, rare_e) in enumerate(colors, 1):
        possible = [(a, b) for a, b in itertools.product([0, 1], repeat=2) if a + b <= 1]
        front_values = [b for a, b in possible if len([x for x, y in possible if y == b]) > 1]
        assert set(front_values) == {0}
        add(
            73,
            v,
            f"לשני אנשים כובעים בצבע {common_h} או {rare_h}, וידוע לשניהם שיש לכל היותר כובע {rare_h} אחד. האחורי רואה את כובע הקדמי ואומר בכנות שאינו יודע את צבע כובעו שלו. מה צבע כובע הקדמי?",
            f"Two people wear {common_e} or {rare_e} hats. Both know there is at most one {rare_e} hat. The rear person sees the front hat and truthfully says they cannot determine their own hat color. What is the front hat's color?",
            (common_h, common_e),
            [
                (rare_h, rare_e),
                ("שני הצבעים עדיין אפשריים", "Either color remains possible"),
                ("הנתונים סותרים את האמירה", "The statement contradicts the conditions"),
            ],
            "אילו הקדמי היה בצבע המוגבל, האחורי היה יודע שכובעו בצבע האחר. חוסר הידיעה שולל זאת.",
            "If the front hat had the restricted color, the rear person would know their own hat had the other color. Their ignorance rules that out.",
            "enumerate possible worlds and rear observer's knowledge",
            dict(possible_worlds=possible),
        )
    for v, (observed, repeats) in enumerate([(0, 1), (1, 1), (0, 3), (1, 4), (0, 10)], 1):
        states = [f"{a}{b}" for a, b in itertools.product([0, 1], repeat=2) if a ^ b == observed]
        add(
            74,
            v,
            f"שני ביטים נסתרים A ו־B אינם משתנים. נמדד רק A XOR B, והתקבלה התוצאה {observed} בכל אחת מ־{repeats} מדידות זהות. איזה זוג מצבים נשאר אפשרי?",
            f"Hidden bits A and B do not change. Only A XOR B is measured, giving {observed} in each of {repeats} identical measurements. Which pair of states remains possible?",
            " / ".join(states),
            ["00 / 01", "00 / 10", "10 / 11"],
            "אותה תצפית על אותו מצב אינה מוסיפה מידע; שני הזוגות נותנים אותו XOR.",
            "Repeating the same observation of an unchanged state adds no information; both states give the same XOR.",
            "enumerate XOR preimage",
            dict(observed=observed, repeats=repeats, possible=states),
        )
    for v, (a, b) in enumerate([(2, 5), (3, 8), (6, 7), (4, 9), (1, 10)], 1):
        assert (a + b) % 2
        add(
            75,
            v,
            f"בשתי קערות יש {a} ו־{b} גולות. כל מהלך מעביר גולה אחת מקערה לא ריקה לאחרת, בלי להוסיף או להוציא גולות. מה מונע השגת כמויות שוות?",
            f"Two bowls contain {a} and {b} marbles. Each move transfers one marble from a nonempty bowl to the other, without adding or removing marbles. What prevents equal counts?",
            ("הסכום הכולל אי־זוגי ונשמר", "The preserved total is odd"),
            [
                (
                    "אי אפשר להעביר יותר מגולה אחת בכל התהליך",
                    "Only one marble may be moved in the entire process",
                ),
                ("כל קערה שומרת על מספרה ההתחלתי", "Each bowl preserves its initial count"),
                ("מספר הגולות הכולל גדל בכל העברה", "The total grows with each transfer"),
            ],
            "שתי כמויות שלמות שוות מסתכמות למספר זוגי, בעוד סכום אי־זוגי נשמר בכל מהלך.",
            "Two equal integer counts have an even total, while transfers preserve the odd total.",
            "conservation and integer parity contradiction",
            dict(counts=[a, b], total=a + b),
        )
    for v, (start, divisor, steps) in enumerate([(1, 2, 3), (3, 2, 4), (1, 3, 2), (5, 2, 5), (2, 3, 3)], 1):
        value = Fraction(start, divisor**steps)
        fraction(
            76,
            v,
            f"מתחילים במספר הממשי {start} ומחלקים ב־{divisor} בכל צעד, בחשבון מדויק. מה הערך אחרי {steps} צעדים, שממחיש שירידה מתמדת אינה מחייבת הגעה לאפס בזמן סופי?",
            f"Start at the real number {start} and divide by {divisor} at every step, using exact arithmetic. What is the value after {steps} steps, illustrating that continued decrease need not reach zero in finite time?",
            value,
            "לאחר מספר סופי של חלוקות המכנה סופי והמונה חיובי, ולכן התוצאה חיובית.",
            "After finitely many divisions the denominator is finite and the numerator positive, so the result is positive.",
            "exact rational repeated division",
            dict(start=start, divisor=divisor, steps=steps),
        )
    for v, (total, a, b) in enumerate([(10, 6, 5), (20, 12, 11), (15, 9, 10), (12, 8, 7), (25, 16, 14)], 1):
        result = a + b - total
        assert 0 <= result <= min(a, b)
        num(
            77,
            v,
            f"בקבוצה של {total} אנשים כולם יודעים לפחות אחת מהשפות Python ו־C. יש {a} שיודעים Python ו־{b} שיודעים C. כמה יודעים את שתיהן?",
            f"In a group of {total} people, everyone knows at least one of Python and C. There are {a} people who know Python and {b} people who know C. How many know both?",
            result,
            "חיבור הגדלים של שתי הקבוצות סופר את החיתוך פעמיים; מפחיתים את מספר האנשים השונים כדי למצוא את גודל החיתוך.",
            "The sum of the two group sizes includes the overlap twice; subtract the number of distinct people to recover the overlap size.",
            "inclusion-exclusion cardinality equation",
            dict(union=total, counts=[a, b]),
        )
    for v, floors in enumerate([3, 4, 5, 6, 7], 1):
        num(
            78,
            v,
            f"יש כדור זכוכית יחיד ובניין של {floors} קומות. הכדור נשבר מקומת סף ומעלה; ייתכן שאינו נשבר באף קומה. לאחר שבירה אין כדור חלופי. כמה הטלות דרושות במקרה הגרוע לזיהוי הסף בוודאות?",
            f"There is one glass ball and a building with {floors} floors. The ball breaks at a threshold floor and above; it may not break on any floor. No replacement is available. How many drops are needed in the worst case to identify the threshold with certainty?",
            floors,
            "חייבים לבדוק קומות מהנמוכה לגבוהה; דילוג על קומה עלול להשאיר אפשרויות שלא ניתן להבחין ביניהן אחרי שבירה.",
            "Test upward one floor at a time; skipping a floor can leave indistinguishable thresholds after breakage.",
            "one-resource threshold decision-tree lower bound and ascending construction",
            dict(floors=floors),
        )
    for v, number in enumerate([123, 245, 702, 1011, 4321], 1):
        digits = list(map(int, str(number)))
        total = sum(digits)
        assert number % 3 == total % 3
        num(
            79,
            v,
            f"לפי מבחן סכום הספרות, מה השארית בחלוקת {number} ב־3?",
            f"Using the digit-sum test, what is the remainder when {number} is divided by 3?",
            number % 3,
            f"סכום הספרות הוא {total}; לכל חזקה של 10 שארית 1 בחלוקה ל־3, ולכן השארית נשמרת.",
            f"The digit sum is {total}; every power of 10 has remainder 1 modulo 3, so the remainder is preserved.",
            "decimal place-value modular identity",
            dict(number=number, digit_sum=total),
            [x for x in range(4) if x != number % 3],
        )
    for v, (original, multiplier, addition) in enumerate(
        [(7, 2, 3), (5, 3, 4), (9, 2, 5), (6, 4, 2), (8, 3, 7)], 1
    ):
        result = original * multiplier + addition
        assert Fraction(result - addition, multiplier) == original
        num(
            80,
            v,
            f"בחרתי מספר, כפלתי אותו ב־{multiplier}, ואז הוספתי {addition}. התוצאה היא {result}. מה המספר המקורי?",
            f"I chose a number, multiplied it by {multiplier}, then added {addition}. The result is {result}. What was the original number?",
            original,
            "מבטלים קודם את הפעולה האחרונה: מחסרים את התוספת ואז מחלקים בגורם הכפל.",
            "Undo the last operation first: subtract the addition, then divide by the multiplier.",
            "inverse operations checked by forward substitution",
            dict(multiplier=multiplier, addition=addition, result=result),
        )
    for v, (circumference, height, turns) in enumerate(
        [(3, 4, 1), (6, 8, 1), (5, 12, 1), (3, 8, 2), (4, 15, 2)], 1
    ):
        length = math.isqrt((circumference * turns) ** 2 + height**2)
        assert length**2 == (circumference * turns) ** 2 + height**2
        num(
            81,
            v,
            f"חוט על גליל שהיקפו {circumference} ס״מ וגובהו {height} ס״מ עושה {turns} סיבובים מלאים מהתחתית לפסגה. הגובה עולה ביחס קבוע לזווית הסיבוב. מה אורך החוט בס״מ? מתעלמים מעוביו.",
            f"A wire on a cylinder of circumference {circumference} cm and height {height} cm makes {turns} full turns from bottom to top. Height increases proportionally to rotation angle. What is the wire length in cm? Ignore its thickness.",
            length,
            "בפריסת הגליל מתקבל קו ישר; מפעילים פיתגורס על הגובה ועל המרחק האופקי המצטבר.",
            "Unrolling gives a straight segment; apply Pythagoras to the height and accumulated horizontal distance.",
            "unrolled-cylinder Euclidean length",
            dict(circumference=circumference, height=height, turns=turns),
        )
    for v, candidates in enumerate(
        [[16, 12, 18, 20], [25, 15, 24, 30], [49, 21, 35, 42], [81, 27, 45, 63], [1, 2, 3, 6]], 1
    ):
        counts = [sum(x % d == 0 for d in range(1, x + 1)) for x in candidates]
        good = [x for x, c in zip(candidates, counts, strict=True) if c % 2]
        assert len(good) == 1
        num(
            82,
            v,
            f"לאיזה מבין המספרים {'; '.join(map(str, candidates))} יש מספר אי־זוגי של מחלקים חיוביים?",
            f"Which of the numbers {'; '.join(map(str, candidates))} has an odd number of positive divisors?",
            good[0],
            "מחלקים מופיעים בזוגות מלבד השורש בריבוע מושלם, שמזווג עם עצמו.",
            "Divisors pair up except for a perfect square's square root, which pairs with itself.",
            "enumerate divisors and verify perfect-square criterion",
            dict(candidates=candidates, divisor_counts=counts),
            [x for x in candidates if x != good[0]],
        )
    for v, positions in enumerate([[0, 4, 10], [-5, 1, 9], [2, 7, 8], [0, 3, 20], [-8, -2, 4]], 1):
        median = sorted(positions)[1]
        sums = {x: sum(abs(x - p) for p in positions) for x in range(min(positions) - 2, max(positions) + 3)}
        assert [x for x, total in sums.items() if total == min(sums.values())] == [median]
        num(
            83,
            v,
            f"שלושה בתים נמצאים על ישר בקואורדינטות {', '.join(map(str, positions))}. באיזו קואורדינטה על אותו ישר סכום מרחקי ההליכה משלושתם הוא הקטן ביותר?",
            f"Three houses lie on a line at coordinates {', '.join(map(str, positions))}. At which coordinate on that line is the sum of walking distances from all three smallest?",
            median,
            "לשלושה מיקומים שונים, החציון ממזער את סכום המרחקים המוחלטים.",
            "For three distinct positions, the median minimizes the sum of absolute distances.",
            "enumerate objective around all integer candidate positions plus median theorem",
            dict(positions=positions, minimum=sum(abs(median - p) for p in positions)),
            [median + 1, median + 2, median + 3],
        )
    for v, (known_faster, _top) in enumerate([(2, 2), (3, 3), (4, 4), (5, 1), (6, 2)], 1):
        num(
            84,
            v,
            f"לסוסים מהירויות קבועות ושונות. ידוע שלפחות {known_faster} סוסים שונים מהירים מ־C. מה הדירוג הטוב ביותר ש־C עדיין יכול להשיג? דירוג 1 הוא המהיר ביותר.",
            f"Horses have fixed distinct speeds. At least {known_faster} distinct horses are known to be faster than C. What is the best rank C can still achieve? Rank 1 is fastest.",
            known_faster + 1,
            "כל סוס שכבר ידוע כמהיר יותר חייב לתפוס מקום לפני C.",
            "Every horse already known to be faster must rank ahead of C.",
            "ranking lower bound with witness order",
            dict(known_faster=known_faster),
        )
    for v, sides in enumerate([4, 6, 8, 10, 12], 1):
        expected = Fraction(sum(range(1, sides + 1)), sides)
        num(
            85,
            v,
            f"מטילים קובייה הוגנת המסומנת 1 עד {sides}. מה תוחלת המספר שמתקבל? התוחלת אינה חייבת להיות תוצאה של הטלה יחידה.",
            f"Roll a fair die numbered 1 through {sides}. What is the expected result? The expectation need not be an outcome of one roll.",
            expected,
            "התוחלת היא ממוצע משוקלל; בתוצאות שוות הסתברות זהו הממוצע הרגיל.",
            "Expectation is a weighted average; for equally likely outcomes it is the ordinary mean.",
            "exact finite weighted expectation",
            dict(sides=sides),
        )
    for v, (streak, requested) in enumerate(
        [(4, "tails"), (6, "heads"), (10, "tails"), (3, "heads"), (20, "tails")], 1
    ):
        word_h = "פלי" if requested == "tails" else "עץ"
        fraction(
            86,
            v,
            f"מטבע הוגן הוטל באופן עצמאי {streak} פעמים והראה עץ בכל ההטלות. מה ההסתברות ל־{word_h} בהטלה הבאה, אם המטבע נשאר הוגן וההטלות עצמאיות?",
            f"A fair coin was tossed independently {streak} times and showed heads every time. What is the probability of {requested} on the next toss, if fairness and independence remain unchanged?",
            Fraction(1, 2),
            "עצמאות קובעת שהעבר אינו משנה את הסתברות ההטלה הבאה.",
            "Independence means past results do not change the next toss's probability.",
            "independent conditional probability factorization",
            dict(prior_heads=streak, next=requested),
        )
    for v, (coins, target) in enumerate(
        [([1, 3, 4], 6), ([1, 4, 5], 8), ([1, 5, 6], 10), ([1, 6, 7], 12), ([1, 7, 8], 14)], 1
    ):
        dp = [0] + [target + 1] * target
        for amount in range(1, target + 1):
            dp[amount] = min([dp[amount - c] + 1 for c in coins if c <= amount])
        left = target
        greedy = 0
        while left:
            c = max(c for c in coins if c <= left)
            left -= c
            greedy += 1
        assert dp[target] == 2 and greedy > 2
        num(
            87,
            v,
            f"משלמים בדיוק {target} במטבעות שערכיהם {', '.join(map(str, coins))}, עם כמות בלתי מוגבלת מכל ערך. מהו מספר המטבעות המזערי, אף שבחירת המטבע הגדול האפשרי בכל צעד אינה מיטבית כאן?",
            f"Pay exactly {target} using unlimited coins of values {', '.join(map(str, coins))}. What is the minimum coin count, even though choosing the largest coin that fits at each step is not optimal here?",
            dp[target],
            f"שני מטבעות בערך {coins[1]} מספיקים; אין מטבע בערך הסכום עצמו. הבחירה החמדנית משתמשת ב־{greedy} מטבעות.",
            f"Two coins of value {coins[1]} suffice; there is no coin worth the entire total. Greedy uses {greedy} coins.",
            "dynamic programming optimum compared with greedy trace",
            dict(coins=coins, target=target, greedy=greedy),
            [1, greedy, greedy + 1],
        )
    for v, names in enumerate(
        [("A", "B", "C"), ("R", "G", "B"), ("X", "Y", "Z"), ("P", "Q", "R"), ("D", "E", "F")], 1
    ):
        a, b, c = names
        edges = {(a, b), (b, c), (c, a)}
        valid = [
            order
            for order in itertools.permutations(names)
            if all((order[i], order[j]) in edges for i in range(3) for j in range(i + 1, 3))
        ]
        assert valid == []
        add(
            88,
            v,
            f"במשחק {a} מנצח את {b}, {b} מנצח את {c}, ו־{c} מנצח את {a}. מה מונע סידור שלהם כך שכל פריט מנצח כל פריט שאחריו?",
            f"In a game, {a} beats {b}, {b} beats {c}, and {c} beats {a}. What prevents ordering them so that each item beats every later item?",
            ("היחס יוצר מעגל ניצחונות", "The relation forms a cycle"),
            [
                ("יש מספר אי־זוגי של פריטים", "There is an odd number of items"),
                ("אין מנצח בשום זוג", "No pair has a winner"),
                ("כל אחד מנצח את כולם", "Every item beats every other item"),
            ],
            "הפריט הראשון תמיד מפסיד לאחד מהפריטים שמופיעים אחריו.",
            "Whichever item comes first loses to one of the items appearing later.",
            "enumerate all six total orders against directed cycle",
            dict(edges=sorted(edges)),
        )


def build_extended():
    for v, (people, limit, extra) in enumerate([(3, 2, 1), (4, 2, 1), (5, 2, 1), (3, 3, 1), (4, 3, 2)], 1):
        threshold = (people - 1) * limit + extra + 1
        assert threshold > extra + (people - 1) * limit
        num(
            101,
            v,
            f"יש {people} משדרים, וכל אחד רשאי לשלוח לכל היותר {limit} אותות. המונה אוסף כל אות פעם אחת, ומצב התחלתי לא ידוע עלול להוסיף עד {extra} ספירות ללא משדר. מהי הספירה הקטנה ביותר שמוכיחה שכולם השתתפו?",
            f"There are {people} senders, each allowed at most {limit} signals. Each signal is collected once, and an unknown initial state may add up to {extra} counts without a sender. What is the smallest count proving everyone participated?",
            threshold,
            f"אם אדם אחד לא השתתף, אפשר להגיע לכל היותר ל־{threshold - 1}, כולל הספירות הנוספות.",
            f"If one sender has not participated, the total is at most {threshold - 1}, including extra counts.",
            "capacity bound excluding one participant",
            dict(senders=people, lifetime_limit=limit, extra_counts=extra),
        )
    actions = [
        (
            "A דלוק ומציין הודעה שלא נקראה; B כבוי.",
            "A is on, marking an unread message; B is off.",
            ("להדליק רק את B", "Turn only B on"),
        ),
        (
            "A דלוק ומציין הודעה שלא נקראה; B דלוק.",
            "A is on, marking an unread message; B is on.",
            ("לכבות רק את B", "Turn only B off"),
        ),
        (
            "A כבוי ומציין הודעה שלא נקראה; B כבוי.",
            "A is off, marking an unread message; B is off.",
            ("להדליק רק את B", "Turn only B on"),
        ),
        (
            "A כבוי ומציין הודעה שלא נקראה; B דלוק.",
            "A is off, marking an unread message; B is on.",
            ("לכבות רק את B", "Turn only B off"),
        ),
        (
            "B דלוק ומציין הודעה שלא נקראה; A כבוי.",
            "B is on, marking an unread message; A is off.",
            ("להדליק רק את A", "Turn only A on"),
        ),
    ]
    for v, (he, en, good) in enumerate(actions, 1):
        message = "B" if v == 5 else "A"
        spare = "A" if v == 5 else "B"
        add(
            102,
            v,
            f"בכל ביקור חייבים להפוך בדיוק מתג אחד. {he} רק המונה רשאי לשנות את מתג ההודעה. מה יעשה מבקר אחר כדי לשמור את המידע ולקיים את חובת הפעולה?",
            f"Every visit must toggle exactly one switch. {en} Only the counter may change the message switch. What should another visitor do to preserve the information and satisfy the mandatory action?",
            good,
            [
                (f"להפוך רק את {message}", f"Toggle only {message}"),
                ("להפוך את שני המתגים", "Toggle both switches"),
                ("לא לשנות שום מתג", "Change neither switch"),
            ],
            f"הופכים את {spare}, שאינו נושא את ההודעה, ומשאירים את מתג ההודעה ללא שינוי.",
            f"Toggle {spare}, which carries no message, and leave the message switch unchanged.",
            "enumerate legal one-switch changes preserving message bit",
            dict(message_switch=message, spare_switch=spare),
        )
    for v, p in enumerate(
        [Fraction(1, 2), Fraction(1, 3), Fraction(2, 3), Fraction(1, 4), Fraction(3, 4)], 1
    ):
        result = p / (1 - (1 - p) ** 2)
        assert result == 1 / (2 - p)
        fraction(
            103,
            v,
            f"A ו־B מנסים לזכות לסירוגין, ו־A מתחיל. כל ניסיון מצליח באופן עצמאי בהסתברות {p}; ההצלחה הראשונה מסיימת את המשחק. מה הסתברות הזכייה של A?",
            f"A and B alternate attempts, with A first. Each attempt independently succeeds with probability {p}; the first success ends the game. What is A's winning probability?",
            result,
            "אחרי שני כישלונות חוזרים למצב ההתחלתי; מסכמים את הסדרה ההנדסית של סיכויי הזכייה בתורות A.",
            "After two failures the initial state repeats; sum the geometric series of A's winning opportunities.",
            "geometric absorption probability and recurrence substitution",
            dict(per_attempt_success=str(p)),
        )
    for v, (reach, conditional) in enumerate(
        [
            (Fraction(3, 5), Fraction(1, 2)),
            (Fraction(2, 3), Fraction(3, 4)),
            (Fraction(1, 2), Fraction(2, 5)),
            (Fraction(4, 5), Fraction(1, 4)),
            (Fraction(3, 4), Fraction(2, 3)),
        ],
        1,
    ):
        result = reach * conditional
        fraction(
            104,
            v,
            f"שחקן מגיע לגמר בהסתברות {reach}. בהינתן שהגיע, הסתברות הזכייה שלו היא {conditional}; בלי הגעה אי אפשר לזכות. מה הסתברות הזכייה הכוללת?",
            f"A player reaches the final with probability {reach}. Given that they reach it, their chance of winning is {conditional}; winning without reaching it is impossible. What is the overall winning probability?",
            result,
            "מכפילים את הסתברות ההגעה בהסתברות המותנית לזכייה; אין צורך להניח עצמאות.",
            "Multiply the probability of reaching the final by the conditional winning probability; independence is not required.",
            "conditional probability multiplication rule",
            dict(reach=str(reach), win_given_reach=str(conditional)),
        )
    for v, (distance, slow, fast) in enumerate([(1, 1, 2), (2, 1, 4), (3, 2, 3), (4, 2, 4), (6, 3, 6)], 1):
        a = Fraction(distance, slow) + Fraction(distance, fast)
        b = Fraction(2 * distance, fast)
        assert a > b
        fraction(
            105,
            v,
            f"שני צעצועים עוברים מרחק כולל של {2 * distance} מטרים. A עובר {distance} מטרים במהירות {slow} מטר לשנייה ואת היתר במהירות {fast}; B עובר הכול במהירות {fast}. מתעלמים מזמן שינוי המהירות. בכמה שניות A מאחר ל־B, אף שמהירות הסיום שווה?",
            f"Two toys each travel {2 * distance} meters. A covers {distance} meters at {slow} m/s and the rest at {fast} m/s; B covers the entire route at {fast} m/s. Ignore speed-change time. How many seconds later does A finish, despite equal final speeds?",
            a - b,
            "מחברים זמני קטעים לכל מסלול ומחסרים את זמנו של B מזמנו של A.",
            "Add segment times for each trip, then subtract B's time from A's.",
            "piecewise travel-time integration",
            dict(half_distance=distance, speeds=[slow, fast], times=[str(a), str(b)]),
        )
    for v, (g, height) in enumerate([(10, 5), (10, 20), (8, 9), (9, 8), (10, 45)], 1):
        speed = math.isqrt(2 * g * height)
        assert speed**2 == 2 * g * height
        num(
            106,
            v,
            f"שתי מסות נקודתיות שונות מתחילות ממנוחה ויורדות {height} מטרים במסילות אידאליות. אין חיכוך, גלגול או אובדן אנרגיה, וכוחות המסילה אינם מבצעים עבודה. עבור g={g} מטר לשנייה בריבוע, מה מהירות כל אחת בסיום, במטר לשנייה?",
            f"Two different point masses start at rest and descend {height} meters on ideal tracks. There is no friction, rolling, or energy loss, and track forces do no work. With g={g} m/s squared, what is each mass's final speed in m/s?",
            speed,
            "שימור אנרגיה נותן v²=2gh; המסה מצטמצמת ולכן שתי המהירויות שוות.",
            "Energy conservation gives v²=2gh; mass cancels, so both speeds are equal.",
            "gravitational and kinetic energy equality",
            dict(g=g, height=height),
        )
    for v, (left_mass, left_arm, right_arm) in enumerate(
        [(2, 1, 2), (3, 2, 3), (4, 3, 6), (6, 1, 3), (5, 4, 2)], 1
    ):
        right_mass = Fraction(left_mass * left_arm, right_arm)
        num(
            107,
            v,
            f"מוט אופקי חסר משקל נתמך בציר שאינו מספק מומנט. משמאל תולים {left_mass} ק״ג במרחק {left_arm} מטרים מהציר. איזו מסה בק״ג יש לתלות מימין במרחק {right_arm} מטרים לאיזון סטטי בכבידה אחידה?",
            f"A weightless horizontal bar rests on a pivot supplying no torque. Hang {left_mass} kg at {left_arm} meters to the left. What mass in kg must hang {right_arm} meters to the right for static balance in uniform gravity?",
            right_mass,
            "משווים מסה כפול זרוע בשני הצדדים; גורם הכבידה משותף ומצטמצם.",
            "Equate mass times lever arm on both sides; the common gravity factor cancels.",
            "opposing torque balance equation",
            dict(left_mass=left_mass, left_arm=left_arm, right_arm=right_arm),
        )
    for v, (x, y) in enumerate([(1, 1), (2, 3), (4, 2), (3, 5), (5, 4)], 1):
        # Ask for correcting position, rather than five repeated 'not balanced' conclusions.
        good = f"(0, {-2 * y})"
        add(
            108,
            v,
            f"לוח אופקי נתמך בנקודה (0, 0) שאינה מספקת מומנט. שתי מסות שוות נמצאות ב־({-x}, {y}) וב־({x}, {y}). באיזו נקודה יש להוסיף מסה שלישית שווה כדי שמרכז המסה של שלושתן יהיה מעל התמיכה? מתעלמים ממשקל הלוח.",
            f"A horizontal plate has a point support at (0, 0) supplying no torque. Equal masses are at ({-x}, {y}) and ({x}, {y}). Where should a third equal mass be added so their combined center of mass lies over the support? Ignore the plate's mass.",
            good,
            [f"(0, {2 * y})", f"({2 * x}, 0)", "(0, 0)"],
            "סכום רכיבי x כבר אפס; צריך לבטל את סכום רכיבי y באמצעות המסה הנוספת.",
            "The x components already sum to zero; the added mass must cancel the y-component sum.",
            "vector center-of-mass sum",
            dict(points=[[-x, y], [x, y]], added=[0, -2 * y]),
        )
    for v, (a, b) in enumerate([(3, 2), (4, 3), (5, 2), (2, 6), (7, 4)], 1):
        num(
            109,
            v,
            f"קבוצה של {a} מסות מייצרת יחד מומנט כולל 0 סביב תמיכה. קבוצה נוספת של {b} מסות מייצרת גם היא מומנט כולל 0 סביב אותה תמיכה. כל המיקומים והכוחות נשארים קבועים. מה המומנט הכולל לאחר איחוד הקבוצות?",
            f"A group of {a} masses produces total torque 0 about a support. Another group of {b} masses also produces total torque 0 about the same support. All positions and forces remain fixed. What is the combined total torque?",
            0,
            "מומנטים מתחברים ליניארית: אפס ועוד אפס נשאר אפס.",
            "Torques add linearly: zero plus zero remains zero.",
            "superposition of specified torque sums",
            dict(group_sizes=[a, b], torque_sums=[0, 0]),
            [1, a, b] if a != b and a != 1 and b != 1 else [1, 2, 3],
        )
    stability_cases = [
        (
            "מעל",
            "above",
            ("שיווי משקל לא יציב", "Unstable equilibrium"),
            "הטיה קטנה מורידה את מרכז המסה, ולכן הכבידה מרחיקה מהמצב ההתחלתי.",
            "A small tilt lowers the center of mass, so gravity drives it farther from the initial position.",
        ),
        (
            "מתחת",
            "below",
            ("שיווי משקל יציב", "Stable equilibrium"),
            "הטיה קטנה מעלה את מרכז המסה, ולכן הכבידה מחזירה לכיוון המצב ההתחלתי.",
            "A small tilt raises the center of mass, so gravity restores it toward the initial position.",
        ),
        (
            "בדיוק על",
            "exactly at",
            ("שיווי משקל אדיש", "Neutral equilibrium"),
            "הסיבוב אינו משנה את גובה מרכז המסה ולכן אינו יוצר מומנט כבידה מחזיר.",
            "Rotation does not change the center-of-mass height and produces no restoring gravitational torque.",
        ),
    ]
    for v, (which, angle) in enumerate([(0, 1), (1, 1), (2, 1), (0, 2), (1, 2)], 1):
        hh, ee, g, eh, ex = stability_cases[which]
        all_choices = [
            ("שיווי משקל לא יציב", "Unstable equilibrium"),
            ("שיווי משקל יציב", "Stable equilibrium"),
            ("שיווי משקל אדיש", "Neutral equilibrium"),
            ("מומנט אפס שולל כל תנועה", "Zero torque rules out all motion"),
        ]
        add(
            110,
            v,
            f"גוף קשיח מסתובב חופשי סביב ציר קבוע ללא חיכוך. מרכז המסה נמצא {hh} הציר, כך שהמומנט כרגע אפס. מסיטים אותו מעט, בזווית של {angle} מעלות. איך מסווגים את המצב ההתחלתי ביחס להפרעה קטנה?",
            f"A rigid body rotates freely about a fixed frictionless pivot. Its center of mass is {ee} the pivot, so torque is currently zero. Tilt it slightly by {angle} degrees. How is the initial equilibrium classified under a small disturbance?",
            g,
            [x for x in all_choices if x != g],
            eh,
            ex,
            "local gravitational potential-energy comparison",
            dict(center_of_mass_position=ee, small_tilt_degrees=angle),
        )
    for v, crossings in enumerate([1, 2, 3, 4, 5], 1):
        inside = crossings % 2
        add(
            111,
            v,
            f"קרן מנקודה שאינה על שפת מצולע פשוט חוצה את השפה {crossings} פעמים לפני האינסוף. כל החציות אמיתיות, ללא קודקודים או השקות. מה אפשר להסיק על הנקודה?",
            f"A ray from a point off a simple polygon's boundary crosses the boundary {crossings} times before infinity. Every crossing is proper, with no vertices or tangencies. What follows about the point?",
            ("הנקודה בפנים", "The point is inside") if inside else ("הנקודה בחוץ", "The point is outside"),
            [
                ("הנקודה בחוץ", "The point is outside")
                if inside
                else ("הנקודה בפנים", "The point is inside"),
                ("הנקודה על השפה", "The point is on the boundary"),
                ("הזוגיות אינה מספיקה גם בהנחות אלה", "Parity is insufficient even under these assumptions"),
            ],
            "באינסוף נמצאים בחוץ וכל חצייה אמיתית מחליפה צד; הזוגיות קובעת את המצב בנקודת ההתחלה.",
            "Infinity is outside, and each proper crossing flips inside/outside; parity determines the starting point.",
            "iterate parity state across proper crossings",
            dict(crossings=crossings),
        )
    for v, (py, low, high) in enumerate([(0, -1, 1), (2, 0, 4), (5, 3, 8), (-2, -5, 1), (10, 7, 12)], 1):
        candidates = [(py, low), (py, high)]
        counted = [i for i, (a, b) in enumerate(candidates) if (a > py) != (b > py)]
        assert counted == [1]
        num(
            112,
            v,
            f"קרן אופקית בגובה y={py} פוגעת בקודקוד מצולע שנמצא בכיוונה. קצה הצלע הסמוכה האחת בגובה {low}, וקצה האחרת בגובה {high}. לפי הכלל (Ay>Py)!=(By>Py), כמה משתי הצלעות נספרות במפגש הקודקוד?",
            f"A horizontal ray at y={py} hits a polygon vertex in its forward direction. One adjacent edge's other endpoint has height {low}; the other's has height {high}. Under (Ay>Py)!=(By>Py), how many of these two edges count at the vertex?",
            1,
            "רק הצלע שממשיכה מעל גובה הקרן עומדת בתנאי; כך מונעים ספירה כפולה של חצייה אחת.",
            "Only the edge extending above the ray satisfies the condition, preventing double-counting one crossing.",
            "evaluate half-open endpoint predicate on both incident edges",
            dict(ray_y=py, other_endpoint_heights=[low, high]),
            [0, 2, 3],
        )
    for v, turns in enumerate([2, 3, 4, 5, 6], 1):
        parity = turns % 2
        good = (
            ("בפנים לפי שתי השיטות", "Inside under both rules")
            if parity
            else ("בחוץ לפי זוגיות, בפנים לפי ליפוף לא־אפס", "Outside by parity, inside by nonzero winding")
        )
        options = [
            ("בפנים לפי שתי השיטות", "Inside under both rules"),
            ("בחוץ לפי זוגיות, בפנים לפי ליפוף לא־אפס", "Outside by parity, inside by nonzero winding"),
            ("בפנים לפי זוגיות, בחוץ לפי ליפוף לא־אפס", "Inside by parity, outside by nonzero winding"),
            ("בחוץ לפי שתי השיטות", "Outside under both rules"),
        ]
        add(
            113,
            v,
            f"עוברים סביב אותו ריבוע בדיוק {turns} פעמים באותו כיוון. הנקודה היא מרכז הריבוע. איך יסווגו אותה כלל זוגיות החציות וכלל מספר הליפוף הלא־אפס?",
            f"Traverse the same square exactly {turns} times in the same direction. The point is its center. How do crossing parity and the nonzero-winding rule classify it?",
            good,
            [x for x in options if x != good],
            f"לקרן יש {turns} חציות, ומספר הליפוף הוא {turns}; הזוגיות והבדיקה לאפס הן תנאים שונים.",
            f"A ray has {turns} crossings and winding number {turns}; parity and nonzero are different tests.",
            "evaluate parity and nonzero winding on repeated traversal",
            dict(repeated_traversals=turns),
        )
    for v, (multiple, radius) in enumerate([(2, 1), (4, 10), (6, 100), (8, 1000), (10, 3)], 1):
        increase = Fraction(multiple, 2)
        num(
            114,
            v,
            f"לחבל מעגלי ברדיוס {radius} ס״מ מוסיפים {multiple}π ס״מ ומעצבים שוב מעגל באותו מרכז, ללא רפיון. בכמה ס״מ גדל הרדיוס?",
            f"Add {multiple}π cm to a circular rope of radius {radius} cm and reshape it into a concentric circle without sagging. By how many cm does the radius increase?",
            increase,
            "תוספת ההיקף היא ‎2π כפול תוספת הרדיוס; הרדיוס המקורי מצטמצם בחיסור.",
            "The circumference increment is 2π times the radius increment; the original radius cancels.",
            "subtract circle circumferences algebraically",
            dict(original_radius=radius, added_pi_multiple=multiple),
        )
    for v, (r1, s1, r2, s2) in enumerate(
        [
            (Fraction(1, 4), 1, 1, 3),
            (Fraction(1, 2), 2, 2, 6),
            (1, 3, 2, 5),
            (2, 6, 3, 8),
            (Fraction(1, 3), 1, 2, 5),
        ],
        1,
    ):
        omega1 = Fraction(s1, r1)
        omega2 = Fraction(s2, r2)
        assert omega1 > omega2 and s1 < s2
        fraction(
            115,
            v,
            f"שחיין מקיף מרכז ברדיוס {r1} מטרים במהירות {s1} מטר לשנייה; רץ מקיף אותו מרכז ברדיוס {r2} מטרים במהירות {s2}. בכמה רדיאנים לשנייה גדולה מהירותו הזוויתית של השחיין?",
            f"A swimmer circles a center at radius {r1} meters and speed {s1} m/s; a runner circles the same center at radius {r2} meters and speed {s2} m/s. By how many radians per second is the swimmer's angular speed greater?",
            omega1 - omega2,
            "המהירות הזוויתית היא המהירות לאורך המסלול חלקי הרדיוס. מחשבים לכל אחד ומחסרים.",
            "Angular speed equals path speed divided by radius. Compute both and subtract.",
            "exact rational angular-speed comparison",
            dict(radii=[str(r1), str(r2)], speeds=[s1, s2]),
        )
    for v, (a, b, c, d) in enumerate(
        [(1, 4, 2, 2), (1, 9, 3, 3), (2, 8, 4, 4), (2, 18, 6, 6), (1, 16, 4, 4)], 1
    ):
        assert a * b == c * d and sorted([a, b]) != sorted([c, d])
        add(
            116,
            v,
            f"מלבן במידות {a}×{b} וריבוע במידות {c}×{d} נמדדים באותן יחידות. איזו טענה נכונה על שטח וחפיפה, כאשר חפיפה מותרת רק בהזזה, סיבוב או שיקוף?",
            f"A {a}×{b} rectangle and a {c}×{d} square use the same units. Which statement about area and congruence is correct, allowing only translation, rotation, or reflection for congruence?",
            ("שטחם שווה אך הם אינם חופפים", "They have equal area but are not congruent"),
            [
                ("הם חופפים כי שטחם שווה", "They are congruent because their areas match"),
                ("שטח הריבוע תמיד גדול יותר", "The square always has larger area"),
                ("סיבוב משנה את אורכי הצלעות", "Rotation changes side lengths"),
            ],
            "המכפלות שוות, אבל אורכי הצלעות שונים ונשמרים בכל הפעולות המותרות.",
            "Their products match, but their side lengths differ and are preserved by the allowed transformations.",
            "compare area product and rigid-motion side invariants",
            dict(dimensions=[[a, b], [c, d]]),
        )
    for v, drops in enumerate([2, 3, 4, 5, 6], 1):

        def capacity(balls, k):
            if balls == 0 or k == 0:
                return 0
            return 1 + capacity(balls - 1, k - 1) + capacity(balls, k - 1)

        floors = capacity(2, drops)
        assert floors == drops * (drops + 1) // 2
        num(
            117,
            v,
            f"יש שני כדורים זהים הנשברים מקומת סף ומעלה, וכדורים ששרדו ניתנים לשימוש חוזר. קומה 0 בטוחה, וייתכן שאין קומת שבירה בטווח. כמה קומות לכל היותר ניתן לכסות בזיהוי ודאי של הסף באמצעות עד {drops} הטלות?",
            f"Two identical balls break at a threshold floor and above; surviving balls are reusable. Floor 0 is safe, and there may be no breaking floor in the range. What is the maximum number of floors for which the threshold can be identified with at most {drops} drops?",
            floors,
            "כל הטלה מחלקת את הבעיה לענף שבירה עם כדור אחד פחות ולענף הישרדות. עם שני כדורים הקיבולת היא הסכום מ־1 עד מספר ההטלות.",
            "Each drop splits into breakage with one fewer ball and survival. With two balls, capacity is the sum from 1 through the drop limit.",
            "full resource-state recurrence checked against triangular formula",
            dict(balls=2, drops=drops),
        )
    for v, (visible, reply) in enumerate(
        [(2, "white"), (3, "black"), (4, "white"), (5, "black"), (0, "white")], 1
    ):
        assert (visible % 2 == 0) == (reply == "white")
        word_h = "לבן" if reply == "white" else "שחור"
        add(
            118,
            v,
            f"בדוגמת כובעים, הדובר הראשון אומר ״לבן״ אם מספר הכובעים השחורים שהוא רואה זוגי, ו״שחור״ אחרת. הוא רואה {visible} כובעים שחורים ואומר ״{word_h}״. צבע כובעו שלו אינו נראה לו ומספרי הצבעים אינם מוגבלים. מה אפשר להסיק על כובעו שלו?",
            f"In a hats protocol, the first speaker says 'white' for an even number of visible black hats and 'black' otherwise. They see {visible} black hats and say '{reply}'. Their own hat is invisible to them, and color counts are unrestricted. What follows about their own hat?",
            ("צבעו עדיין יכול להיות לבן או שחור", "It may still be either white or black"),
            [
                (f"הכובע בהכרח {word_h}", f"The hat must be {reply}"),
                (
                    f"הכובע בהכרח {'שחור' if reply == 'white' else 'לבן'}",
                    f"The hat must be {'black' if reply == 'white' else 'white'}",
                ),
                ("אסור להחליף את צבע כובעו במודל", "Changing their hat color is forbidden by the model"),
            ],
            "האמירה מקודדת את מה שנראה לאחרים; שינוי רק בכובע הדובר אינו משנה את הודעתו.",
            "The word encodes the visible hats; changing only the speaker's own hat does not change the message.",
            "two indistinguishable worlds differing only in sender's own hat",
            dict(visible_black=visible, message=reply, own_hat_worlds=["white", "black"]),
        )


def refine_conceptual():
    """Different logical observations and queries for concepts without useful numeric scaling."""
    refined = {1, 25, 26, 30, 43, 73, 88, 110}
    ROWS[:] = [r for r in ROWS if int(r["source_key"].split("-")[-1]) not in refined]
    CHECKS[:] = [r for r in CHECKS if int(r["key"].split("-")[2]) not in refined]
    # A predicate is (is_equal, location); enumerate every possible coin location.
    location_cases = [
        ([(False, "A"), (True, "A"), (False, "B")], 1),
        ([(True, "A"), (True, "A"), (True, "B")], 2),
        ([(True, "C"), (False, "A"), (True, "B")], 0),
        ([(False, "C"), (True, "B"), (True, "B")], 3),
        ([(True, "C"), (True, "C"), (False, "C")], 2),
    ]
    for v, (predicates, count) in enumerate(location_cases, 1):
        counts = {x: sum((x == location) == equal for equal, location in predicates) for x in ["A", "B", "C"]}
        valid = [x for x, c in counts.items() if c == count]
        assert len(valid) == 1
        he_statements = [f"״{'ב־' if eq else 'לא ב־'}{loc}״" for eq, loc in predicates]
        en_statements = [f"'{'in' if eq else 'not in'} {loc}'" for eq, loc in predicates]
        add(
            1,
            v,
            f"מטבע נמצא בדיוק באחת הקופסאות A, B, C. שלושת המשפטים הם, לפי הסדר: {', '.join(he_statements)}. בדיוק {count} מהמשפטים נכונים. היכן המטבע?",
            f"A coin is in exactly one of boxes A, B, C. The three statements, in order, are {', '.join(en_statements)}. Exactly {count} statements are true. Where is the coin?",
            valid[0],
            [x for x in ["A", "B", "C"] if x != valid[0]]
            + [("אין מיקום מתאים", "No location satisfies the conditions")],
            f"מספרי המשפטים הנכונים עבור A, B, C הם {counts['A']}, {counts['B']}, {counts['C']}; רק {valid[0]} מתאים.",
            f"The true-statement counts for A, B, C are {counts['A']}, {counts['B']}, {counts['C']}; only {valid[0]} matches.",
            "exhaustive evaluation of distinct predicate sets",
            dict(predicates=predicates, required_true=count, truth_counts=counts),
        )
    # All labels wrong means exactly two derangements; a draw from mixed distinguishes them.
    prefix_he = "שלוש קופסאות מכילות רק תפוחים, רק תפוזים ותערובת. כולן מסומנות בתוויות שגויות. "
    prefix_en = "Three boxes contain only apples, only oranges, and a mixture. All three labels are wrong. "
    content_options = [
        ("רק תפוחים", "Only apples"),
        ("רק תפוזים", "Only oranges"),
        ("תערובת", "A mixture"),
        ("לא ניתן לקבוע", "Cannot be determined"),
    ]
    for v, fruit in enumerate(["apple", "orange", "apple", "orange"], 2):
        if v in [2, 3]:
            label = "apples" if fruit == "apple" else "oranges"
            good = ("רק תפוזים", "Only oranges") if fruit == "apple" else ("רק תפוחים", "Only apples")
            label_he = "תפוחים" if fruit == "apple" else "תפוזים"
        else:
            label = "oranges" if fruit == "apple" else "apples"
            good = ("תערובת", "A mixture")
            label_he = "תפוזים" if fruit == "apple" else "תפוחים"
        fruit_he = "תפוח" if fruit == "apple" else "תפוז"
        # Check actual derangement and requested label rather than hand-asserting content.
        arrangements = [
            p
            for p in itertools.permutations(["apples", "oranges", "mixed"])
            if all(x != y for x, y in zip(p, ["apples", "oranges", "mixed"], strict=True))
        ]
        actual = next(p for p in arrangements if p[2] == ("apples" if fruit == "apple" else "oranges"))
        predicted = actual[["apples", "oranges", "mixed"].index(label)]
        assert (
            predicted == {"Only apples": "apples", "Only oranges": "oranges", "A mixture": "mixed"}[good[1]]
        )
        add(
            25,
            v,
            prefix_he + f"מהקופסה המסומנת ״תערובת״ הוצא {fruit_he}. מה יש בקופסה המסומנת ״{label_he}״?",
            prefix_en
            + f"A draw from the box labeled 'mixed' gives an {fruit}. What is in the box labeled '{label}'?",
            good,
            [x for x in content_options if x != good],
            "הקופסה המסומנת כתערובת טהורה. לאחר זיהויה, האיסור על כל תווית להיות נכונה קובע את שתי האחרות.",
            "The mixed-labeled box is pure. Once identified, requiring every label to be wrong fixes the other two contents.",
            "enumerate label derangements and filter by observation",
            dict(draw=fruit, queried_label=label, arrangement=actual),
        )
    add(
        25,
        1,
        prefix_he + "מאיזו קופסה יש להוציא פרי יחיד כדי לקבוע את כל התכולות?",
        prefix_en + "From which labeled box should one fruit be drawn to determine all contents?",
        ("מהמסומנת ״תערובת״", "The one labeled 'mixed'"),
        [
            ("מהמסומנת ״תפוחים״", "The one labeled 'apples'"),
            ("מהמסומנת ״תפוזים״", "The one labeled 'oranges'"),
            ("אין אסטרטגיה עם פרי יחיד", "No one-fruit strategy exists"),
        ],
        "רק התווית ״תערובת״ מבטיחה קופסה טהורה שתכולתה נקבעת מהפרי.",
        "Only the 'mixed' label guarantees a pure box identified by its drawn fruit.",
        "two derangements; mixed-label observation separates both",
        dict(valid_arrangements=2),
    )
    baseh = "יש שלושה מטבעות A, B, C; בדיוק אחד כבד והאחרים שווים. "
    basee = "There are three coins A, B, C; exactly one is heavy and the others weigh the same. "
    coin_cases = [
        ("A", "B", 0, "C"),
        ("A", "B", 1, "A"),
        ("A", "B", -1, "B"),
        ("A", "C", 0, "B"),
        ("B", "C", -1, "C"),
    ]
    for v, (left, right, outcome, good) in enumerate(coin_cases, 1):
        relh = {0: "המאזניים מאוזנים", 1: f"{left} כבד יותר", -1: f"{right} כבד יותר"}[outcome]
        rele = {0: "the pans balance", 1: f"{left} is heavier", -1: f"{right} is heavier"}[outcome]
        hypotheses = []
        for heavy in "ABC":
            result = (int(heavy == left) > int(heavy == right)) - (int(heavy == left) < int(heavy == right))
            if result == outcome:
                hypotheses.append(heavy)
        assert hypotheses == [good]
        add(
            26,
            v,
            baseh + f"שוקלים את {left} מול {right}, ו־{relh}. איזה מטבע כבד?",
            basee + f"Weigh {left} against {right}; {rele}. Which coin is heavy?",
            good,
            [x for x in "ABC" if x != good] + [("אין די מידע", "Insufficient information")],
            "משווים את תוצאת השקילה לכל אחת משלוש השערות המטבע הכבד; רק אחת מתאימה.",
            "Compare the weighing outcome with each heavy-coin hypothesis; exactly one matches.",
            "enumerate three heavy-coin hypotheses against distinct weighing observations",
            dict(left=left, right=right, outcome=outcome),
        )
    implication_cases = [
        (
            "דני לובש כחול. מה אפשר לקבוע על מקצועו?",
            "Danny wears blue. What follows about his profession?",
            ("אי אפשר לקבוע אם הוא מתכנת", "It is undetermined whether he is a programmer"),
            [
                ("הוא בוודאות מתכנת", "He is certainly a programmer"),
                ("הוא בוודאות אינו מתכנת", "He is certainly not a programmer"),
                ("הנתונים סותרים", "The facts contradict each other"),
            ],
            "לבישת כחול אינה מחייבת תכנות.",
            "Wearing blue does not imply being a programmer.",
        ),
        (
            "דני אינו לובש כחול. מה מתחייב?",
            "Danny does not wear blue. What must follow?",
            ("דני אינו מתכנת", "Danny is not a programmer"),
            [
                ("דני מתכנת", "Danny is a programmer"),
                ("דני גם מתכנת וגם אינו מתכנת", "Danny both is and is not a programmer"),
                ("אין מסקנה על מקצועו", "Nothing follows about his profession"),
            ],
            "אילו היה מתכנת, היה חייב ללבוש כחול; משתמשים בשלילה הנגדית.",
            "If he were a programmer, he would wear blue; this is contraposition.",
        ),
        (
            "דני מתכנת. מה מתחייב על לבושו?",
            "Danny is a programmer. What follows about his clothing?",
            ("הוא לובש כחול", "He wears blue"),
            [
                ("הוא אינו לובש כחול", "He does not wear blue"),
                ("אין מסקנה על לבושו", "Nothing follows about his clothing"),
                ("הוא חייב ללבוש אדום במקום כחול", "He must wear red instead of blue"),
            ],
            "כאן מתקיים תנאי הכלל בכיוון המותר.",
            "The rule's premise is given, so its conclusion follows.",
        ),
        (
            "איזה מקרה יכול להתקיים ומפריך את הכיוון ההפוך?",
            "Which possible case disproves the converse?",
            ("אדם שאינו מתכנת ולובש כחול", "A nonprogrammer who wears blue"),
            [
                ("מתכנת שאינו לובש כחול", "A programmer who does not wear blue"),
                ("מתכנת שלובש כחול", "A programmer who wears blue"),
                ("אדם שאינו מתכנת ואינו לובש כחול", "A nonprogrammer who does not wear blue"),
            ],
            "המקרה שומר על הכלל המקורי אך סותר ״כל לובש כחול מתכנת״.",
            "This preserves the original rule while refuting 'everyone wearing blue is a programmer'.",
        ),
        (
            "איזה מקרה סותר ישירות את הכלל?",
            "Which case directly contradicts the rule?",
            ("מתכנת שאינו לובש כחול", "A programmer who does not wear blue"),
            [
                ("מתכנת שלובש כחול", "A programmer who wears blue"),
                ("אדם שאינו מתכנת ולובש כחול", "A nonprogrammer who wears blue"),
                ("אדם שאינו מתכנת ואינו לובש כחול", "A nonprogrammer who does not wear blue"),
            ],
            "רק תנאי אמיתי ומסקנה שקרית מפריכים גרירה.",
            "Only a true premise with a false conclusion falsifies an implication.",
        ),
    ]
    for v, (h, e, g, b, eh, ee) in enumerate(implication_cases, 1):
        add(
            30,
            v,
            "בקבוצה כל מתכנת לובש כחול. " + h,
            "In a group, every programmer wears blue. " + e,
            g,
            b,
            eh,
            ee,
            "classical implication truth-table case",
            dict(case=v, allowed_worlds=[[0, 0], [0, 1], [1, 1]]),
        )
    # Guard variants change observation, respondent identity, and inference target.
    guard_cases = [
        (
            "לא ידוע איזה שומר נשאל. לשאלה ״על איזו דלת האחר יצביע כיציאה?״ התקבלה התשובה A. איזו דלת היא היציאה?",
            "You do not know which guard is asked. Asked 'which door would the other identify as the exit?', the answer is A. Which door is the exit?",
            "B",
            ["A", ("שתי הדלתות יציאות", "Both doors are exits"), ("אי אפשר להסיק", "It cannot be inferred")],
        ),
        (
            "לא ידוע איזה שומר נשאל. לשאלה ״על איזו דלת האחר יצביע כיציאה?״ התקבלה התשובה B. איזו דלת היא היציאה?",
            "You do not know which guard is asked. Asked 'which door would the other identify as the exit?', the answer is B. Which door is the exit?",
            "A",
            ["B", ("שתי הדלתות מלכודות", "Both doors are traps"), ("אי אפשר להסיק", "It cannot be inferred")],
        ),
        (
            "A היא היציאה. דובר האמת נשאל על איזו דלת האחר יצביע כיציאה. איזו דלת יאמר?",
            "A is the exit. The truthful guard is asked which door the other would identify as the exit. Which door will they name?",
            "B",
            [
                "A",
                ("לא יוכל לענות", "They cannot answer"),
                ("חייב לומר את שתי הדלתות", "They must name both doors"),
            ],
        ),
        (
            "B היא היציאה. השקרן נשאל על איזו דלת האחר יצביע כיציאה. איזו דלת יאמר?",
            "B is the exit. The liar is asked which door the other would identify as the exit. Which door will they name?",
            "A",
            [
                "B",
                ("לא יוכל לענות", "They cannot answer"),
                ("חייב לומר את שתי הדלתות", "They must name both doors"),
            ],
        ),
        (
            "מדוע שואלים שומר מה השומר האחר היה אומר על היציאה, ואז בוחרים בדלת האחרת?",
            "Why ask one guard what the other would say is the exit, then choose the opposite door?",
            (
                "שתי זהויות המשיב מובילות להצבעה על המלכודת",
                "Both possible respondent identities point to the trap",
            ),
            [
                ("שניהם דוברי אמת בשאלה מקוננת", "Both tell the truth for a nested question"),
                ("השקרן מפסיק לשקר כשמזכירים את האחר", "The liar stops lying when the other is mentioned"),
                ("התשובה תמיד מצביעה על היציאה", "The answer always points to the exit"),
            ],
        ),
    ]
    for v, (h, e, g, b) in enumerate(guard_cases, 1):
        add(
            43,
            v,
            "יש שתי דלתות A ו־B, אחת יציאה ואחת מלכודת. שני שומרים יודעים את היעד; אחד תמיד דובר אמת ואחד תמיד משקר. "
            + h,
            "There are doors A and B, one exit and one trap. Both guards know the exit; one always tells the truth and the other always lies. "
            + e,
            g,
            b,
            "דובר האמת מדווח על שקרו של האחר; השקרן משקר על תשובת האמת של האחר. שניהם מצביעים על המלכודת.",
            "The truthful guard reports the other's lie; the liar lies about the other's truthful answer. Both point to the trap.",
            "nested response truth/lie composition",
            dict(case=v, truthful_reports="trap", liar_reports="trap"),
        )
    hat_cases = [
        (
            "האחורי רואה את הקדמי ואומר שאינו יודע את צבע כובעו. מה צבע כובע הקדמי?",
            "The rear person sees the front hat and says they cannot determine their own color. What color is the front hat?",
            ("לבן", "White"),
            [
                ("שחור", "Black"),
                ("שני הצבעים עדיין אפשריים", "Either color remains possible"),
                ("אין מצב מתאים", "No possible world fits"),
            ],
        ),
        (
            "האחורי רואה כובע שחור על הקדמי. מה צבע כובע האחורי?",
            "The rear person sees a black front hat. What color is the rear hat?",
            ("לבן", "White"),
            [
                ("שחור", "Black"),
                ("שני הצבעים עדיין אפשריים", "Either color remains possible"),
                ("אין מצב מתאים", "No possible world fits"),
            ],
        ),
        (
            "האחורי רואה כובע לבן על הקדמי. מה הוא יכול לקבוע על כובעו שלו?",
            "The rear person sees a white front hat. What can they determine about their own hat?",
            ("שני הצבעים עדיין אפשריים", "Either color remains possible"),
            [
                ("לבן בוודאות", "Certainly white"),
                ("שחור בוודאות", "Certainly black"),
                ("אין מצב מתאים", "No possible world fits"),
            ],
        ),
        (
            "האחורי רואה את הקדמי ואומר בכנות שהוא יודע שכובעו שלו לבן. מה צבע כובע הקדמי? אין לאחורי מידע נוסף.",
            "The rear person sees the front hat and truthfully says they know their own hat is white. What color is the front hat? The rear person has no additional information.",
            ("שחור", "Black"),
            [
                ("לבן", "White"),
                ("שני הצבעים עדיין אפשריים", "Either color remains possible"),
                ("אין מצב מתאים", "No possible world fits"),
            ],
        ),
        (
            "שני הכובעים בפועל לבנים. האחורי רואה רק את הקדמי, בלי מידע נוסף. מדוע עדיין אינו יכול לדעת את צבע כובעו?",
            "Both hats are actually white. The rear person sees only the front hat, with no additional information. Why can they still not determine their own color?",
            (
                "גם עולם שבו כובעו שחור מתאים למה שהוא רואה",
                "A world where their own hat is black fits the same observation",
            ),
            [
                ("הוא רואה את שני הכובעים", "They see both hats"),
                ("הוא יודע שחייב להיות כובע שחור", "They know there must be a black hat"),
                ("כובע לבן אינו צבע חוקי", "White is not an allowed color"),
            ],
        ),
    ]
    for v, (h, e, g, b) in enumerate(hat_cases, 1):
        add(
            73,
            v,
            "לשני אנשים כובעים לבנים או שחורים, וידוע לשניהם שיש לכל היותר כובע שחור אחד. " + h,
            "Two people wear white or black hats, and both know there is at most one black hat. " + e,
            g,
            b,
            "משווים בין העולמות האפשריים: לבן־לבן, שחור־לבן ולבן־שחור. הידיעה תלויה בתצפית ובמידע המשותף.",
            "Compare possible worlds: white-white, black-white, and white-black. Knowledge depends on observation and common information.",
            "finite possible-world knowledge model",
            dict(case=v, allowed_worlds=[[0, 0], [1, 0], [0, 1]]),
        )
    cycle_cases = [
        (
            "איזו תכונה מונעת סדר שבו כל פריט מנצח כל פריט שאחריו?",
            "What prevents an order in which each item beats every later item?",
            ("מעגל ניצחונות", "A cycle of wins"),
            [
                ("עצם העובדה שיש שלושה פריטים", "Merely having three items"),
                ("אין מנצח בשום זוג", "No pair has a winner"),
                ("כל הניצחונות סימטריים", "All wins are symmetric"),
            ],
        ),
        (
            "מי מבין האחרים מפריך בחירה ב־A כראשון בסדר ניצחונות כולל?",
            "Which other item rules out putting A first in an overall winning order?",
            "C",
            ["A", "B", ("אף אחד", "Neither")],
        ),
        (
            "מן A מנצח B ו־B מנצח C, איזו מסקנה שגויה מתקבלת אם מניחים בטעות מעבריות?",
            "From A beating B and B beating C, which false conclusion follows if transitivity is incorrectly assumed?",
            ("A מנצח C", "A beats C"),
            [("C מנצח A", "C beats A"), ("B מנצח C", "B beats C"), ("A מנצח B", "A beats B")],
        ),
        (
            "משנים רק את התוצאה בין A ל־C כך ש־A מנצח C. איזה סדר כולל נהיה אפשרי?",
            "Change only the A-versus-C result so that A beats C. Which overall order becomes possible?",
            "A, B, C",
            ["C, B, A", "B, A, C", "A, C, B"],
        ),
        (
            "כמה מתוך ששת הסדרים של שלושת הפריטים מקיימים שכל פריט מנצח כל פריט שאחריו?",
            "How many of the six orders have every item beating every later item?",
            "0",
            ["1", "2", "3"],
        ),
    ]
    for v, (h, e, g, b) in enumerate(cycle_cases, 1):
        add(
            88,
            v,
            "A מנצח B, B מנצח C, ו־C מנצח A. " + h,
            "A beats B, B beats C, and C beats A. " + e,
            g,
            b,
            "המעגל אינו יחס סדר מעברי; בודקים את הכיוונים שניתנו, ובגרסה שמשנה קשת בודקים את היחס החדש.",
            "The cycle is not a transitive ordering; use the specified directions, and in the changed-edge variant inspect the new relation.",
            "directed-cycle relation and all-order enumeration",
            dict(case=v, cycle=[["A", "B"], ["B", "C"], ["C", "A"]]),
        )
    stable = [
        (
            "מרכז המסה ישירות מעל הציר. מה קורה אחרי הטיה קטנה?",
            "The center of mass is directly above the pivot. What happens after a small tilt?",
            ("הכבידה מרחיקה מהמצב ההתחלתי", "Gravity drives it farther from the initial position"),
            [
                ("הכבידה תמיד מחזירה למצב ההתחלתי", "Gravity always restores the initial position"),
                (
                    "מרכז המסה נשאר באותו גובה בכל זווית",
                    "The center of mass stays at the same height at every angle",
                ),
                ("מומנט אפס מונע כל תזוזה עתידית", "Zero torque prevents any future displacement"),
            ],
        ),
        (
            "מרכז המסה ישירות מתחת לציר. איך מסווגים את שיווי המשקל?",
            "The center of mass is directly below the pivot. How is the equilibrium classified?",
            ("יציב", "Stable"),
            [("לא יציב", "Unstable"), ("אדיש", "Neutral"), ("אין שיווי משקל", "There is no equilibrium")],
        ),
        (
            "מרכז המסה בדיוק בציר. איך מסווגים את שיווי המשקל בכבידה בלבד?",
            "The center of mass is exactly at the pivot. How is the equilibrium classified under gravity alone?",
            ("אדיש", "Neutral"),
            [
                ("יציב עם מומנט מחזיר", "Stable with a restoring torque"),
                ("לא יציב עם מומנט מרחיק", "Unstable with a destabilizing torque"),
                ("אין שיווי משקל", "There is no equilibrium"),
            ],
        ),
        (
            "הטיה קטנה מעלה את מרכז המסה. מה כיוון מומנט הכבידה ביחס להטיה?",
            "A small tilt raises the center of mass. How does gravitational torque act relative to the tilt?",
            ("נגד ההטיה", "Against the tilt"),
            [
                ("עם ההטיה", "With the tilt"),
                ("הוא בהכרח אפס", "It must be zero"),
                ("הוא אינו תלוי במרכז המסה", "It is independent of the center of mass"),
            ],
        ),
        (
            "המומנט כרגע אפס. איזה מידע נוסף נחוץ כדי להסיק שהמצב יציב?",
            "Torque is currently zero. What additional information is needed to conclude the equilibrium is stable?",
            ("התגובה להפרעה קטנה יוצרת מומנט מחזיר", "Small disturbances produce a restoring torque"),
            [
                ("המסה חיובית בלבד", "Only that the mass is positive"),
                ("הגוף נמצא במנוחה ברגע אחד בלבד", "Only that the body is momentarily at rest"),
                ("יש ציר קבוע בלבד", "Only that the pivot is fixed"),
            ],
        ),
    ]
    for v, (h, e, g, b) in enumerate(stable, 1):
        add(
            110,
            v,
            "גוף קשיח מסתובב חופשי סביב ציר קבוע ללא חיכוך, בכבידה אחידה בלבד. " + h,
            "A rigid body rotates freely about a fixed frictionless pivot under uniform gravity alone. " + e,
            g,
            b,
            "בודקים איך האנרגיה הפוטנציאלית והמומנט משתנים אחרי הפרעה קטנה, ולא רק אם המומנט אפס ברגע ההתחלתי.",
            "Inspect potential energy and torque after a small disturbance, rather than only checking zero torque initially.",
            "local potential energy and torque sign",
            dict(case=v),
        )


def build():
    ROWS.clear()
    CHECKS.clear()
    build_basic()
    build_basic_rest()
    build_expansion()
    build_extended()
    refine_conceptual()
    ROWS.sort(key=lambda r: (r["source_key"], r["variant"]))
    CHECKS.sort(key=lambda r: r["key"])
    return list(ROWS), list(CHECKS)


def main():
    rows, checks = build()
    source = {}
    for name in [
        "fundamentals-code-logic.json",
        "fundamentals-reasoning-expansion.json",
        "fundamentals-reasoning-250.json",
    ]:
        for card in json.loads((ROOT / "apps/web/src/content" / name).read_text(encoding="utf-8")):
            if card["topic"] == "reasoning" and card["id"] not in {"quick-sw-02", "quick-sw-61"}:
                source[card["id"]] = card
    assert len(source) == 86
    assert len(rows) == 430, len(rows)
    assert {r["source_key"] for r in rows} == set(source)
    for key in source:
        group = [r for r in rows if r["source_key"] == key]
        assert sorted(r["variant"] for r in group) == [1, 2, 3, 4, 5]
        for lang in ["he", "en"]:
            assert len({r["prompt"][lang] for r in group}) == 5, (key, lang)
    output = ROOT / "backend/seeds/duel_quiz_batches"
    output.mkdir(parents=True, exist_ok=True)
    (output / "reasoning.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "reasoning.checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{len(rows)} bilingual questions; {len(source)} sources; {len(checks)} evidence rows")


if __name__ == "__main__":
    main()
