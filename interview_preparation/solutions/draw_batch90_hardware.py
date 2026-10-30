"""Deterministic paired diagrams for the batch90 hardware additions."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parents[1]/'diagrams'
BG,INK,PURPLE,PALE,GREEN,GRAY='#fffdf8','#302344','#624883','#eee7f5','#30766a','#ddd6e4'


def canvas(he,en,lang,h=1400):
    im=Image.new('RGB',(2400,h),BG);d=ImageDraw.Draw(im)
    phrase(d,(1200,100),he,en,lang,55,bold=True,color=INK)
    return im,d


def label(d,xy,s,size=42):
    text(d,xy,s,size,bold=True,color=INK)


def box(d,rect,lines):
    d.rounded_rectangle(rect,25,fill=PALE,outline=PURPLE,width=6)
    x1,y1,x2,y2=rect
    for i,line in enumerate(lines):label(d,((x1+x2)/2,y1+(i+1)*(y2-y1)/(len(lines)+1)),line)


def table(d,rows,left,top,widths,rowheight=88,size=36):
    for r,row in enumerate(rows):
        x=left
        for value,w in zip(row,widths,strict=True):
            d.rectangle((x,top+r*rowheight,x+w,top+(r+1)*rowheight),fill=PALE if r==0 else BG,outline=GRAY,width=3)
            label(d,(x+w/2,top+(r+.5)*rowheight),str(value),size)
            x+=w


def serial(lang):
    im,d=canvas('חלוקה טורית בחמש','Serial long division by five',lang,1480)
    box(d,(150,330,700,620),['r[2:0]','0 <= r < 5'])
    box(d,(1000,300,1620,650),['t = 2r + b','z = (t >= 5)','r_next = t - 5z'])
    wire(d,[(700,470),(1000,470)],PURPLE);label(d,(860,410),'r')
    wire(d,[(1300,650),(1300,770),(430,770),(430,620)],GREEN)
    label(d,(920,725),'r_next')
    wire(d,[(840,220),(1300,220),(1300,300)],PURPLE);label(d,(810,220),'b')
    wire(d,[(1620,470),(2170,470)],GREEN);label(d,(1910,390),'z[0]')
    label(d,(1200,875),'NUM = 5Q + r   =>   Q_next = 2Q + z',45)
    table(d,[['r','b=0: r_next / z','b=1: r_next / z'],['0','0 / 0','1 / 0'],['1','2 / 0','3 / 0'],['2','4 / 0','0 / 1'],['3','1 / 1','2 / 1'],['4','3 / 1','4 / 1']],430,950,[240,630,630],70,34)
    phrase(d,(1200,1415),'פלט טורי מוביל באפסים מותר','Leading zero quotient bits are allowed',lang,36)
    return im


def mean(lang):
    im,d=canvas('ממוצע ללא איבוד נשא','Mean without losing the carry',lang,1200)
    box(d,(750,350,1500,740),['(N+1)-bit ADD','S = {0,A}+{0,B}'])
    for yy,value in ((460,'A[N-1:0]'),(640,'B[N-1:0]')):
        wire(d,[(180,yy),(750,yy)],PURPLE);label(d,(420,yy-75),value)
    wire(d,[(1500,480),(2160,480)],GREEN);label(d,(1840,400),'whole = S[N:1]')
    wire(d,[(1500,650),(2160,650)],GREEN);label(d,(1840,735),'half = S[0]')
    label(d,(1200,910),'M = whole + half / 2',50)
    label(d,(1200,1030),'A = 1111, B = 1110  =>  S = 11101  =>  14.5',42)
    return im


def bcd(lang):
    im,d=canvas('ספרת קלט אחת ושתי ספרות פלט','One input digit, two output digits',lang,1570)
    box(d,(140,310,760,650),['D[3:0]','valid = (D < 10)'])
    box(d,(1030,300,1620,660),['P = (D<<1)+D','P[5:0]','0 <= P <= 27'])
    wire(d,[(760,480),(1030,480)],PURPLE)
    wire(d,[(1620,420),(2190,420)],GREEN);label(d,(1940,340),'T[3:0]')
    wire(d,[(1620,580),(2190,580)],GREEN);label(d,(1940,670),'U[3:0]')
    table(d,[['D','0','1','2','3','4','5','6','7','8','9'],['BCD','00','03','06','09','12','15','18','21','24','27']],100,820,[200]+[200]*10,130,36)
    label(d,(1200,1230),'P >= 20: T=2,U=P-20',45)
    label(d,(1200,1320),'else P >= 10: T=1,U=P-10; else T=0,U=P',42)
    phrase(d,(1200,1460),'קלטים עשר עד חמש עשרה מסומנים כלא תקינים','Inputs 10 through 15 are explicitly invalid',lang,38)
    return im


def priority(lang):
    im,d=canvas('עדיפות לביט הנמוך ובחירת קבוצה','Lowest-bit priority and group selection',lang,1600)
    for group in range(4):
        y=280+group*250
        box(d,(150,y,720,y+190),[f'PE4 (LSB): G{group}',f'I[{4*group+3}:{4*group}]'])
        wire(d,[(720,y+95),(1000,y+95)],PURPLE);label(d,(850,y+40),f'V{group},K{group}',34)
    box(d,(1080,300,1710,720),['PE4 (LSB): V[3:0]','V = OR(V0..V3)','G[1:0]'])
    box(d,(1080,900,1710,1230),['MUX 4:1 x2','select = G','L = K[G]'])
    wire(d,[(1395,720),(1395,900)],GREEN)
    wire(d,[(1710,440),(2210,440)],GREEN);label(d,(1960,365),'V')
    wire(d,[(1710,1065),(2210,1065)],GREEN);label(d,(1960,980),'code = V ? {G,L} : 0',31)
    label(d,(1200,1360),'V=0: code=0; V=1,code=0: I0',38)
    label(d,(1200,1460),'PE8: g_i = I_i AND NOT(OR_{0<=j<i} I_j)',42)
    phrase(d,(1200,1540),'שמות אותות זהים מייצגים אותו חיבור','Identical net names denote the same connection',lang,35)
    return im


def half_full(lang):
    im,d=canvas('מחבר מלא משלושה מחברים למחצה','Full adder from three half adders',lang,1360)
    box(d,(200,350,770,680),['HA1','p=A XOR B','g=A AND B'])
    box(d,(970,350,1540,680),['HA2','S=p XOR Cin','h=p AND Cin'])
    box(d,(1750,350,2250,680),['HA3','Cout=g XOR h','unused=g AND h'])
    wire(d,[(770,470),(970,470)],PURPLE);label(d,(870,400),'p')
    wire(d,[(1250,230),(1250,350)],PURPLE);label(d,(1250,185),'Cin')
    wire(d,[(770,600),(850,600),(850,810),(2000,810),(2000,680)],GREEN)
    label(d,(1890,755),'g',42)
    wire(d,[(1540,600),(1750,600)],GREEN);label(d,(1640,540),'h')
    wire(d,[(1540,470),(1660,470)],PURPLE);label(d,(1600,405),'S',38)
    wire(d,[(2250,470),(2360,470)],PURPLE);label(d,(2300,400),'Cout',34)
    for yy,value in ((450,'A'),(600,'B')):
        wire(d,[(70,yy),(200,yy)],PURPLE);label(d,(110,yy-60),value,36)
    label(d,(1200,950),'g*h = A*B*(A XOR B)*Cin = 0',48)
    label(d,(1200,1060),'g OR h = g XOR h; unused = g AND h = 0',44)
    phrase(d,(1200,1210),'אין שער חיצוני שמאחד את הנשאים','No external carry-combining gate',lang,40)
    return im


def window(lang):
    im,d=canvas('שישה אירועים בחלון נע של שבעה','Six events in a sliding seven-sample window',lang,1380)
    box(d,(220,320,950,650),['history[6:0]','oldest = history[6]'])
    box(d,(1230,320,2150,650),['count_next = count + X - oldest','filled_next = min(7,filled+1)'])
    wire(d,[(950,490),(1230,490)],PURPLE)
    label(d,(1200,810),'alarm_next = (filled_next==7) AND (count_next>=6)',42)
    table(d,[['sample','1','2','3','4','5','6','7','8','9'],['X','1','1','1','1','1','1','0','0','1'],['alarm','0','0','0','0','0','0','1','0','0']],120,930,[300]+[210]*9,95,35)
    phrase(d,(1200,1290),'החלון הראשון שלם רק אחרי הדגימה השביעית','The first full window exists only after sample seven',lang,38)
    return im


def pulse(lang):
    im,d=canvas('פולס בכל חזית שעון חמישים','A pulse on every fiftieth clock edge',lang,1280)
    box(d,(180,300,800,650),['phase[5:0]','0..49','reset ->0'])
    box(d,(1110,300,2140,650),['pulse_next = (phase==49)','phase_next = pulse_next ?0:phase+1'])
    wire(d,[(800,470),(1110,470)],PURPLE)
    label(d,(1200,815),'edge:    1 ... 48  49  50  51 ...  99 100',45)
    label(d,(1200,930),'pulse:   0 ...  0   0   1   0 ...   0   1',45)
    phrase(d,(1200,1080),'משך הפולס מחזור קלט אחד ולא חצי מחזור פלט','Pulse width is one input cycle, not half the output period',lang,38)
    return im


def memory(lang,prompt=False):
    im,d=canvas('ממשק הזיכרון שסופק','Supplied memory interface',lang,1340)
    box(d,(1020,340,1850,980),['MEMORY',''] if prompt else ['RAM','1024 x16 bits','16384 bits =2048 bytes'])
    if prompt:phrase(d,(1435,765),'הפונקציה אינה נתונה','Function unspecified',lang,40)
    wire(d,[(220,480),(1020,480)],PURPLE);label(d,(600,410),'IN[9:0]',40)
    wire(d,[(1850,610),(2220,610)],GREEN)
    wire(d,[(2220,610),(1850,610)],GREEN)
    label(d,(2100,520),'IO[15:0]',38)
    for yy in (790,900):
        wire(d,[(600,yy),(1020,yy)],PURPLE);label(d,(790,yy-50),'?',48)
    phrase(d,(1200,1120),'שני פיני הבקרה אינם מסומנים במקור','The source does not label the two control pins',lang,42)
    if not prompt:phrase(d,(1200,1230),'הבדיקות מניחות פעולות קריאה וכתיבה שהוגדרו בנפרד','Tests assume separately specified read and write operations',lang,38)
    return im


if __name__=='__main__':
    for language in ('he','en'):
        for number,stem,draw in ((179,'serial-divide-five',serial),(180,'binary-mean',mean),(181,'bcd-times-three',bcd),(16,'lsb-priority-batch90',priority),(122,'ha-fa-batch90',half_full),(95,'six-of-seven-batch90',window),(78,'fiftieth-edge-batch90',pulse),(76,'capacity-batch90',memory)):
            draw(language).save(OUT/f'prep-{number:03d}-{stem}-{language}.png')
        memory(language,True).save(OUT/f'prep-076-capacity-question-batch90-{language}.png')
