"""Clean bilingual engineering figures; original screenshots remain untouched."""
from pathlib import Path
from draw_batch21_hardware import GREEN, PALE, PURPLE, canvas, label, table
from draw_prep_016_064 import phrase, wire

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def box(d, rect, lines):
    d.rounded_rectangle(rect, 18, fill=PALE, outline=PURPLE, width=5)
    x1, y1, x2, y2 = rect
    for i, line in enumerate(lines, 1):
        label(d, ((x1+x2)/2, y1+i*(y2-y1)/(len(lines)+1)), line, 36)


def dot(d, x, y):
    d.ellipse((x-7, y-7, x+7, y+7), fill=PURPLE)


def swap(lg):
    im,d=canvas('מחליפים רק 5 ו־7 ומשמרים את כל היתר','Exchange only 5 and 7; preserve every other input',lg,1250)
    for y,name in [(300,'x2'),(600,'x1'),(900,'x0')]:
        label(d,(130,y-50),name,43)
    wire(d,[(180,300),(2250,300)],PURPLE,5);label(d,(2280,250),'y2',43)
    wire(d,[(180,900),(2250,900)],PURPLE,5);label(d,(2280,850),'y0',43)
    box(d,(700,390,1050,600),['AND','e = x2 & x0'])
    wire(d,[(400,300),(400,440),(700,440)],PURPLE,4);dot(d,400,300)
    wire(d,[(530,900),(530,550),(700,550)],PURPLE,4);dot(d,530,900)
    box(d,(1450,510,1850,730),['XOR','y1 = x1 ^ e'])
    wire(d,[(1050,495),(1260,495),(1260,570),(1450,570)],GREEN,5)
    wire(d,[(180,600),(300,600),(300,690),(1450,690)],PURPLE,5)
    wire(d,[(1850,620),(2250,620)],GREEN,5);label(d,(2280,560),'y1',43)
    label(d,(1200,1020),'101 -> 111    111 -> 101',50)
    phrase(d,(1200,1135),'שער אחד לזיהוי ושער אחד להיפוך מותנה; כל שמונת הקלטים חוקיים','One AND and one XOR; all eight inputs are legal',lg,39)
    return im


def pulse(lg):
    im,d=canvas('פולס של מחצית גבוהה אחת לפי חוזה מפורש','One high-phase pulse under an explicit timing contract',lg,1600)
    events=[0,1,2,3,4,5,6,6.25,7,8,9,10]
    x=lambda t:350+t*185
    clk=lambda t:int(1<=t<2 or 3<=t<4 or 5<=t<6 or 7<=t<8 or 9<=t<10)
    vin=lambda t:int(1<=t<6.25)
    out=lambda t:int(5<=t<6)
    for idx,(name,fn,color)in enumerate([('clk',clk,PURPLE),('Vin',vin,GREEN),('Out',out,'#ae5371')]):
        y=350+idx*235;label(d,(160,y-35),name,44)
        pts=[];old=fn(events[0]);pts.append((x(0),y-old*100))
        for t in events[1:]:
            pts.append((x(t),y-old*100));old=fn(t);pts.append((x(t),y-old*100))
        d.line(pts,fill=color,width=7)
    for t in (2,4,6,8):
        d.line((x(t),220,x(t),1030),fill='#c3c9d0',width=2)
    phrase(d,(1200,1020),'עדכון מצב בירידות; הקלט יציב סביבן','State updates on falls; Vin meets timing around them',lg,40)
    for a,b,text in [(0,2,'00'),(2,4,'01'),(4,6,'10'),(6,8,'11'),(8,10,'00')]:
        label(d,((x(a)+x(b))/2,1120),text,46)
    label(d,(160,1120),'count',36)
    phrase(d,(1200,1260),'ירידת הקלט צוירה מעט אחרי החזית כדי להימנע מעמימות דגימה','Vin falls slightly after the edge to avoid sampling ambiguity',lg,38)
    label(d,(1200,1380),'Out = !rst & clk & Vin & (count == 2)',49)
    phrase(d,(1200,1490),'רצף גבוה ממושך נשאר במצב 11 ואינו חוזר לפולס','A prolonged high stays in 11 and does not repeat the pulse',lg,38)
    return im


def target_pulse(lg):
    """Prompt-only specification: target traces, without implementation clues."""
    im,d=canvas('תרשים התזמון הנדרש','Required timing diagram',lg,1070)
    events=[0,1,2,3,4,5,6,6.25,7,8,9,10]
    x=lambda t:350+t*185
    signals=[('clk',lambda t:int(1<=t<2 or 3<=t<4 or 5<=t<6 or 7<=t<8 or 9<=t<10),PURPLE),
             ('Vin',lambda t:int(1<=t<6.25),GREEN),
             ('Out',lambda t:int(5<=t<6),'#ae5371')]
    for idx,(name,fn,color)in enumerate(signals):
        y=350+idx*235
        label(d,(160,y-35),name,44)
        old=fn(0)
        points=[(x(0),y-old*100)]
        for t in events[1:]:
            points.append((x(t),y-old*100))
            old=fn(t)
            points.append((x(t),y-old*100))
        d.line(points,fill=color,width=7)
    phrase(d,(1200,970),'לקלט חל חוזה התזמון המפורט בשאלה','The input follows the timing contract stated in the question',lg,38)
    return im


def storage(lg):
    im,d=canvas('שערים עם משוב יוצרים זיכרון; לא לוגיקה צירופית בלבד','Feedback gates create storage; this is not memoryless logic',lg,1800)
    box(d,(150,260,890,500),['a = !rst & Vin','D0 = a & (c1 | !c0)','D1 = a & (c1 | c0)'])
    for i in range(2):
        y=320+i*400
        box(d,(1100,y-60,1510,y+100),[f'MASTER D{i}','EN = clk'])
        box(d,(1780,y-60,2190,y+100),[f'SLAVE Q{i}','EN = !clk'])
        wire(d,[(890,350+i*70),(990,350+i*70),(990,y+20),(1100,y+20)],PURPLE,4)
        wire(d,[(1510,y+20),(1780,y+20)],GREEN,5)
        label(d,(2260,y-30),f'c{i}',38)
        wire(d,[(2190,y+20),(2310,y+20)],GREEN,4)
    phrase(d,(1200,900),'כל תיבה היא נועל משערים; החיבור דוגם בחזית יורדת','Each box is a NAND latch; the pair samples on a falling edge',lg,38)
    # Explicit cross-coupled NAND latch inset.
    box(d,(420,1050,900,1170),['Sbar = NAND(D,EN)'])
    box(d,(420,1390,900,1510),['Rbar = NAND(!D,EN)'])
    box(d,(1260,1050,1900,1170),['Q = NAND(Sbar,Qbar)'])
    box(d,(1260,1390,1900,1510),['Qbar = NAND(Rbar,Q)'])
    wire(d,[(900,1110),(1260,1110)],PURPLE,4)
    wire(d,[(900,1450),(1260,1450)],PURPLE,4)
    wire(d,[(1900,1110),(2040,1110),(2040,1300),(1140,1300),(1140,1485),(1260,1485)],GREEN,4)
    wire(d,[(1900,1450),(2190,1450),(2190,1230),(1050,1230),(1050,1140),(1260,1140)],PURPLE,4)
    label(d,(2110,1050),'Q',36);label(d,(2250,1510),'Qbar',36)
    phrase(d,(1200,1640),'משוב הוא מצב; אתחול ותזמון חייבים להיות מוגדרים','Feedback is state; initialization and timing must be defined',lg,38)
    phrase(d,(1200,1735),'הדגם האידאלי אינו הבטחת תזמון פיזית','The ideal model is not physical timing signoff',lg,36)
    return im


def room(lg):
    im,d=canvas('די בהפרש כדי לבחור צבע, עם גבול תפוסה ידוע','A bounded difference is sufficient to choose the color',lg,1450)
    box(d,(100,300,650,1060),['event[3:0]','1000: -1','0100: +1','0010: +1','0001: -1','0000: hold'])
    box(d,(900,480,1440,860),['signed register d','d_next = d + delta','rst => d = 0'])
    wire(d,[(650,680),(900,680)],PURPLE,5)
    for y,txt in [(400,'RED = (d > 0)'),(700,'GREEN = (d == 0)'),(1000,'BLUE = (d < 0)')]:
        box(d,(1730,y-70,2290,y+90),[txt])
        wire(d,[(1440,680),(1580,680),(1580,y),(1730,y)],GREEN,4)
    dot(d,1580,680)
    label(d,(1200,1170),'d = men - women     -M <= d <= M',46)
    label(d,(1200,1280),'W = 1 + ceil(log2(M + 1))',47)
    phrase(d,(1200,1380),'קידוד האירועים והקיבולת הם הבהרות; קלטים תקינים מובטחים','Event coding and capacity are added; legal histories are promised',lg,35)
    return im


def ha3(lg):
    im,d=canvas('ספירת שלושה ביטים עם שלושה מחברים למחצה בלבד','Three input bits counted with three half adders only',lg,1300)
    box(d,(350,300,750,600),['HA1','a,b -> s,c1'])
    box(d,(1050,300,1450,600),['HA2','s,c -> y0,c2'])
    box(d,(1550,800,1990,1100),['HA3','c1,c2 -> y1,0'])
    label(d,(150,350),'a,b',40);wire(d,[(210,400),(350,400)],PURPLE,4)
    wire(d,[(750,400),(1050,400)],GREEN,5);label(d,(900,330),'s: weight 1',34)
    label(d,(900,540),'c',40);wire(d,[(950,550),(1050,550)],PURPLE,4)
    wire(d,[(750,540),(850,540),(850,880),(1550,880)],PURPLE,4);label(d,(1160,810),'c1: weight 2',37)
    wire(d,[(1450,550),(1510,550),(1510,1010),(1550,1010)],GREEN,4);label(d,(1680,700),'c2: weight 2',37)
    wire(d,[(1450,400),(2260,400)],GREEN,5);label(d,(2240,330),'y0',42)
    wire(d,[(1990,880),(2260,880)],GREEN,5);label(d,(2240,810),'y1',42)
    label(d,(2180,1030),'carry = 0',38)
    phrase(d,(1200,1200),'שני הנשאים אינם פעילים יחד; הפלט בטווח אפס עד שלוש','c1 and c2 cannot both be 1; output y1y0 ranges 0..3',lg,40)
    return im


def squares(lg):
    im,d=canvas('עדכון ריבוע והפרש אי־זוגי במקביל','Update the square and odd difference simultaneously',lg,1350)
    box(d,(400,300,950,570),['register S[n-1:0]','reset = 0'])
    box(d,(400,850,950,1120),['register D[n-1:0]','reset = 1'])
    box(d,(1450,300,2050,570),['ADD: S + D','truncate to n bits'])
    box(d,(1450,850,2050,1120),['ADD: D + 2','truncate to n bits'])
    wire(d,[(950,410),(1450,410)],PURPLE,5)
    wire(d,[(950,965),(1130,965),(1130,510),(1450,510)],GREEN,5);dot(d,1130,965)
    wire(d,[(1130,965),(1450,965)],GREEN,4)
    wire(d,[(2050,410),(2230,410),(2230,190),(260,190),(260,410),(400,410)],PURPLE,4)
    wire(d,[(2050,965),(2230,965),(2230,1200),(260,1200),(260,965),(400,965)],GREEN,4)
    phrase(d,(650,700),'עדכון בו־זמני','Simultaneous updates',lg,38)
    label(d,(1200,1290),'n=4: 0, 1, 4, 9, 0, 9, 4, 1, ... (mod16)',47)
    return im


def loaded(lg):
    im,d=canvas('מונה עם טעינה: שומרים את הקופסה המקורית','Loaded counter: retain the supplied low-bit box',lg,1650)
    box(d,(350,300,1000,750),['SUPPLIED BOX','a[3:0], load, clk','q_low[3:0]'])
    wire(d,[(1000,510),(2220,510)],PURPLE,5);label(d,(2240,440),'q[3:0]',40)
    box(d,(1120,750,1510,950),['AND4','carry = &old_low'])
    wire(d,[(1060,510),(1060,850),(1120,850)],PURPLE,4);dot(d,1060,510)
    box(d,(1570,900,1900,1130),['XOR','h ^ carry'])
    wire(d,[(1510,850),(1730,850),(1730,900)],PURPLE,4)
    box(d,(1570,1230,2050,1410),['DFF h = q4','same clk'])
    box(d,(2100,880,2370,1140),['MUX','select=load'])
    wire(d,[(1900,1015),(2100,1015)],PURPLE,4)
    label(d,(2040,970),'0',32);label(d,(2320,820),'1',32)
    wire(d,[(2240,1140),(2240,1190),(1810,1190),(1810,1230)],PURPLE,5)
    wire(d,[(2050,1320),(2360,1320)],GREEN,5);label(d,(2290,1260),'q4',42)
    wire(d,[(2070,1320),(2070,1460),(1390,1460),(1390,1040),(1570,1040)],GREEN,4)
    dot(d,2070,1320)
    label(d,(2260,750),'a4',42);wire(d,[(2260,780),(2260,880)],GREEN,4)
    phrase(d,(1200,175),'טעינה קודמת לספירה; כל רכיבי המצב חולקים חזית עולה','Load precedes count; all storage shares the rising edge',lg,35)
    phrase(d,(1200,1570),'טעינת אפס מגדירה התחלה; אין איפוס מובנה במקור','Load 00000 to initialize; no reset was supplied',lg,37)
    return im


if __name__=='__main__':
    for number,stem,fn in [(254,'selective-swap',swap),(255,'target-waveform',target_pulse),
                           (255,'phase-waveform',pulse),(255,'nand-storage',storage),
                           (256,'difference-lights',room),(1,'three-ha-batch1103',ha3),
                           (140,'modular-squares-batch1103',squares),(152,'loaded-extension-batch1103',loaded)]:
        for lg in ('he','en'):
            path=OUT/f'prep-{number:03d}-{stem}-{lg}.png'
            fn(lg).save(path)
            print(path.name)
