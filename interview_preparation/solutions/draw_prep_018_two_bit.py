"""Unsigned max(A1A0,B1B0): high-bit priority comparator and shared mux select."""
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, PURPLE
d=Drawing('2-bit unsigned maximum: compare, then select',
          'A = A1 A0, B = B1 B0.  S = 1 when A < B.  The same S controls BOTH output bits.',1390)
d.text(65,155,'1. Equality of the HIGH bits',28,bold=True)
d.rect(255,260,240,130)
d.text(375,280,'XNOR',32,bold=True,anchor='mt')
d.text(375,328,'1 if inputs equal',23,anchor='mt')
for label,y in [('A1',290),('B1',360)]:
    d.text(80,y-19,label,27,BLUE,bold=True)
    d.line([(140,y),(255,y)],BLUE)
d.line([(495,325),(615,325)],GREEN)
d.arrow(615,325,GREEN);d.text(530,282,'E1',28,GREEN,bold=True)
d.text(65,445,'E1 = 1 when A1 = B1',25,GREEN)
d.text(65,485,'Only then may the LOW bits decide.',23)

d.text(680,155,'2. Is B larger than A?',28,bold=True)
# Top path: NOT A1 AND B1.
d.rect(700,245,130,60);d.text(765,258,'NOT',26,bold=True,anchor='mt')
d.text(610,255,'A1',27,BLUE,bold=True);d.line([(665,275),(700,275)],BLUE)
d.rect(970,245,170,110);d.text(1055,282,'AND',29,bold=True,anchor='mt')
d.line([(830,275),(970,275)])
d.text(845,310,'B1',27,BLUE,bold=True);d.line([(905,325),(970,325)],BLUE)
d.line([(1140,300),(1240,300),(1240,410),(1320,410)])
d.text(1163,259,'T1',26,PURPLE,bold=True)
# Bottom path: E1 AND NOT A0 AND B0.
d.rect(970,495,170,140);d.text(1055,540,'AND',29,bold=True,anchor='mt')
d.text(845,502,'E1',27,GREEN,bold=True);d.line([(905,525),(970,525)],GREEN)
d.rect(700,535,130,60);d.text(765,548,'NOT',26,bold=True,anchor='mt')
d.text(610,545,'A0',27,BLUE,bold=True);d.line([(665,565),(700,565)],BLUE)
d.line([(830,565),(970,565)])
d.text(845,586,'B0',27,BLUE,bold=True);d.line([(905,605),(970,605)],BLUE)
d.line([(1140,565),(1240,565),(1240,490),(1320,490)])
d.text(1163,577,'T0',26,PURPLE,bold=True)
d.rect(1320,370,170,160);d.text(1405,428,'OR',30,bold=True,anchor='mt')
d.line([(1490,450),(1780,450)],PURPLE)
d.arrow(1780,450,PURPLE);d.text(1540,399,'S = (A < B)',28,PURPLE,bold=True)
d.text(680,690,'S = (NOT A1 AND B1) OR (E1 AND NOT A0 AND B0)',25)

d.text(65,785,'3. Select the ORIGINAL number using two 1-bit MUXes',29,bold=True)
for x,i in [(380,1),(1180,0)]:
    y=955
    d.rect(x,y,220,180)
    d.text(x+110,y+65,'MUX 2:1',28,bold=True,anchor='mt')
    for name,dy,pin in [(f'A{i}',40,'0'),(f'B{i}',135,'1')]:
        d.text(x-170,y+dy-20,name,28,BLUE,bold=True)
        d.line([(x-105,y+dy),(x,y+dy)],BLUE)
        d.text(x+15,y+dy-18,pin,24)
    d.line([(x+110,y-75),(x+110,y)],PURPLE)
    d.text(x+140,y-64,'S',28,PURPLE,bold=True)
    d.line([(x+220,y+90),(x+435,y+90)],GREEN)
    d.arrow(x+435,y+90,GREEN)
    d.text(x+285,y+44,f'M{i}',29,GREEN,bold=True)
d.text(65,1200,'S=0: M1M0=A1A0.   S=1: M1M0=B1B0.   Ties select A.   No clock or memory.',27)
d.text(65,1250,'Repeated labels are the same wires. The 3-input AND may be built from two 2-input AND gates.',25)
d.text(65,1300,'For a recursive comparator, also export EQ = E1 AND XNOR(A0,B0). The max output alone is not enough.',24)
d.save('prep-018-two-bit-maximum.png')
