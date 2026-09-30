"""Expanded priority logic, showing the data and blocking condition for every bit."""
from draw_prep_010_mod3_counters import Drawing, INK, GREEN, BLUE

d=Drawing('Keep the first 1 from the MSB — all eight output bits',
          'Each output is 1 only if its input is 1 AND every higher input is 0.',1810)
d.text(65,160,'x7 is the MSB; x0 is the LSB. All rows operate in parallel, without a clock.',26,BLUE)
d.line([(400,240),(1580,240)],GREEN,3)
d.arrow(1580,240,GREEN)
d.text(330,220,'x7',28,GREEN,bold=True)
d.text(1620,220,'y7 = x7',28,GREEN,bold=True)

for row,bit in enumerate(range(6,-1,-1)):
    y=320+row*190
    # Direct bit goes to the upper AND input.
    d.line([(400,y+30),(1160,y+30)])
    d.text(330,y+10,'x'+str(bit),28,GREEN,bold=True)
    # Explicit variable-fan-in NOR block: bus annotation names every source bit.
    higher=', '.join('x'+str(j) for j in range(7,bit,-1))
    d.text(65,y+88,higher,24)
    d.line([(400,y+105),(540,y+105)])
    d.arrow(528,y+105)
    d.rect(540,y+65,360,90)
    d.text(720,y+74,'NOR of these higher bits',25,bold=True,anchor='mt')
    d.text(720,y+111,'1 only when ALL are 0',22,BLUE,anchor='mt')
    d.line([(900,y+105),(1040,y+105),(1040,y+90),(1160,y+90)],BLUE)
    # Standard AND gate, inputs at quarter/three-quarter height.
    x,w,h=1160,170,120
    d.line([(x,y+h),(x,y),(x+w-h/2,y)])
    d.d.arc(((x+w-h)*2,y*2,(x+w)*2,(y+h)*2),-90,90,fill=INK,width=6)
    d.line([(x+w-h/2,y+h),(x,y+h)])
    d.text(x+60,y+43,'AND',23,bold=True,anchor='mt')
    d.line([(x+w,y+60),(1580,y+60)],GREEN,3)
    d.arrow(1580,y+60,GREEN)
    d.text(1620,y+40,'y'+str(bit),30,GREEN,bold=True)

d.line([(65,1675),(1835,1675)],'#d8e0e8',2)
d.text(65,1700,'A one-input NOR is NOT. A multi-input NOR may be built from an OR tree followed by NOT.',25)
d.text(65,1746,'The listed higher bits connect to that row\'s NOR inputs. Labels refer to the SAME input vector x[7:0].',24)
d.save('prep-014-priority-gates.png')
