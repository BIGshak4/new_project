"""Bilingual clean counter, NMOS and hidden-resistor diagrams (Pillow)."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw
from prep_153_nmos_load_inverter import dc_output

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG = "#fffdf8"
INK = "#302344"
PURPLE = "#624883"
PALE = "#eee7f5"
GREEN = "#30766a"
GRAY = "#ddd6e4"
ORANGE = "#b46c2f"


def canvas(he, en, lang, h=1450):
    im = Image.new("RGB", (2200, h), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1100, 85), he, en, lang, 48, bold=True, color=INK)
    return im, d


def label(d, xy, value, size=38, color=INK):
    text(d, xy, value, size, bold=True, color=color)


def box(d, rect):
    d.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=5)


def dot(d, x, y, color=PURPLE):
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color)


def counter(lang):
    im, d = canvas("עוד ביט זיכרון על אותו שעון", "One extra state bit on the same clock", lang, 1520)
    box(d, (350, 390, 850, 700))
    label(d, (600, 480), "BLACK BOX", 46)
    label(d, (600, 570), "q: mod16", 40)
    wire(d, [(850, 535), (1100, 535)], PURPLE)
    label(d, (960, 475), "q[3:0]", 36)
    dot(d, 1010, 535)
    box(d, (1200, 430, 1930, 650))
    label(d, (1565, 505), "Y = {h,q[3:0]}", 45)
    label(d, (1565, 580), "five bits", 32)
    wire(d, [(1100, 535), (1200, 535)], PURPLE)
    box(d, (800, 900, 1250, 1100))
    label(d, (1025, 970), "q == 15", 42)
    label(d, (1025, 1040), "AND(q3,q2,q1,q0)", 27)
    wire(d, [(1010, 535), (1010, 900)], PURPLE)
    box(d, (1450, 900, 1910, 1110))
    label(d, (1680, 970), "h DFF", 45)
    label(d, (1680, 1040), "D = h XOR carry", 30)
    wire(d, [(1250, 1005), (1450, 1005)], PURPLE)
    label(d, (1350, 940), "carry", 30)
    wire(d, [(1910, 1005), (2070, 1005), (2070, 730), (1800, 730), (1800, 650)], PURPLE)
    label(d, (1990, 800), "h", 40)
    # Clock is control, never decoded from q.
    label(d, (285, 1240), "clk", 40, GREEN)
    wire(d, [(365, 1240), (600, 1240), (600, 700)], GREEN)
    dot(d, 600, 1240, GREEN)
    wire(d, [(600, 1240), (1680, 1240), (1680, 1110)], GREEN)
    label(d, (1160, 1305), "shared rising edge", 34, GREEN)
    phrase(
        d,
        (1100, 1390),
        "בודקים את הנמוכים לפני החזית; איפוס דורש יישור",
        "Evaluate old low bits; initialization must align both parts",
        lang,
        37,
    )
    im.save(OUT / f"prep-152-same-clock-counter-extension-{lang}.png")


def nmos_symbol(d, x, y, name):
    # Drain at y, source at y+220, gate lead at x-110,y+110.
    wire(d, [(x, y), (x, y + 45)], PURPLE, arrow=False)
    for a, b in ((45, 80), (95, 130), (145, 180)):
        d.line((x, y + a, x, y + b), fill=PURPLE, width=8)
    wire(d, [(x, y + 180), (x, y + 220)], PURPLE, arrow=False)
    d.line((x - 85, y + 40, x - 85, y + 185), fill=PURPLE, width=6)
    wire(d, [(x - 170, y + 110), (x - 85, y + 110)], PURPLE, arrow=False)
    label(d, (x + 150, y + 100), name, 39)
    label(d, (x + 55, y + 17), "D", 28)
    label(d, (x + 55, y + 208), "S", 28)
    label(d, (x - 125, y + 63), "G", 28)


def inverter(lang):
    im, d = canvas("מהפך משני התקני העשרה בלבד", "Inverter using two enhancement NMOS devices", lang, 1540)
    phrase(
        d,
        (1100, 175),
        "העומס מחובר למסילה; הדרייבר נשלט בכניסה",
        "The load is rail-biased; the input controls the driver",
        lang,
        36,
    )
    x = 1200
    d.line((900, 285, 1470, 285), fill=INK, width=6)
    label(d, (1200, 235), "VDD", 43)
    wire(d, [(x, 285), (x, 340)], PURPLE, arrow=False)
    nmos_symbol(d, x, 340, "M_L")
    # Load gate and drain are tied, independently of Vin.
    dot(d, x, 300)
    wire(d, [(1200, 300), (930, 300), (930, 450), (1030, 450)], PURPLE, arrow=False)
    label(d, (645, 395), "G_L = D_L = VDD", 33)
    wire(d, [(1200, 560), (1200, 760)], PURPLE, arrow=False)
    dot(d, 1200, 650)
    wire(d, [(1200, 650), (1900, 650)], GREEN)
    label(d, (1770, 585), "Vout", 45, GREEN)
    nmos_symbol(d, x, 760, "M_D")
    wire(d, [(510, 870), (1030, 870)], PURPLE)
    label(d, (585, 805), "Vin", 42)
    wire(d, [(1200, 980), (1200, 1120)], PURPLE, arrow=False)
    for yy, half in ((1120, 110), (1148, 75), (1176, 35)):
        d.line((1200 - half, yy, 1200 + half, yy), fill=INK, width=6)
    label(d, (1500, 1030), "bodies = 0", 34)
    phrase(d, (560, 1070), "דרייבר חזק יחסית לעומס", "Driver stronger than load", lang, 34)
    label(d, (1100, 1290), "VOH ≈ VDD - VT,L     |     I_load = I_driver", 37)
    phrase(
        d,
        (1100, 1380),
        "רמה גבוהה מוחלשת; זרם סטטי כשהכניסה גבוהה",
        "Degraded high level; static current for high input",
        lang,
        36,
    )
    phrase(
        d,
        (1100, 1460),
        "עומס ריקון הוא חלופה טכנולוגית נפרדת",
        "Depletion load is a separate process-dependent alternative",
        lang,
        33,
    )
    im.save(OUT / f"prep-153-nmos-load-circuit-{lang}.png")


def vtc(lang):
    im, d = canvas(
        "מודל זרם חינוכי של מהפך מבוסס עומס", "Educational current model of the load inverter", lang, 1510
    )
    label(d, (1100, 175), "VDD=5 V   VT0=1 V   normalized beta", 36)
    left, right, top, bottom = 260, 2000, 310, 1110
    for val in range(6):
        xx = left + (right - left) * val / 5
        yy = bottom - (bottom - top) * val / 5
        d.line((xx, top, xx, bottom), fill=GRAY, width=2)
        d.line((left, yy, right, yy), fill=GRAY, width=2)
        label(d, (xx, bottom + 48), str(val), 29)
        label(d, (left - 55, yy), str(val), 29)
    wire(d, [(left, top), (left, bottom), (right + 40, bottom)], INK, width=5)
    label(d, (1150, 1225), "Vin [V]", 39)
    label(d, (155, 265), "Vout [V]", 34)
    entries = [
        (4, 0, PURPLE, "beta_D / beta_L = 4"),
        (16, 0, GREEN, "beta_D / beta_L = 16"),
        (8, 0.4, ORANGE, "ratio = 8, gamma = 0.4"),
    ]
    for index, (ratio, gamma, color, legend) in enumerate(entries):
        pts = []
        for i in range(201):
            vin = i / 40
            vo = dc_output(vin, beta_driver=ratio, gamma=gamma)
            pts.append((left + (right - left) * vin / 5, bottom - (bottom - top) * vo / 5))
        d.line(pts, fill=color, width=6)
        yy = 1320 + index * 58
        d.line((430, yy, 540, yy), fill=color, width=6)
        label(d, (1125, yy), legend, 31, color)
    phrase(
        d,
        (1100, 240),
        "אין כאן מדידת רכיב או הבטחת מרווחי רעש",
        "Not a device measurement or a noise-margin guarantee",
        lang,
        32,
    )
    im.save(OUT / f"prep-153-nmos-dc-model-{lang}.png")


def resistor(d, a, b):
    x1, y1 = a
    x2, y2 = b
    assert y1 == y2
    points = [(x1, y1), (x1 + 20, y1)]
    for i in range(8):
        points.append((x1 + 35 + i * (x2 - x1 - 70) / 7, y1 + (-20 if i % 2 == 0 else 20)))
    points.extend([(x2 - 20, y1), (x2, y1)])
    d.line(points, fill=PURPLE, width=6)


def resistor_question(lang):
    im, d = canvas("רשת ידועה בתוך קופסה סגורה", "Known network inside a closed box", lang, 1430)
    phrase(
        d,
        (1100, 175),
        "נגישים רק ששת המסופים החיצוניים",
        "Only the six external terminals are accessible",
        lang,
        37,
    )
    d.rounded_rectangle((300, 290, 1990, 1080), radius=32, outline=GRAY, width=5)
    for i, y in enumerate((430, 680, 930), 1):
        label(d, (145, y - 65), f"A{i}", 42)
        dot(d, 145, y)
        wire(d, [(145, y), (390, y)], PURPLE, arrow=False)
        resistor(d, (390, y), (660, y))
        label(d, (525, y - 70), f"R{i}", 40)
        wire(d, [(660, y), (840, y)], PURPLE, arrow=False)
        label(d, (2070, y - 65), f"B{i}", 42)
        dot(d, 2070, y)
        wire(d, [(1550, y), (1700, y)], PURPLE, arrow=False)
        resistor(d, (1700, y), (1940, y))
        label(d, (1820, y - 70), f"S{i}", 40)
        wire(d, [(1940, y), (2070, y)], PURPLE, arrow=False)
    wire(d, [(840, 430), (840, 930)], PURPLE, arrow=False)
    wire(d, [(1550, 430), (1550, 930)], PURPLE, arrow=False)
    dot(d, 840, 680)
    dot(d, 1550, 680)
    label(d, (840, 1030), "L", 38)
    label(d, (1550, 1030), "H", 38)
    wire(d, [(840, 680), (1020, 680)], PURPLE, arrow=False)
    resistor(d, (1020, 680), (1360, 680))
    label(d, (1190, 595), "Rc = ?", 45, GREEN)
    wire(d, [(1360, 680), (1550, 680)], PURPLE, arrow=False)
    phrase(
        d,
        (1100, 1200),
        "הקופסה כבויה; יתר המסופים פתוחים בכל מדידה",
        "Power off; all unused terminals float for each reading",
        lang,
        38,
    )
    phrase(
        d,
        (1100, 1295),
        "כל הנגדים חיוביים ולינאריים; אין חיבורים נוספים",
        "All resistors are positive and linear; no other connections",
        lang,
        35,
    )
    im.save(OUT / f"prep-154-seven-resistor-question-network-{lang}.png")


def readings(lang):
    im, d = canvas("ארבע קריאות וביטול תרומות הצד", "Four readings cancel the side branches", lang, 1400)
    rows = [
        ("read", "terminals", "resistance"),
        ("C11", "A1 – B1", "R1 + Rc + S1"),
        ("C22", "A2 – B2", "R2 + Rc + S2"),
        ("LA", "A1 – A2", "R1 + R2"),
        ("LB", "B1 – B2", "S1 + S2"),
    ]
    widths = [360, 580, 950]
    left = 150
    top = 290
    for r, row in enumerate(rows):
        x = left
        for c, value in enumerate(row):
            w = widths[c]
            d.rectangle(
                (x, top + r * 135, x + w, top + (r + 1) * 135),
                fill=PALE if r == 0 else BG,
                outline=GRAY,
                width=3,
            )
            label(d, (x + w / 2, top + r * 135 + 67), value, 39, GREEN if r in (1, 2) else INK)
            x += w
    label(d, (1100, 1080), "Rc = (C11 + C22 - LA - LB) / 2", 47, PURPLE)
    phrase(
        d,
        (1100, 1200),
        "לא נדרש לדעת אף אחד מנגדי הצד בנפרד",
        "No individual side resistor needs to be known",
        lang,
        39,
    )
    phrase(
        d,
        (1100, 1300),
        "קריאות בין צדדים בלבד אינן מזהות את הנגד האמצעי",
        "Cross-only readings do not identify the central resistor",
        lang,
        35,
    )
    im.save(OUT / f"prep-154-four-readings-cancellation-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        counter(language)
        inverter(language)
        vtc(language)
        resistor_question(language)
        readings(language)
    print("Ten clean bilingual diagrams saved.")
