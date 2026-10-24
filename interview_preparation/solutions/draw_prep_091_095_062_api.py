"""Paired authored timing/circuit figures for the October 24 intake."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, PALE = "#302344", "#5d4383", "#33786d", "#e7def0"


def canvas(he, en, lang, height=1100):
    im = Image.new("RGB", (1800, height), "#fffdf8")
    d = ImageDraw.Draw(im)
    phrase(d, (900, 75), he, en, lang, 54, bold=True, color=INK)
    return im, d


def wave(d, events, base, end=10, color=PURPLE):
    points = []
    previous = None
    for time, value in events:
        x, y = 300 + time * 137, base - value * 95
        if previous is not None:
            points.extend([(x, previous), (x, y)])
        else:
            points.append((x, y))
        previous = y
    points.append((300 + end * 137, previous))
    d.line(points, fill=color, width=6)


def prompt_091(lang):
    im, d = canvas("פולס מיד בשינוי הקלט ועד החזית הבאה", "Pulse immediately on input change until the next rising edge", lang)
    phrase(d, (900, 160), "שרטוט מקור מחודש; הזמנים המספריים נוספו להמחשה", "Source redrawn; numeric times are illustrative additions", lang, 34)
    for time in (1, 3, 5, 7, 9):
        x = 300 + 137 * time
        d.line((x, 240, x, 870), fill=PALE, width=3)
        text(d, (x, 920), str(time), 38)
    clock = [(0, 0)] + [(t, t % 2) for t in range(1, 11)]
    for label, events, y, color in [
        ("clk", clock, 380, INK),
        ("In", [(0, 0), (2.2, 1), (6.2, 0)], 590, GREEN),
        ("OUT", [(0, 0), (2.2, 1), (3, 0), (6.2, 1), (7, 0)], 800, PURPLE),
    ]:
        text(d, (145, y - 40), label, 50, bold=True, color=color)
        wave(d, events, y, color=color)
    phrase(d, (900, 1010), "הקלט משתנה בין חזיתות; שני סוגי שינוי מפיקים פולס", "Input changes between edges; both transition directions produce pulses", lang, 37)
    im.save(OUT / f"prep-091-prompt-waveform-{lang}.png")


def circuit_091(lang):
    im, d = canvas("משווים את הקלט לעותק שנדגם", "Compare input with its sampled copy", lang)
    phrase(d, (900, 160), "מימוש בוליאני מושגי; לא מסנכרן קלט אסינכרוני", "Conceptual Boolean circuit; not an asynchronous-input synchronizer", lang, 35)
    d.rounded_rectangle((620, 490, 1020, 830), 22, fill="#f8f4e9", outline=PURPLE, width=5)
    text(d, (820, 590), "DFF", 58, bold=True)
    text(d, (675, 680), "D", 43)
    text(d, (965, 680), "Q", 43)
    d.ellipse((1310, 340, 1450, 480), outline=PURPLE, width=5)
    text(d, (1380, 410), "XOR", 36, bold=True)
    wire(d, [(190, 310), (1120, 310), (1120, 370), (1310, 370)], GREEN)
    text(d, (220, 245), "In", 48, bold=True, color=GREEN)
    wire(d, [(420, 310), (420, 680), (620, 680)], GREEN)
    d.ellipse((411, 301, 429, 319), fill=GREEN)
    wire(d, [(1020, 680), (1170, 680), (1170, 450), (1310, 450)], PURPLE)
    phrase(d, (1150, 755), "הקלט שנדגם", "sampled In", lang, 35, color=PURPLE)
    wire(d, [(1450, 410), (1680, 410)], PURPLE)
    text(d, (1600, 335), "OUT", 48, bold=True, color=PURPLE)
    wire(d, [(820, 970), (820, 830)], INK)
    phrase(d, (820, 1005), "שעון בחזית עולה", "clk (rising edge)", lang, 35)
    text(d, (1490, 890), "OUT = In XOR Q", 43, bold=True, color=PURPLE)
    im.save(OUT / f"prep-091-solution-circuit-{lang}.png")


def window_095(lang):
    im, d = canvas("חלון זז: הדגימה האחת עשרה מוציאה את הראשונה", "Sliding window: sample eleven expires sample one", lang, 1100)
    phrase(d, (900, 170), "דוגמה לפתרון; איפוס לפני הדגימה הראשונה", "Worked example; reset precedes sample one", lang, 37)
    xs = [1, 0, 1, 0, 1] + [0] * 10
    ys = [int(sum(xs[max(0, i - 9):i + 1]) >= 3) for i in range(len(xs))]
    counts = [sum(xs[max(0, i - 9):i + 1]) for i in range(len(xs))]
    for row, values in enumerate((range(1, 16), xs, counts, ys)):
        y = 320 + row * 150
        text(d, (130, y), ("n", "X[n]", "count", "Y[n]")[row], 42, bold=True)
        for index, value in enumerate(values):
            x = 300 + index * 95
            if row == 3 and value:
                d.rounded_rectangle((x - 39, y - 48, x + 39, y + 48), 12, fill=PALE)
            text(d, (x, y), str(value), 42, color=PURPLE if row == 3 else INK)
    phrase(d, (900, 920), "במחזור החמישי נכנס האחד השלישי; באחד עשר נשארים שניים", "Cycle five includes the third one; cycle eleven retains only two", lang, 37)
    text(d, (900, 1010), "Y[n] = 1 iff sum(X[max(1,n-9)..n]) >= 3", 37, bold=True, color=PURPLE)
    im.save(OUT / f"prep-095-window-example-{lang}.png")


def waveform_095(lang):
    im, d = canvas("דוגמת תזמון לחלון זז", "Sliding-window timing example", lang, 1100)
    phrase(d, (900, 160), "ערכים אחרי דגימה והתייצבות; איפוס קודם למחזור הראשון", "Values after sample and settling; reset before cycle one", lang, 36)
    xs = [1, 0, 1, 0, 1] + [0] * 10
    ys = [int(sum(xs[max(0, i - 9):i + 1]) >= 3) for i in range(15)]
    for index in range(15):
        x = 300 + 90 * index
        d.line((x, 250, x, 810), fill=PALE, width=2)
        text(d, (x + 45, 880), str(index + 1), 32)
    for label, values, base, color in (("X[n]", xs, 470, GREEN), ("Y[n]", ys, 740, PURPLE)):
        points = []
        previous = None
        for index, value in enumerate(values):
            x, y = 300 + 90 * index, base - 105 * value
            if previous is not None:
                points.append((x, previous))
            points.append((x, y))
            previous = y
        points.append((1650, previous))
        d.line(points, fill=color, width=6)
        text(d, (145, base - 50), label, 48, bold=True, color=color)
    phrase(d, (900, 1000), "הפלט גבוה במחזורים חמש עד עשר כולל", "Output is high on cycles five through ten inclusive", lang, 39)
    im.save(OUT / f"prep-095-solution-waveform-{lang}.png")


def api_062(lang):
    im, d = canvas("וריאנט הממשק: האטה בהמתנה והאצה אחרי הסימן", "API variant: wait to slow down, accelerate after the marker", lang)
    phrase(d, (900, 160), "דוגמה במרחק שתי יחידות; הבדיקות והבקרה חינמיות", "Example separation two; sensor queries and local control are instantaneous", lang, 35)
    # D=2; t=0..6, solution meets at t=6.
    paths = (([0, 1, 1, 2, 3, 4, 5], GREEN, "Rear (proof only)"),
             ([2, 3, 3, 4, 4, 5, 5], PURPLE, "Front (proof only)"))
    for values, color, name in paths:
        points = [(300 + 195 * t, 830 - 100 * x) for t, x in enumerate(values)]
        d.line(points, fill=color, width=7)
        for x, y in points:
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)
        phrase(d, (1280 if color == GREEN else 1320, 600 if color == GREEN else 260),
               "אחורי לצורך ההוכחה" if color == GREEN else "קדמי לצורך ההוכחה", name, lang, 29, color=color)
    for t in range(7):
        text(d, (300 + 195 * t, 900), str(t), 37)
    phrase(d, (150, 470), "מיקום", "position", lang, 32)
    phrase(d, (1610, 900), "זמן", "time", lang, 35)
    phrase(d, (900, 1000), "אותו קוד בשניהם; רק הסוכן האחורי פוגש את המצנח הנוסף", "Identical code; only the trailing agent encounters another parachute", lang, 35)
    im.save(OUT / f"prep-062-api-trajectories-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        prompt_091(language)
        circuit_091(language)
        window_095(language)
        waveform_095(language)
        api_062(language)
