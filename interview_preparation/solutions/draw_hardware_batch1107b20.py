"""Localized original teaching figures; no edits to archived screenshots."""
from draw_prep_016_064 import BLUE, GREEN, ORANGE, OUT, PURPLE, box, phrase, text, wire
from PIL import Image, ImageDraw


def main():
 for lg in ('he','en'):
  def frame(he,en,height=1450,lg=lg):
   im=Image.new('RGB',(2400,height),'white');d=ImageDraw.Draw(im)
   phrase(d,(1200,100),he,en,lg,63,bold=True);return im,d
  def save(im,n,stem,lg=lg):im.save(OUT/f'prep-{n:03d}-{stem}-batch1107b20-{lg}.png')
  im,d=frame('שלוש הדגימות האחרונות ומיון לאחר קליטה','Capture the latest three samples, then sort')
  box(d,(320,350,1060,1020));text(d,(690,440),'h0 / h1 / h2',63,bold=True)
  for yy,he,en in [(590,'חדש','newest'),(720,'קודם','previous'),(850,'ישן','oldest')]:phrase(d,(690,yy),he,en,lg,51)
  wire(d,[(70,675),(320,675)]);text(d,(180,590),'sample[1:0]',41)
  box(d,(1270,350,2000,1020),GREEN)
  phrase(d,(1635,450),'שלושה שלבי החלפה','Three exchange stages',lg,45,bold=True)
  for yy,s in [(600,'compare(0,1)'),(730,'compare(1,2)'),(860,'compare(0,1)')]:text(d,(1635,yy),s,51)
  wire(d,[(1060,675),(1270,675)]);wire(d,[(2000,675),(2290,675)])
  text(d,(2150,545),'max / mid / min',40)
  text(d,(1200,1160),'out_valid = (accepted_since_reset >= 3)',56,color=PURPLE)
  phrase(d,(1200,1300),'איפוס מרוקן היסטוריה; ערכים כפולים מותרים','Reset flushes history; equal values are allowed',lg,49)
  save(im,279,'latest-three-sort')
  im,d=frame('פייפליין: השהיה לעומת קצב השלמה','Pipeline: latency versus completion rate')
  xs=310;ys=380;cw=235;rh=175
  stages=['IF','ID','EX','MEM','WB'];colors=[BLUE,GREEN,PURPLE,ORANGE,BLUE]
  for c in range(8):text(d,(xs+(c+.5)*cw,260),str(c+1),52,bold=True)
  for r in range(4):
   text(d,(130,ys+(r+.5)*rh),f'I{r}',58,bold=True)
   for c in range(8):
    d.rectangle((xs+c*cw,ys+r*rh,xs+(c+1)*cw,ys+(r+1)*rh),outline='#cbd3df',width=3)
    k=c-r
    if 0<=k<5:box(d,(xs+c*cw+7,ys+r*rh+10,xs+(c+1)*cw-7,ys+(r+1)*rh-10),colors[k]);text(d,(xs+(c+.5)*cw,ys+(r+.5)*rh),stages[k],50,color=colors[k],bold=True)
  text(d,(1200,1190),'5 + 4 - 1 = 8' if lg=='he' else '4 instructions: 5 + 4 - 1 = 8 slots',59,color=GREEN)
  if lg=='he':phrase(d,(1200,1260),'ארבע הוראות בשמונה משבצות','',lg,40,color=GREEN)
  phrase(d,(1200,1320),'ללא עצירות, בועות או סיכוני נתונים בדגם האידאלי','Ideal model: no stalls, bubbles or hazards',lg,47)
  save(im,280,'pipeline-slots')
  im,d=frame('חיבורי המסילות הם חלק מהפונקציה','Signal-connected rails determine the function',1850)
  def mos(cx,cy,p,label,d=d):
   d.line((cx,cy-90,cx,cy-45),fill=BLUE,width=7);d.line((cx,cy+45,cx,cy+90),fill=BLUE,width=7)
   d.line((cx,cy-45,cx,cy+45),fill=BLUE,width=7);d.line((cx-45,cy-50,cx-45,cy+50),fill=BLUE,width=7)
   d.line((cx-120,cy,cx-45,cy),fill=BLUE,width=7)
   if p:d.ellipse((cx-72,cy-13,cx-46,cy+13),fill='white',outline=BLUE,width=6)
   text(d,(cx+120,cy),label,46,bold=True)
  for cx in (720,1770):mos(cx,480,True,'P0' if cx==720 else'P1');mos(cx,900,False,'N0' if cx==720 else'N1')
  wire(d,[(720,570),(720,810)],arrow=False);wire(d,[(1770,570),(1770,810)],arrow=False)
  wire(d,[(720,390),(720,350)],arrow=False);text(d,(720,300),'VDD',54,bold=True)
  wire(d,[(720,990),(720,1130)],arrow=False);d.line((665,1130,775,1130),fill=BLUE,width=7);d.line((680,1150,760,1150),fill=BLUE,width=6);d.line((700,1170,740,1170),fill=BLUE,width=6)
  wire(d,[(200,690),(480,690),(480,480),(600,480)],arrow=False);wire(d,[(480,690),(480,900),(600,900)],arrow=False)
  text(d,(180,630),'A',62,bold=True)
  wire(d,[(250,690),(250,180),(1770,180),(1770,390)],arrow=False);text(d,(1500,260),'A',55,color=GREEN,bold=True)
  wire(d,[(720,690),(1120,690),(1120,1140),(1770,1140),(1770,990)],arrow=False);text(d,(1410,1070),'X = NOT A',50,color=GREEN,bold=True)
  wire(d,[(1300,690),(1530,690),(1530,480),(1650,480)],arrow=False);wire(d,[(1530,690),(1530,900),(1650,900)],arrow=False);text(d,(1370,620),'B',60,bold=True)
  wire(d,[(1770,690),(2210,690)]);text(d,(2160,610),'Y',60,bold=True)
  for x,y in [(250,690),(480,690),(720,690),(1530,690),(1770,690)]:d.ellipse((x-9,y-9,x+9,y+9),fill=BLUE)
  text(d,(1200,1330),'B=0: Y <- A       B=1: Y <- NOT A',57,color=GREEN)
  text(d,(1200,1430),'ideal Y = A XOR B',66,bold=True,color=PURPLE)
  phrase(d,(1200,1560),'אפס חלש דרך פי; אחד חלש דרך אן','PMOS passes a weak zero; NMOS passes a weak one',lg,48)
  phrase(d,(1200,1690),'מודל מתגים אינו מדמה מתח סף או שולי רעש','Digital switches do not model threshold loss or noise margin',lg,44)
  save(im,282,'signal-rail-xor')
  im,d=frame('גרירה לוגית בין שני ערכי אמת','Material implication between two truth values')
  rows=[('A','B','Y'),('0','0','1'),('0','1','1'),('1','0','0'),('1','1','1')]
  for r,row in enumerate(rows):
   y0=260+r*150;box(d,(370,y0,2030,y0+130),ORANGE if r==3 else BLUE)
   for c,v in enumerate(row):text(d,(650+c*550,y0+65),v,65,bold=r==0)
  text(d,(1200,1120),'Y = (NOT A) OR B = MUX(A, 1, B)',61,color=GREEN)
  phrase(d,(1200,1270),'רק הנחת אמת עם מסקנת שקר מפרה גרירה','Only a true premise with a false conclusion violates implication',lg,46)
  save(im,283,'implication-truth')
  im,d=frame('אותו שער וגם בשלוש ספריות רכיבים','The same AND in three primitive libraries',1800)
  for yy,left,right,he,en in [(420,'NAND','NAND','שני שערי נאד','Two NAND gates'),(1420,'NAND','NOR','שער אחד מכל סוג','One gate of each type')]:
   phrase(d,(1200,yy-150),he,en,lg,52,bold=True)
   for xx,label in [(620,left),(1500,right)]:box(d,(xx,yy-80,xx+400,yy+100));text(d,(xx+200,yy+10),label,53,bold=True)
   text(d,(230,yy-35),'A',49);text(d,(230,yy+65),'B',49)
   wire(d,[(300,yy-35),(620,yy-35)]);wire(d,[(300,yy+65),(620,yy+65)])
   wire(d,[(1020,yy+10),(1280,yy+10),(1280,yy-35),(1500,yy-35)])
   wire(d,[(1280,yy+10),(1280,yy+65),(1500,yy+65)])
   d.ellipse((1272,yy+2,1288,yy+18),fill=BLUE)
   wire(d,[(1900,yy+10),(2200,yy+10)]);text(d,(2160,yy-70),'Y',54)
  phrase(d,(1200,720),'שלושה שערי נור','Three NOR gates',lg,52,bold=True)
  for yy,label in [(870,'A'),(1070,'B')]:
   box(d,(620,yy-70,1020,yy+70));text(d,(820,yy),'NOR',53,bold=True);text(d,(250,yy),label,52)
   wire(d,[(300,yy),(470,yy),(470,yy-30),(620,yy-30)])
   wire(d,[(470,yy),(470,yy+30),(620,yy+30)])
   wire(d,[(1020,yy),(1250,yy),(1250,950 if yy==870 else 1010),(1500,950 if yy==870 else 1010)])
  box(d,(1500,900,1900,1060));text(d,(1700,980),'NOR',53,bold=True);wire(d,[(1900,980),(2200,980)]);text(d,(2160,900),'Y',54)
  text(d,(1200,1660),'Y = A AND B',63,color=GREEN,bold=True)
  save(im,286,'and-three-libraries')
  im,d=frame('זיהוי אפס אפס אחד אפס עם חפיפות','Detect 0010 with overlapping matches',1650)
  centers=[350,900,1450,2000];cy=650;r=120
  for i,x in enumerate(centers):
   d.ellipse((x-r,cy-r,x+r,cy+r),fill='#f3f7fc',outline=BLUE,width=7);text(d,(x,cy-25),f'S{i}',59,bold=True);text(d,(x,cy+50),['-','0','00','001'][i],49)
  for i,label in [(0,'0 / 0'),(1,'0 / 0'),(2,'1 / 0')]:
   wire(d,[(centers[i]+r,cy),(centers[i+1]-r,cy)]);text(d,((centers[i]+centers[i+1])/2,cy-65),label,43)
  wire(d,[(900,530),(900,270),(350,270),(350,530)]);text(d,(620,215),'1 / 0',47)
  wire(d,[(2000,770),(2000,1050),(900,1050),(900,770)],GREEN);text(d,(1450,1000),'0 / 1',53,color=GREEN,bold=True)
  wire(d,[(2120,650),(2260,650),(2260,1250),(350,1250),(350,770)]);text(d,(1530,1190),'1 / 0',47)
  for x,label in [(350,'1 / 0'),(1450,'0 / 0')]:
   wire(d,[(x-75,555),(x-170,440),(x+170,440),(x+75,555)]);text(d,(x,380),label,47)
  phrase(d,(1200,1390),'תווית מעבר: סיבית קלט ואחריה אירוע רשום','Transition label: input bit / registered event',lg,48)
  text(d,(1200,1510),'1100100101  ->  0000010010',62,color=GREEN,bold=True)
  save(im,288,'0010-overlap-fsm')
if __name__=='__main__':main()
