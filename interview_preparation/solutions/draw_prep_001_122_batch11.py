"""Reproduce clean bilingual FA-popcount and HA-only adder solution circuits."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, GOLD = "#302344", "#5d4383", "#33786d", "#a47328"
BG, PALE = "#fffdf8", "#e7def0"


def canvas(he, en, lang, height=1500, width=2200):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (width // 2, 78), he, en, lang, 50, bold=True)
    return image, draw


def label(draw, point, value, size=39, color=INK):
    text(draw, point, value, size, bold=True, color=color)


def cell(draw, rect, name, three=False):
    x0, y0, x1, _y1 = rect
    draw.rounded_rectangle(rect, radius=20, fill=PALE, outline=PURPLE, width=5)
    label(draw, ((x0 + x1) // 2, y0 + 35), name, 37)
    if three:
        pins = (("A", y0 + 75), ("B", y0 + 150), ("Cin", y0 + 225))
    else:
        pins = (("A", y0 + 75), ("B", y0 + 225))
    for pin, y in pins:
        label(draw, (x0 + 47, y), pin, 28)
    label(draw, (x1 - 47, y0 + 75), "S", 33, GREEN)
    label(draw, (x1 - 47, y0 + 225), "C", 33, GOLD)


def five_inputs(lang):
    image, d = canvas("ספירת חמישה ביטים באמצעות מחברים מלאים", "Five-input population count from full adders", lang, 1550)
    phrase(d, (1100, 170), "בכל רכיב יש שלוש כניסות; סי הוא נשא ואס הוא סכום", "Each cell has three inputs; S denotes Sum and C denotes Carry", lang, 35)
    cell(d, (400, 350, 800, 650), "FA1", three=True)
    cell(d, (1250, 350, 1650, 650), "FA2", three=True)
    cell(d, (1250, 950, 1650, 1250), "FA3", three=True)
    for i, y in enumerate((425, 500, 575)):
        wire(d, [(150, y), (400, y)], INK)
        label(d, (210, y - 55), f"x{i}", 38)
    wire(d, [(800, 425), (1250, 425)], GREEN)
    label(d, (1020, 370), "s1", 40, GREEN)
    for i, y in ((3, 500), (4, 575)):
        wire(d, [(1100, y), (1250, y)], INK)
        label(d, (1130, y - 38), f"x{i}", 31)
    wire(d, [(1650, 425), (2050, 425)], PURPLE)
    label(d, (1930, 355), "y0  [1]", 41, PURPLE)
    # A/B are symmetric. Bring c1 into the lower input and c2 into the
    # upper input to avoid a crossing; the published FA(c1,c2,0) is unchanged.
    wire(d, [(800, 575), (1000, 575), (1000, 1100), (1250, 1100)], GOLD)
    label(d, (880, 850), "c1 [2]", 36, GOLD)
    wire(d, [(1650, 575), (1850, 575), (1850, 850), (1100, 850), (1100, 1025), (1250, 1025)], GOLD)
    label(d, (1750, 730), "c2 [2]", 36, GOLD)
    wire(d, [(950, 1175), (1250, 1175)], INK)
    label(d, (1030, 1230), "0", 45)
    wire(d, [(1650, 1025), (2050, 1025)], PURPLE)
    label(d, (1940, 960), "y1  [2]", 41, PURPLE)
    wire(d, [(1650, 1175), (2050, 1175)], PURPLE)
    label(d, (1940, 1110), "y2  [4]", 41, PURPLE)
    label(d, (1100, 1350), "count = y0 + 2*y1 + 4*y2       11111 → 101", 40, PURPLE)
    phrase(d, (1100, 1440), "סוגריים מרובעים מציינים משקל בספירה המקורית", "Square brackets show weight in the original count", lang, 36)
    phrase(d, (1100, 1510), "המחבר האחרון הוא רכיב מלא שמבוא אחד שלו מחובר לאפס", "The last cell is still a full adder, with one input tied to zero", lang, 33)
    image.save(OUT / f"prep-001-five-input-network-{lang}.png")


def half_column(lang):
    image, d = canvas("עמודה גבוהה באמצעות שלושה מחברים למחצה", "One higher column built from three half adders", lang, 1520)
    phrase(d, (1100, 170), "אין שער איחוד חיצוני; משתמשים במוצא הסכום של הרכיב האחרון", "No external merging gate; use the last cell's Sum output", lang, 35)
    cell(d, (500, 350, 900, 650), "HA A")
    cell(d, (1300, 350, 1700, 650), "HA B")
    cell(d, (1300, 900, 1700, 1200), "HA C")
    for name, y in (("Ai", 425), ("Bi", 575)):
        wire(d, [(220, y), (500, y)], INK)
        label(d, (320, y - 60), name, 42)
    wire(d, [(900, 425), (1300, 425)], GREEN)
    label(d, (1100, 365), "Pi", 40, GREEN)
    wire(d, [(1100, 575), (1300, 575)], INK)
    label(d, (1150, 520), "Ci", 40)
    wire(d, [(1700, 425), (2070, 425)], PURPLE)
    label(d, (1970, 365), "Si", 46, PURPLE)
    # Gi/Hi are symmetric HA inputs; lower/upper routing avoids a crossing.
    wire(d, [(900, 575), (1000, 575), (1000, 1125), (1300, 1125)], GOLD)
    label(d, (900, 840), "Gi", 43, GOLD)
    wire(d, [(1700, 575), (1900, 575), (1900, 775), (1150, 775), (1150, 975), (1300, 975)], GOLD)
    label(d, (2010, 680), "Hi", 43, GOLD)
    wire(d, [(1700, 975), (2070, 975)], PURPLE)
    label(d, (1950, 910), "C(i+1)", 42, PURPLE)
    wire(d, [(1700, 1125), (2035, 1125)], GOLD)
    label(d, (1920, 1060), "Ui = 0", 39, GOLD)
    d.line(((2035, 1105), (2075, 1145)), fill=GOLD, width=5)
    d.line(((2035, 1145), (2075, 1105)), fill=GOLD, width=5)
    label(d, (1100, 1320), "Gi AND Hi = 0     Gi XOR Hi = Gi OR Hi", 40, PURPLE)
    phrase(d, (1100, 1415), "הנשאים בלעדיים; מוצא הנשׂא האחרון אפס ונשאר ללא שימוש", "The internal carries are exclusive; the last Carry is zero and unused", lang, 34)
    phrase(d, (1100, 1480), "משכפלים לכל ביט גבוה; אין כאן רכיב מחבר מלא נוסף", "Repeat for the three higher columns; no extra full-adder primitive is used", lang, 31)
    image.save(OUT / f"prep-122-half-adder-column-{lang}.png")


def half_network(lang):
    image, d = canvas("מחברים ארבע עמודות ושומרים את הנשא הסופי", "Connect four columns and retain the final carry", lang, 1450, 2400)
    phrase(d, (1200, 170), "העמודה הנמוכה היא רכיב יחיד; כל עמודה גבוהה מורחבת בשרטוט הנוסף", "Lowest column: one HA; each higher column expands as in the other circuit", lang, 35)
    rects = [(160, 460, 510, 930), (700, 460, 1050, 930), (1240, 460, 1590, 930), (1780, 460, 2130, 930)]
    for i, (left, top, right, bottom) in enumerate(rects):
        center = (left + right) // 2
        d.rounded_rectangle((left, top, right, bottom), radius=20, fill=PALE, outline=PURPLE, width=5)
        phrase(d, (center, 525), f"עמודה {i}", f"COLUMN {i}", lang, 35, bold=True)
        label(d, (center, 630), "1 × HA" if i == 0 else "3 × HA", 45, GREEN)
        phrase(d, (center, 815), "סכום", "SUM", lang, 36, bold=True, color=GREEN)
        for x, name in ((center - 85, f"A{i}"), (center + 85, f"B{i}")):
            wire(d, [(x, 330), (x, 460)], INK)
            label(d, (x, 275), name, 39)
        wire(d, [(center, bottom), (center, 1100)], PURPLE)
        label(d, (center, 1160), f"S{i}", 44, PURPLE)
        if i < 3:
            next_left = rects[i + 1][0]
            wire(d, [(right, 710), (next_left, 710)], GOLD)
            label(d, ((right + next_left) // 2, 650), f"C{i + 1}", 35, GOLD)
    wire(d, [(2130, 710), (2340, 710)], PURPLE)
    label(d, (2250, 800), "S4=C4", 34, PURPLE)
    label(d, (1200, 1280), "S[4:0] = C4 S3 S2 S1 S0       1111 + 1111 = 11110", 39, PURPLE)
    phrase(d, (1200, 1380), "עשרה רכיבים במימוש הזה; אין טענת מינימום או תזמון פיזי", "Ten cells in this construction; no minimum-size or physical timing claim", lang, 36)
    image.save(OUT / f"prep-122-half-adder-network-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        five_inputs(language)
        half_column(language)
        half_network(language)
    print("Wrote six bilingual PREP-001/122 solution figures")
