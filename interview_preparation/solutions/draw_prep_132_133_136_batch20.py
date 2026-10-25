"""Reproducible authored diagrams; original screenshots remain separate."""

import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BANK = Path(__file__).resolve().parents[1]
OUT = BANK / "diagrams"
INK = "#20283f"
LINE = "#5670a0"
PAPER = "#fffdf8"
BLUE = "#e8f1fc"
GREEN = "#e7f3ec"
PURPLE = "#eee8f7"
AMBER = "#fff0cf"


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/arial" + ("bd" if bold else "") + ".ttf", size)


def text(draw, xy, value, size=34, *, he=False, fill=INK, bold=False, anchor="mm"):
    draw.text(xy, value[::-1] if he else value, font=font(size, bold), fill=fill, anchor=anchor)


def canvas(title, subtitle, he, height=1600):
    img = Image.new("RGB", (2400, height), PAPER)
    d = ImageDraw.Draw(img)
    text(d, (1200, 85), title, 52, he=he, bold=True)
    text(d, (1200, 155), subtitle, 30, he=he)
    return img, d


def save(img, number, stem, lang):
    img.save(OUT / f"prep-{number:03d}-{stem}-{lang}.png")


def rc_prompt(lang):
    he = lang == "he"
    img, d = canvas(
        "מהפכים עם צימוד קיבולי" if he else "Capacitor-coupled inverters",
        "שרטוט נקי של השאלה והקלט" if he else "Authored question circuit and supplied input shape",
        he,
        1350,
    )
    y = 500
    d.line((100, y, 420, y), fill=LINE, width=7)
    d.polygon([(420, y - 120), (420, y + 120), (620, y)], outline=LINE, width=7)
    d.ellipse((620, y - 17, 654, y + 17), outline=LINE, width=6)
    d.line((654, y, 900, y), fill=LINE, width=7)
    for x in (900, 940):
        d.line((x, y - 100, x, y + 100), fill=LINE, width=7)
    d.line((940, y, 1610, y), fill=LINE, width=7)
    d.polygon([(1610, y - 120), (1610, y + 120), (1810, y)], outline=LINE, width=7)
    d.ellipse((1810, y - 17, 1844, y + 17), outline=LINE, width=6)
    d.line((1844, y, 2250, y), fill=LINE, width=7)
    d.line((1250, 240, 1250, 300), fill=LINE, width=7)
    d.rectangle((1220, 300, 1280, 415), outline=LINE, width=7)
    d.line((1250, 415, 1250, y), fill=LINE, width=7)
    d.line((1150, 240, 1350, 240), fill=LINE, width=7)
    d.ellipse((1238, y - 12, 1262, y + 12), fill=LINE)
    for x, label in ((170, "A"), (740, "B"), (1370, "C"), (2100, "D")):
        text(d, (x, 420), label, 52, bold=True)
    text(d, (1250, 205), "VDD", 38)
    text(d, (1320, 350), "R", 38)
    text(d, (920, 650), "Ccouple", 36)
    text(d, (1200, 780), "A(t)", 44, bold=True)
    points = [(200, 1080), (420, 1080)]
    for i in range(4):
        x = 420 + i * 410
        points.extend([(x, 930), (x + 190, 930), (x + 190, 1080), (x + 410, 1080)])
    d.line(points, fill=INK, width=8)
    text(d, (155, 930), "1", 30)
    text(d, (155, 1080), "0", 30)
    text(
        d,
        (1200, 1200),
        "יש להשלים את המתחים בכל ארבע הנקודות" if he else "Determine the voltage at all four labeled nodes",
        34,
        he=he,
    )
    save(img, 132, "rc-question-circuit", lang)


def rc_solution(lang):
    he = lang == "he"
    img, d = canvas(
        "מתחים במודל אידאלי ללא דיודות הגבלה" if he else "Voltages in an ideal unclamped model",
        "דוגמה בלבד: ערכי הרכיבים ותנאי ההתחלה נבחרו במפורש"
        if he
        else "Illustration only: component values and initial conditions are explicit",
        he,
        1780,
    )
    text(d, (1200, 220), "VDD=1, tau=RC=1, VM=0.5; initially A=0, B=C=1", 32)
    spec = importlib.util.spec_from_file_location(
        "rc_draw", BANK / "solutions/prep_132_rc_coupled_inverters.py"
    )
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    edges = [(i, int(i % 2)) for i in range(1, 9)]
    times = sorted(set([i / 100 for i in range(901)] + [i - 1e-7 for i in range(1, 9)]))
    values = rc.trace(edges, times)
    for row, label in enumerate(("A", "B", "C", "D")):
        top = 330 + row * 285
        bottom = top + 205
        ymax = 2 if row == 2 else 1
        for level in range(ymax + 1):
            yy = bottom - level * 190 / ymax
            d.line((240, yy, 2250, yy), fill="#d8dee8", width=2)
            text(d, (170, yy), str(level), 28)
        text(d, (80, (top + bottom) / 2), label, 46, bold=True)
        for t in range(10):
            x = 240 + t / 9 * 2010
            d.line((x, top, x, bottom), fill="#e5e8ef", width=2)
        points = [
            (240 + t / 9 * 2010, bottom - v[row] * 190 / ymax) for t, v in zip(times, values, strict=True)
        ]
        d.line(points, fill=("#385d9a", "#5b4a8a", "#167961", "#b05d24")[row], width=5)
    for t in range(10):
        text(d, (240 + t / 9 * 2010, 1510), str(t), 28)
    text(d, (1200, 1580), "time / tau", 32)
    text(
        d,
        (1200, 1650),
        "החריגה מעל מתח האספקה שייכת למודל ללא הגבלה בלבד"
        if he
        else "Overshoot above the supply belongs to the unclamped model only",
        32,
        he=he,
    )
    text(
        d,
        (1200, 1710),
        "רוחב הפולס תלוי בסף, בקבוע הזמן ובהיסטוריה"
        if he
        else "Pulse width depends on threshold, time constant and history",
        30,
        he=he,
    )
    save(img, 132, "rc-ideal-waveforms", lang)


def painters(lang):
    he = lang == "he"
    img, d = canvas(
        "תחילית של סדרה אינה מגדירה את המשכה"
        if he
        else "A sequence prefix does not determine its continuation",
        "שני המשכים לדוגמה לאחר הבהרת מספור המיקומים"
        if he
        else "Two illustrative continuations after clarifying position labels",
        he,
        1490,
    )
    xs = [700, 1020, 1340, 1660, 1980]
    rows = [
        ("יום" if he else "day", [0, 1, 2, 3, 4]),
        ("A", [0, 2, 4, 6, 8]),
        ("אפשרות ראשונה" if he else "B: option I", [100, 98, 95, 91, 86]),
        ("אפשרות שנייה" if he else "B: option II", [100, 98, 95, 90, 8]),
    ]
    for row, (name, vals) in enumerate(rows):
        y = 350 + row * 165
        text(d, (280, y), name, 34, bold=True, he=he and name != "A")
        for col, (x, val) in enumerate(zip(xs, vals, strict=True)):
            d.rounded_rectangle(
                (x - 140, y - 60, x + 140, y + 60), 22, fill=BLUE if col < 3 else AMBER, outline=LINE, width=3
            )
            text(d, (x, y), str(val), 44, bold=row > 0)
    text(
        d,
        (1200, 1020),
        "אותם נתוני מקור; במקרה השני שתי הפעולות מגיעות למיקום שמונה יחד"
        if he
        else "Same supplied prefix; option II paints position8 simultaneously",
        32,
        he=he,
    )
    text(d, (1200, 1110), "A(t)=2t; B(t)=100-t(t+3)/2", 38)
    text(d, (1200, 1200), "t=11: (22,23)     t=12: (24,10)", 36)
    text(
        d,
        (1200, 1300),
        "לפי ההמשך הזה אין יום של צביעת אותה דלת יחד"
        if he
        else "Under this particular rule, no same-day painted-door meeting occurs",
        32,
        he=he,
    )
    text(
        d,
        (1200, 1390),
        "מפגש בדרך דורש גם מודל תנועה; זו שאלה אחרת"
        if he
        else "Meeting while traveling additionally requires a motion model",
        32,
        he=he,
    )
    save(img, 133, "painter-prefix-ambiguity", lang)


def ecc(lang):
    he = lang == "he"
    img, d = canvas(
        "שמונה סיביות מידע וארבע סיביות בדיקה" if he else "Eight data bits and four check bits",
        "קוד לתיקון שגיאה יחידה בכל שתים עשרה הסיביות"
        if he
        else "A code correcting one error anywhere in the twelve stored bits",
        he,
        1560,
    )
    data = (3, 5, 6, 7, 9, 10, 11, 12)
    for position in range(1, 13):
        x = 100 + (position - 1) * 190
        y = 400
        d.rounded_rectangle(
            (x, y, x + 170, y + 160),
            20,
            fill=PURPLE if position in (1, 2, 4, 8) else GREEN,
            outline=LINE,
            width=3,
        )
        text(d, (x + 85, y - 45), str(position), 32)
        label = "p" + str(position) if position in (1, 2, 4, 8) else "d" + str(data.index(position))
        text(d, (x + 85, y + 80), label, 38, bold=True)
    for i, (p, positions) in enumerate(
        ((1, "1,3,5,7,9,11"), (2, "2,3,6,7,10,11"), (4, "4,5,6,7,12"), (8, "8,9,10,11,12"))
    ):
        expression = f"s{p} = XOR(r" + ", r".join(positions.split(",")) + ")"
        text(d, (1200, 720 + i * 100), expression, 36)
    text(d, (1200, 1180), "S = 8*s8 + 4*s4 + 2*s2 + s1", 38, bold=True)
    text(
        d,
        (1200, 1280),
        "תסמונת אפס מציינת שאין שגיאה; אחרת הופכים את הסיבית שמספרה כתסמונת"
        if he
        else "S=0: no error     S=1..12: flip bit S",
        32,
        he=he,
    )
    text(
        d,
        (1200, 1380),
        "שגיאה יחידה במקום עשר נותנת תסמונת עשר; גם סיביות הבדיקה מוגנות"
        if he
        else "An error at position10 gives syndrome10; check-bit faults are covered too",
        30,
        he=he,
    )
    text(
        d,
        (1200, 1480),
        "שתי שגיאות אינן כלולות בהבטחת התיקון הזאת"
        if he
        else "Two errors lie outside this correction guarantee",
        34,
        he=he,
        fill="#a64d27",
    )
    save(img, 136, "hamming-twelve-bit-layout", lang)


def prisoners(lang):
    he = lang == "he"
    img, d = canvas(
        "מאה אסירים ומתג יחיד" if he else "One hundred prisoners and one switch",
        "גרסת מצב התחלתי לא ידוע; שינוי המתג אינו חובה"
        if he
        else "Unknown initial state; toggling is optional",
        he,
        1250,
    )
    boxes = [
        (
            110,
            330,
            730,
            640,
            GREEN,
            "תשעים ותשעה מדווחים" if he else "99 contributors",
            "עד שני דיווחים לאסיר" if he else "two sends each",
        ),
        (
            890,
            330,
            1510,
            640,
            BLUE,
            "אות ממתין אחד" if he else "one pending token",
            "כבוי / דולק" if he else "OFF / ON",
        ),
        (
            1670,
            330,
            2290,
            640,
            PURPLE,
            "אסיר סופר אחד" if he else "one counter",
            "מכבה אות ואוסף דיווח" if he else "collect ON -> OFF",
        ),
    ]
    for x, y, x2, y2, color, a, b in boxes:
        d.rounded_rectangle((x, y, x2, y2), 25, fill=color, outline=LINE, width=4)
        text(d, ((x + x2) / 2, y + 100), a, 40, bold=True, he=he)
        text(d, ((x + x2) / 2, y + 220), b, 32, he=he)
    for x in (740, 1520):
        d.line((x, 480, x + 140, 480), fill=LINE, width=6)
        d.polygon([(x + 140, 480), (x + 115, 462), (x + 115, 498)], fill=LINE)
    text(d, (1200, 740), "מצב התחלתי לא ידוע" if he else "Unknown initial state", 36, he=he)
    text(d, (1200, 820), "2*99 = 198", 48, bold=True)
    text(
        d,
        (1200, 900),
        "אם אסיר אחד לא דיווח, לכל היותר" if he else "One missing contributor: at most",
        34,
        he=he,
    )
    text(d, (1200, 960), "2*98 + 1 = 197", 40)
    text(
        d,
        (1200, 1050),
        "אם ידוע שהמתג כבוי בתחילה: דיווח אחד לאסיר וספירה עד תשעים ותשעה"
        if he
        else "Known OFF: one send each; count99",
        32,
        he=he,
    )
    text(
        d,
        (1200, 1140),
        "ההכרזה בטוחה; סיום דורש שכל אסיר יחזור שוב ושוב"
        if he
        else "Declarations are safe; eventual completion needs fair repeated visits",
        32,
        he=he,
    )
    save(img, 57, "hundred-one-switch", lang)


if __name__ == "__main__":
    for lang in ("he", "en"):
        for draw in (rc_prompt, rc_solution, painters, ecc, prisoners):
            draw(lang)
