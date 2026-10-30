"""Authored bilingual diagrams for the second October30 software intake."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE = "#fffdf8", "#35234f", "#73558d"
GREEN, ORANGE, PALE = "#327568", "#ae592e", "#eee7f3"


def panel(draw, rect, color=PURPLE, fill=PALE):
    draw.rounded_rectangle(rect, radius=24, fill=fill, outline=color, width=5)


def canvas(he, en, lang, height=1750):
    image = Image.new("RGB", (2600, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1300, 100), he, en, lang, 62, bold=True, color=INK)
    return image, draw


def costumes(lang):
    image, draw = canvas("קודם מקבלים תחפושת מתאימה ואז משפרים דירוג", "First serve people, then improve preference rank", lang)
    phrase(draw, (1300, 235), "בדוגמה נמסרו ארבע שורות העדפה וחמש תחפושות", "The supplied example has four preference rows and five costumes", lang, 43)
    for x, he, en in ((480, "אדם", "Person"), (1180, "העדפות לפי סדר", "Ranked preferences"), (2050, "הקצאה", "Assignment")):
        phrase(draw, (x, 425), he, en, lang, 46, bold=True)
    for row, (choices, chosen) in enumerate((("a > b", "a"), ("c > a", "c"), ("d > e", "d"), ("d > b", "b")), 1):
        y = 620 + (row - 1) * 210
        color = ORANGE if row == 4 else GREEN
        text(draw, (480, y), f"P{row}", 60, bold=True, color=PURPLE)
        panel(draw, (840, y - 80, 1520, y + 80))
        text(draw, (1180, y), choices, 57, bold=True)
        wire(draw, [(1535, y), (1770, y)], color, width=7)
        panel(draw, (1810, y - 80, 2290, y + 80), color=color,
              fill="#fbf0e9" if row == 4 else "#edf5ef")
        text(draw, (2050, y), chosen, 69, bold=True, color=color)
    panel(draw, (330, 1410, 2270, 1580), color=GREEN, fill="#edf5ef")
    text(draw, (1300, 1495), "score = (served, first choices) = (4, 3)", 55, bold=True, color=GREEN)
    phrase(draw, (1300, 1680), "לשני אנשים אותה בחירה ראשונה ולכן ארבע בחירות ראשונות אינן אפשריות", "Two people share first choice d, so four first choices are impossible", lang, 40)
    image.save(OUT / f"prep-148-costume-lexicographic-assignment-{lang}.png")


def workers(lang):
    image, draw = canvas("מספר העובדים נקבע בשיא הביקוש המצטבר", "Headcount is the peak aggregate demand", lang)
    phrase(draw, (1300, 235), "ימים שלמים כולל שני הקצוות בדוגמה העליונה", "Upper example uses integer days with both endpoints included", lang, 44)
    x0, dx = 400, 350
    for day in range(1, 7):
        x = x0 + (day - 1) * dx
        text(draw, (x, 390), str(day), 47, bold=True)
    for y, start, end, demand in ((540, 1, 3, 6), (730, 2, 6, 7)):
        left, right = x0 + (start - 1) * dx, x0 + (end - 1) * dx
        draw.line([(left, y), (right, y)], fill=PURPLE, width=16)
        for x in (left, right):
            draw.ellipse((x - 17, y - 17, x + 17, y + 17), fill=PURPLE)
        text(draw, ((left + right) // 2, y - 65), f"demand = {demand}", 45, bold=True, color=PURPLE)
    for day, demand in enumerate((6, 13, 13, 7, 7, 7), 1):
        x = x0 + (day - 1) * dx
        top = 1220 - demand * 24
        draw.rounded_rectangle((x - 90, top, x + 90, 1220), radius=12,
                               fill=GREEN if demand == 13 else PALE, outline=GREEN, width=4)
        text(draw, (x, top - 45), str(demand), 44, bold=True, color=GREEN)
    text(draw, (1300, 1335), "minimum headcount = 13", 58, bold=True, color=GREEN)
    phrase(draw, (1300, 1460), "בקצוות נוגעים מוסכמת הזמן משנה את התשובה", "For touching endpoints, the time convention changes the answer", lang, 43)
    text(draw, (1300, 1570), "[1, 2]: 6  +  [2, 3]: 7   =>   13", 49, bold=True, color=ORANGE)
    text(draw, (1300, 1660), "[1, 2): 6  +  [2, 3): 7   =>    7", 49, bold=True, color=GREEN)
    image.save(OUT / f"prep-149-weighted-worker-demand-{lang}.png")


def matrix_grid(draw, source, x, y, *, original=False):
    for i, row in enumerate(source):
        for j, value in enumerate(row):
            cx, cy = x + j * 235, y + i * 225
            color = ORANGE if original and value == 0 else GREEN if value == 0 else PURPLE
            panel(draw, (cx - 90, cy - 80, cx + 90, cy + 80), color=color,
                  fill="#fbf0e9" if color == ORANGE else "#edf5ef" if color == GREEN else PALE)
            text(draw, (cx, cy), str(value), 58, bold=True, color=color)


def matrix(lang):
    image, draw = canvas("רק האפסים המקוריים קובעים מה יאופס", "Only original zeros decide what gets cleared", lang)
    phrase(draw, (715, 330), "קלט", "Input", lang, 51, bold=True)
    phrase(draw, (1890, 330), "תוצאה", "Result", lang, 51, bold=True)
    matrix_grid(draw, ((1, 2, 3, 4), (5, 0, 7, 8), (9, 10, 11, 12)), 360, 540, original=True)
    matrix_grid(draw, ((1, 0, 3, 4), (0, 0, 0, 0), (9, 0, 11, 12)), 1535, 540)
    wire(draw, [(1205, 770), (1360, 770)], GREEN, width=7)
    phrase(draw, (1300, 1170), "מסמנים שורות ועמודות לפני יצירת אפסים חדשים", "Mark affected rows and columns before creating new zeros", lang, 45)
    phrase(draw, (1300, 1290), "אפשר לשמור סימונים בשורה ובעמודה הראשונות", "The first row and column can store the markers", lang, 44)
    phrase(draw, (1300, 1395), "שני דגלים נפרדים זוכרים אם גם הן צריכות איפוס", "Two separate flags remember whether those also need clearing", lang, 42)
    text(draw, (1300, 1550), "[[0, 1], [1, 1]]   =>   [[0, 0], [0, 1]]", 51, bold=True, color=GREEN)
    phrase(draw, (1300, 1660), "האיבר האחרון נשאר אחת ולא ממשיכים שרשרת איפוסים", "The last value stays one: no cascade of newly created zeros", lang, 43)
    image.save(OUT / f"prep-150-original-zero-matrix-markers-{lang}.png")


def popcount(lang):
    image, draw = canvas("מחברים ספירות בקבוצות הולכות וגדלות", "Combine counts in progressively larger groups", lang)
    states = [("קלט", "Input", "11010110", "0xD6"),
              ("ספירה בכל זוג", "Count per pair", "10 | 01 | 01 | 01", "0x95"),
              ("ספירה בכל רביעייה", "Count per nibble", "0011 | 0010", "0x32"),
              ("ספירה בכל הבית", "Count per byte", "0101 = 5", "0x05")]
    for row, (he, en, bits, value) in enumerate(states):
        y = 410 + row * 280
        phrase(draw, (520, y), he, en, lang, 42, bold=True)
        panel(draw, (920, y - 90, 2250, y + 90), color=GREEN if row == 3 else PURPLE,
              fill="#edf5ef" if row == 3 else PALE)
        text(draw, (1585, y), bits, 57, bold=True, color=GREEN if row == 3 else PURPLE)
        text(draw, (2390, y), value, 43, bold=True)
        if row < 3:
            wire(draw, [(1585, y + 100), (1585, y + 175)], GREEN, width=7)
    text(draw, (1300, 1515), "table[0] = 0   table[214] = 5   table[255] = 8", 50, bold=True)
    phrase(draw, (1300, 1640), "גם לולאה של שמונה צעדים היא זמן קבוע בתחום של בית", "Even an eight-step loop is constant time on a fixed-byte domain", lang, 43)
    image.save(OUT / f"prep-151-byte-popcount-groups-{lang}.png")


def bits_row(draw, bits, y, color):
    for index, value in enumerate(bits):
        x = 560 + index * 245
        panel(draw, (x - 95, y - 90, x + 95, y + 90), color=color,
              fill="#edf5ef" if color == GREEN else PALE)
        text(draw, (x, y), value, 67, bold=True, color=color)


def reversal(lang):
    image, draw = canvas("הרוחב הנתון הוא חלק מהקלט", "The supplied width is part of the input", lang)
    text(draw, (1300, 235), "width = 7", 61, bold=True, color=PURPLE)
    bits_row(draw, "1100101", 460, PURPLE)
    phrase(draw, (1300, 690), "קוראים ביטים מהימין ומרכיבים את התוצאה משמאל", "Read from the right and build the reversed result", lang, 46)
    wire(draw, [(1300, 760), (1300, 885)], GREEN, width=8)
    bits_row(draw, "1010011", 1050, GREEN)
    text(draw, (1300, 1250), "reverse(101, 7) = 83", 60, bold=True, color=GREEN)
    text(draw, (1300, 1435), "reverse(1, 7) = 64     reverse(1, 8) = 128", 53, bold=True)
    phrase(draw, (1300, 1570), "לא עוצרים כשהערך שנותר מתאפס", "Do not stop merely because the remaining value reaches zero", lang, 44)
    phrase(draw, (1300, 1660), "אפסים מובילים עדיין שייכים לרוחב הייצוג", "Leading zeros still belong to the declared representation", lang, 43)
    image.save(OUT / f"prep-094-given-width-reversal-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        costumes(language)
        workers(language)
        matrix(language)
        popcount(language)
        reversal(language)
