"""Original bilingual schematics/teaching diagrams, not screenshot copies."""
from math import exp
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
INK, BLUE, GREEN, PURPLE, RED = '#23334b', '#2a62a0', '#257b67', '#7854a2', '#b24747'


def canvas(he, en, lang):
    im = Image.new('RGB', (2400, 1500), 'white')
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 90), he, en, lang, 54, bold=True, color=INK)
    return im, d


def panel(d, rect, color=BLUE):
    d.rounded_rectangle(rect, radius=20, outline=color, width=5, fill='#f5f8fd')


def transmission(lang):
    im, d = canvas('דוגמה מוגדרת: קבל בקצה קו ומקור מותאם', 'Explicit example: capacitive termination and matched source', lang)
    # Source, matched resistor, line rectangle and a genuine shunt capacitor.
    d.ellipse((180, 300, 320, 440), outline=INK, width=6)
    text(d, (250, 370), 'Vs', 43, bold=True)
    d.line((250, 300, 250, 250, 440, 250), fill=INK, width=6)
    d.rectangle((440, 220, 650, 280), outline=INK, width=6)
    text(d, (545, 170), 'Rs = Z0', 43, bold=True)
    d.line((650, 250, 820, 250), fill=INK, width=6)
    panel(d, (820, 215, 1600, 470))
    text(d, (1210, 300), 'Z0; T', 48, bold=True, color=BLUE)
    wire(d, [(960, 370), (1450, 370)], BLUE, width=6)
    text(d, (1200, 415), 'A = Vs/2', 44, bold=True)
    d.line((1600, 250, 1950, 250, 1950, 340), fill=INK, width=6)
    d.line((1840, 340, 2060, 340), fill=INK, width=8)
    d.line((1840, 380, 2060, 380), fill=INK, width=8)
    d.line((1950, 380, 1950, 520, 250, 520, 250, 440), fill=INK, width=6)
    text(d, (2130, 360), 'C', 61, bold=True)
    text(d, (2130, 500), 'vC(0) = 0', 36)
    phrase(d, (1200, 615), 'הזמן בגרף מתחיל כשהגל מגיע לקבל', 'Plot time begins when the incident step reaches the capacitor', lang, 38, color=PURPLE)
    x0, x1, yzero, scale = 260, 2180, 1120, 170
    wire(d, [(x0, 1290), (x0, 730)], INK, width=4)
    wire(d, [(x0, yzero), (x1 + 50, yzero)], INK, width=4)
    for level in (-1, 0, 1, 2):
        y = yzero - level * scale
        d.line((x0, y, x1, y), fill='#dbe3ef', width=2)
        text(d, (180, y), str(level), 34)
    for curve, color in [(lambda t: 2 * (1 - exp(-t)), BLUE), (lambda t: 1 - 2 * exp(-t), RED)]:
        points = [(x0 + t * (x1 - x0) / 6, yzero - scale * curve(t)) for t in (i * 0.02 for i in range(301))]
        d.line(points, fill=color, width=7)
    text(d, (1000, 760), 'vC / A', 43, bold=True, color=BLUE)
    text(d, (1450, 910), 'b / A', 43, bold=True, color=RED)
    text(d, (2070, 1290), 't / (Z0*C)', 39)
    for tick in (0, 2, 4, 6):
        text(d, (x0 + tick * (x1 - x0) / 6, 1210), str(tick), 32)
    phrase(d, (1200, 1400), 'ללא טופולוגיה וספי דגימה אין רשימת ביטים ודאית', 'Without topology and sampling thresholds, no definite bit list follows', lang, 38, bold=True)
    return im


def cavities(lang):
    im, d = canvas('חלל סגור וריק: אותו חוץ נותן אותו קיבול', 'Enclosed empty cavities: the same exterior gives the same capacitance', lang)
    for center, square in [(620, False), (1780, True)]:
        d.ellipse((center - 420, 290, center + 420, 1130), fill='#f8fafc', outline=GREEN, width=7)
        d.ellipse((center - 300, 410, center + 300, 1010), fill='#dce6f3', outline=BLUE, width=7)
        if square:
            d.rectangle((center - 145, 565, center + 145, 855), fill='white', outline=BLUE, width=5)
        else:
            d.ellipse((center - 160, 550, center + 160, 870), fill='white', outline=BLUE, width=5)
        text(d, (center, 710), 'E = 0', 48, bold=True, color=PURPLE)
        phrase(d, (center, 470), 'מוליך: V', 'metal: V', lang, 42, bold=True, color=BLUE)
        phrase(d, (center, 1055), 'אדמה: 0', 'ground: 0', lang, 40, bold=True, color=GREEN)
        wire(d, [(center + 300, 710), (center + 400, 710)], RED, width=5)
        text(d, (center + 350, 650), 'E', 42, color=RED, bold=True)
        phrase(d, (center, 1190), 'רדיוס חוץ R; רדיוס אדמה b', 'outer R; ground b > R', lang, 39)
    phrase(d, (1200, 240), 'הארקה קואקסיאלית נוספה כאן כדוגמה מפורשת', 'Concentric ground is explicitly added here as an example', lang, 36, color=GREEN)
    text(d, (1200, 1300), "C' = 2*pi*epsilon / ln(b/R)", 58, bold=True, color=PURPLE)
    phrase(d, (1200, 1410), 'צורת החור אינה אלקטרודה נוספת ואין בו מטען', 'The hole shape is not an additional electrode; no charge is inside', lang, 39)
    return im


def junction(lang):
    im, d = canvas('צומת: יונים קבועים יוצרים שדה ומחסום', 'PN junction: fixed ions create a field and a barrier', lang)
    d.rectangle((220, 300, 1200, 650), fill='#f7ecee', outline=RED, width=4)
    d.rectangle((1200, 300, 2180, 650), fill='#eaf1fa', outline=BLUE, width=4)
    d.rectangle((880, 300, 1200, 650), fill='#eee4f6', outline=PURPLE, width=4)
    d.rectangle((1200, 300, 1520, 650), fill='#eee4f6', outline=PURPLE, width=4)
    text(d, (520, 385), 'P', 73, bold=True, color=RED)
    text(d, (1850, 385), 'N', 73, bold=True, color=BLUE)
    for x in (960, 1120):
        for y in (410, 560):
            text(d, (x, y), '-', 75, bold=True, color=RED)
    for x in (1280, 1440):
        for y in (410, 560):
            text(d, (x, y), '+', 75, bold=True, color=BLUE)
    phrase(d, (520, 535), 'חורים: נשאי רוב', 'Majority holes', lang, 42, color=RED)
    phrase(d, (1850, 535), 'אלקטרונים: נשאי רוב', 'Majority electrons', lang, 39, color=BLUE)
    wire(d, [(1450, 750), (950, 750)], PURPLE, width=7)
    phrase(d, (1200, 815), 'כיוון השדה: N אל P', 'Field direction: N to P', lang, 43, bold=True, color=PURPLE)
    phrase(d, (1200, 235), 'איור שיווי משקל; כיווני הצדדים הוגדרו במפורש', 'Equilibrium illustration; side directions are defined explicitly', lang, 35)
    panel(d, (210, 920, 1120, 1290), RED)
    phrase(d, (665, 995), 'הטיה קדמית', 'Forward bias', lang, 49, bold=True, color=RED)
    text(d, (665, 1110), 'Va = Vp - Vn > 0', 44, bold=True)
    phrase(d, (665, 1210), 'מחסום קטן יותר', 'Lower barrier', lang, 41)
    panel(d, (1280, 920, 2190, 1290), BLUE)
    phrase(d, (1735, 995), 'הטיה הפוכה', 'Reverse bias', lang, 49, bold=True, color=BLUE)
    text(d, (1735, 1110), 'Va = Vp - Vn < 0', 44, bold=True)
    phrase(d, (1735, 1210), 'אזור מחסור רחב יותר', 'Wider depletion', lang, 41)
    phrase(d, (1200, 1400), 'מחסור בנשאים ניידים אינו היעדר מטען מרחבי', 'Depletion of mobile carriers does not mean absence of space charge', lang, 40, bold=True)
    return im


def graph(d, rect, values, color):
    left, top, right, bottom = rect
    low, high = min(values), max(values)
    span = max(1, high - low)
    wire(d, [(left, bottom), (left, top)], INK, width=4)
    wire(d, [(left, bottom), (right, bottom)], INK, width=4)
    points = [(left + i * (right - left) / (len(values) - 1), bottom - 50 - (v - low) * (bottom - top - 100) / span) for i, v in enumerate(values)]
    d.line(points, fill=color, width=7)
    for x, y in points:
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=color)


def focus(lang):
    im, d = canvas('מספר המדידות תלוי בהבטחה על צורת הפוקוס', 'Measurement count depends on the promised focus shape', lang)
    for x, he, en, values, color, label in [
        (130, 'בלי הנחת צורה', 'Arbitrary shape', [1, 5, 2, 8, 1, 3, 9, 2], BLUE, '1000 queries'),
        (1320, 'עלייה ואז ירידה', 'Strict slopes; one peak', [1, 3, 5, 7, 9, 8, 4, 1], GREEN, '<= 21 queries')]:
        panel(d, (x, 270, x + 950, 1030), color)
        phrase(d, (x + 475, 355), he, en, lang, 45, bold=True, color=color)
        graph(d, (x + 100, 440, x + 850, 820), values, color)
        if lang == 'he':
            text(d, (x + 475, 920), '1000' if color == BLUE else '21', 53, bold=True, color=color)
            phrase(d, (x + 475, 990), 'מדידות' if color == BLUE else 'מדידות לכל היותר', '', lang, 38, color=color)
        else:
            text(d, (x + 475, 940), label, 53, bold=True, color=color)
    phrase(d, (1200, 1130), 'פלטו נמוך עלול להכשיל חיפוש בינארי רגיל', 'A lower plateau can break ordinary binary peak search', lang, 42, bold=True, color=RED)
    text(d, (1200, 1235), '[0, 0, 0, 1]', 58, color=RED)
    phrase(d, (1200, 1370), 'בכל פתרון: בוחרים לבסוף את מצב הזום המנצח', 'For either method, finally select the winning zoom setting', lang, 42, bold=True)
    return im


def payment(lang):
    im, d = canvas('תשלום חד פעמי: כל מטבע פיזי מופיע פעם אחת', 'Single-use payment: each physical coin appears at most once', lang)
    phrase(d, (1200, 230), 'בלי ערכי מטבעות ומלאי אין תשובה מספרית יחידה', 'Without coin values and inventory, no unique numeric answer follows', lang, 42, bold=True, color=RED)
    for x, label, value in [(300, 'i = 0', '50'), (1000, 'i = 1', '50'), (1700, 'i = 2', '20')]:
        panel(d, (x, 335, x + 400, 710))
        text(d, (x + 200, 415), label, 42, bold=True, color=BLUE)
        d.ellipse((x + 85, 470, x + 315, 700), outline=GREEN, width=6, fill='#eef8f3')
        text(d, (x + 200, 585), value, 75, bold=True, color=GREEN)
    text(d, (850, 590), '+', 70, bold=True)
    text(d, (1550, 590), '+', 70, bold=True)
    text(d, (1200, 820), '50 + 50 + 20 = 120', 65, bold=True, color=GREEN)
    panel(d, (220, 930, 2180, 1240), PURPLE)
    text(d, (1200, 1010), 'dp[i][s] = min(skip, take)', 57, bold=True, color=PURPLE)
    text(d, (1200, 1110), 'skip: dp[i-1][s]', 45)
    text(d, (1200, 1190), 'take: 1 + dp[i-1][s-coins[i-1]]', 45)
    phrase(d, (1200, 1380), 'שתי האפשרויות פונות רק למטבעות הקודמים', 'Both branches use only the earlier physical coins', lang, 44, bold=True)
    return im


if __name__ == '__main__':
    for number, draw in [(258, transmission), (259, cavities), (260, junction), (270, focus), (271, payment)]:
        for lang in ('he', 'en'):
            draw(lang).save(OUT / f'prep-{number}-concepts-{lang}.png', optimize=True)
    print('Generated ten original HE/EN diagrams.')
