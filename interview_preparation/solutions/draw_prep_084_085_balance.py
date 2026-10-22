"""Authored paired Hebrew/English static-balance diagrams in the site's palette."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, MUTED, PALE = "#35234f", "#73558d", "#756781", "#e7def0"


def canvas(height=1150):
    image = Image.new("RGB", (1600, height), "#fffdf8")
    return image, ImageDraw.Draw(image)


def label(draw, position, value, size=42, hebrew=False, bold=False, color=INK):
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
    draw.text(position, value[::-1] if hebrew else value, font=font, fill=color, anchor="mm")


def local(draw, position, language, he, en, size=42, bold=False, color=INK):
    label(draw, position, he if language == "he" else en, size, language == "he", bold, color)


def vector(draw, start, end, color=PURPLE, width=4):
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    draw.polygon([end] + [(end[0] - 16 * math.cos(angle + offset), end[1] - 16 * math.sin(angle + offset))
                         for offset in (-0.45, 0.45)], fill=color)


def circle(draw, center, radius):
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline=INK, width=5)
    draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=INK)


def plate(language):
    image, draw = canvas()
    local(draw, (800, 70), language, "איזון צלחת: קודם מגדירים את המקומות", "Plate balance: specify allowed positions first", 52, True)
    local(draw, (800, 140), language, "דוגמאות שהוספנו; מיקום הווים אינו נתון במקור", "Added illustrations; source hook positions are unknown", 37, color=MUTED)
    for index in range(2):
        x0, x1 = 45 + index * 785, 770 + index * 785
        draw.rounded_rectangle((x0, 205, x1, 1020), radius=28, outline=PALE, width=3)
    local(draw, (407, 265), language, "וריאציה: מיקום חופשי", "Variant: free placement", 43, True)
    local(draw, (1192, 265), language, "דוגמה נגדית: ווים קבועים", "Counterexample: fixed hooks", 43, True)
    center, radius = (407, 600), 225
    circle(draw, center, radius)
    points = [(center[0] + radius * math.sin(2 * math.pi * i / 5),
               center[1] - radius * math.cos(2 * math.pi * i / 5)) for i in range(5)]
    for point in points:
        vector(draw, center, point)
        draw.ellipse((point[0] - 18, point[1] - 18, point[0] + 18, point[1] + 18), fill=PURPLE)
    local(draw, (407, 900), language, "מרווחים שווים על אותו מעגל", "Equal spacing on one circle", 36)
    label(draw, (407, 962), "sum(r_i) = (0, 0)", 37, color=PURPLE)
    center = (1192, 600)
    circle(draw, center, radius)
    # A stated counterexample, not a reconstruction of unspecified source hooks.
    draw.line((center[0], 340, center[0], 860), fill=PALE, width=3)
    for angle in (-0.8, -0.3, 0.3, 0.8):
        point = (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))
        vector(draw, center, point, MUTED)
        draw.ellipse((point[0] - 14, point[1] - 14, point[0] + 14, point[1] + 14), fill=MUTED)
    local(draw, (1192, 900), language, "כל הווים בצד אחד: אין ביטול", "All hooks on one side: no cancellation", 34)
    label(draw, (1192, 962), "x_i > 0  =>  sum(x_i) > 0", 36, color=PURPLE)
    local(draw, (800, 1090), language, "מומנט סטטי אפס אינו הוכחת יציבות", "Zero static moment does not prove stability", 36, color=MUTED)
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / f"prep-084-balance-models-{language}.png")


def clock(language, solution=False):
    image, draw = canvas()
    local(draw, (800, 70), language, "חמש אבנים על שנתות שעון", "Five stones on fixed clock marks", 53, True)
    local(draw, (800, 140), language, "מבט מלמעלה; נקודת התמיכה במרכז", "Top view; centered support point", 39, color=MUTED)
    center, radius = (555, 630), 315
    circle(draw, center, radius)

    def position(hour, distance=radius):
        angle = math.pi * hour / 6
        return center[0] + distance * math.sin(angle), center[1] - distance * math.cos(angle)

    for hour in range(1, 13):
        draw.line((position(hour, radius - 17), position(hour, radius + 10)), fill=INK, width=4)
        label(draw, position(hour, radius + 58), str(hour), 43)
    if solution:
        for hours, color in (((12, 4, 8), PURPLE), ((3, 9), "#ab87be")):
            for hour in hours:
                point = position(hour)
                vector(draw, center, point, color, width=5)
                draw.ellipse((point[0] - 23, point[1] - 23, point[0] + 23, point[1] + 23), fill=color, outline=INK, width=2)
        local(draw, (1245, 380), language, "שלוש אבנים", "Three stones", 43, True)
        label(draw, (1245, 444), "12, 4, 8", 48, color=PURPLE)
        local(draw, (1245, 513), language, "מרווחים שווים של שליש סיבוב", "Equal one-third turns", 34)
        local(draw, (1245, 645), language, "ועוד שתי אבנים", "Plus two stones", 43, True)
        label(draw, (1245, 710), "3, 9", 48, color=PURPLE)
        local(draw, (1245, 777), language, "זוג נקודות מנוגדות", "A diametrically opposite pair", 34)
        label(draw, (1245, 902), "sum(r_i) = (0, 0)", 37, color=PURPLE)
    else:
        local(draw, (1245, 430), language, "מקומות מותרים", "Allowed positions", 44, True)
        local(draw, (1245, 505), language, "שתים עשרה השנתות בלבד", "The twelve hour marks only", 35)
        local(draw, (1245, 650), language, "חמש אבנים שוות מסה", "Five equal-mass stones", 35)
        local(draw, (1245, 725), language, "מותר להניח כמה באותו מקום", "Multiple stones per mark allowed", 33)
    local(draw, (800, 1080), language, "אבנים אידאליות; נבדק איזון מומנטים בלבד", "Ideal stones; static moment balance only", 37, color=MUTED)
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / f"prep-085-{'placement' if solution else 'clock'}-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        plate(lang)
        clock(lang)
        clock(lang, solution=True)
