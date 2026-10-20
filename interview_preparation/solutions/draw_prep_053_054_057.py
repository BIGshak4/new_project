"""Reproducible bilingual diagrams; no source screenshot is shown to learners.

Use the bundled Python runtime with Pillow. Hebrew-only labels are reversed for
Pillow builds without RAQM; identifiers/formulas are drawn separately in LTR.
"""
from pathlib import Path
from math import atan2, cos, sin, pi
from PIL import Image, ImageDraw, ImageFont

BANK = Path(__file__).resolve().parents[1]
OUT = BANK / "diagrams"
INK = "#202d49"
BLUE = "#355fa0"
GREEN = "#267660"
ORANGE = "#a16b1e"
GRAY = "#68758c"


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/" + ("segoeuib.ttf" if bold else "segoeui.ttf"), size)


def label(d, xy, text, size=40, fill=INK, bold=False, he=False):
    d.text(xy, text[::-1] if he else text, font=font(size, bold), fill=fill, anchor="mm")


def arrow(d, points, color=BLUE, width=7):
    d.line(points, fill=color, width=width, joint="curve")
    a, b = points[-2:]
    angle = atan2(b[1] - a[1], b[0] - a[0])
    head = [b, (b[0]-28*cos(angle-pi/7), b[1]-28*sin(angle-pi/7)),
            (b[0]-28*cos(angle+pi/7), b[1]-28*sin(angle+pi/7))]
    d.polygon(head, fill=color)


def box(d, rect, color=BLUE, bg="#f2f6fd"):
    d.rounded_rectangle(rect, 30, fill=bg, outline=color, width=6)


def doorway(language):
    he = language == "he"
    im = Image.new("RGB", (3000, 1600), "white")
    d = ImageDraw.Draw(im)
    label(d, (1500, 110), "ספירת אנשים באמצעות שני גלאים" if he else "Count people using two doorway sensors", 66, bold=True, he=he)
    label(d, (500, 380), "מחוץ לחדר" if he else "OUTSIDE", 57, bold=True, he=he)
    label(d, (2450, 380), "בתוך החדר" if he else "ROOM", 57, bold=True, he=he)
    # Two distinct sensor zones, close enough to require overlap during crossing.
    for x, name, color in ((1250, "A", BLUE), (1730, "B", GREEN)):
        d.rounded_rectangle((x-130, 470, x+130, 1060), 35, fill="#e7eef9" if name == "A" else "#e5f4ed", outline=color, width=5)
        d.line((x, 460, x, 1070), fill=color, width=12)
        label(d, (x, 410), name, 70, color, bold=True)
    d.line((1000, 470, 1000, 650), fill=GRAY, width=13)
    d.line((2000, 470, 2000, 650), fill=GRAY, width=13)
    d.line((1000, 900, 1000, 1080), fill=GRAY, width=13)
    d.line((2000, 900, 2000, 1080), fill=GRAY, width=13)
    arrow(d, [(500, 770), (2460, 770)], GREEN, 10)
    label(d, (1500, 1170), "כיוון כניסה לחדר" if he else "Direction of entry into the room", 48, GREEN, bold=True, he=he)
    label(d, (1500, 1320), "אחד פירושו זיהוי אדם באזור הגלאי" if he else "1 means a person occupies that sensor's zone", 44, he=he)
    label(d, (1500, 1410), "אפס פירושו שהאזור פנוי" if he else "0 means that sensor's zone is clear", 44, he=he)
    im.save(OUT / f"prep-053-doorway-prompt-{language}.png")


def fsm(language):
    he = language == "he"
    im = Image.new("RGB", (3600, 2200), "white")
    d = ImageDraw.Draw(im)
    label(d, (1800, 110), "מכונת מצבים לזיהוי מעבר מלא" if he else "State machine: count only a complete crossing", 66, bold=True, he=he)
    xs = [330, 1065, 1800, 2535, 3270]
    for y, states, inputs, delta, color in (
        (650, ["IDLE", "E1", "E2", "E3", "IDLE"], ["10", "11", "01", "00 / +1"], "+1", GREEN),
        (1400, ["IDLE", "X1", "X2", "X3", "IDLE"], ["01", "11", "10", "00 / -1"], "-1", BLUE),
    ):
        for x, state in zip(xs, states):
            d.ellipse((x-150, y-150, x+150, y+150), fill="#f3f7fc", outline=color, width=7)
            label(d, (x, y), state, 54, color, bold=True)
        for i in range(4):
            arrow(d, [(xs[i]+153, y-55), (xs[i+1]-153, y-55)], color)
            label(d, ((xs[i]+xs[i+1])/2, y-115), inputs[i], 45, color, bold=True)
        for i, observed in enumerate(["00", inputs[0], inputs[1]]):
            arrow(d, [(xs[i+1]-153, y+55), (xs[i]+153, y+55)], GRAY)
            label(d, ((xs[i]+xs[i+1])/2, y+120), observed, 44, GRAY)
        label(d, (1800, y-280), "כניסה" if he and delta == "+1" else "יציאה" if he else "ENTRY" if delta == "+1" else "EXIT", 54, color, bold=True, he=he)
    label(d, (1800, 1750), "כל הכיתובים על החצים הם זוג ערכי הגלאים" if he else "Arrow labels are the sampled sensor pair", 45, he=he)
    label(d, (1800, 1830), "AB = {A, B}", 43, GRAY)
    label(d, (1800, 1920), "המצב ההתחלתי חוזר בתרשים לצורך קריאות בלבד" if he else "Repeated IDLE circles denote the SAME state", 43, he=he)
    label(d, (1800, 2010), "קריאה חוזרת משאירה את המצב הקיים וכל מעבר חסר הוא שגיאה" if he else "Repeated sample: hold; unlisted transition: error", 43, ORANGE, he=he)
    label(d, (1800, 2100), "error -> WAIT_CLEAR, count_valid=0;   AB=00 -> IDLE", 42, ORANGE)
    im.save(OUT / f"prep-053-doorway-fsm-{language}.png")


def circuit(language):
    he = language == "he"
    im = Image.new("RGB", (3400, 1500), "white")
    d = ImageDraw.Draw(im)
    label(d, (1700, 120), "מבנה המערכת והפרדת אותות הגלאים" if he else "System structure and sensor conditioning boundary", 60, bold=True, he=he)
    # Sensor conditioning is an explicit external contract, not an unverified CDC fix.
    for x, code in ((200, "A_raw"), (500, "B_raw")):
        label(d, (x, 400), code, 46, BLUE)
    box(d, (80, 600, 900, 1050))
    label(d, (490, 730), "סנכרון וסינון ריצוד" if he else "Synchronize + debounce", 48, bold=True, he=he)
    label(d, (490, 865), "יש לשמור את כל מעברי הגלאים" if he else "preserve all AB transitions", 38, GRAY, he=he)
    arrow(d, [(200, 460), (200, 595)])
    arrow(d, [(500, 460), (500, 595)])
    arrow(d, [(905, 825), (1230, 825)])
    label(d, (1070, 755), "A, B", 46, BLUE, bold=True)
    box(d, (1230, 560, 2100, 1080), GREEN, "#eff8f3")
    label(d, (1665, 700), "מכונת המצבים" if he else "FSM", 56, GREEN, bold=True, he=he)
    label(d, (1665, 845), "מצבי התקדמות ומצב התאוששות" if he else "7 progress states + WAIT_CLEAR", 40, GREEN, he=he)
    label(d, (1665, 940), "7 + 1 = 8", 38, GREEN)
    arrow(d, [(2105, 760), (2440, 760)], GREEN)
    label(d, (2270, 680), "+1 / -1", 47, GREEN, bold=True)
    arrow(d, [(2105, 960), (2440, 960)], ORANGE)
    label(d, (2270, 1040), "bad", 44, ORANGE)
    box(d, (2440, 560, 3300, 1080))
    label(d, (2870, 700), "מונה אנשים" if he else "Occupancy counter", 51, bold=True, he=he)
    label(d, (2870, 850), "count, count_valid", 43, BLUE)
    label(d, (1700, 1230), "שעון משותף ואיפוס רק כאשר הפתח פנוי ומספר האנשים ידוע" if he else "Common clock; reset only with a clear doorway and known occupancy", 45, he=he)
    label(d, (1700, 1350), "0 <= count <= MAX; invalid=1 -> count_valid=0", 42, ORANGE)
    im.save(OUT / f"prep-053-doorway-circuit-{language}.png")


def protocol(number, n, mandatory, language):
    he = language == "he"
    m, threshold = n-1, 2*(n-1)
    im = Image.new("RGB", (3400, 2100), "white")
    d = ImageDraw.Draw(im)
    title = "שני מתגים והחלפה אחת בכל ביקור" if mandatory else "נורה אחת וספירה בטוחה"
    label(d, (1700, 120), title if he else "Two switches: exactly one toggle on every visit" if mandatory else "One light: a safe counting protocol", 61, bold=True, he=he)
    label(d, (1700, 235), f"N={n}    |    m={m}    |    C_target={threshold}", 45, GRAY)
    box(d, (140, 400, 1320, 1120), BLUE)
    label(d, (730, 500), "כל אסיר שאינו הסופר" if he else "Every non-counter prisoner", 49, BLUE, bold=True, he=he)
    label(d, (730, 650), "sent = 0, 1, 2", 52, BLUE, bold=True)
    label(d, (730, 790), "S=0 && sent<2", 49)
    label(d, (730, 900), "S <- 1; sent <- sent+1", 45, GREEN, bold=True)
    label(d, (730, 1030), "אחרת ממשיכים ללא אות" if he else "Otherwise: no signal token", 43, he=he)
    box(d, (2080, 400, 3260, 1120), GREEN, "#eff8f3")
    label(d, (2670, 500), "האסיר שנבחר לספור" if he else "The designated counter", 49, GREEN, bold=True, he=he)
    label(d, (2670, 650), "C = 0", 52, GREEN, bold=True)
    label(d, (2670, 790), "S=1", 49)
    label(d, (2670, 900), "S <- 0; C <- C+1", 45, GREEN, bold=True)
    label(d, (2670, 1000), f"C={threshold}", 43, GREEN, bold=True)
    label(d, (2670, 1080), "כולם ביקרו" if he else "ALL VISITED", 39, GREEN, bold=True, he=he)
    box(d, (1410, 600, 1990, 950), ORANGE, "#fffaed")
    label(d, (1700, 690), "S", 66, ORANGE, bold=True)
    label(d, (1700, 820), "0 / 1", 44, ORANGE)
    arrow(d, [(1325, 760), (1405, 760)], GREEN)
    arrow(d, [(1995, 760), (2075, 760)], GREEN)
    box(d, (160, 1240, 3240, 1510), ORANGE, "#fffaed")
    if mandatory:
        label(d, (1700, 1320), "בכל ביקור שבו לא משנים את מתג האות מחליפים את מתג הדמה" if he else "Every visit that does not toggle S MUST toggle dummy switch D", 46, ORANGE, bold=True, he=he)
        label(d, (1700, 1430), "משנים בדיוק מתג אחד בכל ביקור" if he else "Toggle exactly ONE switch on every visit", 46, ORANGE, he=he)
    else:
        label(d, (1700, 1320), "כאשר אין פעולת אות משאירים את הנורה ללא שינוי" if he else "On every other visit, LEAVE the light unchanged", 48, ORANGE, bold=True, he=he)
        label(d, (1700, 1430), "אין מתג דמה ואין חובה להחליף את מצב הנורה" if he else "No dummy switch; toggling is optional", 45, he=he)
    label(d, (1700, 1650), "גם מצב התחלתי דלוק אינו גורם להכרזה שגויה" if he else "An initially ON signal cannot cause a false declaration", 47, GREEN, bold=True, he=he)
    label(d, (1700, 1750), "אם אסיר אחד טרם ביקר" if he else "If one contributor has not visited", 40, he=he)
    label(d, (1700, 1825), f"C <= 2*{m-1}+1 = {threshold-1} < {threshold}", 47)
    label(d, (1700, 1920), "נדרשת חזרה של כל אסיר שוב ושוב ללא חסם זמן קבוע" if he else "Every prisoner must keep returning; there is no fixed visit bound", 43, GRAY, he=he)
    label(d, (1700, 2000), "מצב התחלתי כבוי ידוע מאפשר אות אחד מכל אסיר" if he else "Known initial OFF permits one signal per contributor", 43, GRAY, he=he)
    im.save(OUT / f"prep-{number:03d}-signal-protocol-{language}.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for language in ("he", "en"):
        doorway(language)
        fsm(language)
        circuit(language)
        protocol(54, 17, True, language)
        protocol(57, 21, False, language)
