"""Original bilingual explanatory figures for the November 7 software shard."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parents[1]/'diagrams'


def canvas(he,en,lang):
    im=Image.new('RGB',(2800,1500),'white');d=ImageDraw.Draw(im)
    phrase(d,(1400,110),he,en,lang,58,bold=True)
    return im,d


def save(im,n,lang):
    im.save(OUT/f'prep-{n:03d}-software-batch1107-{lang}.png')


def flow(n,lang,he,en,labels,footer):
    im,d=canvas(he,en,lang)
    for i,(label,sub) in enumerate(labels):
        x=150+i*880
        box(d,(x,450,x+740,920),GREEN if i==2 else BLUE)
        phrase(d,(x+370,575),label[0],label[1],lang,46,bold=True)
        text(d,(x+370,735),sub,46,color=GREEN if i==2 else BLUE)
        if i<2: wire(d,[(x+740,685),(x+880,685)])
    phrase(d,(1400,1200),footer[0],footer[1],lang,47)
    save(im,n,lang)


def prime(lang):
    im,d=canvas('מחפש מחלק עד השורש ושומר את הקלט','Capture the input and search divisors through its square root',lang)
    for i,(lab,sub) in enumerate([(('קבלת עסקה','Accept'),'n -> number; d = 2'),
                                (('בדיקת מחלק','Test'),'d <= number / d'),
                                (('תוצאה תקפה','Complete'),'busy = 0; valid = 1')]):
        x=150+i*880;box(d,(x,400,x+740,800),GREEN if i==2 else BLUE)
        phrase(d,(x+370,500),*lab,lang,46,bold=True);text(d,(x+370,665),sub,41)
        if i<2: wire(d,[(x+740,600),(x+880,600)])
    text(d,(1400,990),'number % d = 0  ->  composite',56,color=ORANGE)
    text(d,(1400,1100),'d > number / d  ->  prime',56,color=GREEN)
    phrase(d,(1400,1320),'אפס ואחד נפסלים לפני בדיקת מחלקים','Zero and one are rejected before testing divisors',lang,48)
    save(im,265,lang)


def status(lang):
    im,d=canvas('מפרידים פלט מוצר ממצב התהליך','Keep product output separate from process outcome',lang)
    box(d,(220,500,970,1030),BLUE)
    phrase(d,(595,660),'תהליך הילד','Child process',lang,54,bold=True)
    text(d,(595,840),'script.py',57)
    for i,(label,sub,color) in enumerate([(('תוצר','Product'),'stdout',BLUE),(('אבחון','Diagnostics'),'stderr',ORANGE),(('מצב סיום','Outcome'),'returncode',GREEN)]):
        y=300+i*360
        box(d,(1550,y,2500,y+250),color)
        wire(d,[(970,620+i*120),(1250,620+i*120),(1250,y+125),(1550,y+125)],color)
        phrase(d,(1860,y+125),*label,lang,48,bold=True)
        text(d,(2270,y+125),sub,42,color=color)
    phrase(d,(1400,1360),'קוד אפס לבדו אינו הוכחה שהמחרוזת נכונה','Exit zero alone does not prove that the output is correct',lang,48)
    save(im,266,lang)


def joke(lang):
    flow(267,lang,'שלוש שכבות עד למחרוזת שרוצים','Three checks before printing the desired string',[
        (('הצלחת בקשה','HTTP success'),'2xx + timeout'),
        (('גוף תקין','JSON body'),'bounded bytes -> object'),
        (('בדיחה בלבד','Joke only'),"value: str -> stdout")],
        ('שגיאה עוברת לערוץ האבחון ולקוד סיום','Failures use stderr and a nonzero exit status'))


def chat(lang):
    im,d=canvas('מזהה בקשה מונע שכפול ומספר אירוע מאפשר שחזור','Request identity prevents duplicates; event sequence supports replay',lang)
    for i,(title,sub) in enumerate([(('לקוח ראשון','Client A'),'request_id = q7'),(('שרת ויומן','Server + log'),'q7 -> sequence 21'),(('לקוח שחזר','Client B resumes'),'last_seen = 20')]):
        x=130+i*900;box(d,(x,400,x+750,860),GREEN if i==1 else BLUE)
        phrase(d,(x+375,515),*title,lang,50,bold=True);text(d,(x+375,700),sub,42)
        if i<2: wire(d,[(x+750,620),(x+900,620)])
    text(d,(1400,1060),'retry q7 -> ACK 21; no event 22',53,color=ORANGE)
    text(d,(1400,1180),'resume after 20 -> event 21',53,color=GREEN)
    phrase(d,(1400,1380),'מודל יישומי בלבד ללא מימוש רשת','Application model only; no network implementation',lang,47)
    save(im,268,lang)


def speed(lang):
    im,d=canvas('כל התשובות מוכנות מראש בטבלה','Every answer is precomputed in a small table',lang)
    for row,values in enumerate([list(range(11)),list(range(1,11))+[10],[0]+list(range(10))]):
        yy=380+row*250
        text(d,(200,yy+80),['v','gas','brake'][row],50,bold=True)
        for col,value in enumerate(values):
            xx=410+col*200
            box(d,(xx,yy,xx+170,yy+160),GREEN if (row==1 and col==10)or(row==2 and col==0) else BLUE)
            text(d,(xx+85,yy+80),str(value),49)
    phrase(d,(1400,1290),'אפס ועשר נשארים בגבולות המתאימים','Zero and ten remain saturated at their respective boundaries',lang,47)
    phrase(d,(1400,1420),'ליבת הפונקציה היא גישה אחת לפי אינדקס','The function core performs one indexed lookup',lang,46)
    save(im,269,lang)


def binary(lang):
    im,d=canvas('האזור הלא מסווג מצטמצם בכל צעד','The unknown interval shrinks at every step',lang)
    for x,w,lab,sub,color in [(180,650,('אפסים','Zeros'),'[0, left)',GREEN),(900,1000,('עדיין לא סווג','Unknown'),'[left, right]',ORANGE),(1970,650,('אחדים','Ones'),'(right, n)',BLUE)]:
        box(d,(x,470,x+w,880),color);phrase(d,(x+w/2,590),*lab,lang,52,bold=True);text(d,(x+w/2,735),sub,48)
    text(d,(1400,1060),'a[left] = 0  ->  left++',54,color=GREEN)
    text(d,(1400,1170),'a[left] = 1  ->  swap(left,right); right--',50,color=ORANGE)
    phrase(d,(1400,1380),'החלפות שומרות על מספר האפסים והאחדים','Swaps preserve the counts of zero and one',lang,48)
    save(im,19,lang)


def assembly(lang):
    im,d=canvas('תוצאה גדלה ומקור חוזר לערכו','The result grows while the source is restored',lang)
    states=[(3,2,9,99),(3,2,0,0),(0,1,3,3),(3,1,0,3),(3,0,0,6)]
    labels=[('התחלה','Initial'),('אחרי איפוס','After clear'),('אחרי העברה','After transfer'),('אחרי שחזור','After restore'),('סיום','Complete')]
    for row,(values,label) in enumerate(zip(states,labels)):
        yy=310+row*200
        phrase(d,(380,yy+65),*label,lang,43,bold=True)
        for col,value in enumerate(values):
            xx=800+col*470;box(d,(xx,yy,xx+360,yy+135),GREEN if col==3 else BLUE);text(d,(xx+180,yy+68),str(value),49)
            if row==0: text(d,(xx+180,yy-75),f'R{col+1}',47,bold=True)
    phrase(d,(1400,1400),'קפיצה בודקת רגיסטר מפורש ולא דגל מהפקודה הקודמת','The branch tests a named register, not a previous arithmetic flag',lang,43)
    save(im,35,lang)


def missing(lang):
    im,d=canvas('מחפשים את האינדקס הראשון שבו מתחילה ההזחה','Find the first index where displacement begins',lang)
    for row,values in enumerate([[0,1,2,3,4,5],[1,2,3,5,6,7],[1,2,3,4,5,6]]):
        yy=340+row*280
        text(d,(250,yy+90),['i','a[i]','i + 1'][row],50,bold=True)
        for col,value in enumerate(values):
            xx=550+col*350;box(d,(xx,yy,xx+290,yy+180),ORANGE if col>=3 and row==1 else BLUE);text(d,(xx+145,yy+90),str(value),62)
    text(d,(1400,1240),'first mismatch: i = 3; missing = 4',55,color=GREEN)
    phrase(d,(1400,1400),'לפני הדילוג שוויון ואחריו הפרש של אחת','Before the omission equality holds; afterward the difference is one',lang,44)
    save(im,41,lang)


def matrix(lang):
    im,d=canvas('משווים תא סיום לתא ההתחלתי','Compare the final cell with the starting cell',lang)
    for r in range(4):
        for c in range(4):
            xx=350+c*220;yy=350+r*220;box(d,(xx,yy,xx+215,yy+215),GREEN if(r,c)==(1,1)else BLUE)
    wire(d,[(680,680),(900,680),(900,900),(680,900),(680,680)],GREEN,12)
    text(d,(2000,530),'M R M R M R M',55,color=GREEN)
    text(d,(2000,760),'start = (1,1)',55)
    text(d,(2000,920),'finish = (1,1)',55)
    phrase(d,(1400,1320),'אין צורך לשמור את כל המסלול','The entire trail need not be stored',lang,50)
    phrase(d,(1400,1430),'יציאה מהלוח נפסלת בחוזה שנבחר','Leaving the board is rejected by the chosen contract',lang,47)
    save(im,182,lang)


if __name__=='__main__':
    for language in ('he','en'):
        for function in (prime,status,joke,chat,speed,binary,assembly,missing,matrix):
            function(language)
    print('Rendered 18 bilingual software diagrams.')
