"""Independent clean bilingual diagrams for software principles in batch110."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parents[1]/'diagrams'

def canvas(ident,he,en,lang):
    im=Image.new('RGB',(2500,1450),'white');d=ImageDraw.Draw(im)
    phrase(d,(1250,95),he,en,lang,58,bold=True)
    text(d,(1250,195),ident,38,color=BLUE)
    return im,d

def root(lang):
    im,d=canvas('PREP-188','שתי הנקודות הקרובות ביותר','Closest pair across the dividing line',lang)
    d.line([(1250,320),(1250,1140)],fill=ORANGE,width=7)
    d.rectangle((980,300,1520,1160),outline='#c8d8ed',width=4)
    pts=[(430,800),(650,480),(920,1050),(1170,650),(1330,680),(1640,440),(1870,980),(2150,590)]
    for i,(x,y) in enumerate(pts):
        d.ellipse((x-17,y-17,x+17,y+17),fill=BLUE);text(d,(x,y-50),f'p{i}',34)
    wire(d,[pts[3],pts[4]],GREEN,9,False)
    text(d,(1250,1220),'dx^2 < best^2    |    dy^2 < best^2',43,color=GREEN)
    phrase(d,(1250,1330),'שומרים סדר לפי הציר האנכי בכל מיזוג','Return each half in y order; merge once per level',lang,43)
    im.save(OUT/f'prep-188-root-batch110-{lang}.png')
    im,d=canvas('PREP-022','בחירה אקראית של פיקסלים ללא חזרה','Random pixels without replacement',lang)
    for row in range(2):
        for col in range(3):
            x=250+col*220;y=400+row*220
            d.rectangle((x,y,x+180,y+180),outline=BLUE,width=5)
            text(d,(x+90,y+90),f'{row},{col}',40)
    wire(d,[(950,620),(1230,620)],GREEN)
    box(d,(1300,400,2270,850))
    text(d,(1785,480),'id = row*N + column',44,bold=True)
    text(d,(1785,610),'[0, 1, 2, 3, 4, 5]',46)
    phrase(d,(1785,740),'בחירה והסרה בהחלפת הקצה','draw j; swap last; shrink',lang,39,color=GREEN)
    phrase(d,(1250,1070),'כל תא שנותר נמצא פעם אחת במאגר','Every remaining pixel has exactly one active id',lang,48)
    text(d,(1250,1240),'P(order) = 1/(M*N)!',48,color=GREEN)
    im.save(OUT/f'prep-022-root-batch110-{lang}.png')
    im,d=canvas('PREP-125','כפל באמצעות העברה ושחזור','Multiply by transfer and restore',lang)
    for x,label,he,en in [(180,'R0','הקלט','input a'),(950,'R3','מונה העברות','transfer count'),(1720,'R2','המכפלה','product')]:
        box(d,(x,450,x+580,750));text(d,(x+290,520),label,56,bold=True);phrase(d,(x+290,650),he,en,lang,39)
    wire(d,[(760,520),(950,520)],BLUE);text(d,(855,435),'+1',39)
    wire(d,[(1240,750),(1240,900),(470,900),(470,750)],GREEN)
    wire(d,[(760,680),(840,680),(840,1020),(2010,1020),(2010,750)],BLUE)
    d.line([(815,900),(865,900)],fill='white',width=14)
    d.line([(840,870),(840,930)],fill=BLUE,width=8)
    text(d,(1250,1120),'R0=a; R1=b-k; R2=k*a; R3=0; R7=1',43)
    phrase(d,(1250,1290),'כל קפיצה בודקת תוצאה חשבונית טרייה','Every branch follows a fresh arithmetic result',lang,44)
    im.save(OUT/f'prep-125-root-batch110-{lang}.png')
    im,d=canvas('PREP-149','סכימת אירועים בלוג שימוש במעבד','Weighted CPU events and the running load',lang)
    for y,start,end,label in [(410,350,1250,'25%'),(620,800,2050,'40%')]:
        d.line([(start,y),(end,y)],fill=BLUE,width=28);text(d,((start+end)//2,y-65),label,45)
    text(d,(350,770),'09:00',38);text(d,(800,770),'09:30',38);text(d,(1250,770),'10:00',38);text(d,(2050,770),'11:00',38)
    d.line([(220,1190),(350,1190),(350,1050),(800,1050),(800,850),(1250,850),(1250,980),(2050,980),(2050,1190),(2240,1190)],fill=GREEN,width=9)
    text(d,(1010,920),'65%',48,color=GREEN,bold=True)
    phrase(d,(1250,1330),'מאחדים שינויים באותו זמן לפני מדידת השיא','Aggregate equal timestamps before measuring the peak',lang,44)
    im.save(OUT/f'prep-149-root-batch110-{lang}.png')
    im,d=canvas('PREP-189','הריסה וירטואלית ובעלות על משאב','Virtual destruction and resource ownership',lang)
    for x,y,label in [(180,420,'unique_ptr<Interface>'),(1300,420,'Implementation'),(1300,940,'unique_ptr<int[]>')]:
        box(d,(x,y,x+1020,y+260));text(d,(x+510,y+130),label,44,bold=True)
    wire(d,[(1200,550),(1300,550)],GREEN)
    wire(d,[(1810,680),(1810,940)],GREEN)
    text(d,(690,960),'virtual ~Interface() = default',41,color=GREEN)
    phrase(d,(1250,1320),'ניקוי אוטומטי דורש בעלות תקינה','Automatic cleanup depends on correct ownership',lang,46)
    im.save(OUT/f'prep-189-root-batch110-{lang}.png')
    im,d=canvas('PREP-194','היפוך שרשרת עם מצטבר','Abstract-list reversal with an accumulator',lang)
    phrase(d,(1250,340),'הראש הוא ערך והזנב הוא שרשרת','Head returns a value; Tail returns a list',lang,41)
    text(d,(1250,410),'Head(L)    |    Tail(L)    |    L1 @ L2',40)
    for y,unread,result in [(540,'[a,b,c]','[]'),(720,'[b,c]','[a]'),(900,'[c]','[b,a]'),(1080,'[]','[c,b,a]')]:
        text(d,(650,y),unread,50);text(d,(1780,y),result,50,color=GREEN)
        if y<1080:wire(d,[(1220,y+30),(1220,y+140)],BLUE)
    phrase(d,(1250,1280),'נדרשות בדיקת ריקות ובניית שרשרת יחיד','Requires an empty test and a singleton constructor',lang,43)
    im.save(OUT/f'prep-194-root-batch110-{lang}.png')
    im,d=canvas('PREP-196','מספר קריאות לעומת עומק פעיל','Total calls versus active recursion depth',lang)
    for i in range(4):
        y=350+i*190
        box(d,(260+i*90,y,1110+i*90,y+130));text(d,(685+i*90,y+65),f'S({3-i})',48,bold=True)
    box(d,(1550,500,2250,950))
    text(d,(1900,610),'sum = 0',48);text(d,(1900,740),'n -> n-1',48);phrase(d,(1900,850),'לולאה','loop',lang,48,color=GREEN)
    text(d,(740,1200),'T(n)=O(n); S(n)=O(n)',43)
    text(d,(1900,1200),'T(n)=O(n); S(n)=O(1)',43)
    phrase(d,(1250,1320),'זמן ריצה וזיכרון נוסף במילים','Running time and extra storage in words',lang,42)
    im.save(OUT/f'prep-196-root-batch110-{lang}.png')

if __name__=='__main__':
    for language in ('he','en'):root(language)
