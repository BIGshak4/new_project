"""Eight original bilingual explanatory figures; no raw source reconstruction."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def canvas(he, en, lang):
    image = Image.new('RGB', (3000, 1750), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1500, 110), he, en, lang, 59, bold=True)
    return image, draw


def save(image, number, language):
    image.save(OUT / f'prep-{number:03d}-software-batch1107b10-{language}.png')


def sorting(lang):
    image, draw = canvas('מקסימום זמין ותוצאה שגדלה מהסוף', 'An available maximum and a sorted suffix growing from the end', lang)
    levels = [[3, 0, 3, -1], [3, 0, -1, 3], [0, -1, 3, 3], [-1, 0, 3, 3]]
    captions = [('ערימה מוכנה', 'Heap ready'), ('מקסימום ראשון', 'First maximum'),
                ('מקסימום שני', 'Second maximum'), ('מיון הושלם', 'Sorted')]
    for row, values in enumerate(levels):
        y = 340 + row * 285
        phrase(draw, (380, y+90), *captions[row], lang, 45, bold=True)
        for col, value in enumerate(values):
            x = 850 + col * 440
            color = GREEN if row == 3 or col >= 4-row else BLUE
            box(draw, (x, y, x+350, y+180), color)
            text(draw, (x+175, y+90), str(value), 70, color=color)
    phrase(draw, (1500, 1540), 'הקידומת היא ערימה והסיומת במקומה הסופי', 'The prefix is a heap; the suffix is in final sorted position', lang, 49)
    phrase(draw, (1500, 1650), 'כל שינוי הוא החלפה והריבויים נשמרים', 'Every update is a swap; multiplicities are preserved', lang, 49)
    save(image, 273, lang)


def constructor(lang):
    image, draw = canvas('אובייקט חדש מגיע לשימוש רק אחרי אתחול תקין', 'A new object becomes usable after valid initialization', lang)
    items = [(180, ('פרמטרים', 'Parameters'), 'low = -2; high = 7'),
             (1160, ('אתחול חברים', 'Initialize members'), 'low_ = -2; high_ = 7'),
             (2140, ('בדיקת גוף הבנאי', 'Constructor body'), 'low <= high')]
    for i, (x, title, value) in enumerate(items):
        box(draw, (x, 380, x+730, 850), GREEN if i == 2 else BLUE)
        phrase(draw, (x+365, 505), *title, lang, 46, bold=True)
        text(draw, (x+365, 690), value, 42)
        if i < 2:
            wire(draw, [(x+730, 615), (x+980, 615)])
    phrase(draw, (1500, 1060), 'הצלחה משאירה טווח תקין', 'Success leaves a valid range', lang, 53, color=GREEN)
    text(draw, (1500, 1190), 'Range(8,7) -> exception; no completed Range', 53, color=ORANGE)
    phrase(draw, (1500, 1450), 'העתקה מאתחלת חדש והשמה משנה אובייקט קיים', 'Copy construction initializes a new object; assignment updates an existing one', lang, 46)
    phrase(draw, (1500, 1600), 'החברים מאותחלים לפי סדר ההכרזה', 'Members initialize in declaration order', lang, 49)
    save(image, 274, lang)


def tracker(lang):
    image, draw = canvas('בקרה משתמשת במשוב ואימות משתמש במקור נוסף', 'Control uses feedback; validation uses another reference', lang)
    for x, title, value in [(150, ('חיישני אור', 'Light sensing'), 'TL TR BL BR + ADC'),
                            (1160, ('בקר מוגבל', 'Bounded controller'), 'ex, ey -> deg/s'),
                            (2170, ('הנעה ופאנל', 'Drive and panel'), 'motor -> actual angle')]:
        box(draw, (x, 340, x+700, 810), BLUE)
        phrase(draw, (x+350, 465), *title, lang, 47, bold=True)
        text(draw, (x+350, 655), value, 42)
        if x < 2170:
            wire(draw, [(x+700, 580), (x+1010, 580)])
    box(draw, (1980, 1000, 2820, 1300), GREEN)
    phrase(draw, (2400, 1100), 'מקודדי זווית', 'Angle encoders', lang, 48, bold=True)
    text(draw, (2400, 1210), 'measured position', 44, color=GREEN)
    wire(draw, [(2520, 810), (2520, 1000)], GREEN)
    wire(draw, [(1980, 1150), (1510, 1150), (1510, 810)], GREEN)
    box(draw, (180, 1030, 1070, 1350), ORANGE)
    phrase(draw, (625, 1130), 'ייחוס עצמאי', 'Independent reference', lang, 46, bold=True)
    phrase(draw, (625, 1260), 'מקור אור בזווית ידועה', 'Lamp at a known angle', lang, 40)
    box(draw, (1350, 1380, 2670, 1580), GREEN)
    wire(draw, [(1070, 1280), (1200, 1280), (1200, 1480), (1350, 1480)], ORANGE)
    wire(draw, [(2400, 1300), (2400, 1380)], GREEN)
    phrase(draw, (2010, 1480), 'השוואת זווית ושגיאה', 'Compare orientation and error', lang, 47, color=ORANGE)
    phrase(draw, (1500, 1670), 'איזון חיישנים לבדו אינו הוכחה למציאת השמש', 'Balanced sensors alone do not prove the sun was found', lang, 48)
    save(image, 275, lang)


def subsets(lang):
    image, draw = canvas('כל סכום חדש משתמש באינדקס הנוכחי פעם אחת', 'Every new sum uses the current index once', lang)
    rows = [('[]', '{}'), ('[4]', '{4}'), ('[4,-1]', '{-1,3,4}'), ('[4,-1,2]', '{-1,1,2,3,4,5,6}')]
    for i, (prefix, sums) in enumerate(rows):
        y = 330 + i * 270
        box(draw, (240, y, 1120, y+170), BLUE)
        text(draw, (680, y+85), prefix, 57)
        wire(draw, [(1120, y+85), (1400, y+85)])
        box(draw, (1400, y, 2760, y+170), GREEN if i == 3 else BLUE)
        text(draw, (2080, y+85), sums, 55, color=GREEN if i == 3 else BLUE)
    text(draw, (1500, 1500), 'target = 5; witness indices = {0,1,2}', 56, color=GREEN)
    phrase(draw, (1500, 1650), 'אפס אינו נכלל אוטומטית מקבוצה ריקה', 'Zero is not automatically included by an empty subset', lang, 47)
    save(image, 40, lang)


if __name__ == '__main__':
    for language in ('he', 'en'):
        for function in (sorting, constructor, tracker, subsets):
            function(language)
    print('Rendered eight bilingual batch10 software diagrams.')
