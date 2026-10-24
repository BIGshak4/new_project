"""Localized cursor diagram for the stable, read-only sorted-array merge."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0"


def row(draw, x, y, values, active, color):
    for index, value in enumerate(values):
        left = x + 170 * index
        fill = PALE if index < active else PAPER
        if index == active:
            fill = "#eee7f4" if color == PURPLE else "#e6f0eb"
        draw.rounded_rectangle((left, y, left + 140, y + 115), 14,
                               fill=fill, outline=color if index >= active else "#c8c1cb",
                               width=6 if index == active else 3)
        text(draw, (left + 70, y + 57), str(value), 51, color=color, bold=index == active)
        text(draw, (left + 70, y - 35), str(index), 29, color=INK)


def diagram(language):
    image = Image.new("RGB", (1800, 1230), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (900, 75), "משווים רק את שני האיברים שטרם נצרכו",
           "Compare only the two current unread items", language, 49, bold=True, color=INK)
    phrase(draw, (900, 160), "דוגמה שנוספה להסבר — מצב לפני הצעד השלישי",
           "Added worked example — before output item three", language, 35)
    row(draw, 270, 335, [1, 4, 4], 1, PURPLE)
    row(draw, 1030, 335, [2, 4, 7], 1, GREEN)
    text(draw, (500, 250), "left", 45, color=PURPLE, bold=True)
    text(draw, (1260, 250), "right", 45, color=GREEN, bold=True)
    text(draw, (510, 500), "i = 1", 43, color=PURPLE, bold=True)
    text(draw, (1270, 500), "j = 1", 43, color=GREEN, bold=True)
    phrase(draw, (900, 605), "שוויון: בוחרים משמאל ומקדמים רק אותו",
           "Tie: take left and advance only its cursor", language, 39, bold=True, color=PURPLE)
    text(draw, (500, 740), "output = [1, 2]", 45, bold=True)
    wire(draw, [(835, 740), (990, 740)], PURPLE, 5)
    text(draw, (1310, 740), "[1, 2, 4]", 45, color=PURPLE, bold=True)
    text(draw, (900, 845), "next: i = 2, j = 1", 40, color=PURPLE)
    phrase(draw, (900, 950), "הארבע מימין עדיין מחכה — אין למחוק כפילויות",
           "The right-hand four still waits — never discard duplicates", language, 35)
    text(draw, (900, 1050), "final = [1, 2, 4, 4, 4, 7]", 46, bold=True, color=INK)
    phrase(draw, (900, 1150), "האפור כבר הועתק לפלט; שני מערכי הקלט נשארים ללא שינוי",
           "Grey items are already copied; neither input array changes", language, 34)
    image.save(OUT / f"prep-098-merge-cursors-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        diagram(lang)
