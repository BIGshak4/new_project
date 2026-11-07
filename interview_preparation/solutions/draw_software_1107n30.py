"""Six original bilingual diagrams, independent of raw interview screenshots."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def canvas(he, en, lang):
    image = Image.new('RGB', (3000, 1750), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1500, 120), he, en, lang, 59, bold=True)
    return image, draw


def save(image, number, lang):
    image.save(OUT / f'prep-{number:03d}-software-1107n30-{lang}.png')


def cells(d, values, y, colors=None):
    step = 2700 / len(values)
    for i, value in enumerate(values):
        color = colors[i] if colors else BLUE
        x = 160 + i * step
        box(d, (x, y, x + step - 25, y + 180), color)
        text(d, (x + (step - 25) / 2, y + 90), str(value), 61, color=color)


def longest(lang):
    image, d = canvas('רצף נוכחי ורצף טוב ביותר לאורך הסריקה', 'Current run and best run during the scan', lang)
    phrase(d, (1500, 340), 'אינדקסים', 'Indices', lang, 48)
    cells(d, list(range(8)), 440)
    phrase(d, (1500, 760), 'ערכי הקלט', 'Input values', lang, 48)
    cells(d, [0, 1, 1, 0, 1, 1, 1, 0], 860, [BLUE] * 4 + [GREEN] * 3 + [BLUE])
    text(d, (1500, 1240), 'start = 4; end = 6; length = 3', 65, color=GREEN)
    phrase(d, (1500, 1450), 'קצוות כלולים; שוויון נשאר עם הרצף המוקדם', 'Inclusive endpoints; ties retain the earliest run', lang, 50)
    phrase(d, (1500, 1610), 'עדכון בכל אחד מונע אובדן רצף שבסוף המערך', 'Updating on each one preserves a trailing run', lang, 48)
    save(image, 289, lang)


def atoi(lang):
    image, d = canvas('מפרידים דקדוק מחשבון ובודקים לפני כפל', 'Separate grammar from arithmetic; check before multiplying', lang)
    text(d, (1500, 340), r'input = "\n\t+17 rest"', 63)
    stages = [(150, ('רווחים בתחילה', 'Leading whitespace'), r'\n \t'),
              (880, ('סימן', 'Sign'), '+'),
              (1610, ('ספרות', 'Digits'), '1 -> 17'),
              (2340, ('עצירה', 'Stop'), "' '")]
    for i, (x, label, body) in enumerate(stages):
        box(d, (x, 570, x + 550, 1000), GREEN if i == 3 else BLUE)
        phrase(d, (x + 275, 685), *label, lang, 45, bold=True)
        text(d, (x + 275, 860), body, 53)
        if i < 3:
            wire(d, [(x + 550, 790), (x + 720, 790)])
    text(d, (1500, 1230), 'value <= floor((limit - digit) / 10)', 59, color=ORANGE)
    phrase(d, (1500, 1430), 'חריגה נחתכת לגבול הטיפוס לפני יצירת גלישה', 'Clamp to the type endpoint before causing overflow', lang, 49)
    phrase(d, (1500, 1620), 'קוראים את כל הקלט, כולל ירידות שורה בתחילתו', 'Read all stdin, including leading newlines', lang, 49)
    save(image, 295, lang)


def shapes(lang):
    image, d = canvas('כל רכיב שחור מקבל מלבן משלו', 'Each black component gets its own rectangle', lang)
    pixels = [[0, 1, 1, 0, 0, 0, 0, 0],
              [0, 1, 0, 0, 0, 1, 0, 0],
              [0, 1, 1, 0, 0, 1, 1, 0],
              [0, 0, 0, 0, 0, 0, 0, 0],
              [0, 0, 1, 1, 0, 0, 0, 0],
              [0, 0, 0, 1, 0, 0, 0, 0]]
    left, top, step = 250, 400, 165
    for r, row in enumerate(pixels):
        text(d, (160, top + r * step + step / 2), str(r), 43)
        for c, bit in enumerate(row):
            x, y = left + c * step, top + r * step
            d.rectangle((x, y, x + step, y + step), fill='#172433' if bit else 'white', outline='#cbd5df', width=3)
    for c in range(8):
        text(d, (left + c * step + step / 2, 325), str(c), 43)
    bounds = [(0, 1, 2, 2), (1, 5, 2, 6), (4, 2, 5, 3)]
    for i, (r0, c0, r1, c1) in enumerate(bounds):
        color = [BLUE, GREEN, ORANGE][i]
        d.rectangle((left + c0 * step - 8, top + r0 * step - 8,
                     left + (c1 + 1) * step + 8, top + (r1 + 1) * step + 8), outline=color, width=11)
        text(d, (2280, 580 + i * 280), str(list(bounds[i])), 61, color=color)
    phrase(d, (2280, 350), 'קצוות כלולים', 'Inclusive bounds', lang, 49)
    text(d, (2280, 1430), '[min_row,min_col,max_row,max_col]', 37)
    phrase(d, (1500, 1620), 'דוגמה שנבחרה לתרגיל; ארבע שכנויות, בלי חיבור באלכסון', 'Authored example; four neighbors, no diagonal connection', lang, 47)
    save(image, 296, lang)


def grid(lang):
    image, d = canvas('כל ספירה היא סכום מלמעלה ומשמאל', 'Each count is the sum from above and left', lang)
    rows = [[1, 1, 1], [1, 2, 3], [1, 3, 6]]
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            x, y = 650 + c * 800, 440 + r * 360
            if c < 2:
                wire(d, [(x + 130, y), (x + 670, y)])
            if r < 2:
                wire(d, [(x, y + 105), (x, y + 255)])
            color = GREEN if (r, c) == (2, 2) else BLUE
            d.ellipse((x - 130, y - 105, x + 130, y + 105), fill='white', outline=color, width=7)
            text(d, (x, y), str(value), 67, color=color)
    text(d, (1500, 1450), 'W[r,c] = W[r-1,c] + W[r,c-1]', 61)
    phrase(d, (1500, 1640), 'רשת נקודות; תנועה רק ימינה או למטה', 'A grid of nodes; move only right or down', lang, 49)
    save(image, 300, lang)


def recursive(lang):
    image, d = canvas('יורדים לסיומת וחוזרים עם הראש בסוף', 'Descend into the suffix; append the head while returning', lang)
    phrase(d, (1500, 340), 'קריאות', 'Calls', lang, 49)
    cells(d, ['abc', 'bc', 'c', '""'], 470)
    phrase(d, (1500, 880), 'תוצאות בחזרה', 'Unwinding results', lang, 49)
    cells(d, ['""', 'c', 'cb', 'cba'], 1010, [GREEN] * 4)
    text(d, (1500, 1410), 'R(s) = Concat(R(Tail(s)), Head(s))', 60)
    phrase(d, (1500, 1620), 'סוג הראש ועלויות ההעתקה הם חלק מהחוזה', 'Head type and copying costs are part of the contract', lang, 48)
    save(image, 194, lang)


def words(lang):
    image, d = canvas('טקסט, הפרדת מילים וספירות סופיות', 'Text, tokenization and final frequencies', lang)
    text(d, (1500, 350), 'aaa aaa bbb ccc ddd aaa', 70)
    for i, (word, count) in enumerate([('aaa', 3), ('bbb', 1), ('ccc', 1), ('ddd', 1)]):
        x = 230 + i * 680
        color = GREEN if i == 0 else BLUE
        box(d, (x, 650, x + 580, 1130), color)
        text(d, (x + 290, 800), word, 73, color=color)
        text(d, (x + 290, 980), str(count), 73, color=color)
    phrase(d, (1500, 1330), 'הפלט הוא המילה בלבד', 'Output the word only', lang, 52)
    text(d, (1500, 1460), 'aaa', 75, color=GREEN)
    phrase(d, (1500, 1630), 'בשוויון תדירות בוחרים הופעה ראשונה, אחרי הספירה', 'Break frequency ties by first appearance after counting', lang, 48)
    save(image, 225, lang)


if __name__ == '__main__':
    for language in ('he', 'en'):
        for draw in (longest, atoi, shapes, grid, recursive, words):
            draw(language)
    print('Rendered twelve bilingual software figures.')
