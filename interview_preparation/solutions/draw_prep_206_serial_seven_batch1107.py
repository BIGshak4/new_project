"""Clean separate modulo-seven input-order illustrations, HE and EN."""
import math
from pathlib import Path
from PIL import Image, ImageDraw
from draw_prep_016_064 import BLUE, GREEN, ORANGE, PURPLE, box, phrase, text, wire

OUT=Path(__file__).resolve().parents[1]/'diagrams'


def curve(d,start,end,offset,color,rx=120,ry=120):
    dx,dy=end[0]-start[0],end[1]-start[1]
    norm=math.hypot(dx,dy)
    radius=1/math.sqrt((dx/norm/rx)**2+(dy/norm/ry)**2)
    sx,sy=start[0]+radius*dx/norm,start[1]+radius*dy/norm
    ex,ey=end[0]-radius*dx/norm,end[1]-radius*dy/norm
    cx,cy=(sx+ex)/2-offset*dy/norm,(sy+ey)/2+offset*dx/norm
    pts=[]
    for i in range(61):
        t=i/60;u=1-t
        pts.append((u*u*sx+2*u*t*cx+t*t*ex,u*u*sy+2*u*t*cy+t*t*ey))
    wire(d,pts,color)


def serial_seven(lg):
    im=Image.new('RGB',(4200,2500),'white');d=ImageDraw.Draw(im)
    phrase(d,(2100,110),'הכנסה מימין ושבע שאריות','Right append with seven remainder states',lg,63,bold=True)
    text(d,(2100,240),'rnext=(2*r+b)%7     divisible=seen AND(r==0)',60,bold=True)
    for panel,(bit,cycles,fixed,color) in enumerate([
        (0,[(1,2,4),(3,6,5)],0,BLUE),(1,[(0,1,3),(2,5,4)],6,ORANGE)]):
        xoff=panel*2100
        text(d,(xoff+1050,410),'bit='+str(bit),64,bold=True,color=color)
        centers={fixed:(xoff+1050,650)}
        for row,cycle in enumerate(cycles):
            y=1110+row*730
            for state,point in zip(cycle,[(xoff+650,y-130),(xoff+1330,y-130),(xoff+1000,y+270)]):
                centers[state]=point
            for a,b in zip(cycle,cycle[1:]+cycle[:1]):
                curve(d,centers[a],centers[b],100,color)
        for state,(x,y) in centers.items():
            c=GREEN if state==0 else color
            d.ellipse((x-120,y-120,x+120,y+120),fill='white',outline=c,width=8)
            text(d,(x,y),'r'+str(state),58,bold=True,color=c)
        x,y=centers[fixed]
        points=[]
        for i in range(81):
            t=i/80;u=1-t
            points.append((u**3*(x+95)+3*u*u*t*(x+360)+3*u*t*t*(x+340)+t**3*(x+15),
                           u**3*(y-60)+3*u*u*t*(y-280)+3*u*t*t*(y-290)+t**3*(y-120)))
        wire(d,points,color)
    phrase(d,(2100,2320),'שני הפאנלים מראים את אותם שבעה מצבים','Both panels show the same seven states',lg,54)
    phrase(d,(2100,2420),'איפוס מתחיל שארית אפס ומסמן מילה ריקה','Reset starts at remainder zero and marks the word empty',lg,50)
    im.save(OUT/f'prep-206-serial-seven-fsm-batch1107-{lg}.png')
    im=Image.new('RGB',(3200,1900),'white');d=ImageDraw.Draw(im)
    phrase(d,(1600,120),'חלופה נפרדת שבה המשקל הנמוך מגיע ראשון','Separate lowest-weight-first arrival',lg,58,bold=True)
    text(d,(1600,300),'rnext=(r+b*w)%7     w=2^k mod7',59,bold=True)
    centers=[(650,900),(2550,900),(1600,1450)]
    for i,(x,y) in enumerate(centers):
        d.ellipse((x-220,y-150,x+220,y+150),fill='white',outline=PURPLE,width=9)
        text(d,(x,y-40),'phase='+str(i),52,bold=True,color=PURPLE)
        text(d,(x,y+55),'w='+str(1<<i),57,color=GREEN)
    for i in range(3):curve(d,centers[i],centers[(i+1)%3],100,PURPLE,220,150)
    box(d,(1150,480,2050,690),BLUE)
    phrase(d,(1600,585),'שארית בתחום אפס עד שש','remainder r in 0..6',lg,49,color=BLUE)
    phrase(d,(1600,1740),'ביט לא תקף משמר גם פאזה וגם שארית','An invalid cycle holds both remainder and phase',lg,48)
    phrase(d,(1600,1840),'פלט אחד רק אחרי ביט תקף וכאשר השארית אפס','Output one only for a nonempty prefix with remainder zero',lg,47)
    im.save(OUT/f'prep-206-serial-seven-lsb-first-batch1107-{lg}.png')


if __name__=='__main__':
    for language in ('he','en'):serial_seven(language)
