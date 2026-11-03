"""Original clean concept diagrams for PREP-248..253, not source reproductions."""
from pathlib import Path
from PIL import Image, ImageDraw
from draw_prep_016_064 import phrase, text, wire

OUT = Path(__file__).resolve().parents[1]/'diagrams'
INK, BLUE, GREEN, PURPLE = '#23334b', '#2a62a0', '#257b67', '#7854a2'


def canvas(he, en, lang):
    im = Image.new('RGB',(2400,1400),'white')
    d = ImageDraw.Draw(im)
    phrase(d,(1200,90),he,en,lang,55,bold=True,color=INK)
    return im,d


def panel(d,rect,color=BLUE):
    d.rounded_rectangle(rect,radius=22,fill='#f5f8fd',outline=color,width=6)


def height(lang):
    im,d=canvas('מודל זמן נפילה ולא קריאה חשמלית','A fall-time model, not an electrical reading',lang)
    d.rectangle((220,300,650,1080),outline=INK,width=7)
    for row in range(5):
        for col in range(2):
            d.rectangle((275+col*180,365+row*130,355+col*180,425+row*130),outline=BLUE,width=4)
    d.line((110,1080,1070,1080),fill=INK,width=7)
    wire(d,[(850,350),(850,1000)],BLUE,width=7)
    text(d,(950,660),'h',70,bold=True,color=BLUE)
    text(d,(850,275),'t = 0',46)
    text(d,(850,1150),'t = T',46)
    panel(d,(1160,300,2260,1060))
    text(d,(1710,440),'v(0) = 0',56,color=BLUE,bold=True)
    text(d,(1710,585),'h = g * T^2 / 2',59,color=PURPLE,bold=True)
    text(d,(1710,735),'T = 2 s, g = 9.81 m/s^2',43)
    text(d,(1710,880),'h = 19.62 m',62,color=GREEN,bold=True)
    phrase(d,(1710,990),'דוגמה מספרית ולא מדידת בניין','Numerical example, not a building measurement',lang,32)
    phrase(d,(1200,1285),'ניסוי מחשבתי אידאלי בלבד עם זמן ותנאי התחלה מוגדרים','Ideal thought experiment only, with defined timing and initial conditions',lang,38)
    return im


def decibels(lang):
    im,d=canvas('מכפלת יחסים הופכת לסכום לוגריתמי','Multiplying ratios becomes adding logarithmic gains',lang)
    for x,title,ratio,db,color in [(130,'Stage A','P1/P0 = 10','+10 dB',BLUE),(920,'Stage B','P2/P1 = 0.01','-20 dB',PURPLE)]:
        panel(d,(x,310,x+650,900),color)
        phrase(d,(x+325,425),'שלב ראשון' if title=='Stage A' else 'שלב שני',title,lang,58,bold=True,color=color)
        text(d,(x+325,590),ratio,48,bold=True)
        text(d,(x+325,760),db,68,bold=True,color=color)
    wire(d,[(780,610),(920,610)],INK,width=7)
    wire(d,[(1570,610),(1710,610)],INK,width=7)
    panel(d,(1710,310,2290,900),GREEN)
    phrase(d,(2000,425),'כולל','Total',lang,58,bold=True,color=GREEN)
    text(d,(2000,590),'P2/P0 = 0.1',43,bold=True)
    text(d,(2000,760),'-10 dB',68,bold=True,color=GREEN)
    text(d,(1200,1050),'10 log10(Pout / Pin)',61,bold=True,color=BLUE)
    text(d,(1200,1170),'0 dBm = 1 mW',52,bold=True,color=PURPLE)
    phrase(d,(1200,1300),'דציבל הוא יחס והייחוס חייב להיות מפורש','Decibels express a ratio; the reference must be explicit',lang,42)
    return im


def hats(lang):
    im,d=canvas('כל נכנס בוחר את הגבול בלי לראות את כובעו','Each newcomer chooses the boundary without seeing their own hat',lang)
    phrase(d,(1200,270),'לפני הכניסה: אדומים משמאל וכחולים מימין','Before entry: red hats on the left, blue hats on the right',lang,40)
    for x,label,color in [(220,'R0','#b04c49'),(610,'R1','#b04c49'),(1390,'B0',BLUE),(1780,'B1',BLUE)]:
        panel(d,(x,370,x+300,610),color)
        text(d,(x+150,490),label,63,bold=True,color=color)
    d.rounded_rectangle((1000,350,1300,630),radius=20,outline=PURPLE,width=6)
    text(d,(1150,490),'?',85,bold=True,color=PURPLE)
    phrase(d,(1150,720),'מקום הנכנס','Newcomer gap',lang,42,bold=True,color=PURPLE)
    for y,value,he,en,color in [(890,'R R R B B','אם כובעו אדום','If their hat is red','#b04c49'),(1100,'R R B B B','אם כובעו כחול','If their hat is blue',BLUE)]:
        phrase(d,(650,y),he,en,lang,39,color=color)
        text(d,(1630,y),value,67,bold=True,color=color)
    phrase(d,(1200,1305),'בשני המקרים נשמר רצף של שני גושי צבע והקודמים אינם זזים','Both outcomes preserve the two color blocks; earlier people never move',lang,34)
    return im


def weights(lang):
    im,d=canvas('שש משקולות וסכומי תת קבוצות','Six weights and their subset sums',lang)
    for i,value in enumerate([1,2,4,8,16,32]):
        x=100+i*385
        panel(d,(x,320,x+290,650),GREEN if value in (1,16) else BLUE)
        text(d,(x+145,485),str(value),77,bold=True,color=GREEN if value in (1,16) else BLUE)
    text(d,(1200,820),'17 = 16 + 1',65,bold=True,color=GREEN)
    text(d,(1200,1000),'2^5 = 32 < 41 <= 64 = 2^6',58,bold=True,color=PURPLE)
    phrase(d,(1200,1160),'אפס ועוד ארבעים משקלים שונים דורשים לפחות ארבעים ואחד מצבים','Zero plus forty distinct targets require at least forty-one outcomes',lang,35)
    phrase(d,(1200,1300),'כל משקולת נבחרת פעם אחת לכל היותר ורק חיבור מותר','Each weight is used at most once; only addition is allowed',lang,38)
    return im


def copying(lang):
    im,d=canvas('בניית עותק חדש עם בעלות עצמאית','Constructing a new copy with independent ownership',lang)
    for y,name,values,color in [(330,'a','[ 1 | 2 | 3 ]',BLUE),(800,'b(a)','[ 9 | 2 | 3 ]',GREEN)]:
        panel(d,(180,y,800,y+290),color)
        text(d,(490,y+145),name,67,bold=True,color=color)
        wire(d,[(800,y+145),(1260,y+145)],color,width=7)
        panel(d,(1260,y,2230,y+290),color)
        text(d,(1745,y+145),values,66,bold=True,color=color)
    phrase(d,(1200,700),'שינוי בעותק אינו משנה את אובייקט המקור','Changing the copy does not change the original',lang,43,bold=True,color=PURPLE)
    text(d,(1200,1220),'T b(a)  !=  b = a',56,bold=True,color=PURPLE)
    phrase(d,(1200,1320),'אתחול אובייקט חדש שונה מהשמה לאובייקט שכבר קיים','Initializing a new object differs from assigning an existing one',lang,38)
    return im


def spike(lang):
    im,d=canvas('מוכנות לעומס מתוכנן לאורך כל מחזור האירוע','Planned-spike readiness across the event lifecycle',lang)
    rows=[('לפני','Before','תחזית ובדיקת קיבולת','Forecast and measure capacity','SLO + headroom',BLUE),
          ('במהלך','During','הגבלת כניסה ותורים חסומים','Admission limits and bounded queues','metrics + rollback',PURPLE),
          ('אחרי','After','ריקון תורים ותחקיר','Drain backlog and review','reconcile + learn',GREEN)]
    for i,(he,en,bodyhe,bodyen,code,color) in enumerate(rows):
        x=80+i*790
        panel(d,(x,320,x+660,1030),color)
        phrase(d,(x+330,440),he,en,lang,59,bold=True,color=color)
        phrase(d,(x+330,650),bodyhe,bodyen,lang,33,bold=True)
        phrase(d,(x+330,845),['יעדים ומרווח קיבולת','ניטור ותוכנית נסיגה','התאמה ולמידה'][i],code,lang,36,color=color,bold=True)
        if i<2: wire(d,[(x+660,680),(x+790,680)],INK,width=6)
    phrase(d,(1200,1175),'תור בלתי מוגבל אינו קיבולת בלתי מוגבלת','An unlimited queue is not unlimited capacity',lang,49,bold=True,color=PURPLE)
    phrase(d,(1200,1300),'המודל המספרי ממחיש מדיניות ואינו בדיקת עומס של האתר','The numeric model illustrates a policy; it does not load-test this site',lang,36)
    return im


if __name__=='__main__':
    for number,producer in [(248,height),(249,decibels),(250,hats),(251,weights),(252,copying),(253,spike)]:
        for lang in ('he','en'):
            producer(lang).save(OUT/f'prep-{number}-concepts-{lang}.png')
    print('12 bilingual original concept diagrams saved')
