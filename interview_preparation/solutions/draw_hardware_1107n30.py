"""Original bilingual teaching diagrams, separate from archived raw sources."""
import math

from draw_prep_016_064 import (
    BLUE,
    GREEN,
    ORANGE,
    OUT,
    PURPLE,
    box,
    phrase,
    text,
    wire,
)
from PIL import Image, ImageDraw


def resistor(d, a, b, label, color=BLUE, size=44):
    ax,ay=a;bx,by=b
    dx,dy=bx-ax,by-ay
    length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
    points=[a,(ax+.30*dx,ay+.30*dy)]
    for i in range(1,8):
        t=.30+.40*i/8;offset=19 if i%2 else -19
        points.append((ax+t*dx+nx*offset,ay+t*dy+ny*offset))
    points.extend([(ax+.70*dx,ay+.70*dy),b])
    wire(d,points,color,width=6,arrow=False)
    text(d,((ax+bx)/2+nx*62,(ay+by)/2+ny*62),label,size,color=color,bold=True)


def dot(d,x,y,color=BLUE):d.ellipse((x-10,y-10,x+10,y+10),fill=color)


def main():
 for lg in ('he','en'):
  def frame(he,en,height=1750,lg=lg):
   im=Image.new('RGB',(2800,height),'white');d=ImageDraw.Draw(im)
   phrase(d,(1400,100),he,en,lg,61,bold=True);return im,d
  def save(im,n,stem,lg=lg):im.save(OUT/f'prep-{n:03d}-{stem}-1107n30-{lg}.png')

  im,d=frame('קוביית שנים עשר נגדים זהים','Cube of twelve equal resistors',1950)
  positions={0:(750,330),1:(1550,330),2:(350,630),3:(1150,630),4:(750,1180),5:(1550,1180),6:(350,1480),7:(1150,1480)}
  for v in range(8):
   for bit in (1,2,4):
    u=v^bit
    if v<u:resistor(d,positions[v],positions[u],'R',BLUE,38)
  for v,(x,y) in positions.items():
   dot(d,x,y,GREEN if v in (0,7) else BLUE)
   text(d,(x-65,y-60),f'{v:03b}',37,bold=True)
  text(d,(750,230),'A = 1 V',51,color=GREEN,bold=True)
  text(d,(1150,1580),'B = 0 V',51,color=GREEN,bold=True)
  for top,bot,label in [(360,650,'R/3'),(650,1050,'R/6'),(1050,1340,'R/3')]:
   resistor(d,(2230,top),(2230,bot),label,GREEN,51)
  for y,label in [(360,'A: 1 V'),(650,'3/5 V'),(1050,'2/5 V'),(1340,'B: 0 V')]:
   dot(d,2230,y,GREEN);text(d,(2470,y),label,48,color=GREEN)
  text(d,(1400,1730),'Req = R/3 + R/6 + R/3 = 5R/6',67,color=PURPLE,bold=True)
  phrase(d,(1400,1850),'רק נקודות מסומנות הן צמתים','Only marked dots are junctions',lg,46)
  save(im,290,'cube-layers')

  im,d=frame('כפל קבוע בארבעים ותשע עם שני מחברים','Multiply by 49 using two adders')
  for rect,label,color in [((580,460,1220,850),'t = x + 2x',BLUE),((1760,460,2430,850),'y = 16t + x',GREEN)]:
   box(d,rect,color);text(d,((rect[0]+rect[2])/2,650),label,57,color=color,bold=True)
  text(d,(230,650),'x[9:0]',53,bold=True);wire(d,[(360,650),(580,650)])
  wire(d,[(1220,650),(1760,650)]);text(d,(1490,560),'t[11:0]',53)
  wire(d,[(2430,650),(2670,650)]);text(d,(2500,970),'y[15:0]',53,color=GREEN)
  wire(d,[(440,650),(440,1060),(1650,1060),(1650,740),(1760,740)],ORANGE)
  text(d,(1080,1010),'zero-extended x',48,color=ORANGE)
  text(d,(1400,1270),'49x = 16(3x) + x',73,color=PURPLE,bold=True)
  text(d,(1400,1420),'x = 1023  ->  t = 3069  ->  y = 50127',57)
  phrase(d,(1400,1580),'מרחיבים לפני הזזה; תוצאה מדויקת ללא חיתוך','Extend before shifting; exact result without truncation',lg,49)
  save(im,293,'times49-datapath')

  im,d=frame('גשר מאוזן: אותו מתח בשתי נקודות האמצע','Balanced bridge: equal midpoint voltages',1850)
  wire(d,[(650,300),(2050,300)],arrow=False);wire(d,[(650,1400),(2050,1400)],arrow=False)
  for x,top,bot in [(650,'R1','R2'),(2050,'R3','R4')]:
   resistor(d,(x,300),(x,850),top);resistor(d,(x,850),(x,1400),bot);dot(d,x,850)
  resistor(d,(650,850),(2050,850),'R5',GREEN,56)
  text(d,(490,850),'VL',50,color=PURPLE);text(d,(2210,850),'VR',50,color=PURPLE)
  text(d,(1400,230),'Vs != 0',58,bold=True);text(d,(1400,1470),'0 V',53)
  text(d,(1400,1130),'VL = Vs R2/(R1+R2)',51,color=PURPLE)
  text(d,(1400,1230),'VR = Vs R4/(R3+R4)',51,color=PURPLE)
  text(d,(1400,1630),'I5 = 0  <=>  R1 R4 = R2 R3',65,color=GREEN,bold=True)
  phrase(d,(1400,1760),'כל הנגדים חיוביים וסופיים','All resistances are positive and finite',lg,49)
  save(im,294,'bridge-balance')

  im,d=frame('משוב שלילי במגבר שאינו הופך','Negative feedback in a non-inverting amplifier',1850)
  d.polygon([(1350,480),(1350,1200),(2020,840)],outline=BLUE,width=8,fill='#f5f8fd')
  text(d,(1420,700),'-',65,bold=True);text(d,(1420,1000),'+',65,bold=True)
  resistor(d,(330,1000),(1350,1000),'Rin = R')
  text(d,(220,1000),'Vin',52,bold=True)
  wire(d,[(1350,700),(1050,700),(1050,350)],arrow=False)
  resistor(d,(1050,350),(2300,350),'Rf = R')
  wire(d,[(2300,350),(2300,840),(2020,840)],arrow=False)
  wire(d,[(2300,840),(2630,840)]);text(d,(2510,750),'Vout',55,bold=True)
  resistor(d,(1050,700),(420,700),'Rg = R')
  wire(d,[(420,700),(420,550)],arrow=False)
  d.line((365,550,475,550),fill=BLUE,width=7);d.line((380,528,460,528),fill=BLUE,width=6)
  text(d,(350,460),'0 V',46)
  dot(d,1050,700);dot(d,2300,840)
  text(d,(1400,1370),'I+ = I- = 0   ->   V+ = Vin',61,color=GREEN)
  text(d,(1400,1500),'V- = Vout/2 = V+   ->   Vout = 2 Vin',61,color=PURPLE,bold=True)
  phrase(d,(1400,1700),'מודל אידאלי בתחום ליניארי; אין נפילת מתח בנגד הכניסה','Ideal linear operation; input resistor has zero voltage drop',lg,47)
  save(im,297,'noninverting-three-r')

  im,d=frame('עשר דגימות למחזור וקיפול לפי סימטריה','Ten samples per period, folded by symmetry',1950)
  values=[0,19260,31163,31163,19260,0,-19260,-31163,-31163,-19260]
  ox,oy,sx,sy=250,650,250,360
  wire(d,[(180,oy),(2670,oy)],width=4);wire(d,[(ox,1060),(ox,230)],width=4)
  points=[(ox+n*sx,oy-v/32767*sy) for n,v in enumerate(values)]
  wire(d,points,GREEN,width=6,arrow=False)
  for n,(x,y) in enumerate(points):
   dot(d,x,y,GREEN);wire(d,[(x,oy),(x,y)],GREEN,width=3,arrow=False);text(d,(x,1110),str(n),43,bold=True)
  text(d,(1400,1220),'q = phase % 5;  index = min(q, 5-q)',58,color=PURPLE)
  text(d,(1400,1340),'index:  0  1  2  2  1  0  1  2  2  1',56)
  text(d,(1400,1460),'sign:    +  +  +  +  +  -  -  -  -  -',56)
  text(d,(1400,1580),'full: 10 x 16   |   half: 5 x 16   |   folded: 3 x 16 bits',51,color=BLUE,bold=True)
  phrase(d,(1400,1710),'רק שני ערכים שאינם אפס אם אפס מתקבל מחיווט','Only two nonzero constants if zero is supplied by wiring',lg,47)
  phrase(d,(1400,1840),'אין חצי תא זיכרון; רבע מחזור נמצא בין דגימות','No fractional ROM cells; a quarter turn lies between samples',lg,46)
  save(im,299,'sine-phase-fold')

  im,d=frame('שער נאד סטטי בטכנולוגיית סי מוס','Static complementary CMOS NAND',1950)
  def mos(x,y,p,label,d=d):
   wire(d,[(x,y-130),(x,y+130)],arrow=False,width=6)
   d.line((x-55,y-65,x-55,y+65),fill=BLUE,width=7)
   wire(d,[(x-200,y),(x-55,y)],arrow=False,width=6)
   if p:d.ellipse((x-89,y-17,x-55,y+17),fill='white',outline=BLUE,width=5)
   text(d,(x+130,y),label,46,bold=True)
  for x,label in [(1000,'PA'),(1800,'PB')]:mos(x,490,True,label)
  wire(d,[(1000,360),(1000,260),(1800,260),(1800,360)],arrow=False)
  text(d,(1400,210),'VDD',54,bold=True)
  wire(d,[(1000,620),(1000,750),(1800,750),(1800,620)],arrow=False)
  wire(d,[(1400,750),(2430,750)]);text(d,(2480,750),'Y',61,bold=True)
  wire(d,[(1400,750),(1400,870)],arrow=False)
  mos(1400,1000,False,'NA');mos(1400,1390,False,'NB')
  wire(d,[(1400,1130),(1400,1260)],arrow=False)
  wire(d,[(1400,1520),(1400,1590)],arrow=False)
  text(d,(1400,1640),'GND',54,bold=True)
  for x,y,label in [(1000,490,'A'),(1800,490,'B'),(1400,1000,'A'),(1400,1390,'B')]:text(d,(x-270,y),label,52,color=PURPLE,bold=True)
  dot(d,1400,750);text(d,(1400,1760),'Y = NOT (A AND B)',61,color=GREEN,bold=True)
  phrase(d,(1400,1860),'גופי פי למסילה הגבוהה; גופי אן למסילה הנמוכה','PMOS bodies to VDD; NMOS bodies to GND',lg,46)
  save(im,302,'cmos-nand')

  im,d=frame('שבעה מחברים מלאים לספירת שמונה סיביות','Seven full adders count eight input bits',2000)
  rows=[(420,'F0: x0,x1,x2 -> s0,c0','F1: x3,x4,x5 -> s1,c1'),
        (720,'F2: s0,s1,x6 -> s2,c2','F3: s2,x7,0 -> y0,c3'),
        (1080,'F4: c0,c1,c2 -> t0,u0','F5: t0,c3,0 -> y1,u1'),
        (1440,'F6: u0,u1,0 -> y2,y3','')]
  for y,left,right in rows:
   for x,label in [(160,left),(1450,right)]:
    if label:box(d,(x,y-70,x+1180,y+140),GREEN if y>=1080 else BLUE);text(d,(x+590,y+35),label,44,bold=True)
  for y,label in [(270,'weight 1: x[7:0], s0,s1,s2, y0'),(940,'weight 2: c0,c1,c2,c3,t0, y1'),(1300,'weight 4: u0,u1, y2')]:text(d,(1400,y),label,52,color=PURPLE)
  text(d,(1400,1730),'count = y0 + 2y1 + 4y2 + 8y3',65,color=GREEN,bold=True)
  phrase(d,(1400,1870),'כל שורה שומרת משקל; אפס אינו מחבר נפרד','Every cell conserves weight; a zero-tied cell is still an FA',lg,47)
  save(im,1,'eight-fa-compression')

  im,d=frame('מחבר לארבע סיביות: מחבר חלקי ושלושה מלאים','Four-bit addition: one HA followed by three FAs')
  for i in range(4):
   x=290+i*650;label='HA' if i==0 else'FA'
   box(d,(x,490,x+420,910),GREEN if i==0 else BLUE);text(d,(x+210,650),f'{label}{i}',69,bold=True)
   text(d,(x+210,370),f'A{i}, B{i}',51)
   wire(d,[(x+210,410),(x+210,490)]);wire(d,[(x+210,910),(x+210,1110)])
   text(d,(x+210,1200),f'S{i}',60,color=GREEN,bold=True)
   if i<3:
    wire(d,[(x+420,700),(x+650,700)]);text(d,(x+535,620),f'C{i+1}',44)
   else:wire(d,[(x+420,700),(2720,700)]);text(d,(2660,980),'S4',58,color=GREEN,bold=True)
  text(d,(1400,1400),'S[4:0] = A[3:0] + B[3:0]   |   0 <= S <= 30',60,color=PURPLE,bold=True)
  phrase(d,(1400,1580),'ללא נשא כניסה; הסיבית החמישית שומרת את הנשא','No external carry-in; the fifth output retains the final carry',lg,49)
  save(im,122,'mixed-ha-fa-ripple')

  # Separate prompt figures: topology only, with no solution equations/results.
  im,d=frame('נתון: קובייה עם נגד בכל צלע','Given: a cube with one resistor on each edge',1950)
  positions={0:(1050,360),1:(1850,360),2:(650,660),3:(1450,660),4:(1050,1210),5:(1850,1210),6:(650,1510),7:(1450,1510)}
  for v in range(8):
   for bit in (1,2,4):
    u=v^bit
    if v<u:resistor(d,positions[v],positions[u],'1 ohm',BLUE,36)
  for v,(x,y) in positions.items():dot(d,x,y)
  text(d,(1050,260),'A',66,color=GREEN,bold=True)
  text(d,(1450,1630),'B',66,color=GREEN,bold=True)
  phrase(d,(1400,1800),'חישוב התנגדות בין ההדקים המסומנים','Find resistance between the marked terminals',lg,51)
  save(im,290,'cube-given')

  im,d=frame('נתון: גשר נגדים בעל שתי נקודות אמצע','Given: a resistor bridge with two midpoint nodes',1850)
  wire(d,[(650,300),(2050,300)],arrow=False);wire(d,[(650,1400),(2050,1400)],arrow=False)
  for x,top,bot in [(650,'R1','R2'),(2050,'R3','R4')]:
   resistor(d,(x,300),(x,850),top);resistor(d,(x,850),(x,1400),bot);dot(d,x,850)
  resistor(d,(650,850),(2050,850),'R5',GREEN,56)
  text(d,(490,850),'VL',50,color=PURPLE);text(d,(2210,850),'VR',50,color=PURPLE)
  text(d,(1400,230),'Vs != 0',58,bold=True);text(d,(1400,1480),'GND',54)
  phrase(d,(1400,1680),'כל חמש ההתנגדויות חיוביות וסופיות','All five resistances are positive and finite',lg,50)
  save(im,294,'bridge-given')

  im,d=frame('נתון: מגבר שרת ושלושה נגדים שווים','Given: an op-amp and three equal resistors',1850)
  d.polygon([(1350,480),(1350,1200),(2020,840)],outline=BLUE,width=8,fill='#f5f8fd')
  text(d,(1420,700),'-',65,bold=True);text(d,(1420,1000),'+',65,bold=True)
  resistor(d,(330,1000),(1350,1000),'R')
  text(d,(220,1000),'Vin',52,bold=True)
  wire(d,[(1350,700),(1050,700),(1050,350)],arrow=False)
  resistor(d,(1050,350),(2300,350),'R')
  wire(d,[(2300,350),(2300,840),(2020,840)],arrow=False)
  wire(d,[(2300,840),(2630,840)]);text(d,(2510,750),'Vout',55,bold=True)
  resistor(d,(1050,700),(420,700),'R')
  wire(d,[(420,700),(420,550)],arrow=False)
  d.line((365,550,475,550),fill=BLUE,width=7);d.line((380,528,460,528),fill=BLUE,width=6)
  text(d,(350,460),'GND',46)
  dot(d,1050,700);dot(d,2300,840)
  phrase(d,(1400,1490),'מצאו את יחס מתח המוצא למתח הכניסה','Find the output-to-input voltage ratio',lg,55)
  save(im,297,'noninverting-given')


if __name__=='__main__':main()
