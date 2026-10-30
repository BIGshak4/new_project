"""Paired repository-native diagrams for five batch110 reasoning explanations."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, GREEN, PALE, GRAY = "#fffdf8", "#302344", "#624883", "#30766a", "#eee7f5", "#d8d1df"


def canvas(he, en, lang, height=1500):
    image = Image.new("RGB", (2400, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 90), he, en, lang, 55, color=INK, bold=True)
    return image, draw


def label(draw, xy, value, size=44, color=INK):
    text(draw, xy, value, size, color=color, bold=True)


def box(draw, rect):
    draw.rounded_rectangle(rect, 25, fill=PALE, outline=PURPLE, width=5)


def voting(lang):
    image, draw = canvas("רוב מחזורי: המועמד הממתין בגמר מנצח", "A majority cycle: the candidate with the bye wins", lang, 1700)
    phrase(draw, (1200, 195), "דוגמה התואמת לשני התיקו: שלוש קבוצות של שלושים ושבעה", "Both ties hold: three groups of thirty-seven voters", lang, 42)
    for x, y, name in ((1200, 430, "A"), (1800, 970, "B"), (600, 970, "C")):
        draw.ellipse((x - 140, y - 140, x + 140, y + 140), fill=PALE, outline=PURPLE, width=7)
        label(draw, (x, y), name, 110)
    wire(draw, [(1330, 540), (1670, 850)], GREEN, width=9)
    wire(draw, [(1640, 970), (760, 970)], GREEN, width=9)
    wire(draw, [(730, 850), (1070, 540)], GREEN, width=9)
    for xy in ((1590, 620), (1200, 880), (810, 620)):
        label(draw, xy, "74 : 37", 47, GREEN)
    phrase(draw, (1200, 1160), "כל חץ מצביע מהמנצח אל המפסיד", "Each arrow points from winner to loser", lang, 40)
    for index, ranking in enumerate(("A > B > C", "B > C > A", "C > A > B")):
        left = 170 + index * 730
        box(draw, (left, 1250, left + 600, 1430))
        label(draw, (left + 300, 1300), "37", 48, GREEN)
        label(draw, (left + 300, 1380), ranking, 44)
    phrase(draw, (1200, 1540), "תחילה B מול C, אחר כך A מול המנצח", "First B versus C; then A versus the winner", lang, 43)
    phrase(draw, (1200, 1625), "B מנצח את C ואז A מנצח את B", "B defeats C, then A defeats B", lang, 44, color=GREEN, bold=True)
    image.save(OUT / f"prep-190-voting-majority-cycle-{lang}.png")


def bench(lang):
    image, draw = canvas("מימין אינו בהכרח צמוד מימין", "Somewhere right is different from immediately right", lang)
    for index, name in enumerate(("A", "C", "F", "B", "D", "E")):
        left = 260 + index * 320
        box(draw, (left, 330, left + 250, 570))
        label(draw, (left + 125, 445), name, 90, GREEN if name in ("C", "F") else INK)
    draw.rounded_rectangle((565, 310, 1170, 595), 32, outline=GREEN, width=8)
    label(draw, (865, 665), "CF", 66, GREEN)
    phrase(draw, (1200, 790), "מקשה אחת בסדר קבוע ועוד ארבעה אנשים", "One ordered block plus four other people", lang, 45)
    label(draw, (1200, 900), "5! / 6! = 120 / 720 = 1/6", 62, GREEN)
    phrase(draw, (1200, 1060), "למימין כלשהו מחליפים את השמות C ו־F", "For anywhere right, exchange the names C and F", lang, 45)
    label(draw, (1200, 1170), "360 / 720 = 1/2", 55)
    phrase(draw, (1200, 1370), "כל סידורי הישיבה בשורה שווי הסתברות; אין התניה על מושב", "Uniform linear seating; no fixed-seat conditioning", lang, 41)
    image.save(OUT / f"prep-192-bench-ordered-block-{lang}.png")


def boxes(lang):
    image, draw = canvas("החלפת שני פתקים מפצלת מחזור ארוך", "Swapping two notes splits one long cycle", lang, 1550)
    phrase(draw, (1200, 215), "דוגמה קטנה: שמונה קופסאות, תקציב ארבע פתיחות", "Small example: eight boxes, budget four opens", lang, 43)
    for index in range(8):
        x = 230 + index * 280
        box(draw, (x - 95, 345, x + 95, 525))
        label(draw, (x, 435), str(index + 1), 66)
        if index < 7:
            wire(draw, [(x + 95, 435), (x + 185, 435)], PURPLE, width=6)
    wire(draw, [(2190, 530), (2190, 620), (230, 620), (230, 530)], PURPLE, width=6)
    phrase(draw, (1200, 710), "מחליפים את הפתקים בקופסאות אחת וחמש", "Swap notes in boxes one and five", lang, 48, color=GREEN, bold=True)
    for start, sequence in ((300, "1 -> 6 -> 7 -> 8 -> 1"), (1350, "5 -> 2 -> 3 -> 4 -> 5")):
        box(draw, (start - 120, 840, start + 830, 1100))
        label(draw, (start + 355, 925), sequence, 42, GREEN)
        phrase(draw, (start + 355, 1035), "אורך ארבע", "Length four", lang, 43)
    label(draw, (1200, 1250), "L  ->  floor(L/2) + ceil(L/2)", 56, GREEN)
    phrase(draw, (1200, 1390), "במאה קופסאות יש לכל היותר מחזור אחד שאורכו מעל חמישים", "With 100 boxes, at most one cycle can exceed 50", lang, 43)
    image.save(OUT / f"prep-195-helper-swap-cycle-split-{lang}.png")


def nested(lang):
    from prep_198_nested_uniform import nested_marginals

    image, draw = canvas("A אחיד; הגבול האקראי מטה את B לערכים קטנים", "A is uniform; the random bound favors small B values", lang, 1550)
    a_mass, b_mass = nested_marginals()
    left, right, top, bottom = 310, 2160, 320, 1060
    wire(draw, [(left, top), (left, bottom), (right, bottom)], INK, width=4)
    for probability in (0, 0.02, 0.04, 0.06):
        y = bottom - probability / 0.06 * (bottom - top)
        draw.line((left, y, right, y), fill=GRAY, width=2)
        label(draw, (180, y), f"{probability:.2f}", 37)
    for value in (0, 25, 50, 75, 100):
        x = left + value / 100 * (right - left)
        label(draw, (x, bottom + 65), str(value), 39)
    points = [(left + b / 100 * (right - left), bottom - float(probability) / 0.06 * (bottom - top)) for b, probability in enumerate(b_mass)]
    draw.line(points, fill=PURPLE, width=9)
    y = bottom - float(a_mass[0]) / 0.06 * (bottom - top)
    draw.line((left, y, right, y), fill=GREEN, width=7)
    label(draw, (1700, 600), "A: 1/101", 48, GREEN)
    phrase(draw, (1700, 430), "B: מסה יורדת", "B: decreasing mass", lang, 47, color=PURPLE, bold=True)
    label(draw, (1200, 1235), "P(B=b) = (1/101) sum[a=b..100] 1/(a+1)", 44)
    label(draw, (1200, 1350), "E[A]=50      E[B]=25", 56, GREEN)
    phrase(draw, (1200, 1460), "התפלגות בדידה; שני גבולות ההגרלה כלולים", "Discrete integer masses; both endpoints are included", lang, 42)
    image.save(OUT / f"prep-198-nested-uniform-masses-{lang}.png")


def canoe(lang):
    image, draw = canvas("שבע הפלגות, עשרים ושמונה דקות", "Seven trips, twenty-eight minutes", lang, 1650)
    rows = [("1,3", "->", 3, 3), ("1", "<-", 1, 4), ("9,11", "->", 11, 15), ("3", "<-", 3, 18), ("1,6", "->", 6, 24), ("1", "<-", 1, 25), ("1,3", "->", 3, 28)]
    headers = [("חותרים לפי זמן", "Rowers by time"), ("כיוון", "Direction"), ("משך", "Duration"), ("מצטבר", "Total")]
    centers = (470, 970, 1470, 1970)
    for center, (he, en) in zip(centers, headers):
        phrase(draw, (center, 270), he, en, lang, 44, color=GREEN, bold=True)
    for index, row in enumerate(rows):
        y = 380 + index * 135
        draw.rounded_rectangle((230, y - 52, 2210, y + 52), 15, fill=PALE if index % 2 == 0 else BG)
        for x, value in zip(centers, row):
            label(draw, (x, y), str(value), 53)
    label(draw, (1200, 1390), "3+1+11+3+6+1+3 = 28 < 30", 58, GREEN)
    phrase(draw, (1200, 1520), "הקאנו חוזר עם ילד; מסיימים שתי דקות לפני הפיצוץ", "A child returns the canoe; finish two minutes before the explosion", lang, 43)
    image.save(OUT / f"prep-039-canoe-timeline-batch110-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        for render in (voting, bench, boxes, nested, canoe):
            render(language)
