"""Complete, net-labelled DFF, TFF and adder/register modulo-three schematics."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
INK,BLUE,GREEN,PURPLE='#26374a','#1267b1','#087f70','#8054ad'


class Drawing:
    def __init__(self,title,subtitle,height=1260):
        self.height=height
        self.im=Image.new('RGB',(3800,height*2),'white')
        self.d=ImageDraw.Draw(self.im)
        self.text(65,25,title,42,bold=True)
        self.text(65,90,subtitle,26)

    def text(self,x,y,s,size=26,color=INK,bold=False,anchor=None):
        font=ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size*2)
        self.d.text((x*2,y*2),s,font=font,fill=color,anchor=anchor)

    def line(self,pts,color=INK,width=3):
        self.d.line([(x*2,y*2) for x,y in pts],fill=color,width=width*2,joint='curve')

    def rect(self,x,y,w,h):
        self.d.rectangle((x*2,y*2,(x+w)*2,(y+h)*2),fill='#f6f9fc',outline=INK,width=6)

    def circle(self,x,y,r=8,color=INK):
        self.d.ellipse(((x-r)*2,(y-r)*2,(x+r)*2,(y+r)*2),fill='white',outline=color,width=6)

    def arrow(self,x,y,color=INK):
        self.d.polygon([(x*2,y*2),((x-12)*2,(y-7)*2),((x-12)*2,(y+7)*2)],fill=color)

    def curve(self,pts):
        a,b,c,e=pts
        seq=[]
        for i in range(101):
            t=i/100
            seq.append(tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*e[k] for k in (0,1)))
        self.line(seq)

    def gate(self,x,y,kind):
        w,h=180,140
        if kind=='AND':
            self.line([(x,y+h),(x,y),(x+w-h/2,y)])
            self.d.arc(((x+w-h)*2,y*2,(x+w)*2,(y+h)*2),-90,90,fill=INK,width=6)
            self.line([(x+w-h/2,y+h),(x,y+h)])
        else:
            self.curve([(x,y),(x+w*.58,y),(x+w*.86,y+h*.18),(x+w,y+h/2)])
            self.curve([(x+w,y+h/2),(x+w*.86,y+h*.82),(x+w*.58,y+h),(x,y+h)])
            self.curve([(x,y+h),(x+w*.3,y+h*.67),(x+w*.3,y+h*.33),(x,y)])
        for iy in (y+35,y+105):
            self.line([(x-30,iy),(x+(31 if kind=='OR' else 0),iy)])
        self.text(x+90,y-42,kind,27,bold=True,anchor='mt')

    def ff(self,x,y,name,kind,bit):
        self.rect(x,y,250,240)
        self.text(x+125,y+12,name,30,bold=True,anchor='mt')
        self.text(x+15,y+47,'D' if kind=='DFF' else 'T',28)
        self.text(x+215,y+47,'Q',27)
        self.text(x+185,y+99,'Q_N',24)
        self.circle(x+258,y+110)
        self.text(x+125,y+97,kind,27,anchor='mt')
        self.line([(x+250,y+60),(x+410,y+60)])
        self.arrow(x+410,y+60)
        self.text(x+315,y+23,bit,27,GREEN,bold=True)
        self.line([(x+266,y+110),(x+410,y+110)])
        self.text(x+315,y+120,bit+'_N',25,GREEN,bold=True)
        self.line([(x-70,y+180),(x,y+180)],BLUE)
        self.line([(x,y+168),(x+18,y+180),(x,y+192)],BLUE)
        self.text(x-70,y+146,'clk',24,BLUE)
        self.text(x+160,y+205,'CLR',22,PURPLE,anchor='mt')
        self.circle(x+160,y+248,color=PURPLE)
        self.line([(x+160,y+256),(x+160,y+292)],PURPLE)
        self.text(x+160,y+300,'rst_n',24,PURPLE,anchor='mt')

    def bus(self,pts):
        self.line(pts,width=5)

    def save(self,name):
        self.im.resize((1900,self.height),Image.Resampling.LANCZOS).save(ROOT/'diagrams'/name)


def counter(kind):
    c=Drawing('Modulo 3 counter — '+kind,'Binary count (q1,q0): 00 > 01 > 10 > 00   |   Both flip-flops use the same rising-edge clock')
    for y,name,bit in [(280,'FF1','q1'),(700,'FF0','q0')]:
        c.ff(800,y,name,kind,bit)
    if kind=='DFF':
        specs=[(690,'q1_N','q0_N','D0 = q1_N AND q0_N')]
        for y,a,b,equation in specs:
            c.gate(350,y,'AND')
            for label,iy in [(a,y+35),(b,y+105)]:
                c.line([(175,iy),(320,iy)])
                c.text(175,iy-36,label,26,GREEN,bold=True)
            c.line([(530,y+70),(800,y+70)])
            c.arrow(788,y+70)
        c.line([(350,340),(800,340)])
        c.text(350,300,'q0',28,GREEN,bold=True)
        c.arrow(788,340)
        c.text(1290,290,'D = the next bit value',29,bold=True)
        c.text(1290,350,'D1 = q0',26)
        c.text(1290,397,'D0 = q1_N AND q0_N',26)
        c.text(1290,490,'Unused state: 11 > 10',26)
    else:
        c.gate(350,270,'OR')
        for label,iy in [('q1',305),('q0',375)]:
            c.line([(175,iy),(320,iy)])
            c.text(175,iy-36,label,26,GREEN,bold=True)
        c.line([(530,340),(800,340)])
        c.arrow(788,340)
        c.line([(350,760),(800,760)])
        c.text(350,720,'q1_N',28,GREEN,bold=True)
        c.arrow(788,760)
        c.text(1290,290,'T = 1: toggle the bit',29,bold=True)
        c.text(1290,339,'T = 0: keep the bit',29,bold=True)
        c.text(1290,410,'T1 = q1 OR q0',26)
        c.text(1290,457,'T0 = q1_N',26)
        c.text(1290,545,'Unused state: 11 > 01',26)
    c.line([(65,1100),(1835,1100)],'#d8e0e8',2)
    c.text(65,1130,'Same net name = an electrical connection (including feedback). Q_N is the complementary FF output.',25)
    c.text(65,1175,'clk is shared; rst_n is a shared active-low reset to 00. No asynchronous reset is used for normal wraparound.',25,BLUE)
    c.save('prep-010-mod3-'+kind.lower()+'.png')


def adder():
    c=Drawing('Modulo 3 counter — binary adder + register','Count 0 > 1 > 2 > 0. The adder computes the next value; the register remembers the current value.',1160)
    c.rect(270,370,300,270)
    c.text(420,400,'2-bit ADDER',30,bold=True,anchor='mt')
    c.text(290,444,'A',27)
    c.text(290,564,'B',27)
    c.text(545,474,'S',27)
    c.text(420,524,'S = (A + B) mod 4',23,anchor='mt')
    c.bus([(100,460),(270,460)])
    c.bus([(120,580),(270,580)])
    c.text(120,538,'01',28,GREEN,bold=True)
    c.text(420,605,'Cin',22,anchor='mt')
    c.line([(420,640),(420,698)])
    c.text(440,668,'0',26)
    c.bus([(570,490),(760,490),(760,440),(870,440)])
    c.text(640,444,'sum[1:0]',24,GREEN)
    c.rect(870,370,240,300)
    c.text(990,388,'2-bit MUX',28,bold=True,anchor='mt')
    c.text(885,426,'0',26)
    c.text(885,576,'1',26)
    c.bus([(725,590),(870,590)])
    c.text(730,547,'00',27,GREEN,bold=True)
    c.text(990,630,'S',25,anchor='mt')
    c.line([(990,670),(990,735)])
    c.text(1010,695,'q1 = count[1]',25,GREEN)
    c.bus([(1110,500),(1320,500)])
    c.arrow(1308,500)
    c.text(1150,456,'next[1:0]',24,GREEN)
    c.rect(1320,370,300,300)
    c.text(1470,400,'2-bit REGISTER',28,bold=True,anchor='mt')
    c.text(1340,482,'D',27)
    c.text(1585,482,'Q',27)
    c.text(1470,542,'Two DFFs',25,anchor='mt')
    c.line([(1250,600),(1320,600)],BLUE)
    c.line([(1320,588),(1338,600),(1320,612)],BLUE)
    c.text(1250,561,'clk',25,BLUE)
    c.text(1480,635,'CLR',22,PURPLE,anchor='mt')
    c.circle(1480,678,color=PURPLE)
    c.line([(1480,686),(1480,735)],PURPLE)
    c.text(1480,745,'rst_n',25,PURPLE,anchor='mt')
    c.bus([(1620,500),(1780,500),(1780,835),(100,835),(100,460)])
    c.text(1640,455,'count[1:0]',25,GREEN,bold=True)
    c.text(620,855,'Feedback: the stored current count goes back to adder input A',25)
    c.text(65,180,'q1 = 0 (count 0 or 1): select sum.    q1 = 1 (count 2 or 3): select 00.',28)
    c.text(65,232,'The wrap to 00 occurs at the next rising edge, through D — not through the asynchronous reset pin.',25)
    c.line([(65,965),(1835,965)],'#d8e0e8',2)
    c.text(65,995,'Wide wires carry 2 bits. q1 is the high bit of count[1:0]; the MUX select uses that same signal.',25)
    c.text(65,1040,'Initialize the register to 00. Adder carry-out is unused. The unused state 11 also recovers to 00.',25)
    c.save('prep-010-mod3-adder.png')


if __name__=='__main__':
    counter('DFF')
    counter('TFF')
    adder()
