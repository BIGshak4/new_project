"""Clean bilingual software diagrams; all are protected solution illustrations."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, PURPLE, GREEN, ORANGE = "#fffdf8", "#73558d", "#327568", "#ae592e"


def card(draw, bounds, value, color=PURPLE, size=55):
    draw.rounded_rectangle(bounds, radius=24, fill="#edf5ef" if color == GREEN else "#eee7f3", outline=color, width=5)
    text(draw, ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2), value, size, bold=True, color=color)


def canvas(he, en, lang):
    im = Image.new("RGB", (2600, 1750), BG)
    draw = ImageDraw.Draw(im)
    phrase(draw, (1300, 105), he, en, lang, 59, bold=True)
    return im, draw


def sorter(lang):
    im, d = canvas("מחלקים לארבעה בלוקים ומשווים זוגות בלוקים", "Four half-capacity blocks, five compare-splits", lang)
    text(d, (1300, 250), "B0 | B1 | B2 | B3     m = 500", 52, bold=True)
    for row, label in enumerate(("S(B0, B1)    S(B2, B3)", "S(B0, B2)    S(B1, B3)", "S(B1, B2)")):
        y = 480 + row * 300
        card(d, (430, y - 95, 2170, y + 95), label)
        if row < 2:
            wire(d, [(1300, y + 110), (1300, y + 190)], GREEN, width=7)
    phrase(d, (1300, 1320), "חמש הפעלות: חמשת אלפים קריאות וחמשת אלפים כתיבות", "5 calls: 5000 reads + 5000 writes", lang, 50, bold=True, color=GREEN)
    phrase(d, (1300, 1460), "כל הפעלה ממיינת אלף ומחזירה שני חצאים לאותם בלוקים", "Each call sorts 1000 and writes two halves to the same blocks", lang, 42)
    phrase(d, (1300, 1580), "זהו חסם בנייה במודל מסוים ולא מינימום זיכרון ללא הנחות", "A construction in one model, not an unconditional I/O minimum", lang, 43)
    im.save(OUT / f"prep-160-capacity-compare-split-{lang}.png")


def elevator(lang):
    im, d = canvas("משימות קצרות וקו נסיעה ששומר על כיוון", "Short event handling and a LOOK sweep", lang)
    text(d, (1300, 250), "current = 4    requests = {2, 5, 7}    sweep = UP", 52, bold=True)
    for floor in range(1, 9):
        x = 400 + (floor - 1) * 255
        color = GREEN if floor in (2, 5, 7) else PURPLE
        card(d, (x - 95, 470, x + 95, 650), str(floor), color)
    text(d, (1300, 780), "4 -> 5 -> 7 -> 2", 68, bold=True, color=GREEN)
    card(d, (300, 940, 2300, 1120), "ISR: atomic_fetch_or(inbox, request_bit)", size=49)
    card(d, (300, 1240, 2300, 1420), "task: pending |= atomic_exchange(inbox, 0)", size=47)
    phrase(d, (1300, 1540), "המודל מחליט רק כשהמעלית מיושרת בקומה", "The model decides only at aligned landings", lang, 45)
    phrase(d, (1300, 1660), "בדיקות תוכנה אינן בדיקות בלימה דלתות או זמני פסיקה", "Software checks do not test braking, doors or interrupt deadlines", lang, 42)
    im.save(OUT / f"prep-161-elevator-request-sweep-{lang}.png")


def permutations(lang):
    im, d = canvas("סופרים תווים כדי לא להדפיס כפילויות", "Count characters to avoid duplicate visible outputs", lang)
    text(d, (1300, 260), "input = aab      counts = {a: 2, b: 1}", 56, bold=True)
    for x, value in ((650, "a"), (1950, "b")):
        card(d, (x - 280, 490, x + 280, 680), value)
    for x, value in ((500, "aa"), (1100, "ab"), (1950, "ba")):
        card(d, (x - 225, 930, x + 225, 1110), value)
    wire(d, [(650, 700), (500, 910)], GREEN, width=6)
    wire(d, [(650, 700), (1100, 910)], GREEN, width=6)
    wire(d, [(1950, 700), (1950, 910)], GREEN, width=6)
    for x, value in ((500, "aab"), (1100, "aba"), (1950, "baa")):
        wire(d, [(x, 1130), (x, 1230)], GREEN, width=6)
        card(d, (x - 225, 1260, x + 225, 1440), value, GREEN)
    phrase(d, (1300, 1570), "כל ענף משתמש בתו אחד ומחזיר אותו כשחוזרים לאחור", "Choose one character, then restore its count on backtracking", lang, 43)
    phrase(d, (1300, 1680), "שלוש תמורות שונות: קלט ריק נותן תמורה ריקה אחת", "3! / 2! = 3 outputs; empty input gives one empty output", lang, 45, bold=True)
    im.save(OUT / f"prep-162-multiset-permutation-tree-{lang}.png")


def longest(lang):
    im, d = canvas("שתי קידומות עם אותה שארית מגדירות קטע מתאים", "Equal prefix residues delimit a divisible interval", lang)
    text(d, (1300, 250), "input = [1, 2, 4, 5, 6, 7]", 58, bold=True)
    for row, label, values in ((0, "index", (-1, 0, 1, 2, 3, 4, 5)), (1, "prefix % 3", (0, 1, 0, 1, 0, 0, 1))):
        y = 510 + row * 300
        text(d, (280, y), label, 42, bold=True)
        for col, value in enumerate(values):
            x = 650 + col * 265
            card(d, (x - 95, y - 85, x + 95, y + 85), str(value), GREEN if col in (0, 5) else PURPLE)
    wire(d, [(650, 920), (650, 1050), (1975, 1050), (1975, 920)], GREEN, width=8)
    text(d, (1300, 1210), "end - earliest[0] = 4 - (-1) = 5", 59, bold=True, color=GREEN)
    text(d, (1300, 1370), "[1, 2, 4, 5, 6] => 18     [2, 4, 5, 6, 7] => 24", 50, bold=True)
    phrase(d, (1300, 1530), "לכל שארית שומרים רק את ההופעה הראשונה", "Retain only the earliest index for each residue", lang, 46)
    phrase(d, (1300, 1650), "בשוויון אורכים נבחרת ההתחלה המוקדמת", "Equal lengths choose the earlier start", lang, 44)
    im.save(OUT / f"prep-163-prefix-remainder-longest-{lang}.png")


def operators(lang):
    im, d = canvas("כל הספרות נשארות בסדר ורק פעולות מתווספות", "Digits stay in order; only operators are inserted", lang)
    text(d, (1300, 400), "1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 * 9", 72, bold=True)
    card(d, (300, 740, 1200, 1000), "1 + ... + 7 = 28", size=55)
    card(d, (1400, 740, 2300, 1000), "8 * 9 = 72", GREEN, 64)
    card(d, (650, 1230, 1950, 1450), "28 + 72 = 100", GREEN, 76)
    phrase(d, (1300, 1590), "כפל קודם לחיבור לפי מוסכמת החשבון הרגילה", "Multiplication precedes addition under ordinary precedence", lang, 46)
    phrase(d, (1300, 1690), "אין צורך בשרשור ספרות או בהכנסת סוגריים", "No concatenation or parentheses are needed", lang, 43)
    im.save(OUT / f"prep-164-insert-operators-witness-{lang}.png")


def stream(lang):
    im, d = canvas("תקינות מלאה של הקידומת אינה רק איזון הכמויות", "A valid whole prefix requires more than equal totals", lang)
    phrase(d, (1300, 245), "הזנה היא הוספה בסוף לפי סדר ההגעה", "Feed appends at the end in arrival order", lang, 46)
    for index, (symbol, valid) in enumerate(zip(("(", "a", ")", ")", "("), (0, 0, 1, 0, 0), strict=True)):
        x = 550 + index * 375
        card(d, (x - 120, 480, x + 120, 680), symbol)
        wire(d, [(x, 710), (x, 890)], GREEN, width=7)
        card(d, (x - 120, 920, x + 120, 1120), str(valid), GREEN if valid else PURPLE)
    text(d, (1300, 1300), "valid = (depth == 0) AND (NOT broken)", 58, bold=True, color=GREEN)
    phrase(d, (1300, 1450), "סגירה ללא פותח קודם היא שגיאה שאי אפשר לתקן בהמשך", "A close before any matching opener cannot be repaired by appending", lang, 43)
    phrase(d, (1300, 1570), "הסרת קלט מחייבת מידע חזרה ולא נכללת בממשק הזה", "Removing input needs rollback information and is not part of this API", lang, 42)
    im.save(OUT / f"prep-037-append-prefix-validity-{lang}.png")


def missing(lang):
    im, d = canvas("שני סכומים מספיקים למעבר יחיד על זרם", "Two exact moments suffice for one stream pass", lang)
    text(d, (1300, 260), "missing values: 37, 82", 57, bold=True)
    card(d, (300, 490, 2300, 690), "S = 5050 - observed_sum = 119", size=55)
    card(d, (300, 830, 2300, 1030), "Q = 338350 - observed_squares = 8093", size=51)
    text(d, (1300, 1200), "2Q - S*S = 2025 = 45*45", 65, bold=True, color=GREEN)
    text(d, (1300, 1390), "(119 - 45) / 2 = 37     (119 + 45) / 2 = 82", 53, bold=True)
    phrase(d, (1300, 1550), "שורש שלם מדויק בלי עיגול בנקודה צפה", "Use an exact integer square root, without floating rounding", lang, 46)
    phrase(d, (1300, 1670), "ההבטחה על טווח וייחוד ערכים נדרשת ואינה נבדקת במלואה", "Range and uniqueness are promises, not fully validated here", lang, 43)
    im.save(OUT / f"prep-041-one-pass-exact-moments-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        for render in (sorter, elevator, permutations, longest, operators, stream, missing):
            render(language)
