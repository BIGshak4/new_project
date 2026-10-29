"""Author and check five short, bilingual quiz variants for hardware cards 61--125.

These are AI-authored drafts. Running the checks is not human approval.
The main seed is assembled separately; this script owns only its batch and evidence.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content"
SOURCES = {}
for filename in ("fundamentals-hardware-expansion.json", "fundamentals-hardware-250.json"):
    SOURCES.update({q["id"]: q for q in json.loads((CONTENT / filename).read_text(encoding="utf-8"))})
QUESTIONS = []
CHECKS = []


def loc(he, en=None):
    return {"he": str(he), "en": str(he if en is None else en)}


def emit(source, variant, he, en, options, explanation, method, inputs, expected=None):
    """Options arrive correct first; rotate deterministically to balance answer slots."""
    source_key = f"quick-hw-{source:02}"
    assert len(options) == 4
    options = [loc(*x) if isinstance(x, tuple) else loc(x) for x in options]
    assert all(len({o[lang] for o in options}) == 4 for lang in ("he", "en")), (source, variant)
    shift = (source + variant) % 4
    options = options[-shift:] + options[:-shift] if shift else options
    key = f"{source_key}-v{variant}"
    QUESTIONS.append(
        dict(
            key=key,
            source_key=source_key,
            variant=variant,
            topic=SOURCES[source_key]["topic"],
            status="draft",
            prompt=loc(he, en),
            choices=options,
            correct=shift,
            explanation=loc(*explanation),
        )
    )
    CHECKS.append(
        dict(
            key=key,
            method=method,
            inputs=inputs,
            expected=options[shift] if expected is None else expected,
            correct_text=options[shift],
        )
    )


def numeric(source, variant, he, en, value, explanation, method, inputs, alternatives=None):
    if alternatives is None:
        alternatives = [value + 1, value + 2, max(0, value - 1), value + 3, value + 4]
    other = []
    for x in alternatives:
        if x != value and x not in other:
            other.append(x)
    assert len(other) >= 3, (source, variant, value)
    emit(
        source,
        variant,
        he,
        en,
        [str(value)] + [str(x) for x in other[:3]],
        explanation,
        method,
        inputs,
        value,
    )


def run():
    # 61: full-word equality, independently enumerate the differing bit positions.
    for v, (a, b, w) in enumerate([(3, 3, 4), (3, 7, 4), (10, 2, 4), (0, 0, 5), (17, 19, 5)], 1):
        differences = [i for i in range(w) if ((a >> i) & 1) != ((b >> i) & 1)]
        eq = int(not differences)
        assert eq == int((a ^ b) == 0)
        opts = [
            (f"XOR={a ^ b}; eq={eq}", f"XOR={a ^ b}; eq={eq}"),
            (f"XOR={a ^ b}; eq={1 - eq}", f"XOR={a ^ b}; eq={1 - eq}"),
            (f"XOR={a | b}; eq={eq}", f"XOR={a | b}; eq={eq}"),
            ("בודקים רק את הביט הנמוך", "Check only the lowest bit"),
        ]
        # OR and XOR coincide for disjoint words; use an unrelated wrong numeric result then.
        if opts[2][0] == opts[0][0]:
            opts[2] = (f"XOR={(a ^ b) + 1}; eq={eq}", f"XOR={(a ^ b) + 1}; eq={eq}")
        emit(
            61,
            v,
            f"בשתי מילים לא מסומנות ברוחב {w} ביטים, A={a}, B={b}. מחשבים XOR בין המילים, ואז eq=1 רק אם כל ביטי התוצאה אפס. מה מתקבל?",
            f"For unsigned {w}-bit words A={a}, B={b}, compute their XOR, then set eq=1 only if every result bit is zero. What is obtained?",
            opts,
            (
                f"XOR מסמן את הביטים השונים. התוצאה היא {a ^ b}, ולכן eq={eq}.",
                f"XOR marks differing bits. Its result is {a ^ b}, so eq={eq}.",
            ),
            "enumerate_differing_bits",
            dict(a=a, b=b, width=w),
            dict(xor=a ^ b, eq=eq),
        )

    for v, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (1, 1)], 1):
        # Fifth variant asks the packed value rather than repeating the fourth scenario.
        if v == 5:
            numeric(
                62,
                v,
                "בחצי מחבר ללא נשא נכנס, A=B=1. מצרפים את הביטים בסדר CS, כאשר C הוא הנשיאה. מה הערך העשרוני של CS?",
                "In a half adder with no carry-in, A=B=1. Concatenate CS, with carry C first. What is the decimal value of CS?",
                2,
                ("S=0 ו־C=1, ולכן CS=10 בבינארי, שערכו 2.", "S=0 and C=1, so CS is binary 10, equal to 2."),
                "half_adder_integer_sum",
                dict(a=1, b=1),
                [0, 1, 3],
            )
        else:
            s, c = a ^ b, a & b
            assert 2 * c + s == a + b
            emit(
                62,
                v,
                f"חצי־מחבר מקבל A={a} ו־B={b}, ללא נשא נכנס. מה הזוג S,C?",
                f"A half adder adds A={a} and B={b}, with no carry-in. What is the pair S,C?",
                [f"{s},{c}"]
                + [f"{x},{y}" for x, y in itertools.product((0, 1), repeat=2) if (x, y) != (s, c)],
                (
                    f"סיבית הסכום היא S=A XOR B={s}; סיבית הנשיאה היא C=A AND B={c}.",
                    f"S=A XOR B={s}; C=A AND B={c}.",
                ),
                "half_adder_truth_table",
                dict(a=a, b=b),
                [s, c],
            )

    for v, word in enumerate(["0000", "0001", "0010", "1010", "1000"], 1):
        n = int(word, 2)
        valid = int(n > 0)
        index = n.bit_length() - 1 if valid else None
        correct = (
            ("valid=0; האינדקס חסר משמעות", "valid=0; index is meaningless")
            if not valid
            else (f"valid=1; index={index}", f"valid=1; index={index}")
        )
        candidates = [(f"valid=1; index={i}", f"valid=1; index={i}") for i in range(4)]
        if valid:
            candidates.insert(0, ("valid=0; האינדקס חסר משמעות", "valid=0; index is meaningless"))
        wrong = [o for o in candidates if o != correct][:3]
        emit(
            63,
            v,
            f"מקודד עדיפות בן 4 כניסות בוחר את הביט הפעיל הגבוה ביותר. עבור x={word}, מה צריך לציין ממשק עם valid ואינדקס?",
            f"A 4-input priority encoder selects the highest set bit. For x={word}, what should a valid-plus-index interface report?",
            [correct] + wrong,
            (
                "valid מבחין בין קלט ריק לבין בקשה בביט 0. כשהוא 1, האינדקס מצביע על הביט הפעיל הגבוה ביותר.",
                "valid distinguishes an empty input from a request at bit 0. When valid is 1, the index identifies the highest set bit.",
            ),
            "enumerate_set_positions",
            dict(word=word),
            dict(valid=valid, index=index),
        )

    for v, (g, local) in enumerate([(0, 3), (1, 2), (2, 1), (3, 0), (3, 3)], 1):
        n = 4 * g + local
        assert n == int(f"{g:02b}{local:02b}", 2)
        numeric(
            64,
            v,
            f"מקודד בעל 16 כניסות מחולק ל־4 קבוצות רצופות של 4, ממוספרות מ־0. הקבוצה הפעילה הגבוהה ביותר היא {g}, והאינדקס המקומי בה הוא {local}. מה האינדקס הכללי?",
            f"A 16-input encoder uses 4 consecutive groups of 4, numbered from 0. The highest valid group is {g}, with local index {local}. What is the global index?",
            n,
            (
                f"האינדקס הוא 4×{g}+{local}={n}; מספר הקבוצה הוא החלק העליון.",
                f"The index is 4×{g}+{local}={n}; the group number forms the upper part.",
            ),
            "concatenate_binary_group_and_local",
            dict(group=g, local=local),
        )

    for v, (stuck, seq) in enumerate([(0, "01"), (1, "01"), (0, "10"), (1, "10"), (0, "001")], 1):
        detected = [i + 1 for i, x in enumerate(seq) if int(x) != stuck]
        good = ", ".join(map(str, detected))
        alternatives = [
            good,
            "אין אף דגימה / None",
            ", ".join(map(str, range(1, len(seq) + 1))),
            str(next(i + 1 for i, x in enumerate(seq) if int(x) == stuck)),
        ]
        assert len(set(alternatives)) == 4
        emit(
            65,
            v,
            f"ענף שאמור לשאת x עלול להיות תקוע ב־{stuck}. מזינים את סדרת הדגימות {seq}, משמאל לימין. באילו מספרי דגימה הענף התקין שונה מהענף התקול? מדובר בהפעלה בענף, לפני בדיקת התפשטות למוצא.",
            f"A branch intended to carry x may be stuck at {stuck}. Apply samples {seq}, left to right. At which sample numbers does the healthy branch differ from the faulty branch? This asks about activation at the branch, before output propagation.",
            [
                (good, good),
                ("אין אף דגימה", "No sample"),
                (alternatives[2], alternatives[2]),
                (alternatives[3], alternatives[3]),
            ],
            (
                f"תקלה מופעלת כשהערך התקין הוא {1 - stuck}, בניגוד לערך התקוע.",
                f"The fault is activated when the healthy value is {1 - stuck}, opposite to the stuck value.",
            ),
            "compare_healthy_and_stuck_trace",
            dict(stuck=stuck, samples=seq),
            detected,
        )

    for v, (gate, stuck) in enumerate([("AND", 0), ("OR", 1), ("AND", 1), ("OR", 0), ("XOR", 0)], 1):
        # For XOR either B works; explicitly ask for B=0 in that case.
        b = 1 if gate == "AND" else 0
        x = 1 - stuck
        options = [f"X={x}, B={b}"] + [
            f"X={xx}, B={bb}" for xx, bb in itertools.product((0, 1), repeat=2) if (xx, bb) != (x, b)
        ]
        fn = {"AND": lambda a, b: a & b, "OR": lambda a, b: a | b, "XOR": lambda a, b: a ^ b}[gate]
        assert fn(x, b) != fn(stuck, b)
        extra_he = " נדרשת גם B=0." if gate == "XOR" else ""
        extra_en = " Also require B=0." if gate == "XOR" else ""
        emit(
            66,
            v,
            f"Y=X {gate} B. הענף X עלול להיות תקוע ב־{stuck}. איזה קלט חושף את התקלה ב־Y?{extra_he}",
            f"Y=X {gate} B. Branch X may be stuck at {stuck}. Which input reveals the fault at Y?{extra_en}",
            options,
            (
                f"בוחרים X={x} להפעלת התקלה ו־B={b} כדי שההבדל לא ייחסם.",
                f"Choose X={x} to activate the fault and B={b} so the difference is not blocked.",
            ),
            "enumerate_healthy_and_faulty_gate",
            dict(gate=gate, stuck=stuck, required_b=0 if gate == "XOR" else None),
        )

    for v, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (1, 0)], 1):
        # Compare both C values; fifth variant asks about the whole truth table.
        vals = []
        for c in (0, 1):
            healthy = a & (not (b or c)) & (not c)
            faulty = a & (not b) & (not c)
            vals.append((int(healthy), int(faulty)))
        assert all(x == y for x, y in vals)
        he = f"Y=A AND NOT(B OR X) AND NOT C, כאשר X=C במעגל התקין. רק הענף X עלול להיות תקוע ב־0; הענף NOT C תקין. עבור A={a}, B={b}, כמה מערכי C האפשריים מאפשרים לזהות את התקלה דרך Y?"
        en = f"Y=A AND NOT(B OR X) AND NOT C, with healthy X=C. Only X may be stuck at 0; the NOT C branch is healthy. For A={a}, B={b}, how many possible C values reveal the fault through Y?"
        if v == 5:
            he = "Y=A AND NOT(B OR X) AND NOT C, כאשר X=C במעגל התקין. רק X עלול להיות תקוע ב־0. מתוך 8 צירופי A,B,C, בכמה המוצא התקין שונה מהמוצא התקול?"
            en = "Y=A AND NOT(B OR X) AND NOT C, with healthy X=C. Only X may be stuck at 0. Of the 8 combinations of A,B,C, how many distinguish the healthy and faulty outputs?"
        numeric(
            67,
            v,
            he,
            en,
            0,
            (
                "כש־C=0 התקלה אינה מופעלת. כש־C=1, הגורם NOT C מאפס את שני המוצאים.",
                "At C=0 the fault is not activated. At C=1, the NOT C factor forces both outputs to zero.",
            ),
            "exhaustive_fault_observability",
            dict(a=a, b=b, all_inputs=v == 5),
            [1, 2, 8],
        )

    for v, (direct, inverted) in enumerate([(1, 4), (2, 7), (3, 5), (1, 8), (4, 9)], 1):
        width = inverted - direct
        numeric(
            68,
            v,
            f"במודל השהיה אידיאלי, Y=A AND NOT A. A עולה בזמן 0; העלייה מגיעה לכניסת ה־AND הישירה אחרי {direct} ns, וירידת NOT A אחרי {inverted} ns. השהיית שער ה־AND אפס. מה רוחב פולס ה־1 במוצא, ב־ns?",
            f"In an ideal delay model, Y=A AND NOT A. A rises at time 0; the direct AND input rises after {direct} ns and NOT A falls after {inverted} ns. The AND gate has zero delay. What is the output's logic-1 pulse width in ns?",
            width,
            (
                f"שתי כניסות ה־AND הן 1 בין הזמנים {direct} ו־{inverted} ns: רוחב {width} ns.",
                f"Both AND inputs are 1 between {direct} and {inverted} ns: a width of {width} ns.",
            ),
            "interval_intersection_delay_model",
            dict(direct=direct, inverted=inverted),
        )

    cases69 = [
        (
            "שני דרייברים במצב Z, ללא נגד משיכה וללא מקור נוסף. מה מובטח על הקו?",
            "Two drivers are in Z, with no pull resistor or other source. What is guaranteed about the wire?",
            ("אין ערך לוגי מובטח", "No logic value is guaranteed"),
            [
                ("אפס לוגי", "Logic zero"),
                ("אחד לוגי", "Logic one"),
                ("הערך תמיד מתחלף", "The value always toggles"),
            ],
            ("Z אינו כופה 0 או 1.", "Z forces neither 0 nor 1."),
        ),
        (
            "דרייבר אחד ב־Z והשני דוחף 1 על קו אידיאלי. איזה ערך נקבע בקו?",
            "One driver is in Z and another drives 1 on an ideal wire. What value is established?",
            ("1", "1"),
            [("0", "0"), ("Z", "Z"), ("בהכרח קונפליקט", "Necessarily contention")],
            (
                "הדרייבר הפעיל קובע 1; דרייבר Z אינו מתנגד לו.",
                "The active driver establishes 1; the Z driver does not oppose it.",
            ),
        ),
        (
            "כל הדרייברים ב־Z, ועל הקו נגד משיכה תקין כלפי מטה. לאחר התייצבות, מה הערך?",
            "All drivers are in Z, with a functioning pull-down resistor. After settling, what is the value?",
            ("0", "0"),
            [
                ("1", "1"),
                ("בהכרח Z גם עם הנגד", "Necessarily Z even with the resistor"),
                ("היפוך בכל מחזור", "An inversion each cycle"),
            ],
            (
                "נגד המשיכה הוא שמגדיר 0; מצב Z לבדו אינו עושה זאת.",
                "The pull-down establishes 0; Z alone does not.",
            ),
        ),
        (
            "שני דרייברים פעילים על קו משותף: אחד דוחף 0 והשני 1. מה מתאר את המצב?",
            "Two active drivers share a wire: one drives 0 and the other 1. What describes this condition?",
            ("קונפליקט בין דרייברים", "Driver contention"),
            [("מצב Z תקין", "Normal Z state"), ("תמיד 0", "Always 0"), ("תמיד 1", "Always 1")],
            (
                "דרייברים פעילים דוחפים ערכים סותרים; אין להניח ערך לוגי תקין.",
                "Active drivers force conflicting values; a valid logic value cannot be assumed.",
            ),
        ),
        (
            "דרייבר תלת־מצבי מושבת. מה פירוש Z ביציאה שלו?",
            "A tri-state driver is disabled. What does Z at its output mean?",
            ("עכבה גבוהה, ללא כפיית ערך", "High impedance, without forcing a value"),
            [
                ("כתיבת 0", "Writing 0"),
                ("כתיבת 1", "Writing 1"),
                ("ביט מידע שלישי שנשמר בזיכרון", "A third data bit stored in memory"),
            ],
            ("Z מתאר ניתוק מהנעה פעילה של הקו.", "Z describes the absence of active driving of the wire."),
        ),
    ]
    for v, (he, en, correct, wrong, ex) in enumerate(cases69, 1):
        emit(69, v, he, en, [correct] + wrong, ex, "tri_state_contract_case", dict(case=v))

    for v, (w, a, b) in enumerate([(4, 7, 1), (4, -8, -1), (5, 15, 2), (5, -16, -2), (4, 3, 2)], 1):
        raw = (a + b) % (1 << w)
        signed = raw if raw < (1 << (w - 1)) else raw - (1 << w)
        overflow = not -(1 << (w - 1)) <= a + b < 1 << (w - 1)
        assert overflow == ((a >= 0 and b >= 0 and signed < 0) or (a < 0 and b < 0 and signed >= 0))
        yes = loc("כן", "yes") if overflow else loc("לא", "no")
        no = loc("לא", "no") if overflow else loc("כן", "yes")
        emit(
            70,
            v,
            f"מחברים {a} ו־{b} במשלים ל־2 ברוחב {w} ביטים ושומרים רק {w} ביטים. מה הערך המסומן שנשמר, והאם יש גלישה מסומנת?",
            f"Add {a} and {b} in {w}-bit two's complement, retaining {w} bits. What signed value is stored, and is there signed overflow?",
            [
                (f"{signed}; גלישה: {yes['he']}", f"{signed}; overflow: {yes['en']}"),
                (f"{signed}; גלישה: {no['he']}", f"{signed}; overflow: {no['en']}"),
                (f"{signed + 1}; גלישה: {yes['he']}", f"{signed + 1}; overflow: {yes['en']}"),
                (f"{signed - 1}; גלישה: {no['he']}", f"{signed - 1}; overflow: {no['en']}"),
            ],
            (
                f"הסכום המתמטי הוא {a + b}. המילה השמורה היא {raw:0{w}b}, שערכה המסומן {signed}; בודקים גלישה מול הטווח המסומן.",
                f"The mathematical sum is {a + b}. The stored word is {raw:0{w}b}, representing {signed}; check overflow against the signed range.",
            ),
            "signed_range_and_sign_change_crosscheck",
            dict(width=w, a=a, b=b),
            dict(stored=signed, overflow=overflow),
        )

    for v, (w, a, b) in enumerate([(4, 15, 1), (4, 12, 7), (5, 31, 2), (3, 7, 5), (5, 20, 20)], 1):
        truncated = (a + b) % 2**w
        exact = a + b
        emit(
            71,
            v,
            f"A={a} ו־B={b} הם לא מסומנים ברוחב {w} ביטים. מה מתקבל כשמחברים ברוחב {w} ואז מוסיפים אפס משמאל, לעומת הרחבה ל־{w + 1} ביטים לפני החיבור? תנו ערכים עשרוניים בסדר הזה.",
            f"A={a} and B={b} are unsigned {w}-bit values. What results from adding at width {w} and then prepending zero, versus widening to {w + 1} bits before adding? Give decimal values in that order.",
            [
                f"{truncated}, {exact}",
                f"{exact}, {truncated}",
                f"{truncated}, {truncated}",
                f"{exact}, {exact}",
            ],
            (
                f"קיטוע מאבד את הנשיאה: {truncated}. הרחבה לפני החיבור שומרת את הסכום {exact}.",
                f"Truncation loses carry, leaving {truncated}. Widening before addition preserves the sum {exact}.",
            ),
            "wide_sum_vs_modular_sum",
            dict(width=w, a=a, b=b),
            [truncated, exact],
        )

    for v, (a, gap) in enumerate([(4, 2), (7, 4), (10, 6), (12, 2), (3, 8)], 1):
        value = a + gap // 2
        b = a + gap
        assert value * 2 == a + b
        numeric(
            72,
            v,
            f"מספרים לא מסומנים מקיימים a={a}, b=a+{gap}, ושניהם מיוצגים בדיוק. מה הממוצע החשבוני בלי לחשב a+b?",
            f"Unsigned integers satisfy a={a}, b=a+{gap}, and both are represented exactly. What is their arithmetic mean without computing a+b?",
            value,
            (
                f"הממוצע הוא a+{gap // 2}={value}, לפי הקשר המובטח בין הקלטים.",
                f"The mean is a+{gap // 2}={value}, using the guaranteed input relation.",
            ),
            "algebra_and_exact_double_crosscheck",
            dict(a=a, gap=gap),
        )

    for v, w in enumerate([3, 4, 5, 6, 7], 1):
        minimum = -(1 << (w - 1))
        raw = (-minimum) % (1 << w)
        exact = -minimum
        assert raw == 1 << (w - 1)
        emit(
            73,
            v,
            f"מה קורה כאשר שוללים את הערך המזערי {minimum} במשלים ל־2 ברוחב {w} ביטים, באמצעות NOT ועוד 1, בלי להרחיב?",
            f"What happens when negating the minimum value {minimum} in {w}-bit two's complement, using NOT plus 1 without widening?",
            [
                (f"נשמר {minimum}, עם גלישה", f"{minimum} is stored, with overflow"),
                (f"נשמר {exact}, ללא גלישה", f"{exact} is stored, without overflow"),
                ("נשמר 0", "0 is stored"),
                (f"נשמר {minimum + 1}", f"{minimum + 1} is stored"),
            ],
            (
                f"הערך החיובי {exact} אינו בתחום. באותו רוחב תוצאת השלילה היא שוב {minimum}.",
                f"Positive {exact} is outside the range. At the same width, negation yields {minimum} again.",
            ),
            "minimum_twos_complement_negation",
            dict(width=w, minimum=minimum),
            minimum,
        )

    for v, (x, k) in enumerate([(53, 3), (27, 2), (94, 4), (41, 3), (127, 5)], 1):
        value = x % (1 << k)
        bits = x & ((1 << k) - 1)
        assert value == bits
        numeric(
            74,
            v,
            f"x={x} הוא שלם לא מסומן. שומרים את {k} הביטים הנמוכים שלו כדי לחשב x modulo {1 << k}. מה השארית העשרונית?",
            f"x={x} is an unsigned integer. Keep its lowest {k} bits to compute x modulo {1 << k}. What is the decimal remainder?",
            value,
            (
                f"הביטים הגבוהים תורמים כפולות של {1 << k}; הביטים הנמוכים נותנים {value}.",
                f"Higher bits contribute multiples of {1 << k}; the low bits give {value}.",
            ),
            "division_remainder_and_bitmask_crosscheck",
            dict(x=x, k=k),
        )

    for v, (b, w) in enumerate([(3, 3), (4, 3), (7, 4), (8, 4), (10, 4)], 1):
        g = b ^ (b >> 1)
        candidates = []
        for x in [g, b, (g + 1) % 2**w, (g + 2) % 2**w, (g + 3) % 2**w]:
            if x not in candidates:
                candidates.append(x)
        emit(
            75,
            v,
            f"בקוד Gray, g=b XOR (b>>1), כאשר ההזזה לוגית. עבור b={b:0{w}b}, מה g ברוחב {w} ביטים?",
            f"For Gray code, g=b XOR (b>>1), with a logical shift. For b={b:0{w}b}, what is g as a {w}-bit word?",
            [f"{x:0{w}b}" for x in candidates[:4]],
            (
                f"מזיזים את b ימינה ומבצעים XOR: מתקבל {g:0{w}b}.",
                f"Shift b right and XOR with b, obtaining {g:0{w}b}.",
            ),
            "gray_encode_bitwise",
            dict(binary=b, width=w),
            f"{g:0{w}b}",
        )

    for v, depth in enumerate([4, 8, 16, 32, 64], 1):
        addr = (depth - 1).bit_length()
        occupancy = depth.bit_length()
        assert 2**addr >= depth and 2 ** (occupancy - 1) <= depth
        emit(
            76,
            v,
            f"FIFO מכיל {depth} תאים. כמה ביטים דרושים לכתובת תא וכמה למונה תפוסה שמייצג גם ריק וגם מלא? תנו את שני הרוחבים בסדר הזה.",
            f"A FIFO contains {depth} cells. How many bits are needed for a cell address and for occupancy including both empty and full? Give widths in that order.",
            [f"{addr}, {occupancy}", f"{addr}, {addr}", f"{occupancy}, {addr}", f"{occupancy}, {occupancy}"],
            (
                f"כתובות הן 0 עד {depth - 1}; תפוסה היא 0 עד {depth}, ולכן נדרש לה ביט נוסף.",
                f"Addresses range from 0 to {depth - 1}; occupancy ranges from 0 to {depth}, requiring one additional bit.",
            ),
            "enumerate_address_and_occupancy_ranges",
            dict(depth=depth),
            [addr, occupancy],
        )

    for v, (a, b) in enumerate([(2, 2), (3, 3), (4, 4), (3, 5), (5, 5)], 1):
        maximum = (2**a - 1) * (2**b - 1)
        width = maximum.bit_length()
        assert 2 ** (width - 1) <= maximum < 2**width
        numeric(
            77,
            v,
            f"מכפילים מספר לא מסומן ברוחב {a} ביטים במספר לא מסומן ברוחב {b} ביטים. מה רוחב המוצא המזערי שמכיל כל מכפלה בדיוק?",
            f"Multiply an unsigned {a}-bit value by an unsigned {b}-bit value. What minimum output width represents every product exactly?",
            width,
            (
                f"המכפלה המרבית היא {maximum}, והיא זקוקה ל־{width} ביטים.",
                f"The maximum product is {maximum}, which requires {width} bits.",
            ),
            "maximum_product_range_bound",
            dict(a_width=a, b_width=b),
        )

    for v, word in enumerate(["110", "101", "1110", "1001", "10111"], 1):
        r = 0
        trace = []
        for x in word:
            r = (2 * r + int(x)) % 3
            trace.append(r)
        assert r == int(word, 2) % 3
        numeric(
            78,
            v,
            f"קוראים {word} מהביט הגבוה לנמוך. מתחילים ב־r=0 ומעדכנים r=(2r+x) modulo 3 בכל ביט x. מה r בסיום?",
            f"Read {word} most significant bit first. Start at r=0 and update r=(2r+x) modulo 3 for each bit x. What is the final r?",
            r,
            (
                f"השאריות לאחר כל ביט הן {', '.join(map(str, trace))}; השארית הסופית היא {r}.",
                f"The remainders after successive bits are {', '.join(map(str, trace))}; the final remainder is {r}.",
            ),
            "stream_remainder_vs_integer_division",
            dict(bits=word),
            [0, 1, 2, 3, 4],
        )

    for v, seq in enumerate(["01", "10", "001", "110", "101"], 1):
        pairs = [(int(x), 1 - int(x)) for x in seq]
        correct = "; ".join(f"{s}{r}" for s, r in pairs)
        wrong = [
            "; ".join(f"{r}{s}" for s, r in pairs),
            "; ".join("00" for _ in seq),
            "; ".join("11" for _ in seq),
        ]
        emit(
            79,
            v,
            f"דלגלג SR בעל חזית עולה ובקרות סינכרוניות פעילות ב־1: SR=00 שומר, 01 מאפס, 10 מציב, 11 אסור. כדי לממש Q_next=D, אילו זוגות SR יש להזין עבור דגימות D={seq}, משמאל לימין? הניחו עמידה בדרישות תזמון.",
            f"A rising-edge SR flip-flop has synchronous controls active at 1: SR=00 holds, 01 resets, 10 sets, and 11 is forbidden. To implement Q_next=D, which SR pairs match D samples {seq}, left to right? Assume timing requirements are met.",
            [correct] + wrong,
            (
                "מחברים S=D ו־R=NOT D. כך כל חזית דוגמת את D בלי להשתמש ב־11.",
                "Connect S=D and R=NOT D. Each edge then samples D without using 11.",
            ),
            "synchronous_SR_truth_table",
            dict(d_samples=seq),
            pairs,
        )

    for v, (start, end, en) in enumerate([(0, 1, 1), (1, 0, 1), (0, 1, 0), (1, 0, 0), (1, 1, 1)], 1):
        latch = end if en else start
        ff = start
        options = [f"latch={latch}, DFF={ff}"] + [
            f"latch={a}, DFF={b}" for a, b in itertools.product((0, 1), repeat=2) if (a, b) != (latch, ff)
        ]
        emit(
            80,
            v,
            f"ללַאץ׳ D ולדלגלג D בעל חזית עולה יש בתחילה Q={start}. בין חזיתות, D נקבע ל־{end}, ו־EN של הלאץ׳ נשאר {en}. אין בקרות אסינכרוניות. לאחר השהיית ההתפשטות ולפני החזית הבאה, מה שני המוצאים?",
            f"A D latch and a rising-edge D flip-flop initially have Q={start}. Between edges, D is set to {end}, while the latch EN remains {en}. There are no asynchronous controls. After propagation and before the next edge, what are the outputs?",
            options,
            (
                "לאץ׳ שקוף כש־EN=1; אחרת הוא שומר. דלגלג ללא חזית פעילה שומר את הדגימה הקודמת.",
                "The latch is transparent when EN=1 and otherwise holds. Without an active edge, the flip-flop retains its previous sample.",
            ),
            "level_enable_vs_edge_transition",
            dict(initial=start, new_d=end, enable=en),
            dict(latch=latch, dff=ff),
        )
    for v, (edge, setup) in enumerate([(10, 2), (12, 3), (20, 4), (15, 2), (18, 5)], 1):
        deadline = edge - setup
        numeric(
            81,
            v,
            f"חזית הדגימה מגיעה בזמן {edge} ns, וזמן ה־setup הנדרש הוא {setup} ns. ללא אי־ודאות נוספת, עד איזה זמן לכל המאוחר הנתונים חייבים להתייצב? תנו זמן ב־ns.",
            f"The sampling edge arrives at {edge} ns and required setup is {setup} ns. With no additional uncertainty, by what latest time must data settle? Give the time in ns.",
            deadline,
            (
                f"ההתייצבות נדרשת {setup} ns לפני החזית: {edge}−{setup}={deadline} ns.",
                f"Data must settle {setup} ns before the edge: {edge}−{setup}={deadline} ns.",
            ),
            "setup_window_subtraction",
            dict(edge=edge, setup=setup),
        )

    for v, (edge, hold, arrival) in enumerate(
        [(10, 2, 11), (12, 3, 13), (20, 4, 22), (15, 2, 18), (18, 3, 21)], 1
    ):
        limit = edge + hold
        violation = arrival < limit
        correct = (
            f"{limit} ns; הפרה: {'כן' if violation else 'לא'}",
            f"{limit} ns; violation: {'yes' if violation else 'no'}",
        )
        emit(
            82,
            v,
            f"חזית הדגימה בזמן {edge} ns; נדרש hold של {hold} ns. נתון חדש מגיע בזמן {arrival} ns. עד מתי הנתון הישן חייב להישאר, והאם המקרה מפר את hold? התייחסו לגבול כשוויון תקין וללא אי־ודאות.",
            f"The sampling edge is at {edge} ns and required hold is {hold} ns. New data arrives at {arrival} ns. Until when must old data remain, and is hold violated? Treat equality at the limit as valid, with no uncertainty.",
            [
                correct,
                (
                    f"{limit} ns; הפרה: {'לא' if violation else 'כן'}",
                    f"{limit} ns; violation: {'no' if violation else 'yes'}",
                ),
                (f"{edge - hold} ns; אין הפרה", "%s ns; no violation" % (edge - hold)),
                ("האטת השעון תמיד פותרת זאת", "Slowing the clock always fixes it"),
            ],
            (
                f"החלון מסתיים ב־{limit} ns. שינוי לפניו מפר hold; הארכת המחזור לבדה אינה מזיזה את החלון סביב אותה חזית.",
                f"The window ends at {limit} ns. An earlier change violates hold; extending the period alone does not move the window around that edge.",
            ),
            "hold_window_boundary_comparison",
            dict(edge=edge, hold=hold, arrival=arrival),
            dict(limit=limit, violation=violation),
        )

    for v, (a, b, g) in enumerate([(3, 5, 2), (2, 7, 1), (6, 4, 3), (1, 8, 2), (5, 5, 4)], 1):
        result = max(a, b) + g
        numeric(
            83,
            v,
            f"שתי דרכים מקבילות מגיעות לכניסות שער אחרי {a} ns ו־{b} ns. השהיית השער היא {g} ns. ללא השהיות נוספות, מה זמן ההתייצבות המאוחר ביותר במוצא, ב־ns?",
            f"Two parallel paths reach a gate after {a} ns and {b} ns. The gate delay is {g} ns. With no additional delays, what is the latest output settling time in ns?",
            result,
            (
                f"ממתינים לקלט המאוחר ואז לשער: max({a},{b})+{g}={result} ns.",
                f"Wait for the later input, then the gate: max({a},{b})+{g}={result} ns.",
            ),
            "parallel_path_max_plus_gate",
            dict(path_a=a, path_b=b, gate=g),
            [a + b + g, result - 1, result + 1, result + 2],
        )

    for v, (latency, items) in enumerate([(2, 5), (3, 4), (4, 6), (5, 3), (2, 8)], 1):
        total = latency + items - 1
        assert len(list(range(latency, latency + items))) == items
        numeric(
            84,
            v,
            f"צינור ללא עצירות מקבל פריט בתחילת כל מחזור, החל בזמן 0. זמן המעבר הוא {latency} מחזורים, וקצב הקבלה הוא פריט בכל מחזור. באיזה זמן, במחזורים מתחילת ההזנה, יוצא הפריט ה־{items}?",
            f"A stall-free pipeline accepts an item at each cycle start, beginning at time 0. Latency is {latency} cycles and initiation interval is one cycle. At what time, in cycles from the start, does item {items} emerge?",
            total,
            (
                f"הפריט הראשון יוצא בזמן {latency}, וכל הבא מחזור אחריו: {latency}+{items}-1={total}.",
                f"The first item emerges at time {latency}; each following item is one cycle later: {latency}+{items}-1={total}.",
            ),
            "enumerate_pipeline_output_times",
            dict(latency=latency, items=items),
        )

    cases85 = [
        (
            "סיבית בקרה מוחזקת יציבה מספיק זמן ונכנסת לסנכרון בשני דלגלגים בשעון היעד. מה נכון לגבי מטא־יציבות?",
            "A control bit is held stable long enough and crosses through two destination-clock flip-flops. What is true about metastability?",
            ("הסיכון מצטמצם, אך אינו נהפך לאפס מובטח", "The risk is reduced, but not guaranteed to be zero"),
            [
                ("אין שום סיכון אפשרי", "No risk is possible"),
                ("השלב הראשון אינו יכול להיות מטא־יציב", "The first stage cannot be metastable"),
                ("הסנכרון משנה את תדר שעון היעד", "The synchronizer changes the destination clock frequency"),
            ],
        ),
        (
            "מילה רב־ביטית משתנה בין שני ערכים, וכל ביט עובר מסנכרן נפרד. מה חסר כדי להבטיח מילה עקבית?",
            "A multi-bit word changes between two values, and each bit uses an independent synchronizer. What is missing for a coherent word?",
            ("פרוטוקול להעברה עקבית של כל המילה", "A protocol for coherent transfer of the whole word"),
            [
                ("אין צורך בדבר נוסף לעולם", "Nothing else is ever needed"),
                ("היפוך כל הביטים אחרי הסנכרון", "Inverting all bits after synchronization"),
                ("חיבור מוצאי כל הביטים ב־OR", "ORing all bit outputs"),
            ],
        ),
        (
            "למה נותנים זמן בין דגימת השלב הראשון לדגימת השלב השני במסנכרן?",
            "Why allow time between the first and second stage samples in a synchronizer?",
            (
                "כדי להקטין את הסיכוי שמטא־יציבות תגיע ללוגיקה בהמשך",
                "To reduce the chance that metastability reaches downstream logic",
            ),
            [
                ("כדי להבטיח השהיה אנלוגית של אפס", "To guarantee zero analog delay"),
                ("כדי להכפיל את מספר אירועי המקור", "To double source event counts"),
                ("כדי לשמור כל פולס קצר גם ללא דגימה", "To retain every short pulse even without sampling"),
            ],
        ),
        (
            "נוסף שלב שלישי למסנכרן של סיבית יציבה, עם תכנון תזמון מתאים. איזו טענה עדיין אינה מובטחת?",
            "A third stage is added to a stable-bit synchronizer with suitable timing design. Which claim is still not guaranteed?",
            ("אפס מוחלט של כשלים ממטא־יציבות", "Absolutely zero metastability failures"),
            [
                ("השהיה של מספר שלבי דגימה", "A delay through sampling stages"),
                (
                    "אפשרות להפחתת הסיכון לעומת פחות זמן התייצבות",
                    "Potential risk reduction compared with less settling time",
                ),
                ("דגימה לפי שעון היעד", "Sampling with the destination clock"),
            ],
        ),
        (
            "האם הוספת שני דלגלגים בשעון היעד מבטיחה לבדה שמילה רב־ביטית תהיה עקבית ושכל אירוע קצר ייקלט?",
            "Does adding two destination-clock flip-flops alone guarantee both coherent multi-bit words and capture of every short event?",
            (
                "לא; לכל דרישה נדרש מנגנון העברה מתאים",
                "No; each requirement needs a suitable transfer mechanism",
            ),
            [
                ("כן, לכל קלט אפשרי", "Yes, for every possible input"),
                ("כן, אם מסירים את שעון היעד", "Yes, if the destination clock is removed"),
                ("כן, כי מטא־יציבות היא ערך לוגי קבוע", "Yes, because metastability is a fixed logic value"),
            ],
        ),
    ]
    for v, (he, en, correct, wrong) in enumerate(cases85, 1):
        emit(
            85,
            v,
            he,
            en,
            [correct] + wrong,
            (
                "מסנכרן מפחית סיכון למטא־יציבות בתנאים מתאימים; עקביות מילה ושימור אירועים דורשים טיפול נפרד.",
                "A synchronizer reduces metastability risk under suitable conditions; word coherence and event retention require separate treatment.",
            ),
            "CDC_contract_limitation_review",
            dict(case=v),
        )

    for v, (period, start, finish) in enumerate(
        [(10, 2, 5), (12, 1, 8), (8, 2, 6), (20, 4, 13), (16, 3, 11)], 1
    ):
        samples = [t for t in range(0, period * 3, period) if start <= t < finish]
        assert samples == []
        emit(
            86,
            v,
            f"חזיתות שעון היעד הן בזמן 0, {period}, {2 * period} ns. פולס המקור גבוה רק מ־{start} עד {finish} ns ונמוך בשאר הזמן. במודל דגימה אידיאלי, מה יראה השלב הראשון של מסנכרן בשתי החזיתות הראשונות?",
            f"Destination edges occur at 0, {period}, {2 * period} ns. The source pulse is high only from {start} to {finish} ns and low otherwise. In an ideal sampling model, what does the first synchronizer stage sample at the first two edges?",
            ["0, 0", "0, 1", "1, 0", "1, 1"],
            (
                "הפולס כולו נמצא בין חזיתות ולכן אינו נדגם. שני דלגלגים אינם שומרים אירוע שמעולם לא נדגם.",
                "The pulse lies entirely between edges and is never sampled. Two flip-flops do not retain an event that was never sampled.",
            ),
            "explicit_edge_sample_pulse_intersection",
            dict(period=period, pulse_start=start, pulse_end=finish),
            [0, 0],
        )

    for v, (c, push, pop) in enumerate([(3, 1, 0), (3, 0, 1), (4, 1, 1), (0, 0, 0), (6, 1, 1)], 1):
        value = c + push - pop
        numeric(
            87,
            v,
            f"תפוסת FIFO היא c={c}. בקצה השעון push={push}, pop={pop} מציינים פעולות שכבר התקבלו לאחר בדיקות מלא וריק. מה התפוסה אחרי הקצה?",
            f"FIFO occupancy is c={c}. At the edge, push={push}, pop={pop} denote operations already accepted after full/empty checks. What is occupancy after the edge?",
            value,
            (
                f"מעדכנים לפי הפעולות שהתקבלו: {c}+{push}−{pop}={value}.",
                f"Update using accepted operations: {c}+{push}−{pop}={value}.",
            ),
            "accepted_FIFO_operations_count",
            dict(count=c, push=push, pop=pop),
        )

    for v, items in enumerate([list("ABC"), list("PQRS"), list("MN"), list("JKLMN"), list("RST")], 1):
        new = ["X", "Y", "Z", "W", "V"][v - 1]
        returned = items[0]
        remaining = items[1:] + [new]
        good = (
            f"נקרא {returned}; נותר {','.join(remaining)}",
            f"Read {returned}; remaining {','.join(remaining)}",
        )
        emit(
            88,
            v,
            f"FIFO מלא מכיל {','.join(items)} לפי סדר היציאה. החוזה מקבל קריאה וכתיבה יחד גם כשהוא מלא, וקורא מידע ישן לפני הדריסה. באותו קצה קוראים וכותבים {new}. מה נקרא ומה נשאר?",
            f"A full FIFO contains {','.join(items)} in output order. Its contract accepts a simultaneous read/write when full and reads old data before overwrite. One edge reads and writes {new}. What is read and what remains?",
            [
                good,
                (f"נקרא {new}; נותר {','.join(items)}", f"Read {new}; remaining {','.join(items)}"),
                (
                    f"נקרא {returned}; נותר {','.join(items[1:])}",
                    f"Read {returned}; remaining {','.join(items[1:])}",
                ),
                ("שתי הפעולות נדחות", "Both operations are rejected"),
            ],
            (
                "הראש הישן נקרא, הפריט החדש מתווסף בזנב, והתפוסה אינה משתנה.",
                "The old head is read, the new item joins the tail, and occupancy is unchanged.",
            ),
            "FIFO_list_pop_append_model",
            dict(before=items, written=new),
            dict(read=returned, after=remaining),
        )

    for v, (read, write) in enumerate([(1, 1), (1, 0), (0, 1), (0, 0), (1, 1)], 1):
        he = f"FIFO ריק, ללא bypass, דוחה קריאה ממצב ריק ומקבל כתיבה אם מתבקשת. התנאים נבדקים לפי המצב שלפני הקצה. בקשות הקצה הן read={read}, write={write}. מה התפוסה לאחר הקצה?"
        en = f"An empty FIFO has no bypass, rejects reads from empty, and accepts a requested write. Conditions use pre-edge state. Requests are read={read}, write={write}. What is occupancy after the edge?"
        if v == 5:
            he = "FIFO מתחיל ריק וללא bypass. בכל קצה התנאים נבדקים לפי המצב שלפניו. בקצה הראשון מבקשים קריאה וכותבים X; בקצה הבא מבקשים רק קריאה. מה התפוסה לאחר הקצה השני?"
            en = "A FIFO starts empty with no bypass. Each edge uses pre-edge state. The first edge requests a read and writes X; the next requests only a read. What is occupancy after the second edge?"
            value = 0
        else:
            value = write
        numeric(
            89,
            v,
            he,
            en,
            value,
            (
                "בלי bypass, קריאה שנבדקת מול ריק נדחית; הכתיבה אינה משנה בדיעבד את קבלתה באותו קצה.",
                "Without bypass, a read checked against empty is rejected; a simultaneous write does not retroactively accept it.",
            ),
            "pre_edge_empty_no_bypass_FIFO_model",
            dict(read_request=read, write_request=write, second_read=v == 5),
            [0, 1, 2, 3],
        )

    for v, (data, stalls) in enumerate([("A", 1), ("B", 2), ("C", 3), ("D", 4), ("E", 5)], 1):
        emit(
            90,
            v,
            f"בממשק ready/valid, העברה מתבצעת רק בקצה שבו שני האותות 1. השולח מציג valid=1 ונתון {data}; ready נשאר 0 במשך {stalls} מחזורים. אין reset. מה עליו להציג עד קבלת ההעברה?",
            f"In a ready/valid interface, transfer occurs only at an edge with both signals 1. The sender presents valid=1 and data {data}; ready stays 0 for {stalls} cycles. There is no reset. What must it present until acceptance?",
            [
                (f"valid=1; data={data}", f"valid=1; data={data}"),
                ("valid=0; הנתון הבא", "valid=0; next data item"),
                ("valid=1; הנתון הבא בכל מחזור", "valid=1; next data item each cycle"),
                ("valid מתחלף בכל מחזור", "valid toggles each cycle"),
            ],
            (
                "בזמן עצירה השולח שומר valid ואת אותו נתון עד העברה שהתקבלה.",
                "During a stall, the sender holds valid and the same data until an accepted transfer.",
            ),
            "ready_valid_stability_contract",
            dict(data=data, stall_cycles=stalls),
        )

    for v, (width, start, steps) in enumerate([(3, 6, 3), (4, 13, 4), (3, 5, 4), (4, 14, 2), (5, 29, 5)], 1):
        maximum = 2**width - 1
        value = start
        trace = []
        for _ in range(steps):
            value = min(value + 1, maximum)
            trace.append(value)
        assert value == min(start + steps, maximum)
        numeric(
            91,
            v,
            f"מונה רווי לא מסומן ברוחב {width} ביטים מתחיל ב־{start}. הוא מתקדם ב־1 בכל בקשת הגדלה, ונשאר בערך המרבי אם כבר הגיע אליו. מה ערכו אחרי {steps} בקשות?",
            f"An unsigned {width}-bit saturating counter starts at {start}. Each increment request adds 1 unless it is already at the maximum. What is its value after {steps} requests?",
            value,
            (
                f"הערכים לאחר הבקשות הם {', '.join(map(str, trace))}; המונה אינו גולש לאפס.",
                f"The values after requests are {', '.join(map(str, trace))}; the counter does not wrap to zero.",
            ),
            "step_simulation_vs_saturation_bound",
            dict(width=width, start=start, steps=steps),
        )

    for v, (value, inc, dec) in enumerate([(1, 1, 0), (2, 0, 1), (3, 1, 1), (4, 0, 0), (6, 1, 0)], 1):
        new = (value + int(inc and not dec) - int(dec and not inc)) % 8
        toggle = ((value >> 1) & 1) != ((new >> 1) & 1)
        q0 = value & 1
        formula = bool((inc and not dec and q0) or (dec and not inc and not q0))
        assert toggle == formula
        emit(
            92,
            v,
            f"מונה בן 3 ביטים מגדיל עבור inc,dec=10, מקטין עבור 01 ושומר עבור 00 או 11, עם גלישה מודולרית. לפני הקצה Q={value:03b}, inc={inc}, dec={dec}. מה Q אחרי הקצה, והאם ביט המשקל 2 התהפך?",
            f"A 3-bit counter increments for inc,dec=10, decrements for 01, and holds for 00 or 11, with modular wraparound. Before the edge Q={value:03b}, inc={inc}, dec={dec}. What is Q afterward, and did the weight-2 bit toggle?",
            [
                (f"{new:03b}; {'כן' if toggle else 'לא'}", f"{new:03b}; {'yes' if toggle else 'no'}"),
                (f"{new:03b}; {'לא' if toggle else 'כן'}", f"{new:03b}; {'no' if toggle else 'yes'}"),
                (f"{(new + 1) % 8:03b}; כן", f"{(new + 1) % 8:03b}; yes"),
                (f"{(new + 2) % 8:03b}; לא", f"{(new + 2) % 8:03b}; no"),
            ],
            (
                "הגדלה והקטנה יחד מבטלות זו את זו. ביט המשקל 2 מתהפך רק בנשיאה או בשאילה מהביט הנמוך.",
                "Simultaneous increment and decrement cancel. The weight-2 bit toggles only on carry or borrow from the lowest bit.",
            ),
            "counter_simulation_vs_toggle_equation",
            dict(old=value, inc=inc, dec=dec),
            dict(next=new, toggle=toggle),
        )

    cases93 = [
        (
            "בלוק קומבינטורי משים next=DONE רק אם go=1. אחרת הכוונה היא לשמור את מצב הרגיסטר state. איזו ברירת מחדל יש להציב לפני התנאי כדי להשלים את ההשמה בכל מסלול?",
            "A combinational block assigns next=DONE only if go=1. Otherwise it should retain the register state. Which default belongs before the condition to assign next on every path?",
            [
                "next=state",
                "next=DONE",
                "state=next",
                ("ללא השמה במסלול האחר", "No assignment on the other path"),
            ],
            (
                "ברירת המחדל מגדירה את next לכל ערך של go; הרגיסטר הנפרד שומר את המצב.",
                "The default defines next for either value of go; the separate register stores state.",
            ),
        ),
        (
            "במודל RTL, next מחזיק כרגע DONE. בלוק עם השמה רק בענף go=1 מופעל כאשר go=0 ו־state=WAIT. מה קורה ל־next אם אין ברירת מחדל או else?",
            "In an RTL model, next currently holds DONE. A block assigning it only in the go=1 branch is evaluated with go=0 and state=WAIT. What happens to next without a default or else?",
            [
                ("נשאר DONE, ונוצרת דרישה לאחסון לא מכוון", "It remains DONE, requiring unintended storage"),
                ("נהפך אוטומטית ל־WAIT", "It automatically becomes WAIT"),
                ("נהפך אוטומטית לאפס", "It automatically becomes zero"),
                ("מקבל את מצב השעון", "It takes the clock level"),
            ],
            (
                "מסלול ללא השמה משמר את הערך הקודם של next, ולא בהכרח את state.",
                "An unassigned path retains the previous next value, which need not equal state.",
            ),
        ),
        (
            "בלוק קומבינטורי מתחיל ב־next=state ואז מבצע next=DONE אם go=1. עבור state=RUN ו־go=0, מה next?",
            "A combinational block starts with next=state, then assigns next=DONE if go=1. With state=RUN and go=0, what is next?",
            [
                "RUN",
                "DONE",
                "IDLE",
                ("הערך הקודם של next, בלי תלות ב־state", "The previous next value, independent of state"),
            ],
            (
                "ההשמה לפני התנאי פעילה גם כש־go=0; לכן next מקבל את state הנוכחי.",
                "The assignment before the condition also applies when go=0, so next gets the current state.",
            ),
        ),
        (
            "בלוק קומבינטורי משים next=IDLE כברירת מחדל ואז next=DONE אם go=1. רוצים לשמור state כש־go=0. עבור state=RUN ו־go=0, מה הבעיה?",
            "A combinational block defaults next=IDLE, then assigns next=DONE if go=1. The intent is to retain state when go=0. With state=RUN and go=0, what is wrong?",
            [
                (
                    "next מקבל IDLE: אין מסלול חסר, אך התנהגות השמירה שגויה",
                    "next gets IDLE: assignment coverage is complete, but hold behavior is wrong",
                ),
                ("next מקבל RUN כמתוכנן", "next gets RUN as intended"),
                ("חסר בהכרח לאץ׳ בגלל ברירת המחדל", "The default necessarily causes a latch"),
                ("next מקבל DONE", "next gets DONE"),
            ],
            (
                "כיסוי כל המסלולים מונע אחסון משתמע, אך צריך גם לבחור ברירת מחדל שמתאימה להתנהגות הרצויה.",
                "Full path coverage avoids implied storage, but the default must also match the intended behavior.",
            ),
        ),
        (
            "בבלוק קומבינטורי יש if go=1 אז next=DONE. אין ברירת מחדל, ורוצים לשמור state ב־go=0 בלי לאץ׳ עבור next. איזו השלמה מתאימה?",
            "A combinational block has if go=1 then next=DONE. There is no default. To retain state for go=0 without a latch for next, which completion is appropriate?",
            [
                "else next=state",
                "else state=next",
                "else next=next",
                ("להשאיר את ענף else ריק", "Leave else empty"),
            ],
            (
                "השמת next=state בענף else מגדירה את next גם במסלול השני, בלי לדרוש שימור עצמי שלו.",
                "Assigning next=state in else defines next on the other path without requiring next to retain itself.",
            ),
        ),
    ]
    for v, (he, en, options, ex) in enumerate(cases93, 1):
        emit(93, v, he, en, options, ex, "combinational_assignment_path_coverage", dict(case=v))

    # Independent product-machine search: find an input sequence distinguishing two states.
    def distinguish(outputs, transitions, left, right):
        queue = [(left, right, "")]
        seen = set()
        while queue:
            a, b, word = queue.pop(0)
            if (a, b) in seen:
                continue
            seen.add((a, b))
            if outputs[a] != outputs[b]:
                return word
            for x in (0, 1):
                queue.append((transitions[a][x], transitions[b][x], word + str(x)))
        return None

    outputs = {"W0": 0, "W1": 0, "DONE": 1}
    transitions = {"W0": {0: "W1", 1: "DONE"}, "W1": {0: "W0", 1: "DONE"}, "DONE": {0: "DONE", 1: "DONE"}}
    assert distinguish(outputs, transitions, "W0", "W1") is None
    emit(
        94,
        1,
        "במכונת Moore, W0 ו־W1 מוציאים 0. בקלט 0 הם מתחלפים זה בזה; בקלט 1 שניהם עוברים ל־DONE שמוציא 1 ונשאר בו. איזה מיזוג שומר על התנהגות המוצא לכל רצף קלט?",
        "In a Moore machine, W0 and W1 output 0. Input 0 swaps them; input 1 sends both to DONE, which outputs 1 and stays there. Which merge preserves output behavior for every input sequence?",
        [
            ("W0 עם W1", "W0 with W1"),
            ("W0 עם DONE", "W0 with DONE"),
            ("W1 עם DONE", "W1 with DONE"),
            ("כל שלושת המצבים יחד", "All three states together"),
        ],
        (
            "ל־W0 ול־W1 אותו מוצא ועתיד שקול. DONE נבדל מהם כבר במוצא הנוכחי.",
            "W0 and W1 have equal outputs and equivalent futures. DONE differs from them in its current output.",
        ),
        "product_machine_distinguishing_sequence_search",
        dict(outputs=outputs, transitions=transitions),
        None,
    )
    different = {**transitions, "W1": {0: "W0", 1: "W0"}}
    assert distinguish(outputs, different, "W0", "W1") == "1"
    emit(
        94,
        2,
        "במכונת Moore, W0 ו־W1 מוציאים 0 ו־DONE מוציא 1. בקלט 0, W0 ו־W1 מתחלפים. בקלט 1, W0 עובר ל־DONE אך W1 עובר ל־W0. איזה רצף מבדיל בין מוצאיהם לאחר עיבודו, ולכן מונע את מיזוגם?",
        "In a Moore machine, W0 and W1 output 0 and DONE outputs 1. Input 0 swaps W0 and W1. On input 1, W0 enters DONE but W1 enters W0. Which sequence distinguishes their outputs after processing it, preventing a merge?",
        ["1", "0", "00", ("הרצף הריק", "The empty sequence")],
        (
            "לאחר קלט 1, התחלה ב־W0 נותנת מוצא 1, ואילו התחלה ב־W1 נותנת מוצא 0.",
            "After input 1, starting from W0 gives output 1, while starting from W1 gives output 0.",
        ),
        "product_machine_distinguishing_sequence_search",
        dict(outputs=outputs, transitions=different),
        "1",
    )
    different_outputs = {"W0": 0, "W1": 1, "DONE": 1}
    assert distinguish(different_outputs, transitions, "W0", "W1") == ""
    emit(
        94,
        3,
        "בשני מצבי Moore יש אותם יעדי מעבר לכל קלט, אך ב־W0 המוצא 0 וב־W1 המוצא 1. מתי אפשר להבחין בין שני המצבים?",
        "Two Moore states have the same transition destinations for every input, but W0 outputs 0 and W1 outputs 1. When can the states be distinguished?",
        [
            ("כבר במוצא הנוכחי, בלי לקרוא קלט נוסף", "By the current output, without reading another input"),
            ("רק אחרי שני קלטי 1", "Only after two inputs of 1"),
            (
                "אי אפשר להבחין ולכן תמיד מותר למזג",
                "They cannot be distinguished, so merging is always valid",
            ),
            ("רק אם שמות המצבים שונים באורכם", "Only if state names have different lengths"),
        ],
        (
            "שקילות Moore דורשת גם אותו מוצא נוכחי, ולא רק מעברים מתאימים.",
            "Moore equivalence requires equal current outputs as well as compatible transitions.",
        ),
        "current_output_distinguishes_Moore_states",
        dict(outputs=[0, 1]),
        "",
    )
    # Three waiting states form a ring on 0; all enter absorbing DONE on 1.
    ring_outputs = {"W0": 0, "W1": 0, "W2": 0, "DONE": 1}
    ring = {f"W{i}": {0: f"W{(i + 1) % 3}", 1: "DONE"} for i in range(3)}
    ring["DONE"] = {0: "DONE", 1: "DONE"}
    assert all(distinguish(ring_outputs, ring, "W0", f"W{i}") is None for i in range(3))
    numeric(
        94,
        4,
        "שלושה מצבי Moore מוציאים 0 ומתקדמים בטבעת בקלט 0. בקלט 1 כל אחד עובר ל־DONE שמוציא 1 ונשאר בו. כמה מצבי התנהגות שונים נשארים אחרי מיזוג מצבים שקולים?",
        "Three Moore states output 0 and advance around a ring on input 0. Input 1 sends each to DONE, which outputs 1 and stays there. How many behaviorally distinct states remain after merging equivalent states?",
        2,
        (
            "שלושת מצבי ההמתנה שקולים זה לזה; DONE נבדל מהם במוצא. נשארות שתי מחלקות.",
            "The three waiting states are equivalent; DONE has a different output. Two classes remain.",
        ),
        "product_machine_equivalence_class_count",
        dict(outputs=ring_outputs, transitions=ring),
        [1, 3, 4],
    )
    emit(
        94,
        5,
        "במכונת Moore, W0 ו־W1 מוציאים 0, מתחלפים בקלט 0 ועוברים שניהם למצב סופג DONE שמוציא 1 בקלט 1. איזה רצף קלט מבחין בין התחלה ב־W0 לבין התחלה ב־W1 דרך סדרת המוצאים?",
        "In a Moore machine, W0 and W1 output 0, swap on input 0, and both enter absorbing DONE, output 1, on input 1. Which input sequence distinguishes starting in W0 from starting in W1 through the output sequence?",
        [("אין רצף כזה", "No such sequence exists"), "0", "1", "01"],
        (
            "בשני המצבים המוצא נשאר 0 עד ה־1 הראשון ואז נשאר 1; השם הפנימי אינו משנה את סדרת המוצאים.",
            "From either state, output stays 0 until the first 1, then remains 1; the internal name does not change the output sequence.",
        ),
        "product_machine_distinguishing_sequence_search",
        dict(outputs=outputs, transitions=transitions),
        None,
    )

    for v, release in enumerate([0, 1, 0, 1, 0], 1):
        # Distinct trace lengths and request histories; count starts, not busy cycles.
        high_cycles = v + 2
        samples = [(1, 0)] + [(1, 0)] * (high_cycles - 1) + [(1, 1)] + [(release, 0), (1, 0)]
        state = "READY"
        starts = 0
        for s, d in samples:
            if state == "READY" and s:
                starts += 1
                state = "RUN"
            elif state == "RUN" and d:
                state = "WAIT"
            elif state == "WAIT" and not s:
                state = "READY"
        expected = 2 if release == 0 else 1
        assert starts == expected
        numeric(
            95,
            v,
            f"מכונה מתחילה ב־READY: בקלט s=1 מתחילה פעולה ועוברת ל־RUN; ב־RUN, d=1 מעביר ל־WAIT; רק s=0 ב־WAIT מחזיר ל־READY. s נשאר 1 במשך {high_cycles} מחזורי התחלה ועבודה, ואז d=1 בעוד s=1. בשני הקצוות הבאים s הוא {release}, ואז 1, ו־d=0. כמה פעולות התחילו בסך הכול?",
            f"A machine starts READY: s=1 starts work and enters RUN; d=1 in RUN enters WAIT; only s=0 in WAIT returns to READY. s stays 1 for {high_cycles} start/work cycles, then d=1 while s=1. At the next two edges s is {release}, then 1, with d=0. How many operations have started in total?",
            starts,
            (
                "WAIT מחייב דגימת שחרור לפני דריכה מחדש. s גבוה ברצף אינו מתחיל פעולה נוספת.",
                "WAIT requires a sampled release before rearming. A continuously high s does not start another operation.",
            ),
            "explicit_READY_RUN_WAIT_trace",
            dict(samples=samples),
            [0, 1, 2, 3],
        )

    for v, bits in enumerate(["10", "11", "101", "1101", "01101"], 1):
        r = 0
        w = 1
        for x in bits:
            r = (r + int(x) * w) % 3
            w = (2 * w) % 3
        interpreted = sum(int(x) * (1 << i) for i, x in enumerate(bits))
        assert r == interpreted % 3
        numeric(
            96,
            v,
            f"סדרת הקלט {bits} מגיעה משמאל לימין, מהביט הנמוך לגבוה. שומרים את השארית המספרית האמיתית modulo 3. מתחילים r=0,w=1 ומעדכנים r=(r+xw) modulo 3, ואז w=2w modulo 3. מה r בסיום?",
            f"Input samples {bits} arrive left to right, least significant bit first. Keep the actual numerical remainder modulo 3. Start r=0,w=1; update r=(r+xw) modulo 3, then w=2w modulo 3. What is the final r?",
            r,
            (
                f"משקלי הביטים modulo 3 מתחלפים בין 1 ו־2. הערך שנקרא הוא {interpreted}, ושאריתו {r}.",
                f"Bit weights modulo 3 alternate between 1 and 2. The value read is {interpreted}, with remainder {r}.",
            ),
            "LSB_stream_weighted_sum_vs_integer",
            dict(bits_in_time_order=bits),
            [0, 1, 2, 3, 4],
        )

    cycle = ["00", "01", "11", "10"]
    for v, (old, new) in enumerate([("01", "00"), ("00", "01"), ("11", "10"), ("00", "11"), ("10", "10")], 1):
        delta = (cycle.index(new) - cycle.index(old)) % 4
        meanings = [
            ("אין שינוי", "No change"),
            ("צעד קדימה", "One forward step"),
            ("שינוי של שני ביטים; הכיוון אינו נקבע", "Two-bit change; direction is not determined"),
            ("צעד אחורה", "One backward step"),
        ]
        emit(
            97,
            v,
            f"מקודד סיבובי מתקדם במחזור 00→01→11→10→00, ולאחור בסדר ההפוך. הדגימה הקודמת היא {old} והחדשה {new}. מה אפשר להסיק בהנחה שמזהים צעד חוקי יחיד רק כאשר השתנה ביט אחד?",
            f"A rotary encoder moves forward through 00→01→11→10→00 and backward in reverse. The previous sample is {old}, the new sample {new}. What follows if a legal single step requires exactly one changed bit?",
            [meanings[delta]] + [m for i, m in enumerate(meanings) if i != delta],
            (
                "יש להשוות למצב הקודם. שינוי של שני ביטים אינו קובע כיוון יחיד בלי מידע נוסף.",
                "Compare with the previous state. A two-bit change does not establish a unique direction without more information.",
            ),
            "quadrature_cycle_adjacency",
            dict(previous=old, current=new),
            meanings[delta][1],
        )

    for v, (stages, period) in enumerate([(2, 10), (3, 8), (4, 5), (2, 12), (3, 7)], 1):
        result = stages * period
        numeric(
            98,
            v,
            f"מכונת Moore נכנסת, בקצה טריגר, לשרשרת של {stages} מצבי פולס. המוצא 1 בכל מצב בשרשרת, וכל קצה מתקדם למצב הבא; אחרון חוזר ל־IDLE שמוציא 0. מתעלמים מטריגרים בשרשרת ומהשהיות. מחזור השעון {period} ns. מה רוחב הפולס ב־ns?",
            f"On a trigger edge, a Moore machine enters a chain of {stages} pulse states. Each outputs 1; every edge advances one state, with the last returning to IDLE, output 0. Ignore triggers during the chain and propagation delays. Clock period is {period} ns. What is pulse width in ns?",
            result,
            (
                f"כל מצב פולס נמשך מחזור שלם: {stages}×{period}={result} ns.",
                f"Each pulse state lasts one full period: {stages}×{period}={result} ns.",
            ),
            "Moore_high_state_interval_count",
            dict(high_states=stages, period=period),
        )

    for v, stages in enumerate([2, 3, 4, 5, 6], 1):
        numeric(
            99,
            v,
            f"נתונים עוברים בצינור של {stages} רשומות טוריות ללא עצירות, עם רשומה אחת בכל קצה. valid מסמן אם פריט הקלט אמיתי. בכמה מחזורים יש לעכב את valid כדי שיתאים לנתוני המוצא? הניחו איפוס מוגדר ל־valid.",
            f"Data passes through {stages} serial registers without stalls, one register per edge. valid marks real input items. By how many cycles must valid be delayed to match output data? Assume a defined valid reset.",
            stages,
            (
                "מידע וסימון התקפות שלו חייבים לעבור אותו מספר שלבים ובאותם תנאי עדכון.",
                "Data and its validity marker must pass through the same number of stages with matching update conditions.",
            ),
            "paired_data_valid_pipeline_tag",
            dict(stages=stages),
        )

    for v, bits in enumerate(["", "1", "10", "11", "1011"], 1):
        parity = sum(map(int, bits)) % 2
        last = int(bits[-1]) if bits else 0
        text = bits or "ריקה"
        text_en = bits or "empty"
        choices = [f"parity={parity}, last={last}"] + [
            f"parity={p}, last={b}"
            for p, b in itertools.product((0, 1), repeat=2)
            if (p, b) != (parity, last)
        ]
        emit(
            100,
            v,
            f"מכונה שומרת זוג: parity הוא 1 אם מספר האחדות שנקראו אי־זוגי, ו־last הוא הביט האחרון. בתחילה שניהם 0. אחרי סדרת הקלט {text}, מה הזוג?",
            f"A machine retains a pair: parity is 1 for an odd number of ones read, and last is the latest bit. Both start at 0. After input sequence {text_en}, what is the pair?",
            choices,
            (
                "מעדכנים parity באמצעות XOR עם כל ביט, ושומרים אותו ביט ב־last. שתי העובדות יחד דורשות עד ארבעה קודי מצב.",
                "Update parity by XOR with each bit and store that bit in last. The two facts together require up to four state codes.",
            ),
            "enumerate_parity_and_last_bit",
            dict(bits=bits),
            dict(parity=parity, last=last),
        )
    for v, weight in enumerate([1, 2, 4, 8, 16], 1):
        carry_weight = 2 * weight
        for a, b, c in itertools.product((0, 1), repeat=3):
            total = a + b + c
            assert weight * total == weight * (total % 2) + carry_weight * (total // 2)
        numeric(
            101,
            v,
            f"שלוש סיביות בעלות משקל {weight} נכנסות למחבר מלא. סיבית הסכום S נשארת במשקל {weight}. מה המשקל הנכון של סיבית הנשיאה K כדי לשמור על הערך?",
            f"Three bits, each of weight {weight}, enter a full adder. Sum bit S retains weight {weight}. What weight must carry K have to preserve value?",
            carry_weight,
            (
                f"A+B+C=S+2K, ולכן הנשיאה שווה שתי יחידות מהמשקל המקורי: {carry_weight}.",
                f"A+B+C=S+2K, so carry has twice the original weight: {carry_weight}.",
            ),
            "exhaustive_weighted_full_adder_identity",
            dict(weight=weight),
            [weight, weight * 3, weight * 4, weight * 5],
        )

    for v, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (1, 0)], 1):
        cout = [int(a + b + cin >= 2) for cin in (0, 1)]
        if v < 5:
            correct = ", ".join(map(str, cout))
            emit(
                102,
                v,
                f"במחבר מלא A={a}, B={b}. מהם ערכי carry-out עבור Cin=0 ואחריו Cin=1?",
                f"In a full adder A={a}, B={b}. What are carry-out values for Cin=0 followed by Cin=1?",
                [correct] + [f"{x}, {y}" for x, y in itertools.product((0, 1), repeat=2) if [x, y] != cout],
                (
                    "נשיאה היא 1 כשהסכום של שלוש הסיביות לפחות 2. כש־A שונה מ־B, הנשיאה שווה ל־Cin.",
                    "Carry is 1 when the three-bit sum is at least 2. When A differs from B, carry equals Cin.",
                ),
                "full_adder_carry_threshold_table",
                dict(a=a, b=b),
                cout,
            )
        else:
            emit(
                102,
                v,
                "מממשים את נשיאת המחבר המלא באמצעות MUX. בוחרים Cin כאשר P=1, ואחרת בוחרים A. איזו פונקציה של A,B מתאימה ל־P?",
                "Implement full-adder carry with a MUX: select Cin when P=1, otherwise A. Which function of A,B is P?",
                ["A XOR B", "A AND B", "A OR B", "NOT A"],
                (
                    "כששתי הכניסות שונות, Cin קובע את הנשיאה. כשהן שוות, A קובע אותה.",
                    "When the two inputs differ, Cin determines carry. When they match, A determines it.",
                ),
                "exhaustive_carry_mux_equivalence",
                dict(expression="mux(A,Cin,A XOR B)"),
            )

    cases103 = [("B", "C"), ("NOT B", "C"), ("B", "NOT C"), ("0", "B"), ("C", "1")]
    for v, (d0, d1) in enumerate(cases103, 1):
        expr = f"(NOT A AND {d0}) OR (A AND {d1})"
        emit(
            103,
            v,
            f"מממשים F={expr} באמצעות MUX שבוחר D0 כש־S=0 ו־D1 כש־S=1. קובעים S=A. מה חיבורי D0,D1 לפי הסדר?",
            f"Implement F={expr} with a MUX selecting D0 for S=0 and D1 for S=1. Set S=A. What are D0,D1, in order?",
            [f"{d0}; {d1}", f"{d1}; {d0}", "A; NOT A", "0; 0"],
            (
                f"מציבים A=0 ומקבלים D0={d0}; מציבים A=1 ומקבלים D1={d1}.",
                f"Substitute A=0 to obtain D0={d0}; substitute A=1 to obtain D1={d1}.",
            ),
            "Shannon_cofactor_substitution",
            dict(d0=d0, d1=d1),
        )

    def nand(a, b):
        return 1 - (a & b)

    for v, seq in enumerate(
        [
            [(0, 0), (0, 1), (1, 1)],
            [(1, 1), (1, 0), (0, 0)],
            [(0, 1), (1, 0), (1, 1)],
            [(1, 0), (0, 0), (0, 1)],
            [(0, 0), (1, 1), (0, 1), (1, 0)],
        ],
        1,
    ):
        result = []
        for a, b in seq:
            t = nand(a, b)
            u = nand(a, t)
            vv = nand(b, t)
            y = nand(u, vv)
            assert y == a ^ b
            result.append(y)
        good = ", ".join(map(str, result))
        wrong = [
            ", ".join(map(str, [a & b for a, b in seq])),
            ", ".join(map(str, [a | b for a, b in seq])),
            ", ".join(map(str, [1 - (a ^ b) for a, b in seq])),
        ]
        # OR and XOR can agree on a subset, so each selected sequence contains 11.
        if good in wrong or len(set(wrong)) < 3:
            wrong = [
                ", ".join(map(str, [(x + 1) % 2 for x in result])),
                ", ".join("0" for _ in result),
                ", ".join("1" for _ in result),
            ]
        assert good not in wrong and len(set(wrong)) == 3
        pairs = "; ".join(f"{a}{b}" for a, b in seq)
        emit(
            104,
            v,
            f"ארבעה שערי NAND מחוברים כך: t=NAND(A,B), u=NAND(A,t), v=NAND(B,t), Y=NAND(u,v). עבור זוגות AB בסדר {pairs}, מה סדרת Y?",
            f"Four NAND gates are connected as t=NAND(A,B), u=NAND(A,t), v=NAND(B,t), Y=NAND(u,v). For AB pairs {pairs}, in that order, what is the Y sequence?",
            [good] + wrong,
            (
                "המבנה מממש XOR בארבעה שערים, עם שיתוף השער t בין שני הענפים.",
                "This structure implements XOR using four gates, sharing t between the two branches.",
            ),
            "exhaustive_NAND_network_vs_XOR",
            dict(input_pairs=seq),
            result,
        )

    for v, word in enumerate(["1010", "0111", "1001", "0000", "0011"], 1):
        value = int(word, 2)
        highest = 1 << (value.bit_length() - 1) if value else 0
        opts = [highest, value, highest >> 1, (~highest) & 15, (highest + 1) & 15, 15, 2]
        distinct = []
        for x in opts:
            if x not in distinct:
                distinct.append(x)
        assert sum((highest >> i) & 1 for i in range(4)) <= 1
        emit(
            105,
            v,
            f"ממסכת בקשות x={word}, בונים מסכה באותו רוחב ששומרת רק את הביט הפעיל הגבוה ביותר. קלט אפס נותן אפס. מה מסכת המוצא?",
            f"From request mask x={word}, construct a same-width mask retaining only the highest set bit. Zero input produces zero. What is the output mask?",
            [f"{x:04b}" for x in distinct[:4]],
            (
                f"נשארת רק הבקשה בעלת האינדקס הגבוה ביותר: {highest:04b}; זהו וקטור ולא אינדקס בינארי.",
                f"Only the highest-index request remains: {highest:04b}; this is a vector, not a binary index.",
            ),
            "enumerate_highest_one_hot_request",
            dict(word=word),
            f"{highest:04b}",
        )

    for v, n in enumerate([4, 8, 16, 32, 64], 1):
        chain = n - 1
        tree = int(math.log2(n))
        gates = n - 1
        assert 2**tree == n
        emit(
            106,
            v,
            f"מאחדים {n} ביטי בקשה ב־OR באמצעות שערים בעלי שתי כניסות. מה העומק המרבי בשרשרת טורית ובעץ מאוזן, בסדר הזה? הניחו השהיה שווה לשער והתעלמו מחיווט ועומס.",
            f"Combine {n} bits using two-input OR gates. What are the maximum depths of a serial chain and a balanced tree, in that order? Assume equal gate delay and ignore wiring and loading.",
            [f"{chain}, {tree}", f"{tree}, {chain}", f"{n}, {n}", f"{tree}, {tree}"],
            (
                f"השרשרת עוברת עד {chain} שערים; העץ כולל {tree} רמות. בשניהם מספר השערים {gates}.",
                f"The chain crosses up to {chain} gates; the tree has {tree} levels. Both use {gates} gates.",
            ),
            "binary_tree_level_count",
            dict(inputs=n),
            dict(chain=chain, tree=tree, gates=gates),
        )

    for v, (initial, data, enable) in enumerate([(0, 1, 0), (1, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)], 1):
        value = data if enable else initial
        # A sequence asks more than a binary yes/no by presenting the outcome and operating mode together.
        mode = ("שקוף ל־D", "transparent to D") if enable else ("שומר את Q הקודם", "retains previous Q")
        opposite = ("שומר את Q הקודם", "retains previous Q") if enable else ("שקוף ל־D", "transparent to D")
        emit(
            107,
            v,
            f"מודל לאץ׳ לוגי אידיאלי משתמש ב־MUX עם S=EN, D0=Q, D1=D. תחילה Q={initial} יציב, ואז D={data}, EN={enable}. מה Q לאחר התייצבות ומה אופן הפעולה?",
            f"An ideal logical latch model uses a MUX with S=EN, D0=Q, D1=D. Initially Q={initial} is stable; then D={data}, EN={enable}. What is Q after settling, and what is the operating mode?",
            [
                (f"Q={value}; {mode[0]}", f"Q={value}; {mode[1]}"),
                (f"Q={1 - value}; {mode[0]}", f"Q={1 - value}; {mode[1]}"),
                (f"Q={value}; {opposite[0]}", f"Q={value}; {opposite[1]}"),
                ("Q תמיד מתאפס, ללא קשר לקלט", "Q always resets regardless of input"),
            ],
            (
                "בחירת D0 מחזירה ערך קודם יציב; בחירת D1 מעבירה את D. המשוב אינו מגדיר אתחול בעצמו.",
                "Selecting D0 feeds back a stable prior value; selecting D1 passes D. Feedback does not establish initialization by itself.",
            ),
            "MUX_latch_selection_contract",
            dict(initial=initial, data=data, enable=enable),
            value,
        )

    cases108 = [
        (
            "שני לאצ׳ים טוריים שקופים כש־CLK=1. D משתנה במהלך המצב הגבוה. מה עלול לקרות?",
            "Two serial latches are transparent when CLK=1. D changes during the high level. What may happen?",
            (
                "השינוי עלול לעבור דרך שני הלאצ׳ים באותו מצב גבוה",
                "The change may pass through both latches during that high level",
            ),
        ),
        (
            "ברגיסטר דו־לאצ׳י בעל חזית עולה, הראשון שקוף ב־CLK=0 והשני ב־CLK=1. מה הראשון עושה בחזית העולה?",
            "In a two-latch rising-edge register, the first is transparent at CLK=0 and the second at CLK=1. What does the first do at the rising edge?",
            ("נסגר ושומר את הדגימה עבור השני", "It closes and retains the sample for the second"),
        ),
        (
            "בזוג לאצ׳ים בפאזות הפוכות, הראשון נפתח שוב כש־CLK יורד ל־0. מה השני אמור לעשות אז, בהנחת תזמון תקין?",
            "With opposite-phase latches, the first reopens as CLK falls to 0. What should the second do then, assuming valid timing?",
            ("להיסגר ולשמור את מוצאו", "Close and retain its output"),
        ),
        (
            "תכנון דו־לאצ׳י אמור לדגום רק בחזית, אך בפועל שני הלאצ׳ים שקופים במשך פרק חפיפה. מה הסיכון?",
            "A two-latch design should sample only on an edge, but both latches are transparent during an overlap interval. What is the risk?",
            (
                "מרוץ שבו קלט חדש עובר מעבר לנקודת הדגימה המיועדת",
                "A race allowing new input past the intended sampling boundary",
            ),
        ),
        (
            "למה משתמשים בפאזות שקיפות הפוכות בשני לאצ׳ים טוריים למימוש רגיסטר?",
            "Why use opposite transparency phases for two serial latches forming a register?",
            (
                "כדי להפריד בין איסוף הדגימה לבין העברתה למוצא",
                "To separate capturing a sample from passing it to the output",
            ),
        ),
    ]
    wrong108 = [
        ("כל שינוי ב־D יוצר reset", "Every D change creates reset"),
        (
            "השארת שתי הפאזות פתוחות תמיד מבטיחה דגימת חזית",
            "Keeping both phases open always guarantees edge sampling",
        ),
        ("לאץ׳ אינו מושפע מרמת האפשור", "A latch ignores the enable level"),
    ]
    for v, (he, en, correct) in enumerate(cases108, 1):
        emit(
            108,
            v,
            he,
            en,
            [correct] + wrong108,
            (
                "פאזות הפוכות מונעות שקיפות רציפה אידיאלית דרך שני השלבים. יש עדיין לעמוד בדרישות תזמון ולהימנע מחפיפה פיזית בעייתית.",
                "Opposite phases prevent an ideal continuous transparent path through both stages. Timing requirements and problematic physical overlap still need attention.",
            ),
            "two_latch_phase_contract_case",
            dict(case=v),
        )

    for v, (sample, changes) in enumerate([(0, "1"), (1, "0"), (0, "10"), (1, "01"), (0, "101")], 1):
        output = [int(x) ^ sample for x in changes]
        good = ", ".join(map(str, output))
        candidates = [
            good,
            ", ".join(map(str, [1 - x for x in output])),
            ", ".join("0" for _ in output),
            ", ".join("1" for _ in output),
            ", ".join(str(sample) for _ in output),
        ]
        unique = []
        for x in candidates:
            if x not in unique:
                unique.append(x)
        # One transition only has two bit-valued answers; include full-sentence misconceptions.
        while len(unique) < 4:
            unique.append(
                ["המספר המצטבר של מעברים / Cumulative transition count", "Z / High impedance"][
                    len(unique) - 2
                ]
            )
        options = [(x.split(" / ")[0], x.split(" / ")[-1]) if " / " in x else x for x in unique[:4]]
        emit(
            109,
            v,
            f"Q שומר את דגימת In האחרונה, Q={sample}, ו־OUT=In XOR Q. בין חזיתות וללא השהיות, In מקבל ברצף את הערכים {', '.join(changes)}. מה סדרת OUT אחרי כל שינוי?",
            f"Q retains the last In sample, Q={sample}, and OUT=In XOR Q. Between edges, with zero delays, In takes successive values {', '.join(changes)}. What is the OUT sequence after each change?",
            options,
            (
                "XOR מציין אי־התאמה נוכחית לדגימה, ולא סופר או זוכר את כל המעברים שהתרחשו.",
                "XOR indicates current mismatch with the sample; it does not count or retain all transitions.",
            ),
            "XOR_mismatch_trace",
            dict(sample=sample, between_edge_values=changes),
            output,
        )

    for v, (period, transition) in enumerate([(10, 3), (10, 8), (12, 5), (20, 4), (16, 9)], 1):
        width = period - transition
        numeric(
            110,
            v,
            f"OUT=In XOR Q, ו־Q דוגם את In בחזיתות בזמן 0 ו־{period} ns. מיד אחרי זמן 0 הם שווים. In מתהפך פעם אחת בזמן {transition} ns ונשאר יציב. במודל אפס השהיה, לכמה ns יהיה OUT גבוה?",
            f"OUT=In XOR Q, with Q sampling In at 0 and {period} ns. Just after time 0 they match. In toggles once at {transition} ns and stays stable. In a zero-delay model, for how many ns is OUT high?",
            width,
            (
                f"אי־ההתאמה נמשכת מהמעבר ועד הדגימה הבאה: {period}−{transition}={width} ns.",
                f"Mismatch lasts from the transition until the next sample: {period}−{transition}={width} ns.",
            ),
            "mismatch_interval_until_next_edge",
            dict(period=period, transition=transition),
        )

    for v, (period, clock_high) in enumerate([(10, 2), (12, 3), (8, 6), (20, 4), (16, 12)], 1):
        emit(
            111,
            v,
            f"בדלגלג בעל חזית עולה D=NOT Q. מרווח החזיתות העולות הוא {period} ns, והשעון עצמו גבוה רק {clock_high} ns בכל מחזור. לאחר אתחול, מה מחזור Q ומה יחס הזמן הגבוה שלו במודל אפס השהיה?",
            f"A rising-edge flip-flop has D=NOT Q. Rising edges are {period} ns apart, and the clock itself is high for only {clock_high} ns each period. After initialization, what are Q's period and high duty cycle in a zero-delay model?",
            [
                (f"{2 * period} ns; 50%", f"{2 * period} ns; 50%"),
                (f"{period} ns; 50%", f"{period} ns; 50%"),
                (
                    f"{2 * period} ns; {clock_high / period * 100:g}%",
                    f"{2 * period} ns; {clock_high / period * 100:g}%",
                ),
                (f"{period} ns; 100%", f"{period} ns; 100%"),
            ],
            (
                f"Q מתהפך בכל חזית עולה: הוא גבוה {period} ns ונמוך {period} ns, בלי קשר לרוחב המצב הגבוה בשעון.",
                f"Q toggles at every rising edge: high for {period} ns and low for {period} ns, independent of clock high-pulse width.",
            ),
            "toggle_edge_spacing_waveform",
            dict(edge_period=period, clock_high=clock_high),
            dict(q_period=2 * period, duty_percent=50),
        )

    for v, (cq, logic, setup) in enumerate([(1, 2, 1), (2, 3, 1), (1, 4, 2), (3, 2, 2), (2, 5, 1)], 1):
        minimum = cq + logic + setup
        numeric(
            112,
            v,
            f"במשוב Q→XOR→D, clock-to-Q מרבי הוא {cq} ns, השהיית XOR וחיווט {logic} ns, ו־setup הוא {setup} ns. אין skew או אי־ודאות. Q מתהפך בכל חזית. מה T המזערי לפי בדיקת setup, ב־ns?",
            f"In Q→XOR→D feedback, maximum clock-to-Q is {cq} ns, XOR plus wiring delay is {logic} ns, and setup is {setup} ns. There is no skew or uncertainty. Q toggles at every edge. What is the minimum T from the setup check, in ns?",
            minimum,
            (
                f"המשוב חייב להתייצב עד החזית הבאה: T≥{cq}+{logic}+{setup}={minimum} ns. מחזור מוצא של 2T אינו מקנה מסלול רב־מחזורי.",
                f"Feedback must settle by the next edge: T≥{cq}+{logic}+{setup}={minimum} ns. An output period of 2T does not grant a multicycle path.",
            ),
            "one_cycle_feedback_setup_budget",
            dict(clock_to_q=cq, logic=logic, setup=setup),
        )

    for v, (count, previous, bits) in enumerate(
        [(4, 0, "1"), (4, 1, "101"), (3, 0, "101"), (2, 0, "10101"), (4, 0, "0111")], 1
    ):
        c = count
        prev = previous
        pulses = []
        for i, x in enumerate(map(int, bits), 1):
            rise = x and not prev
            pulse = bool(rise and c == 4)
            if pulse:
                pulses.append(i)
                c = 0
            elif rise:
                c += 1
            prev = x
        assert len(pulses) == 1
        numeric(
            113,
            v,
            f"מונה c סופר עליות של x מאז הפולס האחרון. פולס נוצר בעלייה החמישית ואז c מתאפס. prev שומר את הדגימה הקודמת. בתחילה c={count}, prev={previous}. דגימות x הן {bits}, משמאל לימין. באיזו דגימה, ממוספרת מ־1, נוצר פולס?",
            f"Counter c counts x rises since the last pulse. The fifth rise emits a pulse and clears c. prev stores the previous sample. Initially c={count}, prev={previous}. Samples of x are {bits}, left to right. At which sample, numbered from 1, is a pulse emitted?",
            pulses[0],
            (
                "עלייה מתקיימת רק כשהקלט החדש 1 והדגימה הקודמת 0. את בדיקת c=4 מבצעים מול המצב הישן.",
                "A rise requires new input 1 and previous sample 0. Check c=4 against the old state.",
            ),
            "rising_event_counter_state_trace",
            dict(initial_count=count, previous=previous, samples=bits),
            [1, 2, 3, 4, 5, 6],
        )

    for v, (window, threshold, bits) in enumerate(
        [(10, 3, "111"), (8, 2, "11"), (12, 4, "1111"), (10, 3, "110"), (6, 2, "101")], 1
    ):
        history = [0] * window
        for x in map(int, bits):
            history = history[1:] + [x]
        ones = sum(history)
        out = int(ones >= threshold)
        emit(
            114,
            v,
            f"גלאי מוציא 1 אם לפחות {threshold} מתוך {window} הדגימות האחרונות הן 1. ההיסטוריה שלפני ההתחלה מוגדרת כאפסים. לאחר דגימות {bits}, כמה אחדות בחלון ומה המוצא? אין תקופת המתנה למילוי החלון.",
            f"A detector outputs 1 if at least {threshold} of the latest {window} samples are 1. Pre-start history is defined as zeros. After samples {bits}, how many ones are in the window and what is the output? There is no warm-up invalid period.",
            [
                f"count={ones}; Y={out}",
                f"count={ones}; Y={1 - out}",
                f"count={window}; Y=1",
                ("המוצא בהכרח לא תקף עד מילוי החלון", "Output must be invalid until the window fills"),
            ],
            (
                "אפסי ההיסטוריה משתתפים בחלון. אם הסף כבר הושג, המוצא פעיל גם לפני שנקראו כל דגימות החלון.",
                "Historical zeros are part of the window. If the threshold is already reached, output is active even before a full window of real samples has arrived.",
            ),
            "zero_padded_window_explicit_history",
            dict(window=window, threshold=threshold, samples=bits),
            dict(count=ones, output=out),
        )

    for v, (real, limit) in enumerate([(4, 3), (5, 3), (6, 4), (7, 5), (8, 6)], 1):
        real_after = real - 1
        sat_after = limit - 1
        assert real_after >= limit and sat_after < limit
        emit(
            115,
            v,
            f"בחלון הזזה יש בפועל {real} אחדות, אך המונה נשמר ברוויה בסף {limit}. יוצאת מהחלון דגימת 1 ונכנסת דגימת 0. אם פשוט מחסרים 1 מהמונה הרווי, מה זוג הספירות: האמיתית והמחושבת?",
            f"A sliding window actually contains {real} ones, but the stored count saturates at threshold {limit}. A 1 leaves and a 0 enters. If one simply subtracts 1 from the saturated count, what are the actual and computed counts, in that order?",
            [
                f"{real_after}, {sat_after}",
                f"{sat_after}, {real_after}",
                f"{real_after}, {real_after}",
                f"{real}, {limit}",
            ],
            (
                f"הספירה האמיתית יורדת ל־{real_after}, אך המונה הרווי יורד ל־{sat_after}. המידע שנאבד ברוויה נחוץ כאשר דגימות פגות.",
                f"The real count falls to {real_after}, but the saturated count falls to {sat_after}. Information lost through saturation matters when samples expire.",
            ),
            "exact_vs_saturated_window_update",
            dict(actual=real, saturation=limit),
            [real_after, sat_after],
        )

    for v, threshold in enumerate([2, 3, 4, 5, 6], 1):
        bad = threshold + 1
        assert int(bad >= threshold) != int(bad == threshold)
        numeric(
            116,
            v,
            f"הדרישה היא Y=1 כאשר count≥{threshold}, אך המימוש משתמש ב־count=={threshold}. הבדיקות count=0 ו־count={threshold} עברו. איזה count חושף את הטעות?",
            f"The requirement is Y=1 when count≥{threshold}, but the implementation uses count=={threshold}. Tests at count=0 and count={threshold} passed. Which count exposes the error?",
            bad,
            (
                f"ב־count={bad}, הדרישה נותנת 1 אך בדיקת השוויון נותנת 0. צריך לבדוק גם מעל הסף.",
                f"At count={bad}, the requirement gives 1 while equality gives 0. Test above the threshold too.",
            ),
            "threshold_predicate_counterexample",
            dict(threshold=threshold),
            [0, threshold - 1, threshold],
        )

    for v, (window, threshold) in enumerate([(10, 3), (8, 3), (12, 4), (6, 2), (16, 4)], 1):
        one_positions = list(range(window - threshold + 2, window + 2))
        end = window + 1
        lo = end - window + 1
        actual = sum(lo <= i <= end for i in one_positions)
        reset_count = sum(i > window for i in one_positions)
        assert actual == threshold and reset_count < threshold
        emit(
            117,
            v,
            f"נדרש לפחות {threshold} אחדות בכל חלון הזזה של {window} דגימות. רק הדגימות {', '.join(map(str, one_positions))} הן 1; כולן ממוספרות מ־1. מימוש שגוי מאפס ספירה אחרי כל בלוק נפרד של {window} דגימות. מה המוצא הנדרש והמוצא השגוי בדגימה {end}, בסדר הזה?",
            f"Require at least {threshold} ones in every sliding window of {window} samples. Only samples {', '.join(map(str, one_positions))} are 1, with numbering from 1. A faulty implementation clears its count after each separate block of {window} samples. What are the required and faulty outputs at sample {end}, in that order?",
            ["1, 0", "0, 1", "0, 0", "1, 1"],
            (
                f"החלון המסתיים ב־{end} מכיל את כל {threshold} האחדות. איפוס בגבול הבלוק מאבד את אלו שלפניו.",
                f"The window ending at {end} contains all {threshold} ones. Resetting at a block boundary loses those before the boundary.",
            ),
            "sliding_interval_vs_disjoint_block_count",
            dict(window=window, threshold=threshold, one_positions=one_positions, query_sample=end),
            [1, 0],
        )

    for v, (address, old, new) in enumerate([(0, 3, 9), (2, 7, 4), (5, 1, 6), (7, 8, 2), (3, 5, 0)], 1):
        emit(
            118,
            v,
            f"ממשק זיכרון מבטיח write-first. באותו קצה יש קריאה וכתיבה פעילות לכתובת {address}: הערך הישן {old} ו־write_data={new}. הזיכרון הפנימי אינו מבטיח התנהגות התנגשות. איזה נתון יש לבחור ב־bypass עבור תגובת הקריאה, בתזמון שהחוזה מגדיר?",
            f"A memory interface promises write-first. The same edge has enabled read and write at address {address}: old value {old}, write_data={new}. Internal memory does not guarantee collision behavior. Which data should bypass select for the read response at the contract's response time?",
            [str(new), str(old), str(address), "NOT write_data"]
            if address not in (old, new)
            else [str(new), str(old), str(new + old + 1), "NOT write_data"],
            (
                f"בהתנגשות לאותה כתובת, write-first מחייב את הנתון החדש {new}. יש ליישר גם את תזמון התגובה ואת read_valid.",
                f"For a same-address collision, write-first requires new data {new}. Response timing and read_valid must also be aligned.",
            ),
            "write_first_same_address_bypass_contract",
            dict(address=address, old=old, write_data=new),
            new,
        )

    for v, (first, second) in enumerate([(0, 1), (0, 2), (1, 3), (2, 6), (3, 7)], 1):
        emit(
            119,
            v,
            f"כתובות לוגיות {first} ו־{second} עלולות להיות כינויים לאותו תא פיזי, במיפוי יציב. איזו בדיקה מפרידה ביניהן, בניגוד לכתיבת 1 לשתיהן? אין כותבים לכתובות אחרות במהלך הבדיקה.",
            f"Logical addresses {first} and {second} may alias the same physical cell under a stable mapping. Which test distinguishes them, unlike writing 1 to both? No other addresses are written during the test.",
            [
                (
                    f"לכתוב 0 ל־{first}, ואז 1 ל־{second}; לקרוא ולדרוש 0,1",
                    f"Write 0 to {first}, then 1 to {second}; read and require 0,1",
                ),
                ("לכתוב 1 לשתיהן ולדרוש 1,1", "Write 1 to both and require 1,1"),
                ("לקרוא שוב בלי לכתוב מידע ידוע", "Read again without writing known data"),
                ("לכתוב 0 לשתיהן ולדרוש 0,0", "Write 0 to both and require 0,0"),
            ],
            (
                "תא משותף אינו יכול להחזיק בו־זמנית את שני הערכים הצפויים השונים. דפוס אחיד מסתיר כינויים.",
                "One shared cell cannot simultaneously hold the two different expected values. A uniform pattern hides aliasing.",
            ),
            "stable_alias_two_address_memory_simulation",
            dict(first=first, second=second),
        )

    for v, (a, b, da, db) in enumerate(
        [(0, 1, 3, 7), (1, 2, 4, 9), (2, 3, 5, 8), (0, 3, 6, 2), (4, 7, 1, 0)], 1
    ):
        # A stable bijection merely renames physical cells; simulate writes and readback.
        physical = {}
        mapping = {a: b, b: a}
        physical[mapping[a]] = da
        physical[mapping[b]] = db
        assert [physical[mapping[a]], physical[mapping[b]]] == [da, db]
        emit(
            120,
            v,
            f"כל קריאה וכתיבה לכתובת לוגית {a} ניגשת בעקביות לתא הפיזי {b}, ולהפך. אין כינויים ואין גישה פיזית עצמאית. כותבים {da} לכתובת {a} ו־{db} לכתובת {b}. מה ייקרא מאותן כתובות, באותו סדר?",
            f"Every read and write to logical address {a} consistently uses physical cell {b}, and vice versa. There is no aliasing or independent physical access. Write {da} to address {a} and {db} to address {b}. What reads back from those addresses, in that order?",
            [f"{da}, {db}", f"{db}, {da}", f"{da}, {da}", f"{db}, {db}"],
            (
                "אותו מיפוי חד־חד־ערכי משמש לכתיבה ולקריאה, ולכן ההתנהגות הלוגית נשמרת. המספור הפיזי אינו ניתן לזיהוי דרך הממשק הזה.",
                "The same bijection serves writes and reads, preserving logical behavior. Physical numbering is not observable through this interface.",
            ),
            "bijective_address_permutation_simulation",
            dict(address_a=a, address_b=b, data_a=da, data_b=db),
            [da, db],
        )

    for v, width in enumerate([2, 3, 4, 5, 6], 1):
        depth = 2**width
        # Explicitly check that every pair is separated by at least one tested address bit.
        for a, b in itertools.combinations(range(depth), 2):
            assert any(((a >> bit) & 1) != ((b >> bit) & 1) for bit in range(width))
        numeric(
            121,
            v,
            f"בזיכרון חד־ביטי יש {depth} כתובות. בבדיקה כל מעבר כותב בכל כתובת את אחד מביטי הכתובת, ואז קורא ומשווה. כמה מעברים, אחד לכל ביט כתובת, מספיקים להפריד כל זוג כתובות תחת מודל כינויים יציב?",
            f"A one-bit memory has {depth} addresses. Each test pass writes one address bit at every address, then reads and compares. How many passes, one per address bit, suffice to distinguish every address pair under a stable aliasing model?",
            width,
            (
                f"כל זוג כתובות שונות נבדל בלפחות אחד מ־{width} ביטי הכתובת; באותו מעבר צפויים לו ערכים שונים.",
                f"Every distinct address pair differs in at least one of the {width} address bits; that pass expects different data values.",
            ),
            "exhaustive_address_pair_separation",
            dict(address_width=width, depth=depth),
        )

    for v, (copies, write) in enumerate([(2, 1), (3, 0), (4, 1), (2, 0)], 1):
        available = 0 if write else copies
        numeric(
            122,
            v,
            f"יש {copies} עותקים זהים ועדכניים של זיכרון חד־פורט. כל כתיבה חייבת להתבצע בכל העותקים באותו קצה; כל פורט מבצע פעולה אחת בקצה. write={write} מציין אם נדרשת כתיבה כזאת בקצה הנוכחי. כמה קריאות מכתובות שונות אפשר לבצע בו לכל היותר באמצעות הפורטים הפנויים?",
            f"There are {copies} identical, current single-port memory copies. Every write must update all copies at the same edge; each port performs one operation per edge. write={write} indicates whether such a write is required at this edge. At most how many reads from different addresses can the free ports perform?",
            available,
            (
                "בקצה כתיבה כל הפורטים תפוסים. בקצה ללא כתיבה כל עותק יכול לשרת קריאה אחת.",
                "On a write edge all ports are occupied. Without a write, each copy can serve one read.",
            ),
            "single_port_operation_budget",
            dict(copies=copies, write=write),
            [0, 1, copies, copies + 1],
        )
    emit(
        122,
        5,
        "שני עותקי זיכרון חד־פורט אמורים להישאר זהים. כדי לפנות פורט לקריאה, כתיבה מעדכנת רק את העותק הראשון. מה הבעיה אם רוצים לקרוא בהמשך את הכתובת שנכתבה מהעותק השני?",
        "Two single-port memory copies should remain identical. To free a read port, a write updates only the first copy. What is the problem if that address is later read from the second copy?",
        [
            ("העותק השני עלול להחזיר מידע ישן", "The second copy may return stale data"),
            ("שני העותקים מתעדכנים אוטומטית", "Both copies update automatically"),
            (
                "אין בעיה כי כתובות שונות מחייבות מידע שונה",
                "There is no problem because different addresses require different data",
            ),
            (
                "הפורט השני נהפך לפורט כתיבה נוסף בלי עדכון",
                "The second port becomes an extra write port without an update",
            ),
        ],
        (
            "עותק שלא קיבל את הכתיבה אינו בהכרח עדכני. פינוי פורט דורש גם מנגנון עקביות מתאים.",
            "A copy that missed the write is not necessarily current. Freeing a port also requires a suitable coherence mechanism.",
        ),
        "replicated_memory_freshness_counterexample",
        dict(copies=2, written_copies=[0], later_read_copy=1),
    )

    for v, (read, write) in enumerate([(0, 2), (0, 1), (3, 5), (4, 7), (6, 8)], 1):
        rb = read % 2
        wb = write % 2
        conflict = rb == wb
        good = (
            f"בנקים {rb},{wb}; {'קונפליקט' if conflict else 'אין קונפליקט'}",
            f"Banks {rb},{wb}; {'conflict' if conflict else 'no conflict'}",
        )
        emit(
            123,
            v,
            f"זיכרון מחולק לשני בנקים חד־פורטיים לפי זוגיות הכתובת: זוגית בבנק 0, אי־זוגית בבנק 1. מבקשים לקרוא מ־{read} ולכתוב ל־{write} באותו קצה, ללא מנגנון נוסף. לאילו בנקים ניגשים, והאם יש קונפליקט פורט?",
            f"Memory is split into two single-port banks by address parity: even in bank 0, odd in bank 1. Request a read from {read} and write to {write} at one edge, without another mechanism. Which banks are accessed, and is there a port conflict?",
            [
                good,
                (
                    f"בנקים {rb},{wb}; {'אין קונפליקט' if conflict else 'קונפליקט'}",
                    f"Banks {rb},{wb}; {'no conflict' if conflict else 'conflict'}",
                ),
                (f"בנקים {1 - rb},{1 - wb}; תמיד אין קונפליקט", f"Banks {1 - rb},{1 - wb}; never a conflict"),
                (
                    "שני בנקים מבטיחים כל זוג פעולות במקביל",
                    "Two banks guarantee every pair of operations in parallel",
                ),
            ],
            (
                "כל בנק מאפשר פעולה אחת בקצה. שתי כתובות בעלות אותה זוגיות מתחרות על אותו פורט.",
                "Each bank permits one operation per edge. Two addresses of the same parity compete for that port.",
            ),
            "bank_mapping_modulo_two_conflict",
            dict(read_address=read, write_address=write),
            dict(read_bank=rb, write_bank=wb, conflict=conflict),
        )

    for v, (threshold, before, last) in enumerate(
        [(10, 10, 1), (10, 9, 1), (4, 4, 1), (5, 5, 0), (6, 6, 1)], 1
    ):
        total = before + last
        failed = total > threshold
        correct = (
            f"{total}; {'נכשל' if failed else 'לא נכשל'}",
            f"{total}; {'failed' if failed else 'not failed'}",
        )
        emit(
            124,
            v,
            f"מנטרים בלוקים נפרדים של 100000 דגימות. בלוק נכשל רק אם מספר השגיאות גדול מ־{threshold}. לפני הדגימה האחרונה נספרו {before} שגיאות; ERROR בדגימה האחרונה הוא {last}. מה מספר השגיאות הכולל ותוצאת הבלוק, לפני איפוס לבלוק הבא?",
            f"Monitor separate blocks of 100000 samples. A block fails only if its error count exceeds {threshold}. Before the final sample there are {before} errors; final ERROR is {last}. What are the total count and block result before resetting for the next block?",
            [
                correct,
                (
                    f"{total}; {'לא נכשל' if failed else 'נכשל'}",
                    f"{total}; {'not failed' if failed else 'failed'}",
                ),
                (f"{total + 1}; נכשל", f"{total + 1}; failed"),
                ("0; לא נכשל בגלל האיפוס", "0; not failed because of reset"),
            ],
            (
                "כוללים את הדגימה האחרונה, בודקים את הסף ושומרים את תוצאת הבלוק; רק אז מתחילים ספירה חדשה.",
                "Include the final sample, evaluate the threshold, and retain the block result; only then begin a new count.",
            ),
            "inclusive_final_sample_block_threshold",
            dict(threshold=threshold, before_last=before, last_error=last),
            dict(total=total, failed=failed),
        )

    for v, period_cycles in enumerate([3, 5, 7, 9, 11], 1):
        required = period_cycles / 2
        assert not required.is_integer()
        choices = [
            (f"{required:g}T; בלתי אפשרי בתנאים האלה", f"{required:g}T; impossible under these restrictions"),
            (f"{period_cycles // 2}T; נותן בדיוק 50%", f"{period_cycles // 2}T; gives exactly 50%"),
            (f"{period_cycles}T; נותן בדיוק 50%", f"{period_cycles}T; gives exactly 50%"),
            ("T; תמיד נותן 50% לכל מחזור", "T; always gives 50% for every period"),
        ]
        emit(
            125,
            v,
            f"מוצא בינארי רשום יכול להשתנות רק בחזיתות עולות שמרחקן T. רוצים גל חוזר בעל מחזור {period_cycles}T ו־50% זמן גבוה בכל מחזור. מה משך המצב הגבוה הנדרש, והאם הוא אפשרי תחת המגבלה?",
            f"A registered binary output may change only on rising edges spaced T apart. A repeating waveform must have period {period_cycles}T and 50% high time in every period. What high duration is required, and is it possible under this restriction?",
            choices,
            (
                f"נדרש {required:g}T גבוה, אך זמני שינוי בחזיתות עולות בלבד מאפשרים משכים שהם כפולות שלמות של T.",
                f"High duration must be {required:g}T, but rising-edge-only changes allow only integer multiples of T.",
            ),
            "integer_edge_grid_half_period_impossibility",
            dict(period_cycles=period_cycles),
            dict(required_high_cycles=required, possible=False),
        )


def build():
    QUESTIONS.clear()
    CHECKS.clear()
    run()
    grouped = {}
    for question in QUESTIONS:
        grouped.setdefault(question["source_key"], []).append(question["variant"])
    assert set(grouped) == set(SOURCES), sorted(set(SOURCES) - set(grouped))
    assert all(sorted(variants) == [1, 2, 3, 4, 5] for variants in grouped.values())
    assert len(QUESTIONS) == 325
    return list(QUESTIONS), list(CHECKS)


if __name__ == "__main__":
    questions, checks = build()
    folder = ROOT / "backend/seeds/duel_quiz_batches"
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in [("hardware_advanced.json", questions), ("hardware_advanced.checks.json", checks)]:
        (folder / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified and wrote {len(questions)} variants for {len(SOURCES)} sources.")
