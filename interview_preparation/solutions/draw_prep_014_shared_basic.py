"""Explicit net-labelled 20-cell AND/OR/NOT implementation."""
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN

d=Drawing('Shared logic — 6 OR + 7 NOT + 7 AND = 20 gates',
          'Hi = any 1 ABOVE bit i.  yi = xi AND NOT(Hi).  H6 = x7.  y7 = x7.',1590)
d.text(65,148,'Matching signal names are connected wires. Every OR and AND has two inputs.',25,BLUE)
d.text(65,198,'Build the shared higher-bit flags',30,bold=True)
d.text(1020,198,'Allow xi through only when Hi = 0',30,bold=True)
for row,i in enumerate(range(6,-1,-1)):
    y=295+row*163
    if i>0:
        d.rect(290,y,180,90)
        d.text(380,y+26,'OR',29,bold=True,anchor='mt')
        for name,dy in [(f'H{i}',22),(f'x{i}',68)]:
            d.text(100,y+dy-19,name,28,BLUE)
            d.line([(163,y+dy),(290,y+dy)])
        d.line([(470,y+45),(720,y+45)])
        d.arrow(720,y+45)
        d.text(740,y+25,f'H{i-1}',28,GREEN,bold=True)
    else:
        d.text(100,y+5,'No H-1 needed:',26,bold=True)
        d.text(100,y+45,'there is no bit below x0.',26)
    d.text(935,y+6,f'H{i}',28,BLUE)
    d.line([(995,y+25),(1040,y+25)])
    d.rect(1040,y,145,50)
    d.text(1112,y+7,'NOT',27,bold=True,anchor='mt')
    d.line([(1185,y+25),(1320,y+25)])
    d.rect(1320,y,170,100)
    d.text(1405,y+32,'AND',28,bold=True,anchor='mt')
    d.text(1110,y+63,f'x{i}',28,BLUE)
    d.line([(1185,y+80),(1320,y+80)])
    d.line([(1490,y+50),(1650,y+50)],GREEN)
    d.arrow(1650,y+50,GREEN)
    d.text(1680,y+30,f'y{i}',28,GREEN,bold=True)
d.line([(65,1460),(1835,1460)],'#d8e0e8',2)
d.text(65,1490,'Direct wires: H6 = x7 and y7 = x7. No clock or flip-flops. Shared flags are computed only once.',25)
d.save('prep-014-shared-and-or-not.png')
