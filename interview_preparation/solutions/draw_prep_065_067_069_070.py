"""Deterministic, localized, labelled block schematics; no raster AI assets."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, PURPLE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def canvas(title_he, title_en, lang, height=1550):
    im = Image.new('RGB', (2800, height), 'white')
    d = ImageDraw.Draw(im)
    phrase(d, (1400, 100), title_he, title_en, lang, 66, bold=True)
    return im, d


def label(d, xy, value, color=BLUE, size=47):
    text(d, xy, value, size, color=color, bold=True)


def dff(lang):
    im,d=canvas('דלגלג די בעזרת דלגלג אס אר','D flip-flop from an edge-triggered SR flip-flop',lang,1550)
    phrase(d,(1400,205),'רכיב סינכרוני בחזית עולה עם כניסות פעילות בגבוה',
           'Rising-edge primitive with synchronous active-high S and R',lang,43)
    box(d,(1510,390,2250,1050),GREEN)
    label(d,(1880,485),'SR FF',GREEN,62)
    label(d,(1570,620),'S',GREEN);label(d,(1570,900),'R',GREEN)
    label(d,(2180,760),'Q',GREEN)
    wire(d,[(300,620),(1510,620)])
    label(d,(320,550),'D')
    d.ellipse((642,612,658,628),fill=BLUE)
    wire(d,[(650,620),(650,900),(850,900)])
    box(d,(850,810,1170,990),ORANGE);label(d,(1010,900),'NOT',ORANGE)
    wire(d,[(1170,900),(1510,900)],ORANGE);label(d,(1320,820),'~D',ORANGE)
    label(d,(1280,550),'S = D')
    wire(d,[(2250,760),(2620,760)],GREEN);label(d,(2475,685),'Q',GREEN,57)
    wire(d,[(1880,1240),(1880,1050)],PURPLE)
    d.line([(1845,1050),(1880,1010),(1915,1050)],fill=PURPLE,width=5)
    label(d,(1880,1290),'clk',PURPLE)
    phrase(d,(1400,1400),'שינוי ביציאה רק בחזית השעון לאחר זמן התפשטות',
           'Q changes only after the clock edge plus propagation delay',lang,43)
    im.save(OUT/f'prep-065-sr-dff-{lang}.png')


def fifo(lang):
    im,d=canvas('תור חומרה עם שמונה תאי זיכרון','Eight-cell synchronous FIFO',lang,2200)
    phrase(d,(1400,210),'כל פעולות הזיכרון והבקרה משתמשות באותו שעון',
           'Storage and control use the same rising-edge clock',lang,44)
    box(d,(770,390,1990,1010),BLUE)
    label(d,(1380,465),'mem[0:7]    8 x W',BLUE,57)
    for i in range(8):
        x=815+i*140
        d.rectangle((x,575,x+135,770),outline=BLUE,width=4,fill='#edf3fb')
        label(d,(x+67,675),str(i),BLUE)
    label(d,(1380,900),'read old mem[rp]; write mem[wp]',BLUE,44)
    wire(d,[(100,650),(770,650)],BLUE);label(d,(380,570),'din[W-1:0]',BLUE,44)
    box(d,(2230,490,2730,880),GREEN)
    label(d,(2480,565),'DOUT REG',GREEN,47)
    label(d,(2480,700),'W bits',GREEN,43)
    wire(d,[(1990,650),(2230,650)],GREEN)
    wire(d,[(2480,880),(2480,1050)],GREEN);label(d,(2480,1105),'dout[W-1:0]',GREEN,42)
    box(d,(560,1340,2200,1870),PURPLE)
    label(d,(1380,1420),'CONTROL / REGISTERS',PURPLE,53)
    label(d,(1380,1540),'rp[2:0]    wp[2:0]    count[3:0]',PURPLE,46)
    label(d,(1380,1665),'pop = rd_en AND (count > 0)',PURPLE,42)
    label(d,(1380,1770),'push = wr_en AND ((count < 8) OR pop)',PURPLE,40)
    for y,name in [(1440,'rd_en'),(1580,'wr_en'),(1720,'rst'),(1830,'clk')]:
        wire(d,[(125,y),(560,y)],ORANGE);label(d,(280,y-55),name,ORANGE,42)
    wire(d,[(1050,1340),(1050,1180),(1030,1180),(1030,1010)],PURPLE)
    label(d,(875,1150),'rp / wp',PURPLE,40)
    wire(d,[(1670,1340),(1670,1180),(1770,1180),(1770,1010)],PURPLE)
    label(d,(1880,1180),'push / pop',PURPLE,40)
    wire(d,[(2200,1510),(2640,1510)],PURPLE);label(d,(2460,1440),'full / empty',PURPLE,39)
    wire(d,[(2200,1740),(2640,1740)],GREEN);label(d,(2460,1675),'rd_valid',GREEN,42)
    phrase(d,(1400,2010),'קריאה ריקה נדחית וגם כתיבה מלאה בלי קריאה נדחית',
           'Empty read rejected; full write accepted only with a valid read',lang,43)
    phrase(d,(1400,2105),'בקריאה וכתיבה יחד מתקבל קודם הערך הישן',
           'A simultaneous same-address read returns the old stored item',lang,43)
    im.save(OUT/f'prep-067-fifo8-{lang}.png')


def fault(lang, solution=False):
    he='בדיקת תקלה על ענף הכניסה לנור' if solution else 'המעגל הנתון והנקודה החשודה'
    en='Diagnosing the NOR-input branch fault' if solution else 'Given circuit and suspected branch point'
    im,d=canvas(he,en,lang,1900 if solution else 1500)
    phrase(d,(1400,205),'התקלה נמצאת רק בענף המסומן ואינה משפיעה על כניסת המהפך',
           'Only the marked branch is faulty; the inverter still receives original C',lang,43)
    box(d,(1080,520,1580,900),BLUE);label(d,(1330,710),'NOR',BLUE,61)
    box(d,(1080,1040,1580,1240),GREEN);label(d,(1330,1140),'NOT',GREEN,56)
    box(d,(2020,400,2530,1070),PURPLE);label(d,(2275,690),'AND',PURPLE,61)
    phrase(d,(2275,800),'שלוש כניסות','3 inputs',lang,39,color=PURPLE,bold=True)
    wire(d,[(180,370),(1820,370),(1820,520),(2020,520)],PURPLE)
    label(d,(210,310),'A',PURPLE,56)
    wire(d,[(180,610),(1080,610)],BLUE);label(d,(210,550),'B',BLUE,56)
    wire(d,[(180,1000),(620,1000)],GREEN,arrow=False);label(d,(210,940),'C',GREEN,56)
    d.ellipse((609,989,631,1011),fill=GREEN)
    wire(d,[(620,1000),(620,810),(1080,810)],BLUE)
    wire(d,[(620,1000),(620,1140),(1080,1140)],GREEN)
    label(d,(880,740),'X',ORANGE,58)
    d.line([(850,785),(900,835)],fill=ORANGE,width=10)
    d.line([(850,835),(900,785)],fill=ORANGE,width=10)
    wire(d,[(1580,710),(2020,710)],BLUE)
    wire(d,[(1580,1140),(1810,1140),(1810,940),(2020,940)],GREEN)
    label(d,(1810,1235),'~C',GREEN,48)
    wire(d,[(2530,710),(2730,710)],PURPLE);label(d,(2650,640),'Y',PURPLE,56)
    label(d,(850,1310),'X = C   /   stuck-at-0   /   stuck-at-1',ORANGE,42)
    if solution:
        label(d,(1400,1470),'Y = A AND NOT(B OR X) AND NOT C',PURPLE,48)
        label(d,(1400,1600),'A=1, B=0, C=0:   Y(clean)=1   Y(sa0)=1   Y(sa1)=0',ORANGE,42)
        phrase(d,(1400,1740),'תקלה תקועה באפס אינה נצפית ביציאה עבור שום קלט',
               'Stuck-at-0 is unobservable at Y for every input',lang,48,bold=True)
    im.save(OUT/f'prep-069-{"solution" if solution else "prompt"}-{lang}.png')


def fault_table(lang):
    im,d=canvas('טבלת אמת לכל סוגי התקלה','Complete branch-fault truth table',lang,1900)
    heads=['A','B','C','Y (clean)','Y (sa0)','Y (sa1)'];xs=[220,560,900,1420,1940,2460]
    for x,h in zip(xs,heads):label(d,(x,320),h,BLUE,46)
    for n in range(8):
        a,b,c=(n>>2)&1,(n>>1)&1,n&1
        y=int(a==1 and b==0 and c==0);yy=500+n*140
        if n==4:d.rounded_rectangle((70,yy-63,2720,yy+63),radius=15,fill='#fff0df')
        elif n%2==0:d.rectangle((70,yy-63,2720,yy+63),fill='#f0f5fb')
        for x,v in zip(xs,[a,b,c,y,y,0]):label(d,(x,yy),str(v),ORANGE if n==4 else BLUE,51)
    phrase(d,(1400,1710),'רק השורה המודגשת מפרידה בין תקלה תקועה באחת לבין מעגל תקין',
           'Only the highlighted row distinguishes stuck-at-1 from the healthy circuit',lang,42)
    im.save(OUT/f'prep-069-truth-table-{lang}.png')


def mux_and(lang):
    im,d=canvas('שער אנד בעזרת מרבב יחיד','AND from one 2:1 multiplexer',lang,1550)
    box(d,(1130,340,1830,1020),BLUE)
    label(d,(1480,435),'MUX 2:1',BLUE,61)
    label(d,(1230,615),'D0',BLUE,48);label(d,(1230,865),'D1',BLUE,48)
    wire(d,[(320,615),(1130,615)],GREEN);label(d,(400,545),'0',GREEN,62)
    wire(d,[(320,865),(1130,865)],BLUE);label(d,(400,795),'B',BLUE,62)
    wire(d,[(1480,1260),(1480,1020)],PURPLE)
    label(d,(1480,945),'S',PURPLE,50);label(d,(1480,1320),'A',PURPLE,62)
    wire(d,[(1830,735),(2540,735)],ORANGE);label(d,(2210,650),'Y = A AND B',ORANGE,53)
    label(d,(1400,1460),'S=0 -> D0=0       |       S=1 -> D1=B',BLUE,45)
    im.save(OUT/f'prep-070-and-mux-{lang}.png')


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    for language in ('he','en'):
        dff(language)
        fifo(language)
        fault(language)
        fault(language,True)
        fault_table(language)
        mux_and(language)
