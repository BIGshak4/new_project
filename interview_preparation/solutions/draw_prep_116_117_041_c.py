"""Clean bilingual solution diagrams for the batch30 code questions."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE = "#fffdf8", "#35234f", "#73558d"
GREEN, ORANGE, PALE = "#327568", "#ae592e", "#eee7f3"


def panel(draw, rect, color=PURPLE, fill=PALE):
    draw.rounded_rectangle(rect, radius=25, fill=fill, outline=color, width=5)


def canvas(he, en, lang):
    image = Image.new("RGB", (2600, 1600), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1300, 100), he, en, lang, 66, bold=True, color=INK)
    return image, draw


def palindrome(lang):
    image, draw = canvas("פלינדרום: בודקים זוגות מבחוץ פנימה", "Palindrome: check symmetric pairs inward", lang)
    phrase(draw, (1300, 220), "השוואה מדויקת של אותיות ללא נרמול", "Exact letter comparison without normalization", lang, 50)
    centers = [500 + i * 320 for i in range(6)]
    for i, letter in enumerate("aBccBa"):
        cx = centers[i]
        panel(draw, (cx-115, 430, cx+115, 620), fill="#f7f4ec")
        text(draw, (cx, 520), letter, 82, bold=True)
        text(draw, (cx, 680), str(i), 42)
    for i, color in enumerate((PURPLE, GREEN, ORANGE)):
        x1, x2, yy = centers[i], centers[5-i], 310+i*35
        wire(draw, [(x1, 425), (x1, yy), (x2, yy), (x2, 425)], color, width=6)
    text(draw, (centers[0], 800), "left = 0", 47, bold=True, color=PURPLE)
    text(draw, (centers[-1], 800), "right = 5", 47, bold=True, color=PURPLE)
    wire(draw, [(620, 800), (970, 800)], PURPLE)
    wire(draw, [(1980, 800), (1630, 800)], PURPLE)
    phrase(draw, (1300, 920), "כל זוג שנבדק שווה; ממשיכים לזוג הבא", "Each checked pair matches; continue to the next pair", lang, 49)
    text(draw, (1300, 1020), "a = a       B = B       c = c       =>       true", 52, bold=True, color=GREEN)
    panel(draw, (220, 1130, 1230, 1390), color=ORANGE, fill="#fbf0e9")
    text(draw, (725, 1210), '"Aa"   =>   false', 55, bold=True, color=ORANGE)
    phrase(draw, (725, 1320), "אות גדולה וקטנה אינן זהות", "Uppercase and lowercase differ", lang, 42)
    panel(draw, (1370, 1130, 2380, 1390), color=GREEN, fill="#ecf5ef")
    text(draw, (1875, 1210), '""   =>   true', 55, bold=True, color=GREEN)
    phrase(draw, (1875, 1320), "בריקה אין זוג סותר", "Empty input has no unequal pair", lang, 42)
    phrase(draw, (1300, 1500), "הטווח כאן הוא אותיות בלבד; אין סינון תווים", "This edition allows letters only; no character filtering", lang, 43)
    image.save(OUT / f"prep-116-ascii_palindrome-{lang}.png")


def pool(lang):
    image, draw = canvas("רשימת פנויים בתוך התאים הפנויים", "A free list stored in free cells", lang)
    phrase(draw, (1300, 210), "תא מוקצה שומר את מלוא המטען של הלקוח", "An allocated slot preserves the client's entire payload", lang, 47)
    # A logical 32-bit external control word. The base pointer is supplied context.
    panel(draw, (250, 285, 2350, 420), color=PURPLE, fill="#f6f1fa")
    draw.line([(1890, 285), (1890, 420)], fill=PURPLE, width=5)
    phrase(draw, (1070, 350), "עשרים וחמישה ביטים לא מנוצלים", "25 unused bits", lang, 44)
    text(draw, (2120, 350), "head = 12", 46, bold=True)
    text(draw, (2120, 465), "7 bits: 0..64", 40, color=PURPLE)
    phrase(draw, (1300, 540), "מצב לדוגמה: רק שלושה תאים פנויים", "Example state: exactly three free slots", lang, 47)
    positions = [400, 1000, 1600]
    for cx, index, nxt in zip(positions, [12, 7, 3], [7, 3, 64], strict=True):
        panel(draw, (cx-190, 630, cx+190, 850), color=GREEN, fill="#ecf5ef")
        text(draw, (cx, 695), f"cell[{index}]", 46, bold=True, color=GREEN)
        text(draw, (cx, 790), f"next = {nxt}", 48)
    wire(draw, [(590, 740), (810, 740)], GREEN)
    wire(draw, [(1190, 740), (1410, 740)], GREEN)
    wire(draw, [(1790, 740), (2050, 740)], GREEN)
    panel(draw, (2050, 650, 2430, 830), color=ORANGE, fill="#fbf0e9")
    text(draw, (2240, 715), "NIL = 64", 46, bold=True, color=ORANGE)
    phrase(draw, (2240, 785), "לא תא זיכרון", "Not a slot", lang, 34)
    panel(draw, (330, 930, 2270, 1075), color=PURPLE, fill="#f6f1fa")
    phrase(draw, (750, 970), "תא מוקצה", "Allocated slot", lang, 39, bold=True, color=PURPLE)
    text(draw, (750, 1030), "cell[9]", 39, bold=True, color=PURPLE)
    text(draw, (1750, 1000), "payload = 0xffffffffffffffff", 46, bold=True)
    panel(draw, (190, 1160, 1260, 1450), color=GREEN, fill="#ecf5ef")
    text(draw, (725, 1225), "1. malloc() => 12", 48, bold=True, color=GREEN)
    text(draw, (725, 1310), "head = 7      7 -> 3 -> 64", 45)
    phrase(draw, (725, 1390), "מטען כל תא מוקצה אחר נשמר", "Every other allocated payload is preserved", lang, 36)
    panel(draw, (1340, 1160, 2410, 1450), color=ORANGE, fill="#fbf0e9")
    text(draw, (1875, 1225), "2. free(9)", 48, bold=True, color=ORANGE)
    text(draw, (1875, 1310), "cell[9] = 7; head = 9", 45)
    text(draw, (1875, 1390), "9 -> 7 -> 3 -> 64", 45)
    phrase(draw, (1300, 1530), "מותר לשחרר רק תא שמוקצה כעת", "Release only a currently allocated slot", lang, 43)
    image.save(OUT / f"prep-117-pool64_inband_free_list-{lang}.png")


def missing(lang):
    image, draw = canvas("המספר החסר בטווח שמתחיל באפס", "The missing value in a zero-based range", lang)
    text(draw, (1300, 230), "values = [3, 0, 1]       n = 3       domain = 0..3", 51, bold=True)
    phrase(draw, (1300, 360), "עם דגלים: מסמנים לפי הערך שקראנו", "With flags: mark by the observed value", lang, 49)
    for value in range(4):
        cx = 650+value*430
        missing_value = value == 2
        color = ORANGE if missing_value else GREEN
        panel(draw, (cx-165, 470, cx+165, 730), color=color, fill="#fbf0e9" if missing_value else "#ecf5ef")
        text(draw, (cx, 535), f"seen[{value}]", 48, bold=True)
        text(draw, (cx, 650), "False" if missing_value else "True", 55, bold=True, color=color)
    phrase(draw, (1300, 820), "בודקים גם את אפס וגם את הקצה העליון", "Scan zero as well as the upper endpoint", lang, 48)
    phrase(draw, (1300, 970), "בלי מערך עזר: כל זוג זהה מתבטל", "Without auxiliary array: equal pairs cancel", lang, 49)
    text(draw, (1300, 1090), "(0 XOR 1 XOR 2 XOR 3) XOR (3 XOR 0 XOR 1)", 49, bold=True)
    text(draw, (1300, 1200), "(0 XOR 0) XOR (1 XOR 1) XOR (3 XOR 3) XOR 2", 48)
    text(draw, (1300, 1310), "0 XOR 0 XOR 0 XOR 2 = 2", 57, bold=True, color=ORANGE)
    phrase(draw, (1300, 1450), "הקלט נשאר ללא שינוי; המספרים השונים והטווח מובטחים", "Input is unchanged; distinctness and range are promises", lang, 43)
    text(draw, (1300, 1540), "n = 0:  []  =>  0", 44, color=PURPLE)
    image.save(OUT / f"prep-041-c-zero-based-one-missing-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        palindrome(language)
        pool(language)
        missing(language)
