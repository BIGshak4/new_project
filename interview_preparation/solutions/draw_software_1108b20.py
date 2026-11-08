"""Original bilingual explanatory diagrams; no source-photo content copied."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"


def canvas(he, en, lang):
    image = Image.new("RGB", (3000, 1750), "white")
    draw = ImageDraw.Draw(image)
    phrase(draw, (1500, 130), he, en, lang, 59, bold=True)
    return image, draw


def cells(draw, values, y, colors=None, start=180, width=2640):
    step = width / len(values)
    for index, value in enumerate(values):
        x = start + index * step
        color = colors[index] if colors else BLUE
        box(draw, (x, y, x + step - 24, y + 180), color)
        text(draw, (x + (step - 24) / 2, y + 90), str(value), 61, color=color)


def save(image, number, lang):
    image.save(OUT / f"prep-{number:03d}-software-1108b20-{lang}.png")


def spaces(lang):
    image, d = canvas("שומרים רק תווים שאינם הרווח המוגדר", "Keep exactly the characters unequal to the specified space", lang)
    phrase(d, (1500, 350), "תווי הקלט לפי הסדר", "Input characters in order", lang, 49)
    cells(d, ["·", "a", "·", "b", "·", "·", "c", "·"], 500,
          [ORANGE, GREEN, ORANGE, GREEN, ORANGE, ORANGE, GREEN, ORANGE])
    text(d, (1500, 890), "· = U+0020", 60, color=ORANGE)
    wire(d, [(1500, 1020), (1500, 1170)])
    text(d, (1500, 1310), "abc", 88, color=GREEN)
    phrase(d, (1500, 1540), "טאב ושורה חדשה נשמרים לפי החוזה", "Tabs and newlines remain under this contract", lang, 48)
    save(image, 303, lang)


def cursor(lang):
    image, d = canvas("שתי מחסניות סביב האיבר הנוכחי", "Two stacks surround the current value", lang)
    text(d, (1500, 350), "[10, 20, 30]       current = 20", 65)
    phrase(d, (700, 570), "קודמים: הקרוב בראש", "Predecessors: nearest on top", lang, 47)
    phrase(d, (2180, 570), "נוכחי ובאים: הנוכחי בראש", "Current and successors: current on top", lang, 45)
    box(d, (400, 750, 1000, 950), BLUE)
    text(d, (700, 850), "10", 70, color=BLUE)
    box(d, (1880, 750, 2480, 950), GREEN)
    text(d, (2180, 850), "20", 70, color=GREEN)
    box(d, (1880, 980, 2480, 1180), BLUE)
    text(d, (2180, 1080), "30", 70, color=BLUE)
    wire(d, [(1800, 850), (1090, 850)])
    text(d, (1450, 760), "move_next", 54)
    text(d, (1500, 1380), "left(top first) = [20, 10]; right = [30]", 59)
    phrase(d, (1500, 1600), "נוגעים רק בראשי המחסניות ובמספר קבוע של ערכים", "Touch only stack tops and a constant number of values", lang, 47)
    save(image, 304, lang)


def queue(lang):
    image, d = canvas("העברה הופכת סדר ופותחת את הדרך לוותיק ביותר", "Transfer reverses order and exposes the oldest value", lang)
    text(d, (700, 370), "incoming", 64)
    text(d, (2300, 370), "outgoing", 64)
    for j, value in enumerate([3, 2, 1]):
        box(d, (400, 570 + j * 220, 1000, 750 + j * 220), BLUE)
        text(d, (700, 660 + j * 220), str(value), 66, color=BLUE)
    for j, value in enumerate([1, 2, 3]):
        box(d, (2000, 570 + j * 220, 2600, 750 + j * 220), GREEN if j == 0 else BLUE)
        text(d, (2300, 660 + j * 220), str(value), 66, color=GREEN if j == 0 else BLUE)
    wire(d, [(1130, 850), (1870, 850)])
    phrase(d, (1500, 640), "העברה רק כשהפלט ריק", "Transfer only when output is empty", lang, 40)
    text(d, (1500, 1290), "enqueue: O(1); dequeue/peek: O(n) worst, O(1) amortized", 49)
    phrase(d, (1500, 1510), "כל ערך חוצה מהקלט לפלט לכל היותר פעם אחת", "Each value crosses input to output at most once", lang, 49)
    save(image, 305, lang)


def java_stack(lang):
    image, d = canvas("הקידומת הפעילה היא המחסנית, לא המערך כולו", "The active prefix is the stack, not the entire array", lang)
    text(d, (1500, 360), "capacity = 5; size = 3; top = 9", 62)
    cells(d, [7, 7, 9, 0, 0], 610, [GREEN, GREEN, GREEN, BLUE, BLUE])
    wire(d, [(1485, 930), (1485, 820)])
    text(d, (1500, 1070), "pop() -> 9; size = 2; exists(9) -> false", 57)
    cells(d, [7, 7, 9, 0, 0], 1230, [GREEN, GREEN, BLUE, BLUE, BLUE])
    phrase(d, (1500, 1590), "ערך ישן בתא שהוצא אינו איבר פעיל", "An old value in a popped cell is not a live element", lang, 48)
    save(image, 309, lang)


def shuffle(lang):
    image, d = canvas("בחירה מהקידומת ומילוי המקום מהקצה", "Replace the selected value with the last active value", lang)
    phrase(d, (1500, 345), "דוגמה לימודית של חמישה ערכים", "Authored five-value teaching example", lang, 48)
    cells(d, [1, 2, 3, 4, 5], 530, [BLUE, ORANGE, BLUE, BLUE, GREEN])
    text(d, (1500, 840), "selected index = 1; output = 2", 62, color=ORANGE)
    wire(d, [(1500, 950), (1500, 1070)])
    cells(d, [1, 5, 3, 4, 5], 1180, [GREEN] * 4 + [BLUE])
    text(d, (1500, 1480), "remaining = 4; accepted raw count % remaining = 0", 52)
    phrase(d, (1500, 1630), "אחידות תלויה גם בהנחת מקור אקראי מתאים", "Uniformity also depends on the stated random-source assumption", lang, 44)
    save(image, 22, lang)


def multiply(lang):
    image, d = canvas("ניקוי בפעולות יחידה ואז חיבור חוזר", "Clear with unit operations, then repeat addition", lang)
    text(d, (1500, 370), "dirty R2 = 2 -> ADD R2 -> 3 -> SUM / JNZ -> 0", 58)
    phrase(d, (1500, 600), "אין פקודת איפוס מובנית", "There is no built-in CLEAR opcode", lang, 48)
    headers = ["k", "A", "B", "R2", "T"]
    cells(d, headers, 820)
    for row, values in enumerate([[0, 3, 2, 0, 0], [1, 3, 1, 3, 0], [2, 3, 0, 6, 0]]):
        for col, value in enumerate(values):
            text(d, (180 + col * 528 + 252, 1150 + row * 140), str(value), 61,
                 color=GREEN if col == 3 else BLUE)
    phrase(d, (1500, 1620), "הקפיצה בודקת אוגר מפורש; זמן הניקוי תלוי בערכו", "Branch on a named register; clearing cost depends on its initial value", lang, 44)
    save(image, 35, lang)


def division(lang):
    image, d = canvas("כל סבב מסיר מחלק אחד ושומר את המחלק", "Each round removes one divisor and preserves the divisor", lang)
    text(d, (1500, 350), "A0 = 12; B0 = 3; C0 = 0", 63)
    cells(d, ["round k", "A", "B", "C"], 570)
    for row, values in enumerate([[0, 12, 3, 0], [1, 9, 3, 1], [2, 6, 3, 2], [3, 3, 3, 3], [4, 0, 3, 4]]):
        for col, value in enumerate(values):
            text(d, (180 + col * 660 + 318, 880 + row * 120), str(value), 59,
                 color=GREEN if col == 3 else BLUE)
    text(d, (1500, 1530), "A = A0 - k*B0; B = B0; C = k; T = S = 0", 53)
    phrase(d, (1500, 1660), "חלוקה מדויקת ומחלק חיובי מונעים הקטנה מתחת לאפס", "Exact division and a positive divisor prevent decrementing below zero", lang, 43)
    save(image, 311, lang)


if __name__ == "__main__":
    for language in ("he", "en"):
        for draw in (spaces, cursor, queue, java_stack, shuffle, multiply, division):
            draw(language)
