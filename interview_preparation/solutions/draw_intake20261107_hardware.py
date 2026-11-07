"""Original clean HE/EN hardware diagrams; source screenshots stay archived."""
from pathlib import Path
from PIL import Image, ImageDraw
from draw_prep_016_064 import BLUE, GREEN, ORANGE, PURPLE, box, phrase, text, wire

OUT=Path(__file__).resolve().parents[1]/'diagrams'


def canvas(he,en,lg):
    im=Image.new('RGB',(3200,1800),'white');d=ImageDraw.Draw(im)
    phrase(d,(1600,120),he,en,lg,59,bold=True)
    return im,d


def save(im,num,stem,lg):im.save(OUT/f'prep-{num:03d}-{stem}-batch1107-{lg}.png')


def decimal(lg,num):
    times=num==257
    im,d=canvas('מפרידים ערך בינארי מספרות עשרוניות','Separate a binary value from decimal digits',lg)
    for x0,x1,label in [(390,1110,'zero-extend + (x<<2)+x' if times else 'x passthrough + valid'),
                         (1510,2280,'binary -> BCD' if times else 'convert; zero if !valid')]:
        box(d,(x0,470,x1,820),BLUE)
        if lg=='he':
            he_label=('הרחבת אפסים וחיבור' if times else 'העברת קלט ובדיקת תחום') if x0==390 else (
                'המרה לספרות עשרוניות' if times else 'המרה ואיפוס בפסילה')
            phrase(d,((x0+x1)//2,645),he_label,label,lg,41,bold=True)
        else:text(d,((x0+x1)//2,645),label,41,bold=True)
    wire(d,[(130,645),(390,645)]);text(d,(190,550),'x[3:0]' if times else 'x[5:0]',47)
    wire(d,[(1110,645),(1510,645)]);text(d,(1310,550),'product[6:0]' if times else 'x[5:0]',43)
    wire(d,[(2280,570),(2600,570)]);text(d,(2750,570),'tens[3:0]',46)
    wire(d,[(2280,740),(2600,740)]);text(d,(2750,740),'ones[3:0]',46)
    if not times:
        wire(d,[(750,470),(750,350),(1900,350),(1900,470)],ORANGE)
        text(d,(1480,270),'valid = (x <= 32)',43,color=ORANGE)
    rows=[('x','5*x','tens','ones'),('0','0','0','0'),('9','45','4','5'),('15','75','7','5')] if times else [
        ('x','valid','tens','ones'),('0','1','0','0'),('9','1','0','9'),('10','1','1','0'),('32','1','3','2'),('33','0','0','0')]
    for row,values in enumerate(rows):
        y=1000+row*100
        for col,value in enumerate(values):text(d,(650+col*650,y),value,48,bold=row==0,color=GREEN if row==0 else BLUE)
    phrase(d,(1600,1680),'כל ספרה ביציאה היא בתחום אפס עד תשע','Each output digit is in 0..9',lg,51,color=GREEN)
    save(im,num,'decimal',lg)


def threshold(lg):
    im,d=canvas('מספיק לזכור עד שלושה','Saturating at three is enough',lg)
    text(d,(1600,300),'c0=0     ci+1 = min(3, ci + xi)     y=(cN==3)',60,bold=True)
    for i,x in enumerate([380,1080,1780]):
        box(d,(x,650,x+500,1000),BLUE)
        phrase(d,(x+250,765),'רוויה בשלוש','saturate at 3',lg,45,bold=True)
        text(d,(x+250,900),f'x{i}',58,color=ORANGE)
        wire(d,[(x+250,1160),(x+250,1000)],ORANGE)
        text(d,(x+250,1220),f'x[{i}]',46,color=ORANGE)
        if i<2:wire(d,[(x+500,810),(x+700,810)])
    text(d,(2500,810),'...',75);wire(d,[(2580,810),(2920,810)])
    text(d,(2870,690),'cN==3',53,color=GREEN)
    phrase(d,(1600,1430),'זהו קיפול צירופי ללא שעון','Combinational fold; no clock',lg,55)
    phrase(d,(1600,1580),'שתי אחדות אינן מספיקות','Exactly two ones must produce zero',lg,51,color=ORANGE)
    save(im,263,'threshold',lg)


def sr(lg):
    im,d=canvas('שתי חלופות לעדיפות בקלט בו שני האותות פעילים','Two separate priorities when S=R=1',lg)
    for row,(he,en,eq) in enumerate([
        ('עדיפות להצבה','Set priority','D = S OR (Q AND NOT R)'),
        ('עדיפות לאיפוס','Reset priority','D = NOT R AND (S OR Q)')]):
        y=450+row*600
        phrase(d,(650,y+120),he,en,lg,52)
        text(d,(1400,y+120),eq,44,bold=True)
        box(d,(2200,y,2730,y+340),BLUE);text(d,(2465,y+130),'DFF',62,bold=True)
        wire(d,[(1920,y+120),(2200,y+120)])
        wire(d,[(2730,y+120),(3030,y+120)]);text(d,(3050,y+40),'Q',50)
        wire(d,[(2850,y+120),(2850,y+420),(1800,y+420),(1800,y+240)],GREEN)
        wire(d,[(2465,y+440),(2465,y+340)]);text(d,(2465,y+495),'clk',43)
    phrase(d,(1600,1660),'כל חלופה משתמשת בדלגלג אחד ובמשוב נתונים','Each alternative uses one DFF and data feedback',lg,51)
    save(im,65,'sr-from-dff',lg)


def lsb(lg):
    from draw_prep_206_serial_seven_batch1107 import serial_seven
    serial_seven(lg)


def netlist(lg):
    im,d=canvas('מפרידים מסלול נתונים מעץ איפוס','Separate a data path from reset distribution',lg)
    for row,color in [(0,BLUE),(1,ORANGE)]:
        y=500+row*650
        for i,x in enumerate([300,950,1600]):
            box(d,(x,y,x+430,y+230),color);text(d,(x+215,y+115),f'BUF {i+1}',47,color=color)
            if i<2:wire(d,[(x+430,y+115),(x+650,y+115)],color)
        text(d,(2200,y+110),'... BUF 12',48,color=color)
        wire(d,[(2460,y+115),(2750,y+115)],color)
        box(d,(2750,y,3070,y+230),color);text(d,(2910,y+115),'D' if row==0 else 'RST',52,bold=True,color=color)
        phrase(d,(1600,y+355),'מדווחים מסלול בן שנים עשר רכיבים' if row==0 else 'מזהים תפקידי פינים לפני סינון',
            'Report the twelve-buffer data witness' if row==0 else 'Classify trusted pin roles before filtering',lg,49,color=color)
    phrase(d,(1600,1660),'שם אות ומספר חיבורים לבדם אינם הוכחה שזה איפוס','A name or high fanout alone does not prove reset usage',lg,48)
    save(im,261,'netlist',lg)


def fifo(lg):
    im,d=canvas('תור בעל שני שעונים ושני מסלולי סנכרון','Dual-clock FIFO with two pointer crossings',lg)
    for x in [1450,1490]:d.line((x,330,x,1500),fill='#9da7b3',width=4)
    box(d,(200,420,1120,800),BLUE);phrase(d,(660,500),'תחום שעון הכתיבה','wclk domain',lg,53,bold=True)
    text(d,(660,610),'wbin, wgray, full',47);text(d,(660,710),'write iff w_en AND !full',40)
    box(d,(2080,420,3000,800),GREEN);phrase(d,(2540,500),'תחום שעון הקריאה','rclk domain',lg,53,bold=True)
    text(d,(2540,610),'rbin, rgray, empty',47);text(d,(2540,710),'read iff r_en AND !empty',40)
    box(d,(1220,600,1930,940),PURPLE);phrase(d,(1575,720),'זיכרון דו פורט','dual-port RAM',lg,46,bold=True)
    text(d,(1575,840),'data[DEPTH][W]',41)
    wire(d,[(1120,680),(1220,680)],BLUE);wire(d,[(1930,680),(2080,680)],GREEN)
    for y,label,direction,color in [(1110,'wgray -> 2 FF @ rclk',1,BLUE),(1380,'rgray -> 2 FF @ wclk',-1,GREEN)]:
        box(d,(1050,y-70,2210,y+110),color);text(d,(1630,y+20),label,48,bold=True,color=color)
        if direction==1:
            wire(d,[(660,800),(660,y+20),(1050,y+20)],color)
            wire(d,[(2210,y+20),(2540,y+20),(2540,800)],color)
        else:
            wire(d,[(2800,800),(2800,y+20),(2210,y+20)],color)
            wire(d,[(1050,y+20),(400,y+20),(400,800)],color)
    phrase(d,(1600,1660),'חוצים מצביעי גריי ולא דגלים או מונה בינארי גולמי','Cross Gray pointers, not raw binary counters or unsynchronized flags',lg,45)
    save(im,264,'async-fifo-architecture',lg)
    im,d=canvas('מתי דגל הריק מתבטל במימוש הרשום','When registered empty deasserts in this implementation',lg)
    rows=[('edge','sync1','sync2','empty after edge','read accepted'),
          ('before','0','0','1','no'),('R1','new','0','1','no'),
          ('R2','new','new','1','no'),('R3','new','new','0','no'),('R4','new','new','1','yes')]
    he_words={'edge':'חזית','sync1':'שלב ראשון','sync2':'שלב שני','empty after edge':'ריק לאחר החזית',
              'read accepted':'קריאה אושרה','before':'לפני','new':'חדש','no':'לא','yes':'כן'}
    for row,values in enumerate(rows):
        y=400+row*180
        for col,value in enumerate(values):
            if lg=='he' and value in he_words:
                text(d,(250+col*650,y),he_words[value],39,hebrew=True,bold=row==0,color=GREEN if row==4 else BLUE)
            else:text(d,(250+col*650,y),value,39,bold=row==0,color=GREEN if row==4 else BLUE)
    phrase(d,(1600,1540),'כתיבה יחידה ולחצן קריאה מוחזק בכל החזיתות','One write; read request remains asserted at every edge',lg,48)
    phrase(d,(1600,1660),'הפאזה והמטא יציבות עשויות להוסיף זמן','Phase and metastability may add latency',lg,48,color=ORANGE)
    save(im,264,'async-fifo-latency',lg)


if __name__=='__main__':
    for lg in ('he','en'):
        decimal(lg,257);decimal(lg,262)
        for function in (threshold,sr,lsb,netlist,fifo):function(lg)
    print('Rendered eighteen original bilingual hardware diagrams.')
