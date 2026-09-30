"""Render a full two-threshold-box network; OR annotations are not extra gates."""
from draw_prep_010_mod3_counters import Drawing, INK, GREEN, BLUE

d=Drawing('Four-input OR using two 2-of-4 threshold boxes','Allowed components: identical threshold boxes, wires, and constants 0 / 1 only',1000)

def block(x,y,name):
    d.rect(x,y,300,360)
    d.text(x+150,y+18,name,30,bold=True,anchor='mt')
    d.text(x+150,y+132,'Output = 1',27,anchor='mt')
    d.text(x+150,y+176,'when at least',25,anchor='mt')
    d.text(x+150,y+216,'2 inputs are 1',25,anchor='mt')
    for i,offset in enumerate((65,145,225,305)):
        d.text(x+15,y+offset-16,'I'+str(i),22)

def incoming(x,y,label):
    d.line([(x-155,y),(x,y)])
    d.text(x-145,y-38,label,30,GREEN,bold=True)

block(340,300,'BOX 1')
for label,offset in zip(('a','b','c','1'),(65,145,225,305)):
    incoming(340,300+offset,label)
block(1150,300,'BOX 2')
d.line([(640,480),(890,480),(890,365),(1150,365)])
d.arrow(1138,365)
d.text(665,430,'t = a OR b OR c',27,GREEN)
for label,offset in zip(('d','1','0'),(145,225,305)):
    incoming(1150,300+offset,label)
d.line([(1450,480),(1770,480)],GREEN,4)
d.arrow(1770,480,GREEN)
d.text(1510,421,'f = a OR b OR c OR d',27,GREEN,bold=True)
d.text(65,780,'BOX 1 already has one constant 1: any one of a,b,c makes its output 1.',28)
d.text(65,840,'BOX 2 already has one constant 1: either t=1 or d=1 makes its output 1.',28)
d.text(65,910,'OR labels describe the resulting signals. There are no additional OR gates, clock or storage.',25,BLUE)
d.save('prep-013-two-threshold-boxes.png')
