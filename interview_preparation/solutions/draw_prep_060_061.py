"""Editable deterministic bilingual diagrams for PREP-060 and PREP-061."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BLUE,GREEN,ORANGE,INK,MUTED = '#365da5','#277969','#af671b','#17243c','#65758b'


class Figure:
    def __init__(self, height):
        self.im=Image.new('RGB',(3200,height),'#fcfdff')
        self.d=ImageDraw.Draw(self.im)

    def text(self,point,value,size=46,color=INK,bold=False,he=False):
        font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',size)
        self.d.text(point,value[::-1] if he else value,font=font,fill=color,anchor='mm')

    def translated(self,point,lang,he,en,size=46,color=INK,bold=False):
        self.text(point,he if lang=='he' else en,size,color,bold,lang=='he')

    def box(self,xy,color=BLUE,fill='#eef3ff'):
        self.d.rounded_rectangle(xy,radius=26,fill=fill,outline=color,width=6)

    def arrow(self,points,color=BLUE,width=7):
        self.d.line(points,fill=color,width=width,joint='curve')
        a,b=points[-2:]
        angle=math.atan2(b[1]-a[1],b[0]-a[0])
        self.d.polygon([b]+[(b[0]-30*math.cos(angle+v),b[1]-30*math.sin(angle+v)) for v in (-.45,.45)],fill=color)

    def node(self,center,text,color=BLUE,fill='#eef3ff',w=220,h=140):
        x,y=center
        self.box((x-w/2,y-h/2,x+w/2,y+h/2),color,fill)
        self.text(center,text,53,color,bold=True)

    def save(self,stem,lang):
        OUT.mkdir(parents=True,exist_ok=True)
        self.im.save(OUT/f'{stem}-{lang}.png')


def game(lang):
    f=Figure(1900)
    f.text((1600,100),'PREP-060',72,bold=True)
    f.translated((1600,220),lang,'מתחילים באחד ומשלימים כל זוג מהלכים לארבע','Start with one; make each pair of moves sum to four',56,bold=True)
    f.translated((1600,365),lang,'הסכומים בסיום התורים שלנו','Totals at the end of OUR turns',49,color=GREEN)
    f.node((160,660),'0',w=170,h=160)
    for i,total in enumerate((1,5,9,13,17,21)):
        x=560+i*480
        f.node((x,660),str(total),GREEN,'#e9f7f0',w=210,h=180)
        if i:
            f.arrow([(x-480+105,660),(x-105,660)],GREEN)
            f.text((x-240,575),'+4',48,GREEN,bold=True)
    f.arrow([(245,660),(455,660)],BLUE)
    f.text((350,575),'+1',48,BLUE,bold=True)
    f.translated((1600,930),lang,'תגובתנו לכל בחירה של היריב','Our reply to each possible opponent move',50,bold=True)
    f.translated((1050,1060),lang,'היריב מוסיף','Opponent adds',43,color=BLUE)
    f.translated((2140,1060),lang,'אנחנו מוסיפים','We add',43,color=GREEN)
    for row,opponent in enumerate((1,2,3)):
        y=1190+row*170
        f.node((1050,y),str(opponent),w=220,h=120)
        f.arrow([(1160,y),(2030,y)],GREEN)
        f.text((1600,y-48),f'{opponent} + {4-opponent} = 4',40,color=MUTED)
        f.node((2140,y),str(4-opponent),GREEN,'#e9f7f0',w=220,h=120)
    f.translated((1600,1740),lang,'מאחרי שבע עשרה היריב מגיע רק עד עשרים ואנחנו מסיימים בעשרים ואחת','After seventeen, the opponent reaches at most twenty; we finish at twenty-one',42)
    f.save('prep-060-game-twenty-one-strategy',lang)


def fibonacci(lang):
    f=Figure(2350)
    f.text((1600,90),'PREP-061',72,bold=True)
    f.translated((1600,210),lang,'רקורסיה נאיבית לעומת שמירת תוצאות','Naive recursion versus memoized results',57,bold=True)
    f.translated((1600,325),lang,'למעלה אותו חישוב מתבצע שוב בענפים שונים','Above: the same subproblem is recalculated in different branches',44)
    edges=[((1600,490),(1000,700)),((1600,490),(2200,700)),((1000,700),(700,910)),((1000,700),(1300,910)),
           ((2200,700),(1900,910)),((2200,700),(2500,910)),((700,910),(500,1120)),((700,910),(900,1120))]
    for start,end in edges:
        f.arrow([(start[0],start[1]+65),(end[0],end[1]-65)])
    for xy,label in [((1600,490),'F(4)'),((1000,700),'F(3)'),((2200,700),'F(2)'),((700,910),'F(2)'),((1300,910),'F(1)'),
                     ((1900,910),'F(1)'),((2500,910),'F(0)'),((500,1120),'F(1)'),((900,1120),'F(0)')]:
        repeated=label=='F(2)'
        f.node(xy,label,ORANGE if repeated else BLUE,'#fff5e8' if repeated else '#eef3ff',w=230,h=130)
    f.translated((1600,1320),lang,'למטה כל תוצאה מחושבת פעם אחת ואז נקראת מהזיכרון','Below: each result is computed once, then retrieved from cache',45,color=GREEN,bold=True)
    f.arrow([(1600,1515),(1000,1665)],GREEN)
    f.arrow([(1600,1515),(2200,1665)],GREEN)
    f.arrow([(1120,1730),(2080,1730)],GREEN)
    f.arrow([(1000,1795),(1400,1965)],GREEN)
    f.arrow([(2200,1795),(1400,1965)],GREEN)
    f.arrow([(2200,1795),(2700,1965)],GREEN)
    for xy,label in [((1600,1450),'F(4)'),((1000,1730),'F(3)'),((2200,1730),'F(2)'),((1400,2030),'F(1)'),((2700,2030),'F(0)')]:
        f.node(xy,label,GREEN,'#e9f7f0',w=240,h=130)
    f.text((1600,2240),'F(0)=0     F(1)=1     F(n)=F(n-1)+F(n-2)',47,color=MUTED)
    f.save('prep-061-recursion-memoization',lang)


if __name__=='__main__':
    for lang in ('he','en'):
        game(lang)
        fibonacci(lang)
    print('Created four localized diagrams.')
