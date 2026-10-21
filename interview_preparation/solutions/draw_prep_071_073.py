"""Clean paired parity and binary-pooling diagrams for PREP-071/PREP-073."""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, GREEN, PURPLE = "#17243c", "#365da5", "#277969", "#7250a0"


class Figure:
    def __init__(self, height):
        self.im = Image.new("RGB", (2800, height), "#fcfdff")
        self.d = ImageDraw.Draw(self.im)

    def text(self, xy, value, size=43, color=INK, he=False, bold=False):
        f = ImageFont.truetype(
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            size,
        )
        self.d.text(xy, value[::-1] if he else value, font=f, fill=color, anchor="mm")

    def translated(self, xy, lang, he, en, size=43, color=INK, bold=False):
        self.text(xy, he if lang == "he" else en, size, color, lang == "he", bold)

    def box(self, xy, color=BLUE, fill="#eef3ff"):
        self.d.rounded_rectangle(xy, radius=25, fill=fill, outline=color, width=6)

    def arrow(self, points, color=BLUE):
        self.d.line(points, fill=color, width=8, joint="curve")
        a, b = points[-2:]
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        self.d.polygon(
            [b]
            + [
                (b[0] - 30 * math.cos(angle + v), b[1] - 30 * math.sin(angle + v))
                for v in (-0.45, 0.45)
            ],
            fill=color,
        )

    def save(self, stem, lang):
        OUT.mkdir(parents=True, exist_ok=True)
        self.im.save(OUT / f"{stem}-{lang}.png")


def parity(lang):
    f = Figure(1860)
    f.text((1400, 90), "PREP-071", 67, bold=True)
    f.translated(
        (1400, 200),
        lang,
        "שתי נקודות מאותה תבנית זוגיות נותנות אמצע שלם",
        "Same parity in every coordinate gives an integer midpoint",
        49,
        bold=True,
    )
    f.translated(
        (1400, 325),
        lang,
        "בממד אחד יש שתי קבוצות",
        "One dimension: two classes",
        43,
        color=BLUE,
    )
    for x, he, en, formula in [
        (700, "אי זוגיים", "Odd", "1, 3, 5, ..."),
        (2100, "זוגיים", "Even", "2, 4, 6, ..."),
    ]:
        f.box((x - 550, 400, x + 550, 650))
        f.translated((x, 475), lang, he, en, 45, bold=True)
        f.text((x, 565), formula, 50)
    f.translated(
        (1400, 735),
        lang,
        "שלוש הגרלות מול שתי קבוצות",
        "3 draws > 2 classes",
        46,
        color=GREEN,
        bold=True,
    )
    f.translated(
        (1400, 850),
        lang,
        "בשני ממדים יש ארבע תבניות",
        "Two dimensions: four classes",
        43,
        color=BLUE,
    )
    rows = [
        ("00", "(2, 2)", "(4, 6)", "(3, 4)"),
        ("01", "(2, 1)", "(4, 5)", "(3, 3)"),
        ("10", "(1, 2)", "(3, 6)", "(2, 4)"),
        ("11", "(1, 1)", "(3, 5)", "(2, 3)"),
    ]
    f.box((200, 915, 2600, 1480), GREEN, "#e9f7f0")
    for x, label in [
        (500, "(x mod 2, y mod 2)"),
        (1100, "P"),
        (1700, "Q"),
        (2300, "(P + Q) / 2"),
    ]:
        f.text((x, 985), label, 37, color=GREEN, bold=True)
    for i, row in enumerate(rows):
        for x, label in zip((500, 1100, 1700, 2300), row):
            f.text((x, 1090 + i * 100), label, 44)
    f.text(
        (1400, 1585), "5 > 4        |        2^b + 1 > 2^b", 49, color=GREEN, bold=True
    )
    f.translated(
        (1400, 1730),
        lang,
        "האמצע אינו חייב להופיע בין תוצאות המכונה",
        "The midpoint does not have to be another machine output",
        42,
        color=PURPLE,
    )
    f.save("prep-071-midpoint-parity", lang)


def bottles(lang):
    f = Figure(2110)
    f.text((1400, 85), "PREP-073", 67, bold=True)
    f.translated(
        (1400, 195),
        lang,
        "עשר בדיקות במקביל מקודדות אלף בקבוקים",
        "Ten parallel tests encode one thousand bottles",
        52,
        bold=True,
    )
    f.translated(
        (1400, 295),
        lang,
        "מספר הבקבוק שווה לתווית ועוד אחת",
        "public bottle = label + 1; label: 0 ... 999",
        43,
        color=BLUE,
    )
    f.translated(
        (1400, 400),
        lang,
        "דוגמה לבקבוק ארבע עשרה",
        "Example: public bottle fourteen",
        44,
        bold=True,
    )
    f.text((1400, 490), "14 - 1 = 13 = 0000001101 (binary)", 53, color=GREEN, bold=True)
    labels = [f"T{i}" for i in range(10, 0, -1)]
    bits = [0, 0, 0, 0, 0, 0, 1, 1, 0, 1]
    for i, (label, bit) in enumerate(zip(labels, bits)):
        x = 230 + i * 260
        f.text((x, 610), label, 44, color=BLUE, bold=True)
        f.box(
            (x - 90, 665, x + 90, 805),
            GREEN if bit else BLUE,
            "#e9f7f0" if bit else "#eef3ff",
        )
        f.text((x, 735), str(bit), 58, bold=True)
    f.translated(
        (1400, 880),
        lang,
        "אחד מסמן שהטועם מקבל מנה מהבקבוק",
        "One means this taster receives a portion of that bottle",
        43,
    )
    f.box((250, 1000, 950, 1210))
    f.translated((600, 1070), lang, "כל הבקבוקים", "All bottles", 44, bold=True)
    f.text((600, 1150), "1 ... 1000", 48)
    f.box((1230, 965, 2550, 1240), GREEN, "#e9f7f0")
    f.translated(
        (1890, 1035),
        lang,
        "לכל טועם תערובת נפרדת",
        "A separate pool per taster",
        45,
        color=GREEN,
        bold=True,
    )
    f.text((1890, 1120), "Ti:  (((k-1) >> (i-1)) & 1) = 1", 35)
    f.translated(
        (1890, 1190),
        lang,
        "כל עשר הטעימות בתחילת אותו יום",
        "All ten taste at the start of the same day",
        35,
    )
    f.arrow([(950, 1100), (1230, 1100)])
    f.arrow([(1890, 1240), (1890, 1400)], GREEN)
    f.box((1230, 1400, 2550, 1635), PURPLE, "#f5f0fb")
    f.translated(
        (1890, 1470),
        lang,
        "בסוף היום קוראים את דפוס התוצאות",
        "Read the endpoint outcomes",
        44,
        color=PURPLE,
        bold=True,
    )
    f.text(
        (1890, 1550),
        "1 = dead; 0 = alive  ->  0000001101" if lang == "en" else "0000001101",
        40,
    )
    if lang == "he":
        f.translated((1890, 1605), lang, "מת מסומן באחד וחי מסומן באפס", "", 30)
    f.arrow([(1230, 1515), (950, 1515)], PURPLE)
    f.box((250, 1400, 950, 1635), GREEN, "#e9f7f0")
    f.text(
        (600, 1470), "label = 13" if lang == "en" else "13", 49, color=GREEN, bold=True
    )
    f.translated(
        (600, 1550),
        lang,
        "הבקבוק הארבעה עשר",
        "bottle = 14",
        39,
        color=GREEN,
        bold=True,
    )
    f.translated(
        (1400, 1780),
        lang,
        "אם כולם חיים התווית אפס והרעל בבקבוק הראשון",
        "All alive means label zero, so the poisoned bottle is bottle one",
        42,
        color=PURPLE,
    )
    f.text((1400, 1910), "2^9 = 512 < 1000 <= 1024 = 2^10", 49, color=BLUE, bold=True)
    f.translated(
        (1400, 2015),
        lang,
        "מודל חידה מופשט עם בקבוק מורעל אחד ותוצאה ודאית במועד",
        "Abstract puzzle: exactly one poisoned bottle, deterministic deadline outcomes",
        36,
    )
    f.save("prep-073-binary-pooling", lang)


if __name__ == "__main__":
    for language in ("he", "en"):
        parity(language)
        bottles(language)
    print("Created four bilingual diagrams.")
