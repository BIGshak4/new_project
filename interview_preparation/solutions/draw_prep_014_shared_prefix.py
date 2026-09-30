"""Full shared-prefix circuit: seven OR cells and seven XOR cells."""
from draw_prep_010_mod3_counters import Drawing, INK, GREEN, BLUE

d=Drawing('Shared computation — 7 OR + 7 XOR gates',
          'p[i] = OR of x7 through xi.  y[i] = p[i] XOR p[i+1].  y7 = x7.',1810)
d.text(65,160,'Each drawn OR/XOR has TWO inputs. Wires and branches are not additional gates.',26,BLUE)
d.text(65,230,'x7 = p7',28,GREEN,bold=True)
d.line([(255,250),(1510,250)],GREEN,3)
d.arrow(1510,250,GREEN)
d.text(1540,229,'y7',29,GREEN,bold=True)
# A branch carries p7 to the first row; later rows carry their p[i] onward.
spine=560
d.d.ellipse(((spine-5)*2,245*2,(spine+5)*2,255*2),fill=INK)
last_y=250
for row,i in enumerate(range(6,-1,-1)):
    y=340+row*185
    # Rectangular functional gate symbols make two independent input pins clear.
    d.rect(650,y,200,100)
    d.text(750,y+30,'OR',30,bold=True,anchor='mt')
    d.line([(spine,last_y),(spine,y+72),(650,y+72)])
    d.line([(595,y+28),(650,y+28)])
    d.text(590,y-15,'x'+str(i),28,GREEN,bold=True)
    # Tap p[i+1] before the OR, for the XOR's upper input.
    d.d.ellipse(((spine-5)*2,(y-30-5)*2,(spine+5)*2,(y-30+5)*2),fill=INK)
    d.line([(spine,y-30),(1020,y-30),(1020,y+25),(1150,y+25)],BLUE)
    d.text(830,y-66,'p'+str(i+1),25,BLUE)
    # p[i] after the OR, to the XOR's lower input and the next row.
    d.line([(850,y+50),(950,y+50),(950,y+75),(1150,y+75)])
    d.text(871,y+10,'p'+str(i),25,GREEN,bold=True)
    d.d.ellipse((945*2,(y+50-5)*2,955*2,(y+50+5)*2),fill=INK)
    if i>0:
        d.line([(950,y+50),(950,y+140),(spine,y+140)])
    d.rect(1150,y,200,100)
    d.text(1250,y+30,'XOR',30,bold=True,anchor='mt')
    d.line([(1350,y+50),(1510,y+50)],GREEN,3)
    d.arrow(1510,y+50,GREEN)
    d.text(1540,y+28,'y'+str(i),29,GREEN,bold=True)
    last_y=y+140
d.line([(65,1680),(1835,1680)],'#d8e0e8',2)
d.text(65,1705,'The same prefix signal feeds one XOR and the next OR. Filled dots mark connected branches.',25)
d.text(65,1750,'Tradeoff: fewer cells than the unshared network, but a longer ripple path than the parallel-prefix design.',24)
d.save('prep-014-shared-prefix-xor.png')
