"""Clean bilingual diagrams for batch70 hardware, never raw source composites."""

from math import atan2, cos, pi, sin
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG = "#fffdf8"
INK = "#302344"
PURPLE = "#624883"
PALE = "#eee7f5"
GREEN = "#30766a"
GRAY = "#ddd6e4"
ORANGE = "#ad6c31"


def canvas(he, en, lang, h=1500):
    im = Image.new("RGB", (2400, h), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 90), he, en, lang, 51, bold=True, color=INK)
    return im, d


def label(d, xy, value, size=38, color=INK):
    text(d, xy, value, size, bold=True, color=color)


def panel(d, rect):
    d.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=5)


def dot(d, x, y, color=PURPLE):
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color)


def curve(d, points, label_value, where, color=PURPLE):
    path = []
    for i in range(101):
        t = i / 100
        u = 1 - t
        path.append(
            (
                u**3 * points[0][0]
                + 3 * u * u * t * points[1][0]
                + 3 * u * t * t * points[2][0]
                + t**3 * points[3][0],
                u**3 * points[0][1]
                + 3 * u * u * t * points[1][1]
                + 3 * u * t * t * points[2][1]
                + t**3 * points[3][1],
            )
        )
    d.line(path, fill=BG, width=17)
    d.line(path, fill=color, width=5)
    a, b = path[-4], path[-1]
    angle = atan2(b[1] - a[1], b[0] - a[0])
    d.polygon(
        (
            b,
            (b[0] - 25 * cos(angle - 0.4), b[1] - 25 * sin(angle - 0.4)),
            (b[0] - 25 * cos(angle + 0.4), b[1] - 25 * sin(angle + 0.4)),
        ),
        fill=color,
    )
    x, y = where
    d.rounded_rectangle((x - 60, y - 30, x + 60, y + 30), 10, fill=BG)
    label(d, where, label_value, 34, color)


def table(d, rows, left, top, widths, rowheight=105, size=35):
    for r, row in enumerate(rows):
        x = left
        for c, value in enumerate(row):
            w = widths[c]
            d.rectangle(
                (x, top + r * rowheight, x + w, top + (r + 1) * rowheight),
                fill=PALE if r == 0 else BG,
                outline=GRAY,
                width=3,
            )
            label(d, (x + w / 2, top + r * rowheight + rowheight / 2), value, size)
            x += w


def lc_question(lang):
    im, d = canvas(
        "מעבר מטעינה לחיבור סליל", "Transfer from source charging to inductor connection", lang, 1460
    )
    phrase(
        d,
        (1200, 185),
        "הקו המקווקו מציין את מצב המתג אחרי המעבר",
        "Dashed lever indicates the post-transfer switch position",
        lang,
        37,
    )
    # Common bottom rail, capacitor center, source left, inductor right.
    wire(d, [(400, 500), (400, 710)], PURPLE, arrow=False)
    d.line((300, 710, 500, 710), fill=PURPLE, width=8)
    d.line((340, 750, 460, 750), fill=PURPLE, width=8)
    wire(d, [(400, 750), (400, 1110), (1850, 1110), (1850, 935)], PURPLE, arrow=False)
    label(d, (260, 690), "+", 42)
    label(d, (260, 780), "−", 42)
    label(d, (400, 880), "V0", 42)
    wire(d, [(400, 500), (890, 500)], PURPLE, arrow=False)
    dot(d, 890, 500)
    dot(d, 1190, 500)
    wire(d, [(1190, 500), (1850, 500), (1850, 635)], PURPLE, arrow=False)
    dot(d, 1040, 660)
    wire(d, [(1040, 660), (890, 500)], INK, width=6, arrow=False)
    for i in range(10):
        t0 = i / 10
        t1 = min(1, t0 + 0.055)
        d.line(
            (
                1040 + (1190 - 1040) * t0,
                660 + (500 - 660) * t0,
                1040 + (1190 - 1040) * t1,
                660 + (500 - 660) * t1,
            ),
            fill=GREEN,
            width=7,
        )
    label(d, (890, 420), "1", 40)
    label(d, (1190, 420), "2", 40, GREEN)
    label(d, (1100, 320), "t = 0: 1 → 2", 44, GREEN)
    wire(d, [(1040, 660), (1040, 800)], PURPLE, arrow=False)
    d.line((940, 800, 1140, 800), fill=PURPLE, width=7)
    d.line((940, 840, 1140, 840), fill=PURPLE, width=7)
    wire(d, [(1040, 840), (1040, 1110)], PURPLE, arrow=False)
    dot(d, 1040, 1110)
    label(d, (1210, 820), "C", 50)
    label(d, (900, 770), "+", 38)
    label(d, (900, 900), "−", 38)
    for j in range(6):
        d.arc((1810, 635 + j * 50, 1890, 685 + j * 50), -90, 90, fill=PURPLE, width=6)
    label(d, (2010, 775), "L", 50)
    wire(d, [(2090, 650), (2090, 930)], GREEN)
    label(d, (2180, 785), "iL", 42, GREEN)
    phrase(
        d,
        (1200, 1240),
        "אחרי המעבר המקור מנותק; החוט התחתון משותף",
        "After transfer the source is disconnected; bottom wire is common",
        lang,
        39,
    )
    label(d, (1200, 1350), "vC(0)=V0      iL(0)=0      ideal L,C", 43)
    im.save(OUT / f"prep-170-switched-lc-question-{lang}.png")


def lc_wave(lang):
    im, d = canvas(
        "מתח וזרם מחליפים אנרגיה ללא הפסדים", "Voltage and current exchange energy without loss", lang, 1600
    )
    label(d, (1200, 190), "T0 = 2π√(LC)    |    illustration: V0 > 0", 39)
    left, right = 260, 2180
    for center, kind, color, title in (
        (560, "cos", PURPLE, "vC / V0"),
        (1060, "sin", GREEN, "iL / (V0√(C/L))"),
    ):
        for val in (-1, 0, 1):
            y = center - val * 150
            d.line((left, y, right, y), fill=GRAY, width=2)
            label(d, (left - 65, y), str(val), 30)
        for n in range(5):
            x = left + (right - left) * n / 4
            d.line((x, center - 180, x, center + 180), fill=GRAY, width=2)
            label(d, (x, center + 230), str(n / 2), 29)
        pts = [
            (
                left + (right - left) * i / 400,
                center - 150 * (cos if kind == "cos" else sin)(4 * pi * i / 400),
            )
            for i in range(401)
        ]
        d.line(pts, fill=color, width=7)
        label(d, (1150, center - 240), title, 40, color)
        label(d, (2240, center + 230), "t/T0", 31)
    label(d, (1200, 1410), "E = C*vC²/2 + L*iL²/2 = C*V0²/2", 42)
    phrase(
        d,
        (1200, 1510),
        "באפס מתח עדיין יש זרם; אין דעיכה במודל אידאלי",
        "Zero voltage need not mean zero current; ideal amplitude does not decay",
        lang,
        35,
    )
    im.save(OUT / f"prep-170-ideal-lc-waveforms-{lang}.png")


def run_fsm(lang):
    im, d = canvas("זוכרים את סוג הרצף ואת הזוגיות שלו", "Remember run type and length parity", lang, 1570)
    phrase(
        d,
        (1200, 180),
        "כיתוב חץ הוא קלט חלקי אירוע; מותר לפלט אירוע להירשם בנפרד",
        "Edge label is input/event; event registration is separate",
        lang,
        35,
    )
    # States left to right OE,OO,ZO,ZE; all eight directed transitions.
    xs = (320, 900, 1480, 2060)
    y = 760
    r = 105
    curve(d, [(425, y), (580, y), (650, y), (795, y)], "1/0", (610, 700))
    curve(d, [(1005, y), (1160, y), (1230, y), (1375, y)], "0/1", (1190, 700), GREEN)
    curve(d, [(1585, y), (1740, y), (1810, y), (1955, y)], "0/0", (1770, 700))
    curve(d, [(850, 665), (780, 400), (430, 400), (365, 665)], "1/0", (610, 465))
    curve(d, [(2010, 665), (1890, 260), (1080, 260), (950, 665)], "1/1", (1500, 325), GREEN)
    curve(d, [(1930, 825), (1850, 1080), (1670, 1080), (1540, 850)], "0/0", (1740, 1030))
    curve(d, [(1420, 850), (1300, 1180), (1050, 1180), (960, 850)], "1/0", (1190, 1130))
    curve(d, [(280, 860), (360, 1370), (1320, 1370), (1450, 860)], "0/0", (800, 1280))
    names = (("OE", "ones even"), ("OO", "ones odd"), ("ZO", "zeros odd"), ("ZE", "zeros even"))
    for x, (name, description) in zip(xs, names, strict=True):
        d.ellipse((x - r, y - r, x + r, y + r), fill=PALE, outline=PURPLE, width=5)
        label(d, (x, y - 25), name, 43)
        label(d, (x, y + 36), description, 26)
    wire(d, [(65, y), (205, y)], INK)
    label(d, (145, y - 75), "reset", 28)
    phrase(
        d,
        (1200, 1450),
        "מצב איפוס שקול לריק; קלט ראשון אינו מדווח שגיאה",
        "Reset state behaves like empty history; first bit never reports an error",
        lang,
        37,
    )
    im.save(OUT / f"prep-171-run-parity-fsm-{lang}.png")


def run_example(lang):
    im, d = canvas(
        "האירוע מגיע על הביט שסוגר את הרצף", "The event belongs to the bit closing the run", lang, 1300
    )
    bits = "000011111000001"
    out = "000010000100000"
    for row, (name, values) in enumerate((("In", bits), ("Out", out))):
        yy = 420 + row * 180
        label(d, (160, yy), name, 42)
        for i, value in enumerate(values):
            x = 350 + i * 125
            if row == 1 and value == "1":
                d.rounded_rectangle((x - 48, yy - 60, x + 48, yy + 60), 13, fill="#cce5db")
            label(d, (x, yy), value, 44, GREEN if row == 1 and value == "1" else INK)
            if row == 0:
                label(d, (x, yy - 110), str(i + 1), 27)
    label(d, (1200, 830), "bit 5: closes 0000 → error", 42, GREEN)
    label(d, (1200, 925), "bit 10: closes 11111 → error", 42, GREEN)
    label(d, (1200, 1020), "bit 15: closes 00000 → valid", 42)
    phrase(
        d,
        (1200, 1160),
        "האחד האחרון עדיין פתוח; אין בדיקת סוף קלט סמויה",
        "The final one run is unfinished; there is no implicit flush",
        lang,
        38,
    )
    im.save(OUT / f"prep-171-completed-run-example-{lang}.png")


def led_options(lang):
    im, d = canvas("כל מתג הופך את מצב האור", "Either switch toggle reverses the light", lang, 1680)
    panel(d, (650, 360, 1050, 660))
    label(d, (850, 510), "XOR", 53)
    for y, name in ((430, "A"), (590, "B")):
        wire(d, [(220, y), (650, y)], PURPLE)
        label(d, (300, y - 70), name, 44)
    label(d, (430, 755), "defined pull-up inputs", 30)
    panel(d, (1350, 370, 1850, 650))
    label(d, (1600, 455), "LED driver", 42)
    label(d, (1600, 555), "ON when XOR=1", 30)
    wire(d, [(1050, 510), (1350, 510)], PURPLE)
    label(d, (2100, 280), "VDD", 38)
    wire(d, [(2100, 320), (2100, 380)], PURPLE, arrow=False)
    d.line(
        [(2100, 380), (2075, 405), (2125, 435), (2075, 465), (2125, 495), (2100, 520)], fill=PURPLE, width=5
    )
    label(d, (2260, 445), "R", 36)
    d.polygon(((2050, 565), (2150, 565), (2100, 635)), outline=GREEN, width=5)
    d.line((2050, 645, 2150, 645), fill=GREEN, width=5)
    wire(d, [(2100, 520), (2100, 565)], PURPLE, arrow=False)
    label(d, (2250, 610), "LED", 33, GREEN)
    wire(d, [(2100, 645), (2100, 820), (1600, 820), (1600, 650)], PURPLE, arrow=False)
    label(d, (1600, 900), "driver return → GND", 31)
    label(d, (1200, 1050), "LED = A XOR B   OR   LED = NOT(A XOR B)", 42)
    # Mechanical low-voltage SPDT/traveler alternative.
    phrase(
        d,
        (1200, 1160),
        "חלופת שני מתגי מעבר במתח נמוך",
        "Two low-voltage SPDT switches and traveler wires",
        lang,
        37,
    )
    dot(d, 550, 1370)
    dot(d, 1800, 1370)
    wire(d, [(550, 1370), (850, 1260)], PURPLE, arrow=False)
    wire(d, [(1800, 1370), (1500, 1260)], PURPLE, arrow=False)
    for y in (1260, 1460):
        dot(d, 850, y)
        dot(d, 1500, y)
        wire(d, [(850, y), (1500, y)], GREEN, arrow=False)
    label(d, (1175, 1200), "traveler 0", 31, GREEN)
    label(d, (1175, 1515), "traveler 1", 31, GREEN)
    wire(d, [(180, 1370), (550, 1370)], PURPLE, arrow=False)
    wire(d, [(1800, 1370), (2190, 1370)], PURPLE, arrow=False)
    label(d, (370, 1300), "supply + R + LED", 28)
    label(d, (2130, 1300), "GND", 35)
    phrase(
        d,
        (1200, 1600),
        "פלט מיושב בלבד; מגעים קופצים דורשים טיפול נפרד",
        "Settled states only; contact bounce requires separate treatment",
        lang,
        34,
    )
    im.save(OUT / f"prep-172-two-switch-led-options-{lang}.png")


def detector(lang):
    im, d = canvas("זיהוי חופף של הרצף הנתון", "Overlapping detection of the specified pattern", lang, 1550)
    label(d, (1200, 180), "target 1011   |   edge label: input/event", 39)
    xs = (320, 900, 1480, 2060)
    y = 760
    r = 105
    for i, bit in enumerate(("1/0", "0/0", "1/0")):
        curve(
            d,
            [(xs[i] + r, y), (xs[i] + 250, y), (xs[i + 1] - 250, y), (xs[i + 1] - r, y)],
            bit,
            ((xs[i] + xs[i + 1]) / 2, y - 70),
        )
    curve(d, [(270, 665), (150, 380), (490, 380), (370, 665)], "0/0", (320, 405))
    curve(d, [(850, 665), (730, 430), (1070, 430), (950, 665)], "1/0", (900, 450))
    curve(d, [(2010, 665), (1870, 230), (1090, 230), (950, 665)], "1/1", (1500, 300), GREEN)
    curve(d, [(2010, 850), (1890, 1110), (1660, 1110), (1540, 850)], "0/0", (1770, 1050))
    curve(d, [(1430, 850), (1240, 1350), (480, 1350), (370, 850)], "0/0", (860, 1240))
    for n, (x, prefix) in enumerate(zip(xs, ("empty", "1", "10", "101"), strict=True)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=PALE, outline=PURPLE, width=5)
        label(d, (x, y - 25), f"S{n}", 43)
        label(d, (x, y + 38), prefix, 31)
    wire(d, [(65, y), (205, y)], INK)
    label(d, (145, y - 70), "reset", 28)
    label(d, (1200, 1410), "1011011  →  0001001  (detections at 4,7)", 40, GREEN)
    im.save(OUT / f"prep-173-overlapping-1011-fsm-{lang}.png")


def two_square(lang):
    im, d = canvas("ריבוע מדויק של קלט בן שתי סיביות", "Exact square of a two-bit input", lang, 2050)
    table(
        d,
        [
            ("a", "b", "X", "y3y2y1y0"),
            ("0", "0", "0", "0000"),
            ("0", "1", "1", "0001"),
            ("1", "0", "2", "0100"),
            ("1", "1", "3", "1001"),
        ],
        170,
        320,
        [270, 270, 270, 680],
        120,
        39,
    )
    panel(d, (1770, 330, 2250, 900))
    for i, value in enumerate(("y3 = a AND b", "y2 = a AND NOT b", "y1 = 0", "y0 = b")):
        label(d, (2010, 430 + i * 120), value, 28)
    label(d, (1200, 1040), "2 AND + 1 NOT + wiring + zero", 43, PURPLE)
    for yy, out, in2 in ((1300, "y3", "b"), (1640, "y2", "NOT b")):
        panel(d, (1110, yy - 95, 1510, yy + 95))
        label(d, (1310, yy), "AND", 40)
        wire(d, [(850, yy - 42), (1110, yy - 42)], PURPLE)
        label(d, (815, yy - 42), "a", 35)
        if in2 == "b":
            wire(d, [(850, yy + 42), (1110, yy + 42)], PURPLE)
            label(d, (815, yy + 42), "b", 35)
        else:
            wire(d, [(610, yy + 42), (790, yy + 42)], PURPLE, arrow=False)
            label(d, (560, yy + 42), "b", 35)
            d.polygon(((790, yy), (790, yy + 84), (875, yy + 42)), outline=PURPLE, width=5)
            d.ellipse((875, yy + 30, 899, yy + 54), outline=PURPLE, width=4, fill=BG)
            wire(d, [(899, yy + 42), (1110, yy + 42)], PURPLE)
        wire(d, [(1510, yy), (2110, yy)], GREEN)
        label(d, (2180, yy), out, 36, GREEN)
    label(d, (610, 1840), "y1 = 0", 38)
    label(d, (1750, 1840), "y0 = b", 38)
    phrase(
        d,
        (1200, 1940),
        "ללא סימן; הערך תשע דורש ארבע סיביות מוצא",
        "Unsigned input; nine requires four output bits",
        lang,
        39,
    )
    im.save(OUT / f"prep-174-two-bit-square-gates-{lang}.png")


def toggle(lang):
    im, d = canvas("שני ערכים וארבע ספריות פעולות", "Two values under four operation sets", lang, 1300)
    phrase(
        d,
        (1200, 180),
        "הנחת עריכה הדדית; הכיוון ההפוך חסר במקור",
        "Edited reciprocal promise; reverse mapping is absent in the source",
        lang,
        36,
    )
    table(
        d,
        [("x", "if", "11-x", "28/x", "x XOR 3"), ("4", "7", "7", "7", "7"), ("7", "4", "4", "4", "4")],
        180,
        380,
        [280, 400, 400, 400, 530],
        150,
        43,
    )
    label(d, (1200, 1020), "100 XOR 011 = 111    |    111 XOR 011 = 100", 42, PURPLE)
    phrase(
        d,
        (1200, 1160),
        "התחום מוגבל; אין הבטחה לשמר מספרים אחרים",
        "Restricted domain; other values need not be preserved",
        lang,
        38,
    )
    im.save(OUT / f"prep-119-four-seven-constraints-{lang}.png")


def step_illustration(lang):
    im, d = canvas("המחשת מדרגת שער שנבחרה במפורש", "Explicitly chosen gate-step illustration", lang, 1480)
    phrase(
        d,
        (1200, 185),
        "המקור אינו מזהה צומת ואינו כולל מעגל; זה אינו שחזור שלו",
        "The source identifies no node or circuit; this is not its reconstruction",
        lang,
        35,
    )
    panel(d, (230, 330, 2170, 590))
    label(d, (1200, 410), "VDD → Rpullup → Vout → Ron → GND", 44)
    label(d, (1200, 510), "Cout: Vout → GND    |    forced gate step turns Ron ON", 33)
    left, right = 320, 2170
    top, bottom = 750, 1130
    wire(d, [(left, top), (left, bottom), (right, bottom)], INK, width=5)
    pts = []
    for i in range(301):
        from math import exp

        t = 5 * i / 300
        normalized = 0.1 + 0.9 * exp(-t)
        pts.append((left + (right - left) * i / 300, bottom - 340 * normalized))
    d.line(pts, fill=PURPLE, width=7)
    label(d, (1250, 685), "Vout: continuous transition to divider voltage", 35, PURPLE)
    label(d, (220, 800), "VDD", 32)
    label(d, (220, 1100), "Vfinal", 29)
    label(d, (2190, 1200), "time", 32)
    label(d, (1200, 1310), "tau = (Rpullup || Ron)*Cout", 41)
    phrase(
        d,
        (1200, 1410),
        "מודל מתג וקבל בלבד; אין כאן תחזית התקן פיזי",
        "Switch-capacitor model only; not a physical device prediction",
        lang,
        34,
    )
    im.save(OUT / f"prep-115-gate-step-explicit-illustration-{lang}.png")


def sensor(lang):
    im, d = canvas(
        "אותה תצפית יכולה לדרוש עדכון שונה", "The same observation can require different updates", lang, 1370
    )
    table(
        d,
        [
            ("world", "single sensor", "required change"),
            ("ENTRY", "0 → 1 → 0", "+1"),
            ("EXIT", "0 → 1 → 0", "-1"),
        ],
        150,
        350,
        [500, 1050, 550],
        150,
        42,
    )
    phrase(
        d,
        (1200, 950),
        "שני גלאים מסודרים מספקים מידע על סדר המעבר",
        "Two ordered sensors add traversal-order information",
        lang,
        40,
    )
    label(d, (1200, 1070), "ENTRY: 00 → 10 → 11 → 01 → 00", 38, GREEN)
    label(d, (1200, 1160), "EXIT:   00 → 01 → 11 → 10 → 00", 38, GREEN)
    phrase(
        d,
        (1200, 1280),
        "סופרים בהשלמת מעבר לפי גבול מוגדר",
        "Count at a defined completed-passage boundary",
        lang,
        38,
    )
    im.save(OUT / f"prep-053-single-sensor-observability-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        lc_question(language)
        lc_wave(language)
        run_fsm(language)
        run_example(language)
        led_options(language)
        detector(language)
        two_square(language)
        toggle(language)
        step_illustration(language)
        sensor(language)
    print("Twenty clean bilingual diagrams saved.")
