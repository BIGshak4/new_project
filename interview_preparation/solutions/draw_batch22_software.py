"""Clean bilingual diagrams for the software intake; no source images reused."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def base(he, en, language):
    image = Image.new('RGB', (2800, 1500), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1400, 110), he, en, language, 62, bold=True)
    return image, draw


def cells(draw, values, y, color=BLUE, x=230, width=240):
    for index, value in enumerate(values):
        left = x + index * width
        box(draw, (left, y, left + width - 20, y + 150), color)
        text(draw, (left + (width - 20) / 2, y + 75), str(value), 55, color=color)


def save(image, number, language):
    image.save(OUT / f'prep-{number:03d}-software-batch22-{language}.png')


def merge(language):
    image, draw = base('רק ראש כל רשימה מתחרה על המקום הבא', 'Only each list head competes for the next position', language)
    for y, label, values in [(320, 'L0', [1, 4, 9]), (620, 'L1', [1, 3, 7]), (920, 'L2', [2, 8])]:
        text(draw, (150, y + 75), label, 45)
        cells(draw, values, y, x=300)
        draw.rounded_rectangle((295, y - 5, 525, y + 155), radius=20, outline=GREEN, width=10)
    box(draw, (1600, 440, 2600, 940), GREEN)
    phrase(draw, (2100, 535), 'ערימת ראשי הרשימות', 'Heap of current heads', language, 46, bold=True)
    text(draw, (2100, 690), '(1,L0)  (1,L1)  (2,L2)', 44)
    phrase(draw, (2100, 830), 'מוציאים מינימום ומוסיפים רק יורש', 'Pop minimum; insert only its successor', language, 40)
    phrase(draw, (1400, 1210), 'מיחזור צמתים דורש רשימות זרות וללא מעגלים', 'Node reuse requires disjoint acyclic lists', language, 47)
    text(draw, (1400, 1335), 'O(K + N log(max(2,k))) time      O(k) auxiliary space', 44, color=GREEN)
    save(image, 224, language)


def mode(language):
    image, draw = base('ספירה סופית לפני שבירת שוויון', 'Count first, then break final-frequency ties', language)
    cells(draw, ['a', 'b', 'b', 'a'], 310, x=900)
    phrase(draw, (1400, 600), 'שתי המילים מופיעות פעמיים', 'Both words occur twice', language, 52)
    box(draw, (350, 790, 1200, 1070), BLUE)
    text(draw, (775, 880), 'a : 2', 75, color=BLUE)
    phrase(draw, (775, 990), 'הופיעה ראשונה', 'First appearance', language, 42)
    box(draw, (1600, 790, 2450, 1070), ORANGE)
    text(draw, (2025, 880), 'b : 2', 75, color=ORANGE)
    phrase(draw, (2025, 990), 'הגיעה ראשונה לשיא זמני', 'Reached a temporary lead first', language, 38)
    phrase(draw, (1400, 1280), 'התשובה היא a: שוויון נפתר לפי סדר הקלט', 'Answer: a; ties follow input order', language, 50, bold=True)
    save(image, 225, language)


def anagrams(language):
    image, draw = base('אנגרמה משמרת את מספר ההופעות של כל אות', 'Anagrams preserve every letter multiplicity', language)
    cells(draw, ['a', 'a', 'b'], 340, x=560)
    cells(draw, ['a', 'b', 'b'], 650, x=560, color=ORANGE)
    box(draw, (1650, 330, 2540, 850), BLUE)
    text(draw, (2095, 440), 'balance', 55, bold=True)
    text(draw, (2095, 590), 'a : +1', 62, color=ORANGE)
    text(draw, (2095, 740), 'b : -1', 62, color=ORANGE)
    phrase(draw, (1400, 1040), 'אותה קבוצת אותיות אינה מספיקה', 'The same letter set is insufficient', language, 54)
    text(draw, (1400, 1200), 'all balances = 0  <=>  anagrams', 58, color=GREEN)
    phrase(draw, (1400, 1350), 'אותיות אנגליות; רישיות נשמרת וגם כפילויות', 'ASCII, case-sensitive, duplicates counted', language, 44)
    save(image, 226, language)


def stack(language):
    image, draw = base('סדר ההוצאה מגדיר את מבנה הנתונים', 'Removal order defines the data structure', language)
    phrase(draw, (760, 330), 'מחסנית: האחרון יוצא ראשון', 'Stack: last in, first out', language, 49, bold=True)
    for index, value in enumerate(['A', 'B', 'C']):
        box(draw, (520, 990 - index * 180, 1000, 1140 - index * 180), BLUE)
        text(draw, (760, 1065 - index * 180), value, 64)
    wire(draw, [(1000, 705), (1300, 705), (1300, 430)], BLUE)
    text(draw, (1250, 350), 'C', 65, color=BLUE)
    phrase(draw, (2050, 330), 'תור: הראשון יוצא ראשון', 'Queue: first in, first out', language, 49, bold=True)
    cells(draw, ['A', 'B', 'C'], 760, x=1640)
    wire(draw, [(1640, 835), (1480, 835), (1480, 560)], ORANGE)
    text(draw, (1510, 480), 'A', 65, color=ORANGE)
    phrase(draw, (1400, 1300), 'סוג נתונים אינו קובע פריסת זיכרון של מכונה', 'An ADT does not prescribe memory layout or ABI', language, 48)
    save(image, 228, language)


def zeroes(language):
    image, draw = base('מכווצים את הלא־אפסים לקידומת בלי לשנות סדר', 'Compact nonzero values into a stable prefix', language)
    cells(draw, [1, 0, 9, 0, 3, 4, 5, 1], 380, x=410)
    cells(draw, [1, 9, 3, 4, 5, 1, 0, 0], 900, x=410, color=GREEN)
    wire(draw, [(1400, 600), (1400, 810)], GREEN)
    phrase(draw, (1950, 700), 'סמן הכתיבה אינו עובר את סמן הקריאה', 'write never passes read', language, 48)
    phrase(draw, (1400, 1240), 'ריבוי וסדר נשמרים; הסיומת מתמלאת באפסים', 'Preserve multiplicity and order; fill the suffix with zeroes', language, 46)
    text(draw, (1400, 1360), 'O(N) time     O(1) auxiliary words     same array', 46, color=GREEN)
    save(image, 229, language)


def fifo(language):
    image, draw = base('כתיבה ואז קריאה: ההבדל בין ריק למלא', 'Write then read: empty and full boundaries', language)
    text(draw, (1400, 305), 'write_request = 1     read_request = 1', 55, color=BLUE)
    for y, color, he, en, before, after in [
        (500, GREEN, 'ריק: הנתון החדש עובר מיד', 'Empty: the new value passes through', '[]  +  new', 'wrote=1, read=1, value=new'),
        (930, ORANGE, 'מלא: הכתיבה נדחית והישן נקרא', 'Full: reject write, then read oldest', '[old,...]  +  new', 'wrote=0, read=1, value=old')]:
        box(draw, (220, y - 70, 2580, y + 230), color)
        phrase(draw, (1400, y), he, en, language, 48, bold=True)
        text(draw, (800, y + 140), before, 50)
        text(draw, (1880, y + 140), after, 45, color=color)
    phrase(draw, (1400, 1320), 'בעלים יחיד; דגלים אינם מנגנון סנכרון', 'Single owner; flags are not ISR synchronization', language, 47)
    save(image, 230, language)


def reverse(language):
    image, draw = base('אותו מספר, חוזי רוחב שונים', 'Same number, different width contracts', language)
    for y, he, en, expression, color in [
        (440, 'ביטים משמעותיים בלבד', 'Significant bits only', '13:  1101  ->  1011  = 11', GREEN),
        (850, 'רוחב קבוע של שמונה ביטים', 'Fixed width: eight bits', '13:  00001101  ->  10110000  = 176', BLUE)]:
        phrase(draw, (1400, y - 90), he, en, language, 49, bold=True)
        box(draw, (250, y, 2550, y + 200), color)
        text(draw, (1400, y + 100), expression, 62, color=color)
    phrase(draw, (1400, 1260), 'בלי לשמור רוחב, היפוך כפול אינו משחזר אפסים', 'Without retained width, double reversal can lose zero positions', language, 45)
    text(draw, (1400, 1380), '8 (1000) -> 1 -> 1', 55, color=ORANGE)
    save(image, 94, language)


def counting(language):
    image, draw = base('סופרים את מלאי האותיות ואז כותבים לפי הסדר', 'Count the letter inventory, then emit in order', language)
    cells(draw, ['Z', 'A', 'M', 'A'], 310, x=920)
    for x, label, count in [(500, 'A', 2), (1160, 'M', 1), (1820, 'Z', 1)]:
        box(draw, (x, 650, x + 480, 890), BLUE)
        text(draw, (x + 240, 715), label, 55, bold=True)
        text(draw, (x + 240, 815), str(count), 58, color=GREEN)
    cells(draw, ['A', 'A', 'M', 'Z'], 1100, x=920, color=GREEN)
    phrase(draw, (1400, 990), 'עשרים ושישה מונים; אין צורך בהשוואת כל זוג תווים', 'Twenty-six counters; no pairwise character sorting', language, 44)
    text(draw, (1400, 1390), 'O(n + 26) time       O(26) counter words', 49, color=GREEN)
    save(image, 160, language)


if __name__ == '__main__':
    for language in ('he', 'en'):
        for draw_diagram in (merge, mode, anagrams, stack, zeroes, fifo, reverse, counting):
            draw_diagram(language)
    print('Wrote sixteen bilingual software diagrams.')
