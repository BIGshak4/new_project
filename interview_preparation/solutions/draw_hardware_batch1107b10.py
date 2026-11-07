"""Deterministic localized supplementary teaching diagrams."""
from draw_prep_016_064 import BLUE, GREEN, OUT, PURPLE, box, phrase, text, wire
from PIL import Image, ImageDraw


def main():
 for lg in ('he','en'):
  def frame(he,en,lg=lg):
   im=Image.new('RGB',(2000,1250),'white');d=ImageDraw.Draw(im)
   phrase(d,(1000,85),he,en,lg,57,bold=True);return im,d
  def save(im,n,label,lg=lg):im.save(OUT/f'prep-{n:03d}-{label}-batch1107b10-{lg}.png')
  im,d=frame('אחד בחלון של אלף דגימות','Any one in the latest thousand samples')
  box(d,(410,280,1590,770));text(d,(1000,380),'remaining[9:0]',64,bold=True)
  for y,s in [(500,'x=1: 1000'),(600,'x=0: max(remaining-1, 0)'),(700,'rst=1: 0')]:text(d,(1000,y),s,50)
  wire(d,[(80,520),(410,520)]);text(d,(200,445),'x',55)
  wire(d,[(1590,520),(1850,520)]);text(d,(1730,445),'y',55)
  text(d,(1000,900),'y = (remaining > 0)',59,color=GREEN,bold=True)
  phrase(d,(1000,1050),'הסיבית הנוכחית נכללת בחלון','The current sample is included',lg,49)
  save(im,95,'window1000')
  im,d=frame('חלוקה בארבע עם הוספת סיבית מימין','Divide by four with a bit appended on the right')
  wire(d,[(120,530),(450,530)]);text(d,(240,455),'b',55)
  for x,label in [(450,'q0'),(1120,'q1')]:
   box(d,(x,390,x+370,670));text(d,(x+185,530),label,76,bold=True)
  wire(d,[(820,530),(1120,530)]);text(d,(970,455),'old q0',49)
  text(d,(1000,830),'suffix_next = {q0, b}',57,color=BLUE)
  text(d,(1000,950),'divisible = seen AND (q1=q0=0)',53,color=GREEN)
  phrase(d,(1000,1080),'איפוס: שתי סיביות אפס ודגל ריק','Reset: two zero bits and an empty flag',lg,48)
  save(im,206,'serial-four')
  im,d=frame('מקסימום של שני קלטים בני שתי סיביות','Maximum of two unsigned two-bit inputs')
  text(d,(1000,250),'t = a0 OR b0        y1 = a1 OR b1',62,color=GREEN)
  rows=[('a1 b1','y0'),('0  0','a0 OR b0'),('0  1','b0'),('1  0','a0'),('1  1','a0 OR b0')]
  for k,(left,right) in enumerate(rows):
   y=410+k*125;box(d,(390,y-55,1610,y+55));text(d,(650,y),left,55,bold=k==0);text(d,(1260,y),right,55,bold=k==0)
  phrase(d,(1000,1120),'שלושה בוחרים ושני שערי או','Three multiplexers and two OR gates',lg,48)
  save(im,18,'two-bit-max')
  im,d=frame('תור בן ארבעה תאים עם לחיצת יד','Four-cell FIFO with ready / valid handshakes')
  for k in range(4):box(d,(590,260+k*145,1410,390+k*145));text(d,(1000,325+k*145),f'mem[{k}]: W bits',49)
  text(d,(310,400),'in_valid',46);text(d,(310,470),'in_ready',46);text(d,(1690,400),'out_valid',46);text(d,(1690,470),'out_ready',46)
  wire(d,[(180,600),(590,600)]);wire(d,[(1410,600),(1820,600)])
  text(d,(1000,970),'count: 0..4      rptr, wptr: 0..3',52,color=PURPLE)
  phrase(d,(1000,1090),'החלפה בתור מלא מותרת רק עם קריאה מאושרת','Full replacement requires an accepted read',lg,45)
  save(im,67,'ready-valid-four')
  im,d=frame('שני סדרי קלט ושני פירושים למצב','Two input orders and two state meanings')
  for y,kind,formula,he,en in [(320,'MSB first','r_next = (2*r + b) mod 5','המצב הוא השארית הרגילה','State is the ordinary remainder'),(760,'LSB first','s_next = 3*(s + b) mod 5','המצב הוא שארית מנורמלת','State is a normalized remainder')]:
   box(d,(130,y-100,1870,y+260));text(d,(1000,y),kind,59,bold=True,color=BLUE)
   text(d,(1000,y+100),formula,61,color=GREEN);phrase(d,(1000,y+200),he,en,lg,45)
  text(d,(1000,1170),'output = (state == 0)',52,color=PURPLE)
  save(im,50,'mod-five-orders')
  im,d=frame('אילוצי סודוקו ללוח פתרון שלם','Sudoku constraints for a complete solution grid')
  x0,y0,cell=220,250,85
  for r in range(9):
   for c in range(9):
    col='#e6f2ef' if (r//3+c//3)%2==0 else '#edf2fa'
    d.rectangle((x0+c*cell,y0+r*cell,x0+(c+1)*cell,y0+(r+1)*cell),fill=col,outline=BLUE,width=2)
    text(d,(x0+(c+.5)*cell,y0+(r+.5)*cell),str((r*3+r//3+c)%9+1),44)
  for k in (0,3,6,9):
   d.line((x0+k*cell,y0,x0+k*cell,y0+9*cell),fill=BLUE,width=7);d.line((x0,y0+k*cell,x0+9*cell,y0+k*cell),fill=BLUE,width=7)
  for y,he,en in [(380,'ערכים מאחד עד תשע','Values one through nine'),(570,'שורות ללא חזרות','No repeats in a row'),(760,'עמודות ללא חזרות','No repeats in a column'),(950,'תשעה אזורים ללא חזרות','Nine boxes without repeats')]:phrase(d,(1450,y),he,en,lg,42,bold=True)
  phrase(d,(1000,1150),'איור דוגמה בלבד; הפתרון מגריל לוחות','Illustration only; the solution randomizes grids',lg,43)
  save(im,272,'sudoku-constraints')
if __name__=='__main__':main()
