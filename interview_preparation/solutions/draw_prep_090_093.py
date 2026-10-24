"""Clean bilingual diagrams for the ideal rope and equal-partition models."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from prep_093_equal_partitions import partitions, region_polygons

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, MUTED, PALE = "#35234f", "#73558d", "#756781", "#e7def0"
COLORS = ["#e5daef", "#c9b5dc", "#b3c9ca", "#e6d8b8", "#d7c6dd", "#c6d2e4", "#ddd2bd"]


def label(draw, position, value, size=40, hebrew=False, bold=False, color=INK):
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
    draw.text(position, value[::-1] if hebrew else value, font=font, fill=color, anchor="mm")


def local(draw, position, language, he, en, size=40, bold=False, color=INK):
    label(draw, position, he if language == "he" else en, size, language == "he", bold, color)


def arrow(draw, start, end):
    draw.line((start, end), fill=PURPLE, width=4)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    draw.polygon([end] + [(end[0] - 15 * math.cos(angle + d), end[1] - 15 * math.sin(angle + d))
                         for d in [-0.45, 0.45]], fill=PURPLE)


def rope(language, solution=False):
    image = Image.new("RGB", (1600, 1100), "#fffdf8")
    draw = ImageDraw.Draw(image)
    local(draw, (800, 70), language, "חבל סביב כדור הארץ", "A rope around the Earth", 56, True)
    local(draw, (800, 145), language, "מודל מעגלי אידאלי; השרטוט אינו בקנה מידה", "Ideal circular model; diagram not to scale", 37, color=MUTED)
    cx, cy, r, gap = 475, 610, 245, 75
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill="#eee8e1", outline=INK, width=5)
    draw.ellipse((cx-r-gap, cy-r-gap, cx+r+gap, cy+r+gap), outline=PURPLE, width=6)
    arrow(draw, (cx, cy), (cx+r, cy))
    label(draw, (cx+100, cy-30), "R", 44, bold=True)
    arrow(draw, (cx+r, cy), (cx+r+gap, cy))
    label(draw, (cx+r+gap/2, cy-35), "h", 40, bold=True)
    draw.ellipse((cx-6, cy-6, cx+6, cy+6), fill=INK)
    local(draw, (1170, 320), language, "מוסיפים לחבל עשרה מטרים", "Add ten metres to the rope", 39, True)
    label(draw, (1170, 410), "L0 = 2πR", 49)
    label(draw, (1170, 490), "L1 = L0 + 10 m", 49)
    local(draw, (1170, 590), language, "מרווח אחיד מכל הצדדים", "Uniform gap all around", 37, color=MUTED)
    if solution:
        label(draw, (1170, 700), "2πh = 10 m", 50, color=PURPLE, bold=True)
        label(draw, (1170, 790), "h ≈ 1.59 m", 54, color=PURPLE, bold=True)
        local(draw, (800, 1000), language, "המרווח תלוי בתוספת האורך בלבד", "The gap depends only on the added length", 42, True)
    else:
        local(draw, (1170, 740), language, "האם יש מקום לאדם?", "Is there room for a person?", 39, True)
        label(draw, (1170, 820), "height = 1 m", 45)
        local(draw, (800, 1000), language, "החבל החדש הוא מעגל באותו מרכז", "The new rope forms a circle with the same center", 39)
    image.save(OUT / f"prep-090-{'clearance' if solution else 'rope'}-{language}.png")


def shapes(language, solution=False):
    image = Image.new("RGB", (1600, 1230), "#fffdf8")
    draw = ImageDraw.Draw(image)
    local(draw, (800, 65), language, "חלוקת השטחים הלבנים", "Partition the white regions", 56, True)
    local(draw, (800, 140), language, "הוספנו מודל מדויק של משבצות שוות", "Added model: equal unit cells on an ideal grid", 38, color=MUTED)
    x0, y0, unit = 105, 275, 190

    def point(p):
        return (int(x0 + float(p[0]) * unit), int(y0 + float(p[1]) * unit))

    draw.rectangle((x0, y0, x0 + 4*unit, y0 + 4*unit), fill=INK)
    if solution:
        for pieces in partitions().values():
            for i, piece in enumerate(pieces):
                vertices = [point(p) for p in piece]
                draw.polygon(vertices, fill=COLORS[i % len(COLORS)])
                draw.line(vertices + [vertices[0]], fill=INK, width=4, joint="curve")
    else:
        for polygon in region_polygons().values():
            vertices = [point(p) for p in polygon]
            draw.polygon(vertices, fill="#fffdf8")
            draw.line(vertices + [vertices[0]], fill=INK, width=5, joint="curve")
    # Dimension numbers are model units, not measurements of the photograph.
    for i in range(5):
        label(draw, (x0 + i*unit, y0-38), str(i), 32, color=MUTED)
        label(draw, (x0-35, y0+i*unit), str(i), 32, color=MUTED)
    for name, p in {"A": (2.45, .35), "B": (.45, .45), "C": (.4, 3.55), "D": (3.55, 3.55)}.items():
        px, py = point(p)
        draw.ellipse((px-28, py-28, px+28, py+28), fill="#fffdf8", outline=PURPLE, width=2)
        label(draw, (px, py), name, 37, bold=True)
    label(draw, (1200, 320), "A → 2     B → 3", 46, bold=True)
    label(draw, (1200, 395), "C → 4     D → 7", 46, bold=True)
    if solution:
        local(draw, (1200, 530), language, "שטח כל חלק באזור שלו", "Area of each piece in its region", 34, True)
        for i, text in enumerate(["A: 3/2", "B: 1", "C: 3/4", "D: 4/7"]):
            label(draw, (1200, 610 + i*80), text, 45)
        local(draw, (800, 1125), language, "בכל אזור: החלקים שווי שטח וגם חופפים", "Within each region: equal area and congruent", 42, True)
    else:
        local(draw, (1200, 560), language, "כל אזור מחולק בנפרד", "Partition each region separately", 35)
        local(draw, (1200, 650), language, "השטח השחור אינו נכלל", "The dark area is excluded", 35)
        local(draw, (1200, 740), language, "נדרשים חלקים שווי שטח", "Pieces must have equal area", 35)
        local(draw, (800, 1125), language, "המקור אינו מציין מידות; זו הנחת מודל גלויה", "Source dimensions are unspecified; this model is explicit", 38, True)
    image.save(OUT / f"prep-093-{'partitions' if solution else 'regions'}-{language}.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for language in ["he", "en"]:
        rope(language)
        rope(language, True)
        shapes(language)
        shapes(language, True)
