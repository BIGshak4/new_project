"""Full two-multiplier alternative and its ideal arrival-time diagram."""
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, PURPLE

d=Drawing('Compute BOTH possible products in parallel, then select',
          'Extra hardware: TWO multipliers instead of one. Output = B*C if S=0, or A*D if S=1.',1530)

def register(x,y,label,endpoint):
    d.rect(x,y,130,75)
    d.text(x+65,y+19,label,29,bold=True,anchor='mt')
    d.line([(x+130,y+37),endpoint],BLUE,3)

# E/F launch into the unchanged black box.
register(95,215,'E',(450,252))
register(95,335,'F',(450,372))
d.rect(450,190,410,245)
d.text(655,228,'Black box',35,bold=True,anchor='mt')
d.text(655,290,'3.0 ns',32,PURPLE,bold=True,anchor='mt')
d.text(655,358,'same function as before',23,anchor='mt')
d.line([(860,310),(1470,310),(1470,650)],PURPLE,4)
d.text(1070,252,'S ready at t = 3.0 ns',29,PURPLE,bold=True)
d.text(1500,535,'Select S',26,PURPLE,bold=True)

# Both products start immediately from the original operand registers.
for names,y,formula in [(('B','C'),550,'P0 = B * C'),(('A','D'),875,'P1 = A * D')]:
    register(95,y+15,names[0],(450,y+52))
    register(95,y+125,names[1],(450,y+162))
    d.rect(450,y,410,225)
    d.text(655,y+25,'Multiplier',34,bold=True,anchor='mt')
    d.text(655,y+91,formula,31,BLUE,bold=True,anchor='mt')
    d.text(655,y+161,'2.7 ns',29,anchor='mt')

d.line([(860,662),(1190,662),(1190,725),(1360,725)],BLUE,4)
d.text(900,609,'P0 ready at 2.7 ns',26,BLUE,bold=True)
d.line([(860,987),(1190,987),(1190,885),(1360,885)],BLUE,4)
d.text(900,1003,'P1 ready at 2.7 ns',26,BLUE,bold=True)

d.rect(1360,650,220,315)
d.text(1470,766,'MUX',32,bold=True,anchor='mt')
d.text(1470,813,'1.5 ns',27,anchor='mt')
d.text(1377,705,'0',27)
d.text(1377,865,'1',27)
d.line([(1580,805),(1810,805)],GREEN,4)
d.arrow(1810,805,GREEN)
d.text(1620,735,'Output',30,GREEN,bold=True)
d.text(1610,845,'ready at',25,GREEN)
d.text(1610,886,'4.5 ns',32,GREEN,bold=True)

d.line([(65,1150),(1835,1150)],'#d8e0e8',2)
d.text(65,1175,'All three computations start together at t=0 (register outputs available).',27,bold=True)
x0=400; scale=280
for label,y,start,end,col in [('Both products',1270,0,2.7,BLUE),('Black box / S',1340,0,3,PURPLE),('Final MUX',1410,3,4.5,GREEN)]:
    d.text(65,y-14,label,25,col,bold=True)
    d.line([(x0,y),(x0+4.5*scale,y)],'#d8e0e8',2)
    d.line([(x0+start*scale,y),(x0+end*scale,y)],col,18)
for value,label in [(0,'0'),(2.7,'2.7'),(3,'3.0'),(4.5,'4.5 ns')]:
    xx=x0+value*scale
    d.line([(xx,1240),(xx,1435)],'#8c99a5',1)
    d.text(xx,1450,label,24,anchor='mt')
d.save('prep-020-parallel-products.png')
