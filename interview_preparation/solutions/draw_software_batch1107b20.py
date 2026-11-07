"""Original bilingual figures for the five software contracts."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def start(he, en, lang):
    image = Image.new('RGB', (3000, 1750), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1500, 120), he, en, lang, 60, bold=True)
    return image, draw


def save(image, number, lang):
    image.save(OUT / f'prep-{number}-software-batch1107b20-{lang}.png')


def cells(draw, values, y, color=BLUE, left=300, width=2400):
    step = width / len(values)
    for i, value in enumerate(values):
        x = left + i * step
        box(draw, (x, y, x + step - 20, y + 160), color)
        text(draw, (x + (step - 20) / 2, y + 80), str(value), 53, color=color)


def kmeans(lang):
    image, d = start('משייכים, מחשבים ממוצע וחוזרים', 'Assign, average, repeat', lang)
    for x, title, body in [(180, ('נקודות ומרכזי התחלה', 'Points and initial centers'), '(0,0) (0,2) | (10,10) (10,12)'),
                           (1160, ('שיוך למרכז הקרוב', 'Nearest-center assignment'), 'labels = [0,0,1,1]'),
                           (2140, ('ממוצע בכל קבוצה', 'Mean of each group'), '(0,1) | (10,11)')]:
        box(d, (x, 380, x + 700, 850), GREEN if x == 2140 else BLUE)
        phrase(d, (x + 350, 505), *title, lang, 43, bold=True)
        text(d, (x + 350, 690), body, 31)
        if x < 2140:
            wire(d, [(x + 700, 615), (x + 970, 615)])
    text(d, (1500, 1060), 'SSE = 1 + 1 + 1 + 1 = 4', 67, color=GREEN)
    phrase(d, (1500, 1260), 'שוויון נפתר לפי אינדקס; קבוצה ריקה שומרת מרכז', 'Ties use index order; an empty group retains its center', lang, 49)
    phrase(d, (1500, 1450), 'שיוך קבוע מאשר התכנסות לפי החוזה', 'Unchanged labels confirm convergence under the contract', lang, 49)
    phrase(d, (1500, 1620), 'ירידה בשגיאה אינה הוכחת מינימום גלובלי', 'Decreasing error does not prove a global minimum', lang, 49, color=ORANGE)
    save(image, 277, lang)


def packed(lang):
    image, d = start('ביט שמור והזזה לאורך מסלול מעגלי', 'One saved bit and a circular path', lang)
    text(d, (1500, 300), 'x = 1022; y = 3; destination = 1', 58)
    cells(d, [1022, 1023, 0, 1], 500)
    phrase(d, (1500, 450), 'אינדקסים לאורך המסלול', 'Indices along the path', lang, 45)
    cells(d, [1, 0, 1, 0], 830)
    phrase(d, (1500, 780), 'לפני', 'Before', lang, 47)
    cells(d, [0, 1, 0, 1], 1160, GREEN)
    phrase(d, (1500, 1110), 'אחרי', 'After', lang, 47)
    phrase(d, (1500, 1470), 'שלושת הביטים הבאים נסוגים; הראשון נשמר ומגיע לסוף', 'The next three shift back; the saved first bit reaches the end', lang, 45)
    phrase(d, (1500, 1640), 'שאר הביטים נשמרים; בתוך בית מתחילים בביט הפחות משמעותי', 'The other 1020 bits stay unchanged; bytes are LSB-first', lang, 45)
    save(image, 278, lang)


def spin(lang):
    image, d = start('רק פעולה אטומית אחת מקבלת דגל פנוי', 'Only one atomic operation observes a free flag', lang)
    items = [(180, ('מצב פנוי', 'Free state'), 'flag = false'),
             (1160, ('בדיקה והצבה אטומיות', 'Atomic TestAndSet'), 'old = false; flag = true'),
             (2140, ('בעלים נכנס', 'Owner enters'), 'critical section')]
    for i, (x, title, body) in enumerate(items):
        box(d, (x, 350, x + 700, 780), GREEN if i == 2 else BLUE)
        phrase(d, (x + 350, 470), *title, lang, 46, bold=True)
        if i == 2:
            phrase(d, (x + 350, 640), 'קטע מוגן', 'critical section', lang, 43)
        else:
            text(d, (x + 350, 640), body, 43)
        if i < 2:
            wire(d, [(x + 700, 560), (x + 980, 560)])
    box(d, (900, 1010, 2100, 1290), ORANGE)
    phrase(d, (1500, 1100), 'מתחרים מזהים מצב תפוס וממתינים', 'Contenders receive true and wait', lang, 47)
    text(d, (1500, 1210), 'acquire -> protected data -> release clear', 44)
    phrase(d, (1500, 1470), 'השחרור מחזיר מצב פנוי; אין הבטחת סדר הגעה או היעדר רעב', 'Release restores false; no FIFO or starvation-freedom promise', lang, 45)
    phrase(d, (1500, 1640), 'משתנה נדיף לבדו אינו אטומיות או סדר זיכרון', 'volatile alone is neither atomicity nor memory ordering', lang, 46)
    save(image, 281, lang)


def decimal(lang):
    image, d = start('מורידים ספרה ומוסיפים לסוף התוצאה', 'Remove a digit and append it to the result', lang)
    text(d, (1500, 300), 'input = 120; result = 21', 62)
    headers = [('המספר שנותר', 'Remaining'), ('ספרה שנשלפה', 'Extracted digit'), ('תוצאה', 'Result')]
    for col, title in enumerate(headers):
        phrase(d, (650 + col * 850, 520), *title, lang, 45, bold=True)
    for row, values in enumerate([(12, 0, 0), (1, 2, 2), (0, 1, 21)]):
        for col, value in enumerate(values):
            x, y = 300 + col * 850, 650 + row * 230
            box(d, (x, y, x + 700, y + 150), GREEN if row == 2 else BLUE)
            text(d, (x + 350, y + 75), str(value), 62)
    text(d, (1500, 1470), 'result <= floor((limit - digit) / 10)', 58, color=ORANGE)
    phrase(d, (1500, 1630), 'מרחיבים לפני שלילה ובודקים גבול לפני כפל', 'Widen before negation; check the bound before multiplying', lang, 48)
    save(image, 285, lang)


def relative(lang):
    image, d = start('סדר עדיפות וריבוי הם מידע שונה', 'Priority order and multiplicity are different information', lang)
    text(d, (1500, 320), 'A1', 55)
    cells(d, [2, 1, 2, 4, 6, 5, 9, 8, 3, 8, 7], 430)
    text(d, (1500, 750), 'A2: [2,1,8,3]', 60)
    cells(d, [2, 2, 1, 8, 8, 3], 930, GREEN)
    phrase(d, (1500, 870), 'קבוצות לפי סדר העדיפויות', 'Groups in priority order', lang, 45)
    cells(d, [4, 5, 6, 7, 9], 1250, ORANGE)
    phrase(d, (1500, 1190), 'השאר בסדר עולה', 'Remaining values ascending', lang, 45)
    phrase(d, (1500, 1550), 'כל 11 האיברים נשמרים; ספירה שהופקה מוסרת מהמילון', 'All 11 entries survive; emitted counts leave the dictionary', lang, 47)
    save(image, 287, lang)


if __name__ == '__main__':
    for language in ('he', 'en'):
        for render in (kmeans, packed, spin, decimal, relative):
            render(language)
    print('Rendered ten bilingual software figures.')
