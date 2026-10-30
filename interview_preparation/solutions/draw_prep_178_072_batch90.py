"""Bilingual original illustrations: unknown circular length and stream invariant."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, PALE, GREEN = "#fffdf8", "#302344", "#624883", "#eee7f5", "#30766a"


def panel(d, rect):
    d.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=5)


def circular(lang):
    im = Image.new("RGB", (2400, 1300), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 100), "סימן קבוע מגלה את ההקפה הראשונה", "A fixed marker reveals the first wrap", lang, 57, bold=True)
    phrase(d, (1200, 205), "הדגמה בלבד עבור חמישה תאים", "Illustration only: five physical cells", lang, 40)
    for row, values in enumerate((["1", "?", "?", "?", "?"], ["1", "0", "0", "0", "0"], ["0", "0", "0", "0", "0"])):
        top = 310 + row * 235
        for i, value in enumerate(values):
            left = 650 + i * 250
            panel(d, (left, top, left + 210, top + 140))
            text(d, (left + 105, top + 65), value, 57, color=GREEN if i == 0 else INK, bold=True)
            text(d, (left + 105, top + 175), str(i), 35)
        text(d, (350, top + 70), ("write(0, 1)", "write(1..4, 0)", "write(5, 0)")[row], 39, bold=True)
    phrase(d, (1200, 1080), "רק הכתיבה החמישית פוגעת שוב בתא העוגן", "Only the fifth scanned write reaches the anchor again", lang, 45, bold=True)
    text(d, (1200, 1190), "read(0):  1, 1, 1, 1, 0     →     N = 5", 47, color=GREEN)
    im.save(OUT / f"prep-178-circular-marker-{lang}.png")


def stream(lang):
    im = Image.new("RGB", (2400, 1200), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 100), "תת רצף מרבי בזרם ללא חזרה לאחור", "Maximum contiguous sum in a forward-only stream", lang, 55, bold=True)
    for left, right, name in ((130, 700, "next value"), (930, 1530, "ending here"), (1760, 2290, "best so far")):
        panel(d, (left, 340, right, 590))
        text(d, ((left + right) / 2, 420), name, 46, bold=True)
    text(d, (415, 510), "one item", 37)
    text(d, (1230, 510), "sum, start", 37)
    text(d, (2025, 510), "sum, [start,end)", 34)
    wire(d, [(700, 465), (930, 465)], GREEN)
    wire(d, [(1530, 465), (1760, 465)], GREEN)
    text(d, (1200, 740), "ending = max(value, previous_ending + value)", 49, color=PURPLE)
    phrase(d, (1200, 865), "סכום שלילי אינו עוזר לשום המשך עתידי", "A negative prefix cannot improve any future continuation", lang, 45)
    phrase(d, (1200, 995), "מחזירים גבולות וסכום; שחזור האיברים דורש שמירה או מעבר נוסף", "Return boundaries and sum; values need buffering or replay", lang, 40)
    im.save(OUT / f"prep-072-stream-invariant-batch90-{lang}.png")


def counter(lang):
    im = Image.new("RGB", (2400, 1250), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 95), "שני ביטים עם אפשר ספירה ובחירת כיוון", "Two-bit counter: enable plus direction", lang, 55, bold=True)
    text(d, (1200, 205), "inc = enable      dec = direction (1 down, 0 up)", 45, color=GREEN)
    for i, y in enumerate((360, 650)):
        panel(d, (700, y, 1620, y + 185))
        text(d, (1160, y + 55), ("D0 = q0 XOR inc", "D1 = q1 XOR [inc AND (q0 XOR dec)]")[i], 39, bold=True)
        text(d, (1160, y + 130), ("DFF 0", "DFF 1")[i], 37)
        wire(d, [(1620, y + 90), (2050, y + 90)], GREEN)
        text(d, (2170, y + 90), f"q{i}", 48, bold=True)
    wire(d, [(300, 990), (510, 990), (510, 495), (700, 495)], PURPLE)
    wire(d, [(510, 990), (510, 785), (700, 785)], PURPLE)
    text(d, (300, 920), "same clk", 40)
    phrase(d, (1200, 1090), "כל הביטים החדשים מחושבים מן המצב הישן באותה חזית", "Both new bits use the old state at the same clock edge", lang, 41)
    text(d, (1200, 1185), "inc=0: hold       inc=1,dec=0: +1 mod4       inc=1,dec=1: -1 mod4", 36)
    im.save(OUT / f"prep-064-two-bit-enable-direction-batch90-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        circular(language)
        stream(language)
        counter(language)
