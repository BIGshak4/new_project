"""Deterministic bilingual array/frontier figures; no source screenshot reuse."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN = "#35234f", "#73558d", "#327568"
PALE, BG, LINE = "#eee7f3", "#fffdf8", "#d9cfe3"


def canvas(he, en, lang):
    image = Image.new("RGB", (1800, 1100), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (900, 75), he, en, lang, 49, bold=True, color=INK)
    return image, draw


def matrix(lang):
    image, draw = canvas("סופרים לאורך גבול המדרגות", "Count along the staircase frontier", lang)
    phrase(draw, (900, 155), "השורות והעמודות בסדר עולה עם שוויון מותר", "Rows and columns are nondecreasing", lang, 36)
    values = [[-4, -2, 0, 3], [-3, -1, 2, 4], [-1, 1, 3, 6]]
    x0, y0, width, height = 390, 260, 240, 160
    for row, values_row in enumerate(values):
        for column, value in enumerate(values_row):
            x, y = x0 + column * width, y0 + row * height
            draw.rectangle((x, y, x + width, y + height), fill="#dcece7" if value < 0 else PALE,
                           outline=LINE, width=3)
            text(draw, (x + width / 2, y + height / 2), str(value), 56, color=INK, bold=True)
    # The counted portions contain three and then two entries, never overlap.
    draw.rounded_rectangle((397, 267, 623, 733), 12, outline=GREEN, width=7)
    draw.rounded_rectangle((637, 267, 863, 573), 12, outline=GREEN, width=7)
    text(draw, (510, 805), "+3", 53, color=GREEN, bold=True)
    text(draw, (750, 805), "+2", 53, color=GREEN, bold=True)
    text(draw, (1250, 805), "3 + 2 = 5", 51, color=PURPLE, bold=True)
    wire(draw, [(260, 660), (365, 660)], PURPLE, width=7)
    phrase(draw, (230, 590), "התחלה", "start", lang, 33, color=PURPLE)
    phrase(draw, (900, 930), "שלילי: סופרים את החלק העליון בעמודה ועוברים ימינה", "Negative: count the column portion above, then move right", lang, 37)
    phrase(draw, (900, 1000), "אפס או חיובי: עולים שורה בלי להוסיף לספירה", "Zero or positive: move up without adding to the count", lang, 37)
    image.save(OUT / f"prep-097-sorted_matrix_negatives-{lang}.png")


def triples(lang):
    image, draw = canvas("מקבעים ערך ומחפשים שני משלימים", "Fix one value and find its two complements", lang)
    phrase(draw, (900, 155), "עותק ממוין משאיר את הקלט המקורי ללא שינוי", "A sorted copy leaves the original input unchanged", lang, 36)
    values = [-4, -1, -1, 0, 1, 2]
    for index, value in enumerate(values):
        x = 320 + index * 190
        color = GREEN if index in (1, 2, 5) else PURPLE
        draw.rounded_rectangle((x, 315, x + 165, 445), 14, fill="#dcece7" if index in (1, 2, 5) else PALE,
                               outline=color, width=4)
        text(draw, (x + 82, 380), str(value), 55, color=INK, bold=True)
        text(draw, (x + 82, 275), str(index), 31, color=PURPLE)
        if index in (1, 2, 5):
            wire(draw, [(x + 82, 545), (x + 82, 460)], color, width=6)
            label = {1: "first", 2: "left", 5: "right"}[index]
            text(draw, (x + 82, 590), label, 35, color=color, bold=True)
    text(draw, (900, 720), "-1 + (-1) + 2 = 0", 54, color=GREEN, bold=True)
    phrase(draw, (900, 810), "שלושה אינדקסים שונים יכולים להחזיק ערכים שווים", "Three different indices may contain equal values", lang, 37)
    draw.line((240, 875, 1560, 875), fill=LINE, width=3)
    text(draw, (900, 920), "[0,0,0,0,0,0]", 39, color=PURPLE, bold=True)
    phrase(draw, (900, 985), "שלשת ערכים אחת לעומת עשרים שלשות אינדקסים", "One value triple versus twenty index triples", lang, 37, color=PURPLE, bold=True)
    phrase(draw, (900, 1055), "ייחודיות לפי ערכים היא הבהרה מפורשת של גרסת הפתרון", "Unique-value output is an explicit clarification of this edition", lang, 35)
    image.save(OUT / f"prep-101-unique_target_triples-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        matrix(language)
        triples(language)
