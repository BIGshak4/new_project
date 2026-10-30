"""Bilingual source-independent illustrations for second October30 intake."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, ORANGE = "#fffdf8", "#302344", "#71558c", "#33786d", "#b76530"


def panel(d, rect, color=PURPLE):
    d.rounded_rectangle(rect, 24, fill="#eee7f3" if color == PURPLE else "#e8f1eb", outline=color, width=5)


def pointers(lg):
    im = Image.new("RGB", (2300, 1370), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1150, 90),
        "מצביעים בדידים יכולים לחלוף בלי להיפגש",
        "Discrete pointers can pass without sharing a tick position",
        lg,
        51,
        bold=True,
    )
    text(d, (1150, 190), "L(t)=2+2t       R(t)=98-3t       t=0,1,2,...", 44)
    panel(d, (210, 300, 2090, 800))
    for x, header in [(500, "tick t"), (1100, "L(t)"), (1750, "R(t)")]:
        text(d, (x, 365), header, 45, bold=True)
    for y, t, a, b in [(470, 18, 38, 44), (570, 19, 40, 41), (670, 20, 42, 38), (760, 21, 44, 35)]:
        for x, v in [(500, t), (1100, a), (1750, b)]:
            text(
                d,
                (x, y),
                str(v),
                43,
                color=GREEN if t == 19 else ORANGE if t == 20 else INK,
                bold=t in (19, 20),
            )
    phrase(
        d,
        (1150, 900),
        "אותו תא באותו עדכון דורש זמן שלם",
        "Same cell at the same update requires an integer time",
        lg,
        40,
        bold=True,
    )
    text(d, (1150, 990), "2+2t = 98-3t  =>  5t=96  =>  t=19.2", 46, color=PURPLE, bold=True)
    phrase(
        d,
        (1150, 1090),
        "אין זמן שלם ולכן אין מפגש בדיד",
        "No integer time, hence no discrete meeting",
        lg,
        44,
        bold=True,
        color=GREEN,
    )
    phrase(
        d,
        (1150, 1200),
        "תנועה רציפה בין העדכונים היא הנחה אחרת",
        "Continuous travel between updates is a different assumption",
        lg,
        37,
    )
    text(d, (1150, 1285), "linear interpolation only: t=19.2, position=40.4", 39)
    return im


def paper(lg):
    im = Image.new("RGB", (2500, 1510), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1250, 85),
        "תכנית בדיקה מתחילה בדרישה מדידה",
        "A test plan starts with a measurable requirement",
        lg,
        54,
        bold=True,
    )
    for x, he, en in [
        (340, "דרישה", "Requirement"),
        (950, "שיטת מדידה", "Method"),
        (1560, "ראיה", "Evidence"),
        (2170, "החלטה", "Decision"),
    ]:
        panel(d, (x - 250, 270, x + 250, 460))
        phrase(d, (x, 365), he, en, lg, 43, bold=True)
    for a, b in [(590, 700), (1200, 1310), (1810, 1920)]:
        wire(d, [(a, 365), (b, 365)], GREEN, 7)
    phrase(
        d,
        (1250, 580),
        "מידות נומינליות אינן כל מפרט המוצר",
        "Nominal dimensions are not the whole product specification",
        lg,
        42,
        bold=True,
    )
    text(d, (1250, 665), "A4: 210 x 297 mm     count / grammage / tolerance: obtain from specification", 36)
    cases = [
        (380, "דרישה חסרה", "Requirement missing", "needs_requirement", PURPLE),
        (960, "כל התחום עומד בדרישה", "Entire interval conforms", "pass", GREEN),
        (1540, "כל התחום מחוץ לדרישה", "Entire interval outside", "fail", ORANGE),
        (2120, "חוסר ודאות בגבול", "Boundary uncertainty", "inconclusive", PURPLE),
    ]
    for x, he, en, state, color in cases:
        panel(d, (x - 260, 820, x + 260, 1080), color)
        phrase(d, (x, 895), he, en, lg, 30, bold=True)
        text(d, (x, 1000), state, 30, color=color, bold=True)
    phrase(
        d,
        (1250, 1190),
        "קודם תווית ואריזה ואז ספירה ומדידה ודגימות שימוש",
        "Inspect label and package before counting, measuring and use samples",
        lg,
        38,
        bold=True,
    )
    phrase(
        d,
        (1250, 1290),
        "תיעוד מדגם אינו אישור שכל דף בחבילה תקין",
        "A sample report does not certify every sheet in the pack",
        lg,
        39,
    )
    phrase(
        d,
        (1250, 1410),
        "המודל בדק החלטות סינתטיות בלבד ולא חבילת נייר אמיתית",
        "The model checked synthetic decisions, not a physical paper package",
        lg,
        37,
        bold=True,
        color=GREEN,
    )
    return im


def coins(lg):
    im = Image.new("RGB", (2200, 1330), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1100, 90),
        "בוחרים שלושה והופכים רק אותם",
        "Choose three coins and flip only those",
        lg,
        54,
        bold=True,
    )
    text(d, (1100, 190), "total=30      black-up=3      white-up=27", 43)
    for x, he, en, formula in [
        (600, "הקבוצה שנבחרה", "Selected group", "3 coins"),
        (1600, "שאר המטבעות", "Remaining coins", "27 coins"),
    ]:
        panel(d, (x - 410, 300, x + 410, 560))
        phrase(d, (x, 375), he, en, lg, 40, bold=True)
        text(d, (x, 480), formula, 53, bold=True, color=PURPLE)
    phrase(
        d,
        (1100, 670),
        "מספר השחורים שנבחר אינו ידוע ואין צורך לגלות אותו",
        "The selected black count is unknown and need not be discovered",
        lg,
        37,
    )
    text(d, (1100, 780), "selected black before:     x       0    1    2    3", 41)
    text(d, (1100, 880), "selected black after:    3-x       3    2    1    0", 41, color=GREEN, bold=True)
    text(d, (1100, 980), "remaining black:         3-x       3    2    1    0", 41, color=GREEN, bold=True)
    phrase(
        d,
        (1100, 1120),
        "הקבוצות אינן חייבות להיות שוות בגודלן",
        "Group sizes need not be equal",
        lg,
        45,
        bold=True,
    )
    phrase(
        d,
        (1100, 1230),
        "הבחירה וההיפוך קבועים מראש ואינם רואים את הצדדים",
        "Selection and flips are fixed without observing faces",
        lg,
        37,
    )
    return im


def hats(lg):
    im = Image.new("RGB", (2400, 1640), PAPER)
    d = ImageDraw.Draw(im)
    phrase(
        d,
        (1200, 85),
        "שלושה צבעים ושלוש הבטחות",
        "Three colors and three guaranteed results",
        lg,
        52,
        bold=True,
    )
    text(d, (1200, 180), "front: 1 ... 100 :rear      speakers: 100,99,...,1      colors: 0,1,2", 36)
    for y, num, he, en, formula in [
        (
            305,
            "50",
            "כל זוג משתמש בשם הצבע כהודעה לשותף",
            "Each pair relays the front partner color",
            "rear of pair: announce the partner's color",
        ),
        (
            645,
            "98",
            "שני הראשונים מקודדים שתי זוגיויות צבע",
            "Two first speakers encode two color parities",
            "red parity + blue parity of hats 1..98",
        ),
        (
            985,
            "99",
            "הראשון מקודד סכום מודולו שלוש",
            "The first speaker encodes a sum modulo three",
            "S=(c1+...+c99) mod 3",
        ),
    ]:
        panel(d, (110, y, 2290, y + 265), GREEN if num == "99" else PURPLE)
        text(d, (300, y + 125), num, 89, bold=True, color=GREEN if num == "99" else PURPLE)
        phrase(d, (1370, y + 80), he, en, lg, 39, bold=True)
        text(d, (1370, y + 175), formula, 38)
    text(
        d,
        (1200, 1340),
        "my color = (S - visible colors - previous CORRECT colors) mod 3",
        38,
        color=GREEN,
        bold=True,
    )
    phrase(
        d,
        (1200, 1450),
        "הודעת הראשון אינה מידע ודאי על הכובע שלו",
        "The first message does not reveal the speaker's own hat",
        lg,
        37,
    )
    phrase(
        d,
        (1200, 1550),
        "צבע כובע הראשון אינו נראה לו ולכן לא מובטחת הצלת כולם",
        "The first speaker cannot observe their own hat, so saving everyone is impossible",
        lg,
        36,
        bold=True,
    )
    return im


if __name__ == "__main__":
    for lg in ("he", "en"):
        for number, stem, func in [
            (158, "discrete-pointer-crossing", pointers),
            (159, "paper-test-plan", paper),
            (59, "thirty-coins-three-black", coins),
            (96, "three-color-stages", hats),
        ]:
            func(lg).save(OUT / f"prep-{number:03d}-{stem}-{lg}.png")
