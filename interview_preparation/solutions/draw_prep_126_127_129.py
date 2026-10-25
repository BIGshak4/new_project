"""Localized solution-only affine-model, hat-residue and snail-path figures."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE, ORANGE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0", "#b76530"


def panel(draw, rect, color=PURPLE):
    draw.rounded_rectangle(rect, 24, fill=PALE if color == PURPLE else "#e8f1eb", outline=color, width=5)


def coffee(language):
    image = Image.new("RGB", (2200, 1450), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 80), "קירור לינארי דורש גם קצב אחרי הוספת החלב",
           "Linear cooling also needs a postmix rate", language, 54, bold=True)
    phrase(draw, (1100, 170), "שני מודלים שונים מתאימים לאותו קצב התחלתי",
           "Different models can share the same initial coffee slope", language, 37)
    phrase(draw, (1100, 265), "נתונים להמחשה בלבד ולא נתוני הצילום",
           "Illustrative values, not source data", language, 35, color=GREEN)
    text(draw, (1100, 330), "T_coffee = 90     T_milk = 10     C_coffee = 200     C_milk = 50     t = 10 min", 35)
    for x, he, en, formula, early, late in (
        (575, "קצב ירידת טמפרטורה זהה", "Same temperature-drop rate", "a = b = 1 °C/min", "64", "66"),
        (1625, "אובדן חום קבוע לדקה", "Constant heat loss per minute", "P = 200     a = 1     b = 0.8", "66", "66"),
    ):
        panel(draw, (x - 480, 440, x + 480, 1015), PURPLE if x == 575 else GREEN)
        phrase(draw, (x, 505), he, en, language, 36, bold=True)
        text(draw, (x, 590), formula, 33)
        phrase(draw, (x - 210, 705), "הוספה בתחילה", "Add initially", language, 34)
        phrase(draw, (x + 210, 705), "הוספה בסוף", "Add at the end", language, 34)
        text(draw, (x - 210, 800), early, 72, bold=True, color=PURPLE)
        text(draw, (x + 210, 800), late, 72, bold=True, color=GREEN)
        phrase(draw, (x, 925), "בסוף חם יותר" if x == 575 else "אותה טמפרטורה",
               "Late is warmer" if x == 575 else "Equal final temperatures", language, 37, bold=True)
    text(draw, (1100, 1130), "T_late - T_early = (b - alpha * a) * t", 48, bold=True, color=PURPLE)
    text(draw, (1100, 1210), "alpha = C_coffee / (C_coffee + C_milk)", 40)
    phrase(draw, (1100, 1320), "המקור אינו קובע איזה מהמודלים מתאר את התערובת",
           "The source does not choose the mixture's model", language, 37, bold=True)
    phrase(draw, (1100, 1400), "זו השוואת מודלים מתמטיים ואינה מדידת קפה פיזית",
           "Mathematical model comparison, not a physical coffee measurement", language, 34)
    image.save(OUT / f"prep-126-linear-cooling-models-{language}.png")


def hats(language):
    image = Image.new("RGB", (2400, 1800), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 80), "רואים את האחרים ומנחשים בלי לשמוע תשובות",
           "Observe others and guess without hearing answers", language, 54, bold=True)
    phrase(draw, (1200, 160), "ניחוש נכון מובטח אינו ידיעה אישית של צבע הכובע",
           "A guaranteed correct guess is not individual knowledge of one's own color", language, 37)
    for x, he, en, formula in ((620, "מספר אפס אומר את צבע האחר", "Player zero repeats the other color", "g0 = h1"),
                               (1780, "מספר אחד אומר את הצבע הנגדי", "Player one says the opposite color", "g1 = 1 - h0")):
        panel(draw, (x - 515, 250, x + 515, 500))
        phrase(draw, (x, 315), he, en, language, 35, bold=True)
        text(draw, (x, 415), formula, 49, bold=True, color=PURPLE)
    phrase(draw, (1200, 550), "מספר ניחושים נכונים בכל צמד כובעים",
           "Number of correct guesses for each hat pair", language, 30)
    text(draw, (1200, 605), "(h0,h1):    00 → 1     01 → 1     10 → 1     11 → 1", 37)
    phrase(draw, (1200, 675), "תחת ההבטחה לכל המקרים אין מקרה שבו שניהם צודקים",
           "Under a guarantee for every assignment, both are never correct together", language, 38, bold=True)
    phrase(draw, (1200, 790), "אותו רעיון לעשרה גמדים ולעשרה צבעים שיכולים לחזור",
           "Ten players and ten colors with repetitions allowed", language, 42, bold=True)
    text(draw, (1200, 890), "g_i = (i - sum(colors visible to i)) mod 10", 48, color=PURPLE, bold=True)
    phrase(draw, (1200, 980), "לצורך ההוכחה בלבד סוכמים את כל הצבעים",
           "For the proof only, sum all hat colors", language, 35)
    text(draw, (1200, 1050), "S = sum(all colors) mod 10     |     g_i = h_i  iff  i = S", 39)
    values = (2, 7, 1, 0, 4, 2, 3, 6, 5, 8)
    for index, color in enumerate(values):
        x = 340 + index * 190
        if index == 8:
            panel(draw, (x - 80, 1150, x + 80, 1375), GREEN)
        text(draw, (x, 1200), str(index), 44, bold=True)
        text(draw, (x, 1310), str(color), 43, color=GREEN if index == 8 else INK)
    text(draw, (150, 1200), "i", 44, bold=True)
    text(draw, (150, 1310), "h_i", 39)
    text(draw, (1200, 1455), "2+7+1+0+4+2+3+6+5+8 = 38     |     S = 8", 43, bold=True, color=GREEN)
    phrase(draw, (1200, 1550), "בדוגמה רק מספר שמונה פוגע בצבע שלו",
           "In this example only player eight guesses their own color correctly", language, 37)
    phrase(draw, (1200, 1650), "כל גמד מחשב רק מהכובעים שהוא רואה ולא מצבעו הנסתר",
           "Each controller uses only visible hats, never their hidden own color", language, 36)
    phrase(draw, (1200, 1740), "החדרים אינם יוצרים ערוץ תקשורת אחרי התיאום",
           "No communication channel is added after the agreement", language, 35)
    image.save(OUT / f"prep-127-distributed-residue-guesses-{language}.png")


def snail(language):
    image = Image.new("RGB", (2200, 1500), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 75), "עוצרים כשמגיעים לפרח ולא גולשים שוב",
           "Stop at the flower; there is no final slide", language, 55, bold=True)
    phrase(draw, (1100, 155), "דקת טיפוס מתחלפת בדקת מנוחה וגלישה",
           "One climbing minute alternates with one resting/sliding minute", language, 36)
    left, right, top, bottom = 220, 1960, 320, 1030
    def point(time, height):
        return (left + time * (right - left) / 17, bottom - height * (bottom - top) / 10)
    wire(draw, [(left, bottom + 20), (right + 65, bottom + 20)], INK, 4)
    wire(draw, [(left - 15, bottom), (left - 15, top - 55)], INK, 4)
    for minute in (*range(0, 17, 2), 17):
        x, _ = point(minute, 0)
        text(draw, (x, bottom + 65), str(minute), 32)
    for height in range(0, 11, 2):
        _, y = point(0, height)
        text(draw, (left - 65, y), str(height), 32)
        draw.line((left, y, right, y), fill="#e4dce9", width=2)
    for cycle in range(8):
        draw.line((*point(2 * cycle, cycle), *point(2 * cycle + 1, cycle + 2)), fill=GREEN, width=7)
        draw.line((*point(2 * cycle + 1, cycle + 2), *point(2 * cycle + 2, cycle + 1)), fill=PURPLE, width=7)
    draw.line((*point(16, 8), *point(17, 10)), fill=GREEN, width=10)
    x, y = point(17, 10)
    draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=ORANGE)
    text(draw, (1780, 255), "(17, 10)", 42, color=ORANGE, bold=True)
    phrase(draw, (1100, 1140), "זמן בדקות", "Time / minutes", language, 35)
    phrase(draw, (450, 270), "גובה בסנטימטרים", "Height / cm", language, 34)
    panel(draw, (170, 1220, 2030, 1400))
    text(draw, (1100, 1270), "8 * (1 + 1) + 1 = 17", 48, bold=True, color=PURPLE)
    phrase(draw, (1100, 1350), "תשעה טיפוסים ושמונה קטעי גלישה בלבד",
           "Nine climbs and only eight slides", language, 38, bold=True)
    phrase(draw, (1100, 1460), "בזמן שש עשרה הגובה שמונה והטיפוס האחרון נמשך דקה",
           "At minute sixteen height is eight; the final climb takes one minute", language, 34)
    image.save(OUT / f"prep-129-first-contact-zigzag-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        coffee(lang)
        hats(lang)
        snail(lang)
