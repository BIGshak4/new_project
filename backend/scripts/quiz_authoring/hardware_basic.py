"""Author and check five bilingual variants of each owned basic hardware card.

All questions stay drafts. Checks are reproducible finite models, not human approval.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CARDS = {
    int(q["id"].split("-")[-1]): q
    for q in json.loads(
        (ROOT / "apps/web/src/content/fundamentals-hardware.json").read_text(encoding="utf-8")
    )
}
QUESTIONS, CHECKS = [], []
EXISTING = {3, 5, 9, 10, 15, 21, 40}


def pair(he, en=None):
    return {"he": str(he), "en": str(he if en is None else en)}


def text(value):
    if isinstance(value, list):
        return ", ".join(map(str, value))
    return str(value)


def emit(n, v, he, en, good, bad, ehe, een, kind, inputs):
    def loc(x):
        return pair(*x) if isinstance(x, tuple) else pair(text(x))

    options = [loc(good)] + [loc(x) for x in bad]
    assert len(options) == 4
    assert all(len({o[lang] for o in options}) == 4 for lang in ("he", "en")), (n, v, options)
    rotation = (n + v) % 4
    options = options[rotation:] + options[:rotation]
    key = f"quick-hw-{n:02d}-v{v}"
    q = {
        "key": key,
        "source_key": f"quick-hw-{n:02d}",
        "variant": v,
        "topic": CARDS[n]["topic"],
        "status": "draft",
        "prompt": pair(he, en),
        "choices": options,
        "correct": (4 - rotation) % 4,
        "explanation": pair(ehe, een),
    }
    QUESTIONS.append(q)
    CHECKS.append({"key": key, "method": kind, "inputs": inputs, "expected": loc(good)})


def numeric(n, v, he, en, result, ehe, een, kind, inputs, options=None):
    bad = [x for x in (options or [result + 1, result - 1, result + 2, result + 3, 0, 1]) if x != result]
    bad = list(dict.fromkeys(bad))[:3]
    emit(n, v, he, en, result, bad, ehe, een, kind, inputs)


def binary(n, v, he, en, value, width, ehe, een, kind, inputs):
    candidates = [value ^ (1 << i) for i in range(width)]
    candidates += [(value + 1) % (1 << width), (value + 2) % (1 << width)] + list(range(1 << width))
    wrong = list(dict.fromkeys(x for x in candidates if x != value))[:3]
    emit(
        n,
        v,
        he,
        en,
        format(value, f"0{width}b"),
        [format(x, f"0{width}b") for x in wrong],
        ehe,
        een,
        kind,
        inputs,
    )


def seq(n, v, he, en, values, ehe, een, kind, inputs, width=None):
    def fmt(xs):
        return ", ".join(format(x, f"0{width}b") if width else str(x) for x in xs)

    wrong = []
    for i in range(len(values)):
        xs = list(values)
        xs[i] ^= 1
        wrong.append(fmt(xs))
        if len(wrong) == 3:
            break
    assert len(wrong) == 3
    emit(n, v, he, en, fmt(values), wrong, ehe, een, kind, inputs)


def simulate(kind, p):
    """Independent recurrence / bit-weight calculations for generated cases."""
    if kind == "truth":

        def f(xs):
            a, b = xs[:2]
            return {
                "and": a * b,
                "or": int(a + b > 0),
                "nand": int(a * b == 0),
                "nor": int(a + b == 0),
                "xnor": int(a == b),
                "majority": int(sum(xs) >= 2),
                "factor": int(a and (b or xs[-1])),
            }[p["operation"]]

        return [f(xs) for xs in p["rows"]]
    if kind == "invert":
        return sum((1 - int(b)) * 2**i for i, b in enumerate(reversed(p["word"])))
    if kind == "absorb":
        return [int(a or (a and b)) for a, b in p["rows"]]
    if kind == "shift_left":
        bits = format(p["value"], f"0{p['width']}b")
        return int((bits[p["shift"] :] + "0" * p["shift"])[-p["width"] :], 2)
    if kind == "mask":
        return p["value"] & (2 ** p["bit"])
    if kind == "setclear":
        bits = list(format(p["value"], "08b"))
        bits[7 - p["bit"]] = str(p["target"])
        return int("".join(bits), 2)
    if kind == "parity":
        return [sum(map(int, word)) % 2 for word in p["words"]]
    if kind == "pipe":
        state = p["initial"][:]
        out = []
        for x in p["inputs"]:
            state = [x] + state[:-1]
            out.append(int("".join(map(str, state)), 2))
        return out
    if kind == "toggle":
        q, out = p["initial"], []
        for t in p["inputs"]:
            q = q ^ t
            out.append(q)
        return out
    if kind == "reset_register":
        rst = p["rst"] == p["active"]
        return 0 if rst else (p["data"] if p["enable"] else p["initial"])
    if kind == "sync_async":
        sync, async_ = p["initial"], p["initial"]
        if p["reset"]:
            async_ = 0
        if p["edge"] and p["reset"]:
            sync = 0
        return [sync, async_]
    if kind in {"rise", "run11", "sticky", "pairs11", "vending", "stream_parity"}:
        state, out = p["initial"], []
        for x in p["inputs"]:
            if kind == "rise":
                y, state = int(x == 1 and state == 0), x
            elif kind == "pairs11":
                y, state = x * state, x
            elif kind == "run11":
                state = state + 1 if x else 0
                y = int(state >= 2)
            elif kind == "sticky":
                state = int(state or x)
                y = state
            elif kind == "stream_parity":
                state = state ^ x
                y = state
            else:
                y = state * x
                state = (state + x) % 2
            out.append(y)
        return out
    if kind == "statebits":
        width = 0
        while 2**width < p["states"]:
            width += 1
        return [width, 2**width - p["states"]]
    if kind == "cycle":
        state = p["initial"]
        for _ in range(p["edges"]):
            state = (state + 1) % p["states"]
        return state
    if kind == "to_binary":
        return format(p["value"], f"0{p['width']}b")
    if kind == "signed_pair":
        bits = p["word"]
        unsigned = sum(int(b) * 2**i for i, b in enumerate(reversed(bits)))
        signed = unsigned - int(bits[0]) * 2 ** len(bits)
        return [unsigned, signed]
    if kind == "signextend":
        return p["word"][0] * (p["width"] - len(p["word"])) + p["word"]
    if kind == "onehot":
        return [w for w in p["words"] if sum(map(int, w)) == 1][0]
    if kind == "fulladder":
        s = p["a"] + p["b"] + p["cin"]
        return format(s, "02b")
    if kind == "rightshift":
        word = p["word"]
        return ["0" + word[:-1], word[0] + word[:-1]]
    if kind == "enabled_counter":
        value, out = p["initial"], []
        for en in p["inputs"]:
            if en:
                value = (value + 1) % 2 ** p["width"]
            out.append(value)
        return out
    if kind == "down":
        value = p["initial"]
        for _ in range(p["edges"]):
            value = (value - 1) % 2 ** p["width"]
        return value
    if kind == "counter_bit":
        return [((p["initial"] + e) // 2 ** p["bit"]) % 2 for e in range(1, p["edges"] + 1)]
    if kind == "busy":
        state, out = p["initial"], []
        for r, d in p["inputs"]:
            state = (0 if d else 1) if state else (1 if r else 0)
            out.append(state)
        return out
    if kind == "onehot_width":
        return len(list(range(p["states"])))
    if kind == "priority":
        return ["A" if a else "B" if b else "S" for a, b in p["rows"]]
    if kind == "recovery":
        value = p["initial"]
        for _ in range(p["edges"]):
            value = p["recovery"] if value == 3 else (value + 1) % 3
        return value
    raise ValueError(kind)


def build():
    QUESTIONS.clear()
    CHECKS.clear()
    # Gates: output sequences use distinct input orders, with a fifth identification case.
    operations = {
        1: "and",
        2: "or",
        6: "nand",
        7: "majority",
        31: "nand",
        32: "nor",
        33: "xnor",
        38: "factor",
    }
    descriptions = {
        1: ("המוצא הוא 1 אם ורק אם שתי הכניסות הן 1", "The output is 1 if and only if both inputs are 1"),
        2: ("המוצא הוא 1 כאשר לפחות כניסה אחת היא 1", "The output is 1 when at least one input is 1"),
        6: ("המוצא הוא NOT של A AND B", "The output is NOT of A AND B"),
        7: (
            "המוצא הוא 1 אם לפחות שניים משלושת הביטים הם 1",
            "The output is 1 if at least two of the three bits are 1",
        ),
        31: ("שער AND מזין שער NOT", "An AND gate feeds a NOT gate"),
        32: ("המוצא הוא 1 אם ורק אם שתי הכניסות הן 0", "The output is 1 if and only if both inputs are 0"),
        33: (
            "המוצא הוא 1 אם ורק אם שני הביטים שווים",
            "The output is 1 if and only if the two bits are equal",
        ),
        38: ("Y=(A AND B) OR (A AND C)", "Y=(A AND B) OR (A AND C)"),
    }
    for n, op in operations.items():
        arity = 3 if n in (7, 38) else 2
        allrows = list(itertools.product((0, 1), repeat=arity))
        for v in range(1, 6):
            orders = (
                [[0, 1, 2, 3], [3, 2, 1, 0], [1, 3, 0, 2], [2, 0, 3, 1], [0, 3, 1, 2]]
                if arity == 2
                else [[0, 3, 5, 7], [7, 6, 4, 1], [2, 5, 1, 6], [4, 2, 7, 0], [3, 6, 0, 5]]
            )
            rows = [list(allrows[i]) for i in orders[v - 1]]
            p = {"operation": op, "rows": rows}
            result = simulate("truth", p)
            rs = "; ".join("".join(map(str, r)) for r in rows)
            variables = "ABC" if arity == 3 else "AB"
            ehe = {
                "and": "רק זוג כניסות שערכן 1 נותן מוצא 1.",
                "or": "די בכניסה אחת שערכה 1 כדי לקבל מוצא 1.",
                "nand": "NAND נותן 0 רק כאשר שתי הכניסות הן 1.",
                "nor": "NOR נותן 1 רק כאשר שתי הכניסות הן 0.",
                "xnor": "XNOR נותן 1 כאשר הביטים שווים.",
                "majority": "סופרים את האחדות בכל שלישייה; נדרשות לפחות שתיים.",
                "factor": "הביטוי שקול ל־A AND (B OR C).",
            }[op]
            een = {
                "and": "Only two inputs equal to 1 produce 1.",
                "or": "At least one input equal to 1 is sufficient.",
                "nand": "NAND outputs 0 only when both inputs are 1.",
                "nor": "NOR outputs 1 only when both inputs are 0.",
                "xnor": "XNOR outputs 1 when the two bits match.",
                "majority": "Count the ones in each triple; at least two are required.",
                "factor": "The expression equals A AND (B OR C).",
            }[op]
            if v == 1:
                seq(
                    n,
                    v,
                    f"{descriptions[n][0]}. אחרי התייצבות האותות, מהם המוצאים לפי הסדר עבור {variables}: {rs}?",
                    f"{descriptions[n][1]}. After signals settle, what are the outputs in order for {variables}: {rs}?",
                    result,
                    ehe,
                    een,
                    "truth",
                    p,
                )
            elif v == 2:
                if n in (7, 38):
                    good = "(A AND B) OR (A AND C) OR (B AND C)" if n == 7 else "A AND (B OR C)"
                    bad = ["A XOR B XOR C", "A AND B AND C", "A OR B OR C"]
                else:
                    good = {"and": "AND", "or": "OR", "nand": "NAND", "nor": "NOR", "xnor": "XNOR"}[op]
                    bad = [g for g in ["AND", "OR", "NAND", "NOR", "XOR", "XNOR"] if g != good][:3]
                emit(
                    n,
                    v,
                    f"{descriptions[n][0]}. איזה מהביטויים או השערים הבאים מממש כלל זה לכל הקלטים?",
                    f"{descriptions[n][1]}. Which expression or gate implements this rule for every input?",
                    good,
                    bad,
                    ehe,
                    een,
                    "gate_identity",
                    {"operation": op, "expression": good, "arity": arity},
                )
            elif v == 3:
                count = sum(result)
                numeric(
                    n,
                    v,
                    f"{descriptions[n][0]}. בודקים בנפרד את הקלטים {variables}: {rs}. בכמה מהבדיקות המוצא הוא 1?",
                    f"{descriptions[n][1]}. Test the inputs {variables}: {rs} independently. In how many tests is the output 1?",
                    count,
                    ehe,
                    een,
                    "truth_count",
                    p,
                    options=[0, 1, 2, 3, 4],
                )
            elif v == 4:
                total = sum(simulate("truth", {"operation": op, "rows": [list(x) for x in allrows]}))
                numeric(
                    n,
                    v,
                    f"{descriptions[n][0]}. בודקים את כל {2**arity} צירופי הקלט השונים, פעם אחת כל צירוף. בכמה צירופים המוצא הוא 1?",
                    f"{descriptions[n][1]}. Test all {2**arity} distinct input combinations, once each. In how many combinations is the output 1?",
                    total,
                    ehe,
                    een,
                    "truth_count",
                    {"operation": op, "rows": [list(x) for x in allrows]},
                    options=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                )
            else:
                if arity == 2:
                    reduced_rows = [[1, 0], [1, 1]]
                    reduced = simulate("truth", {"operation": op, "rows": reduced_rows})
                    good = text(reduced)
                    emit(
                        n,
                        v,
                        f"{descriptions[n][0]}. מחזיקים A=1 ומשנים את B מ־0 ל־1. מהם שני ערכי המוצא לפי הסדר?",
                        f"{descriptions[n][1]}. Hold A=1 and change B from 0 to 1. What are the two output values in order?",
                        good,
                        [text(x) for x in [[0, 0], [0, 1], [1, 0], [1, 1]] if text(x) != good],
                        ehe,
                        een,
                        "truth",
                        {"operation": op, "rows": reduced_rows},
                    )
                else:
                    reduced_rows = [[1, b, c] for b, c in itertools.product((0, 1), repeat=2)]
                    reduced = simulate("truth", {"operation": op, "rows": reduced_rows})
                    seq(
                        n,
                        v,
                        f"{descriptions[n][0]}. מחזיקים A=1. מהם המוצאים עבור BC=00,01,10,11, לפי הסדר?",
                        f"{descriptions[n][1]}. Hold A=1. What are the outputs for BC=00,01,10,11, in order?",
                        reduced,
                        ehe,
                        een,
                        "truth",
                        {"operation": op, "rows": reduced_rows},
                    )

    for v, word in enumerate(["0011", "1010", "1110", "0001", "1001"], 1):
        result = simulate("invert", {"word": word})
        binary(
            4,
            v,
            f"ארבעה ביטים, {word}, עוברים כל אחד דרך שער NOT אחד. מהי מילת המוצא לאחר התייצבות?",
            f"Each of the four bits in {word} passes through one NOT gate. What is the settled output word?",
            result,
            4,
            "כל שער NOT מחליף 0 ב־1 ו־1 ב־0.",
            "Each NOT gate changes 0 to 1 and 1 to 0.",
            "invert",
            {"word": word},
        )

    for v in range(1, 6):
        rows = [list(x) for x in list(itertools.product((0, 1), repeat=2))]
        rows = rows[v % 4 :] + rows[: v % 4]
        if v == 5:
            rows = [rows[i] for i in [0, 2, 3, 1]]
        rs = "; ".join("".join(map(str, r)) for r in rows)
        ehe = "לפי חוק הספיגה, Y=A; שינוי B אינו משנה את המוצא."
        een = "By absorption, Y=A; changing B cannot change the output."
        if v == 1:
            seq(
                8,
                v,
                f"Y=A OR (A AND B). מהם ערכי Y לפי הסדר עבור AB: {rs}?",
                f"Y=A OR (A AND B). What are the Y values in order for AB: {rs}?",
                simulate("absorb", {"rows": rows}),
                ehe,
                een,
                "absorb",
                {"rows": rows},
            )
        elif v == 2:
            emit(
                8,
                v,
                "איזה ביטוי שקול ל־A OR (A AND B) עבור כל שני ביטים A,B?",
                "Which expression equals A OR (A AND B) for all bits A,B?",
                "A",
                ["B", "A AND B", "A OR B"],
                ehe,
                een,
                "absorption_concept",
                {"case": "identity"},
            )
        elif v == 3:
            emit(
                8,
                v,
                "Y=A OR (A AND B). מחזיקים A=1 ומשנים את B. מה נכון לאחר התייצבות האותות?",
                "Y=A OR (A AND B). Hold A=1 and vary B. Which statement is true after signals settle?",
                ("Y נשאר 1", "Y stays 1"),
                [
                    ("Y עוקב אחר B", "Y follows B"),
                    ("Y עוקב אחר NOT B", "Y follows NOT B"),
                    ("Y נשאר 0", "Y stays 0"),
                ],
                ehe,
                een,
                "absorption_concept",
                {"case": "fixed_one"},
            )
        elif v == 4:
            emit(
                8,
                v,
                "נתון Y=A OR (A AND B), והמוצא הוא 0. מה אפשר להסיק בהכרח על הביטים?",
                "Given Y=A OR (A AND B), the output is 0. What necessarily follows about the bits?",
                ("A=0; B יכול להיות 0 או 1", "A=0; B may be 0 or 1"),
                [
                    ("A=1; B=0", "A=1; B=0"),
                    ("A=1; B=1", "A=1; B=1"),
                    ("B=0; A יכול להיות 0 או 1", "B=0; A may be 0 or 1"),
                ],
                ehe,
                een,
                "absorption_concept",
                {"case": "inverse_zero"},
            )
        else:
            emit(
                8,
                v,
                "במעגל Y=A OR (A AND B), איזה ענף של שער ה־OR אפשר להסיר בלי לשנות את Y עבור שום קלט?",
                "In Y=A OR (A AND B), which OR-input branch can be removed without changing Y for any input?",
                ("הענף A AND B", "The A AND B branch"),
                [
                    ("הענף A", "The A branch"),
                    ("שני הענפים יחד", "Both branches together"),
                    ("אי אפשר להסיר אף ענף", "Neither branch can be removed"),
                ],
                ehe,
                een,
                "absorption_concept",
                {"case": "remove_branch"},
            )

    for v, (value, shift) in enumerate([(19, 1), (71, 1), (45, 2), (129, 1), (13, 3)], 1):
        p = {"value": value, "width": 8, "shift": shift}
        result = simulate("shift_left", p)
        binary(
            11,
            v,
            f"מזיזים את המילה הלא מסומנת {value:08b} שמאלה ב־{shift} מיקומים, מכניסים אפסים מימין ושומרים רק 8 ביטים. מה נשמר?",
            f"Shift unsigned {value:08b} left by {shift} positions, insert zeros on the right, and keep only 8 bits. What is stored?",
            result,
            8,
            f"מכפילים ב־{2**shift} ושומרים את השארית בחלוקה ב־256: {result:08b}.",
            f"Multiply by {2**shift} and retain the remainder modulo 256: {result:08b}.",
            "shift_left",
            p,
        )

    for v, (value, bit) in enumerate([(106, 2), (173, 5), (89, 4), (204, 3), (53, 0)], 1):
        p = {"value": value, "bit": bit}
        result = simulate("mask", p)
        binary(
            12,
            v,
            f"במילה {value:08b}, מספור הביטים מתחיל ב־0 מימין. מה תוצאת AND עם מסכה שמבודדת רק את ביט {bit}?",
            f"In word {value:08b}, bit numbering starts at 0 on the right. What is the result of AND with a mask isolating only bit {bit}?",
            result,
            8,
            f"המסכה היא {1 << bit:08b}; AND מאפס את כל הביטים האחרים.",
            f"The mask is {1 << bit:08b}; AND clears every other bit.",
            "mask",
            p,
        )

    for v, (value, bit, target) in enumerate([(80, 3, 1), (95, 4, 0), (34, 6, 1), (227, 5, 0), (7, 7, 1)], 1):
        p = {"value": value, "bit": bit, "target": target}
        result = simulate("setclear", p)
        binary(
            13,
            v,
            f"מתחילים במילה {value:08b}. יש לקבוע את ביט {bit} לערך {target}, בלי לשנות ביטים אחרים; ביט 0 הוא הימני. מה התוצאה?",
            f"Start with word {value:08b}. Set bit {bit} to {target}, leaving all other bits unchanged; bit 0 is the rightmost bit. What is the result?",
            result,
            8,
            "לקביעת 1 משתמשים ב־OR עם מסכת הביט; לקביעת 0 משתמשים ב־AND עם המסכה המהופכת.",
            "To write 1, OR with the bit mask; to write 0, AND with its complement.",
            "setclear",
            p,
        )

    for v, words in enumerate(
        [
            ["111", "110", "000", "001"],
            ["100", "101", "011", "010"],
            ["000", "111", "101", "100"],
            ["010", "011", "001", "110"],
            ["101", "001", "111", "000"],
        ],
        1,
    ):
        p = {"words": words}
        seq(
            14,
            v,
            f"מחשבים XOR של שלושת הביטים בכל מילה. מהם המוצאים לפי הסדר עבור {', '.join(words)}?",
            f"Compute the XOR of the three bits in each word. What are the outputs in order for {', '.join(words)}?",
            simulate("parity", p),
            "XOR של הביטים הוא 1 כאשר מספר האחדות אי־זוגי.",
            "XOR of the bits is 1 when the number of ones is odd.",
            "parity",
            p,
        )

    for v, (init, xs) in enumerate(
        [
            ([0, 0], [1, 1, 1]),
            ([1, 0], [0, 0, 0]),
            ([0, 1], [1, 0, 1]),
            ([1, 1], [0, 1, 0]),
            ([0, 0], [0, 1, 0, 1]),
        ],
        1,
    ):
        p = {"initial": init, "inputs": xs}
        result = simulate("pipe", p)
        seq(
            16,
            v,
            f"שני דלגלגי D דוגמים באותה חזית עולה: D1=x, D2=Q1. מתחילים ב־Q1Q2={''.join(map(str, init))}, ללא איפוס נוסף. ערכי x היציבים בחזיתות הם {text(xs)}. מהם ערכי Q1Q2 לאחר כל חזית?",
            f"Two D flip-flops sample on the same rising edge: D1=x, D2=Q1. Start at Q1Q2={''.join(map(str, init))}, with no further reset. Stable x values at the edges are {text(xs)}. What is Q1Q2 after each edge?",
            result,
            "בכל חזית Q2 מקבל את Q1 הישן, ו־Q1 מקבל את x.",
            "At each edge, Q2 samples old Q1 while Q1 samples x.",
            "pipe",
            p,
            width=2,
        )

    for n in (17, 18, 22, 23):
        for v, (initial, xs) in enumerate(
            [(0, [1, 1, 1, 1]), (1, [1, 1, 1]), (0, [1, 0, 1, 1]), (1, [0, 1, 0, 1]), (0, [0, 0, 1, 0])], 1
        ):
            if n == 18:
                xs = [0] * (v + 2)
                initial = v % 2
            if n == 22:
                xs = [1] * (v + 2)
                initial = v % 2
            p = {"initial": initial, "inputs": xs}
            result = simulate("toggle", p)
            if n == 22:
                he = f"דלגלג D מחובר כך ש־D=NOT Q ודוגם בחזית עולה. מתחילים ב־Q={initial}, ללא איפוס. מהם ערכי Q לאחר {len(xs)} החזיתות הבאות?"
                en = f"A rising-edge D flip-flop has D=NOT Q. Start with Q={initial}, with no reset. What are the Q values after the next {len(xs)} edges?"
            elif n == 23:
                he = f"נורה נשלטת על ידי ביט מצב Q, שמתחיל ב־{initial}. בכל חזית עולה t=1 הופך את Q ו־t=0 משאיר אותו. ללא איפוס, מהם ערכי Q אחרי קלטי t: {text(xs)}?"
                en = f"A light is controlled by state bit Q, initially {initial}. At each rising edge, t=1 toggles Q and t=0 holds it. With no reset, what are Q values after t inputs: {text(xs)}?"
            else:
                he = f"דלגלג T מתחיל ב־Q={initial}. בכל חזית עולה T=1 הופך את Q ו־T=0 משאיר אותו. אין איפוס. מהם ערכי Q אחרי קלטי T: {text(xs)}?"
                en = f"A T flip-flop starts at Q={initial}. At each rising edge, T=1 toggles Q and T=0 holds it. There is no reset. What are Q values after T inputs: {text(xs)}?"
            seq(
                n,
                v,
                he,
                en,
                result,
                "מחשבים בכל חזית Q החדש = Q הישן XOR T; באינוורטר המשוב T שקול ל־1.",
                "At each edge, new Q equals old Q XOR T; inverter feedback is equivalent to T=1.",
                "toggle",
                p,
            )

    for n, active in [(19, 1), (50, 0)]:
        for v, (initial, data, en, rst_active) in enumerate(
            [(3, 2, 0, True), (2, 1, 1, True), (1, 3, 0, False), (0, 2, 1, False), (3, 1, 1, False)], 1
        ):
            rst = active if rst_active else 1 - active
            p = {"initial": initial, "data": data, "enable": en, "rst": rst, "active": active}
            result = simulate("reset_register", p)
            binary(
                n,
                v,
                f"אוגר בן 2 ביטים דוגם בחזית עולה. איפוס סינכרוני פעיל בערך {active}, מאפס ל־00 וקודם ל־EN. לפני החזית Q={initial:02b}, D={data:02b}, EN={en}, rst={rst}. מה Q לאחר החזית?",
                f"A 2-bit register samples on a rising edge. Synchronous reset is active at {active}, clears to 00, and has priority over EN. Before the edge Q={initial:02b}, D={data:02b}, EN={en}, rst={rst}. What is Q after the edge?",
                result,
                2,
                "קודם בודקים איפוס פעיל; אחרת EN קובע אם לטעון את D או לשמור את Q.",
                "Check active reset first; otherwise EN selects loading D or retaining Q.",
                "reset_register",
                p,
            )

    for v, (initial, reset, edge) in enumerate(
        [(1, True, False), (3, True, False), (2, True, True), (3, False, False), (1, False, True)], 1
    ):
        p = {"initial": initial, "reset": reset, "edge": edge}
        result = simulate("sync_async", p)
        good = f"{result[0]:02b}, {result[1]:02b}"
        alternatives = [
            f"{a:02b}, {b:02b}"
            for a, b in [(0, 0), (initial, initial), (0, initial), (initial, 0), (1, 2)]
            if f"{a:02b}, {b:02b}" != good
        ]
        emit(
            20,
            v,
            f"שני אוגרים בני 2 ביטים מתחילים בערך {initial:02b}. לאחד איפוס סינכרוני ולשני איפוס אסינכרוני; שניהם פעילים ב־1 ומאפסים ל־00. EN=0. כעת rst={int(reset)} ונשאר יציב. {'עוברת חזית עולה אחת' if edge else 'לא עוברת חזית שעון'}. לאחר התייצבות, מהם הערכים בסדר: סינכרוני, אסינכרוני?",
            f"Two 2-bit registers start at {initial:02b}. One reset is synchronous and the other asynchronous; both are active high and clear to 00. EN=0. Now rst={int(reset)} and remains stable. {'One rising edge occurs' if edge else 'No clock edge occurs'}. After settling, what are their values in the order: synchronous, asynchronous?",
            good,
            alternatives[:3],
            "איפוס אסינכרוני אינו ממתין לשעון; איפוס סינכרוני משנה את האוגר רק בחזית הפעילה.",
            "Asynchronous reset does not wait for a clock; synchronous reset changes the register only at an active edge.",
            "sync_async",
            p,
        )

    stream_cases = [
        (0, [1, 1, 0, 1]),
        (1, [1, 0, 1, 1]),
        (0, [0, 1, 1, 1]),
        (1, [0, 0, 1, 0]),
        (0, [1, 0, 0, 1, 1]),
    ]
    for n, kind in [
        (24, "rise"),
        (25, "stream_parity"),
        (26, "run11"),
        (27, "sticky"),
        (55, "vending"),
        (59, "pairs11"),
    ]:
        for v, (initial, xs) in enumerate(stream_cases, 1):
            if n in (26, 27, 55):
                initial = 0
            p = {"initial": initial, "inputs": xs}
            result = simulate(kind, p)
            if n == 24:
                he = f"ביט previous מתחיל ב־{initial}. בכל דגימה מחשבים y=x AND NOT previous ואז מעדכנים previous=x. עבור הקלטים {text(xs)}, מהם ערכי y לפי הסדר?"
                en = f"Bit previous starts at {initial}. At each sample, compute y=x AND NOT previous, then update previous=x. For inputs {text(xs)}, what are the y values in order?"
            elif n == 25:
                he = f"ביט הזוגיות מתחיל ב־{initial} ומתהפך בכל קלט 1; קלט 0 משאיר אותו. עבור הרצף {text(xs)}, מהם ערכי הביט לאחר כל קלט?"
                en = f"A parity bit starts at {initial} and toggles on every input 1; input 0 holds it. For stream {text(xs)}, what are the bit values after each input?"
            elif n == 26:
                he = f"מתחילים ללא אחדות קודמות. לאחר כל קלט y=1 אם שתי הדגימות האחרונות הן 11; אחרת y=0. קלט נוסף של 1 ממשיך לתת 1. עבור {text(xs)}, מהם ערכי y לאחר הדגימות?"
                en = f"Start with no preceding ones. After each input, y=1 if the last two samples are 11; otherwise y=0. An additional 1 keeps y at 1. For {text(xs)}, what are y values after the samples?"
            elif n == 27:
                he = f"ביט אירוע מתחיל ב־0. בחזית עם p=1 הוא נקבע ל־1 ונשאר כך עד איפוס. אין איפוס במהלך הרצף {text(xs)}. מהם ערכיו אחרי כל חזית?"
                en = f"An event bit starts at 0. An edge with p=1 sets it to 1, where it stays until reset. No reset occurs during {text(xs)}. What are its values after each edge?"
            elif n == 55:
                he = f"מכונה מתחילה ללא מטבע שמור. בכל דגימה c=1 מוסיף מטבע ו־c=0 אינו מוסיף. כל מטבע שני מפיק y=1 ומחזיר למצב ללא מטבע; אחרת y=0. עבור {text(xs)}, מהם הפלטים?"
                en = f"A machine starts with no stored coin. At each sample, c=1 adds one coin and c=0 adds none. Every second coin produces y=1 and returns to no stored coin; otherwise y=0. For {text(xs)}, what are the outputs?"
            else:
                he = f"מזהה זוגות 11 חופפים מתחיל כאשר הביט הקודם הוא {initial}. בכל דגימה הפלט 1 אם גם הביט הקודם וגם x הם 1, ואז זוכרים את x. עבור {text(xs)}, מהם הפלטים?"
                en = f"An overlapping 11-pair detector starts with previous bit {initial}. At each sample, output 1 if both the previous bit and x are 1, then remember x. For {text(xs)}, what are the outputs?"
            seq(
                n,
                v,
                he,
                en,
                result,
                "מעדכנים את המצב פעם אחת לכל קלט, לפי כלל המעבר שהוגדר בשאלה.",
                "Update state once per input according to the transition rule stated in the question.",
                kind,
                p,
            )

    styles = [
        (
            "y=(state==READY) AND x",
            "Mealy",
            "המוצא תלוי גם ב־x הנוכחי.",
            "The output also depends on current x.",
        ),
        ("y=(state==BUSY)", "Moore", "המוצא נקבע מהמצב בלבד.", "The output is determined by state alone."),
        (
            "y=(state==IDLE) OR x",
            "Mealy",
            "במצב שאינו IDLE, שינוי x משנה את y.",
            "Outside IDLE, changing x changes y.",
        ),
        (
            "y=(state==DONE)",
            "Moore",
            "אין בקביעת המוצא תלות בקלט הנוכחי.",
            "The output definition has no dependence on current input.",
        ),
        (
            "y=(state==S1) XOR x",
            "Mealy",
            "בכל מצב קבוע, שינוי x הופך את המוצא.",
            "For any fixed state, changing x inverts the output.",
        ),
    ]
    for v, (formula, answer, ehe, een) in enumerate(styles, 1):
        emit(
            28,
            v,
            f"המשתנה state יכול להיות READY, BUSY, IDLE, DONE או S1. הקלט x הוא ביט חופשי. המוצא מוגדר כך: {formula}. מהו סיווג התלות של המוצא?",
            f"Variable state may be READY, BUSY, IDLE, DONE or S1. Input x is an unconstrained bit. The output is defined by {formula}. How is its output dependence classified?",
            answer,
            [
                "Moore" if answer == "Mealy" else "Mealy",
                ("המוצא קבוע תמיד", "The output is always constant"),
                ("המוצא תלוי רק בשעון", "The output depends only on the clock"),
            ],
            ehe,
            een,
            "output_dependency",
            {"formula": formula, "classification": answer},
        )

    for v, states in enumerate([3, 5, 7, 9, 12], 1):
        p = {"states": states}
        width, unused = simulate("statebits", p)
        good = f"{width}, {unused}"
        emit(
            29,
            v,
            f"למכונה {states} מצבים. משתמשים בקידוד בינארי קומפקטי במספר הביטים המזערי. כמה ביטים נחוצים וכמה קודים נותרים פנויים, בסדר זה?",
            f"A machine has {states} states. Use compact binary encoding with the minimum number of bits. How many bits are required and how many codes remain unused, in that order?",
            good,
            [f"{width + 1}, {2 ** (width + 1) - states}", f"{width}, {unused + 1}", f"{width + 1}, {unused}"],
            f"{width} ביטים מספקים {2**width} קודים; לאחר הקצאת {states} נותרו {unused}.",
            f"{width} bits provide {2**width} codes; assigning {states} leaves {unused}.",
            "statebits",
            p,
        )

    for v, (initial, edges) in enumerate([(0, 4), (1, 5), (2, 7), (0, 8), (1, 9)], 1):
        p = {"initial": initial, "edges": edges, "states": 3}
        result = simulate("cycle", p)
        emit(
            30,
            v,
            f"מכונה מתקדמת בחזיתות עולות במחזור S0→S1→S2→S0, ללא איפוס. מתחילים ב־S{initial}. באיזה מצב היא אחרי {edges} חזיתות?",
            f"A machine advances on rising edges in the cycle S0→S1→S2→S0, with no reset. Start in S{initial}. Which state follows {edges} edges?",
            f"S{result}",
            [f"S{x}" for x in range(3) if x != result] + [("אין מצב מוגדר", "The state is undefined")],
            "כל שלוש חזיתות מחזירות לאותו מצב; מתקדמים לפי השארית בחלוקה ב־3.",
            "Every three edges return to the same state; use the edge count modulo 3.",
            "cycle",
            p,
        )

    mux_sets = {
        34: [("A", "1", "0"), ("NOT A", "0", "1"), ("B", "1", "0"), ("NOT B", "0", "1"), ("C", "1", "0")],
        35: [("A", "0", "B"), ("B", "0", "A"), ("NOT A", "B", "0"), ("NOT B", "A", "0"), ("C", "0", "D")],
        36: [("A", "B", "1"), ("B", "A", "1"), ("NOT A", "1", "B"), ("NOT B", "1", "A"), ("C", "D", "1")],
    }
    for n, cases in mux_sets.items():
        for v, (selector, d0, d1) in enumerate(cases, 1):
            target = (
                ("NOT " + selector.replace("NOT ", ""))
                if n == 34
                else (
                    "C AND D"
                    if n == 35 and v == 5
                    else "C OR D"
                    if n == 36 and v == 5
                    else "A AND B"
                    if n == 35
                    else "A OR B"
                )
            )
            good = f"D0={d0}, D1={d1}"
            distractors = [f"D0={d1}, D1={d0}", "D0=0, D1=0", "D0=1, D1=1"]
            emit(
                n,
                v,
                f"בורר MUX בוחר D0 כאשר S=0 ואת D1 כאשר S=1. מחברים S={selector}. אילו חיבורים מממשים Y={target} לכל הקלטים?",
                f"A MUX selects D0 when S=0 and D1 when S=1. Connect S={selector}. Which connections implement Y={target} for every input?",
                good,
                distractors,
                "מציבים S=0 ו־S=1 בנפרד ומוודאים שכל ענף נותן את הפונקציה הרצויה.",
                "Substitute S=0 and S=1 separately and check that each branch yields the required function.",
                "mux_function",
                {"selector": selector, "d0": d0, "d1": d1, "target": target},
            )

    for v, count in enumerate([2, 3, 4, 5, 8], 1):
        outputs = [(0 ^ (count % 2)), (1 ^ (count % 2))]
        good = text(outputs)
        emit(
            37,
            v,
            f"ביט A עובר דרך {count} שערי NOT בטור. לאחר התייצבות, מהם המוצאים עבור A=0 ועבור A=1, בסדר זה?",
            f"Bit A passes through {count} NOT gates in series. After settling, what are the outputs for A=0 and A=1, in that order?",
            good,
            [text(x) for x in [[0, 0], [0, 1], [1, 0], [1, 1]] if text(x) != good],
            "כל זוג היפוכים מתבטל; מספר אי־זוגי של שערים משאיר היפוך אחד.",
            "Each pair of inversions cancels; an odd number of gates leaves one inversion.",
            "inversion_chain",
            {"count": count},
        )

    for v, words in enumerate(
        [
            ["101101", "001010", "111111", "100000"],
            ["000001", "101000", "001100", "110011"],
            ["100101", "111000", "010101", "000000"],
            ["101010", "001111", "110000", "100111"],
            ["011001", "110110", "000010", "001101"],
        ],
        1,
    ):
        values = [int(w[-1]) for w in words]
        seq(
            39,
            v,
            f"מפיקים ביט y=1 עבור מספר לא מסומן אי־זוגי ו־y=0 עבור מספר זוגי. מהם ערכי y עבור {', '.join(words)} לפי הסדר?",
            f"Produce y=1 for an odd unsigned integer and y=0 for an even integer. What are the y values for {', '.join(words)} in order?",
            values,
            "רק הביט הימני קובע זוגיות: 1 מציין מספר אי־זוגי.",
            "Only the rightmost bit determines parity: 1 denotes an odd integer.",
            "integer_parity",
            {"words": words},
        )

    for v, (value, width) in enumerate([(19, 5), (42, 6), (57, 6), (70, 7), (11, 5)], 1):
        p = {"value": value, "width": width}
        result = simulate("to_binary", p)
        binary(
            41,
            v,
            f"מהו הייצוג של המספר הלא מסומן {value} בדיוק ב־{width} ביטים?",
            f"What is the representation of unsigned {value} using exactly {width} bits?",
            value,
            width,
            "מפרקים את המספר לסכום חזקות של 2 ומשלימים אפסים מובילים לפי הרוחב.",
            "Decompose the number into powers of two and add leading zeros to the required width.",
            "to_binary",
            p,
        )

    for v, word in enumerate(["1101", "1011", "11100", "10010", "0110"], 1):
        p = {"word": word}
        unsigned, signed = simulate("signed_pair", p)
        good = f"{unsigned}, {signed}"
        emit(
            42,
            v,
            f"מהם ערכי המילה {word} בפירוש לא מסומן ובפירוש משלים ל־2 ברוחב {len(word)} ביטים, בסדר זה?",
            f"What are the values of word {word} under unsigned and {len(word)}-bit two's-complement interpretations, in that order?",
            good,
            [f"{signed}, {unsigned}", f"{unsigned}, {signed + 1}", f"{unsigned + 1}, {signed}"]
            if unsigned != signed
            else [f"{unsigned}, {-signed}", f"{unsigned + 1}, {signed}", f"{unsigned}, {signed + 1}"],
            "בפירוש משלים ל־2, לביט השמאלי משקל שלילי; אם הוא 1 מחסרים 2 בחזקת רוחב המילה.",
            "In two's complement the leftmost bit has negative weight; if it is 1, subtract 2 raised to the word width.",
            "signed_pair",
            p,
        )

    for v, (word, width) in enumerate([("1010", 6), ("1101", 7), ("1001", 5), ("11100", 8), ("10101", 7)], 1):
        p = {"word": word, "width": width}
        result = simulate("signextend", p)
        binary(
            43,
            v,
            f"מרחיבים את המילה {word} בפירוש משלים ל־2 ל־{width} ביטים, בלי לשנות את ערכה. מהי המילה החדשה?",
            f"Sign-extend two's-complement word {word} to {width} bits without changing its value. What is the new word?",
            int(result, 2),
            width,
            "משכפלים את ביט הסימן משמאל; הרחבה באפסים אינה שומרת על ערך שלילי.",
            "Repeat the sign bit on the left; zero extension does not preserve a negative value.",
            "signextend",
            p,
        )

    for v, word in enumerate(["0001", "00010", "000100", "0001000", "00010000"], 1):
        width = len(word)
        value = int(word, 2)
        bad = ["0" * width, format(value | (1 if value != 1 else 2), f"0{width}b"), "1" * width]
        words = [word] + bad
        emit(
            44,
            v,
            f"איזו מהמילים הבאות באורך {width} ביטים היא one-hot, כלומר מכילה בדיוק ביט אחד שערכו 1?",
            f"Which of the following {width}-bit words is one-hot, meaning it contains exactly one bit equal to 1?",
            word,
            bad,
            "במילה הנכונה יש בדיוק 1 אחד; מילה שכולה אפסים אינה one-hot.",
            "The correct word has exactly one 1; an all-zero word is not one-hot.",
            "onehot",
            {"words": words},
        )

    for v, (a, b, cin) in enumerate([(1, 1, 0), (0, 1, 1), (1, 0, 0), (0, 0, 0), (1, 1, 1)], 1):
        p = {"a": a, "b": b, "cin": cin}
        result = simulate("fulladder", p)
        emit(
            45,
            v,
            f"מחברים ביטים A={a}, B={b}, Cin={cin}. מהי התוצאה בסדר Cout,S, כאשר S הוא הביט הנמוך?",
            f"Add bits A={a}, B={b}, Cin={cin}. What is the result in the order Cout,S, where S is the low bit?",
            result,
            [f"{i:02b}" for i in range(4) if f"{i:02b}" != result],
            f"הסכום הוא {a + b + cin}; כותבים אותו בשני ביטים, כשהנשא משמאל.",
            f"The sum is {a + b + cin}; write it in two bits, with carry on the left.",
            "fulladder",
            p,
        )

    for v, word in enumerate(["10000000", "11100100", "10101010", "01101010", "11000011"], 1):
        p = {"word": word}
        logical, arithmetic = simulate("rightshift", p)
        good = f"{logical}, {arithmetic}"
        alternatives = [
            f"{arithmetic}, {logical}",
            f"{logical}, {logical}",
            f"{arithmetic}, {arithmetic}",
            f"{word}, {word}",
            f"{word[1:] + '0'}, {word[1:] + '0'}",
            f"{word}, {logical}",
            f"{logical}, {word}",
        ]
        bad = list(dict.fromkeys(x for x in alternatives if x != good))[:3]
        emit(
            46,
            v,
            f"מזיזים את המילה {word} ביט אחד ימינה ושומרים 8 ביטים. מהן התוצאות בסדר: הזזה לוגית המכניסה 0, הזזה אריתמטית המשכפלת את ביט הסימן?",
            f"Shift word {word} right by one bit, keeping 8 bits. What are the results in the order: logical shift inserting 0, arithmetic shift repeating the sign bit?",
            good,
            bad,
            "בהזזה ימינה הביט הימני אובד. משמאל נכנס 0 בהזזה לוגית וביט הסימן בהזזה אריתמטית.",
            "A right shift discards the low bit. The new high bit is 0 for a logical shift and the sign bit for an arithmetic shift.",
            "rightshift",
            p,
        )

    for v, (initial, data, enable) in enumerate([(0, 1, 0), (1, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1)], 1):
        p = {"initial": initial, "data": data, "enable": enable}
        result = data if enable else initial
        good = f"D0=Q, D1=data; Q={result}"
        wrong = [
            f"D0=data, D1=Q; Q={data if not enable else initial}",
            f"D0=0, D1=data; Q={data if enable else 0}",
            f"D0=Q, D1=0; Q={0 if enable else initial}",
        ]
        emit(
            47,
            v,
            f"בורר לפני דלגלג D בוחר D0 כש־S=0 ואת D1 כש־S=1. S=EN. האוגר חייב לשמור Q כש־EN=0 ולטעון data כש־EN=1. לפני חזית עולה Q={initial}, data={data}, EN={enable}, ללא איפוס. איזה זוג חיבורים מממש זאת לכל הקלטים, ומה Q אחרי החזית?",
            f"A MUX before a D flip-flop selects D0 when S=0 and D1 when S=1. S=EN. The register must hold Q when EN=0 and load data when EN=1. Before a rising edge Q={initial}, data={data}, EN={enable}, with no reset. Which wiring works for all inputs, and what is Q after the edge?",
            good,
            wrong,
            "משוב Q אל D0 שומר את הערך; data אל D1 מאפשר טעינה.",
            "Feedback from Q to D0 retains the value; connecting data to D1 enables loading.",
            "enable_mux",
            p,
        )

    for v, (initial, xs) in enumerate(
        [(3, [1, 0, 1, 1]), (6, [1, 1, 0, 1]), (0, [0, 1, 0, 1]), (7, [1, 1, 1, 0]), (4, [0, 0, 1, 1])], 1
    ):
        p = {"initial": initial, "inputs": xs, "width": 3}
        result = simulate("enabled_counter", p)
        seq(
            48,
            v,
            f"מונה לא מסומן בן 3 ביטים מתחיל ב־{initial:03b}. בכל חזית עולה הוא גדל ב־1 רק אם EN=1, אחרת שומר את ערכו. שומרים רק 3 ביטים ואין איפוס. עבור EN={text(xs)}, מה נשמר אחרי כל חזית?",
            f"A 3-bit unsigned counter starts at {initial:03b}. At each rising edge it increments only if EN=1; otherwise it holds. Keep only 3 bits, with no reset. For EN={text(xs)}, what is stored after each edge?",
            result,
            "סופרים רק חזיתות שבהן EN=1; הערכים נעטפים בחזרה ל־0 אחרי 7.",
            "Count only edges with EN=1; values wrap to 0 after 7.",
            "enabled_counter",
            p,
            width=3,
        )

    for v, (width, initial, edges) in enumerate([(3, 0, 1), (4, 0, 2), (3, 1, 3), (5, 0, 1), (4, 2, 4)], 1):
        p = {"initial": initial, "width": width, "edges": edges}
        result = simulate("down", p)
        binary(
            49,
            v,
            f"מונה לא מסומן בן {width} ביטים מתחיל ב־{initial}. הוא קטן ב־1 בכל חזית עולה, שומר רק {width} ביטים וללא איפוס. מה נשמר אחרי {edges} חזיתות?",
            f"A {width}-bit unsigned counter starts at {initial}. It decrements by 1 on each rising edge, keeps only {width} bits, and has no reset. What is stored after {edges} edges?",
            result,
            width,
            f"החיסור מתבצע מודולו {2**width}; צעד אחורה מ־0 נותן {2**width - 1}.",
            f"Subtraction is modulo {2**width}; one step backward from 0 gives {2**width - 1}.",
            "down",
            p,
        )

    init_cases = [(1, 1), (0, 1), (1, 2), (0, 2), (1, 3)]
    for v, (data, edges) in enumerate(init_cases, 1):
        good = (f"לא ידוע; {data}", f"Unspecified; {data}")
        emit(
            51,
            v,
            f"לדלגלג D אין איפוס ואין ערך התחלתי מוגדר. D={data} יציב כנדרש סביב כל אחת מ־{edges} החזיתות העולות הראשונות. מה מובטח לגבי Q לפני החזית הראשונה ולאחר החזית האחרונה, בסדר זה?",
            f"A D flip-flop has no reset or specified initial value. D={data} is stable as required around each of the first {edges} rising edges. What is guaranteed about Q before the first edge and after the final edge, in that order?",
            good,
            [
                (f"0; {data}", f"0; {data}"),
                (f"1; {data}", f"1; {data}"),
                ("לא ידוע; לא ידוע", "Unspecified; unspecified"),
            ],
            "לפני הדגימה אין ערך התחלתי מובטח; אחרי חזית תקינה Q שווה ל־D, לאחר השהיית הרכיב.",
            "No initial value is guaranteed before sampling; after a valid edge Q equals D following propagation delay.",
            "uninitialized_d",
            {"data": data, "edges": edges},
        )

    for v, (initial, bit, edges) in enumerate([(0, 0, 4), (0, 1, 4), (2, 0, 5), (1, 1, 5), (3, 2, 5)], 1):
        p = {"initial": initial, "bit": bit, "edges": edges}
        result = simulate("counter_bit", p)
        seq(
            52,
            v,
            f"מונה בינארי לא מסומן בן 3 ביטים מתחיל ב־{initial:03b} וגדל ב־1 בכל חזית עולה, עם גלישה וללא איפוס. ביט 0 הוא הימני. מהם ערכי ביט {bit} אחרי {edges} החזיתות הראשונות?",
            f"A 3-bit unsigned binary counter starts at {initial:03b} and increments on each rising edge, wrapping with no reset. Bit 0 is the rightmost bit. What are the values of bit {bit} after the first {edges} edges?",
            result,
            f"ביט {bit} מחליף ערך כל {2**bit} צעדים; עוקבים אחר קוד המונה בכל חזית.",
            f"Bit {bit} toggles every {2**bit} increments; trace the counter code at each edge.",
            "counter_bit",
            p,
        )

    for v, (initial, xs) in enumerate(
        [
            ([0, 0, 0], [1, 0, 0, 0]),
            ([0, 0, 0], [0, 1, 0, 0]),
            ([1, 0, 0], [0, 0, 0, 0]),
            ([0, 1, 0], [0, 0, 0, 0]),
            ([0, 0, 0], [1, 1, 0, 0]),
        ],
        1,
    ):
        p = {"initial": initial, "inputs": xs}
        result = simulate("pipe", p)
        seq(
            53,
            v,
            f"שלושה דלגלגי D דוגמים באותה חזית עולה: D1=x, D2=Q1, D3=Q2. מתחילים ב־Q1Q2Q3={''.join(map(str, initial))}, ללא איפוס נוסף. x יציב בחזיתות וערכיו {text(xs)}. מהן מילות המצב לאחר כל חזית?",
            f"Three D flip-flops sample on the same rising edge: D1=x, D2=Q1, D3=Q2. Start at Q1Q2Q3={''.join(map(str, initial))}, with no further reset. Stable x values at the edges are {text(xs)}. What are the state words after each edge?",
            result,
            "כל שלב דוגם את הערך הקודם של קודמו; ביט מתקדם שלב אחד בכל חזית.",
            "Each stage samples its predecessor's old value; a bit advances one stage per edge.",
            "pipe",
            p,
            width=3,
        )

    for v, (initial, inputs) in enumerate(
        [
            (0, [[1, 0], [1, 0], [0, 1]]),
            (0, [[0, 1], [1, 1], [0, 0]]),
            (1, [[1, 0], [1, 1], [0, 0]]),
            (0, [[1, 0], [1, 1], [1, 0]]),
            (1, [[0, 0], [0, 1], [1, 0]]),
        ],
        1,
    ):
        p = {"initial": initial, "inputs": inputs}
        result = simulate("busy", p)
        rs = "; ".join(f"({r},{d})" for r, d in inputs)
        seq(
            54,
            v,
            f"מצב READY מסומן 0 ומצב BUSY מסומן 1. מתחילים במצב {initial}. בכל חזית, READY עובר ל־BUSY אם r=1; BUSY מתעלם מ־r וחוזר ל־READY אם d=1. אחרת נשארים במקום. עבור הזוגות (r,d): {rs}, מהם קודי המצב אחרי כל חזית?",
            f"READY is encoded 0 and BUSY is encoded 1. Start in state {initial}. At each edge, READY enters BUSY if r=1; BUSY ignores r and returns to READY if d=1. Otherwise hold state. For pairs (r,d): {rs}, what are the state codes after each edge?",
            result,
            "המעבר נבחר לפי המצב לפני החזית; לא מבצעים שני מעברים באותה חזית.",
            "Choose the transition using the pre-edge state; do not perform two transitions at the same edge.",
            "busy",
            p,
        )

    graphs = [
        {"I": ["I", "R"], "R": ["I", "R"], "E": ["E", "E"]},
        {"I": ["R", "I"], "R": ["R", "I"], "E": ["E", "I"]},
        {"I": ["I", "R"], "R": ["E", "R"], "E": ["E", "E"]},
        {"I": ["R", "R"], "R": ["R", "R"], "E": ["I", "I"]},
        {"I": ["R", "I"], "R": ["R", "E"], "E": ["I", "E"]},
    ]
    for v, g in enumerate(graphs, 1):
        reached = {"I"}
        for _ in range(3):
            reached |= {dst for state in list(reached) for dst in g[state]}
        good = ", ".join(sorted(reached))
        options = ["I", "I, R", "E, I, R", "E, I"]
        rs = "; ".join(f"{s}: 0→{ds[0]}, 1→{ds[1]}" for s, ds in g.items())
        emit(
            56,
            v,
            f"מכונה מתחילה ב־I. המעברים עבור ביט הקלט הם: {rs}. אילו מצבים ניתנים להשגה באמצעות רצף קלט סופי, כולל הרצף הריק?",
            f"A machine starts in I. Transitions for the input bit are: {rs}. Which states are reachable by a finite input sequence, including the empty sequence?",
            good,
            [x for x in options if x != good],
            "מתחילים במצב האתחול ומוסיפים שוב ושוב את כל יעדי המעברים ממצבים שכבר הושגו.",
            "Start with the initial state and repeatedly add all transition destinations from already reachable states.",
            "reachability",
            {"graph": g, "initial": "I"},
        )

    for v, states in enumerate([3, 4, 5, 6, 9], 1):
        numeric(
            57,
            v,
            f"בקידוד one-hot מקצים ביט נפרד לכל מצב, ורק ביט המצב הנוכחי הוא 1. כמה דלגלגים דרושים למכונה עם {states} מצבים?",
            f"One-hot encoding assigns one separate bit to each state, with only the current state bit equal to 1. How many flip-flops are needed for {states} states?",
            states,
            "ב־one-hot יש דלגלג אחד לכל מצב, בניגוד לקידוד בינארי קומפקטי.",
            "One-hot uses one flip-flop per state, unlike compact binary encoding.",
            "onehot_width",
            {"states": states},
            [math.ceil(math.log2(states)), states - 1, states + 1, states + 2],
        )

    rows_all = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for v in range(1, 6):
        rows = rows_all[v % 4 :] + rows_all[: v % 4]
        if v == 5:
            rows = [rows[i] for i in [0, 2, 3, 1]]
        p = {"rows": rows}
        result = simulate("priority", p)
        good = ", ".join(result)
        wrong = []
        for i in range(3):
            candidate = result[:]
            candidate[i] = {"A": "B", "B": "S", "S": "A"}[candidate[i]]
            wrong.append(", ".join(candidate))
        rs = "; ".join(f"({a},{b})" for a, b in rows)
        emit(
            58,
            v,
            f"במצב S ניתנת עדיפות ל־a: אם a=1 עוברים ל־A; אחרת, אם b=1 עוברים ל־B; אחרת נשארים ב־S. מהם יעדי המעבר עבור (a,b): {rs}, כשכל זוג נבדק בנפרד מתוך S?",
            f"In state S, a has priority: if a=1 go to A; otherwise if b=1 go to B; otherwise stay in S. What are the destinations for (a,b): {rs}, with each pair tested independently from S?",
            good,
            wrong,
            "ב־a=b=1 נבחר A; התנאי ל־B הוא a=0 וגם b=1.",
            "When a=b=1, choose A; B requires a=0 and b=1.",
            "priority",
            p,
        )

    for v, (recovery, edges) in enumerate([(0, 1), (0, 2), (1, 1), (2, 2), (1, 3)], 1):
        p = {"initial": 3, "recovery": recovery, "edges": edges}
        result = simulate("recovery", p)
        binary(
            60,
            v,
            f"מונה בן 2 ביטים מתקדם במחזור 00→01→10→00. עבור המצב הלא חוקי 11 הוגדר מעבר התאוששות אל {recovery:02b}. מתחילים ב־11 ואין איפוס. מהו המצב לאחר {edges} חזיתות עולות?",
            f"A 2-bit counter follows 00→01→10→00. Invalid state 11 has a recovery transition to {recovery:02b}. Start in 11 with no reset. What is the state after {edges} rising edges?",
            result,
            2,
            "החזית הראשונה מבצעת את מעבר ההתאוששות; לאחריה מתקדמים במחזור החוקי.",
            "The first edge performs recovery; subsequent edges advance through the valid cycle.",
            "recovery",
            p,
        )
    validate()
    return QUESTIONS, CHECKS


def validate():
    expected_sources = set(CARDS) - EXISTING
    assert len(QUESTIONS) == 5 * len(expected_sources) == 265
    assert {q["source_key"] for q in QUESTIONS} == {f"quick-hw-{n:02d}" for n in expected_sources}
    assert len({q["key"] for q in QUESTIONS}) == 265
    assert all(q["choices"][q["correct"]] == c["expected"] for q, c in zip(QUESTIONS, CHECKS, strict=True))
    for n in expected_sources:
        qs = [q for q in QUESTIONS if q["source_key"] == f"quick-hw-{n:02d}"]
        assert sorted(q["variant"] for q in qs) == [1, 2, 3, 4, 5]
        assert all(len({q["prompt"][lang] for q in qs}) == 5 for lang in ("he", "en")), n
    for q, c in zip(QUESTIONS, CHECKS, strict=True):
        method, p = c["method"], c["inputs"]
        if method == "mux_function":

            def evaluate(expr, env):
                if expr in ("0", "1"):
                    return int(expr)
                if expr.startswith("NOT "):
                    return 1 - env[expr[4:]]
                if " AND " in expr:
                    a, b = expr.split(" AND ")
                    return env[a] & env[b]
                if " OR " in expr:
                    a, b = expr.split(" OR ")
                    return env[a] | env[b]
                return env[expr]

            for bits in itertools.product((0, 1), repeat=4):
                env = dict(zip("ABCD", bits, strict=True))
                actual = evaluate(p["d1"] if evaluate(p["selector"], env) else p["d0"], env)
                assert actual == evaluate(p["target"], env), (q["key"], env)
        if method == "output_dependency":
            expr = p["formula"]
            mealy = "x" in expr
            assert c["expected"]["en"] == ("Mealy" if mealy else "Moore")
        if method == "gate_identity":
            assert c["expected"]["en"] == p["expression"]
            gate_funcs = {
                "AND": lambda a, b, c: a & b,
                "OR": lambda a, b, c: a | b,
                "NAND": lambda a, b, c: 1 - (a & b),
                "NOR": lambda a, b, c: 1 - (a | b),
                "XOR": lambda a, b, c: a ^ b,
                "XNOR": lambda a, b, c: 1 - (a ^ b),
                "(A AND B) OR (A AND C) OR (B AND C)": lambda a, b, c: (a & b) | (a & c) | (b & c),
                "A AND (B OR C)": lambda a, b, c: a & (b | c),
                "A XOR B XOR C": lambda a, b, c: a ^ b ^ c,
                "A AND B AND C": lambda a, b, c: a & b & c,
                "A OR B OR C": lambda a, b, c: a | b | c,
            }
            matching = []
            for i, option in enumerate(q["choices"]):
                func = gate_funcs[option["en"]]
                rows = [list(x) for x in itertools.product((0, 1), repeat=p["arity"])]
                truth = simulate("truth", {"operation": p["operation"], "rows": rows})
                if all(
                    func(*(row + [0] if len(row) == 2 else row)) == value
                    for row, value in zip(rows, truth, strict=True)
                ):
                    matching.append(i)
            assert matching == [q["correct"]], q["key"]
        if method == "truth_count":
            assert c["expected"]["en"] == str(sum(simulate("truth", p)))
        if method == "reachability":
            frontier = [p["initial"]]
            visited = set()
            while frontier:
                s = frontier.pop()
                if s not in visited:
                    visited.add(s)
                    frontier.extend(p["graph"][s])
            assert c["expected"]["en"] == ", ".join(sorted(visited))
        if method == "integer_parity":
            assert c["expected"]["en"] == text([int(w, 2) % 2 for w in p["words"]])
        if method == "inversion_chain":
            assert c["expected"]["en"] == text([((~x) & 1) if p["count"] % 2 else x for x in (0, 1)])
        if method == "reset_register":
            assert c["expected"]["en"] == format(simulate(method, p), "02b")
        if method == "sync_async":
            assert c["expected"]["en"] == ", ".join(format(x, "02b") for x in simulate(method, p))
        if method in {"statebits", "signed_pair"}:
            assert c["expected"]["en"] == text(simulate(method, p))
        if method == "rightshift":
            assert c["expected"]["en"] == text(simulate(method, p))
        if method in {"onehot", "fulladder", "onehot_width"}:
            assert c["expected"]["en"] == str(simulate(method, p))
        if method == "enabled_counter":
            assert c["expected"]["en"] == ", ".join(format(x, "03b") for x in simulate(method, p))
        if method == "recovery":
            assert c["expected"]["en"] == format(simulate(method, p), "02b")
        if method == "enable_mux":
            actual = p["data"] if p["enable"] else p["initial"]
            assert c["expected"]["en"] == f"D0=Q, D1=data; Q={actual}"
        if method == "uninitialized_d":
            assert c["expected"]["en"] == f"Unspecified; {p['data']}"
        if method == "absorption_concept":
            assert all(int(a or (a and b)) == a for a, b in itertools.product((0, 1), repeat=2))
        # Replay numeric/trace models from the stored parameters, not from option positions.
        if method in {
            "truth",
            "absorb",
            "parity",
            "pipe",
            "toggle",
            "rise",
            "stream_parity",
            "run11",
            "sticky",
            "vending",
            "pairs11",
            "counter_bit",
            "busy",
            "priority",
        }:
            val = simulate(method, p)
            width = len(p["initial"]) if method == "pipe" else 3 if method == "enabled_counter" else None
            encoded = ", ".join(format(x, f"0{width}b") if width else str(x) for x in val)
            assert c["expected"]["en"] == encoded, q["key"]
        if method in {"mask", "shift_left", "setclear", "down", "to_binary", "signextend"}:
            val = simulate(method, p)
            width = 8 if method in {"mask", "shift_left", "setclear"} else p["width"]
            encoded = val if isinstance(val, str) else format(val, f"0{width}b")
            assert c["expected"]["en"] == encoded, q["key"]


if __name__ == "__main__":
    build()
    target = ROOT / "backend/seeds/duel_quiz_batches"
    target.mkdir(parents=True, exist_ok=True)
    (target / "hardware_basic.json").write_text(
        json.dumps(QUESTIONS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (target / "hardware_basic.checks.json").write_text(
        json.dumps(CHECKS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Authored and checked {len(QUESTIONS)} bilingual draft variants across {len(QUESTIONS) // 5} sources."
    )
