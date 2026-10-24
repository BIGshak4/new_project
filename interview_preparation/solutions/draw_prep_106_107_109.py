"""Reproducible bilingual SR, prefix-mask and NAND/NOR figures."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, PALE, BG = "#302344", "#5d4383", "#33786d", "#e7def0", "#fffdf8"


def canvas(he, en, lang, height=1500, width=2200):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (width // 2, 85), he, en, lang, 53, bold=True)
    return image, draw


def label(d, xy, value, size=40, color=INK):
    text(d, xy, value, size, bold=True, color=color)


def box(d, rect, title):
    d.rounded_rectangle(rect, 22, fill="#f8f4e9", outline=PURPLE, width=5)
    label(d, ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), title, 47)


def sr_latch(lang):
    image, d = canvas("אחסון אסינכרוני באמצעות שני שערי נור", "Asynchronous storage from two NOR gates", lang)
    phrase(d, (1100, 180), "זהו נועל בעל רגישות לרמה, לא פליפ־פלופ דוגם", "This is a level-sensitive latch, not an edge-triggered flip-flop", lang, 37)
    box(d, (650, 350, 1100, 650), "NOR")
    box(d, (650, 900, 1100, 1200), "NOR")
    wire(d, [(150, 425), (650, 425)], INK)
    label(d, (210, 350), "R", 55)
    wire(d, [(150, 975), (650, 975)], INK)
    label(d, (210, 900), "S", 55)
    wire(d, [(1100, 500), (2020, 500)], PURPLE)
    label(d, (1960, 420), "Q", 56, PURPLE)
    wire(d, [(1100, 1050), (2020, 1050)], GREEN)
    label(d, (1940, 970), "Qbar", 52, GREEN)
    # Data feedback; only explicit dots join output wires. The green bridge
    # crosses the purple feedback without connecting.
    d.ellipse((1590, 490, 1610, 510), fill=PURPLE)
    wire(d, [(1600, 500), (1600, 800), (500, 800), (500, 1125), (650, 1125)], PURPLE)
    d.ellipse((1390, 1040, 1410, 1060), fill=GREEN)
    wire(d, [(1400, 1050), (1400, 700), (350, 700), (350, 575), (650, 575)], GREEN)
    d.rectangle((1388, 779, 1412, 821), fill=BG)
    d.arc((1380, 780, 1420, 820), -90, 90, fill=GREEN, width=6)
    d.rectangle((488, 954, 512, 996), fill=BG)
    d.arc((480, 955, 520, 995), -90, 90, fill=PURPLE, width=6)
    label(d, (1100, 1305), "Q = NOT (R OR Qbar)     Qbar = NOT (S OR Q)", 37, PURPLE)
    phrase(d, (1100, 1415), "נקודה היא חיבור; קשת היא חצייה ללא חיבור", "Dot: connected; bridge: crossing without a connection", lang, 36)
    image.save(OUT / f"prep-106-cross-coupled-nor-{lang}.png")


def sr_edge_extension(lang):
    image, d = canvas("כאשר נדרש רכיב דוגם בחזית עולה", "When rising-edge behavior is required", lang, height=1450)
    phrase(d, (1100, 180), "הרחבה נפרדת: נועלים משתי פאזות ולוגיקת המצב הבא", "Separate extension: opposite-phase latches and next-state logic", lang, 37)
    for rect, title in [((250, 400, 690, 770), "NEXT LOGIC"),
                        ((900, 400, 1340, 770), "D MASTER"),
                        ((1550, 400, 1990, 770), "D SLAVE")]:
        box(d, rect, title)
    wire(d, [(90, 480), (250, 480)], INK)
    label(d, (120, 400), "S,R", 42)
    wire(d, [(690, 580), (900, 580)], GREEN)
    label(d, (790, 500), "D*", 40, GREEN)
    wire(d, [(1340, 580), (1550, 580)], PURPLE)
    label(d, (1440, 500), "M", 40, PURPLE)
    wire(d, [(1990, 580), (2140, 580)], PURPLE)
    label(d, (2100, 500), "Q", 43, PURPLE)
    d.ellipse((2042, 572, 2058, 588), fill=PURPLE)
    wire(d, [(2050, 580), (2050, 1050), (140, 1050), (140, 680), (250, 680)], PURPLE)
    label(d, (1120, 840), "EN = NOT clk", 37)
    label(d, (1770, 840), "EN = clk", 37)
    label(d, (1100, 1160), "D* = S OR (Q AND NOT R)       valid: NOT(S AND R)", 37, PURPLE)
    phrase(d, (1100, 1270), "כל נועל נתונים נבנה משערים; אין תא דוגם מוסתר", "Each D latch is gate-built; no hidden flip-flop primitive", lang, 37)
    phrase(d, (1100, 1370), "המודל דורש תזמון תקין ללא חפיפת שקיפות", "Valid data/clock timing and no transparency overlap are required", lang, 36)
    image.save(OUT / f"prep-106-edge-extension-{lang}.png")


def low_mask(lang):
    image, d = canvas("ביט נשאר רק אם אין אחד נמוך ממנו", "A bit survives only if no lower bit is set", lang, height=1400)
    phrase(d, (1100, 180), "שרשרת קידומת של שערי אור; המספור עולה משמאל לימין כאן", "OR-prefix chain; bit indices increase left to right in this schematic", lang, 36)
    for index in range(4):
        x = 230 + index * 520
        box(d, (x, 430, x + 330, 750), f"CELL {index}")
        wire(d, [(x + 165, 280), (x + 165, 430)], GREEN)
        label(d, (x + 165, 235), f"x{index}", 47, GREEN)
        wire(d, [(x + 165, 750), (x + 165, 910)], PURPLE)
        label(d, (x + 165, 975), f"y{index}", 47, PURPLE)
        if index == 0:
            wire(d, [(60, 590), (x, 590)], INK)
            label(d, (110, 520), "p0=0", 30)
        if index < 3:
            wire(d, [(x + 330, 590), (x + 520, 590)], INK)
            label(d, (x + 425, 520), f"p{index + 1}", 35)
    label(d, (1100, 1100), "yi = xi AND NOT pi     p(i+1) = pi OR xi", 43, PURPLE)
    label(d, (1100, 1205), "x = 1110100       y = 0000100", 46, GREEN)
    phrase(d, (1100, 1310), "אפסים עוברים עד האחד הראשון; אחריו הקידומת חוסמת הכול", "Zeros pass until the first one; afterward the prefix blocks every higher bit", lang, 37)
    image.save(OUT / f"prep-107-low-prefix-chain-{lang}.png")


def truth_prompt(lang):
    image, d = canvas("טבלת האמת הנתונה בשאלה", "The truth table supplied in the question", lang, height=1450, width=1700)
    phrase(d, (850, 180), "כל שמונה הצירופים נתונים; אין מצבי לא־אכפת", "All eight assignments are specified; no don't-care rows", lang, 33)
    left, top, cell_w, cell_h = 270, 290, 290, 113
    rows = [("A", "B", "C", "Z")] + [tuple(f"{n:03b}") + (str(z),) for n, z in enumerate((0, 1, 0, 0, 1, 1, 0, 0))]
    for row_index, row in enumerate(rows):
        for col, value in enumerate(row):
            x, y = left + col * cell_w, top + row_index * cell_h
            d.rectangle((x, y, x + cell_w, y + cell_h), fill=PALE if row_index == 0 else BG,
                        outline=PURPLE, width=3)
            label(d, (x + cell_w // 2, y + cell_h // 2), value, 47)
    phrase(d, (850, 1380), "מצאו פונקציה ומימושים מזעריים לפי ספריית השערים", "Find the function and minimum circuits for each gate library", lang, 34)
    image.save(OUT / f"prep-109-prompt-truth-table-{lang}.png")


def named_gate(d, x, y, kind, left, right, out):
    box(d, (x + 180, y, x + 540, y + 190), kind)
    for offset, name in ((45, left), (145, right)):
        wire(d, [(x, y + offset), (x + 180, y + offset)], GREEN)
        label(d, (x + 65, y + offset - 45), name, 35, GREEN)
    wire(d, [(x + 540, y + 95), (x + 790, y + 95)], PURPLE)
    label(d, (x + 725, y + 40), out, 38, PURPLE)


def truth_circuits(lang):
    image, d = canvas("שתי ספריות שערים, שני גדלים שונים", "Two gate libraries, two different minimum sizes", lang, height=1770)
    label(d, (1100, 185), "Z = NOT B AND (A OR C)", 47, PURPLE)
    label(d, (1100, 300), "NAND: 4", 44)
    for x, y, a, b, out in ((180, 420, "B", "B", "nB"), (1180, 420, "A", "nB", "u"),
                             (180, 770, "C", "nB", "v"), (1180, 770, "u", "v", "Z")):
        named_gate(d, x, y, "NAND", a, b, out)
    label(d, (1100, 1110), "NOR: 2", 44)
    named_gate(d, 180, 1240, "NOR", "A", "C", "t")
    named_gate(d, 1180, 1240, "NOR", "B", "t", "Z")
    phrase(d, (1100, 1550), "תוויות זהות הן אותו חוט; מותר פיצול אות", "Matching labels name the same wire; fanout is allowed", lang, 39)
    phrase(d, (1100, 1660), "כל שער בעל שתי כניסות; גם מהפך מחיבור פינים נספר", "Every gate has two inputs; tied-pin inversion is counted too", lang, 36)
    image.save(OUT / f"prep-109-minimum-circuits-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        sr_latch(language)
        sr_edge_extension(language)
        low_mask(language)
        truth_prompt(language)
        truth_circuits(language)
