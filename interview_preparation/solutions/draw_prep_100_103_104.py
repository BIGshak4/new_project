"""Reproducible bilingual logical schematics and timing explanation figures."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, PALE = "#302344", "#5d4383", "#33786d", "#e7def0"


def canvas(he, en, lang, width=2200, height=1500):
    im = Image.new("RGB", (width, height), "#fffdf8")
    d = ImageDraw.Draw(im)
    phrase(d, (width // 2, 80), he, en, lang, 53, bold=True, color=INK)
    return im, d


def label(d, point, value, size=39, color=INK):
    text(d, point, value, size, bold=True, color=color)


def box(d, rect):
    d.rounded_rectangle(rect, 20, fill="#f8f4e9", outline=PURPLE, width=5)


def times_six(lang):
    im, d = canvas("כפל פי שש באמצעות שמונה מחברים מלאים", "Times six using eight full adders", lang, height=2060)
    phrase(d, (1100, 175), "הזזות הן חיווט; התוצאה המלאה היא בת אחת־עשרה סיביות", "Shifts are wiring; retain the full eleven-bit result", lang, 38)
    label(d, (450, 270), "6x = (x << 1) + (x << 2)", 42, PURPLE)
    label(d, (1760, 270), "y0=0     y1=a0", 44, GREEN)
    for i in range(8):
        y = 370 + i * 170
        column = i + 2
        box(d, (900, y, 1300, y + 120))
        label(d, (1100, y + 58), f"FA{i}", 43)
        first = f"a{i + 1}" if i < 7 else "0"
        second = f"a{i}"
        wire(d, [(420, y + 30), (900, y + 30)], GREEN)
        wire(d, [(420, y + 90), (900, y + 90)], GREEN)
        label(d, (320, y + 30), first, 38, GREEN)
        label(d, (320, y + 90), second, 38, GREEN)
        wire(d, [(1300, y + 60), (1900, y + 60)], PURPLE)
        label(d, (1940, y + 60), f"y{column}", 40, PURPLE)
        if i == 0:
            wire(d, [(1100, y - 55), (1100, y)], INK)
            label(d, (1360, y - 30), "carry in = 0", 32)
        if i < 7:
            wire(d, [(1100, y + 120), (1100, y + 170)], INK)
            label(d, (1460, y + 145), f"carry -> weight 2^{column + 1}", 29)
        else:
            wire(d, [(1100, y + 120), (1100, y + 220), (1900, y + 220)], INK)
            label(d, (1940, y + 220), "y10", 40)
    phrase(d, (1100, 1900), "בכל שורה משקל הנשא היוצא כפול ממשקל הסכום", "Each outgoing carry has twice the sum bit's weight", lang, 38)
    phrase(d, (1100, 1980), "מודל לוגי; לא נטען שזהו מספר המחברים המזערי", "Logical construction; no minimum-adder claim", lang, 36)
    im.save(OUT / f"prep-100-eight-fa-circuit-{lang}.png")


def dff_tff(lang):
    im, d = canvas("מחליפים מצב רק כשהנתון החדש שונה", "Toggle only when new data differs", lang, height=1360)
    phrase(d, (1100, 175), "אותו שעון בחזית עולה; המשוב הוא נתיב נתונים", "Same rising-edge clock; feedback is a data path", lang, 39)
    d.ellipse((670, 485, 850, 715), fill="#f8f4e9", outline=PURPLE, width=5)
    label(d, (760, 600), "XOR", 43)
    box(d, (1110, 440, 1560, 830))
    label(d, (1335, 530), "TFF", 58)
    label(d, (1150, 600), "T", 38)
    label(d, (1515, 600), "Q", 38)
    wire(d, [(160, 550), (670, 550)], GREEN)
    label(d, (220, 480), "D", 55, GREEN)
    wire(d, [(850, 600), (1110, 600)], PURPLE)
    label(d, (980, 520), "T = D XOR Q", 32, PURPLE)
    wire(d, [(1560, 600), (2020, 600)], PURPLE)
    label(d, (1970, 520), "Q", 55, PURPLE)
    d.ellipse((1770, 590, 1790, 610), fill=PURPLE)
    wire(d, [(1780, 600), (1780, 1000), (430, 1000), (430, 650), (670, 650)], PURPLE)
    wire(d, [(1335, 310), (1335, 440)], INK)
    d.polygon([(1310, 440), (1360, 440), (1335, 485)], outline=INK, width=4)
    label(d, (1335, 265), "clk", 44)
    label(d, (1100, 1130), "Q(next) = Q XOR (D XOR Q) = D", 44, PURPLE)
    phrase(d, (1100, 1230), "מתאים רק לרכיב T דוגם ולתנאי תזמון תקינים", "Requires an edge-triggered T primitive and valid timing", lang, 39)
    im.save(OUT / f"prep-103-tff-feedback-circuit-{lang}.png")


def pipeline_prompt(lang):
    im, d = canvas("שלושה פליפ־פלופים החולקים שעון אחד", "Three flip-flops sharing one clock", lang, height=1390)
    phrase(d, (1100, 175), "הקלט עולה לפני החזית הראשונה ומגיע יציב; שלוש הדרגות מתחילות באפס", "Input rises before edge one and is stable; all three stages start at zero", lang, 35)
    for index, x in enumerate((450, 1000, 1550), 1):
        box(d, (x, 300, x + 330, 540))
        label(d, (x + 165, 395), f"DFF {index}", 44)
        wire(d, [(x + 165, 650), (x + 165, 540)], INK)
        d.polygon([(x + 143, 540), (x + 187, 540), (x + 165, 500)], outline=INK, width=4)
        if index < 3:
            wire(d, [(x + 330, 420), (x + 550, 420)], PURPLE)
    wire(d, [(160, 420), (450, 420)], GREEN)
    label(d, (240, 345), "x", 49, GREEN)
    wire(d, [(1880, 420), (2090, 420)], PURPLE)
    label(d, (2020, 345), "out", 49, PURPLE)
    d.line((615, 650, 1715, 650), fill=INK, width=5)
    for x in (615, 1165, 1715):
        d.ellipse((x - 8, 642, x + 8, 658), fill=INK)
    label(d, (1100, 715), "one common rising-edge clk", 40)
    for row, edge in enumerate((1, 2, 3), 1):
        y = 800 + row * 95
        label(d, (600, y), f"edge {edge}", 41)
        label(d, (1140, y), "Q1 Q2 Q3 = ? ? ?", 44, PURPLE)
    phrase(d, (1100, 1230), "תצפית חריגה: המוצא עולה בחזית השנייה או ברביעית", "Unexpected observation: output rises at edge two or four", lang, 39)
    phrase(d, (1100, 1320), "האם התצפית לבדה מספיקה לאבחן את הסיבה?", "Does that observation alone identify the cause?", lang, 38)
    im.save(OUT / f"prep-104-prompt-pipeline-{lang}.png")


def timing_constraints(lang):
    im, d = canvas("שני חלונות תזמון שונים", "Two different timing windows", lang, height=1440)
    label(d, (1100, 180), "skew = capture clock arrival - launch clock arrival", 35)
    for rect, title_he, title_en, equation, explanation_he, explanation_en in (
        ((140, 290, 2060, 660), "זמן הכנה: להגיע לפני החזית הבאה", "Setup: arrive before the next capture edge",
         "tCQ(max) + tPD(max) + tSetup <= T + skew",
         "מסלול מרבי איטי עלול להחמיץ את הדגימה המיועדת", "A slow maximum-delay path may miss its intended capture"),
        ((140, 760, 2060, 1130), "זמן החזקה: לא להשתנות מוקדם מדי", "Hold: do not change too early",
         "tCQ(min) + tCD(min) >= skew + tHold",
         "מסלול מזערי מהיר עלול לפגוע בערך הישן באותה חזית", "A fast minimum-delay path may disturb old data at the same edge"),
    ):
        box(d, rect)
        phrase(d, (1100, rect[1] + 75), title_he, title_en, lang, 44, bold=True)
        label(d, (1100, rect[1] + 180), equation, 42, PURPLE)
        phrase(d, (1100, rect[1] + 285), explanation_he, explanation_en, lang, 38)
    phrase(d, (1100, 1240), "הפרה אינה מבטיחה הקדמה או איחור קבועים של מחזור", "A violation does not guarantee a fixed one-cycle advance or delay", lang, 38)
    phrase(d, (1100, 1340), "אין כאן מודל שמנבא גרף לאחר מטא־יציבות", "This is not a waveform predictor after metastability", lang, 36)
    im.save(OUT / f"prep-104-timing-constraints-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        times_six(language)
        dff_tff(language)
        pipeline_prompt(language)
        timing_constraints(language)
