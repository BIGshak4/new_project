"""Clean native diagrams for six original explanations; paired Hebrew/English."""

from itertools import pairwise
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, PALE, GRAY = "#302344", "#624883", "#30766a", "#eee7f5", "#d8d1df"
BG = "#fffdf8"


def canvas(he, en, lang, height=1350):
    image = Image.new("RGB", (2400, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 90), he, en, lang, 55, color=INK, bold=True)
    return image, draw


def label(draw, xy, value, size=43, color=INK):
    text(draw, xy, value, size, color=color, bold=True)


def box(draw, rect, fill=PALE):
    draw.rounded_rectangle(rect, 25, fill=fill, outline=PURPLE, width=5)


def turtle(lang):
    image, draw = canvas("חזרה למיקום אינה דורשת חזרה לכיוון", "Returning to position does not require the initial heading", lang)
    for x in range(500, 1501, 250):
        draw.line((x, 280, x, 1080), fill=GRAY, width=2)
    for y in range(330, 1081, 250):
        draw.line((400, y, 1600, y), fill=GRAY, width=2)
    route = [(700, 530), (1200, 530), (1200, 1030), (700, 1030), (700, 530)]
    for start, end in pairwise(route):
        wire(draw, [start, end], PURPLE, width=10)
    draw.ellipse((682, 512, 718, 548), fill=GREEN)
    label(draw, (600, 450), "(0,0)", 48, GREEN)
    for at, value in [((950, 465), "M"), ((1300, 790), "M"), ((950, 1110), "M"), ((600, 790), "M")]:
        label(draw, at, value, 55)
    wire(draw, [(700, 530), (850, 530)], GREEN, width=7)
    wire(draw, [(700, 530), (700, 365)], GREEN, width=7)
    box(draw, (1700, 380, 2290, 1000))
    label(draw, (1995, 470), "MRMRMRM", 46)
    label(draw, (1995, 620), "x=0, y=0", 43)
    phrase(draw, (1995, 765), "מיקום זהה", "Same position", lang, 44, color=GREEN)
    phrase(draw, (1995, 895), "כיוון שונה", "Different heading", lang, 44)
    phrase(draw, (1200, 1240), "סופרים תזוזה בכל ציר ושומרים כיוון אחד מתוך ארבעה", "Accumulate both coordinates and keep one of four headings", lang, 43)
    image.save(OUT / f"prep-182-turtle-position-{lang}.png")


def cube(lang):
    image, draw = canvas("פותחים שתי פאות למלבן", "Unfold two faces into a rectangle", lang)
    left, top, side = 400, 340, 650
    draw.rectangle((left, top, left + 2 * side, top + side), fill=PALE, outline=PURPLE, width=6)
    for y in range(top, top + side, 35):
        draw.line((left + side, y, left + side, min(y + 18, top + side)), fill=PURPLE, width=4)
    wire(draw, [(left, top + side), (left + 2 * side, top)], GREEN, width=9)
    for (x, y), name in [((left, top + side), "A"), ((left + side, top + side / 2), "P"), ((left + 2 * side, top), "B")]:
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=GREEN)
        label(draw, (x - 40, y + 65), name, 48, GREEN)
    label(draw, (1050, 1070), "2a", 52)
    label(draw, (290, 665), "a", 52)
    label(draw, (1940, 540), "AP + PB", 45)
    label(draw, (1940, 670), "= a sqrt(5)", 48, GREEN)
    label(draw, (1940, 800), "P: a/2", 43)
    phrase(draw, (1200, 1200), "הקו המקווקו הוא קפל; הקו הירוק ישר בפריסה", "The dashed line is a fold; the green path is straight in the net", lang, 43)
    image.save(OUT / f"prep-183-cube-two-face-net-{lang}.png")


def random7(lang):
    image, draw = canvas("שתי הגרלות יוצרות עשרים וחמש אפשרויות", "Two draws create twenty-five equally likely possibilities", lang, 1550)
    left, top, cell = 600, 340, 180
    label(draw, (1050, 240), "second = 0,1,2,3,4", 42)
    for first in range(5):
        label(draw, (470, top + first * cell + cell / 2), str(first), 48)
        for second in range(5):
            value = 5 * first + second
            rect = (left + second * cell, top + first * cell, left + (second + 1) * cell, top + (first + 1) * cell)
            draw.rectangle(rect, fill=PALE if value < 21 else "#f8e5dc", outline=BG, width=6)
            center = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
            if value < 21:
                label(draw, center, str(value % 7), 43, GREEN)
            else:
                phrase(draw, center, "שוב", "retry", lang, 43, color="#a45e32", bold=True)
    label(draw, (1830, 560), "v = 5*first + second", 42)
    label(draw, (1830, 740), "v < 21: v % 7", 45, GREEN)
    label(draw, (1830, 920), "v >= 21", 43)
    phrase(draw, (1830, 1030), "מגרילים שוב", "draw again", lang, 43)
    phrase(draw, (1200, 1360), "לכל תשובה יש שלושה תאים מתקבלים", "Each output has three accepted cells", lang, 46)
    label(draw, (1200, 1460), "P(accept)=21/25     E[calls]=50/21", 43)
    image.save(OUT / f"prep-184-random5-grid-{lang}.png")


def seven(lang):
    image, draw = canvas("עוקבים רק אחרי הספרות שהשתנו", "Update only the decimal digits that changed", lang)
    values = [("69", "0", None), ("70", "1", "boom"), ("77", "2", "boom"), ("80", "0", None)]
    for index, (number, count, output) in enumerate(values):
        x = 100 + 575 * index
        box(draw, (x, 390, x + 475, 970))
        label(draw, (x + 237, 470), number, 75)
        label(draw, (x + 237, 650), f"count7={count}", 45)
        if output is None:
            phrase(draw, (x + 237, 850), "ללא פלט", "no output", lang, 47, color=GREEN)
        else:
            label(draw, (x + 237, 850), output, 55, GREEN)
        if index < 3:
            wire(draw, [(x + 475, 680), (x + 575, 680)], PURPLE, width=6)
    phrase(draw, (1200, 250), "מפיקים פלט רק אם יש ספרת שבע", "Emit output only when a digit seven occurs", lang, 43)
    phrase(draw, (1200, 1150), "מספר ללא ספרת שבע אינו מפיק פלט", "A number without a digit seven emits nothing", lang, 43)
    label(draw, (1200, 1250), "77 -> boom", 48)
    image.save(OUT / f"prep-185-digit-seven-state-{lang}.png")


def island(lang):
    image, draw = canvas("החוף הוא עוגן רק תחת הנחות גאומטריות מפורשות", "The coast is an anchor only under explicit geometric promises", lang)
    draw.rounded_rectangle((220, 290, 2150, 1030), 100, fill="#eff4e6", outline=GREEN, width=10)
    draw.ellipse((800, 370, 1420, 950), fill=PALE, outline=PURPLE, width=10)
    phrase(draw, (1110, 530), "גדר סגורה", "Closed fence", lang, 45, color=PURPLE)
    wire(draw, [(1080, 710), (2140, 710)], INK, width=7)
    draw.ellipse((1064, 694, 1096, 726), fill=PURPLE)
    draw.ellipse((1387, 694, 1419, 726), fill="#ad6c31")
    phrase(draw, (1620, 630), "חצייה אחת", "1 crossing", lang, 45)
    phrase(draw, (2260, 710), "ים", "sea", lang, 43, color=GREEN)
    phrase(draw, (1110, 830), "בתוך", "Inside", lang, 44)
    phrase(draw, (500, 480), "מחוץ", "Outside", lang, 44)
    phrase(draw, (1200, 1140), "אי ללא חורים; רצועת חישת הים ידועה כחיצונית", "Hole-free island; sea-detection strip is known outside", lang, 43)
    label(draw, (1200, 1250), "initial_inside = final_inside XOR crossing_parity", 43)
    image.save(OUT / f"prep-186-coast-anchor-parity-{lang}.png")


def reverse(lang):
    image, draw = canvas("אותו היפוך תווים בשני שלבים", "Reuse the same character reversal in two stages", lang, 1450)
    values = [("I am an engineer", "input"), ("reenigne na ma I", "reverse all"), ("engineer an am I", "reverse each word")]
    for index, (value, name) in enumerate(values):
        top = 300 + index * 330
        box(draw, (420, top, 1950, top + 210))
        label(draw, (1185, top + 110), value, 68, GREEN if index == 2 else INK)
        label(draw, (2050, top + 110), str(index), 49)
        if index < 2:
            wire(draw, [(1185, top + 210), (1185, top + 330)], PURPLE, width=7)
    phrase(draw, (1200, 180), "אחרי ההיפוך הראשון גם סדר המילים וגם התווים הפוכים", "The first reversal reverses both word order and each word's characters", lang, 43)
    label(draw, (1200, 1360), "reverse_range(buffer, left, right)", 47)
    image.save(OUT / f"prep-187-reverse-words-pipeline-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        for draw_diagram in (turtle, cube, random7, seven, island, reverse):
            draw_diagram(language)
