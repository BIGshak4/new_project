"""Original Hebrew/English diagrams for the November8 hardware intake."""
import math

from draw_prep_016_064 import BLUE, GREEN, ORANGE, OUT, PURPLE, box, phrase, text, wire
from PIL import Image, ImageDraw


def dot(d,x,y):d.ellipse((x-9,y-9,x+9,y+9),fill=BLUE)


def resistor(d,a,b,label):
 ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay;length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
 pts=[a,(ax+.3*dx,ay+.3*dy)]
 for i in range(1,8):
  t=.3+.4*i/8;off=18 if i%2 else-18;pts.append((ax+t*dx+nx*off,ay+t*dy+ny*off))
 pts.extend([(ax+.7*dx,ay+.7*dy),b]);wire(d,pts,width=6,arrow=False)
 text(d,((ax+bx)/2+nx*60,(ay+by)/2+ny*60),label,48,bold=True)


def ground(d,x,y):
 for yy,w in [(0,100),(22,68),(44,32)]:d.line((x-w/2,y+yy,x+w/2,y+yy),fill=BLUE,width=6)


def main():
 for lg in ('he','en'):
  def frame(he,en,height=1800,lg=lg):
   im=Image.new('RGB',(2800,height),'white');d=ImageDraw.Draw(im)
   phrase(d,(1400,100),he,en,lg,62,bold=True);return im,d
  def save(im,n,stem,lg=lg):im.save(OUT/f'prep-{n:03d}-{stem}-1108b20-{lg}.png')
  im,d=frame('פינות עבודה: זמני הגעה מאוחרים ומוקדמים','Operating corners: latest and earliest arrivals',1950)
  headers=['Process','Voltage','Temperature','Main risk'] if lg=='en' else['תהליך','מתח','טמפרטורה','סיכון עיקרי']
  xs=[430,1050,1650,2350]
  for x,h in zip(xs,headers):text(d,(x,300),h,53,bold=True,hebrew=lg=='he')
  rows=[('SS','LOW','HOT','setup'),('TT','NOM','NOM','-'),('FF','HIGH','COLD','hold')]
  for r,row in enumerate(rows):
   y=450+r*200;box(d,(120,y-65,2690,y+85),ORANGE if r!=1 else BLUE)
   for x,v in zip(xs,row):text(d,(x,y+10),v,58,bold=True)
  for x,label in [(420,'launch FF'),(2200,'capture FF')]:
   box(d,(x,1120,x+500,1430));text(d,(x+250,1220),label,51,bold=True);text(d,(x+250,1340),'CLK',44)
  box(d,(1200,1140,1870,1410),GREEN);text(d,(1535,1260),'Dmin / Dmax',55,color=GREEN)
  wire(d,[(920,1270),(1200,1270)]);wire(d,[(1870,1270),(2200,1270)])
  text(d,(1400,1550),'setup: latest arrival <= next capture - setup - uncertainty',47,color=PURPLE)
  text(d,(1400,1650),'hold: earliest arrival >= same capture + hold + uncertainty',47,color=PURPLE)
  phrase(d,(1400,1800),'טבלת הוראה במודל מונוטוני בלבד; יש לבדוק פינות מאופיינות','Teaching table under a monotonic model; check characterized corners',lg,47)
  save(im,306,'pvt-corners')

  def threshold_circuit(solution,lg=lg):
   im,d=frame('קומפרטור למתח קבל וייחוס מתוכנן','Comparator for a capacitor voltage and a designed reference',1950)
   text(d,(190,430),'Vs',62,bold=True);resistor(d,(300,430),(1050,430),'Rc')
   wire(d,[(1050,430),(1580,430),(1580,650),(1750,650)],arrow=False)
   dot(d,1050,430);text(d,(1110,340),'Vc',55,bold=True)
   wire(d,[(1050,430),(1050,900)],arrow=False)
   d.line((930,900,1170,900),fill=BLUE,width=8);d.line((930,940,1170,940),fill=BLUE,width=8)
   wire(d,[(1050,940),(1050,1190)],arrow=False);ground(d,1050,1190);text(d,(1220,920),'C',55)
   d.polygon([(1750,480),(1750,1060),(2300,770)],fill='#f5f8fd',outline=BLUE,width=7)
   text(d,(1810,650),'+',65,bold=True);text(d,(1810,900),'-',65,bold=True)
   wire(d,[(2300,770),(2600,770)]);text(d,(2580,670),'Y',61,bold=True)
   resistor(d,(440,790),(440,1110),'R' if solution else'Rx')
   resistor(d,(440,1110),(440,1430),'2R' if solution else'Ry')
   text(d,(440,710),'Vs',55,bold=True);ground(d,440,1430);dot(d,440,1110)
   wire(d,[(440,1110),(1025,1110)],arrow=False)
   d.arc((1025,1085,1075,1135),180,360,fill=BLUE,width=6)
   wire(d,[(1075,1110),(1450,1110),(1450,900),(1750,900)],arrow=False)
   text(d,(1300,1220),'Vref = 2Vs/3' if solution else'Vref',51,color=PURPLE)
   phrase(d,(1400,1630),'שני הסעיפים במקור מציינים שני שלישים','Both source clauses specify two thirds',lg,49)
   if solution:text(d,(1400,1770),'Y = 1 if Vc > Vref, otherwise 0',58,color=GREEN,bold=True)
   else:phrase(d,(1400,1770),'בחרו את יחס נגדי הייחוס','Choose the reference-resistor ratio',lg,54)
   return im,d
  im,d=threshold_circuit(False);save(im,307,'rc-given')
  im,d=threshold_circuit(True);save(im,307,'threshold-divider')
  im,d=frame('טעינת קבל וחציית סף יחיד','Capacitor charge and one threshold crossing')
  ox,oy=300,1250;sx,sy=600,850
  wire(d,[(ox,oy),(2650,oy)],width=5);wire(d,[(ox,oy),(ox,280)],width=5)
  points=[(ox+(i/100)*sx,oy-(1-math.exp(-i/100))*sy)for i in range(401)]
  wire(d,points,GREEN,width=7,arrow=False)
  y=oy-sy*2/3;wire(d,[(ox,y),(2650,y)],PURPLE,width=4,arrow=False)
  text(d,(2460,y-65),'2Vs/3',60,color=PURPLE,bold=True)
  t=math.log(3);wire(d,[(ox+t*sx,oy+70),(ox+t*sx,y)],ORANGE,width=4,arrow=False)
  text(d,(ox+t*sx,oy+150),'t* = RC ln(3)',58,color=ORANGE)
  text(d,(1400,1520),'Vc(t) = Vs (1 - exp(-t/RC))',65,color=GREEN,bold=True)
  phrase(d,(1400,1680),'אין כאן שני ספים או זיכרון היסטרזיס','This is one threshold, without hysteresis memory',lg,51)
  save(im,307,'charge-threshold')

  im,d=frame('ארבעה ערוצים באמצעות ממיר משותף','Four channels through one shared ADC',2050)
  for channel in range(4):
   y=370+channel*260;text(d,(170,y),f'CH{channel}',56,bold=True)
   box(d,(360,y-80,1080,y+90));text(d,(720,y),'anti-alias LPF',49,bold=True)
   wire(d,[(260,y),(360,y)]);wire(d,[(1080,y),(1450,y)])
  box(d,(1450,260,1800,1250),GREEN);text(d,(1625,700),'MUX',62,bold=True,color=GREEN);text(d,(1625,950),'0,1,2,3',46)
  box(d,(1970,670,2640,1050),PURPLE);text(d,(2305,780),'S/H + ADC',54,color=PURPLE,bold=True);text(d,(2305,950),'1 MSPS',55,color=PURPLE)
  wire(d,[(1800,850),(1970,850)]);text(d,(2230,1200),'channel tag + timestamp + sample',47)
  for k in range(8):
   x=240+k*310;box(d,(x,1420,x+290,1570),[BLUE,GREEN,PURPLE,ORANGE][k%4]);text(d,(x+145,1495),f'CH{k%4}',52,bold=True)
  text(d,(1400,1700),'1 us / slot   ->   4 us / channel   ->   250 kS/s / channel',55,color=GREEN,bold=True)
  phrase(d,(1400,1840),'זמן מיתוג ורכישה והמרה חייב להתאים לחלון','Switch, acquire and convert must fit the slot',lg,48)
  phrase(d,(1400,1950),'לדגימה בו זמנית מוסיפים החזקה נפרדת לכל ערוץ','For simultaneous sampling add a separate hold per channel',lg,47)
  save(im,310,'adc-round-robin')

  im,d=frame('נתון: קבל טורי ונגד לאדמה לפני מהפך','Given: a series capacitor and ground bias before an inverter',1850)
  text(d,(220,560),'A',65,bold=True);wire(d,[(300,560),(700,560)],arrow=False)
  d.line((700,430,700,690),fill=BLUE,width=8);d.line((750,430,750,690),fill=BLUE,width=8)
  text(d,(725,340),'Ccap',49);wire(d,[(750,560),(1760,560)],arrow=False)
  dot(d,1150,560);text(d,(1150,430),'B',63,bold=True)
  resistor(d,(1150,560),(1150,1120),'R');ground(d,1150,1120)
  d.polygon([(1760,360),(1760,760),(2150,560)],fill='#f5f8fd',outline=BLUE,width=7)
  d.ellipse((2150,525,2220,595),outline=BLUE,width=7);wire(d,[(2220,560),(2600,560)])
  text(d,(2580,450),'Cout',60,bold=True)
  wire(d,[(350,1490),(850,1490),(850,1280),(2440,1280)],GREEN,width=7,arrow=False)
  text(d,(230,1430),'A',57,color=GREEN);text(d,(850,1590),'t = 0',55)
  phrase(d,(1400,1750),'לפני המדרגה המערכת התייצבה והקבל אינו טעון','Before the step the circuit is settled and the capacitor uncharged',lg,47)
  save(im,132,'ground-given')
  im,d=frame('הצומת דועך לאפס בזמן שהקבל נטען','The node decays to zero while the capacitor charges',2150)
  ox,sx=420,530
  for row,label in [(0,'A / VDD'),(1,'B / VDD'),(2,'Cout / VDD'),(3,'Vcap / VDD')]:
   y=500+row*360;wire(d,[(ox,y),(2620,y)],width=3);text(d,(200,y-100),label,42,bold=True)
   if row==0:pts=[(ox-160,y),(ox,y),(ox,y-220),(2540,y-220)]
   elif row==1:pts=[(ox-160,y),(ox,y),(ox,y-220)]+[(ox+t/100*sx,y-220*math.exp(-t/100))for t in range(401)]
   elif row==2:pts=[(ox-160,y-220),(ox,y-220),(ox,y),(ox+math.log(2)*sx,y),(ox+math.log(2)*sx,y-220),(2540,y-220)]
   else:pts=[(ox-160,y),(ox,y)]+[(ox+t/100*sx,y-220*(1-math.exp(-t/100)))for t in range(401)]
   wire(d,pts,GREEN if row in(1,3)else BLUE,width=7,arrow=False)
  text(d,(1400,1930),'B = VDD exp(-t/RC)   |   Vcap = A - B',64,color=PURPLE,bold=True)
  text(d,(1400,2050),'VM = VDD/2  ->  negative pulse width = RC ln(2)',55,color=ORANGE)
  save(im,132,'ground-waveforms')

  im,d=frame('נתון: שני חיישני נוכחות ואורך בול העץ','Given: two presence sensors and the wood length',1850)
  for y,long_mode in [(620,False),(1250,True)]:
   wire(d,[(350,y+170),(2460,y+170)],width=5,arrow=False)
   for x,label in [(1000,'A'),(1800,'B')]:
    wire(d,[(x,y-220),(x,y+180)],PURPLE,width=5,arrow=False);text(d,(x,y-300),label,63,color=PURPLE,bold=True)
   left=700;right=2100 if long_mode else 1150
   box(d,(left,y-90,right,y+90),GREEN);text(d,((left+right)/2,y),'L > d' if long_mode else'L < d',60,color=GREEN,bold=True)
   wire(d,[(1000,y+270),(1800,y+270)],width=4);text(d,(1400,y+345),'d',53,bold=True)
  phrase(d,(1400,1710),'יש להגדיר מתי מדווח כיוון ומה אפשר לצפות באזור העיוור','Define when direction is reported and what is observable in the blind gap',lg,46)
  save(im,53,'wood-given')
  im,d=frame('חמש פאזות לזיהוי מעבר שהושלם','Five progress states detect a completed traversal',2350)
  centers={'I':(1400,410),'WAIT_B':(600,980),'EXIT_B':(600,1570),'WAIT_A':(2200,980),'EXIT_A':(2200,1570)}
  for label,(x,y) in centers.items():d.ellipse((x-180,y-130,x+180,y+130),fill='#f5f8fd',outline=BLUE,width=7);text(d,(x,y),label,49,bold=True)
  for target,reading in [('WAIT_B','10'),('WAIT_A','01')]:
   x,y=centers[target];wire(d,[(1400+(-140 if x<1400 else 140),510),(x,850)]);text(d,((1400+x)/2,620),reading,55)
  for x,target,reading in [(600,'EXIT_B','01'),(2200,'EXIT_A','10')]:
   wire(d,[(x,1110),(x,1440)]);text(d,(x+110,1280),reading,55)
  wire(d,[(420,1570),(220,1570),(220,410),(1220,410)],GREEN);text(d,(360,270),'00 / RIGHT',47,color=GREEN,bold=True)
  wire(d,[(2380,1570),(2580,1570),(2580,410),(1580,410)],ORANGE);text(d,(2400,270),'00 / LEFT',47,color=ORANGE,bold=True)
  phrase(d,(1400,1910),'עץ קצר: אפס אפס בזמן ההמתנה הוא פער עיוור','Short wood: 00 while waiting is a blind gap',lg,50)
  phrase(d,(1400,2040),'עץ ארוך: אחד אחד יכול להישאר במצב המתנה','Long wood: 11 may remain in a waiting state',lg,49)
  phrase(d,(1400,2190),'בגרסה הקצרה נדרשת תנועה מונוטונית; עצירות מותרות','The short version requires monotone motion; pauses are allowed',lg,48)
  save(im,53,'wood-progress-fsm')

  im,d=frame('השוואה אחת ושני בוררים לשני המוצאים','One comparison and two multiplexers for both outputs')
  box(d,(820,280,1940,590),PURPLE);text(d,(1380,420),'swap = (a < b)',64,color=PURPLE,bold=True)
  for y,label in [(950,'maximum'),(1450,'minimum')]:
   box(d,(1100,y-140,1830,y+140));text(d,(1465,y),label,63,bold=True)
   text(d,(520,y-70),'b[7:0]' if label=='maximum' else'a[7:0]',53)
   text(d,(520,y+70),'a[7:0]' if label=='maximum' else'b[7:0]',53)
   wire(d,[(700,y-70),(1100,y-70)]);wire(d,[(700,y+70),(1100,y+70)])
   text(d,(1150,y-70),'1',40);text(d,(1150,y+70),'0',40)
   wire(d,[(1830,y),(2540,y)]);text(d,(2200,y-90),'[7:0]',46)
  wire(d,[(1465,590),(1465,810)],PURPLE);wire(d,[(1940,420),(2100,420),(2100,1250),(1465,1250),(1465,1310)],PURPLE)
  phrase(d,(1400,1680),'ללא סימן; שוויון נותן ערכים זהים בשתי היציאות','Unsigned inputs; equality produces the same value at both outputs',lg,47)
  save(im,18,'eight-bit-minmax')
  im,d=frame('סינוס עם שלושים ושתיים פאזות וסימטריה','A sine with thirty-two phases and symmetry',1900)
  ox,oy,sx,sy=260,710,70,400
  wire(d,[(180,oy),(2630,oy)],width=4);wire(d,[(ox,1200),(ox,220)],width=4)
  pts=[(ox+n*sx,oy-math.sin(2*math.pi*n/32)*sy)for n in range(33)]
  wire(d,pts,GREEN,width=6,arrow=False)
  for n,(x,y) in enumerate(pts):
   dot(d,x,y)
   if n%8==0:text(d,(x,1290),str(n),54,bold=True)
  text(d,(1400,1440),'sample[n] = round(32767 sin(2 pi n / 32))',58,color=PURPLE,bold=True)
  text(d,(1400,1570),'full: 32 words   |   half: 16   |   quarter: 9 incl. zero',54)
  phrase(d,(1400,1700),'שמונה קבועים שאינם אפס ואפס מחיווט','Eight nonzero constants plus wired zero',lg,49)
  phrase(d,(1400,1810),'הכפלה בשלושים ושתיים בנוסח המקורי נותנת אפס בדגימות שלמות','Literal multiplication by thirty-two yields zero at integer samples',lg,44)
  save(im,299,'sine32-fold')


if __name__=='__main__':main()
