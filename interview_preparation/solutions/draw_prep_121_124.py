"""Localized solution-only transport and burn-event figures."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE, ORANGE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0", "#b76530"


def panel(draw, rect, color=PURPLE):
    draw.rounded_rectangle(rect, 22, fill=PALE if color == PURPLE else "#e8f1eb", outline=color, width=5)


def camel(language):
    image = Image.new("RGB", (2200, 1500), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 75), "סופרים גם את הדרך חזרה",
           "Count the return trips too", language, 58, bold=True)
    phrase(draw, (1100, 155), "מזון הדרך כלול במטען והמחסנים נשארים במקומם",
           "Travel food is included in the load; caches stay on the road", language, 38)
    rows = (("0 → 200", "3000 → 2000", "3 + 2 = 5", "200"),
            ("200 → 533⅓", "2000 → 1000", "2 + 1 = 3", "333⅓"),
            ("533⅓ → 1000", "1000 → 533⅓", "1 + 0 = 1", "466⅔"))
    headings = ((350, "מיקום בקילומטרים", "Position / km"),
                (900, "כמות בננות", "Banana stock"),
                (1450, "הלוך ועוד חזור", "Forward + return"),
                (1920, "אורך השלב", "Stage length / km"))
    for x, he, en in headings:
        phrase(draw, (x, 270), he, en, language, 34, bold=True)
    for index, row in enumerate(rows):
        y = 375 + index * 210
        panel(draw, (80, y - 65, 2120, y + 90), PURPLE if index % 2 == 0 else GREEN)
        for (x, _, _), value in zip(headings, row, strict=True):
            text(draw, (x, y), value, 43 if x != 1450 else 41, bold=True)
    phrase(draw, (1100, 960), "הוצאה לכל קילומטר של קידום המלאי",
           "Consumption per kilometre of advancing the stock", language, 38, bold=True)
    text(draw, (1100, 1030), "5 → 3 → 1", 54, color=PURPLE, bold=True)
    panel(draw, (120, 1120, 2080, 1345), GREEN)
    phrase(draw, (1100, 1170), "פתרון בבננות שלמות ובתחנות בקילומטרים שלמים",
           "Whole bananas with stations at integer kilometres", language, 37, bold=True)
    if language == "he":
        text(draw, (500, 1250), "km 533: 1001", 36)
        phrase(draw, (1100, 1250), "משאירים אחת ומעמיסים אלף", "", language, 34)
        text(draw, (1780, 1250), "1000 - 467 = 533", 36)
    else:
        text(draw, (1100, 1250), "km 533: 1001 → discard 1 → 1000     |     1000 - 467 = 533", 36)
    phrase(draw, (1100, 1420), "השלב האחרון אינו כולל חזרה מהשוק",
           "No return from the market is required", language, 37)
    image.save(OUT / f"prep-121-bidirectional-cache-stages-{language}.png")


def rope_line(draw, x, y, widths, durations, *, burned_left=0, burned_right=0, meeting=None):
    total_width = sum(widths)
    draw.rounded_rectangle((x, y - 17, x + total_width, y + 17), 12, fill="#d8d1df", outline=INK, width=3)
    if burned_left:
        draw.rectangle((x, y - 14, x + burned_left, y + 14), fill=ORANGE)
    if burned_right:
        draw.rectangle((x + total_width - burned_right, y - 14, x + total_width, y + 14), fill=ORANGE)
    at = x
    for width, duration in zip(widths, durations, strict=True):
        text(draw, (at + width / 2, y - 55), str(duration), 31)
        if at > x:
            draw.line((at, y - 24, at, y + 24), fill=INK, width=3)
        at += width
    if meeting is not None:
        point = x + meeting
        draw.line((point, y - 30, point, y + 30), fill=PURPLE, width=7)


def ropes(language):
    image = Image.new("RGB", (2200, 1560), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 75), "מודדים אירועי כיבוי ולא חצאי אורך",
           "Measure burnouts, not halves of physical length", language, 54, bold=True)
    phrase(draw, (1100, 150), "לכל פתיל זמן בעירה כולל של שעה גם בפרופיל שונה",
           "Each rope has sixty total burn-minutes, with unrelated profiles", language, 37)
    for x, minute, he, en in ((360, "0", "הדלקה", "Ignite"),
                               (1100, "30", "פתיל ראשון כבה", "First rope burns out"),
                               (1840, "45", "פתיל שני כבה", "Second rope burns out")):
        panel(draw, (x - 280, 235, x + 280, 410))
        text(draw, (x, 290), minute, 50, bold=True, color=PURPLE)
        phrase(draw, (x, 365), he, en, language, 32, bold=True)
    wire(draw, [(645, 320), (815, 320)], INK, 5)
    wire(draw, [(1385, 320), (1555, 320)], INK, 5)
    phrase(draw, (1100, 475), "בהתחלה מדליקים את הראשון משני קצותיו ואת השני מקצה אחד",
           "At zero light both ends of A and one end of B", language, 37)
    phrase(draw, (1100, 540), "כשהראשון כבה מדליקים את הקצה השני של הפתיל השני",
           "At A's burnout light the other end of B", language, 37)
    phrase(draw, (1100, 640), "פרופילים להמחשה בלבד והמספרים הם דקות בעירה לכל מקטע",
           "Illustrative profiles only; labels are each segment's burn-minutes", language, 32, color=GREEN)
    text(draw, (210, 775), "A", 47, bold=True)
    rope_line(draw, 410, 775, [350] * 4, [5, 10, 15, 30], burned_left=1050, burned_right=350, meeting=1050)
    phrase(draw, (1100, 865), "החזיתות נפגשות אחרי חצי מזמן הבעירה ולא בהכרח באמצע האורך",
           "Fronts meet after half the burn-time, not necessarily at the spatial midpoint", language, 33)
    text(draw, (210, 1010), "B", 47, bold=True)
    rope_line(draw, 410, 1010, [350] * 4, [40, 10, 5, 5], burned_left=262.5)
    phrase(draw, (1100, 1090), "באירוע הראשון נשארו שלושים דקות בעירה מקצה אחד",
           "At the first event B has thirty one-end burn-minutes left", language, 34)
    text(draw, (1100, 1220), "30 + (60 - 30) / 2 = 45 min", 52, color=PURPLE, bold=True)
    phrase(draw, (1100, 1320), "שתי חזיתות צורכות את יתרת זמן הבעירה בחמש עשרה דקות",
           "Two fronts consume that remaining burn-time in fifteen minutes", language, 36)
    phrase(draw, (1100, 1420), "אין צורך בשעון חיצוני בחיתוך או בכיבוי יזום",
           "No external clock, cutting or deliberate extinguishing is needed", language, 36)
    phrase(draw, (1100, 1500), "הנחת המודל היא שחזיתות אינן משנות את קצב זו של זו עד המפגש",
           "Model assumption: fronts do not alter each other's local rate before meeting", language, 32)
    image.save(OUT / f"prep-124-nonuniform-burn-events-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        camel(lang)
        ropes(lang)
