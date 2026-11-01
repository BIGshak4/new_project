"""Fourteen clean bilingual diagrams, independent of supplied screenshots."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def base(he, en, language):
    image = Image.new('RGB', (2800, 1500), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1400, 110), he, en, language, 60, bold=True)
    return image, draw


def save(image, number, language):
    image.save(OUT / f'prep-{number:03d}-software-batch1101-{language}.png')


def cells(draw, values, y, start=300, width=420, color=BLUE):
    for i, value in enumerate(values):
        x = start + width * i
        box(draw, (x, y, x + width - 35, y + 180), color)
        text(draw, (x + (width - 35) / 2, y + 90), str(value), 60, color=color)


def dictionary(language):
    image, draw = base('החלפה בטוחה: מקצים לפני שמשחררים', 'Safe replacement: allocate before releasing', language)
    box(draw, (180, 380, 1100, 780), BLUE)
    text(draw, (640, 470), 'key -> old value', 60, color=BLUE)
    phrase(draw, (640, 640), 'המצב הישן נשאר תקף', 'Old map remains valid', language, 48)
    box(draw, (1600, 380, 2580, 780), GREEN)
    text(draw, (2090, 470), 'copy(new value)', 60, color=GREEN)
    phrase(draw, (2090, 640), 'עותק חדש ומנותק', 'New detached copy', language, 48)
    wire(draw, [(1100, 580), (1520, 580)], GREEN)
    phrase(draw, (1400, 950), 'הצלחה: מחליפים ומשחררים את הישן', 'Success: replace, then release old storage', language, 51, bold=True)
    phrase(draw, (1400, 1110), 'כשל: מחזירים שגיאה בלי לשנות את המפה', 'Failure: report an error without changing the map', language, 48)
    text(draw, (1400, 1330), 'one owner per allocation     borrowed get pointer', 47, color=BLUE)
    save(image, 237, language)


def reversal(language):
    image, draw = base('שומרים את היורש לפני שהופכים את הקישור', 'Save the successor before reversing the link', language)
    cells(draw, ['A', 'B', 'C'], 390, start=420, width=650)
    wire(draw, [(420, 480), (220, 480)], BLUE)
    text(draw, (220, 350), 'NULL', 48, color=BLUE)
    wire(draw, [(1685, 480), (1720, 480)], BLUE)
    text(draw, (720, 700), 'previous', 50, color=BLUE)
    text(draw, (1370, 700), 'current', 50, color=ORANGE)
    text(draw, (2020, 700), 'successor', 50, color=GREEN)
    wire(draw, [(1370, 800), (1370, 930)], GREEN)
    cells(draw, ['B', 'A'], 1000, start=600, width=650, color=GREEN)
    wire(draw, [(1215, 1090), (1250, 1090)], GREEN)
    text(draw, (2250, 1090), 'C -> NULL', 60, color=BLUE)
    phrase(draw, (1400, 1360), 'קידומת הפוכה וסיומת שלא אבדה', 'A reversed prefix and a preserved suffix', language, 47)
    save(image, 238, language)


def csv_states(language):
    image, draw = base('מצב הציטוט נשמר גם בין מקטעי קריאה', 'Quote state survives read-chunk boundaries', language)
    positions = [(250, 430, 'start'), (900, 430, 'plain'), (1550, 430, 'quoted'), (2200, 430, 'after_quote')]
    for x, y, label in positions:
        box(draw, (x, y, x + 500, y + 220), GREEN if label == 'quoted' else BLUE)
        text(draw, (x + 250, y + 110), label, 52)
    text(draw, (1400, 850), '"a,b",c  ->  ["a,b", "c"]', 72, color=GREEN)
    phrase(draw, (1400, 1030), 'בתוך ציטוט הפסיק הוא תוכן', 'Inside quotes, a comma is data', language, 51)
    phrase(draw, (1400, 1200), 'מחוץ לציטוט הוא מסיים שדה', 'Outside quotes, it ends a field', language, 51)
    text(draw, (1400, 1380), 'CRLF / LF record end     doubled quote -> literal quote', 43, color=BLUE)
    save(image, 239, language)


def pairs(language):
    image, draw = base('כל זוג זהה מתבטל והבודד נשאר', 'Equal pairs cancel; the singleton remains', language)
    cells(draw, [4, 3, 2, 4, 2], 440, start=390, width=420)
    text(draw, (1400, 800), '4 XOR 4 = 0       2 XOR 2 = 0', 62, color=BLUE)
    box(draw, (1050, 990, 1750, 1220), GREEN)
    text(draw, (1400, 1105), 'answer = 3', 75, color=GREEN)
    phrase(draw, (1400, 1380), 'ההבטחה נתונה; עדיין קוראים את כל המערך', 'The promise is supplied; all input still needs reading', language, 45)
    save(image, 27, language)


def power(language):
    image, draw = base('בודקים ביט יחיד ואז מחזירים את המעריך', 'Validate one set bit, then return its exponent', language)
    cells(draw, [8, 4, 2, 1], 460, start=420, width=510)
    for x in [895, 1405, 1915]:
        wire(draw, [(x, 550), (x + 35, 550)], GREEN)
    text(draw, (1400, 850), '8 = 2^3      result = [True, 3]', 68, color=GREEN)
    text(draw, (1400, 1060), '1 -> [True, 0]       0 -> [False, None]', 54, color=BLUE)
    phrase(draw, (1400, 1290), 'כישלון אינו זהה למעריך אפס', 'Failure is distinct from exponent zero', language, 49)
    save(image, 23, language)


def arena(language):
    image, draw = base('רק תאים חופשיים שומרים את קישורי הניהול', 'Only free cells store allocator links', language)
    for index, value, allocated in [(0, 'next=3', False), (1, '-1', True), (2, '99', True), (3, 'next=4', False), (4, 'end=-1', False)]:
        x = 230 + 470 * index
        text(draw, (x + 205, 375), str(index), 55)
        box(draw, (x, 460, x + 410, 730), ORANGE if allocated else GREEN)
        text(draw, (x + 205, 595), value, 49, color=ORANGE if allocated else GREEN)
        phrase(draw, (x + 205, 825), 'בשימוש' if allocated else 'פנוי', 'live' if allocated else 'free', language, 45)
    text(draw, (1400, 1040), 'free_head -> 0     free list: 0 -> 3 -> 4 -> end', 51, color=GREEN)
    phrase(draw, (1400, 1230), 'ערך לקוח יכול להיות גם מינוס אחד', 'A live client value may also be minus one', language, 48)
    phrase(draw, (1400, 1370), 'אינדקס נשמר בתא; מצביע אינו נדחס למספר שלם', 'Store an index; never truncate a pointer into int', language, 45)
    save(image, 117, language)


def packed(language):
    image, draw = base('הביטים הלא תקפים בסיומת אינם נספרים', 'Unused tail bits must not be counted', language)
    box(draw, (250, 440, 1250, 740), BLUE)
    text(draw, (750, 535), '11111111', 80, color=BLUE)
    text(draw, (750, 665), '8 valid -> count 8', 49)
    box(draw, (1550, 440, 2550, 740), GREEN)
    text(draw, (2050, 535), '11111111', 80, color=GREEN)
    text(draw, (2050, 665), '3 valid low bits -> count 3', 43)
    text(draw, (1400, 1000), 'bit_length = 11       total = 8 + 3 = 11', 62, color=GREEN)
    phrase(draw, (1400, 1210), 'מונה התוצאה צריך להכיל את כל הסכום', 'The total counter must hold the whole sum', language, 51)
    text(draw, (1400, 1380), 'O(bytes read) time     no full-array copy', 49, color=BLUE)
    save(image, 151, language)


if __name__ == '__main__':
    for language in ('he', 'en'):
        for diagram in (dictionary, reversal, csv_states, pairs, power, arena, packed):
            diagram(language)
    print('Rendered fourteen bilingual software diagrams.')
