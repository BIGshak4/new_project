"""Clean bilingual software illustrations, separate prompt/solution roles."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE = "#fffdf8", "#35234f", "#73558d"
GREEN, ORANGE, PALE = "#327568", "#ae592e", "#eee7f3"


def panel(draw, rect, color=PURPLE, fill=PALE):
    draw.rounded_rectangle(rect, radius=24, fill=fill, outline=color, width=5)


def canvas(he, en, lang, height=1650):
    image = Image.new("RGB", (2600, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1300, 100), he, en, lang, 62, bold=True, color=INK)
    return image, draw


def search(lang):
    image, draw = canvas("הראשון ששווה הוא גבול ולא פגיעה מקרית", "First equal means a boundary, not any match", lang)
    text(draw, (1300, 240), "target = 3", 58, bold=True, color=GREEN)
    for index, value in enumerate((1, 2, 2, 2, 3, 3, 3, 4)):
        x = 410 + index * 255
        color = GREEN if index == 4 else PURPLE
        panel(draw, (x - 105, 400, x + 105, 590), color=color,
              fill="#edf5ef" if index == 4 else PALE)
        text(draw, (x, 495), str(value), 67, bold=True, color=color)
        text(draw, (x, 675), str(index), 44)
    phrase(draw, (1300, 825), "משמאל לגבול כל הערכים קטנים מהמטרה", "Every value left of the boundary is below the target", lang, 46)
    panel(draw, (250, 940, 1260, 1150), color=ORANGE, fill="#fbf0e9")
    panel(draw, (1340, 940, 2350, 1150), color=GREEN, fill="#edf5ef")
    text(draw, (755, 1045), "a[i] < target", 59, bold=True, color=ORANGE)
    text(draw, (1845, 1045), "a[i] >= target", 59, bold=True, color=GREEN)
    text(draw, (1300, 1270), "lo = hi = 4     a[4] == 3     =>     return 4", 52, bold=True)
    phrase(draw, (1300, 1390), "אם הגבול בסוף או שהערך שונה אין הופעה", "Boundary at the end, or a different value, means absent", lang, 44)
    text(draw, (1300, 1500), "target = 5  =>  -1       target = 0  =>  -1", 49, bold=True)
    image.save(OUT / f"prep-137-lower-bound-first-equal-{lang}.png")


def binary(lang):
    image, draw = canvas("חלוקה בשתיים מגלה את הביט הנמוך", "Division by two reveals the low bit", lang)
    text(draw, (1300, 240), "unsigned value = 13", 57, bold=True)
    for x, he, en in ((550, "ערך", "Value"), (1300, "מנה", "Quotient"), (2050, "שארית", "Remainder")):
        phrase(draw, (x, 410), he, en, lang, 48, bold=True, color=PURPLE)
    for row, (value, quotient, remainder) in enumerate(((13, 6, 1), (6, 3, 0), (3, 1, 1), (1, 0, 1))):
        y = 590 + row * 180
        draw.line([(290, y + 80), (2310, y + 80)], fill="#d7cde1", width=3)
        for x, label in zip((550, 1300, 2050), (value, quotient, remainder), strict=True):
            text(draw, (x, y), str(label), 63, bold=True, color=GREEN if x == 2050 else INK)
    phrase(draw, (1300, 1290), "קוראים את השאריות מלמטה למעלה", "Read the remainders from bottom to top", lang, 47, bold=True)
    text(draw, (1300, 1400), "13  =>  \"1101\" + NUL", 60, bold=True, color=GREEN)
    phrase(draw, (1300, 1520), "חמישה תאים נדרשים בדוגמה זו כולל סיום המחרוזת", "This example needs five bytes, including the terminator", lang, 42)
    image.save(OUT / f"prep-138-unsigned-binary-text-{lang}.png")


def graph(draw, y):
    centers = [390 + index * 360 for index in range(6)]
    for index, x in enumerate(centers):
        panel(draw, (x - 105, y - 85, x + 105, y + 85))
        text(draw, (x, y), chr(ord("A") + index), 67, bold=True, color=PURPLE)
        if index < 5:
            wire(draw, [(x + 110, y), (centers[index + 1] - 115, y)], PURPLE, width=7)
    wire(draw, [(centers[5], y + 90), (centers[5], y + 260),
                (centers[2], y + 260), (centers[2], y + 95)], GREEN, width=7)
    text(draw, (180, y), "head", 41, bold=True)
    wire(draw, [(245, y), (centers[0] - 115, y)], PURPLE, width=6)


def cycle_prompt(lang):
    image, draw = canvas("רשימה מקושרת עם קישור חוזר", "A linked list with a returning link", lang, 1100)
    phrase(draw, (1300, 230), "כל תיבה היא צומת וכל חץ הוא קישור לצומת הבא", "Each box is a node and each arrow is its next link", lang, 47)
    graph(draw, 485)
    phrase(draw, (1300, 890), "האותיות הן שמות צמתים ולא ערכים להשוואה", "Letters identify nodes, not payload values to compare", lang, 46)
    phrase(draw, (1300, 1000), "זהו קלט לדוגמה הממחיש את השאלה", "This sample input illustrates the question", lang, 42)
    image.save(OUT / f"prep-141-linked-cycle-question-{lang}.png")


def cycle_solution(lang):
    image, draw = canvas("מהיר ואיטי נפגשים בתוך המעגל", "Fast and slow meet inside the cycle", lang, 1830)
    graph(draw, 345)
    for x, label in ((470, "step"), (1070, "slow"), (1830, "fast")):
        text(draw, (x, 760), label, 48, bold=True, color=PURPLE)
    for row, (slow, fast) in enumerate((('A', 'A'), ('B', 'C'), ('C', 'E'), ('D', 'C'), ('E', 'E'))):
        y = 900 + row * 120
        for x, label in zip((470, 1070, 1830), (str(row), slow, fast), strict=True):
            text(draw, (x, y), label, 53, bold=True, color=GREEN if row == 4 else INK)
    phrase(draw, (1300, 1510), "מפגש אינו חייב להיות בכניסה למעגל", "The meeting need not be the cycle entry", lang, 47, bold=True)
    text(draw, (1300, 1620), "entry phase:   (A, E) -> (B, F) -> (C, C)", 53, bold=True, color=GREEN)
    phrase(draw, (1300, 1740), "אחרי המפגש מחזירים מצביע אחד לראש ומקדמים יחד", "After meeting, reset one pointer to head and advance both", lang, 43)
    image.save(OUT / f"prep-141-floyd-meeting-entry-{lang}.png")


def minmax(lang):
    image, draw = canvas("שלוש השוואות לכל זוג נוסף", "Three comparisons for each additional pair", lang)
    for x, pair_values, low, high in ((550, "(8, 3)", 3, 8), (1300, "(5, 9)", 5, 9), (2050, "(4, 1)", 1, 4)):
        panel(draw, (x - 250, 330, x + 250, 500))
        text(draw, (x, 415), pair_values, 59, bold=True)
        wire(draw, [(x, 505), (x, 645)], PURPLE, width=7)
        text(draw, (x, 750), f"{low}       {high}", 60, bold=True, color=GREEN)
    phrase(draw, (1300, 240), "השוואה אחת בתוך כל זוג", "One comparison inside each pair", lang, 45)
    phrase(draw, (1300, 915), "מחפשים מינימום רק בין הקטנים ומקסימום רק בין הגדולים", "Find min among smaller values and max among larger values", lang, 43)
    panel(draw, (275, 1050, 1225, 1260), color=GREEN, fill="#edf5ef")
    panel(draw, (1375, 1050, 2325, 1260), color=GREEN, fill="#edf5ef")
    text(draw, (750, 1155), "min(3, 5, 1) = 1", 52, bold=True, color=GREEN)
    text(draw, (1850, 1155), "max(8, 9, 4) = 9", 52, bold=True, color=GREEN)
    text(draw, (1300, 1390), "N = 6:    3 + 2 + 2 = 7 comparisons", 55, bold=True)
    text(draw, (1300, 1510), "ceil(3N / 2) - 2", 63, bold=True, color=PURPLE)
    image.save(OUT / f"prep-142-pairwise-minmax-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        search(language)
        binary(language)
        cycle_prompt(language)
        cycle_solution(language)
        minmax(language)
