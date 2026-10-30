"""Bilingual arithmetic, spectrum, MUX and five-way sorting explanations."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1]/'diagrams'
BG, INK, PURPLE, GREEN = '#fffdf8', '#302344', '#71558c', '#33786d'


def board(w, h):
    im = Image.new('RGB', (w,h), BG)
    return im, ImageDraw.Draw(im)


def panel(d, r, color=PURPLE):
    d.rounded_rectangle(r, 24, fill='#eee7f4' if color == PURPLE else '#e7f2ec', outline=color, width=5)


def arithmetic(lang):
    im,d=board(2200,1400)
    phrase(d,(1100,90),'חשבון רגיל עבור סיביות בודדות','Ordinary arithmetic for scalar bits',lang,54,bold=True)
    text(d,(1100,180),'X, Y in {0,1}',42,color=GREEN)
    panel(d,(100,275,2100,530))
    text(d,(1100,345),'NOT X = 1-X          AND = X*Y',48,bold=True)
    text(d,(1100,455),'OR = X+Y-X*Y          XOR = X+Y-2*X*Y',42,bold=True)
    cols=[300,620,940,1260,1580,1900]
    for x,name in zip(cols,['X','Y','NOT X','AND','OR','XOR'],strict=True):
        text(d,(x,650),name,42,bold=True)
    for i,row in enumerate([(0,0,1,0,0,0),(0,1,1,0,1,1),(1,0,0,0,1,1),(1,1,0,1,1,0)]):
        y=760+i*115
        if i==3:
            d.rounded_rectangle((160,y-45,2040,y+45),16,fill='#e7f2ec')
        for x,value in zip(cols,row,strict=True):
            text(d,(x,y),str(value),45)
    phrase(d,(1100,1240),'המכפלה מתקנת רק את המקרה שבו שניהם אחד','The product corrects only the both-one case',lang,42,bold=True)
    phrase(d,(1100,1320),'הנוסחאות אינן פעולות ביטיות על מספרים כלליים','These are not bitwise formulas for arbitrary integers',lang,36)
    im.save(OUT/f'prep-155-arithmetic-truth-table-{lang}.png')


def bandpass(lang):
    im,d=board(2400,1600)
    phrase(d,(1200,85),'רוחב הפס והמיקום קובעים יחד','Bandwidth and location both matter',lang,55,bold=True)
    text(d,(1200,180),'f1 = 90 kHz     f2 = 110 kHz     B = 20 kHz',45)
    panel(d,(140,270,2260,490))
    text(d,(1200,340),'m = 5:     44 < fs < 45 ksample/s',49,bold=True,color=PURPLE)
    text(d,(1200,430),'example: fs = 44.5 ksample/s',43,color=GREEN)
    phrase(d,(1200,590),'התחום המקורי בתוך אזור נייקוויסט יחיד','The original band fits inside one Nyquist zone',lang,43,bold=True)
    # Focused positive-frequency axis; the real signal also has a mirrored band.
    def x(f):
        return 250+(f-80)*1900/40
    wire(d,[(200,830),(2210,830)],INK,5)
    d.rectangle((x(89),680,x(111.25),830),fill='#eee7f4',outline=PURPLE,width=4)
    d.rectangle((x(90),710,x(110),830),fill='#c9e1d4',outline=GREEN,width=5)
    for f in (80,89,90,110,111.25,120):
        d.line((x(f),820,x(f),850),fill=INK,width=3)
        # Stagger nearby bounds so labels cannot collide.
        text(d,(x(f),895 if f in (89,111.25) else 950),str(f),31,color=PURPLE if f in (89,111.25) else INK)
    text(d,(1200,765),'90 .. 110 kHz',40,bold=True,color=GREEN)
    phrase(d,(1200,1050),'לאחר הקיפול בתחום הדגום','After folding into the sampled baseband',lang,43,bold=True)
    def z(f):
        return 250+f*1900/22.25
    wire(d,[(200,1280),(2220,1280)],INK,5)
    d.rectangle((z(1),1160,z(21),1280),fill='#c9e1d4',outline=GREEN,width=5)
    for f in (0,1,21,22.25):
        d.line((z(f),1270,z(f),1300),fill=INK,width=3)
        text(d,(z(f),1340 if f in (0,22.25) else 1395),str(f),33)
    text(d,(1200,1220),'1 .. 21 kHz',42,bold=True,color=GREEN)
    phrase(d,(1200,1490),'קצות החלון אינם בטוחים לטונים בעלי מופע שרירותי','Window endpoints are unsafe for arbitrary-phase endpoint tones',lang,37,bold=True)
    phrase(d,(1200,1560),'אות ממשי כולל גם תחום שלילי סימטרי שאינו מצויר כאן','A real signal also has the mirrored negative band, not shown here',lang,31)
    im.save(OUT/f'prep-156-bandpass-safe-windows-{lang}.png')


def mux(lang):
    im,d=board(2200,1450)
    phrase(d,(1100,90),'בחירה של כניסת נתונים אחת','Select one data input',lang,56,bold=True)
    d.polygon([(430,310),(900,430),(900,790),(430,910)],fill='#eee7f4',outline=PURPLE,width=7)
    text(d,(640,610),'MUX',54,bold=True)
    text(d,(640,690),'2:1',45)
    for y,name,choice in ((460,'D0','0'),(760,'D1','1')):
        wire(d,[(130,y),(430,y)],INK,7)
        text(d,(220,y-60),name,48,bold=True)
        text(d,(495,y),choice,42,color=PURPLE)
    wire(d,[(900,610),(1190,610)],GREEN,7)
    text(d,(1120,550),'Y',50,bold=True,color=GREEN)
    wire(d,[(665,1120),(665,850)],PURPLE,7)
    text(d,(665,1190),'S',50,bold=True,color=PURPLE)
    panel(d,(1330,330,2110,920),GREEN)
    text(d,(1530,425),'S',46,bold=True)
    text(d,(1890,425),'Y',46,bold=True)
    text(d,(1530,605),'0',50)
    text(d,(1890,605),'D0',50)
    text(d,(1530,795),'1',50)
    text(d,(1890,795),'D1',50)
    phrase(d,(1720,1040),'ללא שעון וללא זיכרון','No clock, no stored state',lang,34,bold=True)
    text(d,(1100,1320),'Y = (NOT S AND D0) OR (S AND D1)',44,bold=True,color=GREEN)
    im.save(OUT/f'prep-157-mux-symbol-truth-table-{lang}.png')


def sorter(lang):
    im,d=board(2500,1650)
    phrase(d,(1250,85),'שבע הפעלות של מיון חמישה','Seven five-way sorting invocations',lang,55,bold=True)
    phrase(d,(1250,175),'שמות הקבוצות נקבעים לפי דירוג המנצחים','Group names follow their winners’ ranking',lang,40)
    rows=[('A','A1 > A2 > A3 > A4 > A5'),('B','B1 > B2 > B3 > B4 > B5'),('C','C1 > C2 > C3 > C4 > C5'),('D','D1 > D2 > D3 > D4 > D5'),('E','E1 > E2 > E3 > E4 > E5')]
    for i,(_,row) in enumerate(rows):
        y=300+i*150
        panel(d,(100,y,1120,y+115))
        text(d,(610,y+58),row,39,bold=True)
    panel(d,(1340,380,2380,660),GREEN)
    phrase(d,(1860,440),'מיון מנצחי הקבוצות','Rank the group winners',lang,37,bold=True)
    text(d,(1860,555),'A1 > B1 > C1 > D1 > E1',38,bold=True,color=GREEN)
    wire(d,[(1120,565),(1340,565)],PURPLE,7)
    phrase(d,(1860,750),'אחרי ניתוב לפי זהות הזוכים','After identity-based routing',lang,35)
    panel(d,(1340,850,2380,1110))
    text(d,(1860,925),'sort [A2, A3, B1, B2, C1]',40,bold=True)
    text(d,(1860,1030),'top 2  ->  places 2, 3',39,color=GREEN)
    wire(d,[(1860,660),(1860,850)],GREEN,6)
    text(d,(630,1190),'A1 = global maximum',43,bold=True,color=GREEN)
    phrase(d,(1250,1340),'מימוש פרוס לעומת שימוש חוזר','Unrolled versus reused hardware',lang,46,bold=True)
    text(d,(1250,1435),'7 instances + routing    OR    1 instance + storage + 7 calls',37)
    phrase(d,(1250,1540),'הוכחת החסם מתירה סדר רק בתוך קופסת המיון','The query lower bound permits ordering only inside the sorter',lang,37)
    im.save(OUT/f'prep-009-five-way-sorter-top-three-{lang}.png')


if __name__=='__main__':
    for language in ('he','en'):
        arithmetic(language)
        bandpass(language)
        mux(language)
        sorter(language)
