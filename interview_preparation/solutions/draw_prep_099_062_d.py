"""Localized, deterministic RC and marker-only rendezvous solution diagrams."""

from math import expm1
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, LIGHT, PAPER = "#302344", "#5d4383", "#33786d", "#e7def0", "#fffdf8"


def sheet(he, en, language, height=1200):
    image = Image.new("RGB", (1800, height), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (900, 80), he, en, language, 52, color=INK, bold=True)
    return image, draw


def ground(draw, x, y):
    for index, width in enumerate((90, 60, 30)):
        draw.line((x - width / 2, y + index * 17, x + width / 2, y + index * 17),
                  fill=INK, width=5)


def circuit(language):
    image, draw = sheet("מודדים את זמן הטעינה של קבל לא ידוע",
                        "Measure an unknown capacitor's charging time", language, 1220)
    phrase(draw, (900, 165), "קירוב בסיסי ללא עומס מדידה משמעותי",
           "Basic approximation with negligible measurement loading", language, 36)
    draw.ellipse((160, 460, 300, 600), outline=PURPLE, width=6)
    text(draw, (230, 505), "+", 42, color=PURPLE)
    text(draw, (230, 555), "−", 42, color=PURPLE)
    wire(draw, [(230, 460), (230, 350), (520, 350)], PURPLE, arrow=False)
    draw.rectangle((520, 305, 800, 395), outline=PURPLE, width=6)
    text(draw, (660, 245), "R", 54, bold=True)
    phrase(draw, (660, 460), "מודדים קודם את ההתנגדות",
           "Measure resistance first", language, 32)
    wire(draw, [(800, 350), (1060, 350), (1060, 620)], GREEN, arrow=False)
    draw.line((965, 620, 1155, 620), fill=GREEN, width=8)
    draw.line((965, 665, 1155, 665), fill=GREEN, width=8)
    wire(draw, [(1060, 665), (1060, 930), (230, 930), (230, 600)], INK, arrow=False)
    ground(draw, 1060, 930)
    text(draw, (1205, 645), "C?", 52, color=GREEN, bold=True)
    draw.ellipse((1050, 340, 1070, 360), fill=GREEN)
    wire(draw, [(1060, 350), (1470, 350), (1470, 510)], GREEN, arrow=False)
    draw.rounded_rectangle((1280, 510, 1660, 760), 22, fill="#f1ecef", outline=PURPLE, width=5)
    phrase(draw, (1470, 565), "אוסצילוסקופ", "Oscilloscope", language, 35, bold=True)
    text(draw, (1470, 635), "V_C(t)", 43, color=GREEN)
    phrase(draw, (1470, 710), "אותה אדמה", "Common ground", language, 31)
    wire(draw, [(1470, 760), (1470, 930), (1060, 930)], INK, arrow=False)
    phrase(draw, (450, 735), "מדרגת מתח", "Voltage step", language, 34)
    text(draw, (450, 795), "0 → 1 V", 40, color=PURPLE)
    text(draw, (900, 1030), "tau = R C       C = tau / R", 49, color=PURPLE, bold=True)
    phrase(draw, (900, 1125), "לתיקון מדויק יותר כוללים התנגדות מקור ועומס פרוב",
           "For correction, include source resistance and probe loading", language, 35)
    image.save(OUT / f"prep-099-rc-step-circuit-{language}.png")


def curve(language):
    image, draw = sheet("קוראים קבוע זמן מתוך העקומה", "Read a time constant from the curve", language, 1200)
    phrase(draw, (900, 165), "הגובה נמדד ביחס לשינוי בין ההתחלה לרמה הסופית",
           "Measure the fraction of the change from initial to final level", language, 35)
    left, right, top, bottom = 250, 1560, 300, 880
    to_x = lambda value: left + (right - left) * value / 5
    to_y = lambda value: bottom - (bottom - top) * value
    wire(draw, [(left, bottom), (right + 70, bottom)], INK, 5)
    wire(draw, [(left, bottom), (left, top - 70)], INK, 5)
    draw.line((left, top, right, top), fill=LIGHT, width=4)
    for multiple in (0, 1, 2, 3, 4, 5):
        x = to_x(multiple)
        draw.line((x, bottom, x, bottom + 14), fill=INK, width=4)
        text(draw, (x, bottom + 55), "0" if multiple == 0 else f"{multiple}τ", 37)
    points = [(to_x(value / 100), to_y(-expm1(-value / 100))) for value in range(501)]
    draw.line(points, fill=GREEN, width=7)
    x_tau, y_tau = to_x(1), to_y(-expm1(-1))
    draw.line((left, y_tau, x_tau, y_tau), fill=PURPLE, width=4)
    draw.line((x_tau, y_tau, x_tau, bottom), fill=PURPLE, width=4)
    draw.ellipse((x_tau - 9, y_tau - 9, x_tau + 9, y_tau + 9), fill=PURPLE)
    text(draw, (130, y_tau), "63.2%", 38, color=PURPLE, bold=True)
    text(draw, (130, top), "100%", 35)
    text(draw, (140, bottom), "0%", 35)
    text(draw, (1600, 950), "t", 43)
    text(draw, (1040, 475), "V(tau) = V0 + (1 - exp(-1))(Vinf - V0)", 35, color=PURPLE)
    text(draw, (900, 1040), "R = 10 kΩ     tau = 1 ms     C = 100 nF", 45, bold=True)
    phrase(draw, (900, 1130), "דוגמה מחושבת במודל אידאלי ולא מדידת מעבדה",
           "Calculated ideal-model example, not a laboratory measurement", language, 34)
    image.save(OUT / f"prep-099-time-constant-curve-{language}.png")


def robots(language):
    image, draw = sheet("דגל קבוע גורם רק לאחורי להפסיק להמתין",
                        "A fixed flag makes only the trailer stop waiting", language, 1230)
    phrase(draw, (900, 165), "דוגמה במרחק שלושה צעדים ובקרה מיידית",
           "Example: three-step separation and instantaneous control", language, 35)
    left, right, top, bottom = 240, 1540, 300, 900
    to_x = lambda time: left + (right - left) * time / 14
    to_y = lambda position: bottom - (bottom - top) * position / 12
    for position in (0, 3):
        y = to_y(position)
        draw.line((left, y, right, y), fill=LIGHT, width=4)
        text(draw, (130, y), f"x={position}", 34)
    wire(draw, [(left, bottom), (right + 75, bottom)], INK, 5)
    wire(draw, [(left, bottom), (left, top - 50)], INK, 5)
    for tick in (0, 2, 5, 10, 14):
        text(draw, (to_x(tick), bottom + 47), str(tick), 34)
    points = [[], []]
    for tick in range(15):
        trailer = (tick + 1) // 2 if tick <= 5 else 3 + tick - 5
        leader = 3 + (tick + 1) // 2
        points[0].append((to_x(tick), to_y(trailer)))
        points[1].append((to_x(tick), to_y(leader)))
    draw.line(points[0], fill=PURPLE, width=8)
    draw.line(points[1], fill=GREEN, width=6)
    meet = (to_x(10), to_y(8))
    draw.ellipse((meet[0] - 12, meet[1] - 12, meet[0] + 12, meet[1] + 12), fill=INK)
    text(draw, (meet[0] + 160, meet[1] + 60), "t = 10", 37, bold=True)
    text(draw, (1620, bottom + 50), "t", 43)
    text(draw, (170, top - 35), "x", 43)
    phrase(draw, (570, 1015), "התחיל מאחור", "Initially trailing", language, 36, color=PURPLE, bold=True)
    phrase(draw, (1220, 1015), "התחיל מלפנים", "Initially leading", language, 36, color=GREEN, bold=True)
    phrase(draw, (900, 1100), "הרתמה מזהה את המפגש לצורך בדיקה בלבד",
           "Only the test harness detects the meeting", language, 36)
    phrase(draw, (900, 1170), "התוכניות ממשיכות לפעול ואין חיישן מפגש",
           "The programs continue; neither has a meeting sensor", language, 34)
    image.save(OUT / f"prep-062-d-marker-only-trajectory-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        circuit(lang)
        curve(lang)
        robots(lang)
