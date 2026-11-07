"""Original bilingual teaching diagrams, independent of source screenshots."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
INK, BLUE, GREEN, RED = '#23334b', '#2a62a0', '#257b67', '#b24747'


def frame(he, en, lang):
    image = Image.new('RGB', (2400, 1500), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 95), he, en, lang, 54, bold=True)
    return image, draw


def card(d, rect, label, color=BLUE, size=45):
    d.rounded_rectangle(rect, radius=24, fill='#f5f8fd', outline=color, width=5)
    text(d, ((rect[0]+rect[2])//2,(rect[1]+rect[3])//2),label,size,bold=True,color=color)


def router(lang):
    image,d=frame('מחלקים תקציב ושומרים על כל הכניסות', 'Allocate budgets while exercising every selected port',lang)
    phrase(d,(1200,210),'הגרלה חוקית אינה מחייבת לולאת ניסיונות',
           'Construct feasible values without an unbounded retry loop',lang,40)
    cards=[((130,350,740,550),'1 <= P <= min(16,MAX/2)'),
           ((900,350,1510,550),'2P <= B <= MAX'),
           ((1670,350,2280,550),'P distinct ports'),
           ((1670,820,2280,1020),'budget[i] >= 2'),
           ((900,820,1510,1020),'2 <= packet <= 65536'),
           ((130,820,740,1020),'send_data(port,size)')]
    for rect,label in cards:card(d,rect,label,size=35)
    for a,b in [((740,450),(900,450)),((1510,450),(1670,450)),
                ((1975,550),(1975,820)),((1670,920),(1510,920)),((900,920),(740,920))]:
        wire(d,[a,b],width=6)
    phrase(d,(1200,710),'לעולם לא משאירים בית בודד', 'NEVER leave remaining = 1',lang,44,bold=True,color=RED)
    text(d,(1200,1165),'sum(packet_size) = B       |       seen_ports = selected_ports',40,bold=True,color=GREEN)
    phrase(d,(1200,1320),'בדיקה עצמאית של כמות וכיסוי', 'Independent conservation and coverage checks',lang,41,bold=True)
    phrase(d,(1200,1410),'ממשק שליחה מדומה אינו בדיקה של נתב אמיתי',
           'A send spy does not validate a physical router',lang,37)
    return image


def counter(lang):
    image,d=frame('אותו מוצא אינו בהכרח אותו מצב', 'Equal outputs do not imply equal states',lang)
    phrase(d,(1200,210),'שני מצבי האחד מובילים לערכים שונים',
           'The two one-output states have different successors',lang,42)
    centers=[(580,480),(1820,480),(1820,1000),(580,1000)]
    for i,((x,y),out) in enumerate(zip(centers,[0,1,2,1])):
        d.ellipse((x-160,y-120,x+160,y+120),fill='#f5f8fd',outline=GREEN if out==1 else BLUE,width=6)
        text(d,(x,y-35),f'S{i}: {i:02b}',43,bold=True)
        text(d,(x,y+42),f'out = {out}',45,color=GREEN if out==1 else BLUE)
    for a,b in [((740,480),(1660,480)),((1820,600),(1820,880)),
                ((1660,1000),(740,1000)),((580,880),(580,600))]:wire(d,[a,b],width=6)
    text(d,(1200,710),'y0 = q0',51,bold=True)
    text(d,(1200,790),'y1 = q1 AND NOT q0',45,bold=True)
    text(d,(1200,1220),'0, 1, 2, 1, 0, 1, 2, 1, ...',52,bold=True,color=GREEN)
    phrase(d,(1200,1370),'ארבעה מצבים מובחנים ולכן שתי סיביות מצב',
           'Four distinguishable states require two state bits',lang,41)
    return image


def gold(lang):
    image,d=frame('שני חיתוכים יוצרים את כל היתרות', 'Two cuts create every required balance',lang)
    phrase(d,(1200,210),'מותר להחליף חתיכות ולקבל עודף',
           'Pieces may be exchanged and returned as change',lang,42)
    x0,y0,width=220,370,280
    for start,units,color in [(0,1,BLUE),(1,2,GREEN),(3,4,'#7854a2')]:
        left=x0+start*width;right=left+units*width
        d.rectangle((left,y0,right,y0+220),fill='#f5f8fd',outline=color,width=6)
        text(d,((left+right)//2,y0+110),str(units),65,bold=True,color=color)
    for split in [1,3]:
        x=x0+split*width
        d.line((x,330,x,640),fill=RED,width=7)
    for i,hold in enumerate(['1','2','1+2','4','1+4','2+4','1+2+4']):
        x=240+i*320
        phrase(d,(x,770),'יום', 'Day',lang,37,bold=True)
        text(d,(x,825),str(i+1),37,bold=True)
        card(d,(x-135,880,x+135,1060),hold,GREEN,size=40)
    phrase(d,(1200,1180),'מספר תת הקבוצות חסום על ידי מספר הבחירות הבינאריות',
           'The ownership subset count bounds the possible balances',lang,37)
    text(d,(1200,1250),'k pieces -> at most 2^k balances',45,bold=True)
    text(d,(1200,1330),'8 balances need k >= 3 pieces -> at least 2 cuts',42,color=GREEN,bold=True)
    phrase(d,(1200,1410),'ללא החזרת עודף נדרש פתרון אחר',
           'Without change, a different payment contract applies',lang,37)
    return image


def room(lang):
    image,d=frame('ארבע תפוסות ושני מצבי נורה', 'Four occupancies, two lamp values',lang)
    phrase(d,(1200,210),'קיבולת שלושה היא הנחת התרגיל שנבחרה',
           'Capacity three is an explicit exercise assumption',lang,42)
    for i,x in enumerate([330,910,1490,2070]):
        d.ellipse((x-130,610,x+130,870),fill='#f5f8fd',outline=BLUE if i==0 else GREEN,width=6)
        text(d,(x,695),f'E{i}',52,bold=True)
        text(d,(x,780),'OFF' if i==0 else 'ON',40,bold=True,color=BLUE if i==0 else GREEN)
    for x in [330,910,1490]:
        wire(d,[(x+105,635),(x+290,470),(x+475,635)],width=6)
        phrase(d,(x+290,405),'כניסה','entry',lang,36,color=GREEN)
        wire(d,[(x+475,845),(x+290,1010),(x+105,845)],width=6,color=BLUE)
        phrase(d,(x+290,1070),'יציאה','exit',lang,36,color=BLUE)
    phrase(d,(1200,1190),'אירוע שגוי או אירוע שנדחה משאירים את המצב',
           'idle / invalid / boundary rejection: HOLD',lang,42,bold=True,color=RED)
    text(d,(1200,1285),'lamp = occupancy != 0',46,bold=True,color=GREEN)
    phrase(d,(1200,1400),'ללא חסם תפוסה אין מכונה סופית מדויקת',
           'Unbounded occupancy has no exact finite entry/exit FSM',lang,39)
    return image


def lag(lang):
    image,d=frame('המספר מתעדכן עכשיו והפלט מתאר קודם',
                     'Update the number now; report the previous prefix',lang)
    phrase(d,(1200,210),'הביט החדש נכנס למקום הגבוה', 'The new bit becomes the most significant bit',lang,42)
    card(d,(800,300,1600,450),'s, seen: PRE-EDGE',BLUE,size=42)
    card(d,(150,570,1050,740),'s_next = 2*(s+b) mod 3',BLUE,size=42)
    card(d,(1350,570,2250,740),'out_next = seen AND (s==0)',GREEN,size=38)
    wire(d,[(1000,450),(600,570)],width=6)
    wire(d,[(1400,450),(1800,570)],width=6)
    phrase(d,(1200,860),'שני העדכונים משתמשים במצב שלפני החזית',
           'Both updates use the PRE-EDGE state',lang,39,bold=True)
    headers=[('חזית','edge'),('ביט','bit'),('ערך הקידומת','prefix N'),('פלט','output')]
    rows=[['1','0','0','0'],['2','1','2','1'],['3','1','6','0'],['4','0','6','1']]
    for col,(he,en) in enumerate(headers):phrase(d,(480+480*col,975),he,en,lang,40,bold=True)
    for r,row in enumerate(rows):
        for col,v in enumerate(row):text(d,(480+480*col,1060+95*r),v,45,color=GREEN if col==3 else INK)
    phrase(d,(1200,1430),'לפני קידומת ראשונה שאינה ריקה המוצא אפס',
           'No previous nonempty prefix: output zero during warmup',lang,39)
    return image


if __name__=='__main__':
    for lang in ('he','en'):
        for number,draw in [(291,router),(292,counter),(298,gold),(301,room),(36,lag)]:
            draw(lang).save(OUT/f'prep-{number:03d}-reasoning-batch1107n30-{lang}.png')
