"""Clean native bilingual diagrams; no source screenshot pixels are reused."""
from pathlib import Path

from PIL import Image, ImageDraw
from draw_prep_016_064 import BLUE, GREEN, INK, ORANGE, box, phrase, text, wire

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def base(ident, he, en, language):
    image = Image.new('RGB', (2800, 1800), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1400, 100), he, en, language, 60, bold=True)
    return image, draw


def triples(language):
    image, draw = base('PREP-210', 'אורכי רצפים מודולו שלוש', 'Equal-value run lengths modulo three', language)
    phrase(draw, (1400, 350), 'דוגמה מוקטנת עם חמש קבוצות מקוריות', 'A smaller example with five original groups', language, 43)
    for index, value in enumerate((1, 5, 1, 1, 2)):
        x = 300 + 460 * index
        box(draw, (x, 440, x + 360, 620), BLUE)
        text(draw, (x + 180, 530), f'{value} {value} {value}', 57, bold=True)
    phrase(draw, (1400, 735), 'נמחקו שני איברים מאחת מקבוצות האחת הסמוכות',
           'Delete two members of one adjacent group of ones', language, 43)
    runs = ((1, 3), (5, 3), (1, 4), (2, 3))
    x = 230
    for value, count in runs:
        width = count * 160
        color = ORANGE if count == 4 else BLUE
        draw.rounded_rectangle((x, 850, x + width, 1110), radius=20,
                               fill='#fff4e8' if count == 4 else '#f5f8fd', outline=color, width=7)
        for index in range(count):
            text(draw, (x + 80 + index * 160, 950), str(value), 62, bold=True, color=color)
        text(draw, (x + width / 2, 1050), f'length = {count}', 38, color=color)
        text(draw, (x + width / 2, 1200), f'{count} mod 3 = {count % 3}', 43, bold=True, color=color)
        x += width + 50
    box(draw, (330, 1370, 2470, 1590), GREEN)
    text(draw, (1400, 1450), 'answer = 1      |      global count(1) = 7', 50, color=GREEN, bold=True)
    phrase(draw, (1400, 1530), 'התשובה אינה חייבת להופיע פעם אחת בכל המערך',
           'The answer need not occur only once in the whole array', language, 42)
    text(draw, (1400, 1710), 'time: Θ(n)      extra space: O(1)', 46, color=BLUE)
    image.save(OUT / f'prep-210-algorithms-batch20-{language}.png')


def ranks(language):
    image, draw = base('PREP-211', 'סדר מספרי ותדירות הם שני דברים שונים',
                       'Numeric rank and frequency are different', language)
    text(draw, (1400, 380), 'input = [5, 5, 4, 4, 2]', 60, bold=True)
    box(draw, (160, 560, 1340, 1330), BLUE)
    phrase(draw, (750, 655), 'שני הערכים השונים הגדולים', 'Two largest distinct values', language, 46, bold=True, color=BLUE)
    text(draw, (750, 835), 'first = 5, count = 2', 49)
    text(draw, (750, 985), 'second = 4, count = 2', 49)
    text(draw, (750, 1200), 'Θ(n) time   |   O(1) space', 45, color=BLUE)
    box(draw, (1460, 560, 2640, 1330), GREEN)
    phrase(draw, (2050, 655), 'השכיח עם הכרעת שוויון', 'Mode with the declared tie rule', language, 43, bold=True, color=GREEN)
    for y, value, count in ((820, 5, 2), (950, 4, 2), (1080, 2, 1)):
        text(draw, (2050, y), f'{value} : {count}', 52, color=GREEN if value == 4 else INK, bold=value == 4)
    text(draw, (2050, 1210), 'mode = 4, count = 2', 49, color=GREEN, bold=True)
    phrase(draw, (1400, 1480), 'בתיקו תדירויות בוחרים בערך הקטן ביותר',
           'A frequency tie chooses the smallest numeric value', language, 48)
    text(draw, (1400, 1620), 'mode map: expected O(n) time, O(k) space', 47, color=GREEN)
    phrase(draw, (1400, 1725), 'שכיח אינו בהכרח רוב של יותר מחצי',
           'A mode need not be a strict majority', language, 42)
    image.save(OUT / f'prep-211-algorithms-batch20-{language}.png')


def chain(draw, y, values, *, new_index=None):
    text(draw, (190, y), 'head', 45, color=BLUE, bold=True)
    centers = [590 + 510 * index for index in range(len(values))]
    wire(draw, [(285, y), (centers[0] - 170, y)], BLUE)
    for index, (x, value) in enumerate(zip(centers, values)):
        color = ORANGE if index == new_index else BLUE
        box(draw, (x - 170, y - 110, x + 170, y + 110), color)
        text(draw, (x, y - 25), str(value), 58, bold=True, color=color)
        text(draw, (x, y + 60), 'owner = L', 30, color=color)
        end = centers[index + 1] - 170 if index + 1 < len(centers) else x + 340
        wire(draw, [(x + 170, y), (end, y)], color)
    text(draw, (centers[-1] + 410, y), 'NULL', 39, color=BLUE)


def linked_list(language):
    image, draw = base('PREP-212', 'מכניסים דרך כתובת של קישור', 'Insert through the address of a link', language)
    phrase(draw, (1400, 350), 'לפני ההכנסה במיקום אחת', 'Before insertion at position one', language, 47, bold=True)
    chain(draw, 570, (10, 20, 30))
    box(draw, (2130, 420, 2690, 720), ORANGE)
    text(draw, (2410, 485), 'new: 99', 49, color=ORANGE, bold=True)
    text(draw, (2410, 580), 'next = NULL', 39)
    text(draw, (2410, 655), 'owner = NULL', 39)
    phrase(draw, (1400, 865), 'בדיקת טווח ובעלות לפני כל שינוי',
           'Validate position and ownership before any mutation', language, 45)
    text(draw, (1400, 960), 'link = &node10->next', 48, color=ORANGE, bold=True)
    chain(draw, 1180, (10, 99, 20, 30), new_index=1)
    box(draw, (370, 1430, 2430, 1660), GREEN)
    text(draw, (1400, 1500), 'new->next = *link;     *link = new;', 46, color=GREEN, bold=True)
    phrase(draw, (1400, 1590), 'הבעלות עוברת לרשימה רק בהצלחה',
           'Ownership transfers to the list only on success', language, 44)
    phrase(draw, (1400, 1730), 'גם זנב ללא קישור הבא עדיין שייך לרשימה',
           'A tail with no next node is still owned by its list', language, 42)
    image.save(OUT / f'prep-212-algorithms-batch20-{language}.png')


if __name__ == '__main__':
    for lang in ('he', 'en'):
        triples(lang)
        ranks(lang)
        linked_list(lang)
