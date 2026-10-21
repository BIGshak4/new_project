"""Deterministic bilingual algorithm figures; editable source accompanies PNGs."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, GREEN, MUTED, ORANGE = "#21314d", "#365da5", "#277969", "#67768c", "#ae641c"


class Figure:
    def __init__(self, height):
        self.image = Image.new("RGB", (2400, height), "#fcfdff")
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, value, size=42, color=INK, he=False, bold=False):
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
        self.draw.text((x, y), value[::-1] if he else value, font=font, fill=color, anchor="mm")

    def tr(self, x, y, lang, he, en, **options):
        self.text(x, y, he if lang == "he" else en, he=lang == "he", **options)

    def box(self, xy, color=BLUE, fill="#eef3ff"):
        self.draw.rounded_rectangle(xy, radius=22, fill=fill, outline=color, width=4)

    def save(self, stem, lang):
        OUT.mkdir(exist_ok=True)
        self.image.save(OUT / f"{stem}-{lang}.png")


def stock(lang):
    f = Figure(1460)
    f.text(1200, 85, "PREP-066", size=62, bold=True)
    f.tr(1200, 185, lang, "לכל יום מכירה בוחרים את המחיר הנמוך שקדם לו", "For each sale, use the lowest price from an earlier day", size=46, bold=True)
    prices = [7, 1, 5, 3, 6, 4]
    f.tr(270, 335, lang, "יום", "Day", color=MUTED)
    f.tr(270, 435, lang, "מחיר", "Price", color=MUTED)
    for index, value in enumerate(prices):
        x = 600 + index * 290
        f.text(x, 335, str(index), color=MUTED)
        color = GREEN if index in (1, 4) else BLUE
        f.box((x - 90, 385, x + 90, 485), color, "#eaf7f0" if color == GREEN else "#eef3ff")
        f.text(x, 435, str(value), size=52, color=color, bold=True)
    f.tr(1200, 590, lang, "קנייה ביום אחד ומכירה ביום ארבע נותנות רווח חמש", "Buy on day 1, sell on day 4: profit 6 - 1 = 5", color=GREEN, size=43, bold=True)
    headings = [(350, "מכירה", "Sell"), (900, "יום מינימום קודם", "Earlier minimum day"), (1480, "רווח מועמד", "Candidate profit"), (2060, "רווח שיא", "Best profit")]
    for x, he, en in headings:
        f.tr(x, 760, lang, he, en, size=36, color=BLUE, bold=True)
    rows = [(1, 0, -6, 0), (2, 1, 4, 4), (3, 1, 2, 4), (4, 1, 5, 5), (5, 1, 3, 5)]
    for n, row in enumerate(rows):
        y = 870 + n * 90
        if n % 2 == 0:
            f.draw.rounded_rectangle((120, y - 40, 2280, y + 40), radius=12, fill="#f1f5fa")
        for (x, _, _), value in zip(headings, row):
            f.text(x, y, str(value), size=42, color=GREEN if n == 3 else INK)
    f.tr(1200, 1370, lang, "מחשבים את הרווח לפני שמכניסים את יום המכירה למינימום", "Evaluate the sale BEFORE admitting that day into the minimum", size=37, color=ORANGE)
    f.save("prep-066-prefix-min-trace", lang)


def maximum(lang):
    f = Figure(1210)
    f.text(1200, 85, "PREP-068", size=62, bold=True)
    f.tr(1200, 185, lang, "מקסימום ללא פעולת השוואה מפורשת", "Maximum without an explicit comparison", size=48, bold=True)
    f.box((200, 300, 2200, 500), GREEN, "#eaf7f0")
    f.text(1200, 400, "(a + b + |a - b|) / 2", size=74, color=GREEN, bold=True)
    f.tr(1200, 585, lang, "הזהות מתאימה לשלמים מדויקים כאשר ערך מוחלט מותר", "Use this identity for exact integers when absolute value is allowed", size=40)
    f.text(1200, 720, "a = -4     b = 7       (-4 + 7 + 11) / 2 = 7", size=48, color=BLUE)
    f.box((180, 840, 2220, 1100), ORANGE, "#fff6e9")
    f.tr(1200, 900, lang, "ברוחב קבוע יש לבדוק גלישה לפני שבוחרים שיטה", "Fixed-width integers require an overflow-safe method", size=41, color=ORANGE, bold=True)
    f.text(1200, 990, "INT32_MAX - INT32_MIN = 4294967295", size=43, color=INK)
    f.tr(1200, 1060, lang, "ההפרש אינו ניתן לייצוג בשלושים ושניים ביטים עם סימן", "This difference does not fit a signed 32-bit integer", size=35, color=MUTED)
    f.save("prep-068-exact-integer-identity", lang)


def subarray(lang):
    f = Figure(1830)
    f.text(1200, 85, "PREP-072", size=62, bold=True)
    f.tr(1200, 185, lang, "בכל תא בוחרים להתחיל מחדש או להמשיך רצף", "At each position, restart or extend the current interval", size=47, bold=True)
    values = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    for i, value in enumerate(values):
        x = 260 + i * 235
        color = GREEN if 3 <= i <= 6 else BLUE
        f.text(x, 315, str(i), color=MUTED, size=32)
        f.box((x - 78, 360, x + 78, 460), color, "#eaf7f0" if color == GREEN else "#eef3ff")
        f.text(x, 410, str(value), size=52, color=color, bold=True)
    f.text(1200, 565, "[4, -1, 2, 1]      sum = 6      start = 3      end = 6", size=44, color=GREEN, bold=True)
    headings = [(260, "אינדקס", "Index"), (700, "ערך", "Value"), (1260, "סכום המסתיים כאן", "Best ending here"), (1960, "שיא עד כאן", "Best so far")]
    for x, he, en in headings:
        f.tr(x, 730, lang, he, en, size=37, color=BLUE, bold=True)
    current = best = values[0]
    for i, value in enumerate(values):
        if i:
            current = value if current < 0 else current + value
            best = max(best, current)
        y = 835 + i * 87
        if i % 2 == 0:
            f.draw.rounded_rectangle((110, y - 38, 2290, y + 38), radius=12, fill="#f1f5fa")
        for (x, _, _), val in zip(headings, (i, value, current, best)):
            f.text(x, y, str(val), size=42, color=GREEN if i == 6 else INK)
    f.tr(1200, 1690, lang, "הדוגמה כאן נקבעה במפורש ואינה תעתיק של צילום המקור", "This explicit example is separate from the ambiguous source screenshot", size=35, color=ORANGE)
    f.tr(1200, 1760, lang, "מאתחלים מהאיבר הראשון כדי לטפל גם במערך שכולו שלילי", "Initialize from the first value to handle all-negative arrays", size=36, color=MUTED)
    f.save("prep-072-kadane-trace", lang)


if __name__ == "__main__":
    for lang in ("he", "en"):
        stock(lang)
        maximum(lang)
        subarray(lang)
