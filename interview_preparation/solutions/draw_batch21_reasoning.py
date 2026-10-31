"""Paired repository-native reasoning diagrams for the 31 October intake."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, GREEN, PALE, ORANGE = "#fffdf8", "#302344", "#624883", "#30766a", "#eee7f5", "#ad6c31"


def canvas(he, en, lang, height=1500):
    image = Image.new("RGB", (2400, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 85), he, en, lang, 55, color=INK, bold=True)
    return image, draw


def label(draw, xy, value, size=44, color=INK):
    text(draw, xy, value, size, color=color, bold=True)


def box(draw, rect):
    draw.rounded_rectangle(rect, 25, fill=PALE, outline=PURPLE, width=5)


def wolves(lang):
    image, draw = canvas("שבעה מצבים נגישים, אף יעד עם שלוש כבשים", "Seven reachable states; none has three sheep across", lang, 1600)
    phrase(draw, (1200, 190), "בדיוק שתיים הלוך ואחת חזור; זאבים ללא כבשים מותרים", "Exactly two forward and one back; wolf-only banks allowed", lang, 42)
    nodes = {"A": (300, 450, "0,0,L"), "B": (800, 330, "1,1,R"), "C": (800, 690, "2,0,R"),
             "D": (1300, 510, "1,0,L"), "E": (1870, 510, "3,0,R"),
             "F": (1870, 1000, "2,0,L"), "G": (1200, 1000, "2,2,R")}
    paths = [([(465, 410), (635, 355)], (545, 285), "WS"),
             ([(465, 510), (635, 640)], (505, 655), "WW"),
             ([(965, 360), (1135, 450)], (1100, 300), "S"),
             ([(965, 640), (1135, 565)], (1100, 740), "W"),
             ([(1465, 510), (1705, 510)], (1585, 420), "WW"),
             ([(1870, 595), (1870, 915)], (2010, 760), "W"),
             ([(1705, 1000), (1365, 1000)], (1530, 1080), "SS")]
    for points, at, group in paths:
        wire(draw, points, GREEN, width=7)
        label(draw, at, group, 43, GREEN)
    for name, (x, y, state) in nodes.items():
        box(draw, (x - 165, y - 85, x + 165, y + 85))
        label(draw, (x, y - 27), name, 39)
        label(draw, (x, y + 35), state, 43)
    phrase(draw, (1200, 1175), "אין חזרה חוקית של חיה אחת ממצב G", "State G has no legal one-animal return", lang, 44, color=ORANGE, bold=True)
    label(draw, (1200, 1300), "state = (W_far, S_far, boat_bank)", 44)
    phrase(draw, (1200, 1410), "W זאב; S כבשה; L התחלה; R יעד", "W wolf; S sheep; L initial bank; R far bank", lang, 42)
    phrase(draw, (1200, 1520), "הקבוצה סגורה לכל מעבר חוקי ולכן מוכיחה אי־אפשרות", "Closure under every legal move proves impossibility", lang, 43)
    image.save(OUT / f"prep-203-wolves-reachable-closure-{lang}.png")


def divisibility(lang):
    image, draw = canvas("התחלקות נקבעת לפי הסיביות הנמוכות", "Divisibility is determined by the low bits", lang)
    label(draw, (1200, 245), "n = 10100_2 = 20", 67)
    data = [(2, "0", "1", "1"), (4, "00", "3", "1"), (8, "100", "7", "0")]
    for index, (divisor, suffix, mask, result) in enumerate(data):
        left = 160 + 760 * index
        box(draw, (left, 390, left + 650, 1100))
        phrase(draw, (left + 325, 490), f"מחלק = {divisor}", f"Divisor = {divisor}", lang, 45, bold=True)
        label(draw, (left + 325, 680), suffix, 100, GREEN if result == "1" else ORANGE)
        label(draw, (left + 325, 860), f"(n & {mask}) == 0", 46)
        label(draw, (left + 325, 1000), f"D{divisor} = {result}", 62, GREEN if result == "1" else ORANGE)
    label(draw, (1200, 1245), "n = 2^k*q + r,    0 <= r < 2^k", 55)
    phrase(draw, (1200, 1380), "מתחלק אם ורק אם כל k הסיביות הנמוכות אפס", "Divisible exactly when all k low bits are zero", lang, 44)
    image.save(OUT / f"prep-206-binary-low-bit-masks-{lang}.png")


def arrays(lang):
    image, draw = canvas("מגדירים קודם אם הסדר חשוב ואם בוחרים את הכול", "First define whether order matters and every item is used", lang, 1550)
    label(draw, (1200, 235), "input = [A,B]", 63)
    for rect in ((180, 380, 1120, 1190), (1280, 380, 2220, 1190)):
        box(draw, rect)
    phrase(draw, (650, 470), "תמורות", "Permutations", lang, 56, color=GREEN, bold=True)
    phrase(draw, (1750, 470), "תתי־קבוצות מיקומים", "Positional subsets", lang, 52, color=GREEN, bold=True)
    for y, value in ((680, "[A,B]"), (880, "[B,A]")):
        label(draw, (650, y), value, 66)
    for y, value in ((640, "[]"), (780, "[A]"), (920, "[B]"), (1060, "[A,B]")):
        label(draw, (1750, y), value, 62)
    label(draw, (650, 1100), "2! = 2", 51, GREEN)
    label(draw, (1750, 1275), "2^2 = 4", 51, GREEN)
    label(draw, (1200, 1350), "[1,1,2]", 45)
    phrase(draw, (1200, 1440), "שלוש תמורות ושמונה תתי־קבוצות מיקומים", "Three permutations and eight positional subsets", lang, 42)
    image.save(OUT / f"prep-162-array-meanings-batch21-{lang}.png")


def error_window(lang):
    image, draw = canvas("בדיוק עשר שניות: הגבול משנה את ההחלטה", "Exactly ten seconds old: the endpoint changes the decision", lang, 1550)
    phrase(draw, (1200, 200), "זמני הדיווח בשניות: אפס, אחת, שתיים, שלוש ועשר", "Report times in seconds: zero, one, two, three and ten", lang, 43)
    left, right = 320, 2060
    for y, closed in ((520, False), (1030, True)):
        wire(draw, [(left - 110, y), (right + 120, y)], PURPLE, width=5)
        for time in (0, 1, 2, 3, 10):
            x = left + (right - left) * time / 10
            eligible = time > 0 or closed
            draw.ellipse((x - 24, y - 24, x + 24, y + 24), fill=GREEN if eligible else BG, outline=GREEN if eligible else ORANGE, width=6)
            label(draw, (x, y + 80), str(time), 43)
        label(draw, (1200, y - 140), "[0,10]" if closed else "(0,10]", 66, GREEN)
        phrase(draw, (1200, y + 185), "חמש בחלון: יוצאים" if closed else "רק ארבע בחלון: ממשיכים", "Five in window: exit" if closed else "Only four in window: continue", lang, 44, color=GREEN if closed else ORANGE, bold=True)
    phrase(draw, (1200, 1405), "שומרים לכל היותר את חמש חותמות השגיאה האחרונות", "Store at most the five most recent error timestamps", lang, 43)
    image.save(OUT / f"prep-081-time-window-batch21-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        for render in (wolves, divisibility, arrays, error_window):
            render(language)
