"""Source-specific code/algorithm quiz cases; run with Python 3.12+.

Uses source functions plus separate reference calculations. This is machine
verification, not an attestation of human editorial approval.
"""

from __future__ import annotations

import itertools
import json
from collections import Counter, deque
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "backend/seeds/duel_quiz_batches"
SOURCES = {}
for name in (
    "fundamentals-code-logic.json",
    "fundamentals-code-expansion.json",
    "fundamentals-code-250.json",
):
    SOURCES.update(
        {q["id"]: q for q in json.loads((ROOT / "apps/web/src/content" / name).read_text(encoding="utf-8"))}
    )
QUESTIONS, CHECKS = [], []


def code(value):
    return f"`{value}`"


def emit(n, v, he, en, options, expected, eh, ee, method, inputs):
    """Options are values, with expected verified against a separate reference."""
    assert len(options) == 4 and len(set(map(str, options))) == 4, (n, v, options)
    assert sum(value == expected for value in options) == 1, (n, v, expected, options)
    source = f"quick-sw-{n:02d}"
    shift = (n + v) % 4
    options = options[shift:] + options[:shift]
    key = f"{source}-v{v}"
    QUESTIONS.append(
        dict(
            key=key,
            source_key=source,
            variant=v,
            topic=SOURCES[source]["topic"],
            status="draft",
            prompt=dict(he=he, en=en),
            choices=[dict(he=str(x), en=str(x)) for x in options],
            correct=options.index(expected),
            explanation=dict(he=eh, en=ee),
        )
    )
    CHECKS.append(dict(key=key, method=method, inputs=inputs, expected=str(expected)))


def numeric_options(value, pool=None):
    out = [value]
    for item in (pool or []) + [0, 1, value + 1, value - 1, value + 2, value + 3]:
        if item not in out:
            out.append(item)
        if len(out) == 4:
            return out
    raise AssertionError(value)


def source_function(n):
    scope = {}
    # Trusted repository content; not supplied or generated code.
    exec(SOURCES[f"quick-sw-{n:02d}"]["code"]["text"], scope)
    return next(value for key, value in scope.items() if key != "__builtins__" and callable(value))


def build():
    QUESTIONS.clear()
    CHECKS.clear()
    for v, (items, added) in enumerate([([2, 4], 7), ([-1, 3], 0), ([], 8), ([5], 5), ([0, 0, 2], -2)], 1):
        original = items.copy()
        copy = source_function(5)(original)
        copy.append(added)
        assert original == items and copy is not original and copy == items + [added]
        expected = repr(original)
        options = [expected, repr(items + [added]), repr([added]), repr(list(reversed(items)))]
        options = list(dict.fromkeys(options))
        for x in ["None", repr(items + [added, added]), "[99]"]:
            if len(options) < 4 and x not in options:
                options.append(x)
        emit(
            5,
            v,
            f"ב־Python נתון `a={items!r}`. מבצעים `b=a[:]` ואז `b.append({added})`. מה ערכה של `a` כעת?",
            f"In Python, `a={items!r}`. Execute `b=a[:]`, then `b.append({added})`. What is `a` now?",
            options,
            expected,
            "החיתוך יוצר רשימה חדשה, ולכן ההוספה ל־`b` אינה משנה את `a`.",
            "Slicing creates a new list, so appending to `b` leaves `a` unchanged.",
            "source execution and list identity",
            dict(items=items, added=added),
        )

    for v, (s, char) in enumerate(
        [("ababa", "a"), ("a a", " "), ("xyz", "q"), ("BBBBb", "B"), ("mississippi", "s")], 1
    ):
        result = source_function(9)(s).get(char, 0)
        expected = len([c for c in s if c == char])
        assert result == expected
        emit(
            9,
            v,
            f"מונים כל תו בנפרד במחרוזת `{s!r}`, כולל רווחים ובהבחנה בין אות גדולה לקטנה. כמה פעמים מופיע התו `{char!r}`?",
            f"Count individual characters in `{s!r}`, including spaces and distinguishing case. How often does `{char!r}` occur?",
            numeric_options(expected),
            expected,
            f"סורקים את המחרוזת ומגדילים את המונה רק בתו המבוקש: {expected} הופעות.",
            f"Scan the string and increment only for the requested character: {expected} occurrences.",
            "source dictionary count versus filtered enumeration",
            dict(text=s, character=char),
        )

    for v, values in enumerate([[-8, -2, -5], [], [0, -3, -1], [4, 9, 9, 2], [-10]], 1):
        result = source_function(11)(values)
        expected = sorted(values)[-1] if values else None
        assert result == expected
        options = list(
            dict.fromkeys([str(expected), "None", "0", str(values[0] if values else -1), "-99", "99"])
        )[:4]
        emit(
            11,
            v,
            f"פונקציה מחזירה את המספר הגדול ביותר ברשימה, או `None` כשהיא ריקה. מה תחזיר עבור `{values}`?",
            f"A function returns the largest list element, or `None` for an empty list. What does it return for `{values}`?",
            options,
            str(expected),
            f"בודקים את כל האיברים; התוצאה היא `{expected}`. אין להניח שהמקסימום אינו שלילי.",
            f"Check every item; the result is `{expected}`. Do not assume a nonnegative maximum.",
            "source scan versus sorted reference",
            dict(values=values),
        )

    for v, (values, target) in enumerate(
        [
            ([1, 4, 7, 9, 12, 15, 20], 15),
            ([2, 5, 8, 11, 14, 17, 23], 5),
            ([-8, -4, -1, 0, 3, 6, 10], -4),
            ([0, 3, 6, 9, 12, 15, 18], 9),
            ([2, 4, 6, 8, 10, 12, 14], 12),
        ],
        1,
    ):
        mid = len(values) // 2
        labels = [
            ("ימינה, ללא האמצע", "Right, excluding the middle"),
            ("שמאלה, ללא האמצע", "Left, excluding the middle"),
            ("עוצרים: נמצאה התאמה", "Stop: a match was found"),
            ("חייבים לבדוק מחדש את כל הרשימה", "The entire list must be searched again"),
        ]
        index = 0 if target > values[mid] else 1 if target < values[mid] else 2
        assert target in (values[mid + 1 :] if index == 0 else values[:mid] if index == 1 else [values[mid]])
        # Bilingual text options require a small conversion after emit.
        emit(
            12,
            v,
            f"בחיפוש בינארי ברשימה העולה `{values}` מחפשים {target}. האיבר האמצעי שנבדק הוא {values[mid]}. מה הצעד הבא?",
            f"Binary search in the ascending list `{values}` seeks {target}. The middle item checked is {values[mid]}. What is the next step?",
            [x[1] for x in labels],
            labels[index][1],
            "סדר הרשימה מאפשר להשליך את הצד שבו היעד אינו יכול להימצא; בשוויון עוצרים.",
            "The ordering rules out the side that cannot contain the target; equality ends the search.",
            "target index and sorted partition membership",
            dict(values=values, target=target, middle=mid),
        )
        localize_choices(labels)

    for v, (n, missing) in enumerate([(6, 4), (1, 1), (8, 8), (7, 1), (9, 5)], 1):
        values = [i for i in range(n, 0, -1) if i != missing]
        result = source_function(14)(values, n)
        expected = repr(sorted(set(range(1, n + 1)) - set(values)))
        assert repr(result) == expected
        emit(
            14,
            v,
            f"הרשימה `{values}` כוללת את כל השלמים מ־1 עד {n} מלבד אחד, ללא כפילויות. פונקציה מחזירה רשימה ובה המספר החסר. מה תחזיר?",
            f"The list `{values}` contains all integers from 1 through {n} except one, with no duplicates. A function returns a list containing the missing number. What is returned?",
            [expected, "[]", repr([0]), repr([n + 1])],
            expected,
            f"מסמנים את הערכים שנמצאו בטווח, ומתעלמים מתא הדגל 0. התוצאה היא `{expected}`.",
            f"Mark encountered values within the range, ignoring flag index 0. The result is `{expected}`.",
            "source flag array versus set difference",
            dict(n=n, values=values),
        )

    for v, (values, target) in enumerate(
        [([3], 6), ([3, 3], 6), ([1, 4, 2], 6), ([-2, 5, 7], 3), ([], 0)], 1
    ):
        pairs = [
            (i, j)
            for i, j in itertools.combinations(range(len(values)), 2)
            if values[i] + values[j] == target
        ]
        assert source_function(15)(values, target) == bool(pairs)
        expected = len(pairs)
        emit(
            15,
            v,
            f"ברשימה `{values}` כמה זוגות אינדקסים שונים `i<j` נותנים סכום {target}? ערכים שווים באינדקסים שונים מותרים.",
            f"In `{values}`, how many distinct index pairs `i<j` sum to {target}? Equal values at different indices are allowed.",
            numeric_options(expected),
            expected,
            f"מונים רק זוגות עם `i<j`, בלי להשתמש באותו איבר פעמיים. יש {expected} זוגות מתאימים.",
            f"Count only pairs with `i<j`, never reusing an item. There are {expected} qualifying pairs.",
            "source pair existence versus exhaustive index pairs",
            dict(values=values, target=target, pairs=pairs),
        )

    for v, (a, b) in enumerate(
        [([2, 8], [4, 5]), ([-3, 1], [-1, 7]), ([6, 9], [1, 10]), ([0, 2], [3, 4]), ([5, 8], [-2, 6])], 1
    ):
        expected = min(a[0], b[0])
        assert sorted(a + b)[0] == expected
        emit(
            17,
            v,
            f"ממזגים את הרשימות הממוינות `{a}` ו־`{b}` בסדר עולה. איזה ערך יש להוציא ראשון, מראש אחת הרשימות?",
            f"Merge the sorted lists `{a}` and `{b}` in ascending order. Which value must be taken first from a list head?",
            list(dict.fromkeys(a + b)),
            expected,
            f"משווים רק בין הראשים. {expected} הוא הקטן מביניהם ולכן קודם במיזוג.",
            f"Compare the heads. {expected} is the smaller head and must come first.",
            "merge head versus full sorted reference",
            dict(a=a, b=b),
        )

    order_options = [
        ("רק הרשימה הראשונה", "Only the first list"),
        ("רק הרשימה השנייה", "Only the second list"),
        ("שתי הרשימות", "Both lists"),
        ("אף רשימה", "Neither list"),
    ]
    for v, (a, b) in enumerate(
        [([], [1, 1, 2]), ([3, 2], [-1, 0]), ([1], [2, 1]), ([2, 1], [0, -1]), ([-3, -3], [0, 0, 0])], 1
    ):
        actual = [source_function(18)(x) for x in (a, b)]
        assert actual == [x == sorted(x) for x in (a, b)]
        index = {(True, False): 0, (False, True): 1, (True, True): 2, (False, False): 3}[tuple(actual)]
        emit(
            18,
            v,
            f"איזו רשימה ממוינת בסדר לא יורד? הראשונה `{a}`, השנייה `{b}`. שוויון מותר; רשימה ריקה נחשבת ממוינת.",
            f"Which list is nondecreasing? First: `{a}`; second: `{b}`. Equal neighbors are allowed; an empty list counts as sorted.",
            [x[1] for x in order_options],
            order_options[index][1],
            "בודקים כל זוג סמוך. ירידה אחת פוסלת; שוויון אינו פוסל.",
            "Check each adjacent pair. One decrease invalidates a list; equal values do not.",
            "source adjacent comparisons versus sorted equality",
            dict(first=a, second=b),
        )
        localize_choices(order_options)

    for v, values in enumerate([[-2, 4, 0, 7], [], [-5, -1], [2, 2, -3], [0, 9, -9, 1]], 1):
        expected = sum(filter(lambda x: x > 0, values))
        assert source_function(31)(values) == expected
        emit(
            31,
            v,
            f"מה סכום האיברים החיוביים ממש ברשימה `{values}`? אפס ושליליים אינם נכללים.",
            f"What is the sum of the strictly positive items in `{values}`? Exclude zero and negative items.",
            numeric_options(expected, [sum(values), len(values)]),
            expected,
            f"מחברים רק ערכים הגדולים מ־0. מתקבל {expected}.",
            f"Add only values greater than 0. The result is {expected}.",
            "source filtered sum versus explicit selection",
            dict(values=values),
        )

    for v, s in enumerate(["code", "level", "", "abca", "Python"], 1):
        expected = "".join(s[i] for i in range(len(s) - 1, -1, -1))
        assert source_function(32)(s) == expected
        options = list(dict.fromkeys(map(repr, [expected, s, s[1:], s + s, "None", "x", "xy"])))[:4]
        emit(
            32,
            v,
            f"מה מחזיר ביטוי ה־Python `{s!r}[::-1]`? האפשרויות מוצגות כמחרוזות.",
            f"What does the Python expression `{s!r}[::-1]` return? Options are string representations.",
            options,
            repr(expected),
            "צעד שלילי בחיתוך קורא מהסוף להתחלה, כולל בקלט ריק.",
            "A negative slice step reads from end to start, including for empty input.",
            "source slicing versus reverse-index traversal",
            dict(text=s),
        )

    for v, (a, b) in enumerate([(2, 7), (-3, 4), (0, 9), (8, -1), (-5, -2)], 1):
        result = source_function(33)(a, b)
        assert result == (b, a)
        expected = repr(result)
        emit(
            33,
            v,
            f"ב־Python מתחילים ב־`a={a}, b={b}` ומבצעים `a,b=b,a`. מה הזוג `(a,b)` כעת?",
            f"In Python, initially `a={a}, b={b}`. Execute `a,b=b,a`. What is `(a,b)` now?",
            [expected, repr((a, b)), repr((a, a)), repr((b, b))],
            expected,
            "צד ימין מחושב לפני ההשמה, ולכן שני הערכים מוחלפים בלי לאבד אחד מהם.",
            "The right-hand side is evaluated before assignment, so the values swap without losing either one.",
            "source execution and parallel-assignment reference",
            dict(a=a, b=b),
        )

    for n, structure in [(34, "stack"), (35, "queue")]:
        for v, order in enumerate(["ABCD", "DACB", "CBAD", "BDCA", "DCBA"], 1):
            a, b, c, d = order
            patterns = [
                [a, b, None, c, d],
                [a, b, c, None, d, None],
                [a, b, c, d, None],
                [a, b, None, c, None, d],
                [a, b, c, None, None, d],
            ]
            operations = patterns[v - 1]
            q, removed = deque(), []
            for value in operations:
                if value is not None:
                    q.append(value)
                else:
                    removed.append(q.pop() if structure == "stack" else q.popleft())
            reference = []
            for value in operations:
                if value is not None:
                    reference.append(value)
                else:
                    del reference[-1 if structure == "stack" else 0]
            expected = q.pop() if structure == "stack" else q.popleft()
            assert expected == reference[-1 if structure == "stack" else 0]
            h = "מחסנית מוציאה את האחרון שנכנס" if structure == "stack" else "תור מוציא את הראשון שנכנס"
            e = (
                "A stack removes the last item inserted"
                if structure == "stack"
                else "A queue removes the first item inserted"
            )
            he_ops = ", ".join(f"מכניסים {x}" if x is not None else "מוציאים איבר" for x in operations)
            en_ops = ", ".join(f"insert {x}" if x is not None else "remove one item" for x in operations)
            emit(
                n,
                v,
                f"{h}. מתחילים במבנה ריק: {he_ops}. מי ייצא בהוצאה הבאה?",
                f"{e}. Start empty: {en_ops}. Which item leaves next?",
                list(order),
                expected,
                f"עוקבים אחרי ההכנסות וההוצאות לפי הסדר. האיבר הבא לפי כלל ההוצאה הוא {expected}.",
                f"Trace the insertions and removals in order. The next item under the removal rule is {expected}.",
                "deque simulation versus independent list trace",
                dict(kind=structure, operations=operations),
            )

    for v, values in enumerate([[4, 2, 4], [1, 1, 1, 1], [], [-1, 0, -1, 2], [5, 4, 3, 2, 5]], 1):
        expected = len(set(values))
        assert expected == len(Counter(values))
        emit(
            36,
            v,
            f"מוסיפים לקבוצת Python ריקה את כל הערכים ברשימה `{values}`. כמה איברים שונים יהיו בקבוצה?",
            f"Insert all values from `{values}` into an empty Python set. How many distinct elements remain?",
            numeric_options(expected),
            expected,
            f"קבוצה שומרת ערכים שונים בלבד, ולכן נשארים {expected} איברים.",
            f"A set retains distinct values only, leaving {expected} elements.",
            "set versus frequency-map keys",
            dict(values=values),
        )

    for v, order in enumerate(["ACDB", "BDAC", "CADB", "DBCA", "ABDC"], 1):
        links = dict(zip(order, order[1:] + "\0", strict=True))
        node, seen = order[0], []
        while node != "\0":
            seen.append(node)
            node = links[node]
        expected = ", ".join(seen)
        options = list(
            dict.fromkeys(
                [
                    expected,
                    ", ".join(sorted(order)),
                    ", ".join(reversed(order)),
                    ", ".join(order[1:] + order[0]),
                    ", ".join(order[::2] + order[1::2]),
                ]
            )
        )[:4]
        desc = "; ".join(f"{a}.next={b}" for a, b in zip(order, list(order[1:]) + ["None"], strict=True))
        emit(
            37,
            v,
            f"ברשימה מקושרת הראש הוא {order[0]}, והקישורים הם `{desc}`. מה סדר הביקור עד `None`?",
            f"A linked list starts at {order[0]} with links `{desc}`. What is the traversal order until `None`?",
            options,
            expected,
            "מתחילים בראש ועוקבים אחרי `next`; שמות הצמתים אינם קובעים סדר.",
            "Start at the head and follow `next`; node names do not determine the order.",
            "pointer-map traversal",
            dict(order=order, links=links),
        )

    for v, n in enumerate([7, 12, 1, 20, 5], 1):
        values = list(range(n))
        # Count actual equality checks for every present value and an absent value.
        # This verifies the maximum rather than assuming the requested bound.
        counts = []
        for target in values + [n]:
            comparisons = 0
            for value in values:
                comparisons += 1
                if value == target:
                    break
            counts.append(comparisons)
        assert max(counts) == n and counts[-1] == n
        emit(
            38,
            v,
            f"מחפשים ערך ברשימה לא ממוינת של {n} איברים, לפי הסדר, עד התאמה או סוף הרשימה. אין מידע נוסף. כמה השוואות נדרשות במקרה הגרוע ביותר?",
            f"Search an unsorted list of {n} items sequentially until a match or the end. No other information is available. How many comparisons are needed in the worst case?",
            numeric_options(n, [max(0, n - 1), n + 1, n * 2]),
            n,
            f"כשהערך חסר נבדקים כל {n} האיברים, ולכן נדרשות {n} השוואות.",
            f"An absent value requires checking all {n} items, so {n} comparisons are needed.",
            "unsuccessful sequential-search comparison count",
            dict(length=n),
        )

    for v, (a, left, right) in enumerate(
        [
            ([2, 3, 1, 4], 1, 2),
            ([-2, 5, 3, 1], 0, 2),
            ([4, -1, 2, 6], 2, 3),
            ([7, 0, -3, 5], 1, 3),
            ([1, 8, 2, -4], 0, 0),
        ],
        1,
    ):
        prefix = [0]
        for x in a:
            prefix.append(prefix[-1] + x)
        expected = prefix[right + 1] - prefix[left]
        assert expected == sum(a[left : right + 1])
        emit(
            39,
            v,
            f"לרשימה באורך {len(a)} נתון `P={prefix}`, כאשר `P[k]` הוא סכום `k` האיברים הראשונים ו־`P[0]=0`. מה סכום האיברים באינדקסים {left} עד {right} כולל? האינדקסים מתחילים ב־0.",
            f"Given `P={prefix}`, where `P[k]` sums the first `k` items of a {len(a)}-item list and `P[0]=0`, what is the sum at indices {left} through {right} inclusive? Indices start at 0.",
            numeric_options(expected, [prefix[right], prefix[left], prefix[-1]]),
            expected,
            f"מחסרים את הסכום שלפני הטווח: `P[{right + 1}]-P[{left}]={expected}`.",
            f"Subtract the prefix before the range: `P[{right + 1}]-P[{left}]={expected}`.",
            "prefix subtraction versus direct slice sum",
            dict(values=a, prefix=prefix, left=left, right=right),
        )

    for v, prices in enumerate([[7, 1, 5, 3, 6], [9, 7, 4, 2], [], [2, 8, 1, 4], [0, 3, 0, 5]], 1):
        expected = max(
            [0] + [prices[j] - prices[i] for i, j in itertools.combinations(range(len(prices)), 2)]
        )
        assert source_function(89)(prices) == expected
        emit(
            89,
            v,
            f"המחירים היומיים הם `{prices}`. מותרת קנייה אחת ומכירה ביום מאוחר יותר, או ויתור על העסקה ברווח 0. מה הרווח המרבי?",
            f"Daily prices are `{prices}`. Buy once and sell on a later day, or skip the transaction for profit 0. What is the maximum profit?",
            numeric_options(expected, [max(prices, default=0) - min(prices, default=0)]),
            expected,
            f"בודקים רק זוגות ימים לפי הסדר, ומשווים גם לוויתור על העסקה. הרווח המרבי הוא {expected}.",
            f"Consider only day pairs in time order, including skipping the trade. Maximum profit is {expected}.",
            "source linear algorithm versus exhaustive buy/sell pairs",
            dict(prices=prices),
        )

    for v, (previous, item) in enumerate([(-3, 4), (5, -2), (-7, -1), (2, 6), (0, -4)], 1):
        expected = max(item, previous + item)
        # A one-item predecessor realizes the supplied ending sum exactly.
        # Enumerate all nonempty suffixes ending at the new position separately.
        tiny_array = [previous, item]
        suffixes = [sum(tiny_array[start:]) for start in range(len(tiny_array))]
        assert max(suffixes) == expected
        emit(
            90,
            v,
            f"באלגוריתם Kadane הסכום המרבי של רצף סמוך לא ריק שמסתיים באיבר הקודם הוא {previous}. האיבר הבא הוא {item}. מה הסכום המרבי של רצף שמסתיים באיבר החדש?",
            f"In Kadane’s algorithm, the best nonempty contiguous sum ending at the previous item is {previous}. The next item is {item}. What is the best sum ending at the new item?",
            numeric_options(expected, [previous + item, previous, 0]),
            expected,
            f"בוחרים בין האיבר לבדו לבין הרחבת הרצף: `max({item}, {previous}+{item})={expected}`.",
            f"Choose the item alone or extend the previous subarray: `max({item}, {previous}+{item})={expected}`.",
            "enumeration of the two exhaustive ending-subarray cases",
            dict(previous=previous, item=item),
        )

    for v, records in enumerate(
        [
            [("A", 2), ("B", 1), ("C", 2)],
            [("Z", 3), ("A", 3), ("M", 1)],
            [("C", 0), ("A", -1), ("B", 0)],
            [("B", 5), ("C", 5), ("A", 5)],
            [("X", 2), ("Y", 0), ("Z", 0)],
        ],
        1,
    ):
        result = source_function(91)(records)
        expected = ", ".join(x[0] for x in result)
        reference = [records[i] for i in sorted(range(len(records)), key=lambda i: (records[i][1], i))]
        assert result == reference
        options = list(
            dict.fromkeys(
                [expected] + [", ".join(x) for x in itertools.permutations([r[0] for r in records])]
            )
        )[:4]
        emit(
            91,
            v,
            f"ממיינים את הרשומות `{records!r}` לפי המספר בסדר עולה, במיון יציב. מה סדר השמות בתוצאה?",
            f"Stably sort `{records!r}` by number in ascending order. What is the resulting name order?",
            options,
            expected,
            "המספר קובע את הסדר; ברשומות בעלות מספר שווה נשמר הסדר המקורי.",
            "The number determines order; equal-number records retain their original relative order.",
            "source stable sort versus explicit original-index tie breaker",
            dict(records=records),
        )

    for v, index in enumerate([2, 4, 1, 6, 3], 1):
        expected = index + 1
        assert set(range(index + 1)) == set(range(0, index)) | {index}
        emit(
            92,
            v,
            f"בערבוב Fisher–Yates תקין מטפלים באינדקס {index}. בוחרים באופן אחיד אינדקס להחלפה מתוך כל האינדקסים מ־0 ועד {index}, כולל החלפה עצמית. כמה אפשרויות בחירה צריכות להיות?",
            f"In correct Fisher–Yates shuffling, process index {index}. Choose uniformly among indices from 0 through {index}, including a self-swap. How many choices must be available?",
            numeric_options(expected, [index, index + 2, 1]),
            expected,
            f"הטווח כולל את שני הקצוות ולכן מכיל {expected} אינדקסים. אסור להשמיט את ההחלפה העצמית.",
            f"The inclusive range contains {expected} indices. The self-swap must remain possible.",
            "inclusive index-range enumeration",
            dict(index=index),
        )

    for v, (first, second) in enumerate(
        [("ACD", "BCD"), ("ABC", "DBC"), ("AC", "BD"), ("ABC", "ABC"), ("ABCD", "CD")], 1
    ):
        nodes = {name: object() for name in set(first + second)}
        actual = next(
            (name for name in first if any(nodes[name] is nodes[other] for other in second)), "None"
        )
        expected = next((name for name in first if name in set(second)), "None")
        assert actual == expected
        options = list(dict.fromkeys([expected, "None"] + list(first + second)))[:4]
        chain1, chain2 = " -> ".join(first) + " -> None", " -> ".join(second) + " -> None"
        emit(
            93,
            v,
            f"שתי רשימות מקושרות הן `{chain1}` ו־`{chain2}`. כל הצמתים מכילים 7; אות זהה מציינת את אותו צומת בזיכרון, ואותיות שונות מציינות צמתים נפרדים. מהו הצומת המשותף הראשון, או `None` אם אין כזה?",
            f"The linked lists are `{chain1}` and `{chain2}`. Every node stores 7; the same letter denotes the same object, and different letters denote distinct objects. What is the first shared node, or `None` if absent?",
            options,
            expected,
            f"משווים זהות צמתים ולא ערכים. מעבר לפי הקישורים מחזיר `{expected}`.",
            f"Compare node identity rather than values. Following the links gives `{expected}`.",
            "object-identity traversal versus first shared identifier",
            dict(first=first, second=second),
        )

    for v, (local, lt, global_value, gt, new, nt) in enumerate(
        [
            (2, 3, 9, 5, 4, 7),
            (8, 2, 6, 4, 1, 9),
            (-1, 1, 0, 6, 7, 8),
            (3, 4, 5, 8, 2, 10),
            (6, 2, -2, 7, 9, 11),
        ],
        1,
    ):
        assert lt < gt < nt
        expected = f"({global_value}, {new})"
        # Directly replay physical writes to a one-cell array as a separate model.
        # Compare that result with the lazy timestamp representation at each read.
        direct_cell = local
        direct_cell = global_value
        first_read = max([(local, lt), (global_value, gt)], key=lambda event: event[1])[0]
        assert first_read == direct_cell
        direct_cell = new
        second_read = max([(new, nt), (global_value, gt)], key=lambda event: event[1])[0]
        assert second_read == direct_cell and repr((first_read, second_read)) == expected
        options = [expected, f"({local}, {new})", f"({global_value}, {global_value})", f"({local}, {local})"]
        emit(
            94,
            v,
            f"חותמות הזמן עולות ואינן גולשות. בתא נשמר {local} בזמן {lt}, ו־`SetAll` שומר {global_value} בזמן {gt}. קוראים את התא; אחר כך כותבים בו {new} בזמן {nt} וקוראים שוב. מה זוג התוצאות לפי הסדר?",
            f"Timestamps increase without overflow. A cell stores {local} at time {lt}; `SetAll` stores {global_value} at time {gt}. Read the cell, write {new} locally at time {nt}, then read again. What is the ordered result pair?",
            options,
            expected,
            "בכל קריאה בוחרים את הערך בעל חותמת הזמן המאוחרת יותר: תחילה הכללי, ואז המקומי החדש.",
            "Each read selects the later timestamp: first the global value, then the new local value.",
            "ordered event replay with strictly increasing timestamps",
            dict(local=[local, lt], global_write=[global_value, gt], later=[new, nt]),
        )

    for v, n in enumerate([4, 6, 2, 8, 5], 1):
        memo = {0: 0, 1: 1}
        calculated = []

        def fib(k, memo=memo, calculated=calculated):
            if k not in memo:
                memo[k] = fib(k - 1) + fib(k - 2)
                calculated.append(k)
            return memo[k]

        fib(n)
        assert sorted(calculated) == list(range(2, n + 1)) and len(set(calculated)) == len(calculated)
        expected = len(calculated)
        emit(
            95,
            v,
            f"מחשבים `F({n})` לפי `F(k)=F(k-1)+F(k-2)` ושומרים כל תוצאה במטמון. `F(0)=0` ו־`F(1)=1` כבר שמורים. כמה ערכי `F` חדשים מחושבים? אין לספור פגיעות במטמון.",
            f"Compute `F({n})` using `F(k)=F(k-1)+F(k-2)` and cache every result. `F(0)=0` and `F(1)=1` are already cached. How many new `F` values are computed? Exclude cache hits.",
            numeric_options(expected, [n, n + 1, 2 * n]),
            expected,
            f"מחשבים פעם אחת כל ערך מ־`F(2)` עד `F({n})`: בסך הכול {expected} ערכים חדשים.",
            f"Compute each value from `F(2)` through `F({n})` once: {expected} new values.",
            "instrumented memoized recursion versus subproblem interval",
            dict(n=n, computed=calculated),
        )

    for v, (values, k) in enumerate(
        [([2, 5, 1], 2), ([-3, 4, 2, -1], 2), ([1, 2, 3, 4], 3), ([5, -2, 0], 1), ([2, 2, 2, 2], 2)], 1
    ):
        result = source_function(96)(values, k)
        expected = repr([sum(values[i : i + k]) for i in range(len(values) - k + 1)])
        assert repr(result) == expected
        options = list(
            dict.fromkeys(
                [
                    expected,
                    repr(result[::-1]),
                    repr([sum(values[:k])]),
                    repr(values),
                    repr([0] * len(result)),
                    "[]",
                ]
            )
        )[:4]
        emit(
            96,
            v,
            f"מהם סכומי כל החלונות הסמוכים באורך {k} ברשימה `{values}`, לפי סדר ההתחלה שלהם?",
            f"What are the sums of all contiguous length-{k} windows in `{values}`, in starting-position order?",
            options,
            expected,
            "מסכמים את החלון הראשון; בכל הזזה מחסרים את האיבר היוצא ומוסיפים את הנכנס.",
            "Sum the first window; each move subtracts the departing item and adds the arriving one.",
            "source incremental window versus direct slice sums",
            dict(values=values, k=k),
        )

    truth_options = ["(True, True)", "(True, False)", "(False, True)", "(False, False)"]
    for v, value in enumerate([0, None, 3, 7, 1], 1):
        expected = repr((bool(value), value is not None))
        emit(
            97,
            v,
            f"ב־Python פונקציית חיפוש מחזירה אינדקס או `None`. עבור `result={value}` מה הזוג `(bool(result), result is not None)`?",
            f"In Python, a search returns an index or `None`. For `result={value}`, what is `(bool(result), result is not None)`?",
            truth_options,
            expected,
            "אפס הוא ערך שקרי אך אינו `None`; בדיקת זהות ל־`None` מבדילה בין אינדקס תקין להיעדר התאמה.",
            "Zero is false in a condition but is not `None`; testing identity against `None` distinguishes a valid index from no match.",
            "Python truth conversion and None identity",
            dict(result=value),
        )

    label_options = ["['positive', 'even']", "['positive']", "['even']", "[]"]
    for v, number in enumerate([2, 3, 0, -4, -3], 1):
        expected = repr((["positive"] if number > 0 else []) + (["even"] if number % 2 == 0 else []))
        assert repr(source_function(98)(number)) == expected
        emit(
            98,
            v,
            f"מוסיפים תווית `positive` כשהמספר גדול מ־0, ואחריה `even` כשהוא זוגי, בשתי בדיקות `if` נפרדות. מה הרשימה עבור {number}?",
            f"Append `positive` when the number exceeds 0, then `even` when it is even, using two separate `if` tests. What list is returned for {number}?",
            label_options,
            expected,
            "שני התנאים נבדקים באופן עצמאי, ולכן עשויות להתווסף שתי תוויות.",
            "Both conditions are tested independently, so both labels may be added.",
            "source branch execution versus independent predicate concatenation",
            dict(number=number),
        )

    for v, (first, second) in enumerate([(1, 2), (4, 7), (-1, 0), (8, 8), (3, -2)], 1):
        function = source_function(99)
        a, b = function(first), function(second)
        assert a == [first] and b == [second] and a is not b
        expected = f"({a!r}, {b!r})"
        emit(
            99,
            v,
            f"ב־Python הפונקציה `add_item(item, items=None)` יוצרת רשימה ריקה חדשה כש־`items is None`, מוסיפה אליה את `item` ומחזירה אותה. מבצעים `a=add_item({first})` ואז `b=add_item({second})`. מה הזוג `(a,b)` אחרי שתי הקריאות?",
            f"In Python, `add_item(item, items=None)` creates a fresh empty list when `items is None`, appends `item`, and returns the list. Execute `a=add_item({first})`, then `b=add_item({second})`. What is `(a,b)` after both calls?",
            [
                expected,
                f"({[first, second]!r}, {[first, second]!r})",
                f"({[first]!r}, {[first, second]!r})",
                "([], [])",
            ],
            expected,
            "בכל קריאה בלי רשימה מפורשת נוצרת רשימה חדשה, כך שהקריאות אינן חולקות רשימה.",
            "Each call without an explicit list creates a fresh list, so the calls do not share one.",
            "source repeated calls and distinct list identity",
            dict(first=first, second=second),
        )

    for v, n in enumerate([0, 1, 4, 7, 10], 1):
        expected = n * (n + 1) // 2
        assert source_function(100)(n) == expected
        eh = (
            f"גבול העצירה אינו נכלל, ולכן מסכמים מ־1 עד {n} כולל. הסכום הוא {expected}."
            if n
            else "הביטוי range(1, 1) ריק כי גבול העצירה אינו נכלל. סכום הרצף הריק הוא 0."
        )
        ee = (
            f"The stop boundary is excluded, so the sum includes 1 through {n}. The sum is {expected}."
            if n
            else "The range(1, 1) sequence is empty because the stop boundary is excluded. Its sum is 0."
        )
        emit(
            100,
            v,
            f"מה ערך הביטוי `sum(range(1, {n}+1))` ב־Python?",
            f"What is the value of `sum(range(1, {n}+1))` in Python?",
            numeric_options(expected, [n * (n - 1) // 2, n]),
            expected,
            eh,
            ee,
            "source range sum versus arithmetic-series formula",
            dict(n=n),
        )

    for v, (values, target) in enumerate(
        [([1, 4, 1, 4], 5), ([3, 3, 3], 6), ([2, 2, 5], 7), ([0, 0, 0, 0], 0), ([1, 2, 3, 4, 5], 6)], 1
    ):
        expected = sum(
            values[i] + values[j] == target for i, j in itertools.combinations(range(len(values)), 2)
        )
        seen, count = Counter(), 0
        for x in values:
            count += seen[target - x]
            seen[x] += 1
        assert count == expected
        emit(
            119,
            v,
            f"כמה זוגות אינדקסים `i<j` ברשימה `{values}` נותנים סכום {target}? סופרים בנפרד מופעים שונים גם כשערכיהם שווים.",
            f"How many index pairs `i<j` in `{values}` sum to {target}? Distinct occurrences count separately even when values match.",
            numeric_options(expected),
            expected,
            f"מונים זוגות אינדקסים ולא רק זוגות ערכים. יש {expected} זוגות מתאימים.",
            f"Count index pairs rather than just value pairs. There are {expected} qualifying pairs.",
            "exhaustive pair enumeration versus frequency accumulation",
            dict(values=values, target=target),
        )

    for v, (a, b) in enumerate([(2, 6), (3, 5), (0, 8), (7, 9), (4, 5)], 1):
        z = a ^ b
        mask = source_function(120)(z)
        expected = 1 << next(i for i in range(z.bit_length()) if ((a >> i) & 1) != ((b >> i) & 1))
        assert mask == expected and bool(a & mask) != bool(b & mask)
        emit(
            120,
            v,
            f"שני המספרים החסרים הם {a} ו־{b}. מתקבל `z={a} XOR {b}`. מה ערך המסכה `z & -z` ב־Python, המבודדת את הביט הדלוק הנמוך ביותר?",
            f"The missing values are {a} and {b}, giving `z={a} XOR {b}`. What is Python’s `z & -z` mask, isolating the lowest set bit?",
            numeric_options(mask, [z, a, b]),
            mask,
            f"המסכה היא {mask}; בביט הזה שני החסרים שונים ולכן יופרדו לשתי קבוצות.",
            f"The mask is {mask}; the missing values differ at that bit, separating them into two groups.",
            "source mask versus first differing bit enumeration",
            dict(a=a, b=b, xor=z),
        )

    for v, value in enumerate([1, 2, 12, 129, 0], 1):
        expected = int(f"{value:08b}"[::-1], 2)
        assert source_function(121)(value) == expected
        emit(
            121,
            v,
            f"הופכים את סדר כל 8 הסיביות של {value}, המיוצג כ־`{value:08b}`. מה הערך העשרוני של התוצאה? גם אפסים מובילים משתתפים.",
            f"Reverse all 8 bits of {value}, represented as `{value:08b}`. What is the decimal result? Include leading zeros.",
            numeric_options(expected, [value, 255 - value]),
            expected,
            f"הייצוג ההפוך הוא `{expected:08b}`, ולכן הערך העשרוני הוא {expected}.",
            f"The reversed representation is `{expected:08b}`, giving decimal value {expected}.",
            "source bit loop versus fixed-width string reversal",
            dict(value=value, width=8),
        )

    for v, coords in enumerate(
        [
            (2, 0, 2, 4, 0, 2),
            (-2, 4, -2, 0, 0, 2),
            (0, 0, 4, 4, 1, 2),
            (4, 4, 0, 0, 3, 2),
            (1, -2, 5, 6, 1, 0),
        ],
        1,
    ):
        ax, ay, bx, by, px, py = coords
        assert min(ay, by) < py < max(ay, by)
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        assert cross != 0
        x_intersect = Fraction(ax) + Fraction((bx - ax) * (py - ay), by - ay)
        right = source_function(122)(*coords)
        assert right == (x_intersect > px)
        expected = (
            ("ימינה; הסימנים זהים", "Right; the signs match")
            if right
            else ("שמאלה; הסימנים שונים", "Left; the signs differ")
        )
        options = [
            ("ימינה; הסימנים זהים", "Right; the signs match"),
            ("שמאלה; הסימנים שונים", "Left; the signs differ"),
            ("על הנקודה; המכפלה הווקטורית אפס", "At the point; the cross product is zero"),
            ("אין חיתוך בגובה הנקודה", "No intersection at the point’s height"),
        ]
        emit(
            122,
            v,
            f"נתונים `A=({ax},{ay}), B=({bx},{by}), P=({px},{py})`. הקטע חוצה את גובה `P` ממש בין קצותיו. נגדיר `cross=(Bx-Ax)*(Py-Ay)-(By-Ay)*(Px-Ax)`. באיזה צד של `P` החיתוך האופקי, ומה הקשר בין סימני `cross` ו־`By-Ay`?",
            f"Given `A=({ax},{ay}), B=({bx},{by}), P=({px},{py})`, the segment strictly straddles P’s height. Define `cross=(Bx-Ax)*(Py-Ay)-(By-Ay)*(Px-Ax)`. Which side of P contains the horizontal intersection, and how do the signs of `cross` and `By-Ay` compare?",
            [x[1] for x in options],
            expected[1],
            f"מתקבל `cross={cross}` ו־`By-Ay={by - ay}`. סימנים זהים מציינים חיתוך מימין; סימנים שונים מציינים חיתוך משמאל.",
            f"Here `cross={cross}` and `By-Ay={by - ay}`. Matching signs mean rightward; different signs mean leftward.",
            "source orientation test versus exact rational intersection",
            dict(coordinates=coords, cross=cross, x_intersection=str(x_intersect)),
        )
        localize_choices(options)

    for v, prime in enumerate([3, 5, 7, 11, 2], 1):
        expected = prime * prime
        smaller = [p for p in range(2, prime) if all(p % d for d in range(2, p))]
        assert all(any((prime * k) % p == 0 for p in smaller) for k in range(2, prime))
        assert all(expected % p != 0 for p in smaller)
        emit(
            123,
            v,
            f"בנפת ארטוסתנס כבר טופלו כל הראשוניים הקטנים מ־{prime}. מהי הכפולה הראשונה של {prime} שעשויה להימחק לראשונה בשלב שלו? אין למחוק את הראשוני עצמו.",
            f"In the Sieve of Eratosthenes, all primes smaller than {prime} have been processed. What is the first multiple of {prime} that may be newly marked at its stage? Do not mark the prime itself.",
            numeric_options(expected, [prime, 2 * prime, expected + prime]),
            expected,
            f"כל כפולה קטנה יותר, מלבד {prime} עצמו, כבר מסומנת דרך גורם ראשוני קטן יותר. מתחילים ב־{expected}.",
            f"Each smaller multiple other than {prime} itself was already marked via a smaller prime factor. Start at {expected}.",
            "enumerated smaller-multiple factor coverage",
            dict(prime=prime, smaller_primes=smaller),
        )

    bracket_cases = [
        ["([])", "([)]", "(()", "]["],
        ["{[]}", "{[}]", "}{", "(()"],
        ["[()()]", "[)(]", "[(])", "]["],
        ["({[]})", "({[}])", "())(", "{{}"],
        ["()[]{}", "([{})]", "][][", "((]"],
    ]

    def valid(text):
        stack = []
        for c in text:
            if c in "([{":
                stack.append(c)
            elif not stack or stack.pop() != {")": "(", "]": "[", "}": "{"}[c]:
                return False
        return not stack

    for v, choices in enumerate(bracket_cases, 1):
        assert [valid(x) for x in choices] == [True, False, False, False]
        expected = code(choices[0])
        candidates = ", ".join(code(x) for x in choices)
        emit(
            124,
            v,
            f"נתונות המחרוזות {candidates}. איזו מהן מקוננת כהלכה? כל סימן סגירה חייב להתאים לפותח האחרון שטרם נסגר.",
            f"Given strings {candidates}, which is correctly nested? Each closing bracket must match the most recent unmatched opener.",
            [code(x) for x in choices],
            expected,
            "בדיקת מחסנית מקבלת רק את המחרוזת המסומנת: בכל סגירה הסוג מתאים, ובסוף המחסנית ריקה.",
            "A stack check accepts only the marked string: each closing type matches and the stack ends empty.",
            "stack parser on all four candidate strings",
            dict(strings=choices, valid=[True, False, False, False]),
        )

    for v, (root, left, right) in enumerate(
        [(3, 99, 4), (-2, -1, -5), (8, 12, 10), (7, 1, 4), (0, -3, 5)], 1
    ):
        expected = max(root, left, right)
        assert sorted([root, left, right])[-1] == expected
        emit(
            125,
            v,
            f"בעץ בינארי השורש הוא {root}, הבן השמאלי {left} והימני {right}; שניהם עלים. אין הבטחה של עץ חיפוש. מהו הערך המרבי בעץ?",
            f"A binary tree has root {root}, left child {left}, and right child {right}; both children are leaves. No search-tree ordering is guaranteed. What is its maximum value?",
            numeric_options(expected, [root, left, right]),
            expected,
            f"בודקים את כל שלושת הצמתים. המקסימום הוא {expected}; מיקום ימני אינו מבטיח ערך גדול יותר בעץ בינארי כללי.",
            f"Inspect all three nodes. The maximum is {expected}; a rightward position does not guarantee a larger value in a general binary tree.",
            "full node enumeration versus sorted maximum",
            dict(root=root, left=left, right=right),
        )

    owned = {key for key, q in SOURCES.items() if q["topic"] != "reasoning" and key != "quick-sw-03"}
    assert len(owned) == 36
    assert {q["source_key"] for q in QUESTIONS} == owned
    assert len(QUESTIONS) == 180
    return QUESTIONS, CHECKS


def localize_choices(pairs):
    translations = {en: he for he, en in pairs}
    for option in QUESTIONS[-1]["choices"]:
        option["he"] = translations[option["en"]]


if __name__ == "__main__":
    questions, checks = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in [("code.json", questions), ("code.checks.json", checks)]:
        (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified and wrote {len(questions)} questions for 36 sources.")
