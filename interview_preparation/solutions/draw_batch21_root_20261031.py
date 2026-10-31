"""Bilingual reusable diagrams for anonymous navigation, barriers and residence."""
import math
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, INK, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1]/'diagrams'


def base(ident, he, en, language):
    im = Image.new('RGB', (2800, 1800), 'white'); d = ImageDraw.Draw(im)
    phrase(d, (1400, 100), he, en, language, 63, bold=True)
    text(d, (1400, 200), ident, 40, color=BLUE)
    return im, d


def rooms(language):
    im, d = base('PREP-201', 'סופרים חדרים באמצעות סימן וחזרה', 'Count rooms by a marker and counted return', language)
    center = (820, 900); radius = 480
    points = [(center[0]+radius*math.cos(i*math.pi/3), center[1]+radius*math.sin(i*math.pi/3)) for i in range(6)]
    for i, (x, y) in enumerate(points):
        xx, yy = points[(i+1)%6]; dx, dy = xx-x, yy-y; length = math.hypot(dx, dy)
        wire(d, [(x+100*dx/length, y+100*dy/length), (xx-105*dx/length, yy-105*dy/length)], BLUE)
    for i, (x, y) in enumerate(points):
        d.ellipse((x-95, y-95, x+95, y+95), fill='#f5f8fd', outline=ORANGE if i==0 else BLUE, width=8)
        d.ellipse((x-30, y-30, x+30, y+30), fill='#f2cf67' if i in (0, 2) else '#d7e1ed', outline=INK, width=3)
    phrase(d, (820, 910), 'דוגמה בלבד', 'Example only', language, 41)
    phrase(d, (820, 1500), 'החדרים אינם מסומנים באלגוריתם', 'No room identities are visible to the algorithm', language, 43)
    box(d, (1580, 370, 2630, 650), ORANGE)
    phrase(d, (2105, 455), 'מדליקים את העוגן', 'Light the chosen anchor', language, 45, bold=True)
    text(d, (2105, 570), 'anchor := ON', 43, color=ORANGE)
    box(d, (1580, 800, 2630, 1090), BLUE)
    phrase(d, (2105, 870), 'מוצאים מנורה דולקת ומכבים', 'Find a lit lamp and clear it', language, 42, bold=True)
    phrase(d, (2105, 1000), 'חוזרים בדיוק כמספר הצעדים', 'Retrace the counted steps', language, 43)
    wire(d, [(2105, 650), (2105, 800)], BLUE)
    box(d, (1580, 1250, 2630, 1530), GREEN)
    phrase(d, (2105, 1330), 'העוגן כבוי רק בסיבוב שלם', 'Anchor off means one complete cycle', language, 41, bold=True)
    text(d, (2105, 1450), 'OFF => n = steps', 44, color=GREEN)
    wire(d, [(2105, 1090), (2105, 1250)], BLUE)
    phrase(d, (1400, 1620), 'כאשר כל המנורות מתחילות דולקות', 'When all lamps start on', language, 43)
    text(d, (1400, 1710), 'M(n) = 2(1+2+...+n) = n(n+1)', 46, color=GREEN)
    im.save(OUT/f'prep-201-root-batch21-{language}.png')


def barrier(language):
    im, d = base('PREP-208', 'ממתינים לקידומת שהושלמה ללא חורים', 'Wait for the hole-free completed prefix', language)
    phrase(d, (1400, 360), 'לחיצה מצלמת יעד קבוע לפני קליטה נוספת', 'A press captures a fixed target before later arrivals', language, 47)
    states = [(1, True), (2, False), (3, True), (4, True), (5, False), (6, True)]
    for i, (ident, complete) in enumerate(states):
        x = 200+i*430
        d.rounded_rectangle((x, 620, x+340, 920), radius=24, fill='#edf7f1' if complete else '#fff4e8', outline=GREEN if complete else ORANGE, width=7)
        text(d, (x+170, 710), str(ident), 67, bold=True)
        phrase(d, (x+170, 835), 'הושלמה' if complete else 'ממתינה', 'done' if complete else 'pending', language, 42)
    d.line([(1885, 520), (1885, 1040)], fill=BLUE, width=7)
    text(d, (1885, 1120), 'T = 4', 53, color=BLUE, bold=True)
    text(d, (600, 1120), 'prefix = 1', 53, color=GREEN, bold=True)
    box(d, (500, 1310, 2300, 1570), ORANGE)
    phrase(d, (1400, 1380), 'השלמות מאוחרות אינן סוגרות חור ישן', 'Later completions do not fill an earlier hole', language, 46, bold=True)
    text(d, (1400, 1490), 'ready <=> prefix >= T', 46)
    phrase(d, (1400, 1690), 'השלמת המשימה השנייה תקדם את הקידומת ליעד', 'Finishing task two advances the prefix to the target', language, 43)
    im.save(OUT/f'prep-208-root-batch21-{language}.png')


def residence(language):
    im, d = base('PREP-209', 'זמן שהייה שהושלם וגיל של פקטים בפנים', 'Completed residence and unfinished packet ages', language)
    phrase(d, (1400, 350), 'אותן ספירות אינן מזהות איזה פקט יצא', 'Identical counts do not identify the departed packet', language, 47)
    phrase(d, (1400, 435), 'קטעי נוכחות שנחתכו בזמן התצפית', 'Presence intervals clipped at the observation time', language, 39)
    for y, x1, x2, color, label in [(600, 400, 2000, BLUE, 'p: 0 -> 10'), (900, 1840, 2000, GREEN, 'q: 9 -> 10')]:
        d.line([(x1, y), (x2, y)], fill=color, width=22)
        text(d, (1000, y-80), label, 45, color=color, bold=True)
    for x, label in [(400, '0'), (1840, '9'), (2000, '10')]:
        d.line([(x, 480), (x, 1040)], fill='#c8d8ed', width=4)
        text(d, (x, 1110), label, 45)
    box(d, (340, 1260, 2460, 1560), GREEN)
    text(d, (1400, 1340), 'A(t) = S(t) + G(t)' if language=='he' else 'A(t) = completed lifetimes + resident ages', 44, color=GREEN)
    phrase(d, (1400, 1450), 'ממוצע היוצאים יכול להיות עשר או אחת', 'Departed mean can be ten or one', language, 44, bold=True)
    phrase(d, (1400, 1515), 'השטח זהה בשני המקרים', 'The occupancy area is the same in both cases', language, 40)
    if language=='he':
        phrase(d, (1400, 1660), 'לממוצע מדויק של היוצאים דרושים זיהוי או סדר יציאה מובטח', 'unused', language, 43)
        text(d, (1400, 1730), 'A(10)=11', 42)
    else:
        text(d, (1400, 1690), 'A(10)=11    |    exact completed mean requires identity or FIFO', 42, color=INK)
    im.save(OUT/f'prep-209-root-batch21-{language}.png')


if __name__=='__main__':
    for lang in ('he', 'en'):
        rooms(lang); barrier(lang); residence(lang)
