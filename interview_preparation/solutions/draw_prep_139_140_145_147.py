"""Clean, deterministic bilingual diagrams; originals stay in private archive."""

from math import atan2, cos, sin
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG = "#fffdf8"
INK = "#302344"
PURPLE = "#624883"
PALE = "#eee7f5"
GREEN = "#30766a"
GRAY = "#dbd4e2"


def canvas(he, en, lang, h=1400):
    im = Image.new("RGB", (2200, h), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1100, 88), he, en, lang, 51, bold=True, color=INK)
    return im, d


def label(d, xy, value, size=38, color=INK):
    text(d, xy, value, size, bold=True, color=color)


def box(d, rect):
    d.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=5)


def curve(d, pts, color=PURPLE):
    points = []
    for i in range(101):
        t = i / 100
        u = 1 - t
        points.append(
            (
                u**3 * pts[0][0] + 3 * u * u * t * pts[1][0] + 3 * u * t * t * pts[2][0] + t**3 * pts[3][0],
                u**3 * pts[0][1] + 3 * u * u * t * pts[1][1] + 3 * u * t * t * pts[2][1] + t**3 * pts[3][1],
            )
        )
    d.line(points, fill=BG, width=17)
    d.line(points, fill=color, width=5)
    a, b = points[-4], points[-1]
    angle = atan2(b[1] - a[1], b[0] - a[0])
    d.polygon(
        (
            b,
            (b[0] - 24 * cos(angle - 0.4), b[1] - 24 * sin(angle - 0.4)),
            (b[0] - 24 * cos(angle + 0.4), b[1] - 24 * sin(angle + 0.4)),
        ),
        fill=color,
    )


def controller(lang):
    im, d = canvas(
        "בקר שמסריאל בקשות עד לסיום אמיתי", "Serialized controller waits for actual completion", lang, 1500
    )
    phrase(
        d,
        (1100, 178),
        "כל מעבר מתרחש בחזית; אירועי קבלה וסיום נפרדים",
        "Every transition is sampled at an edge; handshakes are distinct",
        lang,
        35,
    )
    positions = {"IDLE": (370, 480), "ISSUE": (1100, 480), "WAIT": (1830, 480), "RESP": (1100, 1040)}
    curve(d, [(515, 480), (650, 480), (800, 480), (955, 480)])
    label(d, (735, 420), "request accepted", 31)
    curve(d, [(1245, 480), (1410, 480), (1510, 480), (1685, 480)])
    label(d, (1465, 405), "cmd accepted", 31)
    label(d, (1465, 447), "not complete", 27)
    curve(d, [(1790, 620), (1720, 890), (1420, 1040), (1245, 1040)])
    label(d, (1870, 920), "completion", 31)
    curve(d, [(1100, 625), (1100, 730), (1100, 790), (1100, 895)])
    label(d, (1365, 720), "cmd accepted", 30)
    label(d, (1365, 765), "+ completion", 30)
    curve(d, [(955, 1040), (670, 1040), (370, 860), (370, 625)])
    label(d, (480, 1010), "response consumed", 29)
    for name, (x, y) in positions.items():
        d.ellipse((x - 145, y - 145, x + 145, y + 145), fill=PALE, outline=PURPLE, width=5)
        label(d, (x, y - 35), name, 44)
        label(
            d,
            (x, y + 28),
            {"IDLE": "accept one", "ISSUE": "hold command", "WAIT": "one active", "RESP": "hold response"}[
                name
            ],
            25,
        )
        label(
            d,
            (x, y + 72),
            {"IDLE": "R/W arbiter", "ISSUE": "cmd_valid", "WAIT": "busy", "RESP": "resp_valid"}[name],
            24,
            GREEN,
        )
    wire(d, [(90, 480), (215, 480)], INK)
    phrase(
        d,
        (1100, 1270),
        "בכל מקרה אחר נשארים במצב; אין קבלה נוספת בזמן העיסוק",
        "Otherwise hold state; no further acceptance while busy",
        lang,
        36,
    )
    phrase(
        d,
        (1100, 1360),
        "אישור כתיבה חייב להבטיח שהנתון גלוי לקריאה הבאה",
        "Write ACK must guarantee visibility to the next read",
        lang,
        34,
    )
    im.save(OUT / f"prep-139-controller-states-{lang}.png")


def square_question(lang):
    im, d = canvas("ממשק הרכיב הנתון", "Specified component interface", lang, 1050)
    box(d, (720, 300, 1510, 840))
    phrase(d, (1115, 560), "רכיב לתכנון", "Component to design", lang, 45, bold=True)
    for y, name in ((450, "clk"), (710, "rst")):
        wire(d, [(230, y), (720, y)], PURPLE)
        label(d, (340, y - 60), name, 49)
    for y, name in ((450, "n"), (710, "n²")):
        wire(d, [(1510, y), (1990, y)], GREEN)
        label(d, (1800, y - 60), name, 49, GREEN)
    phrase(
        d,
        (1100, 952),
        "גבול סופי ידוע; יש להגדיר אתחול והתנהגות בגבול",
        "Known finite limit; define initialization and terminal behavior",
        lang,
        37,
    )
    im.save(OUT / f"prep-140-cycle-square-question-{lang}.png")


def square_solution(lang):
    im, d = canvas(
        "מספר המחזור וריבועו מתוך המצב הקודם", "Cycle index and square from the previous state", lang, 1500
    )
    label(d, (1100, 185), "(n+1)² = n² + (2n+1)", 48, PURPLE)
    box(d, (280, 370, 730, 610))
    label(d, (505, 450), "n register", 45)
    label(d, (505, 535), "old n", 36)
    box(d, (1450, 370, 1900, 610))
    label(d, (1675, 450), "s register", 45)
    label(d, (1675, 535), "old s = n²", 36)
    box(d, (280, 930, 730, 1110))
    label(d, (505, 1020), "INC(n)", 42)
    box(d, (1450, 930, 1900, 1110))
    label(d, (1675, 1020), "ADD", 46)
    wire(d, [(280, 490), (150, 490), (150, 1020), (280, 1020)], PURPLE)
    wire(d, [(505, 930), (505, 610)], PURPLE)
    label(d, (600, 775), "next n", 31)
    wire(d, [(1900, 490), (2050, 490), (2050, 1020), (1900, 1020)], GREEN)
    wire(d, [(1675, 930), (1675, 610)], GREEN)
    label(d, (1790, 775), "next s", 31)
    box(d, (900, 690, 1260, 850))
    label(d, (1080, 770), "{n,1}", 44, PURPLE)
    wire(d, [(730, 490), (1080, 490), (1080, 690)], PURPLE)
    wire(d, [(1260, 770), (1335, 770), (1335, 1020), (1450, 1020)], PURPLE)
    label(d, (1080, 898), "fixed wiring", 30)
    phrase(
        d,
        (1100, 1230),
        "איפוס מאפס את שניהם; בהגעה לגבול שניהם נשמרים",
        "Reset clears both; at the terminal limit both hold",
        lang,
        39,
    )
    label(d, (1100, 1320), "n_next = n+1       s_next = s+{n,1}", 37)
    phrase(
        d,
        (1100, 1405),
        "המשוואות משתמשות בערכים שלפני החזית",
        "Both equations use values before the edge",
        lang,
        36,
    )
    im.save(OUT / f"prep-140-square-recurrence-{lang}.png")


def address(lang):
    im, d = canvas("מגדיל אחד לשלוש תוספות", "One incrementer shared by three additions", lang, 1600)
    phrase(
        d, (1100, 176), "הביטים הנמוכים עוקפים את רכיב ההגדלה", "Low bits bypass the incrementer", lang, 37
    )
    box(d, (440, 350, 770, 810))
    label(d, (605, 425), "MUX", 45)
    for y, name in ((530, "A"), (630, "{0,A[7:1]}"), (730, "{00,A[7:2]}")):
        wire(d, [(80, y), (440, y)], PURPLE)
        label(d, (245, y - 45), name, 31)
    box(d, (980, 480, 1340, 740))
    label(d, (1160, 550), "INC8", 47)
    label(d, (1160, 640), "+1 mod 256", 33)
    wire(d, [(770, 610), (980, 610)], PURPLE)
    box(d, (1530, 350, 2000, 810))
    label(d, (1765, 425), "ROUTE", 45)
    wire(d, [(1340, 610), (1530, 610)], PURPLE)
    label(d, (1765, 520), "SIZE=1: INC", 31)
    label(d, (1765, 620), "SIZE=2: {INC,A0}", 29)
    label(d, (1765, 720), "SIZE=4: {INC[6:0],A1:0}", 24)
    wire(d, [(2000, 610), (2130, 610)], GREEN)
    label(d, (2050, 550), "routed", 29, GREEN)
    wire(d, [(170, 860), (170, 1020), (1765, 1020), (1765, 810)], GREEN)
    label(d, (820, 960), "original A[1:0] bypass", 36, GREEN)
    label(d, (605, 905), "select: SIZE", 32)
    box(d, (790, 1140, 1900, 1320))
    label(d, (1345, 1196), "carry = (SIZE==1) AND A7 AND ... AND A0", 31)
    label(d, (1345, 1260), "Y[7:0] = routed[7:0]    Y8 = routed8 OR carry", 29)
    phrase(
        d,
        (1100, 1420),
        "הגדלה של החלק העליון והחזרת הביטים הנמוכים",
        "Increment the upper partition and restore the low bits",
        lang,
        38,
    )
    label(d, (1100, 1500), "A = 2^k*U + L  →  A+2^k = 2^k*(U+1) + L", 35)
    im.save(OUT / f"prep-145-single-incrementer-routing-{lang}.png")


def swap_question(lang):
    im, d = canvas(
        "נתיב הנתונים הנתון והבקרה הנפרדת", "Supplied datapath and separate control wiring", lang, 1510
    )
    # Green control is independent of the purple data paths; all joins explicit.
    label(d, (300, 255), "LOAD", 42, GREEN)
    wire(d, [(420, 255), (600, 255), (600, 405)], GREEN)
    d.ellipse((592, 247, 608, 263), fill=GREEN)
    wire(d, [(600, 255), (1080, 255)], GREEN, arrow=False)
    d.polygon(((1080, 215), (1080, 295), (1160, 255)), outline=GREEN, width=5)
    d.ellipse((1160, 243, 1184, 267), outline=GREEN, width=4, fill=BG)
    wire(d, [(1184, 255), (1600, 255), (1600, 405)], GREEN)
    label(d, (1370, 205), "NOT LOAD", 34, GREEN)
    for x, name in ((600, "Y"), (1600, "X")):
        box(d, (x - 190, 405, x + 190, 650))
        label(d, (x, 525), name, 58)
        label(d, (x, 367), "EN", 28, GREEN)
    # Both output buses feed the ALU; feedback data inputs enter outer sides.
    wire(d, [(600, 650), (600, 800), (930, 800), (930, 900)], PURPLE)
    wire(d, [(1600, 650), (1600, 800), (1270, 800), (1270, 900)], PURPLE)
    d.polygon(((800, 900), (1400, 900), (1300, 1110), (900, 1110)), fill=PALE, outline=PURPLE, width=5)
    label(d, (1100, 995), "ALU", 49)
    wire(d, [(460, 1010), (850, 1010)], GREEN)
    label(d, (570, 955), "SEL", 37, GREEN)
    label(d, (1100, 165), "XOR / AND / OR / NOR / NAND", 31)
    wire(d, [(1100, 1110), (1100, 1265), (230, 1265), (230, 525), (410, 525)], PURPLE)
    d.ellipse((1092, 1257, 1108, 1273), fill=PURPLE)
    wire(d, [(1100, 1265), (1970, 1265), (1970, 525), (1790, 525)], PURPLE)
    phrase(
        d,
        (1100, 1370),
        "הנחת עריכה: אוגרים דוגמים בחזית משותפת",
        "Editorial model: registers capture at a shared edge",
        lang,
        37,
    )
    phrase(
        d,
        (1100, 1450),
        "ירוק הוא בקרה; סגול הוא נתון; אין חיבור בין המסלולים",
        "Green is control; purple is data; the paths are not connected",
        lang,
        34,
    )
    im.save(OUT / f"prep-147-alu-swap-question-datapath-{lang}.png")


def swap_solution(lang):
    im, d = canvas(
        "החלפה באמצעות שלוש חזיתות קליטה", "Swap through three controlled capture edges", lang, 1280
    )
    rows = [
        ("edge", "SEL", "LOAD", "X", "Y"),
        ("start", "—", "—", "x", "y"),
        ("1", "XOR", "0", "x XOR y", "y"),
        ("2", "XOR", "1", "x XOR y", "x"),
        ("3", "XOR", "0", "y", "x"),
    ]
    widths = [240, 330, 270, 550, 550]
    left = 130
    top = 300
    for r, row in enumerate(rows):
        x = left
        for c, value in enumerate(row):
            w = widths[c]
            d.rectangle(
                (x, top + r * 130, x + w, top + (r + 1) * 130),
                fill=PALE if r == 0 else BG,
                outline=GRAY,
                width=3,
            )
            label(d, (x + w / 2, top + r * 130 + 65), value, 37, GREEN if r == 4 else INK)
            x += w
    phrase(
        d,
        (1100, 1050),
        "בכל חזית רק האוגר שנבחר משתנה",
        "Only the selected register changes at each edge",
        lang,
        39,
    )
    phrase(
        d,
        (1100, 1145),
        "החזקה לאחר החזית השלישית דורשת חוזה בקרה נוסף",
        "Holding after edge three needs an additional control contract",
        lang,
        35,
    )
    im.save(OUT / f"prep-147-xor-swap-three-captures-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        controller(language)
        square_question(language)
        square_solution(language)
        address(language)
        swap_question(language)
        swap_solution(language)
    print("12 bilingual authored diagrams saved; source images unchanged.")
