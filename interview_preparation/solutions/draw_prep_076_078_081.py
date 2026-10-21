"""Reproducible, authored bilingual schematics for this intake only.

Pillow is used for native diagram primitives, not screenshot editing.
Hebrew diagram headings contain Hebrew only and are reversed for fonts on a
runtime without libraqm; all signal names and formulas remain LTR.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
INK, ACCENT, MUTED = "#312247", "#62458A", "#6D607D"
BG, FILL, GREEN = "#FCFAF5", "#F0EAF6", "#286C5C"


class Diagram:
    def __init__(self, width, height):
        self.image = Image.new("RGB", (width * SCALE, height * SCALE), BG)
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, value, size=25, color=INK, he=False):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * SCALE)
        hebrew = he or any("\u05d0" <= letter <= "\u05ea" for letter in value)
        self.draw.text((x * SCALE, y * SCALE), value[::-1] if hebrew else value,
                       font=font, fill=color, anchor="mm")

    def line(self, points, color=ACCENT, width=3, arrow=False):
        self.draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=color,
                       width=width * SCALE, joint="curve")
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            a = math.atan2(y - py, x - px)
            self.draw.polygon([(x * SCALE, y * SCALE)] +
                              [((x - 14 * math.cos(a + d)) * SCALE,
                                (y - 14 * math.sin(a + d)) * SCALE) for d in (-.5, .5)], fill=color)

    def box(self, x, y, w, h, lines, fill=FILL):
        self.draw.rounded_rectangle((x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE),
                                    radius=12 * SCALE, fill=fill, outline=ACCENT, width=2 * SCALE)
        for i, line in enumerate(lines):
            size = 25 if i else 29
            while ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * SCALE).getlength(line) > (w - 28) * SCALE:
                size -= 1
            self.text(x + w / 2, y + h * (i + 1) / (len(lines) + 1), line, size)

    def save(self, name):
        target = ROOT / "diagrams" / name
        self.image.save(target)
        print(target)


def address_test(lang):
    d = Diagram(1320, 610)
    d.text(660, 47, "כתיבה לכל הכתובות ואז קריאה מכל הכתובות" if lang == "he" else
           "Write every address, then read every address", 34, he=lang == "he")
    d.box(55, 105, 1210, 105, ["N = 4, W = 1", "כתובות לוגיות" if lang == "he" else "Logical addresses", "0          1          2          3"])
    d.box(55, 240, 440, 150, ["ביט אפס של הכתובת" if lang == "he" else "Address bit 0", "0   1   0   1", "כותבים הכל ואז קוראים" if lang == "he" else "Write all, then read all"])
    d.box(825, 240, 440, 150, ["ביט אחד של הכתובת" if lang == "he" else "Address bit 1", "0   0   1   1", "כותבים הכל ואז קוראים" if lang == "he" else "Write all, then read all"])
    d.line([(495, 315), (825, 315)], arrow=True)
    d.text(660, 282, "וגם תבנית משלימה" if lang == "he" else "also test complements", 24)
    d.box(100, 435, 1120, 120, ["כתובות אפס ושתיים חולקות תא פיזי אחד" if lang == "he" else "Example alias: logical 0 and 2 share one physical cell",
                               "בביט אפס הן זהות ובביט אחד נדרשים אפס ואחד באותו תא" if lang == "he" else "Bit 0 cannot separate them; bit 1 requests 0 and 1 in the same cell."], fill="#E8F1EA")
    d.save(f"prep-076-bit-plane-test-{lang}.png")


def prompt_counter(lang):
    d = Diagram(1020, 610)
    d.text(510, 45, "המונה הנתון" if lang == "he" else "Given counter interface", 34, he=lang == "he")
    d.box(350, 120, 320, 330, ["COUNTER", "Q[2:0]"])
    for label, y in (("EN", 185), ("clk", 345)):
        d.text(150, y - 30, label, 31)
        d.line([(160, y), (350, y)], arrow=True)
    d.line([(350, 330), (374, 345), (350, 360)])
    for label, y in (("Q2", 185), ("Q1", 280), ("Q0", 375)):
        d.line([(670, y), (870, y)], arrow=True)
        d.text(825, y - 30, label, 31)
    d.line([(510, 540), (510, 450)], arrow=True)
    d.text(570, 500, "RST", 29)
    d.text(510, 580, "מונה עם אפשור ספירה ואיפוס בחזית השעון העולה" if lang == "he" else "EN: count enable     clk: rising-edge clock     RST: reset", 23)
    d.save(f"prep-078-counter-prompt-{lang}.png")


def fifth_edge(lang):
    d = Diagram(1450, 670)
    d.text(725, 42, "פולס בכל חזית קלט חמישית" if lang == "he" else
           "One pulse on every fifth sampled input rise", 34, he=lang == "he")
    d.box(210, 120, 230, 120, ["D-FF", "previous <= x"])
    d.box(540, 280, 260, 120, ["גילוי עלייה" if lang == "he" else "Rising event", "e = x & ~previous"])
    d.box(900, 280, 260, 120, ["מונה אירועים" if lang == "he" else "Mod-5 counter", "0 -> 1 -> ... -> 4 -> 0"])
    d.box(900, 470, 260, 100, ["פענוח לפני החזית" if lang == "he" else "Terminal condition", "e & (count == 4)"])
    d.box(1230, 470, 170, 100, ["D-FF", "pulse"])
    d.text(70, 340, "x", 32)
    d.line([(105, 340), (540, 340)], arrow=True)
    d.line([(150, 340), (150, 180), (210, 180)], arrow=True)
    d.line([(440, 180), (670, 180), (670, 280)], arrow=True)
    d.line([(800, 340), (900, 340)], arrow=True)
    d.text(850, 310, "e", 25)
    d.line([(850, 340), (850, 520), (900, 520)], arrow=True)
    for x, y in ((150, 340), (850, 340)):
        d.draw.ellipse(((x - 5) * SCALE, (y - 5) * SCALE, (x + 5) * SCALE, (y + 5) * SCALE), fill=ACCENT)
    d.line([(1030, 400), (1030, 470)], arrow=True)
    d.line([(1160, 520), (1230, 520)], arrow=True)
    d.text(690, 445, "המצב הישן קובע את הפולס הרשום" if lang == "he" else "old count; pulse is registered", 24)
    d.text(725, 600, "שעון משותף ואיפוס סינכרוני לכל רכיבי המצב" if lang == "he" else "Common clock and synchronous reset for all state", 27)
    d.text(725, 640, "rst=1: previous=0, count=0, pulse=0", 27)
    d.save(f"prep-078-fifth-edge-solution-{lang}.png")


def fifth_trace(lang):
    d = Diagram(1390, 580)
    d.text(695, 42, "עקבת מחזורים לדוגמה" if lang == "he" else "Complete example clock trace", 34, he=lang == "he")
    labels = ["דגימה", "x", "אירוע", "מצב אחרי", "פלט אחרי"] if lang == "he" else ["sample", "x", "event", "count (after)", "pulse (after)"]
    rows = [list(range(13)), [0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0],
            [0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0],
            [0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]]
    start, step = 285, 80
    for i, (label, values) in enumerate(zip(labels, rows)):
        y = 130 + i * 78
        d.text(135, y, label, 25)
        for j, value in enumerate(values):
            color = GREEN if j == 10 else INK
            d.text(start + j * step, y, str(value), 30, color)
        if i < 4:
            d.line([(35, y + 38), (1350, y + 38)], color="#DCD3E4", width=1)
    d.text(695, 520, "previous=0, count=0", 25)
    d.text(695, 558, "לאחר דגימה עשר הפולס גבוה למחזור אחד" if lang == "he" else "Pulse is high for one cycle after sample 10 only.", 25)
    d.save(f"prep-078-cycle-trace-{lang}.png")


def error_monitor(lang):
    d = Diagram(1300, 690)
    d.text(650, 42, "בדיקה במקטעים קבועים" if lang == "he" else "Fixed non-overlapping blocks", 34, he=lang == "he")
    d.box(50, 130, 310, 130, ["דגימת הקלט" if lang == "he" else "Sample ERROR", "ERROR" if lang == "he" else "once per rising clock"])
    d.box(495, 130, 310, 130, ["עדכון מונים" if lang == "he" else "Update counters", "cycles += 1", "errors = min(11, errors+ERROR)"])
    d.box(940, 130, 310, 130, ["בדיקת סוף מקטע" if lang == "he" else "Block complete?", "cycles == 100000"])
    d.line([(360, 195), (495, 195)], arrow=True)
    d.line([(805, 195), (940, 195)], arrow=True)
    d.box(720, 385, 530, 130, ["דיווח לפי המונים המעודכנים" if lang == "he" else "Report using updated errors", "errors > 10  ->  Failed", "errors <= 10 -> Passed"])
    d.line([(1095, 260), (1095, 385)], arrow=True)
    d.text(1145, 325, "כן" if lang == "he" else "yes", 24)
    d.box(50, 385, 400, 130, ["איפוס למקטע הבא" if lang == "he" else "Reset for next block", "cycles = 0, errors = 0"])
    d.line([(720, 450), (450, 450)], arrow=True)
    d.line([(250, 385), (250, 260)], arrow=True)
    d.line([(1250, 205), (1280, 205), (1280, 585), (30, 585), (30, 205), (50, 205)], arrow=True)
    d.text(650, 620, "אם לא הסתיים המקטע ממשיכים לדגום" if lang == "he" else "no: continue sampling; sample 100000 belongs to the current block", 25)
    d.text(650, 660, "סופרים מחזורים גבוהים ולא עליות של הקלט ורק מעל עשר שגיאות נכשל" if lang == "he" else "Count HIGH CYCLES, not signal rising edges. Exactly 10 is allowed.", 26, GREEN)
    d.save(f"prep-081-fixed-block-monitor-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        address_test(language)
        prompt_counter(language)
        fifth_edge(language)
        fifth_trace(language)
        error_monitor(language)
