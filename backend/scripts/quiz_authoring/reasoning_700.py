"""70 original interview-linked short cards and 350 draft bilingual variants.

The public schema is unchanged. Editorial difficulty and provenance live only in
the private checks file. Python finite-model validation is not expert review.
"""

from __future__ import annotations

import itertools as it
import json
import math
from collections import Counter
from datetime import date
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content/fundamentals-reasoning-700.json"
OUT = ROOT / "backend/seeds/duel_quiz_batches"


def subsets(values):
    return [
        tuple(v for v, take in zip(values, mask, strict=True) if take)
        for mask in it.product((0, 1), repeat=len(values))
    ]


def sums(values):
    return {sum(part) for part in subsets(values)}


def first_gap(values):
    available = sums(values)
    return next(x for x in range(1, sum(values) + 2) if x not in available)


def normal(data):
    return {key: str(value) if isinstance(value, F) else value for key, value in data.items()}


def build_bundle():
    cards, rows, checks = [], [], []

    def add(
        task,
        refs,
        title,
        prompt,
        explanation,
        takeaway,
        fields,
        cases,
        solve,
        difficulty=3,
        probability=False,
    ):
        number = 251 + len(cards)
        assert len(cases) == 5
        local = []
        for variant, values in enumerate(cases, 1):
            data = normal(dict(zip(fields.split(), values, strict=True)))
            good = F(solve(data))
            candidates = (
                [F(0), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(3, 16)]
                if task == "factory_covariance"
                else [F(0), F(1), F(1, 2), F(1, 3), F(2, 3), F(1, 4), F(3, 4)]
                if probability
                else [good + 1, max(F(0), good - 1), good + 2, F(0), good * 2, good + 3]
            )
            options = [str(good), *[str(x) for x in dict.fromkeys(candidates) if x != good][:3]]
            assert len(options) == len(set(options)) == 4
            shift = (number + variant) % 4
            options = options[-shift:] + options[:-shift] if shift else options
            row = dict(
                key=f"quick-sw-{number}-v{variant}",
                source_key=f"quick-sw-{number}",
                variant=variant,
                topic="reasoning",
                status="draft",
                prompt={lg: text.format(**data) for lg, text in zip(("he", "en"), prompt, strict=True)},
                choices=[dict(he=x, en=x) for x in options],
                correct=shift,
                explanation=dict(zip(("he", "en"), explanation, strict=True)),
            )
            rows.append(row)
            local.append(row)
            checks.append(
                dict(
                    key=row["key"],
                    task=task,
                    inputs=data,
                    options=options,
                    expected=str(good),
                    method="Independent input-derived finite model or exact algebra; see test_fundamentals_reasoning_700.py",
                    professional_review="pending",
                    authorship="AI-assisted original principle exercise",
                    interviewIds=[f"PREP-{x:03d}" for x in refs],
                    source_relation="Original scenario teaching a principle of the linked interview; not a reported interview variant",
                    difficulty=difficulty,
                    difficulty_rationale=explanation[1],
                    source_difficulty=difficulty,
                    source_difficulty_rationale=explanation[1],
                )
            )
        first = local[0]
        cards.append(
            dict(
                id=first["source_key"],
                topic="reasoning",
                interviewIds=[f"PREP-{x:03d}" for x in refs],
                title=dict(zip(("he", "en"), title, strict=True)),
                prompt=first["prompt"],
                answer={
                    lg: first["choices"][first["correct"]][lg] + ". " + first["explanation"][lg]
                    for lg in ("he", "en")
                },
                takeaway=dict(zip(("he", "en"), takeaway, strict=True)),
            )
        )

    add(
        "coin_min",
        [271],
        ("המלאי קובע את התשלום", "Inventory determines exact payment"),
        (
            "המטבעות הזמינים הם {coins}; כל איבר הוא מטבע נפרד לשימוש יחיד. מה מספר המטבעות המזערי לתשלום מדויק {target}? החזירו −1 אם בלתי אפשרי.",
            "Available coins are {coins}; each entry is one distinct, single-use coin. What is the fewest coins paying exactly {target}? Return −1 if impossible.",
        ),
        (
            "בודקים תת־קבוצות של מטבעות פיזיים. ערכים שווים אינם אותו מטבע; יעד אפס דורש אפס מטבעות.",
            "Consider subsets of physical coins. Equal values are distinct inventory items; a zero target needs zero coins.",
        ),
        (
            "מינימום תלוי גם במלאי, לא רק בערכי המטבעות.",
            "A minimum depends on inventory as well as denominations.",
        ),
        "coins target",
        [([1, 3, 4, 4], 8), ([2, 3, 6], 7), ([2, 2, 5], 4), ([3, 5], 0), ([1, 2, 4], 7)],
        lambda d: min((len(p) for p in subsets(d["coins"]) if sum(p) == d["target"]), default=-1),
    )

    add(
        "coin_ways",
        [271],
        ("ערך זהה אינו בחירה זהה", "Equal values are distinct selections"),
        (
            "מטבעות ממוספרים שערכיהם {coins}, לשימוש יחיד, משלמים יעד {target}. כמה תת־קבוצות אינדקסים משלמות בדיוק? סדר התשלום אינו משנה.",
            "Indexed single-use coins have values {coins}, with target {target}. How many index subsets pay exactly? Payment order does not matter.",
        ),
        (
            "מונים קבוצות אינדקסים ולא רצפי בחירה. שני עותקים שווי ערך עשויים ליצור פתרונות נפרדים.",
            "Count index subsets, not selection orders. Equal-valued copies can create distinct solutions.",
        ),
        (
            "זהות הפריטים ומושג הסדר קובעים מה סופרים.",
            "Item identity and order conventions determine what is counted.",
        ),
        "coins target",
        [([1, 1, 2], 2), ([2, 2, 2], 4), ([1, 3, 4], 5), ([4, 4], 0), ([1, 2, 3, 3], 6)],
        lambda d: sum(sum(p) == d["target"] for p in subsets(d["coins"])),
    )

    add(
        "coverage_gap",
        [251],
        ("המסה הראשונה שאי אפשר להרכיב", "The first unrepresentable mass"),
        (
            "המשקולות {weights} זמינות פעם אחת כל אחת. מותר רק לחבר תת־קבוצה, בלי חיסור. מה המסה השלמה החיובית הקטנה ביותר שלא ניתן ליצור?",
            "Weights {weights} are each available once. Only subset addition is allowed, without subtraction. What is the smallest positive integer mass that cannot be formed?",
        ),
        (
            "עוברים בסדר עולה ושומרים טווח רציף מ־0. משקולת הגדולה מהטווח ועוד 1 משאירה חור שאחרות גדולות ממנה לא יתקנו.",
            "Scan sorted weights while maintaining coverage from 0. A weight exceeding the covered endpoint plus 1 leaves a gap that later weights cannot repair.",
        ),
        (
            "כיסוי רציף דורש לבדוק את המסה החסרה הראשונה.",
            "Continuous coverage requires checking the first missing mass.",
        ),
        "weights",
        [([1, 2, 5],), ([2, 3],), ([1, 1, 3],), ([1, 2, 4],), ([1, 3, 3],)],
        lambda d: first_gap(d["weights"]),
    )

    add(
        "lost_weight",
        [251],
        ("יתירות מגינה מפני משקולת שאבדה", "Redundancy protects against a lost weight"),
        (
            "משקולות חד־פעמיות {weights}. יריב מסיר בדיוק משקולת אחת לפני שקילה בחיבור בלבד. מה K הגדול ביותר כך שכל מסה 0..K ניתנת להרכבה בכל הסרה?",
            "Single-use weights are {weights}. An adversary removes exactly one before addition-only weighing. What is the largest K such that every mass 0..K remains representable after every removal?",
        ),
        (
            "מחשבים את סוף הכיסוי הרציף לכל הסרה, ואז לוקחים את המינימום. סכום גדול לבדו אינו מבטיח כיסוי.",
            "Compute the contiguous covered endpoint after each removal, then take the minimum. A large total alone does not guarantee coverage.",
        ),
        (
            "הבטחה מול תקלה נקבעת במקרה ההסרה הגרוע ביותר.",
            "A fault guarantee is determined by the worst removal.",
        ),
        "weights",
        [([1, 1, 2, 4],), ([1, 2, 4],), ([1, 1, 1],), ([1, 1, 2, 2],), ([1],)],
        lambda d: min(
            first_gap(d["weights"][:i] + d["weights"][i + 1 :]) - 1 for i in range(len(d["weights"]))
        ),
        4,
    )

    add(
        "extend_coverage",
        [251],
        ("המשקולת הבאה צריכה לסגור את הפער", "The next weight must bridge the gap"),
        (
            "המשקולות הקיימות מכסות בדיוק את כל המסות השלמות 0..{covered}. מוסיפים משקולת חיובית אחת W לשימוש יחיד. מה W הגדול ביותר שמשאיר את הכיסוי עד {covered}+W ללא חורים?",
            "Existing weights cover exactly all integer masses 0..{covered}. Add one positive single-use weight W. What is the largest W keeping coverage through {covered}+W gap-free?",
        ),
        (
            "הטווח החדש הוא W..W+R והישן 0..R. כדי שייגעו או יחפפו דרוש W≤R+1; השוויון נותן את ההרחבה הגדולה ביותר.",
            "The new interval is W..W+R and the old one 0..R. They touch or overlap exactly when W≤R+1; equality maximizes the extension.",
        ),
        (
            "חיבור טווחי אפשרויות מצריך חפיפה או סמיכות.",
            "Combining possibility intervals requires overlap or adjacency.",
        ),
        "covered",
        [(3,), (0,), (1,), (7,), (10,)],
        lambda d: d["covered"] + 1,
        2,
    )

    add(
        "weight_bound",
        [251],
        ("מספר אפשרויות נותן חסם למשקולות", "Subset capacity bounds the weight count"),
        (
            "בוחרים משקולות שלמות חיוביות, עותק יחיד מכל משקולת, בחיבור בלבד. מה המספר המזערי שמאפשר ליצור כל מסה 1..{target}? מותר שהסכום הכולל יהיה גדול מהיעד.",
            "Choose positive integer weights, each usable once, with addition only. What is the minimum count representing every mass 1..{target}? Their total may exceed the target.",
        ),
        (
            "עם k משקולות יש לכל היותר 2^k תת־קבוצות, כולל הריקה. חזקות של 2 משיגות את החסם בכיסוי רציף.",
            "With k weights there are at most 2^k subsets, including the empty one. Powers of 2 attain this bound with contiguous coverage.",
        ),
        ("חסם ספירה צריך גם בנייה שמשיגה אותו.", "A counting bound also needs a matching construction."),
        "target",
        [(10,), (1,), (7,), (8,), (40,)],
        lambda d: d["target"].bit_length(),
    )

    add(
        "signed_weights",
        [251, 298],
        ("חיסור משנה את המסות האפשריות", "Subtraction changes attainable masses"),
        (
            "לכל משקולת ב־{weights} מותר מקדם −1,0,+1, כי אפשר לשים אותה בכל אחת משתי כפות המאזניים. כמה מסות חיוביות שונות ניתן ליצור?",
            "Each weight in {weights} may receive coefficient −1,0,+1 by using either balance pan. How many distinct positive masses can be formed?",
        ),
        (
            "מחשבים סכומים חתומים ומאחדים תוצאות זהות. 3^k הוא מספר הקצאות, ולא בהכרח מספר המסות השונות.",
            "Form signed sums and merge equal results. 3^k counts assignments, not necessarily distinct masses.",
        ),
        (
            "אפשרויות פעולה שונות עשויות להוביל לאותה תוצאה.",
            "Different action choices may produce the same result.",
        ),
        "weights",
        [([1, 3],), ([1, 1],), ([2, 6],), ([1, 3, 9],), ([2, 3],)],
        lambda d: (
            len(
                {
                    sum(x * y for x, y in zip(d["weights"], c, strict=True))
                    for c in it.product((-1, 0, 1), repeat=len(d["weights"]))
                }
                - {0}
            )
            // 2
        ),
    )

    add(
        "gold_cuts",
        [298],
        ("תשלום מצטבר מאפשר החלפת חתיכות", "Cumulative payment permits exchanging pieces"),
        (
            "מוט זהב שווה {days} ימי שכר. כל חיתוך מפצל חתיכה אחת לשתיים; ניתן לקבל חתיכות חזרה כעודף. כמה חיתוכים לפחות מאפשרים לעובד להחזיק בדיוק d יחידות בסוף כל יום d=1..{days}?",
            "A gold bar equals {days} daily wages. Each cut splits one piece into two; pieces may be returned as change. What is the fewest cuts allowing the worker to hold exactly d units after every day d=1..{days}?",
        ),
        (
            "k חתיכות נותנות לכל היותר 2^k יתרות. בוחרים חתיכות המכסות ברצף עד מלוא המוט; יצירת k חתיכות דורשת k−1 חיתוכים.",
            "k pieces allow at most 2^k balances. Choose pieces covering continuously through the whole bar; making k pieces requires k−1 cuts.",
        ),
        ("מספר חתיכות ומספר חיתוכים נבדלים באחד.", "The piece count and cut count differ by one."),
        "days",
        [(7,), (1,), (3,), (4,), (10,)],
        lambda d: d["days"].bit_length() - 1,
    )

    add(
        "gold_exchange",
        [298],
        ("שינוי היתרה אינו מספר ההעברות", "Balance change is not transfer count"),
        (
            "חתיכות הזהב הן 1,2,4,...,2^{power}. העובד מחזיק כרגע {before} יחידות וצריך להחזיק {after}. משתמשים בייצוג הבינארי היחיד בכל יתרה. כמה חתיכות עוברות בין הצדדים, בשני הכיוונים יחד?",
            "Gold pieces are 1,2,4,...,2^{power}. The worker holds {before} units and must hold {after}. Use the unique binary representation of each balance. How many pieces change owner, counting both directions?",
        ),
        (
            "כל ביט ששונה מציין חתיכה שעוברת בעלות. חתיכות שמוחזקות בשתי היתרות אינן צריכות לזוז.",
            "Each differing bit represents a piece changing owner. Pieces present in both balances need not move.",
        ),
        ("עלות העדכון תלויה בהבדל בין המצבים.", "Update cost depends on the difference between states."),
        "power before after",
        [(2, 3, 4), (2, 0, 1), (3, 7, 8), (2, 5, 6), (2, 4, 4)],
        lambda d: (d["before"] ^ d["after"]).bit_count(),
        2,
    )

    add(
        "gold_no_change",
        [298],
        ("איסור החזרה משנה את דרישת החיתוך", "Forbidding change changes the cutting requirement"),
        (
            "מוט זהב שווה {days} ימי שכר. חייבים להעביר שכר של יחידה אחת מדי יום, ואסור לקבל חתיכות חזרה או לחתוך אצל העובד. כמה חיתוכים במוט נחוצים מראש? כל חיתוך מפצל חתיכה אחת.",
            "A gold bar equals {days} daily wages. Transfer exactly one unit daily; returned pieces and cutting the worker's pieces are forbidden. How many initial cuts are necessary? Each cut splits one piece.",
        ),
        (
            "ללא עודף צריך חתיכה של יחידה לכל יום. D חתיכות נוצרות ב־D−1 חיתוכים.",
            "Without change, each day requires its own unit piece. D pieces require D−1 cuts.",
        ),
        ("היתר להחליף משאבים הוא חלק מהבעיה.", "Permission to exchange resources is part of the problem."),
        "days",
        [(7,), (1,), (2,), (4,), (10,)],
        lambda d: d["days"] - 1,
        2,
    )

    quality = [
        ("1/2", "3/4", "1/4"),
        ("1/2", "1/2", "1/2"),
        ("1/3", "1", "1/2"),
        ("3/4", "1/3", "0"),
        ("1/4", "0", "1"),
    ]

    def posterior(d, successes, failures):
        a = F(d["prior"]) * F(d["a"]) ** successes * (1 - F(d["a"])) ** failures
        b = (1 - F(d["prior"])) * F(d["b"]) ** successes * (1 - F(d["b"])) ** failures
        return a / (a + b)

    add(
        "factory_posterior",
        [308, 159],
        ("בדיקה לא מושלמת משנה את משקל הראיה", "An imperfect test changes the evidence weight"),
        (
            "P(A)={prior}; שיעורי תקינות במפעלים A,B הם {a},{b}. בדיקה חיובית בהסתברות {sensitivity} לפריט תקין ו־{false_positive} לפגום. פריט נבדק חיובי. מה P(A|חיובי)?",
            "P(A)={prior}; good rates at factories A,B are {a},{b}. A test is positive with probability {sensitivity} on good chips and {false_positive} on bad chips. A chip tests positive. What is P(A|positive)?",
        ),
        (
            "לכל מפעל מחברים את מסלולי החיובי האמיתי וחיובי השווא. מכפילים במשקל המוקדם ומנרמלים; תוצאה חיובית אינה הוכחה לתקינות.",
            "For each factory add true-positive and false-positive paths. Multiply by the prior and normalize; a positive result does not prove the chip is good.",
        ),
        ("איכות המדידה היא חלק ממודל הראיה.", "Measurement quality is part of the evidence model."),
        "prior a b sensitivity false_positive",
        [
            ("1/2", "3/4", "1/4", "1", "1/4"),
            ("1/2", "3/4", "1/4", "1/2", "1/2"),
            ("1/3", "1", "1/2", "1", "0"),
            ("3/4", "1/3", "0", "1/2", "1/4"),
            ("1/4", "0", "1", "1/2", "0"),
        ],
        lambda d: (lambda wa, wb: wa / (wa + wb))(
            F(d["prior"]) * (F(d["a"]) * F(d["sensitivity"]) + (1 - F(d["a"])) * F(d["false_positive"])),
            (1 - F(d["prior"]))
            * (F(d["b"]) * F(d["sensitivity"]) + (1 - F(d["b"])) * F(d["false_positive"])),
        ),
        4,
        True,
    )

    add(
        "factory_predict",
        [308],
        ("הפריט הבא חולק את המקור", "The next item shares the source"),
        (
            "P(A)={prior}; תקינות היא {a} במפעל A ו־{b} ב־B. שני פריטים באותה קופסה עצמאיים בהינתן המפעל. הראשון תקין. מה הסיכוי שהשני תקין?",
            "P(A)={prior}; good rates are {a} at A and {b} at B. Two chips in one box are independent conditional on the factory. The first is good. What is the second chip's good probability?",
        ),
        (
            "מעדכנים את משקל המפעל בעקבות התוצאה הראשונה, ואז משקללים לפיו את סיכוי התקינות של הפריט הבא.",
            "Update the factory weight after the first result, then average the next chip's good rate using that posterior.",
        ),
        (
            "עצמאות מותנית אינה עצמאות לאחר הסתרת המקור.",
            "Conditional independence is not independence when the source is hidden.",
        ),
        "prior a b",
        quality,
        lambda d: posterior(d, 1, 0) * F(d["a"]) + (1 - posterior(d, 1, 0)) * F(d["b"]),
        4,
        True,
    )

    add(
        "factory_mixed",
        [308],
        ("כישלון והצלחה מעדכנים יחד", "Success and failure update together"),
        (
            "P(A)={prior}, ותקינות במפעלים A,B היא {a},{b}. באותה קופסה נצפו {good} תקינים ואחריהם {bad} פגומים. הפריטים עצמאיים בהינתן המפעל. מה ההסתברות המעודכנת ל־A?",
            "P(A)={prior}, and good rates at A,B are {a},{b}. In one box, the observed sequence is {good}×good then {bad}×bad. Chips are independent given the factory. What is the updated probability of A?",
        ),
        (
            "מכפילים עבור כל מפעל את גורמי ההצלחה והכישלון ואת המשקל המוקדם, ואז מנרמלים. כישלון עשוי להפוך את כיוון העדכון.",
            "Multiply each factory's success factors, failure factors and prior, then normalize. Failure can reverse the direction of the update.",
        ),
        (
            "כל תצפית נבחנת לפי הסבירות שלה בכל השערה.",
            "Evaluate each observation's likelihood under every hypothesis.",
        ),
        "prior a b good bad",
        [
            ("1/2", "3/4", "1/4", 1, 1),
            ("1/2", "3/4", "1/4", 2, 1),
            ("1/3", "1/2", "1/4", 0, 2),
            ("1/2", "1", "1/2", 1, 1),
            ("3/4", "1/2", "1/2", 2, 2),
        ],
        lambda d: posterior(d, d["good"], d["bad"]),
        4,
        True,
    )

    add(
        "factory_covariance",
        [308],
        ("מקור משותף יוצר תלות", "A common source creates dependence"),
        (
            "P(A)={prior}; שיעורי תקינות A,B הם {a},{b}. X,Y מציינים תקינות שני פריטים מאותה קופסה, עצמאיים בהינתן המפעל. מה Cov(X,Y)=E[XY]−E[X]E[Y]?",
            "P(A)={prior}; good rates at A,B are {a},{b}. X,Y indicate two chips' quality in one box, independent given the factory. What is Cov(X,Y)=E[XY]−E[X]E[Y]?",
        ),
        (
            "המקור המשותף נותן שונות בין שיעורי התקינות. הקווריאנציה היא q(1−q)(a−b)^2, ולכן נעלמת כשהשיעורים שווים או שהמקור ודאי.",
            "The shared source contributes variation between good rates. Covariance is q(1−q)(a−b)^2, vanishing for equal rates or a certain source.",
        ),
        (
            "שונות במקור נסתר יכולה להסביר תלות בין מדידות.",
            "Variation in a hidden source can explain dependence between measurements.",
        ),
        "prior a b",
        [
            ("1/2", "3/4", "1/4"),
            ("1/2", "1/2", "1/2"),
            ("1", "1", "0"),
            ("1/4", "1", "0"),
            ("1/3", "2/3", "1/3"),
        ],
        lambda d: F(d["prior"]) * (1 - F(d["prior"])) * (F(d["a"]) - F(d["b"])) ** 2,
        4,
        True,
    )

    add(
        "evidence_order",
        [308],
        ("סדר תצפיות אינו תמיד מידע נוסף", "Observation order need not add information"),
        (
            "בקופסה אחת כל הפריטים עצמאיים בהינתן המפעל, עם שיעור תקינות קבוע. נצפו {good} תקינים ו־{bad} פגומים. לכמה רצפי תוצאות מסודרים יש בדיוק אותה סבירות בכל מפעל?",
            "Within one box, chips are independent given the factory, with a constant good rate. Observe {good} good and {bad} bad chips. How many ordered result sequences have exactly this composition and hence the same likelihood at every factory?",
        ),
        (
            "בוחרים את מיקומי התקינים בין כל התוצאות. החלפת הסדר אינה משנה את מכפלת ההסתברויות כשהמודל קבוע ועצמאי מותנית.",
            "Choose the good positions among all outcomes. Reordering preserves the likelihood product under this fixed, conditionally independent model.",
        ),
        ("מידע הסדר תלוי בהנחות המודל.", "Whether order carries information depends on the model."),
        "good bad",
        [(2, 1), (0, 3), (2, 2), (1, 4), (3, 0)],
        lambda d: math.comb(d["good"] + d["bad"], d["good"]),
        2,
    )

    add(
        "prior_balance",
        [308],
        ("איזה משקל מוקדם מאזן את הראיה", "Which prior balances the evidence"),
        (
            "תצפית E מתקבלת בסיכוי {a} במקור A ובסיכוי {b} במקור B. איזה ערך q=P(A) ייתן P(A|E)=1/2? שני מקורות אלה ממצים את האפשרויות.",
            "Observation E has probability {a} under source A and {b} under B. Which q=P(A) makes P(A|E)=1/2? These two sources exhaust the possibilities.",
        ),
        (
            "כדי שהמשקלים המעודכנים ישתוו פותרים qa=(1−q)b. לכן q=b/(a+b); ראיה חזקה יותר מאפשרת משקל מוקדם נמוך יותר.",
            "Equal posterior weights require qa=(1−q)b. Thus q=b/(a+b); stronger evidence can offset a smaller prior.",
        ),
        ("אפשר להסיק לאחור מהאיזון המבוקש.", "Reason backward from the desired balance."),
        "a b",
        [("3/4", "1/4"), ("1/2", "1/2"), ("1/4", "3/4"), ("1", "1/3"), ("2/3", "1/2")],
        lambda d: F(d["b"]) / (F(d["a"]) + F(d["b"])),
        3,
        True,
    )

    add(
        "sample_exact_defects",
        [159, 308],
        ("מספר פגומים מדויק דורש שתי בחירות", "An exact defect count requires two selections"),
        (
            "בקופסה {good} פריטים תקינים ו־{bad} פגומים. דוגמים {draws} פריטים שונים באופן אחיד ללא החזרה. מה ההסתברות שבמדגם בדיוק {defects} פגומים?",
            "A box contains {good} good and {bad} bad items. Uniformly sample {draws} distinct items without replacement. What is the probability of exactly {defects} defective items in the sample?",
        ),
        (
            "בוחרים את מספר הפגומים המבוקש ואת יתר המדגם מהתקינים. מכפילים את מספרי הבחירות ומחלקים במספר כלל המדגמים מאותו גודל.",
            "Choose the requested defects and the remaining sample from good items. Multiply these selection counts and divide by all same-size samples.",
        ),
        (
            "ללא החזרה, מצב המלאי משתנה בכל בחירה.",
            "Without replacement, inventory changes after every selection.",
        ),
        "good bad draws defects",
        [(3, 2, 2, 1), (1, 3, 2, 2), (4, 0, 3, 1), (3, 2, 0, 0), (2, 2, 4, 2)],
        lambda d: F(
            math.comb(d["bad"], d["defects"]) * math.comb(d["good"], d["draws"] - d["defects"])
            if 0 <= d["defects"] <= d["bad"] and 0 <= d["draws"] - d["defects"] <= d["good"]
            else 0,
            math.comb(d["good"] + d["bad"], d["draws"]),
        ),
        3,
        True,
    )

    add(
        "stop_on_failure",
        [159],
        ("עצירה מוקדמת משנה את מספר הבדיקות", "Early stopping changes the test count"),
        (
            "בודקים לכל היותר {limit} פריטים עצמאיים, שכל אחד תקין בהסתברות {p}. עוצרים בכישלון הראשון או בהגעה למגבלה. מה תוחלת מספר הבדיקות שבוצעו?",
            "Test at most {limit} independent items, each good with probability {p}. Stop at the first failure or the limit. What is the expected number of tests performed?",
        ),
        (
            "הבדיקה ה־j מתבצעת רק אם כל קודמותיה הצליחו. מסכמים את הסתברויות ההגעה לכל בדיקה, לרבות הראשונה.",
            "Test j occurs only if all earlier tests passed. Sum the probabilities of reaching each test, including the first.",
        ),
        (
            "אפשר לחשב תוחלת דרך הסתברויות ההגעה לשלבים.",
            "Expectation can be computed from stage-reach probabilities.",
        ),
        "limit p",
        [(3, "1/2"), (4, "0"), (4, "1"), (1, "2/3"), (3, "3/4")],
        lambda d: sum((F(d["p"]) ** i for i in range(d["limit"])), F()),
    )

    add(
        "conditional_failures",
        [159],
        ("לפחות כישלון אחד משנה את המדגם", "At least one failure changes the sample space"),
        (
            "שני פריטים עצמאיים נכשלים בהסתברויות {a},{b}. ידוע שלפחות אחד נכשל. מה ההסתברות ששניהם נכשלו?",
            "Two independent items fail with probabilities {a},{b}. At least one is known to have failed. What is the probability that both failed?",
        ),
        (
            "מחלקים את הסתברות שני הכישלונות בהסתברות איחוד הכישלונות. במכנה מפחיתים פעם אחת את החפיפה.",
            "Divide the probability of two failures by the probability of their union. Subtract their overlap once in the denominator.",
        ),
        ("התניה מצמצמת את עולם האפשרויות.", "Conditioning restricts the possible worlds."),
        "a b",
        [("1/2", "1/2"), ("1", "1/3"), ("0", "1/2"), ("1/4", "3/4"), ("1", "1")],
        lambda d: F(d["a"]) * F(d["b"]) / (F(d["a"]) + F(d["b"]) - F(d["a"]) * F(d["b"])),
        3,
        True,
    )

    add(
        "positive_precision",
        [159],
        ("התראות שווא תלויות גם בשכיחות", "False alerts also depend on prevalence"),
        (
            "בבדיקת ייצור סומנו {detected} פריטים פגומים ו־{false} פריטים תקינים כחשודים. בוחרים באחידות אחד מהחשודים. מה ההסתברות שהוא באמת פגום?",
            "A production check flagged {detected} defective items and {false} good items. Choose one flagged item uniformly. What is the probability that it is truly defective?",
        ),
        (
            "המכנה הוא מספר כל החשודים, לא כל הפריטים ולא כל הפגומים. מחשבים את חלקם של הפגומים בקרב החשודים.",
            "The denominator is all flagged items, not all items or all defects. Compute the defective fraction among the flagged.",
        ),
        (
            "הסתברות מותנית דורשת מכנה התואם למה שכבר ידוע.",
            "A conditional probability needs a denominator matching what is already known.",
        ),
        "detected false",
        [(9, 9), (1, 99), (20, 0), (0, 12), (8, 2)],
        lambda d: F(d["detected"], d["detected"] + d["false"]),
        2,
        True,
    )

    add(
        "fleet_range",
        [244],
        ("פחות אופנועים שורפים פחות דלק", "Fewer motorcycles burn less fuel"),
        (
            "{n} אופנועים מתחילים יחד, בכל אחד מיכל מלא של {capacity} ליטר. כל אופנוע נוסע צורך ליטר למטר. מותר להעביר דלק ללא אובדן ולנטוש אופנועים, ללא מחסנים או חזרה. מה המרחק המרבי שאחד יגיע אליו?",
            "{n} motorcycles start together, each with a full {capacity}-litre tank. Each moving motorcycle burns one litre per metre. Lossless transfers and abandonment are allowed, without depots or return. What is the farthest one can reach?",
        ),
        (
            "כשנותרים k אופנועים, נסיעה של C/k צורכת מיכל אחד במשותף. מרכזים את הדלק באחרים ויורדים שלב; מסכמים C/k עד שנותר אחד.",
            "With k motorcycles, C/k distance consumes one tank collectively. Consolidate fuel into the others and drop one; sum C/k until one remains.",
        ),
        (
            "קצב צריכת משאב משתנה כשמספר הצורכים יורד.",
            "Resource consumption rate changes when the number of consumers decreases.",
        ),
        "n capacity",
        [(3, 6), (1, 5), (2, 3), (4, 12), (5, 2)],
        lambda d: d["capacity"] * sum((F(1, k) for k in range(1, d["n"] + 1)), F()),
        4,
    )

    add(
        "fleet_abandon",
        [244],
        ("מקום פנוי מגביל איחוד דלק", "Free tank space limits consolidation"),
        (
            "{n} אופנועים, כל אחד עם {capacity} ליטר במיכל מלא, נסעו יחד {distance} מטר. צריכה: ליטר למטר לכל אופנוע. כמה אופנועים לפחות חייבים להישאר כדי לאחסן את כל הדלק שנותר? מותר להעביר דלק בלי אובדן.",
            "{n} motorcycles, each initially holding {capacity} litres in a full tank, travelled {distance} metres together. Each burns one litre per metre. At least how many motorcycles must remain to hold all remaining fuel? Transfers are lossless.",
        ),
        (
            "הדלק הנותר הוא n(C−d). מחלקים בקיבולת מיכל ומעגלים כלפי מעלה; אם אין דלק אפשר לאחסן אותו באפס אופנועים.",
            "Remaining fuel is n(C−d). Divide by tank capacity and round upward; zero fuel needs zero tanks.",
        ),
        (
            "שימור כמות חייב להתאים גם לקיבולת האחסון.",
            "Quantity conservation must also respect storage capacity.",
        ),
        "n capacity distance",
        [(3, 6, 2), (3, 6, 1), (2, 5, 0), (4, 4, 4), (5, 10, 7)],
        lambda d: math.ceil(F(d["n"] * (d["capacity"] - d["distance"]), d["capacity"])),
    )

    add(
        "fleet_transfer",
        [244],
        ("עודף במיכל קטן עלול ללכת לאיבוד", "A small tank may waste transferred fuel"),
        (
            "שני אופנועים נמצאים יחד. במיכל הראשון {a} ליטר ובשני {b}; קיבולת השני {capacity}. נוטשים את הראשון ומעבירים לשני כמה שאפשר. השני צורך {rate} ליטר למטר. כמה מטרים נוספים יוכל לעבור?",
            "Two motorcycles are together. The first holds {a} L and the second {b} L; the second tank holds at most {capacity} L. Abandon the first and transfer as much as fits. The second burns {rate} L/m. How many additional metres can it travel?",
        ),
        (
            "כמות הדלק לאחר ההעברה מוגבלת למינימום של הסכום והקיבולת. מחלקים אותה בצריכה ליחידת דרך.",
            "Fuel after transfer is the minimum of the total and capacity. Divide by consumption per unit distance.",
        ),
        (
            "דלק זמין ודלק שניתן לשאת אינם בהכרח שווים.",
            "Available fuel and carryable fuel need not be equal.",
        ),
        "a b capacity rate",
        [(4, 3, 5, 1), (1, 2, 5, 1), (0, 2, 5, 2), (3, 0, 4, 2), (5, 5, 5, 1)],
        lambda d: F(min(d["a"] + d["b"], d["capacity"]), d["rate"]),
        2,
    )

    def distances(d):
        n = d["n"]
        dist = [[0 if i == j else 10**6 for j in range(n)] for i in range(n)]
        for a, b, w in d["edges"]:
            dist[a][b] = dist[b][a] = min(dist[a][b], w)
        for k, i, j in it.product(range(n), repeat=3):
            dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
        return dist

    graph_cases = [
        (3, [[0, 1, 2], [1, 2, 2], [0, 2, 7]], [0, 2]),
        (4, [[0, 1, 1], [0, 2, 1], [0, 3, 1]], [1, 2, 3]),
        (3, [[0, 1, 1], [1, 2, 4]], [0, 0, 2]),
        (2, [[0, 1, 5]], [1, 1]),
        (4, [[0, 1, 2], [1, 2, 1], [2, 3, 2], [3, 0, 1]], [0, 2, 3]),
    ]
    add(
        "graph_meeting",
        [246],
        ("רשת הרחובות קובעת את עלות המפגש", "The street network determines meeting cost"),
        (
            "צמתים 0..{n} לא כולל {n}; רחובות דו־כיווניים (קצה,קצה,אורך): {edges}. אנשים נמצאים ב־{people}, כולל חזרות. מה סכום מרחקי ההליכה הקצרים המזערי למפגש בצומת?",
            "Vertices are 0..{n}, excluding {n}; undirected streets (endpoint,endpoint,length): {edges}. People are at {people}, including repetitions. What is the minimum sum of shortest walking distances to a meeting vertex?",
        ),
        (
            "מחשבים מרחקי מסלולים קצרים ברשת, ואז לכל יעד מסכמים מרחק עבור כל אדם. רחוב ישיר אינו בהכרח המסלול הקצר.",
            "Compute shortest network distances, then sum one distance per person for each destination. A direct street need not be the shortest route.",
        ),
        ("אופטימיזציה תלויה במטריקה המותרת.", "Optimization depends on the permitted distance metric."),
        "n edges people",
        graph_cases,
        lambda d: min(sum(distances(d)[p][v] for p in d["people"]) for v in range(d["n"])),
        4,
    )

    add(
        "meeting_radius",
        [246],
        ("להקטין את ההליכה הארוכה ביותר", "Minimize the longest walk"),
        (
            "אנשים נמצאים בנקודות {positions} על ישר. נקודת המפגש יכולה להיות כל מספר ממשי. מה המרחק הגדול ביותר הקטן ביותר שאפשר להבטיח? ממזערים מרחק מרבי, לא סכום.",
            "People occupy positions {positions} on a line. The meeting point may be any real number. What is the smallest possible maximum walking distance? Minimize the maximum, not the sum.",
        ),
        (
            "שני הקיצונים רחוקים D זה מזה, ולכן אחד מהם ילך לפחות D/2. אמצע הקיצונים משיג בדיוק את החסם.",
            "The extremes are D apart, so at least one must walk D/2. Their midpoint attains that bound.",
        ),
        (
            "שינוי פונקציית המטרה יכול לשנות את נקודת המפגש.",
            "Changing the objective can change the meeting point.",
        ),
        "positions",
        [([0, 1, 10],), ([4, 4],), ([-3, 2],), ([0, 0, 0, 8],), ([1, 3, 5, 7],)],
        lambda d: F(max(d["positions"]) - min(d["positions"]), 2),
        3,
    )

    add(
        "reachable_meetings",
        [246],
        ("מפגש דורש רכיב משותף", "A meeting requires a shared component"),
        (
            "רשת לא מכוונת מכילה צמתים 0..{n} לא כולל {n}, וקשתות {edges}. אנשים נמצאים ב־{people}. בכמה צמתים יכולים כולם להיפגש באמצעות הליכה ברשת?",
            "An undirected network has vertices 0..{n}, excluding {n}, and edges {edges}. People are at {people}. At how many vertices can everyone meet by walking through the network?",
        ),
        (
            "כל אדם יכול להגיע רק לרכיב הקשירות שלו. יעדים אפשריים הם החיתוך של קבוצות ההגעה של כל האנשים.",
            "Each person can reach only their connected component. Feasible destinations are the intersection of everyone's reachable sets.",
        ),
        (
            "לפני חיפוש יעד מיטבי בודקים שקיים יעד אפשרי.",
            "Check feasibility before optimizing a destination.",
        ),
        "n edges people",
        [
            (4, [[0, 1, 1], [1, 2, 1]], [0, 2]),
            (4, [[0, 1, 1], [2, 3, 1]], [0, 2]),
            (3, [], [1, 1]),
            (3, [[0, 1, 1]], [0]),
            (4, [[0, 1, 1], [1, 2, 1], [2, 3, 1]], [0, 3]),
        ],
        lambda d: sum(all(distances(d)[p][v] < 10**6 for p in d["people"]) for v in range(d["n"])),
    )

    add(
        "shortcut_savings",
        [246],
        ("קיצור דרך עשוי להיות חסר השפעה", "A shortcut may have no effect"),
        (
            "בין A ל־C יש מסלול דרך B באורכים {ab},{bc}, ורחוב ישיר באורך {ac}. מוסיפים רחוב ישיר חדש באורך {new}. בכמה מתקצר המסלול הקצר ביותר בין A ל־C? כל האורכים חיוביים.",
            "Between A and C, a route through B has lengths {ab},{bc}, and a direct street has length {ac}. Add a new direct street of length {new}. How much does the shortest A-to-C route decrease? All lengths are positive.",
        ),
        (
            "משווים את הרחוב החדש למינימום הקודם, ולא רק לרחוב הישיר הישן. הוספה לא יכולה להאריך את המסלול הקצר.",
            "Compare the new street with the previous minimum, not just the old direct street. Adding an option cannot lengthen the shortest route.",
        ),
        (
            "אפשרות חדשה מועילה רק אם היא משפרת את הטובה הקיימת.",
            "A new option helps only if it improves the existing best.",
        ),
        "ab bc ac new",
        [(2, 3, 9, 4), (2, 3, 9, 7), (6, 5, 4, 2), (1, 1, 2, 2), (4, 4, 12, 3)],
        lambda d: max(0, min(d["ab"] + d["bc"], d["ac"]) - d["new"]),
        2,
    )

    add(
        "meeting_tiebreak",
        [246],
        ("שוויון בעלות צריך כלל הכרעה", "Equal cost needs a tie rule"),
        (
            "צמתים 0..{n} לא כולל {n}; רחובות לא מכוונים (u,v,אורך): {edges}. מיקומי אנשים: {people}. איזה אינדקס צומת ממזער סכום מרחקים קצרים? בשוויון בוחרים אינדקס קטן ביותר.",
            "Vertices are 0..{n}, excluding {n}; undirected streets (u,v,length): {edges}. People occupy {people}. Which vertex index minimizes total shortest distance? Choose the smallest index on ties.",
        ),
        (
            "סופרים אנשים חוזרים כמשקל נוסף. משווים זוגות של עלות ואינדקס, כדי לקבל בחירה חד־משמעית גם כשיש כמה יעדים מיטביים.",
            "Repeated people add weight. Compare cost-index pairs to make the selection unique even when several destinations are optimal.",
        ),
        ("שובר שוויון הוא חלק מחוזה הפלט.", "Tie-breaking is part of the output contract."),
        "n edges people",
        graph_cases,
        lambda d: min(range(d["n"]), key=lambda v: (sum(distances(d)[p][v] for p in d["people"]), v)),
        4,
    )

    add(
        "cluster_mean",
        [277],
        ("מרכז אשכול הוא ממוצע משוקלל", "A cluster center is a weighted mean"),
        (
            "נקודות אשכול חד־ממדי הן {points}, עם חזרות כפי שמופיעות. מה המרכז שממזער את סכום ריבועי המרחקים? המרכז יכול להיות שבר.",
            "A one-dimensional cluster contains {points}, including the shown repetitions. Which center minimizes the sum of squared distances? The center may be fractional.",
        ),
        (
            "המינימום מתקבל בממוצע החשבוני של כל הדגימות, כולל כל חזרה. עיגול למספר שלם משנה את הבעיה.",
            "The arithmetic mean of every sample, including repeated ones, minimizes the objective. Rounding to an integer changes the problem.",
        ),
        (
            "במרחק ריבועי, כל דגימה משפיעה על מרכז הכובד.",
            "Under squared distance, every sample contributes to the center.",
        ),
        "points",
        [([0, 0, 6],), ([-2, 2],), ([1, 2],), ([4],), ([1, 1, 1, 9],)],
        lambda d: F(sum(d["points"]), len(d["points"])),
        2,
    )

    add(
        "cluster_sse",
        [277],
        ("מרחקים מנוגדים אינם מבטלים שגיאה", "Opposite deviations do not cancel error"),
        (
            "נקודות {points} משויכות כולן למרכז {center}. מה SSE, סכום ריבועי המרחקים למרכז?",
            "Points {points} are all assigned to center {center}. What is SSE, the sum of squared distances to that center?",
        ),
        (
            "מחסרים את המרכז מכל נקודה, מעלים כל הפרש בריבוע ואז מסכמים. ריבוע הסכום אינו סכום הריבועים.",
            "Subtract the center from each point, square each difference, then sum. The square of a sum is not the sum of squares.",
        ),
        (
            "מסכמים את העלות לכל דגימה לפני הסקת איכות כוללת.",
            "Sum per-sample costs before assessing overall quality.",
        ),
        "points center",
        [([-2, 2], 0), ([3, 3], 3), ([0, 1, 2], 1), ([1, 1, 5], 2), ([0], "1/2")],
        lambda d: sum((F(x) - F(d["center"])) ** 2 for x in d["points"]),
        2,
    )

    add(
        "nearest_tie",
        [277],
        ("מרכזים שווים במרחק אינם בהכרח זהים", "Equidistant centers need not coincide"),
        (
            "נקודה x={x}; מרכזי האשכולות לפי אינדקס הם {centers}. בוחרים מרחק ריבועי קטן ביותר, ובשוויון את האינדקס הקטן ביותר. מה אינדקס האשכול שנבחר? אינדקסים מתחילים ב־0.",
            "Point x={x}; cluster centers in index order are {centers}. Choose the smallest squared distance, breaking ties by smallest index. Which cluster index is selected? Indices start at 0.",
        ),
        (
            "משווים ריבועי הפרשים ולא את ערכי המרכזים. כלל השוויון חל גם על מרכזים שונים הנמצאים משני צדי הנקודה.",
            "Compare squared differences, not center values. The tie rule also applies to distinct centers on opposite sides of the point.",
        ),
        ("מרחק שווה אינו מחייב זהות בערכים.", "Equal distance does not imply equal values."),
        "x centers",
        [(2, [0, 4]), (3, [0, 4]), (1, [1, 1, 5]), (-2, [2, -3, -1]), (5, [0, 3, 8])],
        lambda d: min(range(len(d["centers"])), key=lambda i: ((d["x"] - d["centers"][i]) ** 2, i)),
        2,
    )

    add(
        "empty_cluster",
        [277],
        ("אשכול ריק צריך מדיניות מפורשת", "An empty cluster needs an explicit policy"),
        (
            "נקודות {points}; מרכזים לפי אינדקס {centers}. משייכים לקרוב ביותר, בשוויון לאינדקס הקטן. מעדכנים לממוצע; אשכול ריק שומר את מרכזו. מה מרכז אשכול {index} אחרי סבב אחד?",
            "Points are {points}; indexed centers are {centers}. Assign to the nearest center, choosing the smallest index on ties. Update to means; an empty cluster retains its center. What is cluster {index}'s center after one round?",
        ),
        (
            "קובעים קודם את כל השיוכים לפי המרכזים הישנים. אם אין נקודות באשכול המבוקש, אין ממוצע לחישוב ופועלים לפי מדיניות השימור.",
            "First assign every point using the old centers. If the requested cluster has no points, no mean exists; apply the retention policy.",
        ),
        (
            "מקרה ריק אינו היתר לחלק באפס או להמציא מרכז.",
            "An empty case does not permit division by zero or an invented center.",
        ),
        "points centers index",
        [
            ([0, 1], [0, 10], 1),
            ([0, 2], [0, 2], 1),
            ([1, 1], [1, 1], 1),
            ([-2, 0, 2], [-3, 3], 0),
            ([4], [0, 4, 8], 2),
        ],
        lambda d: (lambda pts: F(sum(pts), len(pts)) if pts else F(d["centers"][d["index"]]))(
            [
                x
                for x in d["points"]
                if min(range(len(d["centers"])), key=lambda i: ((x - d["centers"][i]) ** 2, i)) == d["index"]
            ]
        ),
        4,
    )

    add(
        "merge_cost",
        [277],
        ("איחוד אשכולות מוסיף עלות בין המרכזים", "Merging clusters adds between-center cost"),
        (
            "שתי קבוצות קבועות הן {left} ו־{right}, כל אחת במרכזה הממוצע. מאחדים אותן לאשכול אחד בממוצע המשותף. בכמה גדל SSE? אין שיוך מחדש לאשכולות אחרים.",
            "Two fixed groups are {left} and {right}, each at its mean center. Merge them into one cluster at their combined mean. By how much does SSE increase? No reassignment to other clusters occurs.",
        ),
        (
            "מחשבים עלות לפני ואחרי. התוספת היא n₁n₂/(n₁+n₂) כפול ריבוע ההפרש בין הממוצעים, ולכן אפס אם הם שווים.",
            "Compare costs before and after. The increase is n₁n₂/(n₁+n₂) times the squared difference between means, hence zero for equal means.",
        ),
        (
            "גודל הקבוצות והמרחק ביניהן קובעים את מחיר האיחוד.",
            "Group sizes and separation determine the merge cost.",
        ),
        "left right",
        [([0, 0], [4, 4]), ([-1, 1], [0]), ([0], [2]), ([0, 2], [4]), ([1, 1, 1], [5])],
        lambda d: (
            F(len(d["left"]) * len(d["right"]), len(d["left"]) + len(d["right"]))
            * (F(sum(d["left"]), len(d["left"])) - F(sum(d["right"]), len(d["right"]))) ** 2
        ),
        4,
    )

    add(
        "reassign_count",
        [277],
        ("עדכון מרכז יכול לשנות שיוך", "Updating a center can change assignments"),
        (
            "נקודות {points}; מרכזים ישנים {old} ומרכזים חדשים {new}. בכל מצב בוחרים את המרכז הקרוב, ובשוויון את האינדקס הקטן. לכמה נקודות משתנה אינדקס השיוך?",
            "Points are {points}; old centers are {old}, new centers {new}. In each state choose the nearest center, breaking ties by smallest index. How many points change their assigned cluster index?",
        ),
        (
            "מחשבים לכל נקודה את השיוך בשני המצבים. שינוי מספרי במרכזים לבדו אינו מוכיח ששינוי שיוך התרחש.",
            "Compute each point's assignment in both states. A numerical center change alone does not prove an assignment changed.",
        ),
        (
            "מצב האלגוריתם כולל גם שיוכים, לא רק מרכזים.",
            "Algorithm state includes assignments as well as centers.",
        ),
        "points old new",
        [
            ([0, 3, 4, 10], [0, 10], [2, 7]),
            ([0, 1], [0, 10], [1, 9]),
            ([2], [0, 4], [0, 3]),
            ([0, 5, 10], [0, 10], [10, 0]),
            ([1, 1, 4], [0, 6], [2, 6]),
        ],
        lambda d: sum(
            min(range(len(d["old"])), key=lambda i: ((x - d["old"][i]) ** 2, i))
            != min(range(len(d["new"])), key=lambda i: ((x - d["new"][i]) ** 2, i))
            for x in d["points"]
        ),
        3,
    )

    add(
        "sse_scaling",
        [277],
        ("שינוי יחידות מרבע את שגיאת הריבועים", "Changing units squares the SSE scale"),
        (
            "SSE של נקודות ומרכזיהן הוא {sse}. ממירים את כולם לפי y={scale}x+{shift}, בלי לשנות שיוכים. מה SSE החדש?",
            "Points and their assigned centers have SSE={sse}. Transform all of them by y={scale}x+{shift}, retaining assignments. What is the new SSE?",
        ),
        (
            "ההזזה מתבטלת בהפרש בין נקודה למרכז. כל הפרש מוכפל בסולם, ולכן כל ריבוע מוכפל בריבוע הסולם.",
            "Translation cancels in each point-center difference. Scaling multiplies each difference, so its square scales by the squared factor.",
        ),
        (
            "עלויות ריבועיות תלויות בריבוע יחידת המידה.",
            "Squared costs depend on the square of the measurement unit.",
        ),
        "sse scale shift",
        [(5, 2, 3), (8, "1/2", 10), (6, -1, 4), (0, 7, -2), (3, 0, 5)],
        lambda d: F(d["sse"]) * F(d["scale"]) ** 2,
        2,
    )

    add(
        "unseen_focus",
        [270],
        ("ללא צורה ידועה צריך לבדוק כל מועמד", "Without a shape promise every candidate matters"),
        (
            "יש {n} הגדרות פוקוס עם ערכים יציבים אך בלתי מוגבלים, בלי הנחת צורה. כבר נמדדו האינדקסים {seen}, כולל חזרות. כמה הגדרות נוספות חייבים למדוד במקרה הגרוע כדי לדעת בוודאות את המקסימום?",
            "There are {n} focus settings with stable but unbounded values and no shape promise. Indices {seen} have been measured, including repeats. In the worst case, how many additional settings must be measured to guarantee the maximum?",
        ),
        (
            "כל הגדרה שלא נמדדה עשויה להסתיר ערך גדול יותר. מדידה חוזרת של אינדקס קיים אינה מצמצמת את מספר המועמדים שלא נבדקו.",
            "Any unseen setting may hide a larger value. Repeating a measured index does not reduce the number of unseen candidates.",
        ),
        (
            "שיטת חיפוש מהירה דורשת הנחה שמצמצמת אפשרויות.",
            "A faster search needs an assumption that eliminates possibilities.",
        ),
        "n seen",
        [(5, [0, 2]), (4, [1, 1]), (3, [0, 1, 2]), (1, []), (6, [0, 5, 0])],
        lambda d: d["n"] - len(set(d["seen"])),
        2,
    )

    add(
        "focus_plateau",
        [270],
        ("מישור מקסימום עדיין דורש בחירה", "A maximum plateau still needs a selection"),
        (
            "ערכי הפוקוס לפי אינדקס הם {values}. המפרט דורש את האינדקס הקטן ביותר שערכו מרבי, גם במישור מקסימום. מה האינדקס? המספור מתחיל ב־0.",
            "Focus values in index order are {values}. The specification requires the smallest index attaining the maximum, including a maximum plateau. What is the index? Numbering starts at 0.",
        ),
        (
            "מאתרים את הערך המרבי ואז את הופעתו הראשונה. מרכז המישור או ההופעה האחרונה אינם עומדים בכלל השוויון.",
            "Find the maximum value and then its first occurrence. The plateau midpoint or last occurrence violates the tie rule.",
        ),
        ("ערך מיטבי אינו מגדיר לבדו פלט יחיד.", "An optimal value alone does not define a unique output."),
        "values",
        [([1, 4, 4, 2],), ([5, 4, 3],), ([1, 2, 7],), ([3, 3, 3],), ([1, 5, 2, 5],)],
        lambda d: d["values"].index(max(d["values"])),
        2,
    )

    add(
        "noise_possible_max",
        [270, 159],
        ("רעש משאיר כמה מועמדים למקסימום", "Noise leaves several possible maxima"),
        (
            "טווחי הערכים האמיתיים של הגדרות הם {intervals}, כולל הקצוות. כל שילוב בטווחים אפשרי, ושוויון נחשב מקסימום. כמה הגדרות יכולות להיות מרביות עבור שילוב כלשהו?",
            "Settings' true-value intervals are {intervals}, including endpoints. Every combination within the intervals is possible, and ties count as maxima. How many settings could be maximal for some combination?",
        ),
        (
            "מועמד אפשרי אם הקצה העליון שלו אינו קטן מהקצה התחתון הגבוה ביותר. להצגת אפשרות מציבים אותו גבוה ואת המתחרים נמוך.",
            "A candidate is possible when its upper endpoint reaches the greatest lower endpoint. A witness sets it high and competitors low.",
        ),
        ("טווחים חופפים מגבילים את הוודאות בדירוג.", "Overlapping intervals limit certainty about rankings."),
        "intervals",
        [
            ([[2, 4], [3, 5], [0, 1]],),
            ([[5, 5], [0, 4]],),
            ([[1, 3], [1, 3], [1, 3]],),
            ([[2, 2], [1, 2]],),
            ([[0, 0]],),
        ],
        lambda d: sum(hi >= max(lo for lo, _ in d["intervals"]) for _, hi in d["intervals"]),
        3,
    )

    add(
        "focus_travel",
        [270],
        ("אותן מדידות יכולות לעלות דרך שונה", "The same measurements can require different travel"),
        (
            "המכשיר מתחיל בהגדרה {start}, מבקר לפי הסדר ב־{order}, ולבסוף חייב לעמוד ב־{finish}. עלות מעבר היא הפרש אינדקסים מוחלט. מה עלות התנועה הכוללת? מדידה עצמה אינה מזיזה אותו.",
            "An instrument starts at setting {start}, visits {order} in order, and must finish at {finish}. Movement cost is the absolute index difference. What is total movement cost? Measurement itself does not move it.",
        ),
        (
            "מסכמים מרחק בין מיקומים עוקבים, כולל החזרה למיקום הסיום. מספר המדידות לבדו אינו קובע עלות תנועה.",
            "Sum distances between consecutive positions, including repositioning to the final setting. Measurement count alone does not determine movement cost.",
        ),
        ("עלות גישה ועלות מדידה הן מדדים נפרדים.", "Access cost and measurement cost are separate metrics."),
        "start order finish",
        [(0, [5, 1, 4], 5), (0, [1, 4, 5], 5), (3, [3, 3], 3), (4, [0, 2], 0), (0, [], 7)],
        lambda d: sum(
            abs(a - b) for a, b in zip([d["start"]] + d["order"], d["order"] + [d["finish"]], strict=True)
        ),
        2,
    )

    add(
        "settling_cost",
        [270],
        ("שהייה נדרשת אחרי שינוי מצב", "Settling is needed after a state change"),
        (
            "מתחילים בהגדרה {start} שכבר התייצבה ומודדים לפי {order}. כל מדידה עולה {measure} יחידות זמן. כל שינוי הגדרה מוסיף {settle} להתייצבות; מדידה חוזרת באותה הגדרה אינה מוסיפה זאת. מה הזמן הכולל?",
            "Start at already-settled setting {start}; measure in order {order}. Measurement duration: {measure}; settling duration per setting change: {settle}, in the same time unit. Repeated measurements at the same setting need no settling. What is total time?",
        ),
        (
            "סופרים כל מדידה, אך מוסיפים התייצבות רק כשאינדקס המצב משתנה. גם המעבר הראשון תלוי במצב ההתחלתי.",
            "Count every measurement, but add settling only when the setting changes. The first transition also depends on the initial setting.",
        ),
        (
            "תקורה יכולה להיות תלויה במעבר ולא במספר הקריאות.",
            "Overhead may depend on transitions rather than call count.",
        ),
        "start order measure settle",
        [(0, [0, 1, 1, 2], 1, 3), (2, [2, 2], 2, 5), (0, [1, 0, 1], 1, 2), (1, [], 4, 2), (3, [0], 2, 4)],
        lambda d: (
            len(d["order"]) * d["measure"]
            + d["settle"]
            * sum(a != b for a, b in zip([d["start"]] + d["order"][:-1], d["order"], strict=False))
        ),
        2,
    )

    add(
        "lion_counts",
        [231],
        ("איום עתידי יכול למנוע ארוחה", "A future threat can prevent a meal"),
        (
            "אריה שאוכל פרה הופך לפרה; כולם מעדיפים לשרוד על פני לאכול, והחשיבה רציונלית ומשותפת. בכמה מספרי אריות התחלתיים בטווח 1..{limit} הפרה המקורית תיאכל? המהלכים עוקבים, לא בו־זמניים.",
            "A lion eating a cow becomes the cow; all prioritize survival over eating, with common rational reasoning. For how many initial lion counts in 1..{limit} will the original cow be eaten? Actions are sequential, not simultaneous.",
        ),
        (
            "ללא אריות הפרה בטוחה. אריה יאכל רק אם הפרה שיהפוך אליה תהיה בטוחה מול מספר קטן באחד; כך המצבים מתחלפים עם הזוגיות.",
            "With no lions, the cow is safe. A lion eats only if the cow it becomes is safe against one fewer lion; outcomes therefore alternate with parity.",
        ),
        (
            "הסקה לאחור תלויה בסדר העדיפויות של המשתתפים.",
            "Backward reasoning depends on participants' preference ordering.",
        ),
        "limit",
        [(6,), (1,), (2,), (9,), (0,)],
        lambda d: (d["limit"] + 1) // 2,
        3,
    )

    add(
        "calendar_age",
        [232],
        ("גיל משתנה ביום ההולדת", "Age changes on the birthday"),
        (
            "תאריך לידה {born}; התאריך כעת {today}, בפורמט שנה־חודש־יום. מה הגיל בשנים שלמות? אין מקרי לידה ב־29 בפברואר.",
            "Birth date is {born}; today is {today}, both year-month-day. What is age in completed years? No birth occurs on February 29.",
        ),
        (
            "מחסרים שנות לוח, ואז מפחיתים שנה אם יום ההולדת השנה טרם הגיע. החלפת השנה לבדה אינה יום הולדת.",
            "Subtract calendar years, then subtract one if this year's birthday has not occurred. New Year's Day alone is not a birthday.",
        ),
        ("מונה שנים שלמות תלוי גם בחודש וביום.", "Completed-year counts depend on month and day too."),
        "born today",
        [
            ("2017-12-31", "2026-01-01"),
            ("2017-12-31", "2026-12-31"),
            ("2000-05-10", "2026-05-09"),
            ("2000-05-10", "2026-05-10"),
            ("2025-01-01", "2026-01-01"),
        ],
        lambda d: (lambda b, t: t.year - b.year - ((t.month, t.day) < (b.month, b.day)))(
            date.fromisoformat(d["born"]), date.fromisoformat(d["today"])
        ),
        2,
    )

    add(
        "calendar_days",
        [232],
        ("שינוי שנה אינו שנה שחלפה", "A calendar-year change is not a year elapsed"),
        (
            "מה מספר הימים שחלפו בין תחילת {start} לתחילת {end}, לפי הלוח הגרגוריאני? הפורמט שנה־חודש־יום; אין חישוב שעות או אזורי זמן.",
            "How many days elapse from the start of {start} to the start of {end}, using the Gregorian calendar? Dates use year-month-day; ignore clock times and time zones.",
        ),
        (
            "סופרים מעברי תאריך בפועל. דצמבר יכול לעבור לינואר בתוך יום אחד, ופברואר כולל יום נוסף בשנה מעוברת.",
            "Count actual date transitions. December can become January in one day, and February includes an extra day in a leap year.",
        ),
        ("תוויות תאריך וזמן שחלף הם גדלים שונים.", "Date labels and elapsed time are different quantities."),
        "start end",
        [
            ("2025-12-31", "2026-01-02"),
            ("2024-02-28", "2024-03-01"),
            ("2025-02-28", "2025-03-01"),
            ("2026-01-01", "2026-01-01"),
            ("2026-04-30", "2026-05-02"),
        ],
        lambda d: (date.fromisoformat(d["end"]) - date.fromisoformat(d["start"])).days,
        2,
    )

    add(
        "freefall_height",
        [248],
        ("זמן נפילה נכנס בריבוע", "Fall time enters quadratically"),
        (
            "במודל מחשבתי גוף משתחרר ממנוחה, ללא גרר, בתאוצה קבועה g={g} מטר לשנייה בריבוע. זמן הנפילה הוא {time} שניות. מה הגובה במטרים?",
            "In a thought model, a body is released from rest without drag under constant g={g} metres per second squared. Fall time is {time} seconds. What is the height in metres?",
        ),
        (
            "המהירות גדלה מ־0 ל־gt; המהירות הממוצעת היא gt/2. כפל בזמן נותן h=gt²/2 במודל הנתון.",
            "Speed rises from 0 to gt, so average speed is gt/2. Multiplying by time gives h=gt²/2 in the stated model.",
        ),
        (
            "בונה מדידה צריך לקשר את הנמדד לגודל המבוקש.",
            "A measurement model must connect the observation to the requested quantity.",
        ),
        "g time",
        [(10, 2), (10, "1/2"), (8, 3), (10, 0), (6, "3/2")],
        lambda d: F(d["g"]) * F(d["time"]) ** 2 / 2,
        2,
    )

    add(
        "impact_sound",
        [248],
        ("שמיעת הפגיעה מוסיפה זמן חזרה", "Hearing impact adds return travel time"),
        (
            "בניסוי מחשבתי, נפילה מגובה {height} מטר נמשכת {fall} שניות. צופה בגג עוצר שעון כשהוא שומע את הפגיעה. מה הקריאה, אם הקול חוזר אנכית במהירות {sound} מטר לשנייה וכל השהיה אחרת אפס?",
            "In a thought experiment, falling {height} metres takes {fall} seconds. A rooftop observer stops timing upon hearing impact. What is the reading if sound returns vertically at {sound} metres per second and all other delays are zero?",
        ),
        (
            "השעון מודד את זמן הנפילה ועוד זמן תנועת הקול חזרה, h/c. אין להציב את זמן השמיעה ישירות בנוסחת הנפילה.",
            "The timer measures fall time plus the sound's return time, h/c. Do not substitute the hearing time directly into the fall formula.",
        ),
        ("מסלול הדיווח עשוי להוסיף השהיה למדידה.", "The reporting path may add latency to a measurement."),
        "height fall sound",
        [(20, 2, 300), (5, 1, 100), (45, 3, 300), (0, 0, 300), (80, 4, 320)],
        lambda d: F(d["fall"]) + F(d["height"], d["sound"]),
        2,
    )

    add(
        "height_uncertainty",
        [248, 159],
        ("אי־ודאות בזמן אינה לינארית בגובה", "Time uncertainty is nonlinear in height"),
        (
            "במודל נפילה ממנוחה ללא גרר, g={g}. זמן הנפילה נמצא בטווח [{low},{high}] שניות, כולל הקצוות. מה רוחב טווח הגבהים האפשריים, במטרים?",
            "For a drag-free fall from rest, g={g}. Fall time lies in [{low},{high}] seconds, including endpoints. What is the width of the possible height interval, in metres?",
        ),
        (
            "הגובה עולה עם הזמן הלא־שלילי. מחשבים g·high²/2 פחות g·low²/2, ולא ריבוע של הפרש הזמנים.",
            "Height increases with nonnegative time. Compute g·high²/2 minus g·low²/2, not the square of the time difference.",
        ),
        (
            "מעבירים את גבולות המדידה דרך המודל עצמו.",
            "Propagate measurement bounds through the actual model.",
        ),
        "g low high",
        [(10, 1, 2), (10, 2, 2), (8, 0, 1), (10, "3/2", "5/2"), (6, 2, 3)],
        lambda d: F(d["g"]) * (F(d["high"]) ** 2 - F(d["low"]) ** 2) / 2,
        3,
    )

    add(
        "fuel_units",
        [244],
        ("יחידת הדרך משנה את משמעות הצריכה", "Distance units change consumption meaning"),
        (
            "מיכל מכיל {fuel} ליטר. הצריכה היא {rate} ליטר לכל {unit} מטר, קבועה וללא רזרבה. מה טווח הנסיעה במטרים?",
            "A tank contains {fuel} L. Consumption is {rate} L per {unit} m, constant with no reserve. What is travel range in metres?",
        ),
        (
            "מוצאים כמה מנות דלק זמינות ומכפילים במרחק למנה. שומרים את יחידת הדרך המפורשת ולא מניחים קילומטרים.",
            "Find the number of fuel portions available and multiply by distance per portion. Preserve the stated distance unit instead of assuming kilometres.",
        ),
        ("יחידות הן חלק מהנתון, לא קישוט.", "Units are part of the data."),
        "fuel rate unit",
        [(50, 1, 1), (5, 1, 1000), (9, 3, 100), (0, 2, 1000), (3, 2, 1)],
        lambda d: F(d["fuel"] * d["unit"], d["rate"]),
        2,
    )

    add(
        "midpoint_pair_count",
        [71],
        ("מחלקות זוגיות סופרות אמצעים שלמים", "Parity classes count integer midpoints"),
        (
            "הנקודות השלמות הן {points}. כמה זוגות של נקודות שונות במיקומן ברשימה נותנים אמצע עם כל הקואורדינטות שלמות? כל זוג לא מסודר נספר פעם אחת.",
            "Integer points are {points}. How many pairs of distinct list entries have an integer midpoint in every coordinate? Count each unordered pair once.",
        ),
        (
            "אמצע שלם מתקבל כששתי הנקודות שוות בזוגיות בכל קואורדינטה. בכל מחלקה בגודל c יש c(c−1)/2 זוגות.",
            "An integer midpoint requires matching parity in every coordinate. A class of size c contributes c(c−1)/2 pairs.",
        ),
        (
            "חתימה משותפת הופכת בדיקה זוגית לספירה בקבוצות.",
            "A shared signature turns pair checking into grouped counting.",
        ),
        "points",
        [
            ([[0, 0], [2, 4], [1, 1]],),
            ([[0], [2], [4], [1]],),
            ([[0, 0], [0, 1], [1, 0], [1, 1]],),
            ([[2, 2], [4, 6], [8, 0]],),
            ([[0, 0, 0], [2, 2, 2], [1, 1, 1], [3, 3, 3]],),
        ],
        lambda d: sum(
            c * (c - 1) // 2 for c in Counter(tuple(x % 2 for x in p) for p in d["points"]).values()
        ),
        3,
    )

    add(
        "parity_group_guarantee",
        [71],
        ("להבטיח יותר מזוג באותה מחלקה", "Guaranteeing more than a pair in one class"),
        (
            "מוציאים נקודות שלמות שונות בממד {dimension}. כמה נקודות לפחות מבטיחות {group} נקודות בעלות אותה חתימת זוגיות? חתימה מציינת זוגי או אי־זוגי בכל קואורדינטה.",
            "Draw distinct integer points in dimension {dimension}. How many guarantee {group} points sharing one parity signature? A signature records even or odd in every coordinate.",
        ),
        (
            "יש 2^d חתימות. אפשר לפזר k−1 בכל אחת בלי להגיע ל־k; הנקודה הבאה מכריחה קבוצה בגודל המבוקש.",
            "There are 2^d signatures. Put k−1 in each without reaching k; the next point forces the requested group size.",
        ),
        ("עקרון שובך היונים נותן גם הבטחת ריבוי.", "The pigeonhole principle also guarantees larger groups."),
        "dimension group",
        [(2, 3), (1, 4), (3, 2), (2, 1), (3, 3)],
        lambda d: 2 ** d["dimension"] * (d["group"] - 1) + 1,
        3,
    )

    add(
        "midpoint_free_subset",
        [71],
        ("לבחור בלי זוג אמצע שלם", "Selecting without an integer-midpoint pair"),
        (
            "מתוך הנקודות {points}, מה גודל תת־קבוצה מרבי שאין בה אף זוג בעל אמצע שלם בכל קואורדינטה?",
            "From points {points}, what is the largest subset containing no pair whose midpoint is integral in every coordinate?",
        ),
        (
            "מותר לבחור לכל היותר נקודה אחת מכל חתימת זוגיות. בחירת נציגה מכל חתימה שמופיעה משיגה את החסם.",
            "Choose at most one point per parity signature. One representative from every occurring signature attains the bound.",
        ),
        (
            "איסור על זוגות יכול להפוך לבחירת נציגים.",
            "A forbidden-pair condition can become representative selection.",
        ),
        "points",
        [
            ([[0, 0], [2, 2], [1, 0]],),
            ([[0], [2], [4]],),
            ([[0, 0], [0, 1], [1, 0], [1, 1]],),
            ([[5]],),
            ([[0, 0, 0], [2, 2, 2], [1, 1, 1]],),
        ],
        lambda d: len({tuple(x % 2 for x in p) for p in d["points"]}),
        3,
    )

    worlds = [
        ([[1, 10], [1, 11], [2, 10]],),
        ([[1, 10], [2, 11], [3, 12]],),
        ([[1, 10], [1, 11], [2, 10], [2, 11]],),
        ([[1, 10]],),
        ([[1, 10], [1, 12], [2, 12], [3, 13], [3, 14]],),
    ]
    add(
        "knowledge_unique",
        [46],
        ("ידיעה היא יחידות בקבוצת האפשרויות", "Knowledge means uniqueness among possibilities"),
        (
            "העולמות האפשריים הם זוגות (חודש,יום): {worlds}. אדם יודע רק את החודש. בכמה מהעולמות הוא יכול לזהות לבדו את הזוג המדויק? הרשימה ידועה לכולם.",
            "Possible worlds are (month,day) pairs: {worlds}. A person knows only the month. In how many worlds can they identify the exact pair alone? Everyone knows the list.",
        ),
        (
            "מקבצים לפי החודש הידוע. ידיעה מלאה מתקבלת רק בקבוצה המכילה עולם אחד; תחושה שהאפשרות סבירה אינה ידיעה.",
            "Group worlds by the known month. Complete knowledge occurs only in singleton groups; a likely possibility is not knowledge.",
        ),
        (
            "בודקים ידיעה מול כל המצבים שאינם ניתנים להבחנה.",
            "Check knowledge against all indistinguishable states.",
        ),
        "worlds",
        worlds,
        lambda d: sum(c == 1 for c in Counter(a for a, _ in d["worlds"]).values()),
        3,
    )

    add(
        "public_ignorance",
        [46, 33],
        ("הודעת חוסר ידיעה מסננת עולמות", "A public ignorance statement filters worlds"),
        (
            "הזוגות האפשריים הם {worlds}. אדם יודע רק את הרכיב הראשון ומודיע אמת: איני יודע את הזוג. כמה עולמות נשארים אפשריים אחרי ההודעה?",
            "Possible pairs are {worlds}. A person knows only the first component and truthfully announces: I do not know the pair. How many worlds remain possible after this announcement?",
        ),
        (
            "מוחקים עולמות שהרכיב הראשון שלהם מופיע רק פעם אחת. בקבוצות גדולות חוסר הידיעה תואם לכל עולם. אפס עולמות אומר שההודעה סותרת את האפשרויות הידועות.",
            "Remove worlds whose first component occurs only once. In larger groups, ignorance fits every member. Zero worlds means the announcement contradicts the known possibilities.",
        ),
        (
            "תוכן ההודעה כולל גם מה שהדובר אינו יודע.",
            "An announcement can reveal what the speaker does not know.",
        ),
        "worlds",
        worlds,
        lambda d: sum(Counter(a for a, _ in d["worlds"])[a] > 1 for a, _ in d["worlds"]),
        3,
    )

    add(
        "knows_other_ignorance",
        [46],
        ("ודאות על אחר דורשת לבדוק את כל האפשרויות", "Certainty about another needs every possibility"),
        (
            "זוגות אפשריים: {worlds}. A יודע רק רכיב ראשון; B רק שני. בכמה עולמות A יודע בוודאות ש־B אינו יודע את הזוג, עוד לפני כל הודעה?",
            "Possible pairs: {worlds}. A knows only the first component; B only the second. In how many worlds is A certain that B cannot identify the pair, before any announcement?",
        ),
        (
            "לכל קבוצה של A בודקים את כל הרכיבים השניים שבה. אם אפילו אחד מופיע רק פעם ברשימה הכוללת, A אינו יכול להיות בטוח בחוסר הידיעה של B.",
            "For each A-group inspect every second component in it. If any occurs only once globally, A cannot be certain of B's ignorance.",
        ),
        (
            "לדעת שאחר אינו יודע היא טענה על כל האפשרויות שלך.",
            "Knowing another is ignorant is a claim about all your possibilities.",
        ),
        "worlds",
        worlds,
        lambda d: sum(
            all(Counter(b for _, b in d["worlds"])[b] > 1 for aa, b in d["worlds"] if aa == a)
            for a, _ in d["worlds"]
        ),
        4,
    )

    add(
        "hat_worlds",
        [33],
        ("מלאי כובעים מצמצם עולמות אפשריים", "Hat inventory restricts possible worlds"),
        (
            "נותרו {white} כובעים לבנים ו־{black} שחורים לחלוקה ל־{people} אנשים מסודרים. כובעים מאותו צבע אינם מובחנים, ואין חובה להשתמש בכולם. כמה רצפי צבעים אפשריים?",
            "There remain {white} white and {black} black hats for {people} ordered people. Same-colored hats are indistinguishable, and unused hats are allowed. How many color sequences are possible?",
        ),
        (
            "לכל מספר לבנים חוקי בוחרים את מיקומיהם. המלאי מגביל גם את הלבנים וגם את השחורים; אין לספור זהות של כובעים מאותו צבע.",
            "For every feasible white count, choose its positions. Inventory constrains both colors; do not count identities of same-colored hats.",
        ),
        (
            "כמות הפריטים ויכולת ההבחנה ביניהם קובעות את עולם האפשרויות.",
            "Inventory and distinguishability determine the possible worlds.",
        ),
        "white black people",
        [(3, 2, 3), (0, 3, 2), (1, 1, 3), (2, 2, 0), (2, 2, 4)],
        lambda d: sum(
            math.comb(d["people"], w)
            for w in range(d["people"] + 1)
            if w <= d["white"] and d["people"] - w <= d["black"]
        ),
        3,
    )

    add(
        "implication_counterexamples",
        [283],
        ("מתי מערכת גרירות נכשלת", "When a system of implications fails"),
        (
            "יש {n} משתנים בוליאניים ממוספרים מ־0. הכללים (a,b) ב־{rules} פירושם אם a=1 אז b=1. כמה השמות מתוך 2^{n} מפרות לפחות כלל אחד?",
            "There are {n} Boolean variables indexed from 0. Rules (a,b) in {rules} mean if a=1 then b=1. How many of the 2^{n} assignments violate at least one rule?",
        ),
        (
            "גרירה נכשלת רק במצב 1→0. סופרים כל השמה פעם אחת גם אם היא מפרה כמה כללים; אין לחבר הפרות חופפות.",
            "An implication fails only on 1→0. Count each assignment once even if it breaks several rules; overlapping violations cannot simply be added.",
        ),
        (
            "דוגמה נגדית צריכה לקיים את התנאי ולהפר את המסקנה.",
            "A counterexample must satisfy the premise and violate the conclusion.",
        ),
        "n rules",
        [(3, [[0, 1], [1, 2]]), (2, [[0, 1]]), (2, [[0, 0]]), (3, [[0, 1], [1, 0]]), (3, [])],
        lambda d: sum(
            any(bits[a] and not bits[b] for a, b in d["rules"]) for bits in it.product((0, 1), repeat=d["n"])
        ),
        3,
    )

    add(
        "forced_true",
        [283],
        ("מסקנה הכרחית משותפת לכל מודל חוקי", "A necessary conclusion holds in every legal model"),
        (
            "משתנים 0..{n} לא כולל {n}. גרירות (a,b): {rules}; ערכים ידועים (אינדקס,ערך): {known}. כמה משתנים חייבים להיות 1 בכל השמה המקיימת את הכל? נתונים אלה עקביים.",
            "Variables are 0..{n}, excluding {n}. Implications (a,b): {rules}; known (index,value) pairs: {known}. How many variables must equal 1 in every satisfying assignment? These data are consistent.",
        ),
        (
            "שומרים רק השמות שמקיימות את העובדות והגרירות, וסופרים משתנים שהם 1 בכולן. היפוך גרירה אינו כלל תקף.",
            "Keep assignments satisfying facts and implications, then count variables equal to 1 in all of them. Reversing an implication is not valid.",
        ),
        (
            "אפשרי אינו הכרחי; מסקנה הכרחית שורדת כל מודל חוקי.",
            "Possible is not necessary; necessary conclusions survive every legal model.",
        ),
        "n rules known",
        [
            (3, [[0, 1], [1, 2]], [[0, 1]]),
            (3, [[0, 1], [1, 2]], [[2, 1]]),
            (3, [[0, 1], [1, 2]], [[2, 0]]),
            (3, [[0, 1], [1, 0]], [[1, 1]]),
            (4, [[0, 1], [2, 3]], [[0, 1], [2, 0]]),
        ],
        lambda d: (lambda models: sum(all(bits[i] for bits in models) for i in range(d["n"])))(
            [
                bits
                for bits in it.product((0, 1), repeat=d["n"])
                if all(bits[i] == v for i, v in d["known"])
                and all(not bits[a] or bits[b] for a, b in d["rules"])
            ]
        ),
        4,
    )

    add(
        "quantified_batches",
        [159],
        ("כל פריט לעומת לפחות פריט אחד", "Every item versus at least one item"),
        (
            "אצוות המדידות הן {batches}. אצווה מתקבלת אם כל ערכיה לפחות {low}, ולפחות אחד מערכיה הוא {high} ומעלה. כמה אצוות מתקבלות? אצווה ריקה אינה עומדת בתנאי השני.",
            "Measurement batches are {batches}. Accept a batch if every value is at least {low} and at least one value is {high} or greater. How many batches pass? An empty batch fails the second condition.",
        ),
        (
            "בודקים בנפרד תנאי על כל האיברים ותנאי קיום. הצלחה של איבר אחד אינה מתקנת איבר אחר שמתחת לסף התחתון.",
            "Check the universal and existence conditions separately. One high value cannot repair another value below the lower bound.",
        ),
        ("מילות כל וקיים מגדירות דרישות שונות.", "All and exists express different requirements."),
        "batches low high",
        [
            ([[2, 5], [1, 9], [3, 3]], 2, 5),
            ([[], [4], [2, 4]], 2, 4),
            ([[3, 3], [2, 3], [4]], 3, 3),
            ([[0, 10], [5, 6]], 1, 7),
            ([[1, 5], [5, 5], [2, 7]], 1, 5),
        ],
        lambda d: sum(all(x >= d["low"] for x in b) and any(x >= d["high"] for x in b) for b in d["batches"]),
        2,
    )

    add(
        "measurement_intersection",
        [159],
        ("מדידות של אותו גודל צריכות להתיישב", "Measurements of one quantity must agree"),
        (
            "גודל שלם יחיד חייב להיות בתוך כל הטווחים הסגורים {intervals}. כמה ערכים שלמים אפשריים? אפס פירושו שהטווחים אינם עקביים יחד.",
            "One integer quantity must lie inside every closed interval in {intervals}. How many integer values are possible? Zero means the intervals are mutually inconsistent.",
        ),
        (
            "החיתוך מתחיל בגבול התחתון הגדול ביותר ומסתיים בעליון הקטן ביותר. בטווח שלם סגור מוסיפים 1 להפרש, ורצפה היא אפס.",
            "The intersection starts at the largest lower bound and ends at the smallest upper bound. A closed integer interval has endpoint difference plus 1, floored at zero.",
        ),
        (
            "מידע על אותו נעלם מצטבר בחיתוך אילוצים.",
            "Information about one unknown combines by intersecting constraints.",
        ),
        "intervals",
        [
            ([[1, 5], [3, 7]],),
            ([[1, 2], [3, 4]],),
            ([[0, 2], [2, 5]],),
            ([[-3, 3], [-1, 1], [0, 2]],),
            ([[4, 4]],),
        ],
        lambda d: max(0, min(hi for _, hi in d["intervals"]) - max(lo for lo, _ in d["intervals"]) + 1),
        2,
    )

    add(
        "sum_uncertainty",
        [159],
        ("שגיאות חסומות מצטברות במקרה הגרוע", "Bounded errors accumulate in the worst case"),
        (
            "ערכי רכיבים נמצאים בטווחים {intervals}; כל שילוב ערכים אפשרי. מה רוחב הטווח האפשרי של סכום הרכיבים? אין הנחת אקראיות או ביטול שגיאות.",
            "Component values lie in intervals {intervals}; every combination is possible. What is the width of the possible sum interval? Assume neither randomness nor error cancellation.",
        ),
        (
            "הסכום הקטן מתקבל בכל הגבולות התחתונים, והגדול בכל העליונים. רוחב טווח הסכום הוא סכום רוחבי הטווחים.",
            "The minimum uses all lower bounds and the maximum all upper bounds. The sum interval's width is the sum of individual widths.",
        ),
        (
            "חסם ודאי אינו חיבור סטטיסטי של שגיאות.",
            "A deterministic bound is not a statistical error combination.",
        ),
        "intervals",
        [
            ([[1, 3], [4, 5]],),
            ([[2, 2], [7, 7]],),
            ([[-2, 2], [-1, 1]],),
            ([[0, 1], [0, 1], [0, 1]],),
            ([[-5, -2]],),
        ],
        lambda d: sum(hi - lo for lo, hi in d["intervals"]),
        2,
    )

    add(
        "common_bias",
        [159, 154],
        ("הפרש יכול לבטל הטיה משותפת", "A difference can cancel shared bias"),
        (
            "שתי קריאות הן X={x}, Y={y}. המודל הוא X=a+b ו־Y=c+b, עם אותה הטיה לא ידועה b וללא שגיאה נוספת. מה a−c?",
            "Readings are X={x}, Y={y}. The model is X=a+b and Y=c+b, with the same unknown bias b and no other error. What is a−c?",
        ),
        (
            "מחסרים את שתי המשוואות. ההטיה המשותפת מתבטלת בדיוק, אף שלא ניתן להסיק ממנה את כל אחד מהערכים בנפרד.",
            "Subtract the equations. The shared bias cancels exactly, although the individual true values cannot be recovered from this alone.",
        ),
        (
            "לעתים הפרש ניתן לזיהוי גם כשהערכים עצמם לא.",
            "Sometimes a difference is identifiable while individual values are not.",
        ),
        "x y",
        [(17, 12), (8, 8), (3, 10), (-2, -7), (0, 4)],
        lambda d: d["x"] - d["y"],
        2,
    )

    add(
        "minimax_experiment",
        [159, 154],
        ("בדיקה טובה מפצלת את המקרה הגרוע", "A good test splits the worst case"),
        (
            "כל שורה ב־{tests} מציגה את תוצאתה של בדיקה אפשרית עבור אותן השערות, לפי סדר. בוחרים בדיקה אחת. מה המספר המזערי של השערות שעלולות להישאר במקרה הגרוע אחרי התוצאה?",
            "Each row in {tests} lists one possible test's outcomes for the same ordered hypotheses. Choose one test. What is the smallest worst-case number of hypotheses remaining after its result?",
        ),
        (
            "בכל בדיקה מקבצים השערות לפי התוצאה ומוצאים את הקבוצה הגדולה ביותר. בוחרים בדיקה שהקבוצה הגדולה שלה קטנה ככל האפשר.",
            "For each test group hypotheses by outcome and find its largest group. Choose the test whose largest group is smallest.",
        ),
        (
            "למזעור המקרה הגרוע מאזנים את ענפי המידע.",
            "Minimizing the worst case requires balancing information branches.",
        ),
        "tests",
        [
            ([[0, 0, 0, 1], [0, 0, 1, 1]],),
            ([[0, 0, 0], [0, 1, 2]],),
            ([[0, 0], [1, 1]],),
            ([[0, 0, 1, 1, 2], [0, 0, 0, 1, 2]],),
            ([[0, 1, 0, 1, 0, 1], [0, 1, 2, 0, 1, 2]],),
        ],
        lambda d: min(max(Counter(t).values()) for t in d["tests"]),
        3,
    )

    add(
        "expected_survivors",
        [159, 154],
        ("עלות מידע ממוצעת שוקלת את גודל הענף", "Average information cost weights branch size"),
        (
            "השערות שוות הסתברות מניבות תוצאות בדיקה {outcomes}, ערך אחד לכל השערה. אחרי הבדיקה שומרים את כל ההשערות המתאימות לתוצאה. מה תוחלת מספר ההשערות שנותרו?",
            "Equally likely hypotheses produce test outcomes {outcomes}, one value per hypothesis. After testing, retain every hypothesis matching the result. What is the expected number of remaining hypotheses?",
        ),
        (
            "ענף בגודל c מתרחש בסיכוי c/N ומשאיר c השערות. מסכמים c²/N על כל התוצאות השונות.",
            "A branch of size c occurs with probability c/N and leaves c hypotheses. Sum c²/N across distinct outcomes.",
        ),
        (
            "ענף גדול גם סביר יותר וגם משאיר יותר אי־ודאות.",
            "A large branch is both more likely and leaves more uncertainty.",
        ),
        "outcomes",
        [([0, 0, 0, 1],), ([0, 0, 1, 1],), ([0, 1, 2],), ([1, 1, 1],), ([0, 0, 1, 2, 2],)],
        lambda d: F(sum(c * c for c in Counter(d["outcomes"]).values()), len(d["outcomes"])),
        3,
    )

    add(
        "code_distance",
        [73],
        ("הבדל בין קודים קובע עמידות לשגיאה", "Code separation determines error tolerance"),
        (
            "חתימות הבדיקה החוקיות הן {codes}, מחרוזות בינאריות באותו אורך. מה מרחק המינג המזערי בין שתי חתימות שונות? מרחק המינג הוא מספר מיקומי הביט השונים.",
            "Legal test signatures are {codes}, equal-length binary strings. What is the minimum Hamming distance between two different signatures? Hamming distance counts differing bit positions.",
        ),
        (
            "משווים כל זוג חתימות וסופרים מיקומים שונים. המינימום, ולא הממוצע, קובע את הזוג שהכי קשה להבחין בו תחת שגיאות.",
            "Compare every signature pair and count differing positions. The minimum, not the average, identifies the pair hardest to distinguish under errors.",
        ),
        ("עמידות נקבעת לפי הזוג הקרוב ביותר.", "Robustness is determined by the closest pair."),
        "codes",
        [
            (["000", "111"],),
            (["000", "001", "110"],),
            (["0000", "1100", "0011"],),
            (["010", "101", "111"],),
            (["00000", "11110", "00111"],),
        ],
        lambda d: min(
            sum(a != b for a, b in zip(x, y, strict=True)) for x, y in it.combinations(d["codes"], 2)
        ),
        3,
    )

    add(
        "erased_observations",
        [73, 159],
        ("מידע חסר אינו תוצאה שלילית", "Missing information is not a negative result"),
        (
            "חתימות אפשריות: {codes}. התצפית היא `{observed}`, שבה x מציין ביט שלא נמדד. כמה חתימות עדיין מתאימות לכל הביטים הידועים?",
            "Possible signatures: {codes}. The observation is `{observed}`, where x denotes an unmeasured bit. How many signatures remain consistent with every known bit?",
        ),
        (
            "משווים רק מיקומים שנמדדו. הסימון x תואם גם 0 וגם 1; אסור להתייחס אליו כאפס.",
            "Compare only measured positions. The marker x matches both 0 and 1; it must not be treated as zero.",
        ),
        ("חוסר תצפית אינו ראיה להיעדר.", "An absent observation is not evidence of absence."),
        "codes observed",
        [
            (["000", "010", "110", "111"], "x1x"),
            (["00", "01", "10"], "xx"),
            (["00", "11"], "01"),
            (["000", "001", "100"], "00x"),
            (["010", "101"], "010"),
        ],
        lambda d: sum(
            all(o == "x" or o == c for o, c in zip(d["observed"], word, strict=True)) for word in d["codes"]
        ),
        2,
    )

    add(
        "joint_information",
        [159, 154],
        ("שתי בדיקות עשויות לשאול אותו דבר", "Two tests may ask the same thing"),
        (
            "עבור אותן השערות לפי סדר, תוצאות בדיקה A הן {a} ותוצאות B הן {b}. מבצעים את שתיהן ללא רעש. לכמה קבוצות מובחנות מתחלקות ההשערות לפי זוג התוצאות?",
            "For the same ordered hypotheses, test A outcomes are {a} and test B outcomes are {b}. Perform both noiselessly. Into how many distinguishable groups do the hypotheses split by their outcome pairs?",
        ),
        (
            "מונים זוגות תוצאות שונים. מכפלת מספר התוצאות בכל בדיקה היא רק חסם; אם הבדיקות תלויות לא כל זוג מתקבל.",
            "Count distinct outcome pairs. Multiplying separate outcome counts gives only a bound; dependent tests need not realize every pair.",
        ),
        (
            "יותר בדיקות אינן תמיד יותר מידע עצמאי.",
            "More tests do not always provide more independent information.",
        ),
        "a b",
        [
            ([0, 0, 1, 1], [0, 0, 1, 1]),
            ([0, 0, 1, 1], [0, 1, 0, 1]),
            ([0, 0, 0], [0, 1, 2]),
            ([0, 1, 2], [2, 1, 0]),
            ([0, 0, 1, 1, 1], [0, 1, 0, 1, 2]),
        ],
        lambda d: len(set(zip(d["a"], d["b"], strict=True))),
        3,
    )

    add(
        "capacity_slack",
        [149],
        ("כוח אדם פנוי נקבע בעומס השיא", "Spare workforce is determined at peak demand"),
        (
            "יש {capacity} עובדים. דרישות הן (התחלה,סיום,עובדים): {jobs}, בטווחים חצי־פתוחים `[התחלה,סיום)`. מה מרווח הקיבולת המזערי לאורך הזמן? ערך שלילי מציין מחסור.",
            "There are {capacity} workers. Jobs (start,end,workers) are {jobs}, on half-open intervals `[start,end)`. What is minimum capacity slack over time? A negative value indicates a shortage.",
        ),
        (
            "מסכמים דרישות פעילות בכל קטע זמן ומחסרים את השיא מהקיבולת. עבודה שמסתיימת בזמן t אינה חופפת לעבודה שמתחילה ב־t.",
            "Sum active demands on each time segment and subtract the peak from capacity. A job ending at t does not overlap one starting at t.",
        ),
        (
            "מרווח קיבולת חיובי הוא הבטחה רק ביחס למודל הדרישות.",
            "Positive capacity slack is a guarantee only for the stated demand model.",
        ),
        "capacity jobs",
        [
            (6, [[0, 2, 3], [1, 3, 4]]),
            (5, [[0, 1, 5], [1, 2, 5]]),
            (4, [[0, 3, 1], [1, 2, 2]]),
            (3, []),
            (2, [[0, 4, 0], [2, 3, 3]]),
        ],
        lambda d: (
            d["capacity"]
            - max([0] + [sum(w for a, b, w in d["jobs"] if a <= t < b) for t in {a for a, _, _ in d["jobs"]}])
        ),
        3,
    )

    add(
        "deadline_capacity",
        [149],
        ("דדליין מוקדם דורש בדיקה משלו", "An early deadline needs its own capacity check"),
        (
            "עבודות יחידה זמינות בזמן 0, עם דדליינים שלמים {deadlines}. כל עובד מבצע עבודה אחת בכל משבצת זמן שלמה. כמה עובדים לפחות דרושים לסיום כל עבודה עד הדדליין שלה? אין תלות בין העבודות.",
            "Unit jobs are available at time 0, with integer deadlines {deadlines}. Each worker completes one job per integer time slot. What is the minimum workers needed to finish every job by its deadline? Jobs are independent.",
        ),
        (
            "לכל זמן t סופרים עבודות שהדדליין שלהן עד t ומחלקים ב־t כלפי מעלה. החסם הגדול ביותר מספיק באמצעות סדר דדליינים עולה.",
            "For every t count jobs due by t and round that count divided by t upward. The largest bound is attainable by earliest-deadline order.",
        ),
        (
            "קיבולת כוללת מספיקה רק אם היא זמינה לפני כל דדליין.",
            "Total capacity suffices only when available before every deadline.",
        ),
        "deadlines",
        [([1, 1, 3, 3],), ([2, 2, 2],), ([1, 2, 3],), ([3, 3, 3, 3],), ([],)],
        lambda d: max(
            [0] + [math.ceil(F(sum(x <= t for x in d["deadlines"]), t)) for t in set(d["deadlines"])]
        ),
        4,
    )

    add(
        "preemptive_work",
        [149],
        ("שעות עבודה אינן מספר עבודות", "Work hours are not job count"),
        (
            "דרישות העבודה הן {work} שעות. כולן זמינות עכשיו ודדליין משותף בעוד {deadline} שעות. מותר לפצל ולעצור עבודה, אך כל עבודה משתמשת בעובד אחד לכל היותר בכל רגע. כמה עובדים לפחות דרושים? כל עבודה אינה ארוכה מהדדליין.",
            "Jobs require {work} hours, all available now with deadline in {deadline} hours. Preemption is allowed, but each job uses at most one worker at a time. What is the minimum workers needed? Each job fits individually before the deadline.",
        ),
        (
            "מחלקים את סך שעות העבודה בחלון הזמן ומעגלים למעלה. תחת פיצול בזמן, והגבלת אורך כל עבודה, ניתן להשיג את החסם בלוח זמנים ללא הרצה מקבילית לאותה עבודה.",
            "Divide total work by the time window and round upward. With preemption and each job's duration bounded by the deadline, a nonparallel schedule attains this bound.",
        ),
        (
            "חסם עומס הופך למספיק רק תחת הנחות תזמון מתאימות.",
            "A workload bound is sufficient only under appropriate scheduling assumptions.",
        ),
        "work deadline",
        [([3, 3, 3], 5), ([4, 4], 4), ([1, 1, 1], 5), ([], 3), ([2, 4, 4], 5)],
        lambda d: math.ceil(F(sum(d["work"]), d["deadline"])),
        4,
    )

    add(
        "route_deadlines",
        [161],
        ("מסלול קצר אינו בהכרח עומד בזמן", "A short route may still miss a deadline"),
        (
            "מעלית מתחילה בקומה {start} בזמן 0. מבקרת לפי הסדר בבקשות (קומה,דדליין) {requests}. מעבר קומה עולה יחידת זמן, עצירה אינה עולה זמן. לכמה בקשות היא מגיעה עד הדדליין, כולל שוויון?",
            "An elevator starts at floor {start} at time 0. It visits ordered requests (floor,deadline) {requests}. Moving one floor costs one time unit; stops take no time. How many requests are reached by their deadlines, including equality?",
        ),
        (
            "צוברים זמן נסיעה לאורך הסדר הנתון, ובכל הגעה משווים לדדליין של אותה בקשה. איחור קודם אינו מאפס את השעון.",
            "Accumulate travel time along the given order and compare each arrival with its own deadline. A previous delay does not reset the clock.",
        ),
        (
            "יש לבדוק זמני הגעה לכל בקשה, לא רק אורך כולל.",
            "Check each request's arrival time, not only total route length.",
        ),
        "start requests",
        [
            (0, [[3, 3], [1, 4], [4, 8]]),
            (2, [[2, 0], [3, 1]]),
            (0, [[4, 3], [5, 6]]),
            (5, [[1, 4], [4, 6]]),
            (0, []),
        ],
        lambda d: sum(
            sum(
                abs(a - b)
                for a, b in zip(
                    [d["start"]] + [r[0] for r in d["requests"][:i]],
                    [r[0] for r in d["requests"][: i + 1]],
                    strict=True,
                )
            )
            <= deadline
            for i, (_, deadline) in enumerate(d["requests"])
        ),
        3,
    )

    add(
        "order_implications",
        [9, 190],
        ("תוצאות השוואה גוררות סדרים נוספים", "Comparison results imply further ordering"),
        (
            "ל־{n} מתחרים מהירויות שונות. תוצאות (a,b) ב־{faster} אומרות ש־a מהיר מ־b. כמה זוגות סדורים שונים מוכרעים לטובת הראשון, כולל מסקנות מעבריות? הנתונים ללא סתירות.",
            "There are {n} competitors with distinct speeds. Results (a,b) in {faster} say a is faster than b. How many distinct ordered pairs are determined in favor of the first, including transitive conclusions? The data are consistent.",
        ),
        (
            "שרשרת השוואות תקפה גוררת שהראשון מהיר מהאחרון. מאחדים את כל הזוגות המוכחים, בלי לספור זוג פעמיים או להסיק בין בלתי־ניתנים להשוואה.",
            "A valid comparison chain implies its first is faster than its last. Union all proved pairs, without double-counting or ordering incomparable competitors.",
        ),
        (
            "טרנזיטיביות מוסיפה מסקנות אך לא משלימה בהכרח סדר מלא.",
            "Transitivity adds conclusions without necessarily completing a total order.",
        ),
        "n faster",
        [
            (4, [[0, 1], [1, 2], [2, 3]]),
            (4, [[0, 1], [0, 2], [0, 3]]),
            (4, [[0, 1], [2, 3]]),
            (3, []),
            (4, [[0, 1], [0, 2], [1, 3], [2, 3]]),
        ],
        lambda d: (lambda rel: len(rel))(_closure(d["faster"])),
        3,
    )

    return cards, rows, checks


def build():
    """Expose the common quiz-authoring API without writing generated files."""
    _, rows, checks = build_bundle()
    return rows, checks


def _closure(edges):
    relation = {tuple(edge) for edge in edges}
    while True:
        expanded = relation | {(a, d) for a, b in relation for c, d in relation if b == c}
        if expanded == relation:
            return relation
        relation = expanded


if __name__ == "__main__":
    cards, rows, checks = build_bundle()
    for path, value in [
        (CONTENT, cards),
        (OUT / "reasoning_700.json", rows),
        (OUT / "reasoning_700.checks.json", checks),
    ]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Wrote {len(cards)} cards and {len(rows)} draft variants")
