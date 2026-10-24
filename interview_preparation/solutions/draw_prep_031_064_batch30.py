"""Clean localized solution-only figures for two archived source variants."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0"


def panel(draw, rect, color=PURPLE):
    draw.rounded_rectangle(rect, 24, fill=PALE, outline=color, width=5)


def timing(language):
    image = Image.new("RGB", (1900, 1300), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (950, 80), "השהיה צריכה להתייחס למסלול מוגדר",
           "Delay must refer to a defined path", language, 53, bold=True)
    phrase(draw, (950, 155), "מודל נתונים מדלגלג לדלגלג עם שעון משותף",
           "Register-to-register data path with a common clock", language, 36)
    for x, name_he, name_en in ((270, "דלגלג משגר", "Launch DFF"), (1620, "דלגלג קולט", "Capture DFF")):
        panel(draw, (x - 155, 245, x + 155, 455))
        phrase(draw, (x, 300), name_he, name_en, language, 36, bold=True)
        text(draw, (x, 370), "Q" if x == 270 else "D", 48, bold=True)
    panel(draw, (650, 260, 1240, 440), GREEN)
    phrase(draw, (945, 310), "לוגיקה וחיווט", "Logic and routing", language, 39, bold=True)
    text(draw, (945, 385), "d_comb,max", 42, color=GREEN)
    wire(draw, [(425, 365), (650, 365)], PURPLE, 5)
    wire(draw, [(1240, 365), (1465, 365)], GREEN, 5)
    wire(draw, [(270, 560), (270, 455)], INK, 5)
    wire(draw, [(1620, 560), (1620, 455)], INK, 5)
    draw.line((270, 560, 1620, 560), fill=INK, width=5)
    text(draw, (950, 525), "clk", 35)
    text(draw, (950, 655), "T_min = t_cq,max + d_comb,max + t_setup + U - s", 43,
         bold=True, color=PURPLE)
    if language == "he":
        phrase(draw, (950, 725), "סטייה היא הגעת שעון לקולט פחות הגעתו למשגר",
               "", language, 33)
    else:
        text(draw, (950, 725), "s = capture clock arrival - launch clock arrival", 33)
    phrase(draw, (950, 790), "שינוי תדר אינו מתקן הפרת החזקה",
           "Changing clock frequency does not repair a hold violation", language, 35, color=GREEN)
    for x, he, en, detail, answer in (
        (485, "שתי ננו הן כל המסלול", "Two ns is the complete path", "d_comb,max = 2 ns", "f_ideal = 500 MHz"),
        (1415, "שתי ננו לכל מרבב בשתי רמות", "Two ns per MUX, two levels", "d_comb,max = 2 + 2 = 4 ns", "f_ideal = 250 MHz"),
    ):
        panel(draw, (x - 440, 865, x + 440, 1125))
        phrase(draw, (x, 915), he, en, language, 34, bold=True)
        text(draw, (x, 990), detail, 35)
        text(draw, (x, 1065), answer, 39, color=PURPLE, bold=True)
    phrase(draw, (950, 1190), "שתי התוצאות מניחות אפס תקורות שעון ושהמסלול הזה מגביל",
           "Both ideal results ignore clock overheads and assume this path limits the clock", language, 32)
    phrase(draw, (950, 1250), "חלוקה לשלבים מחייבת יישור אותות ומשנה השהיה במחזורים",
           "Pipelining needs signal alignment and changes latency in clock cycles", language, 32)
    image.save(OUT / f"prep-031-register-path-timing-{language}.png")


def staged_counter(language):
    image = Image.new("RGB", (1900, 1500), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (950, 75), "כניסת האפשור מחליטה אם לספור בחזית",
           "Enable decides whether to count at an edge", language, 51, bold=True)
    phrase(draw, (950, 150), "זו כניסת נתונים ואינה שעון",
           "Enable is data, never the clock", language, 37, color=GREEN)
    panel(draw, (220, 215, 1680, 390))
    phrase(draw, (950, 260), "ביט אחד עם דלגלג נתונים ומשוב",
           "One bit: a D flip-flop with data feedback", language, 37, bold=True)
    if language == "he":
        text(draw, (650, 335), "D = q XOR e", 39)
        phrase(draw, (1220, 335), "אפס שומר ואחד הופך", "", language, 37)
    else:
        text(draw, (950, 335), "D = q XOR e     |     e=0: hold     e=1: toggle", 39)
    phrase(draw, (950, 460), "בוחרים אחד משני תכנונים נפרדים לשלושה ביטים",
           "Choose one of two separate three-bit designs", language, 38, bold=True)
    for x, he, en, lines in (
        (485, "מונה עולה", "Up counter", ("T0 = e", "T1 = e AND q0", "T2 = e AND q1 AND q0")),
        (1415, "מונה יורד", "Down counter", ("T0 = e", "T1 = e AND NOT q0", "T2 = e AND NOT q1 AND NOT q0")),
    ):
        panel(draw, (x - 440, 520, x + 440, 810), GREEN)
        phrase(draw, (x, 565), he, en, language, 39, bold=True, color=GREEN)
        for index, line in enumerate(lines):
            text(draw, (x, 640 + 65 * index), line, 37 if index < 2 else 32)
    panel(draw, (565, 900, 1335, 1120))
    text(draw, (950, 960), "D_i = q_i XOR T_i", 45, bold=True, color=PURPLE)
    phrase(draw, (950, 1040), "שלושה דלגלגים על אותו שעון",
           "Three DFFs on the same clock", language, 35)
    wire(draw, [(325, 1000), (565, 1000)], GREEN, 5)
    text(draw, (275, 955), "T[2:0]", 34, color=GREEN)
    wire(draw, [(1335, 1000), (1635, 1000)], PURPLE, 5)
    text(draw, (1635, 945), "Q[2:0]", 36, bold=True)
    wire(draw, [(1510, 1000), (1510, 1190), (380, 1190), (380, 1090), (565, 1090)], PURPLE, 5)
    phrase(draw, (1510, 1250), "משוב נתונים", "old Q: data feedback", language, 31, color=PURPLE)
    wire(draw, [(800, 1280), (800, 1120)], INK, 5)
    wire(draw, [(1100, 1280), (1100, 1120)], GREEN, 5)
    text(draw, (800, 1315), "clk", 35)
    text(draw, (1100, 1315), "rst", 35, color=GREEN)
    phrase(draw, (950, 1390), "כל תנאי ההיפוך משתמשים בביטים שלפני החזית",
           "All toggle conditions use the pre-edge bits", language, 35, bold=True)
    phrase(draw, (950, 1460), "אפשור אפס שומר מצב ואיפוס פעיל קובע אפס עם עדיפות",
           "Zero enable holds; active reset has priority and loads zero", language, 34)
    image.save(OUT / f"prep-064-staged-enable-counters-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        timing(lang)
        staged_counter(lang)
