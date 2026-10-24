"""Original bilingual diagrams; Hebrew-only labels and separate LTR formulas."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, GREEN = "#17213a", "#345b9f", "#276858"
FONT = "C:/Windows/Fonts/arial.ttf"


def text(d, xy, value, size=32, he=False, color=INK):
    d.text(xy, value[::-1] if he else value, fill=color,
           font=ImageFont.truetype(FONT, size), anchor="mm")


def canvas(title, subtitle, he):
    image = Image.new("RGB", (2000, 1300), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (1000, 70), title, 46, he)
    text(draw, (1000, 150), subtitle, 30, he)
    return image, draw


def arrow(d, points):
    d.line(points, fill=BLUE, width=5)
    (a, b), (x, y) = points[-2:]
    if x > a:
        head = [(x, y), (x-17, y-10), (x-17, y+10)]
    elif x < a:
        head = [(x, y), (x+17, y-10), (x+17, y+10)]
    elif y > b:
        head = [(x, y), (x-10, y-17), (x+10, y-17)]
    else:
        head = [(x, y), (x-10, y+17), (x+10, y+17)]
    d.polygon(head, fill=BLUE)


def mux(d, x, y):
    d.rounded_rectangle((x, y, x+300, y+250), 18, fill="#f3f6fb", outline=BLUE, width=4)
    text(d, (x+150, y+110), "MUX 2:1", 36)
    text(d, (x+35, y+60), "0", 28)
    text(d, (x+35, y+190), "1", 28)
    text(d, (x+150, y+220), "S", 28)


for lang in ("he", "en"):
    he = lang == "he"
    img, d = canvas("החלפה בין תשע לשלוש עשרה באמצעות היפוך ביט" if he else
                    "Swap nine and thirteen by toggling one bit",
                    "פתרון מוצע — הקלט מובטח להיות אחד משני הערכים" if he else
                    "Proposed solution — the input is promised to be one of the two values", he)
    for row, (number, bits) in enumerate(((9, "1001"), (13, "1101"))):
        y = 400 + row*270
        text(d, (350, y), f"{number} =", 60)
        for i, value in enumerate(bits):
            x = 570 + i*250
            d.rounded_rectangle((x, y-90, x+170, y+90), 15,
                                fill="#fff0bd" if i == 1 else "#f3f6fb", outline=BLUE, width=4)
            text(d, (x+85, y), value, 75)
            if row == 0:
                text(d, (x+85, y-135), f"bit {3-i}", 30)
    arrow(d, [(1700, 415), (1780, 415), (1780, 655), (1700, 655)])
    text(d, (1000, 900), "mask = 0100 = 4", 48)
    text(d, (1000, 1005), "9 XOR 4 = 13;   13 XOR 4 = 9", 46)
    text(d, (1000, 1170), "אין השוואה ואין תנאי; שאר הביטים נשמרים" if he else
         "No comparison or conditional; the other bits are preserved", 34, he, GREEN)
    img.save(OUT/f"prep-119-toggle-bit-two-{lang}.png")

    img, d = canvas("מימוש שני המוצאים בעזרת שלושה מרבבים" if he else
                    "Implement both outputs with three MUXes",
                    "פתרון מוצע — קבועי אפס ואחד מותרים, אין היפוך כניסה חינמי" if he else
                    "Proposed solution — constants zero and one allowed; no free complemented input", he)
    mux(d, 300, 500)
    for y, value in ((560, "1"), (690, "0")):
        text(d, (140, y), value, 42)
        arrow(d, [(200, y), (300, y)])
    text(d, (450, 880), "B", 42)
    arrow(d, [(450, 835), (450, 750)])
    mux(d, 1100, 180)
    mux(d, 1100, 800)
    arrow(d, [(600, 625), (875, 625), (875, 370), (1100, 370)])
    arrow(d, [(875, 625), (875, 860), (1100, 860)])
    d.ellipse((866, 616, 884, 634), fill=BLUE)
    text(d, (770, 570), "t = NOT B", 32)
    for y, value in ((240, "1"), (990, "0")):
        text(d, (970, y), value, 40)
        arrow(d, [(1020, y), (1100, y)])
    for y in (430, 1050):
        arrow(d, [(1250, y+85), (1250, y)])
        text(d, (1250, y+125), "A", 40)
    for y, label in ((305, "Y_NAND"), (925, "Y_NOR")):
        arrow(d, [(1400, y), (1640, y)])
        text(d, (1790, y), label, 40)
    text(d, (1000, 1220), "MUX(S,D0,D1):  S=0 → D0;  S=1 → D1", 35)
    img.save(OUT/f"prep-120-shared-mux-inverter-{lang}.png")
print("Wrote four original bilingual solution PNGs.")
