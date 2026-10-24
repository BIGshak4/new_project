"""Reproducible bilingual bit diagrams with explicit widths and index labels."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
BG, CARD, INK, PURPLE, GREEN = '#f8f4e9', '#fffdf8', '#302344', '#5d4383', '#33786d'


def label(draw, position, value, size=40, color=INK):
    text(draw, position, value, size, color=color, bold=True)


def allocator(lang):
    im = Image.new('RGB', (1900, 1320), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (950, 90), 'מפת תפוסה של שלושים ושניים תאים', 'One occupancy bit per memory slot', lang, 60, bold=True)
    phrase(d, (950, 180), 'אחד פירושו תפוס; אפס פירושו פנוי', 'One means occupied; zero means free', lang, 42)
    for row in range(2):
        for col in range(16):
            index = 31 - row * 16 - col
            x, y = 150 + col * 100, 310 + row * 225
            used = index in (0, 1, 3)
            selected = index == 2
            d.rounded_rectangle((x, y, x + 84, y + 94), radius=12,
                                fill='#e1d5ed' if used else CARD,
                                outline=GREEN if selected else PURPLE, width=7 if selected else 3)
            label(d, (x + 42, y + 46), '1' if used else '0', 43)
            label(d, (x + 42, y - 43), str(index), 32)
    label(d, (950, 770), 'used = 0x0000000B', 47)
    wire(d, [(950, 815), (950, 895)], GREEN)
    label(d, (950, 955), 'malloc_index() = 2     used = 0x0000000F', 43, GREEN)
    phrase(d, (950, 1060), 'בוחרים את האינדקס הפנוי הנמוך ביותר ומסמנים רק אותו',
           'Select the lowest free index and set only its occupancy bit', lang, 40)
    phrase(d, (950, 1150), 'שחרור תא אינו מחייב איפוס של תוכן הזיכרון',
           'Freeing a slot need not erase its stored payload', lang, 40)
    phrase(d, (950, 1240), 'מצב ניהול יחיד: שלושים ושניים ביטים, בנפרד מתוכן התאים',
           'Persistent management state: 32 bits, separate from the payload', lang, 38)
    im.save(OUT / f'prep-102-bitmap-{lang}.png')


def onehot(lang):
    im = Image.new('RGB', (1900, 1260), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (950, 90), 'בודקים תבנית ביטים ברוחב קבוע', 'Test the complete fixed-width bit pattern', lang, 59, bold=True)
    phrase(d, (950, 180), 'ממירים ללא סימן לפני החיסור; אפס נפסל בנפרד',
           'Convert to unsigned before subtracting; reject zero separately', lang, 40)
    lines = [('u', '00000000000010000000000000000000'),
             ('u - 1', '00000000000001111111111111111111'),
             ('AND', '00000000000000000000000000000000')]
    for row, (name, bits) in enumerate(lines):
        y = 345 + row * 145
        label(d, (230, y), name, 44, PURPLE)
        label(d, (1100, y), bits, 43, GREEN if name == 'AND' else INK)
    label(d, (950, 810), 'u = 0x00080000 = 1 << 19', 48, PURPLE)
    phrase(d, (950, 925), 'גם ביט הסימן לבדו הוא ביט אחד פעיל',
           'The sign bit alone is still one active bit', lang, 43)
    label(d, (950, 1015), 'n = -2147483648     u = 0x80000000     TRUE', 40, GREEN)
    phrase(d, (950, 1130), 'זו אינה בדיקה שמספר חתום הוא חזקה חיובית של שתיים',
           'This differs from asking whether a signed value is a positive power of two', lang, 36)
    im.save(OUT / f'prep-105-one-hot-{lang}.png')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for language in ('he', 'en'):
        allocator(language)
        onehot(language)
