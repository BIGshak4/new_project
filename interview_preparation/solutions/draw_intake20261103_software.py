"""Clean original bilingual diagrams for the November3 software shard."""
from pathlib import Path
from PIL import Image, ImageDraw
from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def canvas(number, language, he, en):
    image = Image.new('RGB', (2800, 1500), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1400, 110), he, en, language, 57, bold=True)
    return image, draw


def save(image, number, language):
    image.save(OUT / f'prep-{number:03d}-software-batch1103-{language}.png')


def sudoku(language):
    image, draw = canvas(245, language, 'בוחרים תא מוגבל, מנסים ומחזירים לאחור', 'Choose a constrained cell, try, then undo on failure')
    for row in range(9):
        for col in range(9):
            x, y = 300 + col * 90, 330 + row * 90
            box(draw, (x, y, x+88, y+88), ORANGE if (row, col) == (0, 1) else BLUE)
            value = ['1', '?', '3', '4', '5', '6', '.', '8', '9'][col] if row == 0 else '.'
            text(draw, (x+44, y+44), value, 41)
    for k in (0, 3, 6, 9):
        draw.line((300+k*90,330,300+k*90,1140), fill=BLUE, width=8)
        draw.line((300,330+k*90,1110,330+k*90), fill=BLUE, width=8)
    phrase(draw, (1940, 480), 'רשימת מועמדים לתא', 'Candidates for a cell', language, 51)
    text(draw, (1940, 650), '{2, 7}', 100, color=GREEN)
    box(draw, (1450, 850, 2450, 1080), GREEN)
    phrase(draw, (1950, 965), 'מנסים, ממשיכים, ומבטלים בכישלון', 'try -> recurse -> undo', language, 48, color=GREEN)
    phrase(draw, (1400, 1340), 'הפתרון שומר כל נתון מקורי', 'Every original clue is preserved', language, 49)
    save(image, 245, language)


def streets(language):
    image, draw = canvas(246, language, 'מסכמים מרחקי רחובות לכל מועמד', 'Sum street-path distances to each candidate')
    positions = [(400,650), (1100,650), (1800,650), (1100,1080)]
    for a,b,length in [(0,1,2),(1,2,4),(1,3,1)]:
        wire(draw, [positions[a],positions[b]], BLUE)
        x=(positions[a][0]+positions[b][0])/2; y=(positions[a][1]+positions[b][1])/2
        text(draw,(x+65,y-80),str(length),58,color=BLUE)
    for i,(x,y) in enumerate(positions):
        draw.ellipse((x-105,y-105,x+105,y+105),fill='white',outline=GREEN if i==1 else BLUE,width=10)
        text(draw,(x,y),str(i),68,color=GREEN if i==1 else BLUE)
    phrase(draw,(2320,520),'צומתי האנשים','People vertices',language,46)
    text(draw,(2320,630),'0, 2, 3',53)
    text(draw,(2320,800),'2 + 4 + 1 = 7',48,color=GREEN)
    phrase(draw,(1400,1350),'רשת כללית אינה בהכרח מרחק מנהטן','A general street graph is not necessarily Manhattan distance',language,46)
    save(image,246,language)


def missing(language):
    image, draw = canvas(247,language,'לכל מספר חיובי יש תא ייעודי','A positive value v belongs at index v-1')
    for row,values in enumerate(([3,4,-1,1],[1,-1,3,4])):
        y=400+row*460
        for i,value in enumerate(values):
            x=420+i*520;box(draw,(x,y,x+450,y+210),GREEN if row and i!=1 else BLUE)
            text(draw,(x+225,y+105),str(value),80)
            text(draw,(x+225,y+270),str(i),46,color=BLUE)
    phrase(draw,(1400,1300),'המקום הראשון שבו חסר הערך הצפוי הוא התשובה','The first slot not holding i+1 reveals the missing value',language,47)
    phrase(draw,(1400,1430),'התשובה: שתיים','answer = 2',language,58,color=GREEN)
    save(image,247,language)


def reversal(language):
    image, draw = canvas(94,language,'החלפת קבוצות גדלות הופכת את סדר הסיביות','Swapping larger groups reverses all 32 bits')
    for i,(he,en) in enumerate([('ביטים שכנים','neighbour bits'),('קבוצות של שניים','pairs'),('קבוצות של ארבעה','nibbles'),('בתים','bytes'),('חצאי מילה','halfwords')]):
        y=290+210*i
        box(draw,(350,y,2450,y+160),GREEN if i==4 else BLUE)
        text(draw,(600,y+80),str(1<<i),65,color=GREEN if i==4 else BLUE)
        phrase(draw,(1500,y+80),he,en,language,52)
    phrase(draw,(1400,1430),'ללא טבלת חיפוש; אפסים מובילים נשמרים','No lookup table; leading-zero positions remain part of the word',language,45)
    save(image,94,language)


def deletion(language):
    image, draw = canvas(238,language,'מחיקת זהות לעומת העתקת ערך היורש','Removing node identity versus copying a successor value')
    for row in range(2):
        y=420+row*510
        for i,label in enumerate(['A','B','C'] if row==0 else ['A','C']):
            x=250+i*650;box(draw,(x,y,x+460,y+180),ORANGE if i==1 else BLUE)
            text(draw,(x+230,y+90),label,72)
            if i<2:wire(draw,[(x+460,y+90),(x+650,y+90)],BLUE)
        if row==1:
            text(draw,(1750,y+90),'NULL',65,color=BLUE)
    text(draw,(2420,510),'head -> A',51,color=BLUE)
    phrase(draw,(2400,1020),'זהות הצומת נשמרת','B keeps identity',language,39,color=ORANGE)
    phrase(draw,(1400,1370),'ללא ראש הרשימה: שיטת ההעתקה מוגבלת לצומת שאינו זנב','Without head: successor-copy requires a non-tail node',language,46)
    save(image,238,language)


if __name__=='__main__':
    for language in ('he','en'):
        for function in (sudoku,streets,missing,reversal,deletion):
            function(language)
    print('Rendered ten bilingual software diagrams.')
