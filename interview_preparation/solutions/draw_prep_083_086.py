"""Reproducible bilingual JobRun MUX storage and priority-prefix schematics."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, CARD, PURPLE, INK, GREEN = "#f8f4e9", "#fffdf8", "#5d4383", "#302344", "#33786d"


def canvas(he, en, lang, height=1500, width=2200):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (width // 2, 90), he, en, lang, 62, bold=True, color=INK)
    return image, draw


def box(draw, rect, color=PURPLE):
    draw.rounded_rectangle(rect, 28, fill=CARD, outline=color, width=6)


def label(draw, point, value, size=43, color=INK):
    text(draw, point, value, size, color=color, bold=True)


def mux_latch(lang):
    im, d = canvas("נועל באמצעות בורר ומשוב", "Latch using a MUX and feedback", lang)
    phrase(d, (1100, 195), "מודל מושגי לאחר התייצבות", "Conceptual model after settling", lang, 40, color=PURPLE)
    d.polygon([(850, 390), (1300, 520), (1300, 1000), (850, 1130)], fill=CARD, outline=PURPLE, width=7)
    label(d, (1060, 760), "MUX 2:1", 54)
    label(d, (895, 560), "1", 46)
    label(d, (895, 980), "0", 46)
    wire(d, [(310, 560), (850, 560)], GREEN)
    label(d, (365, 485), "D", 58, GREEN)
    wire(d, [(1300, 760), (1910, 760)], PURPLE)
    label(d, (1870, 680), "Q", 58, PURPLE)
    d.ellipse((1578, 748, 1602, 772), fill=PURPLE)
    wire(d, [(1590, 760), (1590, 1210), (580, 1210), (580, 980), (850, 980)], PURPLE)
    wire(d, [(1070, 320), (1070, 455)], GREEN)
    label(d, (1070, 275), "EN", 52, GREEN)
    phrase(d, (1100, 1320), "אחד מעביר נתון חדש ואפס בוחר את המצב הקיים", "EN=1 passes D; EN=0 selects stored Q", lang, 43)
    label(d, (1100, 1420), "Q(next) = EN ? D : Q", 48, PURPLE)
    im.save(OUT / f"prep-083-mux-latch-{lang}.png")


def master_slave(lang):
    im, d = canvas("רגיסטר בחזית עולה משני נועלים", "Rising-edge register from two latches", lang, height=1650)
    phrase(d, (1100, 195), "כל קופסה היא נועל עם בורר ומשוב", "Each box is one MUX-feedback latch", lang, 42, color=PURPLE)
    for x0, title, en, low, high in [
        (460, "MASTER", "EN = NOT clk", "transparent", "hold"),
        (1280, "SLAVE", "EN = clk", "hold", "transparent"),
    ]:
        box(d, (x0, 440, x0 + 500, 990))
        label(d, (x0 + 250, 535), title, 51)
        label(d, (x0 + 250, 655), en, 38, PURPLE)
        if lang == "he":
            for y, clock, state in ((800, 0, low), (890, 1, high)):
                label(d, (x0 + 125, y), f"clk={clock}", 33)
                phrase(d, (x0 + 345, y), "שקוף" if state == "transparent" else "שומר", state, lang, 37)
        else:
            label(d, (x0 + 250, 800), f"clk=0: {low}", 35)
            label(d, (x0 + 250, 890), f"clk=1: {high}", 35)
    wire(d, [(120, 710), (460, 710)], GREEN)
    label(d, (200, 625), "D", 54, GREEN)
    wire(d, [(960, 710), (1280, 710)], PURPLE)
    label(d, (1120, 625), "M", 53, PURPLE)
    wire(d, [(1780, 710), (2090, 710)], GREEN)
    label(d, (2025, 625), "Q", 54, GREEN)
    wire(d, [(710, 1200), (710, 990)], PURPLE)
    label(d, (710, 1260), "NOT clk", 44, PURPLE)
    wire(d, [(1530, 1200), (1530, 990)], PURPLE)
    label(d, (1530, 1260), "clk", 44, PURPLE)
    phrase(d, (1100, 1380), "במעבר עולה הראשון נסגר והשני נפתח", "On a rising edge the master closes and the slave opens", lang, 42)
    phrase(d, (1100, 1480), "נועלים אמיתיים דורשים תזמון תקין ללא מעבר מרוץ", "Real latches require valid clock and data timing without race-through", lang, 39)
    label(d, (1100, 1580), "NOT clk = MUX(sel=clk, I0=1, I1=0)", 40)
    im.save(OUT / f"prep-083-master-slave-{lang}.png")


def base_cell(lang):
    im, d = canvas("יחידת בסיס לשתי בקשות", "Two-request priority base unit", lang, height=1600)
    phrase(d, (1100, 190), "הכניסה הגבוהה מנצחת אם אינה חסומה מבחוץ", "The higher input wins unless a higher external group blocks it", lang, 40)
    box(d, (600, 390, 1650, 1110))
    label(d, (1125, 480), "PRIORITY CELL 2", 54)
    for y, name in ((620, "x1"), (790, "x0"), (960, "B")):
        wire(d, [(190, y), (600, y)], GREEN)
        label(d, (300, y - 68), name, 51, GREEN)
    for y, name in ((620, "y1"), (790, "y0"), (960, "V")):
        wire(d, [(1650, y), (2050, y)], PURPLE)
        label(d, (1925, y - 68), name, 51, PURPLE)
    for y, formula in ((635, "y1 = x1 AND NOT B"), (805, "y0 = x0 AND NOT (B OR x1)"), (975, "V = x1 OR x0")):
        label(d, (1125, y), formula, 38)
    phrase(d, (1100, 1230), "חיווי הקבוצה מחושב מהבקשות המקוריות", "V reports raw requests, even when the group is blocked", lang, 42)
    phrase(d, (1100, 1340), "חסימה פירושה שקיימת בקשה בקבוצה גבוהה יותר", "B means at least one request exists in a higher group", lang, 41)
    label(d, (1100, 1460), "Standalone: B=0      x1x0=11 -> y1y0=10", 44, PURPLE)
    im.save(OUT / f"prep-086-base-cell-{lang}.png")


def prefix_tree(lang):
    im, d = canvas("עץ תקפות וחסימה מאוזן", "Balanced valid-and-block tree", lang, height=1940, width=2500)
    phrase(d, (1250, 190), "דוגמה לארבע כניסות בסדר עדיפות יורד", "Four-input example, decreasing priority from left to right", lang, 42)
    # Upward green edges carry raw OR-valid. Downward purple edges carry blocking.
    positions = {"root": (1250, 470), "hi": (670, 870), "lo": (1830, 870)}
    for name, (x, y) in positions.items():
        box(d, (x - 260, y - 110, x + 260, y + 110))
        label(d, (x, y - 35), {"root": "GROUP [3:0]", "hi": "GROUP [3:2]", "lo": "GROUP [1:0]"}[name], 42)
        label(d, (x, y + 55), {"root": "B=0", "hi": "V_H = x3 OR x2", "lo": "V_L = x1 OR x0"}[name], 34, PURPLE)
    for x0, x1, valid in ((670, 1110, "V_H"), (1830, 1390, "V_L")):
        wire(d, [(x0 - 55, 760), (x0 - 55, 650), (x1, 650), (x1, 580)], GREEN)
        label(d, ((x0 + x1) // 2, 620), valid, 34, GREEN)
    wire(d, [(1150, 580), (1150, 690), (725, 690), (725, 760)], PURPLE)
    label(d, (935, 730), "B_H = 0", 33, PURPLE)
    wire(d, [(1350, 580), (1350, 690), (1885, 690), (1885, 760)], PURPLE)
    label(d, (1615, 730), "B_L = V_H", 33, PURPLE)
    for index, x in zip((3, 2, 1, 0), (390, 950, 1550, 2110), strict=True):
        group_x = 670 if index >= 2 else 1830
        box(d, (x - 190, 1190, x + 190, 1440), GREEN)
        label(d, (x, 1260), f"LEAF {index}", 37, GREEN)
        label(d, (x, 1360), f"x{index} / y{index}", 40)
        high_leaf = index % 2 == 1
        up_x = group_x - (170 if high_leaf else 60)
        down_x = group_x + (60 if high_leaf else 170)
        up_y = 1060 if high_leaf else 1095
        down_y = 1130 if high_leaf else 1160
        # Distinct ports: requests are inputs to OR logic, never shorted together.
        wire(d, [(x - 55, 1190), (x - 55, up_y), (up_x, up_y), (up_x, 980)], GREEN)
        wire(d, [(down_x, 980), (down_x, down_y), (x + 55, down_y), (x + 55, 1190)], PURPLE)
        blocked = {3: "B3=0", 2: "B2=x3", 1: "B1=V_H", 0: "B0=V_H OR x1"}[index]
        label(d, (x, 1520), blocked, 34, PURPLE)
    phrase(d, (1250, 1640), "למעלה מחשבים תקפות ולמטה מפיצים חסימה", "Upward: compute valid. Downward: propagate higher-present blocking.", lang, 43)
    label(d, (1250, 1750), "V = V_H OR V_L     B_high = B     B_low = B OR V_H", 43, PURPLE)
    label(d, (1250, 1850), "At each leaf: y[i] = x[i] AND NOT B[i]", 44)
    im.save(OUT / f"prep-086-balanced-tree-{lang}.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for language in ("he", "en"):
        mux_latch(language)
        master_slave(language)
        base_cell(language)
        prefix_tree(language)
