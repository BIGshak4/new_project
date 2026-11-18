"""Interview-linked reasoning exercises with exact answers and worked bilingual explanations."""

from __future__ import annotations

import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content/fundamentals-reasoning-800.json"
OUT = ROOT / "backend/seeds/duel_quiz_batches"
LANGUAGES = ("he", "en")


def bilingual(pair, data):
    return {lang: text.format(**data) for lang, text in zip(LANGUAGES, pair, strict=True)}


def build_bundle():
    cards, rows, checks = [], [], []

    def add(task, ref, difficulty, title, prompt, why, takeaway, fields, cases, solve):
        number = 351 + len(cards)
        source = f"quick-sw-{number}"
        refs = [f"PREP-{ref:03d}"]
        assert len(cases) == 5
        for variant, values in enumerate(cases, 1):
            data = dict(zip(fields.split(), values, strict=True))
            expected, distractors = solve(**data)
            # Prefer task-specific mistakes; use nearby counts to resolve ties at boundaries.
            expected = Fraction(expected)
            pool = [*map(Fraction, distractors), expected + 1, abs(expected - 1), expected + 2, expected + 3]
            options = [str(expected), *[str(x) for x in dict.fromkeys(pool) if x != expected][:3]]
            correct = (number + variant) % 4
            if correct:
                options = options[-correct:] + options[:-correct]
            example = {**data, "answer": str(expected)}
            row = dict(
                key=f"{source}-v{variant}",
                source_key=source,
                variant=variant,
                topic="reasoning",
                status="draft",
                prompt=bilingual(prompt, example),
                choices=[{"he": x, "en": x} for x in options],
                correct=correct,
                explanation=bilingual(why, example),
            )
            rows.append(row)
            checks.append(
                dict(
                    key=row["key"],
                    task=task,
                    inputs=data,
                    options=options,
                    expected=str(expected),
                    method="Independent case oracle in test_fundamentals_reasoning_800.py",
                    professional_review="pending",
                    authorship="AI-assisted original principle exercise",
                    interviewIds=refs,
                    source_relation="Original exercise based on a principle of the linked interview",
                    difficulty=difficulty,
                    source_difficulty=difficulty,
                    difficulty_rationale=row["explanation"]["en"],
                    source_difficulty_rationale=takeaway[1],
                )
            )
            if variant == 1:
                cards.append(
                    dict(
                        id=source,
                        topic="reasoning",
                        interviewIds=refs,
                        title=bilingual(title, example),
                        prompt=row["prompt"],
                        answer=row["explanation"],
                        takeaway=bilingual(takeaway, example),
                    )
                )

    add(
        "copy_scale",
        374,
        3,
        ("הגדלה שונה למודל ולציור", "Copying at unequal magnifications"),
        (
            "מודל ברוחב {w} ס״מ נראה דרך הגדלה אופקית פי {m}. את הקנבס רואים בהגדלה פי {c}. מה יהיה רוחב הציור בס״מ כששני הרוחבים הנראים ישתוו?",
            "A model of width {w} cm is viewed with horizontal magnification {m}. The canvas is viewed with magnification {c}. How wide in cm will the painting be when the apparent widths match?",
        ),
        (
            "הרוחב הנראה של המודל הוא {w} × {m}. מחלקים בהגדלה של הקנבס, {c}, ומקבלים רוחב פיזי של {answer} ס״מ.",
            "The model appears {w} × {m} cm wide. Dividing by the canvas magnification of {c} gives a physical width of {answer} cm.",
        ),
        (
            "כותבים את תנאי השוויון במרחב הנראה ואז ממירים ליחידות פיזיות.",
            "Equate the apparent sizes before converting back to physical units.",
        ),
        "w m c",
        [(8, 3, 2), (10, 2, 4), (7, 3, 3), (9, 2, 3), (5, 3, 4)],
        lambda w, m, c: (Fraction(w * m, c), [w, Fraction(w * c, m), w * m, w * c]),
    )

    add(
        "traffic_delay",
        375,
        2,
        ("כמה זמן נוסף בגלל העומס?", "How much time did congestion add?"),
        (
            "קטע כביש שאורכו {d} ק״מ ארך היום {t} דקות. המהירות באותו קטע בכביש פנוי היא {v} קמ״ש. כמה דקות נוספו לזמן הנסיעה לעומת כביש פנוי?",
            "A {d} km road segment took {t} minutes today. Its free-flow speed is {v} km/h. How many minutes did congestion add relative to the free-flow trip?",
        ),
        (
            "זמן הנסיעה בכביש פנוי בדקות הוא 60 × {d} / {v}. הפחתתו מ־{t} נותנת עיכוב של {answer} דקות.",
            "Free-flow time in minutes is 60 × {d} / {v}. Subtracting it from {t} gives a delay of {answer} minutes.",
        ),
        (
            "עיכוב ביחס לזמן ייחוס יכול להצטבר גם תוך כדי תנועה.",
            "Delay relative to a baseline can accumulate while the vehicle is moving.",
        ),
        "d v t",
        [(12, 60, 20), (6, 30, 12), (15, 90, 16), (3, 40, 7), (25, 75, 50)],
        lambda d, v, t: (t - Fraction(60 * d, v), [t, Fraction(60 * d, v), t + Fraction(60 * d, v)]),
    )

    add(
        "hidden_share",
        376,
        3,
        ("חלוקה אחידה כשסוג האסימון נסתר", "Equal shares from hidden token types"),
        (
            "ידוע שבאוסף יש {a} אסימונים מסוג A ועוד {b} מסוג B, אך אי אפשר לזהות אותם. לוקחים מכל אסימון אותו חלק. איזה חלק מכל אסימון יש לקחת כדי שכמות החומר מסוג A, ביחידות של אסימון שלם, תהיה {goal}?",
            "A collection contains {a} tokens of type A and {b} of type B, with hidden labels. The same fraction is taken from every token. Which fraction makes the amount of type A, measured in whole-token units, equal to {goal}?",
        ),
        (
            "אם החלק מכל אסימון הוא f, הכמות מסוג A היא {a} × f. כדי לקבל {goal}, מחלקים ב־{a} ומקבלים {answer}.",
            "Taking fraction f of each token collects {a} × f units of A. Dividing the target {goal} by {a} gives {answer}.",
        ),
        (
            "איסוף אותו חלק מכל פריט שומר על הרכב האוסף.",
            "Taking the same fraction of every item preserves the composition.",
        ),
        "a b goal",
        [(4, 2, 1), (6, 4, 2), (3, 6, 2), (5, 3, 4), (4, 5, 0)],
        lambda a, b, goal: (
            Fraction(goal, a),
            [Fraction(goal, a + b), Fraction(a, a + b), Fraction(1, b), 1],
        ),
    )

    add(
        "cooldown_return",
        372,
        3,
        ("מתי תווית יכולה להופיע שוב?", "When can a label return?"),
        (
            "בכל הגרלה בוחרים באופן אחיד מבין {n} תוויות, למעט {k} התוצאות האחרונות. בדיוק {k} תוצאות שונות התקבלו מאז שהתווית X הופיעה. מה ההסתברות לקבל X בהגרלה הבאה?",
            "Each draw is uniform over {n} labels excluding the last {k} results. Exactly {k} distinct results have occurred since label X last appeared. What is the probability of X on the next draw?",
        ),
        (
            "התווית X כבר מחוץ לחלון. מספר התוויות המותרות הוא {n} פחות {k}, ורק אחת מהן היא X. מכאן שההסתברות היא {answer}.",
            "X has left the exclusion window. There are {n} minus {k} eligible labels, exactly one of which is X. The probability is {answer}.",
        ),
        (
            "הסיכוי בהגרלה מותנה בקבוצת התוויות הזמינות כרגע.",
            "The draw probability depends on the currently eligible labels.",
        ),
        "n k",
        [(8, 3), (5, 4), (9, 1), (10, 5), (7, 2)],
        lambda n, k: (Fraction(1, n - k), [0, Fraction(1, n), Fraction(k, n), Fraction(1, k)]),
    )

    add(
        "cooldown_sequences",
        372,
        4,
        ("ספירת רצפים עם איסור חזרה", "Counting sequences with a repeat exclusion"),
        (
            "מתחילים בהיסטוריה ריקה, עם {n} סמלים. בכל צעד אסור לבחור סמל שהופיע ב־{k} הצעדים האחרונים. כמה רצפים שונים באורך {t} אפשר ליצור?",
            "Start with an empty history and {n} symbols. At each step, exclude symbols seen in the last {k} steps. How many different sequences of length {t} are possible?",
        ),
        (
            "בצעד הראשון יש {n} אפשרויות. אחרי j צעדים נגרעות min(j, {k}) אפשרויות. כפל מספרי האפשרויות לאורך {t} הצעדים נותן {answer} רצפים.",
            "The first step allows {n} choices. After j steps, min(j, {k}) choices are excluded. Multiplying the choices across {t} steps gives {answer} sequences.",
        ),
        (
            "לפני שהחלון מתמלא, מספר האפשרויות משתנה בכל צעד.",
            "The number of choices changes while the exclusion window fills.",
        ),
        "n k t",
        [(4, 2, 4), (3, 1, 4), (5, 3, 2), (3, 2, 5), (4, 2, 1)],
        lambda n, k, t: (
            math.prod(n - min(i, k) for i in range(t)),
            [n**t, (n - k) ** t, n * (n - 1) ** (t - 1), math.factorial(n)],
        ),
    )

    add(
        "cooldown_cycle",
        372,
        3,
        ("חלון שהופך את ההמשך לקבוע", "When the exclusion window forces a cycle"),
        (
            "יש {n} כרטיסים הממוספרים מ־1 עד {n}. אי אפשר לבחור שוב כרטיס שהופיע ב־{k} הבחירות האחרונות. הבחירות הראשונות היו כל הכרטיסים בסדר עולה. איזה מספר יופיע בבחירה ה־{t}?",
            "There are {n} cards numbered 1 through {n}. No card from the previous {k} picks may be chosen. The first picks were all the cards in increasing order. Which number appears on pick {t}?",
        ),
        (
            "החלון חוסם {k} מתוך {n} הכרטיסים. בכל תור יוצא ממנו בדיוק הכרטיס הבא בסדר המקורי, ולכן הסדרה מחזורית. בבחירה ה־{t} מתקבל {answer}.",
            "The window blocks {k} of the {n} cards. Each turn releases the next card in the original order, so the sequence cycles. Pick {t} gives {answer}.",
        ),
        (
            "כשרק תוצאה אחת מותרת, ההמשך נקבע גם אם הבחירות הראשונות היו אקראיות.",
            "Once only one outcome is legal, the continuation is determined even after a random start.",
        ),
        "n k t",
        [(4, 3, 6), (5, 4, 10), (5, 4, 7), (6, 5, 14), (4, 3, 9)],
        lambda n, k, t: ((t - 1) % n + 1, [t % n or n, t % k + 1, n, k, *range(1, n + 1)]),
    )

    add(
        "service_sites",
        358,
        3,
        ("מתדלוקים ביום למספר תחנות", "From daily refuels to a station count"),
        (
            "במודל לעיר דרושים {d} תדלוקים ביום. בכל תחנה {p} עמדות, וכל עמדה משלימה {r} תדלוקים בשעה במשך {h} שעות. מה מספר התחנות השלם המזערי שיכול לספק את הביקוש?",
            "A model city needs {d} refuels per day. Each station has {p} pumps, each serving {r} cars per hour for {h} hours. What is the minimum whole number of stations with adequate daily capacity?",
        ),
        (
            "הקיבולת היומית של תחנה היא {p} × {r} × {h}. מחלקים את {d} בקיבולת ומעגלים כלפי מעלה. נדרשות {answer} תחנות.",
            "Daily capacity per station is {p} × {r} × {h}. Divide {d} by that capacity and round up. This requires {answer} stations.",
        ),
        ("מחשבים ביקוש והספק באותן יחידות זמן.", "Express demand and capacity over the same time interval."),
        "d p r h",
        [(1000, 4, 8, 10), (960, 3, 8, 10), (481, 4, 10, 12), (200, 2, 6, 10), (1199, 5, 8, 10)],
        lambda d, p, r, h: (
            math.ceil(Fraction(d, p * r * h)),
            [d // (p * r * h), math.ceil(Fraction(d, r * h)), math.ceil(Fraction(d, p * h)), 1],
        ),
    )

    add(
        "station_bounds",
        358,
        3,
        ("איזה תרחיש דורש הכי הרבה תחנות?", "Which scenario needs the most sites?"),
        (
            "הביקוש היומי הוא בין {lo} ל־{hi} ביקורים. הקיבולת לתחנה היא בין {a} ל־{b} ביקורים ביום. בהנחה שכל צירוף אפשרי, מה מספר התחנות המזערי שיספיק בוודאות?",
            "Daily demand ranges from {lo} to {hi} visits. Capacity per station ranges from {a} to {b} visits per day. Any combination is possible. What is the smallest number of stations sufficient in the worst case?",
        ),
        (
            "מצרפים את הביקוש המרבי {hi} לקיבולת המזערית {a}. חלוקה ועיגול כלפי מעלה נותנים {answer} תחנות.",
            "Pair maximum demand {hi} with minimum capacity {a}. Divide and round up to get {answer} stations.",
        ),
        (
            "חסם שמבטיח כיסוי מחייב לשלב את הקצוות המחמירים יחד.",
            "A guaranteed capacity bound must account for the adverse extremes together.",
        ),
        "lo hi a b",
        [(400, 600, 80, 120), (750, 900, 100, 150), (64, 65, 16, 32), (90, 120, 40, 60), (100, 100, 24, 25)],
        lambda lo, hi, a, b: (
            math.ceil(Fraction(hi, a)),
            [math.ceil(Fraction(lo, b)), math.ceil(Fraction(hi, b)), math.ceil(Fraction(lo, a)), hi // a],
        ),
    )

    add(
        "weighing_label",
        344,
        2,
        ("קריאת המשקל מקודדת את מספר השק", "A scale reading encodes a bag number"),
        (
            "משק שמספרו j נלקחו j מטבעות. רק בשק אחד משקל כל מטבע שונה מהרגיל ב־{delta} גרם, כולל הסימן. הסכום שנמדד הוא {actual} גרם במקום {normal} גרם. מה מספר השק החריג?",
            "Exactly j coins were taken from bag j. In just one bag, each coin differs from normal by {delta} grams, including the sign. The reading is {actual} grams instead of {normal} grams. Which bag is unusual?",
        ),
        (
            "ההפרש בין {actual} ל־{normal} נוצר כולו בשק החריג. חלוקתו בהפרש למטבע, {delta}, מחזירה את מספר השק {answer}.",
            "The entire difference between {actual} and {normal} comes from the unusual bag. Dividing by the signed per-coin difference {delta} gives bag {answer}.",
        ),
        (
            "מספר מטבעות שונה מכל שק הופך את הפרש המשקל לחתימה.",
            "Distinct sample counts turn the mass difference into a bag signature.",
        ),
        "delta normal actual",
        [(2, 150, 158), (-2, 300, 294), (3, 450, 453), (-1, 180, 174), (4, 240, 260)],
        lambda delta, normal, actual: (
            (actual - normal) // delta,
            [abs(actual - normal), abs(delta), abs(actual - normal) // abs(delta) + 1, 0],
        ),
    )

    add(
        "zero_sample",
        344,
        4,
        ("שק שלא משתתף גם הוא משאיר סימן", "An unsampled bag also leaves a signature"),
        (
            "בדיוק אחד מבין {n} שקים מכיל מטבעות כבדים יותר בהפרש ידוע. יש די מטבעות בכל שק ומשקל דיגיטלי מדויק לשקילה אחת. מותר לדגום אפס מטבעות משק. כמה מטבעות יש לשקול לכל הפחות כדי לזהות תמיד את השק?",
            "Exactly one of {n} bags contains coins heavier by a known amount. Each bag has enough coins. You get one exact digital weighing and may sample zero coins from a bag. What is the fewest total coins needed to always identify the bag?",
        ),
        (
            "כל שני שקים שנדגמו באותה כמות היו מפיקים אותה סטייה. לכן בוחרים {n} כמויות שונות, החל מאפס. סכומן המזערי הוא {answer}.",
            "Two bags with the same sample count would produce the same deviation. Use {n} distinct counts starting at zero. Their minimum sum is {answer}.",
        ),
        (
            "גם תוצאה ללא סטייה נושאת מידע כשמובטח שיש שק חריג.",
            "A zero deviation carries information when an unusual bag is guaranteed.",
        ),
        "n",
        [(5,), (2,), (8,), (6,), (4,)],
        lambda n: (n * (n - 1) // 2, [n * (n + 1) // 2, n, n - 1, n * n]),
    )

    add(
        "opening_byes",
        317,
        2,
        ("כמה משתתפים עולים בלי משחק?", "How many entrants receive an opening bye?"),
        (
            "בטורניר הדחה יש {n} משתתפים. משבצים אותם בטבלה המזערית שמספר המקומות בה הוא חזקה של 2. כל מקום ריק משובץ מול משתתף בסיבוב הראשון. כמה משתתפים עולים אוטומטית?",
            "A knockout tournament has {n} entrants. Use the smallest bracket with a power-of-2 number of slots. Each empty slot faces an entrant in the opening round. How many entrants receive a bye?",
        ),
        (
            "מכפילים את גודל הטבלה עד שיש מקום ל־{n}. מספר המקומות הפנויים שווה למספר העולים אוטומטית, והוא {answer}.",
            "Double the bracket size until it fits {n}. Each unfilled slot gives one automatic advance, for {answer} byes.",
        ),
        (
            "מקום ריק בטבלה מאפשר עלייה בלי להדיח שחקן.",
            "An empty slot advances one entrant without eliminating anyone.",
        ),
        "n",
        [(13,), (16,), (17,), (6,), (31,)],
        lambda n: ((1 << (n - 1).bit_length()) - n, [n // 2, (n - 1).bit_length(), n % 2, n - 1]),
    )

    add(
        "survivor_rounds",
        317,
        3,
        ("מי נשאר אחרי כמה סיבובים?", "How many survive several rounds?"),
        (
            "מתוך {n} משתתפים מזווגים בכל סיבוב כמה שיותר זוגות. בכל משחק יש מודח אחד, ומשתתף בודד עולה אוטומטית. כמה משתתפים נשארים אחרי {r} סיבובים?",
            "Starting with {n} entrants, form as many pairs as possible each round. Each match eliminates one entrant, and an unpaired entrant advances. How many entrants remain after {r} rounds?",
        ),
        (
            "בכל סיבוב שורד אחד מכל זוג, וגם המשתתף הבודד אם יש כזה. חצייה בעיגול מעלה, {r} פעמים החל מ־{n}, משאירה {answer}.",
            "One survives from each pair, as does a possible unpaired entrant. Halving {n} with upward rounding for {r} rounds leaves {answer}.",
        ),
        (
            "אם מספר המשתתפים אי־זוגי, מעגלים את מחציתו כלפי מעלה כדי לספור את השורדים.",
            "An odd field rounds the survivor count upward.",
        ),
        "n r",
        [(13, 2), (17, 4), (12, 2), (9, 1), (31, 3)],
        lambda n, r: (math.ceil(Fraction(n, 2**r)), [n // 2**r, n - 2**r, n // 2, n - r]),
    )

    add(
        "factorial_jump",
        319,
        3,
        ("קפיצה במספר האפסים של עצרת", "A jump in factorial trailing zeros"),
        (
            "במעבר מהעצרת של {prev} לעצרת של {n}, כמה אפסים חדשים מתווספים בסוף הכתיב העשרוני?",
            "Going from {prev} factorial to {n} factorial, how many new trailing zeros appear in decimal?",
        ),
        (
            "הגורם החדש במכפלה הוא {n}. בזוגות שיוצרים 10 יש עודף של גורמי 2, לכן סופרים כמה פעמים 5 מחלק את הגורם החדש. התוספת היא {answer}.",
            "The new factor is {n}. Factors of 2 are already plentiful for forming pairs that make 10. Count how many times 5 divides the new factor. The increase is {answer}.",
        ),
        (
            "מכפלה אחת יכולה להוסיף כמה אפסים כשיש בה כמה גורמים של 5.",
            "One new factor can add several zeros when it contains several factors of 5.",
        ),
        "prev n",
        [(24, 25), (124, 125), (29, 30), (48, 49), (49, 50)],
        lambda prev, n: (valuation(n, 5), [n // 5, 1, n % 5, 0, 3]),
    )

    add(
        "factorial_radix",
        319,
        4,
        ("אפסים בסוף העצרת בבסיס מורכב", "Trailing zeros in a composite base"),
        (
            "כותבים את {n}! בבסיס {base}. כמה אפסים מופיעים ברצף בסוף הייצוג?",
            "Write {n}! in base {base}. How many consecutive zeros appear at the end?",
        ),
        (
            "כל אפס דורש גורם שלם של {base} במכפלה. מפרקים את הבסיס לגורמים ראשוניים ובודקים כמה קבוצות מלאות אפשר להרכיב מתוך {n}!. מתקבלות {answer} קבוצות.",
            "Each trailing zero needs one complete factor of {base}. Factor the base into primes and count how many complete groups are available in {n}!. There are {answer} groups.",
        ),
        (
            "הגורם שמספיק למספר הקבוצות הקטן ביותר קובע את מספר האפסים.",
            "The limiting prime factor determines the number of trailing zeros.",
        ),
        "n base",
        [(8, 12), (10, 8), (7, 9), (11, 6), (5, 16)],
        lambda n, base: (
            valuation(math.factorial(n), base),
            [n // base, n // 2, n // 5, valuation(math.factorial(n), 2)],
        ),
    )

    add(
        "power_ratio",
        316,
        3,
        ("השוואה על ידי מעבר לבסיס משותף", "Comparing powers using a shared base"),
        (
            "ידוע כי A = {a}^{i} וכי B = {b}^{j}. שני הבסיסים הם חזקות של 2. מה המנה A/B המדויקת?",
            "Let A = {a}^{i} and B = {b}^{j}. Both bases are powers of 2. What is the exact ratio A/B?",
        ),
        (
            "ממירים את שני הביטויים לחזקות של 2. בחילוק מחסרים את המעריכים לאחר ההמרה. כך מתקבלת המנה {answer}.",
            "Rewrite both terms as powers of 2. Dividing subtracts their exponents after conversion. The resulting ratio is {answer}.",
        ),
        ("המרת בסיס קודמת לביצוע פעולות במעריכים.", "Convert to a common base before combining exponents."),
        "a i b j",
        [(8, 5, 4, 7), (4, 4, 16, 2), (2, 6, 4, 4), (16, 3, 8, 3), (4, 6, 8, 5)],
        lambda a, i, b, j: (
            Fraction(a**i, b**j),
            [Fraction(b**j, a**i), Fraction(a, b), Fraction(i, j), 1, 2],
        ),
    )

    add(
        "lockstep_coverage",
        315,
        3,
        ("כמה אתרים בדקו שני רובוטים?", "How many sites did two robots check?"),
        (
            "שני רובוטים מתחילים באתרים 0 ו־{gap} על ישר של שלמים. שניהם נעים {s} צעדים ימינה ובודקים גם את אתרי ההתחלה וגם כל אתר בדרך. כמה אתרים שונים נבדקו?",
            "Two robots start at sites 0 and {gap} on an integer line. Both move {s} steps right, checking their starts and every site they visit. How many distinct sites have been checked?",
        ),
        (
            "כל רובוט מבקר ב־{s} + 1 אתרים. סופרים את האיחוד של שני הקטעים, כך שאתרי חפיפה נספרים פעם אחת. מתקבלים {answer} אתרים.",
            "Each robot visits {s} + 1 sites. Take the union of their two intervals, counting any overlap once. This gives {answer} sites.",
        ),
        (
            "תנועה זהה משמרת את המרחק, אבל המסלולים עדיין עשויים לחפוף.",
            "Lockstep motion preserves separation, but visited paths can still overlap.",
        ),
        "gap s",
        [(3, 5), (5, 2), (1, 0), (4, 3), (2, 6)],
        lambda gap, s: (s + 1 + min(s + 1, gap), [2 * (s + 1), 2 * s, s + gap + 1, s + 1]),
    )

    add(
        "excursion_cost",
        315,
        3,
        ("הדרך חזרה בחיפוש בשני כיוונים", "Return travel in a two-sided search"),
        (
            "רובוט מתחיל ב־0. בכל גיחה שהסתיימה הוא חזר לנקודת ההתחלה. אורכי ההלוך בגיחות שהסתיימו הם {legs}. בגיחה הבאה הוא מוצא מטרה אחרי {last} צעדים ועוצר מיד. כמה צעדים צעד בסך הכול?",
            "A robot starts at 0 and returns to its start after each completed excursion. Outward lengths of completed excursions are {legs}. On the next excursion it finds its target after {last} steps and stops immediately. How many steps did it walk in total?",
        ),
        (
            "בגיחות שברשימה {legs} משלמים גם על החזרה. רק {last} הצעדים של הגיחה האחרונה נספרים פעם אחת. סך המרחק הוא {answer}.",
            "Each excursion in {legs} includes the return trip. Only the last {last} steps are paid once. Total travel is {answer}.",
        ),
        (
            "מרחק מההתחלה ואורך המסלול שבוצע הם גדלים שונים.",
            "Displacement from the start and total distance traveled are different quantities.",
        ),
        "legs last",
        [([1, 2, 4], 5), ([1], 2), ([], 1), ([2, 4], 7), ([1, 3], 4)],
        lambda legs, last: (
            2 * sum(legs) + last,
            [sum(legs) + last, 2 * (sum(legs) + last), max([last, *legs]), 2 * sum(legs)],
        ),
    )

    add(
        "clock_interval",
        330,
        3,
        ("כמה תצוגות שעון משתמשות בשתי ספרות לכל היותר?", "Clock displays with at most two digits"),
        (
            "שעון מציג שעות, דקות ושניות עם אפסים מובילים. בין {start} ל־{end}, כולל שני הקצוות, בכמה תצוגות מופיעות לכל היותר שתי ספרות שונות?",
            "A clock shows hours, minutes and seconds with leading zeros. Between {start} and {end}, including both endpoints, how many displays use at most two distinct digits?",
        ),
        (
            "בודקים כל שנייה בטווח, כולל הקצוות. שומרים את האפסים המובילים ומתעלמים מהנקודתיים. רק {answer} תצוגות עומדות בתנאי.",
            "Check each second in the inclusive interval, preserving leading zeros and ignoring colons. Exactly {answer} displays qualify.",
        ),
        (
            "ספרה שמופיעה כמה פעמים עדיין תופסת מקום אחד בקבוצת הספרות.",
            "Repeated occurrences of a digit still count as one distinct digit.",
        ),
        "start end",
        [
            ("11:11:08", "11:11:15"),
            ("12:21:19", "12:21:24"),
            ("00:00:00", "00:00:02"),
            ("08:59:59", "09:00:01"),
            ("23:33:20", "23:33:23"),
        ],
        lambda start, end: count_displays(start, end),
    )

    add(
        "clock_minutes",
        330,
        3,
        ("כמה ערכי דקות מותר להציג?", "How many minute fields are legal?"),
        (
            "בשעון שמציג שעות ודקות, השעה קבועה על {hour}. הספרות היחידות המותרות בכל התצוגה הן {a} ו־{b}. כמה ערכי דקות תקינים אפשר להציג בשעה זו?",
            "On a clock displaying hours and minutes, the hour is fixed at {hour}. The only digits allowed anywhere are {a} and {b}. How many valid minute fields can appear in that hour?",
        ),
        (
            "ספרת העשרות של הדקות חייבת להיות בין 0 ל־5. לספרת היחידות מותרת כל אחת משתי הספרות. כפל מספר האפשרויות לכל מקום נותן {answer}.",
            "The minute tens digit must lie between 0 and 5. Either allowed digit may occupy the units place. Multiplying the choices at the two positions gives {answer}.",
        ),
        (
            "בתצוגה עם שדות זמן, לתפקיד הספרה יש השפעה על הטווח שלה.",
            "A digit's position in a time field constrains its allowed range.",
        ),
        "hour a b",
        [("18", 1, 8), ("12", 1, 2), ("09", 0, 9), ("23", 2, 3), ("07", 0, 7)],
        lambda hour, a, b: (2 * ((a <= 5) + (b <= 5)), [1, 2, 3, 4, 6]),
    )

    add(
        "checkpoint_paths",
        300,
        3,
        ("מסלולים שחייבים לעבור בנקודה", "Paths through a required point"),
        (
            "יוצאים מ־(0,0) אל ({x},{y}) בצעדים של יחידה ימינה או למעלה. כמה מסלולים עוברים בנקודה ({a},{b})?",
            "Travel from (0,0) to ({x},{y}) using unit steps right or up. How many paths pass through ({a},{b})?",
        ),
        (
            "בוחרים את סדר הצעדים עד ({a},{b}) ואת סדרם ממנה אל ({x},{y}). כל בחירה בחלק הראשון מתחברת לכל בחירה בשני. מכפלת הספירות היא {answer}.",
            "Choose the order of steps to ({a},{b}), then the order from there to ({x},{y}). Any first segment can join any second segment. Multiplying their counts gives {answer}.",
        ),
        (
            "נקודת חובה מפרקת את המסלול לשני חלקים שאפשר לצרף בחופשיות.",
            "A required checkpoint splits a path into two freely combinable pieces.",
        ),
        "x y a b",
        [(3, 3, 1, 1), (4, 2, 2, 0), (2, 3, 0, 0), (4, 3, 2, 2), (3, 2, 3, 2)],
        lambda x, y, a, b: path_count_options(x, y, a, b, False),
    )

    add(
        "obstacle_paths",
        300,
        3,
        ("מסלולים שעוקפים נקודה חסומה", "Paths avoiding a blocked point"),
        (
            "ברשת אפשר לנוע יחידה ימינה או למעלה בלבד. כמה מסלולים מ־(0,0) אל ({x},{y}) נמנעים מהנקודה החסומה ({a},{b})?",
            "On a grid, each move goes one unit right or up. How many paths from (0,0) to ({x},{y}) avoid the blocked point ({a},{b})?",
        ),
        (
            "ממספר כל המסלולים מפחיתים את מספר המסלולים דרך ({a},{b}). כל מסלול כזה עובר בנקודה פעם אחת. נותרו {answer} מסלולים.",
            "Subtract the paths through ({a},{b}) from all paths. Such a path visits that point exactly once. This leaves {answer} paths.",
        ),
        (
            "קל לספור קבוצה באמצעות הסרת המקרים המשלימים.",
            "A complement count removes disallowed cases from the total.",
        ),
        "x y a b",
        [(3, 3, 1, 2), (3, 2, 2, 0), (2, 2, 1, 1), (4, 1, 0, 1), (2, 3, 2, 3)],
        lambda x, y, a, b: path_count_options(x, y, a, b, True),
    )

    add(
        "grid_clashes",
        353,
        3,
        ("חפיפה מותרת, שכנות קרובה אסורה", "Coincidence is legal but near neighbors conflict"),
        (
            "דגימות משני צבעים נמצאות על אותה שורה. מיקומי האדומות הם {red} ומיקומי הירוקות הם {green}. זוג בצבעים שונים נפסל רק כשהמרחק חיובי ולכל היותר 2. כמה זוגות נפסלים?",
            "Two colors of samples lie on one line. Red coordinates are {red} and green coordinates are {green}. An opposite-color pair is invalid only at positive distance at most 2. How many pairs are invalid?",
        ),
        (
            "עוברים על כל צירוף של נקודה אדומה וירוקה. הפרש מוחלט 1 או 2 פוסל אותו, והפרש אפס מותר. מספר הזוגות הפסולים הוא {answer}.",
            "For each red–green pair, an absolute difference of 1 or 2 disqualifies it. Zero difference is allowed. The count of invalid pairs is {answer}.",
        ),
        (
            "תנאי מרחק עם חריג באפס דורש לבדוק את שני גבולות הטווח.",
            "A distance bound with a zero exception requires checking both ends of its interval.",
        ),
        "red green",
        [([0, 4], [0, 2, 4]), ([3], [3]), ([1, 4], [6, 8]), ([0, 3, 6], [1, 4, 7]), ([2, 9], [5, 12])],
        lambda red, green: grid_conflicts(red, green),
    )

    add(
        "pyramid_pixels",
        354,
        3,
        ("מספר הפיקסלים בכל רמות הפירמידה", "Pixels across all pyramid levels"),
        (
            "תמונה בגודל {h} × {w} היא רמה 0. בכל אחת מ־{levels} ההקטנות שומרים את השורות והעמודות שמספריהן זוגיים, החל מאפס. כמה פיקסלים יש בכל הרמות יחד, כולל המקור?",
            "An image of size {h} × {w} forms level 0. The number of reductions is {levels}. Each reduction keeps even-indexed rows and columns starting at zero. How many pixels are there across all levels, including the original?",
        ),
        (
            "בכל צעד מחלקים כל ממד ב־2 ומעגלים מעלה. מסכמים גובה כפול רוחב בכל הרמות ומקבלים {answer} פיקסלים.",
            "Divide each dimension by 2, rounding upward at every step. Summing height times width over all levels gives {answer} pixels.",
        ),
        (
            "בתמונה עם ממד אי־זוגי חשוב לדעת מאיזה אינדקס הדגימה מתחילה.",
            "For an odd dimension, the sampling origin affects the output size.",
        ),
        "h w levels",
        [(5, 7, 2), (8, 4, 2), (1, 5, 2), (3, 3, 1), (7, 2, 0)],
        lambda h, w, levels: pixel_count(h, w, levels),
    )

    add(
        "drainage",
        355,
        4,
        ("לאיזה שקע מתנקזת שורת הגבהים?", "Which sites drain into one sink?"),
        (
            "גובהי האתרים בשורה הם {z}, עם אינדקסים מאפס. מים זורמים לשכן הנמוך ביותר רק אם הוא נמוך מהאתר עצמו. בשוויון בין שני שכנים נמוכים בוחרים בשמאלי. כמה אתרים, כולל השקע עצמו, מתנקזים לאינדקס {sink}?",
            "Sites on a line have heights {z}, indexed from zero. Water moves to the lowest neighbor only if it is strictly lower than the current site. Ties between two lower neighbors go left. How many sites, including the sink itself, drain to index {sink}?",
        ),
        (
            "עוקבים מכל אתר אחרי ירידות קפדניות עד לנקודת עצירה. בספירה של כל המסלולים שמסתיימים באינדקס {sink} מתקבלים {answer} אתרים.",
            "Follow strict descents from each site until a terminal point. Counting all paths ending at index {sink} gives {answer} sites.",
        ),
        (
            "אגן כולל גם אתרים שמגיעים לשקע דרך כמה אתרי ביניים.",
            "A basin includes sites that reach the sink through intermediate sites.",
        ),
        "z sink",
        [([1, 4, 3, 2, 0], 4), ([2, 4, 2], 0), ([7], 0), ([0, 1, 3, 2, 1], 4), ([5, 4, 3, 2, 1], 4)],
        lambda z, sink: drainage_size(z, sink),
    )

    add(
        "josephus_rotate",
        12,
        3,
        ("התחלה שונה במעגל ההדחות", "Changing the starting point in a circle"),
        (
            "במעגל יושבים {n} משתתפים ממוספרים 1 עד {n}. מתחילים לספור מהמשתתף שמספרו {s} כ־1, מדיחים כל משתתף שני וממשיכים מהבא אחריו. איזה מספר נשאר אחרון?",
            "A circle contains {n} participants labeled 1 through {n}. Count participant {s} as 1, eliminate every second participant, and resume at the next one. Which label survives?",
        ),
        (
            "מתחילים במעגל של משתתף יחיד עם אינדקס 0. כשמגדילים מעגל לגודל m, אינדקס השורד משתנה ל־(index + 2) mod m. בסוף מזיזים את תחילת המספור ל־{s}. השורד הוא {answer}.",
            "Start with survivor index 0 in a circle of one. Growing the circle to size m changes that index to (index + 2) mod m. Then rotate the origin to {s}. The surviving label is {answer}.",
        ),
        (
            "הזזת נקודת ההתחלה מסובבת את התוצאה באותו מרחק.",
            "Rotating the starting point rotates the result by the same offset.",
        ),
        "n s",
        [(7, 3), (8, 4), (5, 5), (6, 2), (9, 1)],
        lambda n, s: josephus(n, s),
    )

    add(
        "silence_worlds",
        343,
        4,
        ("כמה הרכבים עדיין אפשריים אחרי שתיקה?", "How many hidden sets remain after silence?"),
        (
            "ל־{n} משתתפים יש סימון גלוי לכל האחרים בלבד. הוכרז בפומבי שלפחות אחד מסומן. לפי כללי החידה, אם בדיוק j מסומנים, האות הראשון נשמע בסוף סיבוב j. חלפו {r} סיבובים שקטים. כמה קבוצות שונות של משתתפים מסומנים עדיין אפשריות לצופה שרק מאזין?",
            "At least one of {n} people is marked. Exactly j marked people will produce the first public signal in round j. After {r} silent rounds, how many different sets of marked people are still possible for a listener who sees no marks?",
        ),
        (
            "השתיקה שוללת כל קבוצה שגודלה לכל היותר {r}. מונים את תתי־הקבוצות של {n} המשתתפים הגדולות מכך. נותרות {answer} קבוצות.",
            "Silence rules out all sets of size at most {r}. Count the subsets of the {n} participants larger than that bound. There are {answer} possibilities.",
        ),
        (
            "מידע על מספר האנשים עדיין משאיר אי־ודאות לגבי זהותם.",
            "Information about a group size can leave its members' identities undetermined.",
        ),
        "n r",
        [(4, 2), (5, 3), (3, 1), (6, 5), (4, 0)],
        lambda n, r: (
            sum(math.comb(n, k) for k in range(r + 1, n + 1)),
            [2**n, n - r, math.comb(n, r), 2 ** (n - r)],
        ),
    )

    add(
        "digit_chain",
        38,
        4,
        ("הספרה המשותפת מחברת זוגות", "An overlapping digit connects adjacent pairs"),
        (
            "בונים מחרוזת באורך {n} ספרות. כל זוג ספרות סמוכות חייב להופיע ברשימה {pairs}. אפס מותר בתחילת המחרוזת. כמה מחרוזות אפשר לבנות?",
            "Build a string of {n} digits. Every adjacent digit pair must belong to {pairs}. A leading zero is allowed. How many strings are possible?",
        ),
        (
            "שומרים לכל ספרה את מספר המחרוזות שמסתיימות בה. מוסיפים ספרה רק כשנוצר זוג מהרשימה, ומחברים את הספירות המגיעות לאותה סיומת. באורך {n} מתקבלות {answer} מחרוזות.",
            "Track how many strings end in each digit. Append a digit only along an allowed pair and add the counts arriving at the same ending. At length {n} the total is {answer}.",
        ),
        (
            "אי אפשר לבחור זוגות בנפרד מפני שהסוף של זוג אחד הוא ההתחלה של הבא.",
            "Pairs cannot be chosen independently because one ends where the next starts.",
        ),
        "n pairs",
        [
            (3, ["12", "21", "23"]),
            (4, ["01", "10"]),
            (3, ["12", "34"]),
            (4, ["11", "12", "21"]),
            (2, ["00", "09", "90", "99"]),
        ],
        lambda n, pairs: digit_walks(n, pairs),
    )

    add(
        "majority_error",
        369,
        4,
        ("מתי הכרעת הרוב שגויה?", "When is a majority decision wrong?"),
        (
            "שלושה מחשבים קוראים אותו ביט. כל אחד הופך את הביט באופן בלתי תלוי בהסתברות {p}. מה ההסתברות שהביט שמתקבל בהצבעת רוב שגוי?",
            "Three computers read the same bit. Each independently flips it with probability {p}. What is the probability that the majority vote is wrong?",
        ),
        (
            "רוב שגוי מתקבל כששניים טועים או כששלושתם טועים. אם p = {p}, מחברים 3 × p² × (1−p) ו־p³ ומקבלים {answer}.",
            "The majority is wrong with exactly two errors or three errors. For p = {p}, adding 3 × p² × (1−p) and p³ gives {answer}.",
        ),
        (
            "כדי לסכום הסתברויות יש לחלק את האירוע למקרים זרים.",
            "Split the event into disjoint cases before adding their probabilities.",
        ),
        "p",
        [("1/4",), ("1/3",), ("1/2",), ("1/10",), ("2/3",)],
        lambda p: vote_errors(Fraction(p), False),
    )

    add(
        "unanimous_error",
        369,
        4,
        ("עד כמה אפשר לסמוך על הסכמה מלאה?", "How reliable is unanimous agreement?"),
        (
            "כל אחד משלושה קוראים הופך ביט משותף באופן בלתי תלוי בהסתברות {p}. נמסר רק ששלושתם החזירו ביט זהה. מה ההסתברות שהביט שעליו הסכימו שגוי?",
            "Each of three readers independently flips a shared bit with probability {p}. You learn only that all three reported the same bit. What is the probability their agreed bit is wrong?",
        ),
        (
            "בהינתן הסכמה נשארים שני מקרים בלבד. משקל הטעות המשותפת הוא p³ ומשקל ההצלחה המשותפת הוא (1−p)³. עבור p = {p}, חלקה היחסי של הטעות הוא {answer}.",
            "Agreement leaves only two cases. All errors have weight p³ and all correct readings have weight (1−p)³. For p = {p}, the share due to error is {answer}.",
        ),
        (
            "ההסתברות לטעות אחרי תצפית מחושבת רק בתוך המקרים שמתאימים לה.",
            "After observing agreement, normalize over the cases consistent with it.",
        ),
        "p",
        [("1/3",), ("1/4",), ("2/5",), ("3/4",), ("1/2",)],
        lambda p: vote_errors(Fraction(p), True),
    )

    add(
        "repeat_coverage",
        370,
        4,
        ("לכסות כל ערוץ פעמיים", "Covering every channel more than once"),
        (
            "יש {n} ערוצי מדידה. בסבב בודקים לכל היותר {k} ערוצים שונים. כל ערוץ חייב להיבדק ב־{r} סבבים שונים. מהו מספר הסבבים המזערי?",
            "There are {n} measurement channels. Each round can test at most {k} distinct channels. Every channel must be tested in {r} distinct rounds. What is the minimum number of rounds?",
        ),
        (
            "נדרשות {n} × {r} בדיקות. חוזרים ברצף על רשימת הערוצים ומחלקים אותה לקבוצות של עד {k}. ערוץ אינו מופיע פעמיים בקבוצה, והחלוקה משיגה את החסם של {answer} סבבים.",
            "There are {n} × {r} required tests. Repeat the channel list and cut it into groups of at most {k}. No group repeats a channel, attaining the bound of {answer} rounds.",
        ),
        (
            "חסם לפי קיבולת הופך לתשובה מדויקת רק אחרי שמציגים שיבוץ חוקי.",
            "A capacity bound becomes exact once a legal schedule achieves it.",
        ),
        "n k r",
        [(5, 3, 2), (6, 3, 2), (7, 7, 3), (4, 1, 2), (7, 4, 3)],
        lambda n, k, r: (
            math.ceil(Fraction(n * r, k)),
            [r * math.ceil(Fraction(n, k)), n * r // k, n * r, r],
        ),
    )

    add(
        "pyramid_indent",
        347,
        2,
        ("כמה רווחים נדרשים למרכוז הפירמידה?", "How much indentation centers the pyramid?"),
        (
            "לפירמידת כוכביות ממורכזת יש בסיס ברוחב {w}. רוחבי השורות הם 1, 3 וכן הלאה, עד לרוחב הבסיס {w}. כמה רווחים מובילים יודפסו בכל השורות יחד? אין רווחים מימין.",
            "A centered star pyramid has an odd base width of {w}. Rows have widths 1, 3 and so on up to {w}. How many leading spaces are printed across all rows? There is no right padding.",
        ),
        (
            "בשורה הראשונה יש ({w}−1)/2 רווחים, ובכל שורה הבאה רווח אחד פחות. סכום המספרים עד אפס הוא {answer}.",
            "The first row has ({w}−1)/2 leading spaces; each subsequent row has one fewer. Summing down to zero gives {answer}.",
        ),
        (
            "הרחבה בשתי כוכביות מפחיתה רווח אחד בכל צד של המרכז.",
            "Two extra stars reduce the indentation by one on either side of the center.",
        ),
        "w",
        [(7,), (1,), (5,), (11,), (9,)],
        lambda w: (sum(range((w + 1) // 2)), [((w + 1) // 2) ** 2, (w - 1) // 2, w, (w * w - 1) // 4]),
    )

    add(
        "cube_layers",
        290,
        4,
        ("ספירת קשתות בין שכבות של קובייה", "Counting edges between cube layers"),
        (
            "קודקודי קובייה ב־{d} ממדים הם מחרוזות של {d} ביטים. שכנים נבדלים בביט אחד. כמה קשתות מחברות את שכבת המחרוזות עם {k} אחדות לשכבה שבה יש אחד נוסף?",
            "Vertices of a {d}-dimensional cube are strings of {d} bits. Neighbors differ in one bit. How many edges join the layer with {k} ones to the layer with one additional one?",
        ),
        (
            "בוחרים מיקומים ל־{k} אחדות בקודקוד הראשון ואז בוחרים אחד מהאפסים להפוך. לכל קשת יש התחלה יחידה בשכבה הנמוכה. מתקבלות {answer} קשתות.",
            "Choose positions for {k} ones at the lower vertex, then select one zero to flip. Each edge has a unique lower endpoint. This counts {answer} edges.",
        ),
        (
            "כיוון השינוי מונע ספירה כפולה של קשתות בין שתי שכבות.",
            "Orienting the change avoids double-counting edges between layers.",
        ),
        "d k",
        [(3, 1), (4, 0), (4, 2), (5, 4), (5, 2)],
        lambda d, k: (
            math.comb(d, k) * (d - k),
            [math.comb(d, k), math.comb(d, k + 1), 2**d, d * 2 ** (d - 1)],
        ),
    )

    add(
        "expression_slots",
        164,
        3,
        ("כמה דרכים לבחור חיבורים וסימנים?", "Counting gaps and operator choices"),
        (
            "בין {n} ספרות נתונות אפשר להשאיר את הרווח ריק כדי לשרשר אותן או להכניס פלוס או מינוס. רוצים ביטוי עם בדיוק {groups} מספרים. כמה בחירות שונות של מיקומים וסימנים קיימות? אין סימן לפני הספרה הראשונה.",
            "Between {n} given digits, each gap may be left empty for concatenation or filled with plus or minus. Form exactly {groups} numbers. How many distinct placements and signs are possible? There is no leading sign.",
        ),
        (
            "בוחרים את המקומות שמפרידים בין {groups} המספרים מתוך הרווחים שבין הספרות. לכל מקום שנבחר יש שני סימנים אפשריים. בסך הכול יש {answer} בחירות.",
            "Choose the gaps separating the {groups} numbers from the gaps between digits. Each selected gap has two sign choices. This gives {answer} placements with signs.",
        ),
        (
            "ספירת ביטויים כתובים שונה מספירת ערכים מספריים שונים.",
            "Counting written expressions differs from counting distinct numerical values.",
        ),
        "n groups",
        [(5, 3), (6, 1), (4, 4), (6, 2), (7, 4)],
        lambda n, groups: (
            math.comb(n - 1, groups - 1) * 2 ** (groups - 1),
            [
                math.comb(n - 1, groups - 1),
                2 ** (n - 1),
                math.comb(n, groups) * 2 ** (groups - 1),
                3 ** (n - 1),
            ],
        ),
    )

    add(
        "parking_prefix",
        356,
        3,
        ("מהי התפוסה ההתחלתית המזערית?", "Minimum initial occupancy from an event log"),
        (
            "ברשומת חניון כל 1 הוא כניסה וכל −1 הוא יציאה. סדר האירועים הוא {events}. מהו מספר המכוניות המזערי שחייב להיות בחניון לפני האירוע הראשון כדי שהתפוסה לעולם לא תרד מתחת לאפס? יש די מקומות חנייה.",
            "In a parking log, 1 means an arrival and −1 a departure. The events in order are {events}. What is the smallest number of cars the lot could start with while keeping occupancy nonnegative after every event? Capacity is ample.",
        ),
        (
            "סוכמים את האירועים מתחילת הרשומה ועד כל נקודה בה. התפוסה ההתחלתית צריכה לכסות את החוסר הגדול ביותר שנוצר בדרך. דרושות {answer} מכוניות.",
            "Sum the events from the start to each point in the log. Initial occupancy must cover the largest deficit anywhere along the way. This requires {answer} cars.",
        ),
        (
            "מאזן סופי אינו בודק אם יציאה מוקדמת הייתה אפשרית.",
            "The final balance alone cannot show whether an earlier departure was possible.",
        ),
        "events",
        [([-1, -1, 1, 1],), ([1, -1, -1],), ([1, 1, -1],), ([-1, 1, -1, -1, -1],), ([],)],
        lambda events: (
            -min(itertools.accumulate(events, initial=0)),
            [
                max(0, -sum(events)),
                events.count(-1),
                len(events),
                max(itertools.accumulate(events, initial=0)),
            ],
        ),
    )

    add(
        "sampling_overlap",
        353,
        3,
        ("שתי רשתות דגימה על אותה שורה", "Two sampling grids on the same row"),
        (
            "על שורת פיקסלים, דוגם אחד שומר כל כפולה של {a} ודוגם שני כל כפולה של {b}, החל מאפס. כמה מיקומים משותפים יש בתחום האינדקסים מ־{lo} עד {hi}, כולל הקצוות?",
            "On a pixel row, one sampler keeps every multiple of {a} and another every multiple of {b}, starting at zero. How many positions do they share from index {lo} through {hi}, inclusive?",
        ),
        (
            "הדוגמים נפגשים בכפולות של הכפולה המשותפת המזערית של {a} ו־{b}. סופרים רק את הכפולות שבטווח הסגור. מתקבלים {answer} מיקומים.",
            "The samplers coincide at multiples of the least common multiple of {a} and {b}. Count those in the closed interval. This gives {answer} positions.",
        ),
        (
            "בנוסף למחזור המשותף צריך לבדוק מי מהקצוות נכלל בספירה.",
            "Alongside the common period, check which interval endpoints are included.",
        ),
        "a b lo hi",
        [(3, 4, 0, 25), (2, 4, 1, 11), (4, 6, 1, 10), (5, 5, 5, 15), (2, 3, 6, 6)],
        lambda a, b, lo, hi: overlap_counts(a, b, lo, hi),
    )

    return cards, rows, checks


def valuation(n, base):
    count = 0
    while n % base == 0:
        n //= base
        count += 1
    return count


def count_displays(start, end):
    def time_in_seconds(text):
        h, m, s = map(int, text.split(":"))
        return h * 3600 + m * 60 + s

    words = [
        f"{t // 3600:02d}{t // 60 % 60:02d}{t % 60:02d}"
        for t in range(time_in_seconds(start), time_in_seconds(end) + 1)
    ]
    good = sum(len(set(word)) <= 2 for word in words)
    return good, [sum(len(set(word)) == 2 for word in words), len(words), len(words) - 1, len(words) - good]


def path_count_options(x, y, a, b, avoid):
    total = math.comb(x + y, x)
    left = math.comb(a + b, a)
    right = math.comb(x - a + y - b, x - a)
    via = left * right
    return (total - via if avoid else via), [total, via, total - via, left + right, left, right]


def grid_conflicts(red, green):
    distances = [abs(r - g) for r in red for g in green]
    return sum(0 < d <= 2 for d in distances), [
        sum(d <= 2 for d in distances),
        distances.count(2),
        distances.count(1),
        len(distances),
    ]


def pixel_count(h, w, levels):
    base = h * w
    total = base
    for _ in range(levels):
        h = (h + 1) // 2
        w = (w + 1) // 2
        total += h * w
    return total, [total - base, h * w, base, total - h * w]


def drainage_size(z, sink):
    def destination(i):
        candidates = [j for j in (i - 1, i + 1) if 0 <= j < len(z) and z[j] < z[i]]
        return destination(min(candidates, key=lambda j: (z[j], j))) if candidates else i

    basins = [destination(i) for i in range(len(z))]
    return basins.count(sink), [len(set(basins)), len(z), len(z) - basins.count(sink), z[sink], 1]


def josephus(n, s):
    idx = 0
    for m in range(2, n + 1):
        idx = (idx + 2) % m
    return (idx + s - 1) % n + 1, [idx + 1, (idx + s) % n + 1, n, s, 1]


def digit_walks(n, pairs):
    old = [1] * 10
    for _ in range(n - 1):
        new = [0] * 10
        for ab in pairs:
            new[int(ab[1])] += old[int(ab[0])]
        old = new
    return sum(old), [len(pairs) ** (n - 1), len(pairs), sum(x > 0 for x in old), n * len(pairs)]


def vote_errors(p, unanimous):
    all_wrong = p**3
    two_wrong = 3 * p**2 * (1 - p)
    majority_wrong = all_wrong + two_wrong
    given_agreement = all_wrong / (all_wrong + (1 - p) ** 3)
    return (given_agreement if unanimous else majority_wrong), [
        p,
        all_wrong,
        two_wrong,
        1 - p,
        given_agreement,
        majority_wrong,
        0,
        1,
    ]


def overlap_counts(a, b, lo, hi):
    period = math.lcm(a, b)
    common = hi // period - (lo - 1) // period
    return common, [
        hi // period,
        hi // max(a, b) - (lo - 1) // max(a, b),
        hi // (a * b) - (lo - 1) // (a * b),
        hi - lo + 1,
    ]


def build():
    _, rows, checks = build_bundle()
    return rows, checks


if __name__ == "__main__":
    cards, rows, checks = build_bundle()
    for path, value in [
        (CONTENT, cards),
        (OUT / "reasoning_800.json", rows),
        (OUT / "reasoning_800.checks.json", checks),
    ]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Wrote {len(cards)} reasoning cards and {len(rows)} game variants")
