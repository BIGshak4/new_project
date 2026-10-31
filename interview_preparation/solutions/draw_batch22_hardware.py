"""Clean bilingual schematics for RC/follower, integrator and data movement."""
from pathlib import Path

from draw_batch21_hardware import (
    GREEN,
    INK,
    PALE,
    PURPLE,
    canvas,
    label,
    table,
)
from draw_prep_016_064 import phrase, wire

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def box(draw, rect, lines, lg='en'):
    draw.rounded_rectangle(rect,24,fill=PALE,outline=PURPLE,width=6)
    x1,y1,x2,y2=rect
    for index,line in enumerate(lines,1):
        position=((x1+x2)/2,y1+index*(y2-y1)/(len(lines)+1))
        if isinstance(line,tuple):
            phrase(draw,position,*line,lg,39,bold=True,color=INK)
        else:
            label(draw,position,line)


def ground(draw, x, y):
    wire(draw, [(x,y),(x,y+35)], INK, 5, arrow=False)
    for k in range(3):
        draw.line([(x-35+10*k,y+35+14*k),(x+35-10*k,y+35+14*k)], fill=INK, width=5)


def dot(draw, x, y):
    draw.ellipse((x-8,y-8,x+8,y+8), fill=PURPLE)


def resistor(draw, x1, x2, y):
    draw.rectangle((x1,y-30,x2,y+30), outline=PURPLE, fill=PALE, width=5)


def opamp(draw, x, y):
    draw.polygon([(x,y-200),(x,y+200),(x+420,y)], outline=PURPLE, fill=PALE, width=6)
    label(draw,(x+45,y-100),'-',47)
    label(draw,(x+45,y+100),'+',47)


def lpf(lg):
    im,d = canvas('מסנן מעביר נמוכים עם עוקב מתח','Low-pass filter with a voltage follower',lg,1500)
    wire(d,[(130,630),(400,630)],PURPLE,arrow=False); label(d,(160,550),'Vin',48)
    resistor(d,400,580,630); label(d,(490,545),'R',48)
    wire(d,[(580,630),(1050,630),(1050,710),(1350,710)],PURPLE,arrow=False)
    dot(d,720,630)
    wire(d,[(720,630),(720,760)],PURPLE,arrow=False)
    d.line([(665,760),(775,760)],fill=PURPLE,width=6); d.line([(665,795),(775,795)],fill=PURPLE,width=6)
    wire(d,[(720,795),(720,910)],PURPLE,arrow=False); ground(d,720,910); label(d,(830,775),'C',48)
    label(d,(865,560),'v',45)
    opamp(d,1350,610)
    wire(d,[(1770,610),(2200,610)],GREEN,arrow=False); label(d,(2150,520),'Vout',48)
    wire(d,[(1870,610),(1870,350),(1240,350),(1240,510),(1350,510)],GREEN,arrow=False); dot(d,1870,610)
    phrase(d,(1200,1110),'המשוב לכניסה השלילית; הקבל לאדמה','Feedback goes to the negative input; the capacitor goes to ground',lg,41)
    label(d,(1200,1230),'H(s) = 1 / (1+sRC)       fc = 1 / (2 pi RC)',48)
    label(d,(1200,1350),'Vout / v = A / (1+A)  ->  1',45)
    return im


def integrator(lg):
    im,d = canvas('אינטגרטור הופך במשוב קיבולי','Inverting integrator with capacitive feedback',lg,1650)
    wire(d,[(130,500),(400,500)],PURPLE,arrow=False); label(d,(170,410),'Vin',48)
    resistor(d,400,580,500); label(d,(490,415),'R',48)
    wire(d,[(580,500),(1350,500)],PURPLE,arrow=False); dot(d,800,500)
    opamp(d,1350,600)
    wire(d,[(1770,600),(2200,600)],GREEN,arrow=False); label(d,(2160,510),'Vout',48)
    wire(d,[(800,500),(800,300),(1090,300)],GREEN,arrow=False)
    d.line([(1090,245),(1090,355)],fill=PURPLE,width=6); d.line([(1125,245),(1125,355)],fill=PURPLE,width=6)
    wire(d,[(1125,300),(1900,300),(1900,600)],GREEN,arrow=False); dot(d,1900,600); label(d,(1105,200),'C',48)
    wire(d,[(1100,850),(1100,700),(1350,700)],PURPLE,arrow=False); ground(d,1100,850)
    label(d,(930,570),'v- ~ 0',39)
    wire(d,[(600,425),(730,425)],GREEN,4); label(d,(665,360),'iR',38)
    label(d,(1200,1050),'dVout/dt = -Vin/(RC)',53)
    label(d,(1200,1170),'Vin = +0.1 V;  RC = 1 ms;  dVout/dt = -100 V/s',43)
    # A DC ramp with the initial point shown, not a periodic waveform.
    wire(d,[(570,1520),(570,1260)],INK,4); wire(d,[(570,1310),(1800,1310)],INK,4)
    wire(d,[(600,1310),(1700,1470)],PURPLE,6,arrow=False)
    label(d,(460,1280),'V0',35); label(d,(1850,1310),'t',35)
    phrase(d,(1200,1590),'נגד משוב במקביל הוא הרחבה נפרדת','A parallel feedback resistor is a separate extension',lg,37)
    return im


def ramp(lg):
    im,d = canvas('ארבעה בתים בכל קריאה וגבולות מפורשים','Four bytes per read with explicit boundaries',lg,1500)
    table(d,[[('כתובת','address'),'0','1','2','3'],[('בית בהקס','byte hex'),'00','01','02','03']],220,270,[520,340,340,340,340],lg,height=120,size=43)
    box(d,(220,660,1120,950),['little-endian','0x03020100','50462976'])
    box(d,(1280,660,2180,950),['big-endian','0x00010203','66051'])
    phrase(d,(1200,1040),'כתובות התחלה מיושרות','Aligned starting addresses',lg,40)
    label(d,(1200,1110),'0, 4, 8, ... , 252  =>  64',43)
    phrase(d,(1200,1190),'כל כתובות ההתחלה החוקיות','Every legal starting address',lg,40)
    label(d,(1200,1260),'0, 1, ... , 252  =>  253',43)
    phrase(d,(1200,1340),'אין קריאה שחורגת מארבעת הבתים האחרונים','No read extends beyond the final four bytes',lg,42)
    phrase(d,(1200,1420),'בדיקה של תבנית נתונה אינה בדיקה של כל התקלות','One prescribed pattern does not test every possible fault',lg,38)
    return im


def copy_register(lg):
    im,d = canvas('העתקה אל רגיסטר שני בלי רגיסטר נתונים שלישי','Copy to a second register without a third data register',lg,1670)
    box(d,(240,310,920,620),['A: Q[N-1:0]',('החזקה','hold')],lg)
    box(d,(1490,310,2170,620),['B: D[N-1:0]',('לכידה','capture')],lg)
    wire(d,[(920,465),(1490,465)],PURPLE); label(d,(1200,390),'N',44)
    phrase(d,(1200,745),'חיבור מקביל מאפשר חזית לכידה אחת','Parallel wiring permits one capture edge',lg,43)
    box(d,(240,930,920,1240),['A',('הזזה ימינה','shift right'),'LSB -> MSB'],lg)
    box(d,(1490,930,2170,1240),['B',('הזזה ימינה','shift right'),'A_old[0] -> MSB'],lg)
    wire(d,[(920,1085),(1490,1085)],GREEN); label(d,(1200,1000),'A_old[0]',43)
    wire(d,[(1010,1085),(1010,1320),(140,1320),(140,1085),(240,1085)],GREEN,arrow=False); dot(d,1010,1085)
    label(d,(1200,1430),'N=3:  (101,010) -> (110,101) -> (011,010) -> (101,101)',41)
    phrase(d,(1200,1550),'במסלול טורי נדרשות מספר חזיתות השווה לרוחב','A serial path needs as many edges as the word width',lg,41)
    phrase(d,(1200,1625),'בקרה חיצונית אם גם רגיסטר בקרה נוסף אסור','Use external control if another control register is forbidden too',lg,35)
    return im


def nand_drivers(lg):
    im,d = canvas('שלושה רכיבי דרייבר מממשים שער נאנד','Three driver cells implement NAND',lg,1620)
    specs=[('A(x,x)',400),('A(y,y)',700),('B(x,y)',1000)]
    for title,y in specs:
        box(d,(220,y-100,850,y+100),[title])
        wire(d,[(850,y),(1180,y)],PURPLE,arrow=False)
    wire(d,[(1180,400),(1180,1000)],PURPLE,arrow=False)
    for _,y in specs:dot(d,1180,y)
    wire(d,[(1180,700),(1580,700)],GREEN);label(d,(1630,700),'F',60)
    table(d,[['xy','A(x,x)','A(y,y)','B(x,y)','F'],['00','1','1','Z','1'],['01','1','Z','Z','1'],['10','Z','1','Z','1'],['11','Z','Z','0','0']],180,1210,[230,500,500,500,260],lg,height=65,size=35)
    phrase(d,(1840,350),'יציאה משותפת פתורה','One resolved output net',lg,36)
    phrase(d,(1840,470),'אין דרייברים מנוגדים','No opposing drivers',lg,36)
    phrase(d,(1840,870),'ברמת אפס אפס שני דרייברים מסכימים','At zero zero two drivers agree',lg,33)
    phrase(d,(1200,1580),'מינימום שלושה תאים במודל הסטטי המוגדר','Minimum three cells in the stated static model',lg,38)
    return im


def popcount(lg):
    im,d = canvas('מוחקים אחד בכל צעד עד אפס','Delete one set bit per step until zero',lg,1400)
    rows=[[('צעד','step'),('מצב בינארי','x binary'),('מונה','count')],['0','10110100','0'],['1','10110000','1'],['2','10100000','2'],['3','10000000','3'],['4','00000000','4']]
    table(d,rows,400,260,[350,900,350],lg,height=120,size=47)
    label(d,(1200,1120),'x_next = x AND (x-1)',55)
    label(d,(1200,1240),'count + ones(x_current) = ones(x_original)',43)
    phrase(d,(1200,1350),'רוחב בלתי מסומן מוגדר מונע עמימות של מספר שלילי','An explicit unsigned width avoids ambiguity for negative integers',lg,37)
    return im


if __name__ == '__main__':
    for number,stem,render in [(221,'lpf-follower',lpf),(222,'integrator',integrator),
                               (223,'ramp-word-reads',ramp),(227,'register-copy',copy_register),
                               (15,'nand-drivers',nand_drivers),(151,'uint32-popcount',popcount)]:
        for language in ('he','en'):
            render(language).save(OUT/f'prep-{number:03d}-{stem}-batch22-{language}.png')
