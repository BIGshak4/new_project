"""Independent bilingual drawings for seven batch70 reasoning items."""

from math import cos, sin, pi, sqrt
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, ORANGE, BLUE = (
    "#fffdf8",
    "#302344",
    "#71558c",
    "#33786d",
    "#b76530",
    "#4678af",
)


def panel(d, rect, color=PURPLE):
    d.rounded_rectangle(
        rect,
        24,
        fill="#eee7f3" if color == PURPLE else "#e8f1eb",
        outline=color,
        width=5,
    )


def clock(lg):
    im = Image.new("RGB", (2400, 1430), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1200, 85),
        "שני מוטות ושלושה סכומים שווים",
        "Two straight rods, three equal number sums",
        lg,
        56,
        bold=True,
    )
    cx, cy, r = 650, 750, 440
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white", outline=INK, width=7)
    u = (sin(pi / 12), -cos(pi / 12))
    v = (cos(pi / 12), sin(pi / 12))
    for side in (-1, 1):
        center = (cx + side * r * 0.5 * u[0], cy + side * r * 0.5 * u[1])
        a = (center[0] - r * sqrt(3) / 2 * v[0], center[1] - r * sqrt(3) / 2 * v[1])
        b = (center[0] + r * sqrt(3) / 2 * v[0], center[1] + r * sqrt(3) / 2 * v[1])
        d.line([a, b], fill=PURPLE, width=12)
    for n in range(1, 13):
        col = GREEN if n in (11, 12, 1, 2) else ORANGE if n in (5, 6, 7, 8) else INK
        text(
            d,
            (cx + 365 * sin(n * pi / 6), cy - 365 * cos(n * pi / 6)),
            str(n),
            62,
            bold=True,
            color=col,
        )
    for y, formula, col in [
        (460, "11 + 12 + 1 + 2 = 26", GREEN),
        (720, "3 + 4 + 9 + 10 = 26", PURPLE),
        (980, "5 + 6 + 7 + 8 = 26", ORANGE),
    ]:
        panel(d, (1220, y - 100, 2310, y + 110), col)
        text(d, (1765, y), formula, 48, bold=True, color=col)
    text(d, (1200, 1260), "1+2+...+12=78       78/3=26", 43)
    phrase(
        d,
        (1200, 1350),
        "המוטות מקבילים ואינם עוברים על מספר",
        "The rods are parallel and avoid every number",
        lg,
        43,
        bold=True,
    )
    return im


def coins_game(lg):
    im = Image.new("RGB", (2400, 1430), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1200, 85),
        "מתחילים במרכז ומשיבים בחצי סיבוב",
        "Start in the center and answer by a half turn",
        lg,
        53,
        bold=True,
    )
    cx, cy, r = 650, 745, 430
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white", outline=INK, width=7)
    for x, y, col, label in [
        (0, 0, PURPLE, "O"),
        (190, 150, ORANGE, "P"),
        (-190, -150, GREEN, "-P"),
    ]:
        xx, yy = cx + x, cy - y
        d.ellipse(
            (xx - 66, yy - 66, xx + 66, yy + 66),
            fill="#eee7f3" if col == PURPLE else "#e8f1eb",
            outline=col,
            width=6,
        )
        text(d, (xx, yy), label, 36, bold=True, color=col)
    for y, he, en, formula in [
        (425, "תור ראשון", "First turn", "O = (0,0)"),
        (690, "אחרי כל מהלך יריב", "After each opponent move", "(x,y) -> (-x,-y)"),
        (955, "אינווריאנט", "Invariant", None),
    ]:
        panel(d, (1210, y - 95, 2320, y + 125))
        phrase(d, (1765, y - 25), he, en, lg, 40, bold=True)
        if formula is not None:
            text(d, (1765, y + 65), formula, 34)
        else:
            phrase(
                d,
                (1765, y + 65),
                "לכל מטבע בן זוג ממול",
                "Each off-center coin has an opposite partner",
                lg,
                34,
            )
    phrase(
        d,
        (1200, 1250),
        "אם מהלך היריב חוקי גם התשובה הסימטרית חוקית",
        "A legal opponent move always has a legal symmetric reply",
        lg,
        40,
        bold=True,
        color=GREEN,
    )
    phrase(
        d,
        (1200, 1350),
        "מטבעות זהים בשטח חיובי מבטיחים משחק סופי",
        "Equal positive-area coins make the game finite",
        lg,
        40,
    )
    return im


def boat(lg):
    im = Image.new("RGB", (2500, 1500), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1250, 85),
        "משווים נפח מים שנדחה לפני ואחרי",
        "Compare displaced water volume before and after",
        lg,
        55,
        bold=True,
    )
    phrase(
        d,
        (1250, 185),
        "כשהחפץ בסירה משקלו קובע את תוספת הדחייה",
        "While carried in the boat, the object adds its weight to displacement",
        lg,
        39,
    )
    text(d, (1250, 275), "V_before = m / rho_water", 48, bold=True, color=PURPLE)
    for x, he, en, state, formula in [
        (440, "שוקע", "Sinks", "dense", "V_after = V_object < m/rho_water"),
        (1250, "צף", "Floats", "light", "V_after = m/rho_water"),
        (
            2060,
            "ציפה ניטרלית",
            "Neutral buoyancy",
            "neutral",
            "V_after = V_object = m/rho_water",
        ),
    ]:
        panel(d, (x - 365, 390, x + 365, 1120), GREEN)
        phrase(d, (x, 465), he, en, lg, 44, bold=True)
        d.rectangle((x - 280, 700, x + 280, 990), fill="#d9eaf6")
        d.line((x - 280, 700, x + 280, 700), fill=BLUE, width=7)
        yy = 930 if state == "dense" else 695 if state == "light" else 820
        d.rounded_rectangle(
            (x - 65, yy - 45, x + 65, yy + 45),
            12,
            fill=ORANGE if state == "dense" else PURPLE,
        )
        text(d, (x, 590), formula, 29, bold=True, color=GREEN)
        phrase(
            d,
            (x, 1060),
            "המפלס יורד" if state == "dense" else "המפלס אינו משתנה",
            "Level falls" if state == "dense" else "Level unchanged",
            lg,
            37,
            bold=True,
        )
    phrase(
        d,
        (1250, 1250),
        "לאחר שהגלים נרגעו וללא שפיכה או שינוי בחפץ",
        "After waves settle, without spill or object changes",
        lg,
        42,
        bold=True,
    )
    text(
        d,
        (1250, 1355),
        "delta_h = (V_after - m/rho_water) / pool_area",
        42,
        color=GREEN,
    )
    return im


def nine(lg):
    im = Image.new("RGB", (2500, 1490), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1250, 85),
        "תשעה מטבעות שאחד מהם קל מהשאר",
        "Nine coins, one counterfeit known to be lighter",
        lg,
        53,
        bold=True,
    )
    panel(d, (620, 235, 1880, 450))
    text(d, (1250, 345), "(1,2,3)  vs  (4,5,6)", 48, bold=True)
    for x, he, en, group in [
        (420, "שמאל קל", "Left lighter", "1,2,3"),
        (1250, "מאוזן", "Balanced", "7,8,9"),
        (2080, "ימין קל", "Right lighter", "4,5,6"),
    ]:
        wire(d, [(1250, 450), (x, 600)], PURPLE, 6)
        panel(d, (x - 330, 610, x + 330, 870), GREEN)
        phrase(d, (x, 685), he, en, lg, 38, bold=True)
        text(d, (x, 795), group, 56, bold=True, color=GREEN)
    phrase(
        d,
        (1250, 1000),
        "בקבוצה שנשארה שוקלים את הראשון מול השני",
        "In the remaining group, weigh the first against the second",
        lg,
        43,
        bold=True,
    )
    phrase(
        d,
        (1250, 1110),
        "הקל מבין השניים נבחר ואם מאוזן נבחר השלישי",
        "Choose the lighter of the two; if balanced, choose the third",
        lg,
        37,
    )
    text(d, (1250, 1240), "3 * 3 = 3^2 = 9", 43, color=PURPLE, bold=True)
    phrase(
        d,
        (1250, 1360),
        "בכל מסלול בדיוק שתי שקילות ואין משקולת חיצונית",
        "Every path uses exactly two weighings and no external weight",
        lg,
        40,
    )
    return im


def urns(lg):
    im = Image.new("RGB", (2300, 1420), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1150, 85),
        "הבחירה היא תיבה ואז כדור ולא כדור מכלל המאה",
        "Choose an urn, then a ball within that urn",
        lg,
        51,
        bold=True,
    )
    for x, label, formula in [(600, "A", "1 red"), (1700, "B", "49 red + 50 white")]:
        panel(d, (x - 400, 310, x + 400, 1010), GREEN)
        text(d, (x, 400), label, 52, bold=True)
        if x == 600:
            d.ellipse((x - 75, 565, x + 75, 715), fill="#b54e56", outline=INK, width=4)
        else:
            d.ellipse((x - 175, 560, x - 25, 710), fill="#b54e56", outline=INK, width=4)
            d.ellipse((x + 25, 560, x + 175, 710), fill="white", outline=INK, width=4)
        if lg == "he":
            phrase(
                d,
                (x, 820),
                "אדום אחד" if x == 600 else "ארבעים ותשעה אדומים וחמישים לבנים",
                formula,
                lg,
                37,
                bold=True,
            )
        else:
            text(d, (x, 820), formula, 48, bold=True)
        text(d, (x, 930), "P(red | urn)=1" if x == 600 else "P(red | urn)=49/99", 38)
    text(
        d,
        (1150, 1130),
        "P(red)=1/2 * 1 + 1/2 * 49/99 = 74/99",
        45,
        bold=True,
        color=GREEN,
    )
    text(d, (1150, 1225), "74/99 = 0.747474...", 42)
    phrase(
        d,
        (1150, 1330),
        "כל הכדורים משובצים ושתי התיבות אינן ריקות",
        "All balls are allocated and both urns are nonempty",
        lg,
        39,
    )
    return im


def bottles(lg):
    im = Image.new("RGB", (2500, 1550), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1250, 85),
        "חמש מאות בקבוקים מסומנים בתשע סיביות",
        "Five hundred bottles fit in nine binary bits",
        lg,
        54,
        bold=True,
    )
    text(d, (1250, 190), "2^8 = 256 < 500 <= 512 = 2^9", 48, bold=True, color=GREEN)
    phrase(
        d,
        (1250, 290),
        "תשעה טועמים מספיקים והעשירי יכול להישאר ללא תערובת",
        "Nine testers suffice; the tenth can remain unused",
        lg,
        40,
    )
    headers = [
        ("מספר הבקבוק", "public bottle"),
        ("תווית פנימית", "internal label"),
        (None, "code T9...T1"),
        ("תערובות", "pools"),
    ]
    cols = [300, 850, 1430, 2070]
    panel(d, (90, 400, 2410, 1160))
    for x, (he, en) in zip(cols, headers, strict=True):
        if he is None:
            text(d, (x, 480), "T9...T1", 35, bold=True)
        else:
            phrase(d, (x, 480), he, en, lg, 35, bold=True)
    rows = [
        ("1", "0", "000000000", "none"),
        ("2", "1", "000000001", "T1"),
        ("3", "2", "000000010", "T2"),
        ("14", "13", "000001101", "T1,T3,T4"),
        ("500", "499", "111110011", "T1,T2,T5,T6,T7,T8,T9"),
    ]
    for i, row in enumerate(rows):
        for x, v in zip(cols, row, strict=True):
            if v == "none":
                phrase(d, (x, 620 + i * 115), "ללא", v, lg, 32)
            else:
                text(d, (x, 620 + i * 115), v, 32, bold=i == 4)
    phrase(
        d,
        (1250, 1260),
        "כל הטעימות מתחילות יחד וקוראים את התוצאה במועד הסיום",
        "All pools start together; read binary outcomes at the deadline",
        lg,
        39,
        bold=True,
    )
    text(d, (1250, 1360), "positive=1, negative=0       b = decoded label + 1", 42)
    phrase(
        d,
        (1250, 1460),
        "כל הטועמים חיים מזהה את בקבוק אחד תחת הבטחת רעל יחיד",
        "All alive identifies bottle one under the exactly-one-poison promise",
        lg,
        36,
    )
    return im


def hats(lg):
    im = Image.new("RGB", (2450, 1510), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1225, 85),
        "אלף כובעים ושתי הבטחות מפורשות",
        "One thousand hats, two explicit guarantees",
        lg,
        55,
        bold=True,
    )
    panel(d, (100, 280, 2350, 790))
    phrase(d, (1225, 355), "אסטרטגיית קבוצות", "Grouped strategy", lg, 44, bold=True)
    text(d, (1225, 465), "332 * 3  +  1 * 4  =  1000", 43)
    text(d, (1225, 575), "332 * 2 + 3 = 667 = ceil(2000/3)", 43, color=GREEN, bold=True)
    phrase(
        d,
        (1225, 695),
        "בכל קבוצה הראשון מודיע זוגיות והאחרים משחזרים צבע",
        "Each block leader signals parity; the others recover their colors",
        lg,
        39,
    )
    panel(d, (100, 890, 2350, 1265), GREEN)
    phrase(
        d,
        (1225, 970),
        "אסטרטגיית זוגיות אחת לכולם",
        "One global parity strategy",
        lg,
        45,
        bold=True,
    )
    phrase(
        d,
        (1225, 1080),
        "תשע מאות תשעים ותשע תשובות נכונות בוודאות",
        "999 guaranteed correct replies after one parity message",
        lg,
        43,
        bold=True,
        color=GREEN,
    )
    phrase(
        d,
        (1225, 1185),
        "אי אפשר להבטיח את צבע כובע הדובר הראשון",
        "The first speaker's own hat cannot be guaranteed",
        lg,
        39,
    )
    phrase(
        d,
        (1225, 1390),
        "רואים רק קדימה ושומעים את כל התשובות הקודמות",
        "Only forward hats are visible; every earlier reply is audible",
        lg,
        40,
    )
    return im


if __name__ == "__main__":
    for lg in ("he", "en"):
        for number, stem, func in [
            (165, "clock-three-sums", clock),
            (166, "center-half-turn-game", coins_game),
            (167, "boat-density-displacement", boat),
            (168, "nine-lighter-coins", nine),
            (169, "two-urn-allocation", urns),
            (73, "five-hundred-bottles", bottles),
            (96, "thousand-binary-stages", hats),
        ]:
            func(lg).save(OUT / f"prep-{number:03d}-{stem}-{lg}.png")
