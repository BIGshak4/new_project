"""Clean bilingual postfix traces and a neutral primitive-ISA prompt card."""
from pathlib import Path

from draw_prep_016_064 import phrase, text
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE = "#fffdf8", "#35234f", "#73558d"
GREEN, ORANGE, PALE = "#327568", "#ae592e", "#eee7f3"


def panel(draw, rect, color=PURPLE, fill=PALE):
    draw.rounded_rectangle(rect, radius=25, fill=fill, outline=color, width=5)


def canvas(height, he, en, lang):
    image = Image.new("RGB", (2600, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1300, 105), he, en, lang, 63, bold=True, color=INK)
    return image, draw


def postfix(lang):
    image, draw = canvas(1750, "ביטוי פוסטפיקס: מחסנית של תוצאות ביניים", "Postfix: a stack of intermediate results", lang)
    text(draw, (1300, 230), "3, 2, +, 5, +, 2, *     =>     ((3 + 2) + 5) * 2", 49, bold=True)
    phrase(draw, (1300, 325), "ראש המחסנית מימין; המצב מוצג אחרי כל טוקן", "Stack top is on the right; state follows each token", lang, 44)
    panel(draw, (250, 405, 2350, 1325), fill="#f7f4fa")
    headings = [(500, "שלב", "Step"), (900, "טוקן", "Token"), (1650, "מחסנית", "Stack")]
    for x, he, en in headings:
        phrase(draw, (x, 465), he, en, lang, 45, bold=True)
    states = ["[3]", "[3, 2]", "[5]", "[5, 5]", "[10]", "[10, 2]", "[20]"]
    for index, (token, stack) in enumerate(zip(("3", "2", "+", "5", "+", "2", "*"), states, strict=True), 1):
        yy = 530 + index * 105
        draw.line([(300, yy-55), (2300, yy-55)], fill="#d7cde1", width=2)
        text(draw, (500, yy), str(index), 44)
        text(draw, (900, yy), token, 55, bold=True)
        text(draw, (1650, yy), stack, 50, bold=True, color=GREEN if index==7 else INK)
    phrase(draw, (1300, 1410), "בחיסור חשוב להוציא ימין לפני שמאל", "For subtraction, pop right before left", lang, 48, bold=True)
    text(draw, (1300, 1510), "[3, 2]    right = 2    left = 3    =>    3 - 2 = 1", 49, color=ORANGE, bold=True)
    phrase(draw, (1300, 1635), "נדרשים שני אופרנדים לפעולה וערך יחיד בסוף", "Require two operands per operation and one final value", lang, 43)
    image.save(OUT / f"prep-123-postfix-stack-trace-{lang}.png")


def instruction_card(lang):
    image, draw = canvas(2100, "שפת אוגרים: ארבע פקודות בלבד", "Register language: four instructions only", lang)
    phrase(draw, (1300, 220), "כרטיס השאלה: פקודות, אתחול ושתי משימות", "Prompt card: instructions, initialization and two tasks", lang, 47)
    cards = [
        (200, 340, "INC REG", [("מגדילה אוגר ביחידה", "Increase a register by one")]),
        (1370, 340, "DEC REG", [("מקטינה אוגר ביחידה", "Decrease a register by one")]),
        (200, 720, "JNZ LABEL", [("קופצת אם תוצאת הפקודה החשבונית", "Branch if the immediately preceding"),
                                   ("שבוצעה מיד לפניה אינה אפס", "INC or DEC result is nonzero")]),
        (1370, 720, "HALT", [("מסיימת את התוכנית", "Stop the program")]),
    ]
    for x, y, command, lines in cards:
        panel(draw, (x, y, x+1030, y+300), color=PURPLE, fill="#f6f0fa")
        text(draw, (x+515, y+80), command, 61, bold=True, color=PURPLE)
        for row, (he, en) in enumerate(lines):
            phrase(draw, (x+515, y+170+row*70), he, en, lang, 40)
    panel(draw, (200, 1130, 2400, 1490), color=GREEN, fill="#edf5ef")
    phrase(draw, (1300, 1195), "כל תוכנית מתחילה מחדש", "Each program starts fresh", lang, 46, bold=True, color=GREEN)
    text(draw, (1300, 1290), "A, B, C, ... , Z", 50, bold=True)
    text(draw, (1300, 1385), "A = a >= 0       B = b >= 0       C..Z = 0", 50)
    phrase(draw, (1300, 1560), "אוגרים טבעיים ללא חסם; הפחתה מאפס אסורה", "Unbounded natural registers; decrement at zero is forbidden", lang, 43)
    panel(draw, (200, 1650, 1230, 1925), color=ORANGE, fill="#fbf0e9")
    phrase(draw, (715, 1715), "תוכנית א: מכפלה", "Program A: product", lang, 43, bold=True, color=ORANGE)
    text(draw, (715, 1835), "C = A0 * B0", 62, bold=True)
    panel(draw, (1370, 1650, 2400, 1925), color=ORANGE, fill="#fbf0e9")
    phrase(draw, (1885, 1715), "תוכנית ב: גודל הפרש", "Program B: absolute difference", lang, 40, bold=True, color=ORANGE)
    text(draw, (1885, 1835), "C = |A0 - B0|", 62, bold=True)
    phrase(draw, (1300, 1970), "הקלטים המסומנים באפס הם הערכים בתחילת הריצה", "A0 and B0 denote the initial input values", lang, 37)
    phrase(draw, (1300, 2060), "מותרות תוויות קוד; אין פקודות נוספות", "Code labels are allowed; no other instructions exist", lang, 39)
    image.save(OUT / f"prep-125-primitive-register-instructions-{lang}.png")


def table(draw, x, y, headings, rows, labels, lang):
    width = 1080
    panel(draw, (x, y, x+width, y+610), fill="#f7f4fa")
    centers = [x+410+i*170 for i in range(len(headings))]
    for cx, name in zip(centers, headings, strict=True):
        text(draw, (cx, y+70), name, 47, bold=True, color=PURPLE)
    for index, (values, (he, en)) in enumerate(zip(rows, labels, strict=True)):
        yy=y+180+index*120
        draw.line([(x+25, yy-55), (x+width-25, yy-55)], fill="#d7cde1", width=2)
        phrase(draw, (x+170, yy), he, en, lang, 33)
        for cx, value in zip(centers, values, strict=True):
            text(draw, (cx, yy), str(value), 49, bold=True, color=GREEN if index==len(rows)-1 else INK)


def solution_trace(lang):
    image, draw = canvas(2150, "שתי תוכניות נפרדות: עקבות ופקודות בקרה", "Separate programs: traces and control instructions", lang)
    phrase(draw, (1300, 220), "כל עקבה מתחילה מאתחול חדש", "Every trace begins from fresh initialization", lang, 46)
    phrase(draw, (700, 345), "מכפלה: שחזור בין סיבובים", "Product: restore between rounds", lang, 43, bold=True)
    phrase(draw, (1900, 345), "הפרש: מסירים זוגות", "Difference: remove pairs", lang, 43, bold=True)
    table(draw, 160, 430, ["A", "B", "D", "C"],
          [(3,2,0,0),(0,1,3,3),(3,1,0,3),(3,0,0,6)],
          [("התחלה", "Start"),("העברה", "Transfer"),("שחזור", "Restore"),("סיום", "Finish")], lang)
    table(draw, 1360, 430, ["A", "B", "C"],
          [(2,5,0),(1,4,0),(0,3,0),(0,0,3)],
          [("התחלה", "Start"),("זוג ראשון", "First pair"),("זוג שני", "Second pair"),("סיום", "Finish")], lang)
    text(draw, (700, 1130), "C = 3 * 2 = 6", 55, color=GREEN, bold=True)
    text(draw, (1900, 1130), "C = |2 - 5| = 3", 55, color=GREEN, bold=True)
    panel(draw, (160, 1240, 1240, 1850), fill="#f6f0fa")
    phrase(draw, (700, 1320), "בדיקת אפס בלי שינוי אוגר", "Zero probe without changing a register", lang, 40, bold=True)
    for index, line in enumerate(["INC R", "DEC R", "JNZ NONZERO"]):
        text(draw, (700, 1440+index*95), line, 53, bold=True, color=PURPLE)
    text(draw, (700, 1770), "R: 0 -> 1 -> 0   /   5 -> 6 -> 5", 39)
    panel(draw, (1360, 1240, 2440, 1850), fill="#f6f0fa")
    phrase(draw, (1900, 1320), "קפיצה שתמיד נלקחת", "An always-taken branch", lang, 42, bold=True)
    for index, line in enumerate(["INC Z", "DEC Z", "JNZ TARGET"]):
        text(draw, (1900, 1440+index*95), line, 53, bold=True, color=PURPLE)
    text(draw, (1900, 1770), "Z: 1 -> 2 -> 1", 44)
    phrase(draw, (1300, 1960), "האוגר לבקרה מקבל אחת בפקודה הראשונה בכל תוכנית", "The control register is set to one by each program's first instruction", lang, 43)
    text(draw, (1300, 2055), "Z = 0       INC Z       =>       Z = 1", 47, bold=True)
    image.save(OUT / f"prep-125-primitive-register-solution-trace-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        postfix(language)
        instruction_card(language)
        solution_trace(language)
