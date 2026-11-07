"""Deterministic diagrams of explicit teaching contracts; no source photograph reuse."""
from pathlib import Path

from draw_prep_016_064 import phrase, text
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
INK, BLUE, GREEN, RED = '#23334b', '#2a62a0', '#257b67', '#b24747'


def frame(he, en, lang):
    image = Image.new('RGB', (2400, 1500), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 95), he, en, lang, 54, bold=True)
    return image, draw


def card(draw, bounds, title, color=BLUE):
    draw.rounded_rectangle(bounds, radius=24, fill='#f5f8fd', outline=color, width=5)
    text(draw, ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2), title, 43, bold=True, color=color)


def arrow(draw, start, end, color=INK):
    draw.line((*start, *end), fill=color, width=6)
    x, y = end
    if abs(end[0] - start[0]) >= abs(end[1] - start[1]):
        direction = 1 if end[0] > start[0] else -1
        draw.polygon([(x, y), (x - direction * 23, y - 14), (x - direction * 23, y + 14)], fill=color)
    else:
        direction = 1 if end[1] > start[1] else -1
        draw.polygon([(x, y), (x - 14, y - direction * 23), (x + 14, y - direction * 23)], fill=color)


def inheritance(lang):
    image, d = frame('ירושה אינה סיבוכיות של פעולה', 'Inheritance is not an operation complexity', lang)
    phrase(d, (1200, 200), 'אותה הפניה לבסיס יכולה לבחור גופים בעלי עלויות שונות',
           'A base reference can select bodies with different costs', lang, 39)
    card(d, (780, 310, 1620, 510), 'const Score& object')
    arrow(d, (1050, 510), (620, 690))
    arrow(d, (1350, 510), (1780, 690))
    card(d, (180, 700, 1060, 1040), 'Score::score(xs)', BLUE)
    card(d, (1340, 700, 2220, 1040), 'FixedScore::score(xs)', GREEN)
    text(d, (620, 1130), 'sum n values: Theta(n)', 45, color=BLUE)
    text(d, (1780, 1130), 'return 7: O(1)', 45, color=GREEN)
    phrase(d, (1200, 1270), 'מנתחים גוף פעולה; שיגור, בנייה והקצאה נפרדים',
           'Analyze the body; dispatch, construction and allocation are separate', lang, 40, bold=True)
    phrase(d, (1200, 1380), 'טבלת פונקציות היא מימוש נפוץ, לא הבטחת פריסה או זמן פיזי',
           'A function table is typical, not a universal ABI or timing promise', lang, 37)
    return image


def parents(lang):
    image, d = frame('מפת הורים: מי מגיע לשורש המסומן?', 'Parent map: who reaches the designated root?', lang)
    phrase(d, (1200, 200), 'החצים מצביעים אל ההורה; זהות אובייקט קובעת',
           'Arrows point to parents; object identity matters', lang, 39)
    for x, label in [(400, 'ROOT'), (1000, 'C'), (1600, 'D'), (2100, 'None')]:
        card(d, (x - 170, 350, x + 170, 510), label, GREEN if label == 'ROOT' else RED)
    card(d, (230, 720, 570, 880), 'A', GREEN)
    card(d, (230, 1090, 570, 1250), 'B', GREEN)
    arrow(d, (400, 720), (400, 510), GREEN)
    arrow(d, (400, 1090), (400, 880), GREEN)
    arrow(d, (1170, 395), (1430, 395), RED)
    arrow(d, (1430, 475), (1170, 475), RED)
    card(d, (830, 800, 1170, 960), 'F', RED)
    arrow(d, (1000, 800), (1000, 510), RED)
    card(d, (1930, 800, 2270, 960), 'E', RED)
    arrow(d, (2100, 800), (2100, 510), RED)
    text(d, (1510, 1090), 'disconnected: C, D, F, E', 42, bold=True, color=RED)
    phrase(d, (1510, 1195), 'מעגל או סוף חסר אינם מגיעים לשורש',
           'A cycle or missing end does not reach ROOT', lang, 34, color=RED)
    phrase(d, (1200, 1380), 'השורש טרמינלי; כל צומת נפתר ונשמר פעם אחת',
           'ROOT is terminal; resolve and memoize each node once', lang, 39, bold=True)
    return image


def rope(lang):
    image, d = frame('עוד שני מטרים בהיקף: מרווח שאינו תלוי ברדיוס',
                     'Two added circumference metres: about 31.83 cm clearance', lang)
    phrase(d, (1200, 205), 'מעגלים בעלי אותו מרכז, עם תמיכה ומרווח אחיד',
           'Supported concentric circles with uniform clearance', lang, 39)
    d.ellipse((160, 400, 1120, 1360), outline=GREEN, width=9, fill='#f7fafc')
    d.ellipse((280, 520, 1000, 1240), outline=BLUE, width=7, fill='#e7eff8')
    text(d, (640, 870), 'Earth: R', 57, bold=True, color=BLUE)
    text(d, (640, 1295), 'R + h', 46, color=GREEN)
    text(d, (1720, 425), '2*pi*(R+h) - 2*pi*R = 2', 39)
    text(d, (1720, 545), 'h = 1/pi = 0.318309886 m', 42, bold=True, color=GREEN)
    d.rectangle((1450, 810, 1600, 1170), fill='#d9eee7', outline=GREEN, width=5)
    d.rectangle((1790, 890, 1940, 1170), fill='#e8edf8', outline=BLUE, width=5)
    text(d, (1525, 740), '31.83 cm', 40, bold=True, color=GREEN)
    text(d, (1865, 820), '25 cm', 40, bold=True, color=BLUE)
    phrase(d, (1700, 1255), 'גובה החתול נבחר בדוגמה: כן, עובר',
           'Chosen effective cat height: yes, it fits', lang, 36, bold=True)
    phrase(d, (1200, 1440), 'הגובה הוא השלמה שלנו; התרשים אינו בקנה מידה',
           'Height is our teaching completion; diagram not to scale', lang, 34)
    return image


def bytes_diagram(lang):
    image, d = frame('ארבעה בתים זרים מכסים את כל סיביות המילה',
                     'Four disjoint bytes cover all thirty-two bits', lang)
    phrase(d, (1200, 205), 'מחלצים שדות מספריים: אין תלות בסדר הבתים בזיכרון',
           'Extract numeric bit fields: memory endianness does not matter', lang, 39)
    for i, (field, value, count) in enumerate([('31:24', '0x80', '1'), ('23:16', '0x00', '0'),
                                              ('15:8', '0x01', '1'), ('7:0', '0xFF', '8')]):
        x = 360 + i * 560
        card(d, (x - 215, 350, x + 215, 580), value)
        text(d, (x, 295), 'bits ' + field, 38)
        arrow(d, (x, 580), (x, 740))
        card(d, (x - 215, 750, x + 215, 950), 'byte_count = ' + count, GREEN)
    text(d, (1200, 1100), '1 + 0 + 1 + 8 = 10', 66, bold=True, color=GREEN)
    phrase(d, (1200, 1230), 'בדיוק ארבע קריאות לפעולה שכבר נתונה',
           'Exactly four calls to the already supplied operation', lang, 43, bold=True)
    phrase(d, (1200, 1360), 'בטבלת בית מאתיים חמישים ושישה מונים; הבנייה היא עלות נפרדת',
           'A byte table has 256 counters; building it is separate preprocessing', lang, 36)
    return image


if __name__ == '__main__':
    for language in ('he', 'en'):
        for number, draw in [(276, inheritance), (284, parents), (90, rope), (151, bytes_diagram)]:
            draw(language).save(OUT / f'prep-{number:03d}-reasoning-batch1107b20-{language}.png')
