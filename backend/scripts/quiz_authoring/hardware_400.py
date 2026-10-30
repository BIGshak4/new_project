"""Author 75 interview-linked short cards and 375 draft quiz cases.

Every case is replayed against an independent physical, arithmetic or trace
oracle. These are teaching models, not physical timing or human review.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content"
OUT = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = []
QUESTIONS = []
CHECKS = []
SPECS = []


def loc(he, en):
    return {"he": he, "en": en}


def fmt(value):
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (tuple, list)):
        return ", ".join(fmt(v) for v in value)
    return str(value)


def model(method, p):
    """Compact author calculation; verify() uses other constructions below."""
    match method:
        case "rc_ambiguity":
            return p["tau"] / p["r"]
        case "rc_half":
            return p["r"] * p["c"] * math.log(2)
        case "cap_jump":
            return p["before"] + p["after_b"] - p["before_b"]
        case "cap_dc":
            return p["vdd"]
        case "overshoot":
            return p["before"] + p["jump"]
        case "cap_history":
            return p["vdd"] + (p["start"] - p["vdd"]) * p["decay"] + p["jump"]
        case "gate_charge":
            return p["c"] * p["dv"]
        case "doping":
            return "permanent" if p["operation"] == "implant" else "reversible"
        case "mos_on":
            return "off" if p["vg"] - p["vs"] <= p["vt"] else "on"
        case "mos_region":
            return (
                "off" if p["vgs"] <= p["vt"] else "saturation" if p["vds"] >= p["vgs"] - p["vt"] else "linear"
            )
        case "mos_square":
            return p["factor"] ** 2
        case "nmos_high":
            return p["vdd"] - p["vt"]
        case "static_current":
            return p["vdd"] / (p["pullup"] + p["pulldown"])
        case "lc_initial":
            return (p["v0"], 0)
        case "lc_quarter":
            return p["v0"] * math.sqrt(p["c"] / p["l"])
        case "lc_half":
            return -p["v0"]
        case "lc_period_ratio":
            return math.sqrt(p["l_ratio"] * p["c_ratio"])
        case "buffer_delay":
            return math.log(2) * (p["rs"] * p["cin"] + p["rb"] * p["cl"]) + p["tb"]
        case "buffer_breakeven":
            return (p["rs"] * p["cin"] + p["tb"] / math.log(2)) / (p["rs"] - p["rb"])
        case "led_resistor":
            return (p["vs"] - p["vf"] - p["vd"]) / p["current"]
        case "skew_effect":
            return (p["s"], -p["s"])
        case "uncertainty":
            return (-p["us"], -p["uh"])
        case "speedup":
            return (p["dmax_reduction"], -p["dmin_reduction"])
        case "timing_exception":
            return "valid" if p["functional_cycles"] >= p["constraint_cycles"] else "invalid"
        case "coupling_ceff":
            return p["cg"] + p["cc"] * (1 - p["ratio"])
        case "quiet_noise":
            return p["cc"] * p["da"] / (p["cg"] + p["cc"])
        case "window_overlap":
            return max(0, min(p["a1"], p["v1"]) - max(p["a0"], p["v0"]))
        case "shield_delta":
            return p["new_cg"] + 2 * p["new_cc"] - p["old_cg"] - 2 * p["old_cc"]
        case "nyquist_phase":
            return tuple(round(math.sin(math.pi * n + p.get("phase", 0) * math.pi)) for n in range(4))
        case "alias":
            return abs(((p["frequency"] + p["fs"] / 2) % p["fs"]) - p["fs"] / 2)
        case "band_interval":
            return (2 * p["fh"] / p["m"], 2 * p["fl"] / (p["m"] - 1))
        case "band_margin":
            return "safe" if 2 * p["fh"] / p["m"] < p["fs"] < 2 * p["fl"] / (p["m"] - 1) else "unsafe"
        case "parity_locations":
            return p["n"]
        case "hamming_bits":
            return next(r for r in range(1, 20) if 2**r >= 1 + p["data"] + r)
        case "syndrome":
            return p["position"]
        case "secded":
            return (
                "none"
                if not p["syndrome"] and not p["parity"]
                else "overall"
                if not p["syndrome"]
                else "single"
                if p["parity"]
                else "double"
            )
        case "short_syndrome":
            return "correct" if 1 <= p["syndrome"] <= 12 else "clean" if not p["syndrome"] else "reject"
        case "queue_overflow":
            return max(0, p["arrivals"] - p["capacity"])
        case "commit_ack":
            return "safe" if p["read_issue"] >= p["visible"] else "stale_possible"
        case "wait_evidence":
            return "safe" if p["wait"] >= p["actual_latency"] else "premature"
        case "immediate_completion":
            return "RESP" if p["accepted"] and p["done"] else "WAIT" if p["accepted"] else "ISSUE"
        case "round_robin":
            return ", ".join("R" if (p["first"] + i) % 2 == 0 else "W" for i in range(p["n"]))
        case "serialized_issue":
            return p["previous_response_consumed"] + 1
        case "size_low":
            return p["a"] % p["size"]
        case "size_carry":
            return (p["a"] + p["size"]) // 256
        case "size_valid":
            return (int(p["size"] in (1, 2, 4)), (p["a"] + p["size"]) % 256 if p["size"] in (1, 2, 4) else 0)
        case "odd_delta":
            return 2 * p["n"] + 1
        case "square_next":
            return p["n"] ** 2 + 2 * p["n"] + 1
        case "square_terminal":
            n = min(p["steps"], p["limit"])
            return (n, n * n)
        case "xor_swap":
            x, y = p["x"], p["y"]
            for i in range(p["edges"]):
                if i % 2 == 0:
                    x ^= y
                else:
                    y ^= x
            return (x, y)
        case "complement_load":
            return "Y" if p["load"] else "X"
        case "extended_counter":
            return (p["initial"] + p["edges"]) % 32
        case "compare_msb":
            return "greater" if p["a"] > p["b"] else "less" if p["a"] < p["b"] else "equal"
        case "pair_counts":
            return sum(((p["x"] >> i) & 1) << (i // 2 * 2) for i in range(8))
        case "popcount_width":
            return max(1, math.ceil(math.log2(p["inputs"] + 1)))
        case "times_six_low":
            return (6 * p["x"]) % 2
        case "ha_carry_pair":
            c1 = p["a"] & p["b"]
            c2 = (p["a"] ^ p["b"]) & p["cin"]
            return (c1, c2)
        case "times_thirteen":
            return (p["x"] << 3) + (p["x"] << 2) + p["x"]
        case "square_bit2":
            return 2 if p.get("inverse") else ((p["x"] * p["x"]) >> 2) & 1
        case "signed_square":
            value = p["bits"] - 4 if p["bits"] >= 2 else p["bits"]
            return p["bits"] ** 2 - value * value if p.get("difference") else value * value
        case "run_error":
            return int((p["bit"] == 0 and p["length"] % 2 == 0) or (p["bit"] == 1 and p["length"] % 2 == 1))
        case "run_reset":
            return "ZO" if p["first"] == 0 else "OO"
        case "prefix_fallback":
            history = p["history"]
            return next(k for k in range(3, -1, -1) if history.endswith("1011"[:k]))
        case "lsb_five":
            return ((p["state"] + p["bit"]) * 3) % 5
        case "winner":
            return next((x for x in p["arrivals"] if x != "-"), "-")
        case "one_sensor":
            return "ambiguous"
        case "door_retreat":
            return 0
        case "pipeline_diagnosis":
            return "insufficient"
        case "bubble_input":
            return 0 if p.get("inverse") else p["a"] & (1 - p["b"])
        case "promise_mask":
            return p["a"] ^ p["b"]
        case "hysteresis":
            return 1 if p["vin"] >= p["high"] else 0 if p["vin"] <= p["low"] else p["previous"]
        case "threshold_gap":
            return "low" if p["vin"] <= p["vil"] else "high" if p["vin"] >= p["vih"] else "unspecified"
        case "compare_split":
            return tuple(sorted(p["left"] + p["right"])[: len(p["left"])])
        case "threshold_witness":
            return (p["low"] + p["high"]) / 2
        case "padding_failure":
            return tuple(sorted(p["real"] + [p["sentinel"]])[: len(p["real"])])
        case _:
            raise AssertionError(method)


DOMAINS = {
    "doping": {
        "permanent": loc("זיהום קבוע של החומר", "Permanent material doping"),
        "reversible": loc("שכבת היפוך הנשלטת במתח", "Voltage-controlled inversion layer"),
        "insulator": loc("בידוד השער", "Gate insulation"),
        "inductor": loc("אנרגיית סליל", "Inductor energy"),
    },
    "mos_on": {
        "off": loc("מתחת לסף; אין תעלת היפוך במודל", "Below threshold; no inversion channel in the model"),
        "on": loc("מעל הסף; תעלת היפוך אפשרית", "Above threshold; inversion channel possible"),
        "always": loc("תמיד דלוק ללא תלות במתחים", "Always on regardless of voltage"),
        "vdd": loc("רק VDD קובע", "Only VDD matters"),
    },
    "mos_region": {
        "off": loc("קיטעון", "Cutoff"),
        "linear": loc("אזור לינארי", "Linear region"),
        "saturation": loc("רוויה", "Saturation"),
        "breakdown": loc("פריצה בהכרח", "Necessarily breakdown"),
    },
    "timing_exception": {
        "valid": loc("החריגה תואמת את החוזה שנמסר", "The exception matches the stated contract"),
        "invalid": loc(
            "החריגה אינה מוצדקת בחוזה שנמסר", "The exception is unsupported by the stated contract"
        ),
        "hold": loc("היא מתקנת אוטומטית כל hold", "It automatically fixes all hold failures"),
        "reset": loc("היא מאפסת את האוגרים", "It resets registers"),
    },
    "band_margin": {
        "safe": loc("בתוך החלון הפתוח שנבחר", "Inside the selected open safe interval"),
        "unsafe": loc("אינו בתוך החלון הפתוח שנבחר", "Not inside the selected open safe interval"),
        "iq": loc("בטוח רק כי זו בהכרח דגימת I/Q", "Safe because this must be I/Q sampling"),
        "dc": loc("כל המידע הופך ל־DC", "All information becomes DC"),
    },
    "secded": {
        "none": loc("אין שגיאה תחת ההבטחה", "No error under the promise"),
        "overall": loc("שגיאה בביט הזוגיות הכולל", "Error in the overall parity bit"),
        "single": loc("שגיאה יחידה במילת Hamming", "Single error in the Hamming word"),
        "double": loc("שתי שגיאות: לזהות ולא לתקן כיחידה", "Double error: detect,do not single-correct"),
    },
    "short_syndrome": {
        "correct": loc("להפוך את הביט במיקום הסינדרום", "Flip the bit at the syndrome position"),
        "clean": loc("ללא שגיאה תחת הבטחת יחיד", "No error under the single-error promise"),
        "reject": loc("לדחות כסינדרום מחוץ למודל", "Reject as outside the fault model"),
        "all": loc("להפוך את כל ביטי המידע", "Flip all data bits"),
    },
    "commit_ack": {
        "safe": loc("ההנפקה אינה קודמת לנראות הכתיבה", "Issue does not precede write visibility"),
        "stale_possible": loc("ייתכן ערך ישן בלי forwarding", "Stale data is possible without forwarding"),
        "drop": loc("מותר למחוק את בקשת הקריאה", "Discarding the read request is allowed"),
        "clock": loc("אין צורך בשעון", "No clock is needed"),
    },
    "wait_evidence": {
        "safe": loc("המתנה זו מספיקה למקרה המספרי בלבד", "This wait suffices for this numeric case only"),
        "premature": loc("ההתקדמות מוקדמת מההשלמה", "Progress precedes completion"),
        "always": loc("כל latency עתידי יהיה זהה", "Every future latency must match"),
        "cancel": loc("הפעולה מתבטלת מעצמה", "The operation cancels itself"),
    },
    "immediate_completion": {
        "RESP": loc("RESP: לשמור תגובה", "RESP: retain response"),
        "WAIT": loc("WAIT: להמתין להשלמה", "WAIT: wait for completion"),
        "ISSUE": loc("ISSUE: להמשיך להציג פקודה", "ISSUE: keep offering the command"),
        "IDLE": loc("IDLE: למחוק את המטא־נתונים", "IDLE: discard metadata"),
    },
    "complement_load": {
        "X": loc("רק X נטען", "Only X loads"),
        "Y": loc("רק Y נטען", "Only Y loads"),
        "both": loc("שניהם נטענים", "Both load"),
        "neither": loc("שניהם מחזיקים ללא טעינה", "Neither loads"),
    },
    "compare_msb": {
        "greater": loc("A>B", "A>B"),
        "less": loc("A<B", "A<B"),
        "equal": loc("A=B", "A=B"),
        "none": loc("אין יחס מוגדר למילים חוקיות", "No relation exists for valid words"),
    },
    "winner": {
        "A": loc("A", "A"),
        "B": loc("B", "B"),
        "C": loc("C", "C"),
        "-": loc("טרם נשמר מנצח", "No winner retained yet"),
    },
    "one_sensor": {
        "ambiguous": loc("אותו רצף אינו מבחין בין הכיוונים", "The trace cannot distinguish direction"),
        "entry": loc("בהכרח כניסה", "Necessarily entry"),
        "exit": loc("בהכרח יציאה", "Necessarily exit"),
        "two": loc("בהכרח עברו 2 אנשים", "Necessarily 2 people crossed"),
    },
    "pipeline_diagnosis": {
        "insufficient": loc("אין אבחנה יחידה מהמספר לבדו", "The edge count alone is insufficient"),
        "setup": loc("זו הוכחה יחידה להפרת setup", "This uniquely proves a setup violation"),
        "hold": loc("זו הוכחה יחידה להפרת hold", "This uniquely proves a hold violation"),
        "correct": loc("כל קלט בהכרח היה תקין", "Every input was necessarily valid"),
    },
    "threshold_gap": {
        "low": loc("0 מובטח לפי הגבול", "0 guaranteed by the bound"),
        "high": loc("1 מובטח לפי הגבול", "1 guaranteed by the bound"),
        "unspecified": loc("הערך הלוגי אינו מובטח", "Logical value is unspecified"),
        "half": loc("ביט שערכו 0.5", "A bit with value 0.5"),
    },
}


def choices(method, value):
    if method in DOMAINS:
        domain = DOMAINS[method]
        return [domain[value]] + [text for key, text in domain.items() if key != value]
    if isinstance(value, (int, float)):
        candidates = [value + 1, value - 1, value + 2, value * 2, value / 2, value + 3]
    elif isinstance(value, (tuple, list)):
        candidates = [
            tuple(x + 1 for x in value),
            tuple(reversed(value)),
            tuple(0 for x in value),
            tuple(x - 1 for x in value),
            tuple(x + 2 for x in value),
        ]
    elif method == "run_reset":
        candidates = ["ZO", "ZE", "OO", "OE"]
    elif method == "round_robin":
        candidates = [
            ", ".join(["R"] * len(value.split(","))),
            ", ".join(["W"] * len(value.split(","))),
            ", ".join(reversed(value.split(", "))),
            value + ", R",
        ]
    else:
        raise AssertionError((method, value))
    texts = [fmt(value)]
    for candidate in candidates:
        if fmt(candidate) not in texts:
            texts.append(fmt(candidate))
        if len(texts) == 4:
            break
    assert len(texts) == 4, (method, value, texts)
    return [loc(t, t) for t in texts]


def add(
    number,
    topic,
    prep,
    title_he,
    title_en,
    take_he,
    take_en,
    method,
    prompt_he,
    prompt_en,
    explain_he,
    explain_en,
    cases,
):
    assert len(cases) == 5, (number, len(cases))
    SPECS.append(
        dict(
            number=number,
            topic=topic,
            prep=prep,
            title=loc(title_he, title_en),
            takeaway=loc(take_he, take_en),
            method=method,
            prompt=loc(prompt_he, prompt_en),
            explanation=loc(explain_he, explain_en),
            cases=cases,
        )
    )


def definitions():
    # Electrical behavior: each objective is absent from the previous 125 cards.
    add(
        126,
        "gates",
        99,
        "אותה עקומה,קיבול אחר",
        "Same curve,different capacitance",
        "מדידת RC אינה מפרידה בין R ל־C בלי מידע נוסף.",
        "An RC response alone does not separate R from C.",
        "rc_ambiguity",
        "נמדדה קבועת זמן tau={tau}ms. איזה C ב־µF מתאים אם R={r}kΩ? R אינו ידוע מהעקומה לבדה.",
        "Measured tau={tau}ms. What C in µF fits R={r}kΩ? The curve alone does not specify R.",
        "C=tau/R. שינוי R משנה את הקיבול המתאים לאותה עקומה; צריך למדוד או לדעת את R בנפרד.",
        "C=tau/R. Changing R changes the compatible capacitance while preserving the curve; independently measure or know R.",
        [dict(tau=t, r=r) for t, r in [(2, 1), (2, 2), (3, 6), (0.5, 5), (10, 0.5)]],
    )
    add(
        127,
        "gates",
        99,
        "חצי מתח אינו קבוע זמן",
        "Half voltage is not one time constant",
        "זמן חצייה תלוי גם בסף התצפית.",
        "Crossing time depends on the observation threshold.",
        "rc_half",
        "קבל נטען ממדרגה דרך R={r}kΩ,עם C={c}nF. מתי המתח מגיע לחצי מערכו הסופי,ב־µs?",
        "A step charges C={c}nF through R={r}kΩ. When does it reach half its final voltage,in µs?",
        "מהתגובה 1−exp(−t/RC) מתקבל t=RC ln(2),ולא RC. הנתונים כאן במודל אידאלי.",
        "From 1−exp(−t/RC),the crossing is RC ln(2),not RC. This is an ideal lumped model.",
        [dict(r=r, c=c) for r, c in [(1, 1), (2, 3), (5, 0.2), (0.5, 8), (10, 0)]],
    )
    add(
        128,
        "gates",
        132,
        "איזה מתח רציף על הקבל?",
        "Which capacitor voltage stays continuous?",
        "קפיצה בשני הקצוות יכולה לשמר את המתח ביניהם.",
        "Both terminals may jump while their difference stays continuous.",
        "cap_jump",
        "בקבל טורי אידאלי,B משתנה מ־{before_b}V ל־{after_b}V. C היה {before}V לפני הקפיצה. מהו C מיד אחריה,ללא clamp?",
        "Across an ideal coupling capacitor,B changes from {before_b}V to {after_b}V. Node C was {before}V. What is C immediately afterward,without a clamp?",
        "המתח C−B על הקבל נשמר בקפיצה ללא הזרקת מטען; לכן שינוי C שווה לשינוי B.",
        "Without impulsive injected charge,C−B stays continuous; the change in C equals the change in B.",
        [
            dict(before_b=b, after_b=a, before=c)
            for b, a, c in [(3, 0, 3), (0, 3, 3), (5, 0, 4), (1, 2, 0), (2, 2, 1)]
        ],
    )
    add(
        129,
        "gates",
        132,
        "אחרי שהמעבר נגמר",
        "After the transition ends",
        "קבל טורי אינו מעביר שינוי DC קבוע.",
        "A series capacitor does not pass a permanent DC change.",
        "cap_dc",
        "B קבוע אחרי מעבר. C מחובר דרך נגד ל־VDD={vdd}V וכניסת האינוורטר אידאלית. לאיזה מתח C שואף לאחר זמן רב?",
        "B stays constant after an edge. A resistor pulls C to VDD={vdd}V; the inverter input is ideal. What voltage does C approach after a long time?",
        "במצב DC אין זרם קבל מתמשך. ללא זרם כניסה אין נפילת מתח על הנגד,ולכן C שואף ל־VDD.",
        "At DC no capacitor current persists. With zero input current there is no resistor drop,so C approaches VDD.",
        [dict(vdd=v) for v in [1, 1.8, 2.5, 3.3, 5]],
    )
    add(
        130,
        "gates",
        132,
        "האם המסילה היא מהדק?",
        "Is the rail automatically a clamp?",
        "אין להוסיף דיודת הגנה למודל שלא הגדיר אותה.",
        "Do not silently add a protection diode to a model.",
        "overshoot",
        "במודל קבל טורי ללא clamp,C הוא {before}V וקצה B קופץ ב־{jump}V. מהו C מיד אחרי הקפיצה,גם אם עבר את VDD?",
        "In an unclamped coupling model,C is {before}V and B jumps by {jump}V. What is C immediately afterward,even if it exceeds VDD?",
        "המודל מתיר overshoot: מוסיפים ל־C את אותה קפיצה. רכיב פיזי עשוי לכלול הגנה,שמשנה גם את מצב הקבל.",
        "The model permits overshoot:add the same step to C. Physical protection may limit it and change capacitor history.",
        [dict(before=b, jump=j) for b, j in [(3, 3), (2, 1), (5, 5), (1, -2), (0, 2)]],
    )
    add(
        131,
        "gates",
        132,
        "המעבר הבא זוכר את הקודם",
        "The next edge remembers the previous one",
        "מעבירים את המצב האנלוגי בין קטעי הזמן.",
        "Carry analog state across waveform segments.",
        "cap_history",
        "C מתחיל ב־{start}V ונרגע לעבר VDD={vdd}V. עד הקצה הבא פקטור הדעיכה הוא {decay}; אז מתווספת קפיצה {jump}V. מהו המתח החדש?",
        "C starts at {start}V and relaxes toward VDD={vdd}V. Decay factor before the next edge is {decay}; that edge adds {jump}V. What is the new voltage?",
        "לפני הקצה C=VDD+(Cstart−VDD)·decay. רק לאחר חישוב זה מוסיפים את הקפיצה; אין לאתחל ל־VDD בכל קצה.",
        "Before the edge,C=VDD+(Cstart−VDD)·decay. Then add the step; do not reset to VDD at every edge.",
        [
            dict(start=s, vdd=v, decay=d, jump=j)
            for s, v, d, j in [
                (0, 4, 0.5, 4),
                (8, 4, 0.5, -4),
                (0, 2, 0.25, 2),
                (3, 3, 0.5, -3),
                (1, 5, 0, 1),
            ]
        ],
    )
    add(
        132,
        "gates",
        115,
        "שער מבודד עדיין נטען",
        "An insulated gate still charges",
        "זרם DC קטן אינו אומר שאין עומס בזמן מעבר.",
        "Tiny DC current does not imply zero switching load.",
        "gate_charge",
        "שער MOS מיוצג בקיבול C={c}pF. מתחו משתנה ב־{dv}V. מה המטען שהדרייבר מעביר,ב־pC,במודל הקיבולי?",
        "A MOS gate is modeled as C={c}pF. Its voltage changes by {dv}V. What charge does its driver transfer,in pC?",
        "Q=C·ΔV. בידוד השער אינו מבטל את הקיבול; מקור ההנעה מספק או שואב מטען במעבר.",
        "Q=C·ΔV. Gate insulation does not remove capacitance; the driver supplies or removes charge during transitions.",
        [dict(c=c, dv=v) for c, v in [(2, 3), (1, 1.8), (5, 0), (0.5, -2), (4, 2.5)]],
    )
    add(
        133,
        "gates",
        115,
        "זיהום לעומת תעלת היפוך",
        "Doping versus inversion",
        "לא כל ריכוז אלקטרונים נוצר באותו מנגנון.",
        "Carrier concentration can arise through different mechanisms.",
        "doping",
        "במודל MOS,הפעולה המתוארת היא {description_he}. איזו תוצאה מתאימה?",
        "In a MOS model,the action is {description_en}. Which result fits?",
        "השתלת מזהמים יוצרת אזור חומר מסומם; מתח שער יוצר שכבת היפוך הפיכה ואינו מחליף את הרכב המזהמים.",
        "Implantation changes material doping; gate bias creates a reversible inversion layer without replacing dopants.",
        [
            dict(operation=o, description_he=h, description_en=e)
            for o, h, e in [
                ("implant", "השתלת תורמים ב־source", "implanting donors in the source"),
                ("gate", "העלאת מתח השער מעל הסף", "raising gate bias above threshold"),
                ("gate", "הסרת מתח השער אחרי היפוך", "removing gate bias after inversion"),
                ("implant", "יצירת אזור drain מסוג n+", "forming an n+ drain"),
                ("gate", "שינוי אלקטרוסטטי של פני המצע", "electrostatically changing the body surface"),
            ]
        ],
    )
    add(
        134,
        "gates",
        115,
        "מתח שער ביחס למי?",
        "Gate voltage relative to what?",
        "הסף תלוי ב־VGS,לא בשם מסילת האספקה.",
        "Threshold compares VGS,not merely a supply name.",
        "mos_on",
        "ל־NMOS ארוך־תעלה VG={vg}V,VS={vs}V,VT={vt}V. מתעלמים מזרם תת־סף. מה קובע המודל לגבי תעלת היפוך?",
        "A long-channel NMOS has VG={vg}V,VS={vs}V,VT={vt}V. Ignore subthreshold current. What does the model say about inversion?",
        "מחשבים VGS=VG−VS ומשווים ל־VT. מתח שער גבוה ביחס לאדמה לבדו אינו מספיק אם גם ה־source עולה.",
        "Compute VGS=VG−VS and compare with VT. A high gate-to-ground voltage alone is insufficient if the source also rises.",
        [dict(vg=g, vs=s, vt=t) for g, s, t in [(2, 0, 1), (2, 1.5, 1), (1, 0, 1), (3, 1, 0.5), (0, 0, 1)]],
    )
    add(
        135,
        "gates",
        115,
        "מעל הסף אינו בהכרח רוויה",
        "Above threshold need not mean saturation",
        "אזור פעולה נקבע משילוב מתחים.",
        "Operating region depends on several voltages.",
        "mos_region",
        "במודל NMOS ארוך־תעלה,VGS={vgs}V,VT={vt}V,VDS={vds}V. הזניחו אפקטים קצרים. מהו אזור הפעולה?",
        "For a long-channel NMOS,VGS={vgs}V,VT={vt}V,VDS={vds}V. Ignore short-channel effects. What is its region?",
        "אם VGS≤VT זהו קיטעון במודל. אחרת רוויה דורשת VDS≥VGS−VT; מתחת לגבול זהו אזור לינארי.",
        "If VGS≤VT,the model is cutoff. Otherwise saturation needs VDS≥VGS−VT; below that boundary the region is linear.",
        [dict(vgs=g, vt=t, vds=d) for g, t, d in [(3, 1, 1), (3, 1, 2), (3, 1, 4), (0.5, 1, 2), (2, 0.5, 0)]],
    )
    add(
        136,
        "gates",
        115,
        "מכפילים את מתח היתר",
        "Scaling overdrive",
        "מודל ריבועי אינו יחס ישר במתח היתר.",
        "A square-law model is not linear in overdrive.",
        "mos_square",
        "במודל רוויה ID=K(VGS−VT)² עם K קבוע,מתח היתר מוכפל ב־{factor}. פי כמה גדל הזרם?",
        "In saturation ID=K(VGS−VT)² with fixed K,the overdrive is multiplied by {factor}. What is the current factor?",
        "הגורם נכנס בריבוע. ההשוואה מניחה ש־VT,K ואזור הרוויה נשארו מתאימים; אינה כלל לכל MOS מודרני.",
        "The factor is squared. This holds with fixed VT,K and continued saturation,not as a universal modern-MOS rule.",
        [dict(factor=x) for x in [2, 3, 0.5, 1, 4]],
    )
    add(
        137,
        "gates",
        153,
        "למה האחד אינו מגיע למסילה?",
        "Why is high below the rail?",
        "עומס NMOS מסוג enhancement יכול לתת רמה גבוהה מוחלשת.",
        "An enhancement-NMOS load can produce a degraded high.",
        "nmos_high",
        "בעומס NMOS ששערו ו־drain שלו ב־VDD={vdd}V,מודל סף קבוע VT={vt}V וללא body effect. לאיזה VOH שואף המוצא ללא עומס DC?",
        "An NMOS load has gate/drain at VDD={vdd}V. Assume fixed VT={vt}V,no body effect and no DC load. What VOH does it approach?",
        "בעת עליית המוצא,VGS של העומס קטן. במודל הוא מתקרב ל־VT ולכן VOH≈VDD−VT,לא VDD.",
        "As output rises,the load VGS falls toward VT,giving VOH≈VDD−VT rather than VDD in this model.",
        [dict(vdd=v, vt=t) for v, t in [(5, 1), (3.3, 0.7), (2, 0.5), (1.8, 0.4), (4, 1.5)]],
    )
    add(
        138,
        "gates",
        153,
        "אפס לוגי עם זרם קבוע",
        "Logical low with static current",
        "פלט יציב אינו מבטיח שההספק הסטטי אפס.",
        "A stable output does not imply zero static power.",
        "static_current",
        "להמחשת עומס NMOS,מחליפים מסלול pull-up ב־{pullup}kΩ ו־pull-down פעיל ב־{pulldown}kΩ בטור. VDD={vdd}V. מה זרם המסילה ב־mA?",
        "For an NMOS-load illustration,use {pullup}kΩ pull-up and active {pulldown}kΩ pull-down in series. VDD={vdd}V. What is rail current in mA?",
        "שני מסלולים מוליכים יוצרים זרם גם בלי מיתוג: I=VDD/(Rup+Rdown). זוהי המחשת התנגדויות,לא מודל MOS מדויק.",
        "Both conducting paths create current without switching:I=VDD/(Rup+Rdown). This resistance illustration is not an exact MOS model.",
        [
            dict(pullup=u, pulldown=d, vdd=v)
            for u, d, v in [(9, 1, 5), (4, 1, 3), (1, 1, 2), (19, 1, 4), (2, 3, 5)]
        ],
    )
    add(
        139,
        "gates",
        170,
        "מה נשמר ברגע ההחלפה?",
        "What survives the switching instant?",
        "תנאי התחלה פיזיקליים קובעים את צורת התגובה.",
        "Physical initial conditions determine the response.",
        "lc_initial",
        "קבל אידאלי טעון ל־{v0}V מחובר לסליל שזרמו היה 0,ללא הזרקת אנרגיה. מה הזוג vC,iL מיד לאחר ההעברה?",
        "An ideal capacitor charged to {v0}V connects to an inductor initially carrying 0 current,without injected energy. What is vC,iL immediately afterward?",
        "מתח הקבל וזרם הסליל רציפים בהעברה האידאלית. אין להחליף תנאי התחלה בתוצאה הסופית של מעגל נגדי.",
        "Capacitor voltage and inductor current remain continuous at the ideal transfer. A resistive final-state intuition cannot replace initial conditions.",
        [dict(v0=v) for v in [1, 3, -2, 0, 5]],
    )
    add(
        140,
        "gates",
        170,
        "אפס מתח,זרם מרבי",
        "Zero voltage,maximum current",
        "אנרגיה יכולה לעבור מהשדה החשמלי למגנטי.",
        "Energy can move from electric to magnetic storage.",
        "lc_quarter",
        "ב־LC אידאלי,V0={v0}V,C={c}F,L={l}H וזרם התחלתי 0. ברבע מחזור ראשון מתח הקבל 0. מהו זרם הסליל החיובי כלפי מטה?",
        "In ideal LC,V0={v0}V,C={c}F,L={l}H and initial current0. At the first quarter-period capacitor voltage is0. What is downward inductor current?",
        "משימור אנרגיה LI²/2=CV0²/2 מתקבל I=V0√(C/L),עם הסימן לפי ההגדרה. אפס מתח אינו אפס אנרגיה כוללת.",
        "Energy conservation gives LI²/2=CV0²/2 and I=V0√(C/L),with the defined sign. Zero voltage is not zero total energy.",
        [
            dict(v0=v, c=c, l=axis_value)
            for v, c, axis_value in [(2, 1, 1), (3, 4, 1), (-2, 1, 4), (0, 2, 1), (1, 1, 4)]
        ],
    )
    add(
        141,
        "gates",
        170,
        "הקבל יכול להחליף קוטביות",
        "The capacitor can reverse polarity",
        "סליל אינו רק נגד שמרוקן קבל.",
        "An inductor is not merely a capacitor-discharging resistor.",
        "lc_half",
        "קבל מתחיל ב־V0={v0}V וזרם הסליל 0. מה מתח הקבל אחרי חצי מחזור LC אידאלי וללא הפסדים?",
        "A capacitor starts at V0={v0}V with zero inductor current. What is its voltage after half an ideal lossless LC period?",
        "vC=V0 cos(ωt). בחצי מחזור cos(π)=−1; האנרגיה חזרה לקבל בקוטביות הפוכה.",
        "vC=V0 cos(ωt). At half a period cos(π)=−1:energy is back in the capacitor with reversed polarity.",
        [dict(v0=v) for v in [1, 3, -2, 0, 5]],
    )
    add(
        142,
        "gates",
        170,
        "משנים L או C",
        "Changing L or C",
        "תדר עצמי נקבע משורש מכפלת L ו־C.",
        "Natural frequency depends on the square root of LC.",
        "lc_period_ratio",
        "במעגל LC אידאלי,L מוכפל ב־{l_ratio} ו־C מוכפל ב־{c_ratio}. פי כמה משתנה המחזור T?",
        "In ideal LC,L is multiplied by {l_ratio} and C by {c_ratio}. What is the period multiplier?",
        "T=2π√(LC),ולכן יחס המחזורים הוא √(Lratio·Cratio). מתח הטעינה אינו קובע את המחזור במודל הלינארי.",
        "T=2π√(LC),so period scales by √(Lratio·Cratio). Initial voltage does not set the period in this linear model.",
        [
            dict(l_ratio=axis_value, c_ratio=c)
            for axis_value, c in [(4, 1), (1, 9), (4, 4), (0.25, 1), (0.25, 4)]
        ],
    )
    add(
        143,
        "gates",
        175,
        "מחיר הבאפר בנתיב השלם",
        "Count the whole buffered path",
        "הקלה על המקור אינה מבטלת השהיית יציאה.",
        "Unloading the source does not remove output delay.",
        "buffer_delay",
        "מודל באפר:Rs={rs},Cin={cin},Rb={rb},CL={cl},tb={tb},ביחידות עקביות. מה אומדן ההשהיה ln(2)(RsCin+RbCL)+tb?",
        "Buffer model:Rs={rs},Cin={cin},Rb={rb},CL={cl},tb={tb},in consistent units. What is ln(2)(RsCin+RbCL)+tb?",
        "המקור טוען את Cin,ואז הבאפר מניע את CL. מוסיפים גם tb; לא משווים רק התנגדות יציאה.",
        "The source charges Cin,then the buffer drives CL. Add tb as well; output resistance alone is not the complete comparison.",
        [
            dict(rs=r, cin=i, rb=b, cl=c, tb=t)
            for r, i, b, c, t in [
                (10, 1, 1, 20, 2),
                (2, 1, 1, 3, 1),
                (5, 0, 2, 4, 0),
                (4, 2, 1, 0, 3),
                (10, 1, 1, 1, 10),
            ]
        ],
    )
    add(
        144,
        "gates",
        175,
        "מתי ההוספה משתלמת?",
        "When does an added buffer pay off?",
        "רכיב נוסף עשוי להאט עומס קטן.",
        "An added component may slow a small load.",
        "buffer_breakeven",
        "Rs={rs}>Rb={rb},Cin={cin},tb={tb}. באומדן RC,מהו CL שבו ln(2)RsCL שווה להשהיה עם באפר?",
        "Rs={rs}>Rb={rb},Cin={cin},tb={tb}. In the RC estimate,what CL makes direct ln(2)RsCL equal buffered delay?",
        "פותרים CL=[RsCin+tb/ln(2)]/(Rs−Rb). מעליו הבאפר עוזר במודל ומתחתיו עלול להזיק; זו אינה בחירת תא פיזי.",
        "Solve CL=[RsCin+tb/ln(2)]/(Rs−Rb). Above it the model benefits; below it buffering may hurt. This is not physical cell selection.",
        [
            dict(rs=r, rb=b, cin=i, tb=t)
            for r, b, i, t in [(10, 2, 1, 0), (8, 4, 2, 0), (4, 1, 3, 1), (20, 5, 0.5, 2), (5, 4, 1, 0)]
        ],
    )
    add(
        145,
        "gates",
        172,
        "לד צריך גם הגבלת זרם",
        "An LED also needs current limiting",
        "טבלת אמת אינה קובעת זרם מותר.",
        "A truth table does not specify allowed current.",
        "led_resistor",
        "לד טורי:Vs={vs}V,Vf={vf}V,נפילת דרייבר Vd={vd}V וזרם רצוי {current}mA. איזה נגד ב־kΩ נותן המודל האידאלי?",
        "Series LED:Vs={vs}V,Vf={vf}V,driver drop Vd={vd}V,target current{current}mA. What resistor in kΩ follows the ideal model?",
        "R=(Vs−Vf−Vd)/I. זו המחשה; במימוש בודקים טווח Vf,דירוגי זרם והספק,ולא מניחים ששער מספק זרם בלתי מוגבל.",
        "R=(Vs−Vf−Vd)/I. Check Vf variation,current/power ratings in hardware; a logic output is not an unlimited current source.",
        [
            dict(vs=v, vf=f, vd=d, current=i)
            for v, f, d, i in [(5, 2, 0, 3), (3.3, 2, 0, 2), (5, 2, 0.2, 2), (2, 1.5, 0, 1), (12, 3, 1, 4)]
        ],
    )
    add(
        146,
        "sequential",
        176,
        "שעון לכידה מאוחר",
        "A later capture clock",
        "אותו skew פועל בכיוונים הפוכים על setup ו־hold.",
        "The same skew affects setup and hold in opposite directions.",
        "skew_effect",
        "skew חיובי מוגדר כלכידה מאוחרת. מוסיפים s={s}ns,בלי שינוי אחר. מה שינוי ה־slack בסדר setup,hold?",
        "Positive skew means later capture. Add s={s}ns with nothing else changed. What are the setup,hold slack changes?",
        "ל־setup מתווסף s ול־hold נגרע s באותו נתיב חד־מחזורי. סימן skew חייב להישאר עקבי.",
        "Setup gains s while hold loses s on this one-cycle path. Keep the skew sign convention consistent.",
        [dict(s=x) for x in [0.2, -0.1, 0, 0.5, -0.4]],
    )
    add(
        147,
        "sequential",
        176,
        "לאן נעלם מרווח הביטחון?",
        "Where did timing margin go?",
        "אי־ודאות צורכת תקציב ולא מוסיפה זמן נתון.",
        "Uncertainty consumes budget rather than creating data time.",
        "uncertainty",
        "נוספו אי־ודאות setup של {us}ns ואי־ודאות hold של {uh}ns. מה שינוי ה־slack בסדר setup,hold?",
        "Add setup uncertainty{us}ns and hold uncertainty{uh}ns. What are the setup,hold slack changes?",
        "כל אי־ודאות מקטינה את המרווח של הבדיקה המתאימה. אלו שני תקציבים נפרדים,לא שינוי במחזור הנתון.",
        "Each uncertainty reduces its corresponding margin. They are separate budgets,not a change to the stated clock period.",
        [dict(us=u, uh=h) for u, h in [(0.1, 0.2), (0, 0.3), (0.4, 0), (0.05, 0.05), (0.2, 0.1)]],
    )
    add(
        148,
        "sequential",
        176,
        "מהירות יכולה ליצור תקלה אחרת",
        "Speed can create another violation",
        "שיפור נתיב מקסימום מחייב בדיקה מחודשת של המינימום.",
        "Improving maximum delay requires rechecking minimum delay.",
        "speedup",
        "תיקון מקטין Dmax ב־{dmax_reduction}ns ו־Dmin ב־{dmin_reduction}ns. כל היתר קבוע. מה שינוי setup slack,hold slack?",
        "A repair reduces Dmax by{dmax_reduction}ns and Dmin by{dmin_reduction}ns. Everything else stays fixed. What are the setup,hold slack changes?",
        "נתון מאוחר מגיע מוקדם יותר ולכן setup משתפר. גם הנתון המוקדם מקדים ולכן hold קטן; אין להסיק ששניהם השתפרו.",
        "Latest arrival improves setup,while earlier earliest arrival reduces hold margin. Faster does not automatically improve both.",
        [
            dict(dmax_reduction=a, dmin_reduction=b)
            for a, b in [(0.3, 0.1), (0.2, 0), (0, 0.2), (0.5, 0.5), (0.1, 0.4)]
        ],
    )
    add(
        149,
        "sequential",
        176,
        "דוח נוח או חוזה נכון?",
        "A convenient report or a valid contract?",
        "חריגת תזמון זקוקה להצדקה פונקציונלית.",
        "A timing exception needs a functional basis.",
        "timing_exception",
        "הפרוטוקול מבטיח שהמקלט לא דורש נתון לפני {functional_cycles} מחזורים. מגדירים ל־setup תקציב של {constraint_cycles} מחזורים,ובודקים hold בנפרד. האם ההרחבה מוצדקת בהבטחה הזאת?",
        "The protocol guarantees no required capture before{functional_cycles}cycles. Setup is constrained to{constraint_cycles}cycles and hold is checked separately. Does that promise justify this budget?",
        "אסור לתת לכלי יותר זמן ממה שהפונקציה מאפשרת. התחייבות פרוטוקולית מתאימה יכולה להצדיק multicycle; דוח אדום לבדו אינו הצדקה.",
        "The tool cannot be granted more time than function permits. A matching protocol promise can justify multicycle; a red report alone cannot.",
        [dict(functional_cycles=f, constraint_cycles=c) for f, c in [(2, 2), (1, 2), (3, 2), (2, 3), (1, 1)]],
    )
    add(
        150,
        "gates",
        177,
        "מי טוען את קבל הצימוד?",
        "Who charges the coupling capacitor?",
        "זרם צימוד תלוי בשינוי הפרש המתחים.",
        "Coupling current depends on changing voltage difference.",
        "coupling_ceff",
        "במודל שיפועים מיושרים,Cg={cg} ו־Cc={cc}. היחס k=a′/v′ הוא {ratio}. מהו Ceff=Cg+Cc(1−k)?",
        "For prescribed aligned slopes,Cg={cg},Cc={cc},and k=a′/v′={ratio}. What is Ceff=Cg+Cc(1−k)?",
        "ביחד קבל הצימוד עשוי לא לדרוש מטען,מול שכן שקט הוא נטען פעם אחת ובמעבר נגדי שווה פעמיים. זו המחשת שיפועים,לא גורם אוניברסלי.",
        "Same ramps can remove coupling charge; quiet and equal opposite ramps give one and two coupling contributions. This prescribed-slope model is not universal.",
        [dict(cg=g, cc=c, ratio=r) for g, c, r in [(2, 1, 1), (2, 1, 0), (2, 1, -1), (3, 0, -1), (1, 2, -1)]],
    )
    add(
        151,
        "gates",
        177,
        "רעש בלי מעבר מתוכנן",
        "Noise without an intended transition",
        "קורבן שקט דורש ניתוח רעש ולא רק השהיה.",
        "A quiet victim needs noise analysis,not only delay analysis.",
        "quiet_noise",
        "בהמחשה מיידית,דרייבר הקורבן פתוח; Cg={cg},Cc={cc}. ה־aggressor קופץ ב־{da}V. משימור מטען,מה קפיצת מתח הקורבן?",
        "For an instantaneous illustration,the victim driver is open; Cg={cg},Cc={cc}. The aggressor steps by{da}V. By charge conservation,what is the victim step?",
        "משימור מטען מתקבל Δv=Cc·Δa/(Cg+Cc). אחר כך הדרייבר וההתנגדויות משנים את הפולס; אין לייחס זאת למעבר לוגי מתוכנן.",
        "Charge conservation gives Δv=Cc·Δa/(Cg+Cc). Driver resistance changes the later pulse; this is not an intended logical transition.",
        [dict(cg=g, cc=c, da=a) for g, c, a in [(3, 1, 4), (1, 1, 2), (2, 0, 3), (1, 3, -2), (4, 1, 5)]],
    )
    add(
        152,
        "gates",
        177,
        "חלון הפעילות חשוב",
        "Activity windows matter",
        "אותם ערכים סופיים אינם מבטיחים אותה הפרעת תזמון.",
        "Identical final values need not imply identical timing interference.",
        "window_overlap",
        "להערכת חפיפה בלבד,מעבר הקורבן פעיל ב־[{v0},{v1}]ns ומעבר השכן ב־[{a0},{a1}]ns. כמה ns חופפים? אין כאן חישוב delay פיזי.",
        "For overlap accounting only,the victim transition spans[{v0},{v1}]ns and the aggressor spans[{a0},{a1}]ns. How many ns overlap? This is not physical delay.",
        "אורך החיתוך הוא max(0,min(ends)−max(starts)). חלון ללא חפיפה שונה ממעברים מיושרים גם אם שני הביטים מסיימים באותם ערכים.",
        "Intersection length is max(0,min(ends)−max(starts)). Nonoverlapping activity differs from aligned transitions despite identical final bits.",
        [
            dict(v0=v0, v1=v1, a0=a0, a1=a1)
            for v0, v1, a0, a1 in [(1, 4, 2, 5), (1, 2, 3, 4), (0, 3, 0, 3), (2, 6, 3, 4), (0, 1, 1, 2)]
        ],
    )
    add(
        153,
        "gates",
        177,
        "מגן מוסיף גם עומס",
        "A shield also adds load",
        "הקטנת צימוד אינה בהכרח הקטנת כל הקיבול.",
        "Less coupling does not necessarily mean less total capacitance.",
        "shield_delta",
        "במודל מעבר נגדי,Ceff=Cg+2Cc. לפני מגן:Cg={old_cg},Cc={old_cc}; אחריו:Cg={new_cg},Cc={new_cc}. מה השינוי Ceff_after−Ceff_before?",
        "For opposite ramps,Ceff=Cg+2Cc. Before shielding:Cg={old_cg},Cc={old_cc}; afterward:Cg={new_cg},Cc={new_cc}. What is Ceff_after−Ceff_before?",
        "מחשבים את שתי התרומות. מגן יכול להקטין Cc ולהגדיל Cg,ולכן צריך להעריך מחדש השהיה והספק במקום להניח שיפור חינם.",
        "Count both terms. Shielding can reduce Cc while increasing Cg,so recompute delay and power rather than assuming a free improvement.",
        [
            dict(old_cg=g, old_cc=c, new_cg=n, new_cc=k)
            for g, c, n, k in [(2, 2, 3, 0.5), (1, 1, 5, 0), (3, 0.5, 4, 0), (2, 1, 2, 0), (1, 2, 3, 1)]
        ],
    )
    add(
        154,
        "sequential",
        144,
        "סינוס שנעלם בדגימה",
        "A sine wave invisible to sampling",
        "בגבול Nyquist גם המופע חשוב.",
        "At the Nyquist boundary,phase matters.",
        "nyquist_phase",
        "x(t)=sin(2π·{frequency}t),והדגימה ב־fs=2·{frequency} בנקודות t=n/fs. מה ערך כל הדגימות האידאליות?",
        "x(t)=sin(2π·{frequency}t),sampled at fs=2·{frequency} at t=n/fs. What is every ideal sample?",
        "הדגימות הן sin(πn)=0. אות שאינו אפס יכול לתת דגימות אפס,ולכן אין הבטחה כללית לכל מופע בקצה הסגור.",
        "Samples are sin(πn)=0. A nonzero signal can have zero samples,so a closed-boundary guarantee for every phase is invalid.",
        [dict(frequency=f) for f in [1, 2, 5, 10, 100]],
    )
    add(
        155,
        "sequential",
        144,
        "אחרי הקיפול כבר מאוחר",
        "After aliasing,it is too late",
        "סינון דיגיטלי אינו מחזיר מידע שכבר התקפל.",
        "Digital filtering cannot restore already aliased information.",
        "alias",
        "קוסינוס בתדר {frequency}kHz נדגם ב־fs={fs}kHz. מה תדר ה־alias החיובי בתחום0..fs/2? נניח דגימה אחידה אידאלית.",
        "A cosine at{frequency}kHz is sampled at fs={fs}kHz. What is its nonnegative alias in0..fs/2 under ideal uniform sampling?",
        "תדרים הנבדלים בכפולות fs,ובהיפוך סימן לקוסינוס,יכולים ליצור אותן דגימות. מסנן אנלוגי לפני הדגימה מונע את הערבוב מלכתחילה.",
        "Frequencies differing by fs multiples,and sign for cosine,can share samples. Analog filtering before sampling prevents the mixing.",
        [dict(frequency=f, fs=s) for f, s in [(18, 20), (23, 20), (7, 20), (30, 20), (41, 20)]],
    )
    add(
        156,
        "sequential",
        156,
        "רוחב פס אינו כל הסיפור",
        "Bandwidth is not the whole story",
        "בדגימת bandpass גם מיקום הפס קובע.",
        "Bandpass sampling depends on band location too.",
        "band_interval",
        "לפס ממשי חיובי({fl},{fh}),ובחירת m={m}>1,מה גבולות חלון fs:2fh/m < fs < 2fl/(m−1)? הגבולות עצמם אינם כלולים.",
        "For positive real band({fl},{fh}) and m={m}>1,what are the bounds of2fh/m < fs < 2fl/(m−1)? Endpoints are excluded.",
        "שני הגבולות מונעים חפיפה בין עותקים ספקטרליים גם עם הפס השלילי. דרישה fs>2·bandwidth לבדה אינה מספיקה לכל מיקום.",
        "Both bounds prevent spectral-copy overlap,including the negative band. Merely exceeding twice bandwidth is not sufficient for every band location.",
        [
            dict(fl=axis_value, fh=h, m=m)
            for axis_value, h, m in [(90, 110, 5), (100, 120, 5), (30, 40, 3), (48, 50, 4), (20, 25, 3)]
        ],
    )
    add(
        157,
        "sequential",
        156,
        "גבול פתוח הוא דרישה אמיתית",
        "An open bound is a real condition",
        "נגיעה בקצות פס אינה מרווח בטוח לכל אות.",
        "Touching band edges is not safe margin for every signal.",
        "band_margin",
        "החוזה דורש חלון פתוח לפס({fl},{fh}),m={m}:2fh/m < fs < 2fl/(m−1). האם fs={fs} נמצא בתוכו?",
        "The contract requires the open interval for band({fl},{fh}),m={m}:2fh/m < fs < 2fl/(m−1). Is fs={fs} inside?",
        "בודקים את שתי אי־השוויונות בקפדנות. שוויון אינו עונה לחוזה הפתוח; בפס סגור טוני קצה עלולים להיות בלתי נבדלים.",
        "Check both strict inequalities. Equality fails this open contract; closed-band edge tones can become indistinguishable.",
        [
            dict(fl=axis_value, fh=h, m=m, fs=s)
            for axis_value, h, m, s in [
                (90, 110, 5, 44.5),
                (90, 110, 5, 44),
                (90, 110, 5, 45),
                (100, 120, 5, 49),
                (100, 120, 5, 48),
            ]
        ],
    )
    add(
        158,
        "bits",
        136,
        "זיהוי אינו איתור",
        "Detecting is not locating",
        "זוגיות אחת מבחינה בשינוי אך אינה מזהה את מיקומו.",
        "One parity bit can detect a change without locating it.",
        "parity_locations",
        "למילת מידע בת {n} ביטים נשמר ביט זוגיות. התגלתה זוגיות שגויה וידוע שהתקלקל בדיוק ביט מידע אחד. כמה מיקומי תקלה אפשריים עדיין מתאימים לזוגיות לבדה?",
        "An{n}-data-bit word stores one parity bit. Parity is wrong and exactly one data bit flipped. How many fault positions remain compatible with parity alone?",
        "כל אחד מביטי המידע יכול להפוך זוגיות. ללא מידע נוסף כל המיקומים אפשריים,כך שאין דרך כללית לשחזר את המילה.",
        "Every data-bit flip changes parity. Without other information all positions remain possible,so general recovery is impossible.",
        [dict(n=n) for n in [8, 4, 2, 16, 1]],
    )
    add(
        159,
        "bits",
        136,
        "כמה ביטי בדיקה צריכים?",
        "How many check bits are needed?",
        "תיקון דורש קוד נפרד לכל מיקום וגם ללא שגיאה.",
        "Correction needs distinct signatures for every position and no error.",
        "hamming_bits",
        "ל־{data} ביטי מידע נדרשת תיקון תקלה יחידה בכל המילה,כולל ביטי הבדיקה. מה r המינימלי המקיים2^r≥1+{data}+r?",
        "For{data}data bits,correct one flip anywhere including check bits. What is the smallest r satisfying2^r≥1+{data}+r?",
        "צריך להבחין בין ללא תקלה לבין כל אחד מ־data+r מיקומים. זו מגבלת יתירות,לא הוכחת מינימום שערים או מחזורי קריאה.",
        "Distinguish no error from each of data+r positions. This bounds redundancy,not minimum gate count or read latency.",
        [dict(data=n) for n in [8, 4, 1, 11, 12]],
    )
    add(
        160,
        "bits",
        136,
        "הסינדרום הוא כתובת תקלה",
        "The syndrome names the error position",
        "קבוצות בדיקה בינאריות מזהות גם ביט בדיקה פגום.",
        "Binary check groups identify failed check bits too.",
        "syndrome",
        "בקוד Hamming במיקומים1..12,בדיקת משקל k מכסה מיקומים שהביט k שלהם דולק. התהפך רק מיקום {position}. מה ערך הסינדרום?",
        "In Hamming positions1..12,weight-k checks cover positions with bit k set. Only position{position}flips. What is the syndrome value?",
        "התקלה משנה בדיוק את הבדיקות המתאימות לכתיבה הבינארית של מיקומה,ולכן הסינדרום שווה למיקום,גם כשהוא ביט בדיקה.",
        "The flip changes checks matching its binary position,so syndrome equals position,including check-bit locations.",
        [dict(position=j) for j in [10, 4, 1, 12, 7]],
    )
    add(
        161,
        "bits",
        136,
        "שתי תקלות אינן תקלה אחת",
        "Two errors are not one error",
        "SECDED מפריד תיקון יחיד מזיהוי זוג תקלות.",
        "SECDED separates single correction from double-error detection.",
        "secded",
        "ב־SECDED,לכל היותר2 תקלות. סינדרום S={syndrome},וזוגיות כוללת שגויה P={parity}. מה האבחנה? S מתייחס למילת Hamming ללא הביט הכולל.",
        "In SECDED,at most2 faults:syndrome S={syndrome},bad overall parity P={parity}. What is the diagnosis? S excludes the overall parity bit.",
        "זוגיות שגויה מתאימה למספר אי־זוגי של תקלות. עם ההבטחה,סינדרום לא אפס וזוגיות תקינה מציינים זוג שאין לתקן כיחיד.",
        "Bad parity indicates an odd count. Under the promise,nonzero syndrome with correct parity identifies a double error that must not be single-corrected.",
        [dict(syndrome=s, parity=p) for s, p in [(0, 0), (0, 1), (5, 1), (6, 0), (12, 1)]],
    )
    add(
        162,
        "bits",
        136,
        "כתובת תקלה שאינה קיימת",
        "An error position that does not exist",
        "קוד מקוצר אינו מתיר להפוך ביט מחוץ למילה.",
        "A shortened code does not permit flipping a nonexistent bit.",
        "short_syndrome",
        "בקוד Hamming מקוצר בן12 ביטים עם הבטחת עד תקלה יחידה,נקרא סינדרום {syndrome}. מה הפעולה המותרת במודל?",
        "A shortened12-bit Hamming code promises at most one fault. Its syndrome is{syndrome}. What action is valid in this model?",
        "0 מציין ללא שגיאה תחת ההבטחה,1..12 מאפשרים תיקון.13..15 אינם מיקומי מילה ולכן מצביעים על מצב מחוץ למודל.",
        "Zero means no error under the promise;1..12 locate a correction.13..15 are not stored positions and must be rejected as outside the model.",
        [dict(syndrome=s) for s in [0, 12, 13, 15, 8]],
    )
    add(
        163,
        "states",
        139,
        "תור סופי מול השהיה לא חסומה",
        "Finite queue,unbounded delay",
        "ללא backpressure או חסם תעבורה אין הבטחת אפס אובדן.",
        "Without backpressure or a traffic bound,zero loss is not guaranteed.",
        "queue_overflow",
        "תור ריק מכיל לכל היותר{capacity} בקשות. הזיכרון אינו משלים דבר בזמן שמגיעות{arrivals} בקשות שאסור לעכב. כמה אינן נכנסות לתור?",
        "An empty queue holds at most{capacity}requests. Memory completes nothing while{arrivals}unpausable requests arrive. How many do not fit?",
        "קיבולת סופית אינה סופגת זרם לא חסום. נדרשים חסם תעבורה,backpressure או חוזה דחייה וניסיון חוזר.",
        "Finite capacity cannot absorb an unbounded stream. Require bounded traffic,backpressure or explicit rejection/retry.",
        [dict(capacity=b, arrivals=a) for b, a in [(4, 5), (2, 2), (0, 1), (8, 12), (3, 1)]],
    )
    add(
        164,
        "states",
        139,
        "ACK אינו בהכרח התחייבות לזיכרון",
        "ACK need not mean committed",
        "סדר פקודות צריך להתייחס לנראות ולא רק לקבלה.",
        "Command ordering depends on visibility,not only acceptance.",
        "commit_ack",
        "כתיבה קיבלה ACK בתור ב־t=1 אך נראית לקריאות רק ב־t={visible}. קריאה לאותה כתובת מונפקת ב־t={read_issue},בלי forwarding. מה ניתן לקבוע?",
        "A write gets enqueue ACK at t=1 but becomes read-visible at t={visible}. A same-address read issues at t={read_issue},without forwarding. What follows?",
        "ACK של הכנסה לתור אינו commit. כדי למנוע ערך ישן מחכים לנראות הכתיבה או מוסיפים forwarding וחוזה סדר מתאים.",
        "An enqueue ACK is not commit. Wait for write visibility or add forwarding with an explicit ordering contract.",
        [dict(visible=v, read_issue=r) for v, r in [(5, 2), (5, 5), (3, 4), (8, 7), (2, 2)]],
    )
    add(
        165,
        "states",
        139,
        "מונה המתנה אינו ראיית השלמה",
        "A wait count is not completion evidence",
        "latency משתנה דורש אירוע השלמה או חסם מוכח.",
        "Variable latency needs completion evidence or a proven bound.",
        "wait_evidence",
        "בקר מתקדם אחרי{wait} מחזורים,אבל הפעולה המסוימת משלימה רק אחרי{actual_latency}. מה נכון למקרה הזה?",
        "A controller proceeds after{wait}cycles,but this operation completes after{actual_latency}. What is true for this case?",
        "אם ההמתנה קצרה מה־latency ההתקדמות מוקדמת. גם המתנה שמספיקה בדוגמה אינה מוכיחה חסם לכל פעולות העתיד.",
        "A wait shorter than actual latency is premature. A sufficient wait for one example does not prove a bound for future operations.",
        [
            dict(wait=w, actual_latency=axis_value)
            for w, axis_value in [(3, 5), (5, 5), (8, 2), (0, 1), (2, 9)]
        ],
    )
    add(
        166,
        "states",
        139,
        "השלמה באותה חזית",
        "Completion on the acceptance edge",
        "יש לטפל גם במקרה המהיר ביותר שהממשק מתיר.",
        "Handle the fastest completion the interface permits.",
        "immediate_completion",
        "במצב ISSUE:פקודה accepted={accepted},והשלמה תואמת done={done} באותה חזית. החוזה מתיר זאת. לאיזה מצב עוברים? accepted=0 מחייב done=0.",
        "In ISSUE,command accepted={accepted} and matching done={done} occur at this edge. The contract permits immediate completion. Which state follows? accepted=0 requires done=0.",
        "כשקבלה והשלמה חופפות שומרים תגובה ונכנסים RESP. מעבר עיוור ל־WAIT עלול להחמיץ את האירוע היחיד.",
        "When acceptance and completion coincide,retain the response and enter RESP. Blindly entering WAIT can lose the only completion event.",
        [
            dict(accepted=a, done=d, tag=i)
            for i, (a, d) in enumerate([(1, 1), (1, 0), (0, 0), (1, 1), (1, 0)])
        ],
    )
    add(
        167,
        "states",
        139,
        "מי מקבל את התור הבא?",
        "Who gets the next turn?",
        "הוגנות דורשת מדיניות בחירה מפורשת.",
        "Fairness requires an explicit arbitration policy.",
        "round_robin",
        "READ ו־WRITE מבקשים ברציפות. round-robin מקבל{n} בקשות,החל ב־{first_label}. כל פעולה ותגובה משלימות לפני הבחירה הבאה. מה סדר הקבלות?",
        "READ and WRITE request continuously. Round-robin accepts{n}requests,starting with{first_label}. Each operation and response completes before the next arbitration. What is the acceptance order?",
        "בשתי בקשות מתמשכות מחליפים זוכה בכל קבלה. זה מונע רעב בהנחת התקדמות; אינו מבטיח latency מספרי לזיכרון.",
        "With both persistent requests,the winner alternates at each acceptance. This prevents starvation under progress assumptions,not a numeric memory-latency guarantee.",
        [
            dict(n=n, first=f, first_label="R" if f == 0 else "W")
            for n, f in [(4, 0), (5, 1), (3, 0), (6, 1), (2, 0)]
        ],
    )
    add(
        168,
        "states",
        139,
        "כתובות שונות עדיין ממתינות",
        "Different addresses can still wait",
        "בטיחות בסריאליזציה באה במחיר של מקביליות.",
        "Serialization trades concurrency for a simple safety invariant.",
        "serialized_issue",
        "בקר מסוריאל אינו מקבל פעולה נוספת עד שתגובת הקודמת נצרכת בחזית{previous_response_consumed}. הוא חוזר ל־IDLE אחריה. באיזו חזית מוקדמת אפשר לקבל בקשה חדשה?",
        "A serialized controller accepts nothing new until the previous response is consumed at edge{previous_response_consumed}; IDLE begins afterward. At which earliest edge can a new request be accepted?",
        "לפי מכונת המצבים הזאת הבחירה הבאה בחזית העוקבת,גם בכתובת אחרת. זו פשרה בטוחה ולא טענת throughput מיטבי.",
        "In this state-machine contract,the next acceptance is on the following edge,even for another address. This is a safe tradeoff,not optimal throughput.",
        [dict(previous_response_consumed=n) for n in [3, 7, 1, 10, 4]],
    )
    add(
        169,
        "bits",
        145,
        "איזה חלק עוקף את המחבר?",
        "Which part bypasses the incrementer?",
        "הוספת חזקה של2 משאירה ביטים נמוכים ללא שינוי.",
        "Adding a power of2 leaves lower bits unchanged.",
        "size_low",
        "במימוש A+SIZE,‏A={a},SIZE={size}=2^k. מה ערך k הביטים הנמוכים שמועברים ללא שינוי סביב ה־incrementer? עבור k=0 התוצאה0.",
        "For A+SIZE,A={a},SIZE={size}=2^k. What value do the k low bits bypass unchanged around the incrementer? For k=0 the value is0.",
        "מפרקים A=SIZE·U+L. מקדמים רק U,והשארית L=A mod SIZE נשמרת בחיווט.",
        "Write A=SIZE·U+L. Increment only U; remainder L=A mod SIZE is retained by wiring.",
        [dict(a=a, size=s) for a, s in [(255, 4), (254, 4), (13, 2), (8, 2), (255, 1)]],
    )
    add(
        170,
        "bits",
        145,
        "הנשא שחסר לבלוק",
        "The block’s missing carry",
        "רוחב בלוק אינו מבטיח שפלט הנשיאה נגיש.",
        "A block width does not guarantee an exposed carry port.",
        "size_carry",
        "A={a},SIZE={size}; נדרשת תוצאה מדויקת בת9 ביטים. מה ביט המשקל256 של A+SIZE? ה־incrementer עצמו מוציא רק8 ביטים.",
        "A={a},SIZE={size}; the exact result needs9bits. What is its weight256 carry bit? The incrementer itself exposes only8result bits.",
        "בודקים אם A+SIZE≥256. במקרה SIZE=1 ו־A=255 הבלוק עוטף לאפס,ולכן נדרש לשחזר carry מבחוץ.",
        "Check A+SIZE≥256. For SIZE=1,A=255,the block wraps to zero; the missing carry must be generated externally.",
        [dict(a=a, size=s) for a, s in [(255, 1), (255, 4), (252, 4), (251, 4), (254, 1)]],
    )
    add(
        171,
        "bits",
        145,
        "אפס חוקי ואפס של קלט פסול",
        "Valid zero and invalid-input zero",
        "valid צריך לשמר את משמעות הנתון.",
        "Validity must preserve data meaning.",
        "size_valid",
        "גרסת8 ביטים מחזירה modulo256 עם valid=1 רק ל־SIZE∈{{1,2,4}}; אחרת valid=0,result=0. עבור A={a},SIZE={size},מה valid,result?",
        "An8-bit variant returns modulo256 with valid=1 only for SIZE∈{{1,2,4}}; otherwise valid=0,result=0. For A={a},SIZE={size},what is valid,result?",
        "גם אפס יכול להיות פלט חשבוני חוקי. אין להסיק פסילה מערך הנתון לבדו; SIZE קובע valid.",
        "Zero can be a valid arithmetic output. Do not infer invalidity from the data value alone; SIZE determines valid.",
        [dict(a=a, size=s) for a, s in [(255, 1), (252, 4), (0, 0), (20, 3), (4, 2)]],
    )
    add(
        172,
        "bits",
        140,
        "הפרש בין ריבועים",
        "The difference between squares",
        "רקורסיה יכולה להחליף מכפל ברצף ידוע.",
        "A recurrence can replace multiplication in a known sequence.",
        "odd_delta",
        "רכיב מחזיק n={n} ו־s=n². כמה צריך להוסיף ל־s כדי לקבל (n+1)² בלי מכפל?",
        "A component holds n={n} and s=n². What must be added to s to obtain(n+1)² without multiplication?",
        "מהזהות (n+1)²=n²+2n+1 מוסיפים את המספר האי־זוגי2n+1. הצמדה של1 לימין n מייצגת את אותו ערך.",
        "The identity(n+1)²=n²+2n+1 gives the odd increment2n+1. Appending1 to n in binary encodes that value.",
        [dict(n=n) for n in [0, 1, 3, 7, 15]],
    )
    add(
        173,
        "sequential",
        140,
        "באיזה n משתמש העדכון?",
        "Which n does the update use?",
        "עדכון מצומד צריך להשתמש במצב שקדם לחזית.",
        "Coupled updates must use pre-edge state.",
        "square_next",
        "לפני חזית n={n},s=n². באותה חזית מבצעים n_next=n+1,s_next=s+2n+1. מה s_next? n בצד ימין הוא הערך הישן.",
        "Before an edge,n={n},s=n². Update n_next=n+1 and s_next=s+2n+1 together. What is s_next? Right-hand n is the old value.",
        "השימוש ב־n הישן שומר s_next=n_next². שימוש ב־n שכבר הוגדל יוסיף2 יותר מן הנדרש.",
        "Using old n preserves s_next=n_next². Using already-incremented n adds2too much.",
        [dict(n=n) for n in [0, 2, 4, 9, 15]],
    )
    add(
        174,
        "sequential",
        140,
        "עוצרים את שני המצבים יחד",
        "Stop both coupled states together",
        "תנאי סיום צריך לשמר את האינווריאנט.",
        "A terminal condition must preserve the invariant.",
        "square_terminal",
        "מונה וריבועו מתחילים ב־0,0 ומתקדמים יחד עד N={limit},שם שניהם מחזיקים. מה n,s אחרי{steps} חזיתות ללא reset?",
        "A counter and square start at0,0 and advance together until N={limit},where both hold. What is n,s after{steps}edges without reset?",
        "n=min(steps,N),ו־s=n². החזקת המונה לבדו תוך המשך צבירה הייתה מפרה את הקשר. N=0 הוא מקרה חוקי.",
        "n=min(steps,N),s=n². Holding only n while continuing accumulation would break the relation. N=0 is valid.",
        [dict(limit=n, steps=s) for n, s in [(3, 5), (0, 4), (5, 2), (2, 2), (4, 8)]],
    )
    add(
        175,
        "sequential",
        147,
        "הערכים באמצע החלפה",
        "Values midway through a swap",
        "טבלת פעולות צריכה להראות גם מצב ביניים.",
        "An operation schedule must show intermediate state.",
        "xor_swap",
        "בהחלפה על אוגרים נפרדים,X={x},Y={y}. מבצעים X←X XOR Y,אחר כך Y←X XOR Y,אחר כך X←X XOR Y,בחזיתות נפרדות. מה X,Y אחרי{edges} חזיתות?",
        "With separate registers,X={x},Y={y},perform X←X XOR Y,then Y←X XOR Y,then X←X XOR Y on separate edges. What is X,Y after{edges}edges?",
        "כל שורה משתמשת במצב החדש מן השורה הקודמת,ורק אוגר היעד נטען. ביטול XOR משחזר את שני הערכים,גם כשהם שווים.",
        "Each step uses the preceding step’s state and loads only its target. XOR cancellation recovers both originals,including equal values.",
        [dict(x=x, y=y, edges=e) for x, y, e in [(3, 5, 1), (3, 5, 2), (3, 5, 3), (7, 7, 3), (0, 9, 2)]],
    )
    add(
        176,
        "sequential",
        147,
        "האם יש מצב שבו שניהם מחזיקים?",
        "Can both registers hold?",
        "שתי הרשאות משלימות אינן הרשאת עצירה משותפת.",
        "Complementary enables are not a shared stop enable.",
        "complement_load",
        "בחזית פעילה LOAD=1 טוען Y ו־NOT LOAD טוען X. LOAD={load},ללא global enable. אילו אוגרים מורשים להיטען בחזית {edge}?",
        "At an active edge LOAD=1 loads Y and NOT LOAD loads X. LOAD={load},with no global enable. Which registers are enabled at edge{edge}?",
        "בכל LOAD בינארי בדיוק אוגר אחד מאופשר. כדי להבטיח שמירת שניהם אחרי ההחלפה צריך מנגנון עצירה נוסף שהמקור לא סיפק.",
        "For either binary LOAD exactly one register is enabled. Guaranteeing both hold after the swap needs an additional stop mechanism.",
        [dict(load=axis_value, edge=e) for axis_value, e in [(0, 1), (1, 2), (0, 3), (1, 4), (0, 5)]],
    )
    add(
        177,
        "sequential",
        152,
        "נשא של המונה השחור",
        "Carry from the black-box counter",
        "מרחיבים מונה בשעון משותף ובבדיקת הערך הישן.",
        "Extend a counter with a shared clock and old-state carry.",
        "extended_counter",
        "מונה4 ביטים ו־FF גבוה יוצרים מונה modulo32. לפני החזית המורחב הוא{initial}; הגבוה מתהפך כשהנמוך הישן15. מה הערך אחרי{edges} חזיתות?",
        "A4-bit counter and high FF form modulo32. The initial extended count is{initial}; high toggles when old low=15. What follows{edges}edges?",
        "הנמוך עוטף באותה חזית שבה הגבוה מתהפך. כולם דוגמים את המצב הישן; אין צורך להפוך פלט מונה לשעון חדש.",
        "Low wrap and high toggle occur at the same edge using old state. No counter output must become a new clock.",
        [dict(initial=i, edges=e) for i, e in [(15, 1), (31, 1), (14, 2), (0, 16), (30, 3)]],
    )
    add(
        178,
        "gates",
        110,
        "איזה ביט מכריע השוואה?",
        "Which bit decides the comparison?",
        "בהשוואה לא מסומנת,הביט השונה הגבוה ביותר מכריע.",
        "The highest differing bit decides unsigned comparison.",
        "compare_msb",
        "משווים מילים לא מסומנות בנות4 ביטים:A={a},B={b}. הביטים הנמוכים אינם רשאים לגבור על הבדל גבוה יותר. מה היחס?",
        "Compare unsigned4-bit words A={a},B={b}. Lower bits cannot override a higher differing bit. What is the relation?",
        "מתחילים מן ה־MSB. רק כל עוד הביטים שווים ממשיכים למטה; ההבדל הראשון קובע את הכיוון.",
        "Scan from the MSB; continue only while equal. The first differing bit fixes the result.",
        [dict(a=a, b=b) for a, b in [(8, 7), (7, 8), (6, 6), (10, 9), (3, 4)]],
    )
    add(
        179,
        "bits",
        151,
        "סופרים בזוגות בלי זליגת נשא",
        "Count pairs without cross-group carry",
        "מסכות יוצרות סכומים מקומיים בתוך מילה.",
        "Masks create local sums inside a word.",
        "pair_counts",
        "ל־byte x={x},מחשבים y=(x AND 85)+((x>>1) AND 85). מה ערך y? כל זוג ביטים מחזיק את מספר האחדות המקורי בו.",
        "For byte x={x},compute y=(x AND85)+((x>>1) AND85). What is y? Each bit pair stores its original one-count.",
        "85 הוא01010101. כל חיבור זוג מקבל לכל היותר2,שנכנס בשני ביטים,ולכן אינו נושא לקבוצה הבאה.",
        "85 is01010101. Each pair sums at most2,which fits two bits and cannot carry into the next group.",
        [dict(x=x) for x in [255, 170, 85, 0, 60]],
    )
    add(
        180,
        "bits",
        1,
        "רוחב פלט לספירת אחדות",
        "Output width for counting ones",
        "מספר התוצאות כולל גם את הספירה אפס.",
        "The output range includes the zero count.",
        "popcount_width",
        "סופרים אחדות ב־{inputs} כניסות ביט עצמאיות ומוציאים ספירה מדויקת. כמה ביטי פלט נדרשים לכל התוצאות0..{inputs}?",
        "Count ones in{inputs}independent input bits exactly. How many output bits cover every count0..{inputs}?",
        "יש inputs+1 תוצאות אפשריות,לכן נדרש ceil(log2(inputs+1)),ולפחות ביט אחד בחוזה הזה. אין צורך בביט פלט לכל כניסה.",
        "There are inputs+1 possible counts,requiring ceil(log2(inputs+1)),with at least one bit in this contract. One output bit per input is unnecessary.",
        [dict(inputs=n) for n in [5, 8, 7, 1, 16]],
    )
    add(
        181,
        "bits",
        100,
        "ביט שנקבע בלי לחשב",
        "A result bit fixed without calculation",
        "גורם קבוע יכול לכפות ביטי פלט.",
        "A constant factor can force result bits.",
        "times_six_low",
        "רכיב מחשב6x בדיוק עבור x={x} ללא סימן. מהו ביט0 של התוצאה,לפני תכנון רשת המחברים?",
        "A component computes exact6x for unsigned x={x}. What is output bit0 before designing its adder network?",
        "6x=2·(3x) תמיד זוגי,ולכן ביט0 תמיד0. ההזזה הקבועה יכולה להיות חיווט ולא מחבר נוסף.",
        "6x=2·(3x) is always even,so bit0 is always0. A fixed shift can be wiring rather than another adder.",
        [dict(x=x) for x in [0, 1, 7, 128, 255]],
    )
    add(
        182,
        "gates",
        122,
        "שני נשאים שלא יכולים להופיע יחד",
        "Two carries that cannot coexist",
        "בלעדיות מאפשרת להחליף OR ב־XOR במקום המסוים.",
        "Mutual exclusion can make OR and XOR equivalent locally.",
        "ha_carry_pair",
        "בבניית FA משני HA,C1=A AND B ו־C2=(A XOR B) AND Cin. עבור A={a},B={b},Cin={cin},מה C1,C2?",
        "In a full-adder decomposition,C1=A AND B and C2=(A XOR B) AND Cin. For A={a},B={b},Cin={cin},what is C1,C2?",
        "כאשר C1=1 אז A=B=1 ולכן A XOR B=0 ו־C2=0. אין מצב11,ולכן OR ו־XOR של שני הנשאים זהים כאן בלבד.",
        "C1=1 implies A=B=1,forcing A XOR B=0 and C2=0. Pair11 is impossible,so OR and XOR agree for these carries.",
        [dict(a=a, b=b, cin=c) for a, b, c in [(1, 1, 1), (1, 0, 1), (0, 1, 0), (0, 0, 1), (1, 1, 0)]],
    )
    add(
        183,
        "bits",
        134,
        "כפל קבוע מתוך חיבורים",
        "Constant multiplication from wiring",
        "פירוק הקבוע מאפשר לשתף מבנה חשבוני.",
        "Decomposing a constant exposes arithmetic structure.",
        "times_thirteen",
        "מחשבים13x כ־(x<<3)+(x<<2)+x בחשבון מדויק. עבור x={x},מה התוצאה? הזזות קבועות מותרות כחיווט.",
        "Compute exact13x as(x<<3)+(x<<2)+x. For x={x},what is the result? Fixed shifts may be wiring.",
        "13=8+4+1,ולכן החיבור שקול לכפל. יש להרחיב לפני הזזות וחיבורים; הרחבה אחרי חיתוך אינה משחזרת ביטים.",
        "13=8+4+1,so the sum equals multiplication. Widen before shifts/addition; widening a truncated result cannot restore bits.",
        [dict(x=x) for x in [0, 1, 3, 15, 255]],
    )
    add(
        184,
        "gates",
        174,
        "עמודת הביט של ארבע",
        "The weight-four column",
        "טבלת אמת קטנה יכולה לבטל צורך במכפל כללי.",
        "A small truth table can eliminate a general multiplier.",
        "square_bit2",
        "X בן2 ביטים ללא סימן,וערכו{x}. מה ביט המשקל4 בתוצאה המדויקת X²?",
        "Unsigned2-bit X has value{x}. What is the weight4 bit of exact X²?",
        "הריבועים הם0,1,4,9. ביט המשקל4 דולק רק בקלט10,ולכן y2=a AND NOT b עבור X=(a,b).",
        "Squares are0,1,4,9. Weight4 is set only for input10,so y2=a AND NOT b for X=(a,b).",
        [dict(x=x, case=i) for i, x in enumerate([0, 1, 2, 3, 2])],
    )
    add(
        185,
        "bits",
        174,
        "ריבוע תלוי בפירוש הקלט",
        "Squaring depends on input interpretation",
        "לפני שימוש בטבלה קובעים signedness.",
        "Specify signedness before choosing a truth table.",
        "signed_square",
        "התבנית בת2 הביטים היא הערך העשרוני{bits},ומפורשת במשלים לשתיים. מה הריבוע המתמטי המדויק שלה? זהו פירוש חתום,לא unsigned.",
        "A2-bit pattern has unsigned code{bits}but is interpreted as two’s complement. What is its exact mathematical square? This is signed,not unsigned.",
        "הקודים0,1,2,3 מייצגים0,1,−2,−1. הריבועים הם0,1,4,1,שלא כמו טבלת unsigned בשורה11.",
        "Codes0,1,2,3 denote0,1,−2,−1. Their squares are0,1,4,1,unlike the unsigned table at11.",
        [dict(bits=b, case=i) for i, b in enumerate([3, 2, 1, 0, 3])],
    )
    add(
        186,
        "states",
        171,
        "בודקים את הרצף שנסגר",
        "Check the run that just closed",
        "אירוע סגירה שונה מבדיקת כל קידומת זמנית.",
        "A closing event differs from testing each temporary prefix.",
        "run_error",
        "רצף של הביט{bit} באורך{length} נסגר עכשיו בביט הנגדי. שגיאה היא אפסים באורך זוגי או אחדות באורך אי־זוגי. מה אירוע השגיאה0/1?",
        "A run of bit{bit},length{length},is now closed by the opposite bit. Errors are even zero runs or odd one runs. What is the0/1 error event?",
        "בודקים את סוג הרצף הישן ואת זוגיות אורכו,ואז מתחילים רצף חדש באורך1. לא בודקים את זוגיות הרצף החדש במקום הישן.",
        "Check old run type and length parity,then start a new length1 run. Do not substitute the new run’s parity.",
        [dict(bit=b, length=n) for b, n in [(0, 4), (1, 5), (0, 5), (1, 2), (0, 1)]],
    )
    add(
        187,
        "states",
        171,
        "מצב מדומה שמייצג התחלה ריקה",
        "A virtual state representing empty history",
        "מצבים שקולים נקבעים לפי התנהגות עתידית.",
        "State equivalence is determined by future behavior.",
        "run_reset",
        "בגלאי רצפים,reset משתמש ב־OE:אחדות באורך זוגי,השקול להיסטוריה ריקה. הביט הראשון הוא{first}. איזה מצב היסטוריה מתקבל ללא אירוע שגיאה? Z/O=סוג,E/O=זוגי/אי־זוגי.",
        "The run detector resets to OE:even ones,equivalent to empty history. First bit is{first}. Which history state follows without an error? Z/O=bit type,E/O=even/odd.",
        "ביט ראשון יוצר רצף באורך1:אפס עובר ל־ZO ואחד ל־OO. הרצף המדומה באורך0 אינו מדווח כשגיאה.",
        "The first bit starts a length1 run:zero enters ZO,one enters OO. The virtual length0 history causes no error.",
        [dict(first=b, case=i) for i, b in enumerate([0, 1, 0, 1, 1])],
    )
    add(
        188,
        "states",
        173,
        "כישלון חלקי אינו מחיקה מלאה",
        "A partial mismatch need not clear everything",
        "שומרים סיומת שהיא עדיין קידומת של היעד.",
        "Retain a suffix that is still a target prefix.",
        "prefix_fallback",
        "גלאי1011 קלט עד כה את ההיסטוריה{history}. מה אורך הקידומת הארוכה ביותר מבין ריקה,1,10,101 שהיא גם סיומת ההיסטוריה?",
        "A1011detector has read history{history}. What is the longest suffix length among target prefixes empty,1,10,101?",
        "משווים סיומות לקידומות היעד. למשל1010 שומר10 ולא מאפס הכול; כך לא מאבדים התחלה שכבר הגיעה.",
        "Match suffixes to target prefixes. For example,1010 keeps10 rather than clearing everything,retaining progress already received.",
        [dict(history=w) for w in ["1010", "1011", "100", "111", "0101"]],
    )
    add(
        189,
        "states",
        50,
        "שארית מנורמלת לקלט מהסוף",
        "Normalized remainder for LSB-first input",
        "קידוד מצב מתאים יכול לספוג את מופע המשקל.",
        "A suitable state encoding can absorb weight phase.",
        "lsb_five",
        "בגלאי חלוקה ב־5 לקלט LSB-first,המצב מוגדר r=V·2^(-k) mod5 אחרי k ביטים. כעת r={state},והביט הבא{bit}. מה r_next=3(r+bit) mod5?",
        "For LSB-first divisibility by5,state r=V·2^(-k) mod5 after k bits. Now r={state},next bit{bit}. What is r_next=3(r+bit) mod5?",
        "3 הוא ההופכי של2 modulo5. הכפלה בו מנרמלת את המשקל אחרי הוספת הביט,בלי לטעון ש־r הוא השארית המספרית הישירה.",
        "3 is the inverse of2 modulo5. It normalizes the next weight after adding the bit;r is not the direct numeric remainder.",
        [dict(state=r, bit=b) for r, b in [(0, 1), (3, 0), (2, 1), (4, 1), (1, 0)]],
    )
    add(
        190,
        "states",
        45,
        "הראשון נשאר הראשון",
        "The first stays first",
        "שמירת זוכה מחייבת חסימת כתיבות מאוחרות.",
        "Retaining a winner requires blocking later writes.",
        "winner",
        "אוגר זוכה מתחיל ריק. בכל צעד מגיע לכל היותר מסיים אחד; - פירושו אין מסיים. הרצף הוא{trace}. מי צריך להישאר שמור?",
        "A winner register starts empty. At most one finisher arrives per step;- means none. The sequence is{trace}. Who must remain stored?",
        "טוענים רק כשהאוגר ריק ויש אירוע. לאחר הזכייה מתעלמים ממסיימים מאוחרים עד reset; זה אינו מנגנון העדיפות האחרון.",
        "Load only while empty and an event arrives. Ignore later finishers until reset; this is not last-arrival priority.",
        [dict(arrivals=list(w), trace=",".join(w)) for w in ["-AB", "BCA", "--C", "---", "C-A"]],
    )
    add(
        191,
        "states",
        53,
        "גלאי נוכחות אינו גלאי כיוון",
        "Presence is not direction",
        "האלגוריתם מוגבל למידע שהחיישן באמת חושף.",
        "An algorithm is limited by its actual observations.",
        "one_sensor",
        "גלאי יחיד מחזיר רק חסום/פנוי,ואדם יכול לעבור בשני הכיוונים. נצפה0,1,0 עם זמן חסימה{duration}. הכיוון לא משפיע על הרגישות. מה אפשר להסיק על הכיוון?",
        "One sensor reports blocked/clear only; people may move either way. Its trace is0,1,0 with blocked duration{duration}. Sensitivity is direction-independent. What can be inferred about direction?",
        "אותה תנועה הפוכה יכולה ליצור בדיוק אותה תצפית וזמן חסימה. ללא מידע נוסף אין הכרעה בין כניסה ליציאה.",
        "Reversing the passage can produce the identical trace and duration. Without more information,entry and exit are indistinguishable.",
        [dict(duration=t) for t in ["1s", "2s", "0.5s", "3s", "4s"]],
    )
    add(
        192,
        "states",
        53,
        "נסיגה אינה כניסה",
        "A retreat is not an entry",
        "סופרים מעבר מלא ולא רק הפעלת החיישן הראשון.",
        "Count a complete passage,not just first-sensor activation.",
        "door_retreat",
        "שני גלאים מסודרים,אדם יחיד וללא דגימות חסרות. נתיב החסימות הוא{trace},ומסתיים באותו צד שממנו התחיל. מה שינוי ספירת האנשים בפנים?",
        "Two ordered sensors,one person,no missed samples:trace{trace}ends on the starting side. What is the net occupancy change?",
        "האדם התקרב ונסוג בלי להשלים מעבר. שינוי הספירה0; עדכון על החסימה הראשונה היה יוצר ספירת שווא.",
        "The person approached and retreated without a completed passage. Net change is0; counting first activation creates a false entry.",
        [dict(trace=t) for t in ["00,10,00", "00,01,00", "00,10,11,10,00", "00,01,11,01,00", "00,10,10,00"]],
    )
    add(
        193,
        "sequential",
        104,
        "תצפית אינה אבחנת סיבה",
        "An observation is not a root-cause proof",
        "מאבחנים תזמון בעזרת נתיב,שעון וראיות נוספות.",
        "Timing diagnosis needs path,clock and additional evidence.",
        "pipeline_diagnosis",
        "צינור אמור להציג שינוי אחרי3 חזיתות,אך נצפה אחרי{observed}. אין נתוני נתיב,reset,חזית קלט או skew. מה ניתן להסיק על סוג התקלה?",
        "A pipeline should change after3edges,but changes after{observed}. Path,reset,input-edge and skew data are missing. What can be inferred about the fault type?",
        "ספירת חזיתות לבדה אינה מוכיחה setup או hold. צריך לבדוק את ההגדרה והשעונים,תנאי ההתחלה והגעת הנתונים.",
        "Edge count alone does not prove setup or hold. Inspect the contract,clocks,initial conditions and arrivals.",
        [dict(observed=n, case=i) for i, n in enumerate([2, 4, 1, 5, 3])],
    )
    add(
        194,
        "gates",
        112,
        "הבועה נמצאת בכניסה",
        "The bubble is on the input",
        "מיקום ההיפוך משנה את הפונקציה.",
        "The location of inversion changes the function.",
        "bubble_input",
        "לשער AND יש בועה רק בכניסת B. עבור A={a},B={b},מה הפלט? זה אינו NAND בעל בועה ביציאה.",
        "An AND gate has a bubble only on input B. For A={a},B={b},what is output? This is not NAND with an output bubble.",
        "הפונקציה A AND NOT B. NAND היה NOT(A AND B),ולכן אסור להזיז בועה בלי שינוי מתאים בשערים.",
        "The function is A AND NOT B. NAND is NOT(A AND B); moving a bubble requires the corresponding logic transformation.",
        [dict(a=a, b=b, case=i) for i, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (1, 0)])],
    )
    add(
        195,
        "bits",
        119,
        "מסכה להחלפת שני ערכים מובטחים",
        "A mask for two promised values",
        "טריק חוקי בתחום מובטח אינו מפרט לכל מספר.",
        "A trick on a promised domain is not a specification for every number.",
        "promise_mask",
        "הקלט מובטח להיות רק{a} או{b}. רוצים להחליף ביניהם באמצעות x XOR mask. איזו mask פועלת בשני הכיוונים?",
        "Input is promised to be only{a}or{b}. Swap these values using x XOR mask. Which mask works in both directions?",
        "mask=a XOR b. ביטול XOR מחזיר את הערך השני. אין כאן התחייבות למיפוי רצוי עבור מספרים מחוץ להבטחה.",
        "mask=a XOR b. XOR cancellation maps each promised value to the other. Inputs outside the promise have no additional required mapping.",
        [dict(a=a, b=b) for a, b in [(9, 13), (4, 7), (0, 8), (3, 12), (5, 10)]],
    )
    add(
        196,
        "sequential",
        118,
        "בתוך רצועת ההיסטרזיס",
        "Inside the hysteresis band",
        "שני ספים יוצרים תלות מכוונת בהיסטוריה.",
        "Two thresholds intentionally introduce history dependence.",
        "hysteresis",
        "משווה היסטרזיס עולה ל־1 ב־Vin≥{high}V ויורד ל־0 ב־Vin≤{low}V. באמצע הוא מחזיק. היה פלט{previous},ועכשיו Vin={vin}V. מה הפלט?",
        "A hysteretic comparator sets1at Vin≥{high}V and0at Vin≤{low}V; between thresholds it holds. Previous output={previous},now Vin={vin}V. What is output?",
        "בתוך הרצועה שומרים את הפלט הקודם; מחוצה לה הסף המתאים קובע. אי אפשר לתאר את כל ההתנהגות בטבלת Vin חד־ערכית ללא מצב.",
        "Inside the band retain previous output; outside,the relevant threshold decides. Vin alone cannot describe the full behavior without state.",
        [
            dict(low=axis_value, high=h, previous=p, vin=v)
            for axis_value, h, p, v in [
                (1, 2, 0, 1.5),
                (1, 2, 1, 1.5),
                (1, 2, 0, 2),
                (1, 2, 1, 1),
                (0.5, 2.5, 0, 3),
            ]
        ],
    )
    add(
        197,
        "gates",
        118,
        "מתח ביניים אינו חצי ביט",
        "An intermediate voltage is not half a bit",
        "רמות לוגיות מובטחות דורשות גבולות מתח.",
        "Guaranteed logic levels require voltage bounds.",
        "threshold_gap",
        "כניסה מבטיחה0 כאשר Vin≤VIL={vil}V ו־1 כאשר Vin≥VIH={vih}V. כעת Vin={vin}V. מה מובטח?",
        "An input guarantees0for Vin≤VIL={vil}V and1for Vin≥VIH={vih}V. Now Vin={vin}V. What is guaranteed?",
        "בתחום שבין VIL ל־VIH אין ערך לוגי מובטח. זה אינו ערך נתון של0.5,וסף אמיתי עשוי להשתנות עם תנאים.",
        "Between VIL and VIH no logic value is guaranteed. This is not a data value of0.5,and actual thresholds vary with conditions.",
        [
            dict(vil=axis_value, vih=h, vin=v)
            for axis_value, h, v in [(0.8, 2, 1.2), (0.8, 2, 0.8), (0.8, 2, 2), (1, 3, 0), (1, 3, 4)]
        ],
    )
    add(
        198,
        "gates",
        160,
        "משווה בלוקים במקום מספר בודד",
        "Compare-split whole blocks",
        "בלוק מיון יכול להפריד חצי נמוך וחצי גבוה.",
        "A sorter can split blocks into lower and upper halves.",
        "compare_split",
        "שני בלוקים שווי אורך הם{left} ו־{right}. פעולת compare-split ממיינת את האיחוד ומחזירה לבלוק הראשון את החצי הנמוך. מה נשאר בו?",
        "Equal-length blocks are{left}and{right}. Compare-split sorts their union and returns the lower half to the first block. What remains there?",
        "ממיינים את כל ההופעות ושומרים את החצי הנמוך,כולל כפילויות. אין די בהשוואת איבר יחיד או במקסימום של כל בלוק.",
        "Sort all occurrences and retain the lower half,including duplicates. One scalar comparison or block maximum is insufficient.",
        [
            dict(left=a, right=b)
            for a, b in [
                ([1, 9], [2, 8]),
                ([4, 4], [1, 4]),
                ([0, 2], [3, 5]),
                ([-2, 7], [-1, 0]),
                ([9, 10], [1, 2]),
            ]
        ],
    )
    add(
        199,
        "gates",
        160,
        "סף שחושף היפוך סדר",
        "A threshold exposing an inversion",
        "הוכחת מיון יכולה לצמצם שגיאה מספרית למקרה בינארי.",
        "A sorting proof can reduce a numeric inversion to a binary one.",
        "threshold_witness",
        "בפלט מופיע{high} לפני{low},כאשר הראשון גדול יותר. רוצים סף θ כך שערך קטן מ־θ יהפוך0 ואחרת1,והזוג יהפוך1,0. איזה θ באמצע מתאים?",
        "Output places{high}before{low},with the first larger. Map values below θ to0and others to1. Which midpoint θ makes this pair1,0?",
        "כל סף בין הערכים מפריד אותם. מיון וסיווג סף מתחלפים,לכן רשת שגויה בסדר מספרי חושפת גם כשל בינארי.",
        "A threshold between the values separates them. Sorting commutes with threshold classification,so a numeric inversion exposes a binary failure.",
        [dict(low=axis_value, high=h) for axis_value, h in [(2, 8), (-4, 2), (1, 2), (0, 10), (5, 9)]],
    )
    add(
        200,
        "gates",
        160,
        "אינסוף מומצא עלול למחוק מידע",
        "A guessed infinity can erase data",
        "ריפוד צריך להיות גדול בהגדרה,לא רק בדוגמה.",
        "Padding must be greater by definition,not only in an example.",
        "padding_failure",
        "מרפדים רשימת אמת{real} בערך sentinel={sentinel},ממיינים ועורכים חיתוך לאורך המקורי. מה הפלט בפועל? אין תג שמבדיל ריפוד מנתון.",
        "Pad real data{real}with sentinel={sentinel},sort,and keep the original length. What output actually remains? No tag separates padding from real data.",
        "אם sentinel קטן מנתון אמיתי הוא נכנס לפלט ודוחק מידע. תג ריפוד שמדורג מעל כל נתון פותר זאת בלי לנחש גבול מספרי.",
        "A sentinel smaller than real data enters the output and displaces it. A padding tag ordered above all real data avoids guessing a numeric bound.",
        [
            dict(real=a, sentinel=s)
            for a, s in [([1, 200], 100), ([-1, 2], 0), ([3, 4], 99), ([7, 8], 7), ([0, 1], -1)]
        ],
    )


def refinements():
    by_id = {s["number"]: s for s in SPECS}
    for n, s in by_id.items():
        if n in set(range(126, 146)) | set(range(150, 158)) | {196, 197}:
            s["topic"] = "electronics"
    by_id[141]["prompt"]["en"] = by_id[141]["prompt"]["en"].replace(
        "zero inductor current", "0 inductor current"
    )
    by_id[127]["cases"][4]["c"] = 0.01
    by_id[131]["cases"][4]["decay"] = 0.125
    by_id[156]["explanation"]["en"] = by_id[156]["explanation"]["en"].replace(
        "Merely exceeding twice bandwidth", "The condition fs>2·bandwidth alone"
    )
    by_id[162]["explanation"]["en"] = by_id[162]["explanation"]["en"].replace("Zero means", "0 means")
    by_id[158]["explanation"] = loc(
        "כל אחד מביטי המידע יכול להפוך זוגיות,ולכן נותרים n מיקומים אפשריים. כש־n>1 אין איתור יחיד; n=1 הוא החריג הטריוויאלי.",
        "Every data-bit flip changes parity,leaving n possible positions. For n>1 there is no unique location;n=1 is the trivial exception.",
    )
    for lang in ("he", "en"):
        by_id[140]["explanation"][lang] = (
            by_id[140]["explanation"][lang]
            .replace("LI²/2=CV0²/2", "L·I²/2=C·V₀²/2")
            .replace("I=V0√", "I=V₀√")
        )
        by_id[180]["explanation"][lang] = by_id[180]["explanation"][lang].replace("log2(", "log₂(")
    s = by_id[154]
    s["prompt"] = loc(
        "דוגמים x(t)=sin(2π·{frequency}t+φ),ב־fs=2·{frequency} וב־φ={phase}π. מה ארבע הדגימות עבור n=0,1,2,3?",
        "Sample x(t)=sin(2π·{frequency}t+φ) at fs=2·{frequency},with φ={phase}π. What are samples n=0,1,2,3?",
    )
    s["explanation"] = loc(
        "בגבול הזה הדגימות הן sin(πn+φ). כאשר φ=0 הן כולן0 אף שהאות אינו אפס; שינוי מופע משנה את הסדרה אך אינו מבטיח שחזור כל מופע.",
        "At this boundary samples are sin(πn+φ). For φ=0 all are0 despite a nonzero signal; other phases change the sequence without guaranteeing every-phase reconstruction.",
    )
    for p, phase in zip(s["cases"], [0, 0.5, 1, -0.5, 0], strict=True):
        p["phase"] = phase
    s = by_id[166]
    s["cases"][3]["he"] = (
        "ב־ISSUE היו3 מחזורי stall. בחזית הבאה הפקודה מתקבלת וגם מסתיימת; done חוזר0 במחזור הבא. לאיזה מצב חייבים לעבור כדי לשמר את התגובה?"
    )
    s["cases"][3]["en"] = (
        "ISSUE stalls for3cycles,then the command is accepted and completed at one edge; done returns0next cycle. Which state retains that response?"
    )
    s["cases"][4].update(accepted=0, done=0)
    s["cases"][4]["he"] = (
        "ב־ISSUE הפקודה לא התקבלה במשך4 חזיתות,ולא הייתה השלמה. באיזה מצב חייבים להמשיך להציג את הפקודה היציבה?"
    )
    s["cases"][4]["en"] = (
        "In ISSUE,the command is unaccepted for4edges and no completion occurs. Which state must keep presenting the stable command?"
    )
    s = by_id[184]
    s["cases"][4].update(inverse=True)
    s["cases"][4]["he"] = "ל־X ללא סימן בן2 ביטים,ביט המשקל4 של X² הוא1. איזה X יחיד מתוך0..3 מתאים?"
    s["cases"][4]["en"] = "For unsigned2-bit X,the weight4bit of X² is1. Which single X in0..3 fits?"
    s = by_id[185]
    s["cases"][4].update(difference=True)
    s["cases"][4]["he"] = (
        "לתבנית11,מה ההפרש בין הריבוע בפירוש unsigned לבין הריבוע בפירוש signed במשלים לשתיים?"
    )
    s["cases"][4]["en"] = "For pattern11,what is unsigned-square minus two’s-complement signed-square?"
    for p, old in zip(by_id[187]["cases"], ["OO", "ZE", "ZO", "OE", "OO"], strict=True):
        p["old"] = old
        p["he"] = (
            "ZO/ZE הם רצף אפסים אי־זוגי/זוגי; OO/OE הם רצף אחדות אי־זוגי/זוגי. הגלאי היה ב־{old},אך reset קובע OE השקול להיסטוריה ריקה. הביט הראשון אחריו{first}. מה המצב החדש ללא שגיאה?"
        )
        p["en"] = (
            "ZO/ZE mean odd/even zero runs; OO/OE mean odd/even one runs. Before reset,state={old}; reset sets OE,equivalent to empty history. First subsequent bit={first}. What history state follows without error?"
        )
    s = by_id[194]
    s["cases"][4].update(inverse=True)
    s["cases"][4]["he"] = "לשער AND עם בועה רק בכניסת B,נמדדו A=1 ופלט1. איזה B מתאים?"
    s["cases"][4]["en"] = "An AND with a bubble only on input B has A=1 and output1. Which B fits?"


def source_model(stem):
    path = ROOT / "interview_preparation/solutions" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def close(actual, expected):
    if isinstance(actual, (tuple, list)):
        return (
            isinstance(expected, (tuple, list))
            and len(actual) == len(expected)
            and all(close(a, b) for a, b in zip(actual, expected, strict=True))
        )
    if isinstance(actual, (float, int)) and isinstance(expected, (float, int)):
        return math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)
    return actual == expected


def verify(method, p, value):
    """Independent replay: charge/KCL,absolute clocks,codewords or full history.

    Conceptual cases are checked in their explicitly chosen teaching model.
    They do not claim transistor measurements or analog signoff.
    """
    expected = None
    match method:
        case "rc_ambiguity":
            assert close(p["r"] * value, p["tau"])
            assert close(1 - math.exp(-p["tau"] / (p["r"] * value)), 1 - math.exp(-1))
            return
        case "rc_half":
            if not p["c"]:
                expected = 0
            else:
                lo, hi = 0, 10 * p["r"] * p["c"]
                for _ in range(70):
                    mid = (lo + hi) / 2
                    if 1 - math.exp(-mid / (p["r"] * p["c"])) < 0.5:
                        lo = mid
                    else:
                        hi = mid
                expected = (lo + hi) / 2
        case "cap_jump":
            assert close(value - p["after_b"], p["before"] - p["before_b"])
            return
        case "cap_dc":
            assert close((p["vdd"] - value) / 13, 0)
            return
        case "overshoot":
            assert close(value - p["jump"], p["before"])
            return
        case "cap_history":
            # Independently integrate dv/dt=VDD-v over the relaxation segment.
            if not p["decay"]:
                v = p["vdd"]
            else:
                v = p["start"]
                dt = -math.log(p["decay"]) / 1000
                for _ in range(1000):
                    k1 = p["vdd"] - v
                    k2 = p["vdd"] - (v + dt * k1 / 2)
                    k3 = p["vdd"] - (v + dt * k2 / 2)
                    k4 = p["vdd"] - (v + dt * k3)
                    v += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            expected = v + p["jump"]
        case "gate_charge":
            # Sum one thousand equal charge increments along a prescribed ramp.
            expected = sum(p["c"] * (p["dv"] / 1000) for _ in range(1000))
        case "doping":
            initial_atoms = 100
            after_atoms = initial_atoms + (7 if p["operation"] == "implant" else 0)
            expected = "permanent" if after_atoms != initial_atoms else "reversible"
        case "mos_on":
            inversion_strength = max(0, p["vg"] - p["vs"] - p["vt"]) ** 2
            expected = "on" if inversion_strength > 0 else "off"
        case "mos_region":
            over = p["vgs"] - p["vt"]
            # Positive channel at source but no inversion at drain defines pinch-off.
            source_inverted = over > 0
            drain_inverted = p["vgs"] - p["vds"] > p["vt"]
            expected = "off" if not source_inverted else "linear" if drain_inverted else "saturation"
        case "mos_square":
            base = 0.37 * (2.1 - 0.6) ** 2
            altered = 0.37 * ((2.1 - 0.6) * p["factor"]) ** 2
            expected = altered / base
        case "nmos_high":
            lo, hi = 0.0, p["vdd"]
            for _ in range(80):
                mid = (lo + hi) / 2
                if p["vdd"] - mid > p["vt"]:
                    lo = mid
                else:
                    hi = mid
            expected = (lo + hi) / 2
        case "static_current":
            assert close(p["vdd"] - value * p["pullup"], value * p["pulldown"])
            return
        case "lc_initial":
            expected = source_model("prep_170_switched_ideal_lc").response(0, 2, 3, p["v0"])
        case "lc_quarter":
            expected = source_model("prep_170_switched_ideal_lc").response(
                math.pi / 2 * math.sqrt(p["l"] * p["c"]), p["l"], p["c"], p["v0"]
            )[1]
        case "lc_half":
            expected = source_model("prep_170_switched_ideal_lc").response(math.pi, 1, 1, p["v0"])[0]
        case "lc_period_ratio":
            # Verify a full revolution of the independently defined state oscillator.
            omega = 1 / math.sqrt(p["l_ratio"] * p["c_ratio"])
            assert close(omega * 2 * math.pi * value, 2 * math.pi)
            return
        case "buffer_delay":
            expected = source_model("prep_175_buffer_load_model").compare_paths(
                p["rs"], p["cl"], p["cin"], p["rb"], p["tb"]
            )[1]
        case "buffer_breakeven":
            model_ref = source_model("prep_175_buffer_load_model")
            direct, buffered = model_ref.compare_paths(p["rs"], value, p["cin"], p["rb"], p["tb"])
            assert close(direct, buffered)
            d, b = model_ref.compare_paths(p["rs"], 2 * value, p["cin"], p["rb"], p["tb"])
            assert d > b
            d, b = model_ref.compare_paths(p["rs"], value / 2, p["cin"], p["rb"], p["tb"])
            assert d < b
            return
        case "led_resistor":
            assert close(p["current"] * value + p["vf"] + p["vd"], p["vs"])
            return
        case "skew_effect" | "uncertainty" | "speedup":
            ref = source_model("prep_176_setup_hold_budgets")
            base = ref.timing_slacks(10, 1, 2, 1, 3, 0.5, 0.5)
            if method == "skew_effect":
                new = ref.timing_slacks(10, 1, 2, 1, 3, 0.5, 0.5, p["s"])
            elif method == "uncertainty":
                new = ref.timing_slacks(10, 1, 2, 1, 3, 0.5, 0.5, 0, p["us"], p["uh"])
            else:
                new = ref.timing_slacks(10, 1, 2, 1 - p["dmin_reduction"], 3 - p["dmax_reduction"], 0.5, 0.5)
            expected = tuple(n - b for n, b in zip(new, base, strict=True))
        case "timing_exception":
            # Permitted data can settle just before its first required capture.
            worst_allowed_arrival = p["functional_cycles"] - 0.01
            tool_deadline = p["constraint_cycles"]
            expected = "invalid" if tool_deadline > worst_allowed_arrival + 1 else "valid"
            # Equivalent check via permitted capture edge enumeration.
            assert (expected == "valid") == all(
                edge >= p["constraint_cycles"]
                for edge in range(p["functional_cycles"], p["functional_cycles"] + 3)
            )
        case "coupling_ceff":
            dv = 0.8
            da = p["ratio"] * dv
            expected = (p["cg"] * dv + p["cc"] * (dv - da)) / dv
        case "quiet_noise":
            assert close(p["cg"] * value + p["cc"] * (value - p["da"]), 0)
            return
        case "window_overlap":
            expected = sum(
                p["v0"] < t + 0.5 < p["v1"] and p["a0"] < t + 0.5 < p["a1"] for t in range(-10, 20)
            )
        case "shield_delta":
            before = p["old_cg"] * 0.8 + p["old_cc"] * (0.8 - (-0.8))
            after = p["new_cg"] * 0.8 + p["new_cc"] * (0.8 - (-0.8))
            expected = (after - before) / 0.8
        case "nyquist_phase":
            amplitude = math.sin(p["phase"] * math.pi)
            expected = tuple(round(amplitude * ((-1) ** n)) for n in range(4))
        case "alias":
            for n in range(8):
                assert close(
                    math.cos(2 * math.pi * p["frequency"] * n / p["fs"]),
                    math.cos(2 * math.pi * value * n / p["fs"]),
                )
            assert 0 <= value <= p["fs"] / 2
            return
        case "band_interval":
            lo, hi = value
            assert close(p["m"] * lo, 2 * p["fh"]) and close((p["m"] - 1) * hi, 2 * p["fl"])
            assert spectral_disjoint(p["fl"], p["fh"], (lo + hi) / 2)
            return
        case "band_margin":
            expected = "safe" if spectral_disjoint(p["fl"], p["fh"], p["fs"]) else "unsafe"
        case "parity_locations":
            originals = []
            for position in range(p["n"]):
                original = [0] * p["n"]
                original[position] = 1
                assert sum(original) % 2 == 1
                corrupted = original.copy()
                corrupted[position] ^= 1
                assert not any(corrupted)
                originals.append(tuple(original))
            expected = len(set(originals))
        case "hamming_bits":
            assert 2**value >= 1 + p["data"] + value
            assert all(2**r < 1 + p["data"] + r for r in range(value))
            return
        case "syndrome":
            checks = [int(bool(p["position"] & mask)) for mask in (1, 2, 4, 8)]
            expected = int("".join(str(x) for x in reversed(checks)), 2)
        case "secded":
            possibilities = set()
            for count in range(3):
                for fault in itertools.combinations(range(1, 14), count):
                    s = 0
                    for bit in fault:
                        if bit != 13:
                            s ^= bit
                    if s == p["syndrome"] and count % 2 == p["parity"]:
                        possibilities.add(
                            "none"
                            if count == 0
                            else "double"
                            if count == 2
                            else "overall"
                            if fault == (13,)
                            else "single"
                        )
            assert len(possibilities) == 1
            expected = possibilities.pop()
        case "short_syndrome":
            candidates = [j for j in range(13) if j == p["syndrome"]]
            expected = "reject" if not candidates else "clean" if candidates == [0] else "correct"
        case "queue_overflow":
            used = lost = 0
            for _ in range(p["arrivals"]):
                if used == p["capacity"]:
                    lost += 1
                else:
                    used += 1
            expected = lost
        case "commit_ack":
            memory = 0
            read = None
            for tick in range(max(p["visible"], p["read_issue"]) + 1):
                if tick == p["visible"]:
                    memory = 1
                if tick == p["read_issue"]:
                    read = memory
            expected = "safe" if read == 1 else "stale_possible"
        case "wait_evidence":
            busy = [tick < p["actual_latency"] for tick in range(max(p["wait"], p["actual_latency"]) + 1)]
            expected = "premature" if busy[p["wait"]] else "safe"
        case "immediate_completion":
            outstanding = int(bool(p["accepted"])) - int(bool(p["done"]))
            expected = "ISSUE" if not p["accepted"] else "WAIT" if outstanding else "RESP"
        case "round_robin":
            pending = ["R", "W"] if p["first"] == 0 else ["W", "R"]
            trace = []
            for _ in range(p["n"]):
                winner = pending.pop(0)
                trace.append(winner)
                pending.append(winner)
            expected = ", ".join(trace)
        case "serialized_issue":
            state = "RESP"
            accepted = []
            for edge in range(p["previous_response_consumed"] + 2):
                if state == "IDLE":
                    accepted.append(edge)
                if edge == p["previous_response_consumed"]:
                    state = "IDLE"
            expected = accepted[0]
        case "size_low":
            expected = (p["a"] + p["size"]) & (p["size"] - 1)
        case "size_carry":
            carry = 0
            for j in range(8):
                carry = (((p["a"] >> j) & 1) + ((p["size"] >> j) & 1) + carry) // 2
            expected = carry
        case "size_valid":
            valid = p["size"] in (1, 2, 4)
            expected = (int(valid), sum([p["a"], p["size"]]) & 255 if valid else 0)
        case "odd_delta":
            expected = (p["n"] + 1) ** 2 - p["n"] ** 2
        case "square_next":
            expected = (p["n"] + 1) ** 2
        case "square_terminal":
            n = 0
            s = 0
            for _ in range(p["steps"]):
                if n < p["limit"]:
                    n += 1
                    s = n * n
            expected = (n, s)
        case "xor_swap":
            x, y = p["x"], p["y"]
            expected = {1: (x ^ y, y), 2: (x ^ y, x), 3: (y, x)}[p["edges"]]
        case "complement_load":
            enables = {"X": 1 - p["load"], "Y": p["load"]}
            expected = next(name for name, on in enables.items() if on)
            assert sum(enables.values()) == 1
        case "extended_counter":
            high = p["initial"] // 16
            low = p["initial"] % 16
            for _ in range(p["edges"]):
                if low == 15:
                    high = 1 - high
                low = (low + 1) & 15
            expected = 16 * high + low
        case "compare_msb":
            expected = "equal"
            for a, b in zip(f"{p['a']:04b}", f"{p['b']:04b}", strict=True):
                if a != b:
                    expected = "greater" if a == "1" else "less"
                    break
        case "pair_counts":
            groups = [sum(int(x) for x in f"{p['x']:08b}"[i : i + 2]) for i in range(0, 8, 2)]
            expected = int("".join(f"{x:02b}" for x in groups), 2)
        case "popcount_width":
            assert all(count < 2**value for count in range(p["inputs"] + 1))
            assert value == 1 or p["inputs"] >= 2 ** (value - 1)
            return
        case "times_six_low":
            expected = (sum([p["x"]] * 3) + sum([p["x"]] * 3)) & 1
        case "ha_carry_pair":
            first = p["a"] + p["b"]
            second = (first % 2) + p["cin"]
            expected = (first // 2, second // 2)
            assert not all(expected)
        case "times_thirteen":
            expected = sum(p["x"] for _ in range(13))
        case "square_bit2":
            if p.get("inverse"):
                expected = next(x for x in range(4) if ((x >> 1) & 1) and not (x & 1))
            else:
                expected = ((p["x"] >> 1) & 1) & (1 - (p["x"] & 1))
        case "signed_square":
            signed = -2 * ((p["bits"] >> 1) & 1) + (p["bits"] & 1)
            squared = abs(signed) * abs(signed)
            expected = p["bits"] * p["bits"] - squared if p.get("difference") else squared
        case "run_error":
            trace = [p["bit"]] * p["length"] + [1 - p["bit"]]
            expected = source_model("prep_171_completed_run_parity").detect(trace)[-1]
        case "run_reset":
            ref = source_model("prep_171_completed_run_parity")
            state, _ = ref.step(p["old"], 0, reset=True)
            expected, error = ref.step(state, p["first"])
            assert error == 0
        case "prefix_fallback":
            ref = source_model("prep_173_overlapping_1011")
            state = 0
            for bit in p["history"]:
                state, _ = ref.step(state, int(bit))
            expected = state
        case "lsb_five":
            outputs = set()
            for k in range(1, 9):
                for prefix in range(2**k):
                    if prefix * pow(2, -k, 5) % 5 == p["state"]:
                        new_value = prefix + p["bit"] * 2**k
                        outputs.add(new_value * pow(2, -k - 1, 5) % 5)
            assert len(outputs) == 1
            expected = outputs.pop()
        case "winner":
            locked = False
            expected = "-"
            for item in p["arrivals"]:
                if not locked and item != "-":
                    expected = item
                    locked = True
        case "one_sensor":
            worlds = [{"direction": 1, "observation": (0, 1, 0)}, {"direction": -1, "observation": (0, 1, 0)}]
            compatible = {w["direction"] for w in worlds if w["observation"] == (0, 1, 0)}
            assert compatible == {-1, 1}
            expected = "ambiguous"
        case "door_retreat":
            trace = p["trace"].split(",")
            assert trace[0] == trace[-1] == "00"
            assert all(
                sum(a != b for a, b in zip(x, y, strict=True)) <= 1
                for x, y in zip(trace, trace[1:], strict=False)
            )
            first = next(x for x in trace if x != "00")
            last = next(x for x in reversed(trace) if x != "00")
            assert first == last
            expected = 0
        case "pipeline_diagnosis":
            # Distinct unprovided timing origins can explain the same reported count.
            possible_first_sample_edges = {p["observed"] - 2, p["observed"] - 1}
            assert len(possible_first_sample_edges) > 1
            expected = "insufficient"
        case "bubble_input":
            if p.get("inverse"):
                expected = next(b for b in (0, 1) if 1 and not b)
            else:
                expected = int(bool(p["a"]) and not bool(p["b"]))
        case "promise_mask":
            assert p["a"] ^ value == p["b"] and p["b"] ^ value == p["a"]
            return
        case "hysteresis":
            # Replay an explicitly chosen Schmitt state transition.
            states = {p["previous"]}
            if p["vin"] <= p["low"]:
                states = {0}
            if p["vin"] >= p["high"]:
                states = {1}
            expected = states.pop()
        case "threshold_gap":
            trip_points = [p["vil"] + (p["vih"] - p["vil"]) * f for f in (0.001, 0.25, 0.5, 0.75, 0.999)]
            outputs = {int(p["vin"] >= trip) for trip in trip_points}
            expected = "low" if outputs == {0} else "high" if outputs == {1} else "unspecified"
        case "compare_split" | "padding_failure":
            original = p["left"] + p["right"] if method == "compare_split" else p["real"] + [p["sentinel"]]
            ordered = []
            for item in original:
                i = 0
                while i < len(ordered) and ordered[i] <= item:
                    i += 1
                ordered.insert(i, item)
            size = len(p["left"]) if method == "compare_split" else len(p["real"])
            expected = tuple(ordered[:size])
        case "threshold_witness":
            assert p["low"] < value < p["high"]
            assert close(value - p["low"], p["high"] - value)
            assert [int(x >= value) for x in [p["high"], p["low"]]] == [1, 0]
            return
        case _:
            raise AssertionError(method)
    assert close(value, expected), (method, p, value, expected)


def spectral_disjoint(low, high, rate):
    for sign in (1, -1):
        start, end = (low, high) if sign == 1 else (-high, -low)
        for shift in range(-20, 21):
            if sign == 1 and shift == 0:
                continue
            if min(high, end + shift * rate) >= max(low, start + shift * rate) - 1e-10:
                return False
    return True


def clean(text):
    text = re.sub(r"(?<=[\u05d0-\u05ea])(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])(?=[\u05d0-\u05ea])", " ", str(text))
    text = re.sub(r"(?<=[\u05d0-\u05ea])(?=-[0-9])", " ", text)
    text = re.sub(r"[,;](?=\S)", lambda m: m[0] + " ", text)
    for _ in range(2):
        text = re.sub(r"(?<=[0-9])(?=[A-Za-z]{2})", " ", text)
        text = re.sub(r"\b([A-Za-z]{2,}|A)(?=-?[0-9])", r"\1 ", text)
    text = re.sub(r"(?<=[0-9])(?=[A-Za-z]{2})", " ", text)
    return text.strip()


def build():
    CARDS.clear()
    QUESTIONS.clear()
    CHECKS.clear()
    SPECS.clear()
    definitions()
    refinements()
    assert {s["number"] for s in SPECS} == set(range(126, 201))
    for spec in SPECS:
        number = spec["number"]
        source = f"quick-hw-{number}"
        rows = []
        explanation = {lang: clean(spec["explanation"][lang]) for lang in ("he", "en")}
        for variant, p in enumerate(spec["cases"], 1):
            value = model(spec["method"], p)
            verify(spec["method"], p, value)
            prompt = {lang: clean(p.get(lang, spec["prompt"][lang]).format(**p)) for lang in ("he", "en")}
            options = choices(spec["method"], value)
            options = [{lang: clean(text[lang]) for lang in ("he", "en")} for text in options]
            shift = (number + variant) % 4
            rotated = options[-shift:] + options[:-shift] if shift else options
            key = f"{source}-v{variant}"
            row = dict(
                key=key,
                source_key=source,
                variant=variant,
                topic=spec["topic"],
                status="draft",
                prompt=prompt,
                choices=rotated,
                correct=shift,
                explanation=explanation,
            )
            QUESTIONS.append(row)
            rows.append(row)
            CHECKS.append(
                dict(
                    key=key,
                    method=spec["method"],
                    inputs=p,
                    expected=json.loads(json.dumps(value)),
                    correct_text=options[0],
                    scope="Independent bounded teaching-model replay; not human review,hardware or timing signoff.",
                )
            )
        short = rows[0]
        CARDS.append(
            dict(
                id=source,
                topic=spec["topic"],
                interviewIds=[f"PREP-{spec['prep']:03}"],
                title={lang: clean(spec["title"][lang]) for lang in ("he", "en")},
                prompt=short["prompt"],
                answer={
                    lang: clean(short["choices"][short["correct"]][lang] + ". " + explanation[lang])
                    for lang in ("he", "en")
                },
                takeaway={lang: clean(spec["takeaway"][lang]) for lang in ("he", "en")},
            )
        )
    return QUESTIONS, CHECKS


def write():
    build()
    CONTENT.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (CONTENT / "fundamentals-hardware-400.json").write_text(
        json.dumps(CARDS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, values in [("hardware_400.json", QUESTIONS), ("hardware_400.checks.json", CHECKS)]:
        (OUT / name).write_text(json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Authored {len(CARDS)} bilingual short cards and {len(QUESTIONS)} independently replayed draft cases."
    )


if __name__ == "__main__":
    write()
