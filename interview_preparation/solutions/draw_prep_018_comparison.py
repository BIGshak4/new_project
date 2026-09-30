"""Two unsigned N=2 designs, with identical final data selectors."""
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, PURPLE

def selectors(d):
    d.text(65,825,'Select the ORIGINAL 2-bit number (same output stage in both designs)',29,bold=True)
    for x,i in [(360,1),(1160,0)]:
        y=990
        d.rect(x,y,240,170)
        d.text(x+120,y+58,'MUX 2:1',28,bold=True,anchor='mt')
        for name,dy,pin in [(f'A{i}',35,'0'),(f'B{i}',130,'1')]:
            d.text(x-140,y+dy-20,name,27,BLUE,bold=True)
            d.line([(x-80,y+dy),(x,y+dy)],BLUE)
            d.text(x+14,y+dy-18,pin,24)
        d.line([(x+120,y-75),(x+120,y)],PURPLE)
        d.text(x+150,y-62,'S',28,PURPLE,bold=True)
        d.line([(x+240,y+85),(x+430,y+85)],GREEN)
        d.arrow(x+430,y+85,GREEN)
        d.text(x+290,y+44,f'M{i}',28,GREEN,bold=True)
    d.text(65,1230,'S=0 selects A1A0. S=1 selects B1B0. Matching labels are the same wires. No clock or FF.',25)

def recursive():
    d=Drawing('N=2: divide-and-conquer comparison + selection',
              'Unsigned A=A1A0 and B=B1B0 (0..3). LT means less-than; EQ means equal.',1310)
    d.text(65,160,'Compare each bit pair',29,bold=True)
    for i,y in [(1,250),(0,500)]:
        d.rect(260,y,550,170)
        d.text(535,y+15,('HIGH' if i else 'LOW')+' bit comparator',28,bold=True,anchor='mt')
        d.text(295,y+64,f'LT{i} = NOT(A{i}) AND B{i}',27)
        d.text(295,y+113,('EQ1 = A1 XNOR B1' if i else 'EQ0 is not needed for this final max'),25)
        for name,dy in [(f'A{i}',60),(f'B{i}',125)]:
            d.text(85,y+dy-20,name,28,BLUE,bold=True)
            d.line([(145,y+dy),(260,y+dy)],BLUE)
        d.line([(810,y+75),(940,y+75)],PURPLE)
        d.arrow(940,y+75,PURPLE)
        d.text(840,y+35,f'LT{i}',25,PURPLE,bold=True)
        if i:
            d.line([(810,y+135),(940,y+135)],GREEN)
            d.arrow(940,y+135,GREEN)
            d.text(840,y+143,'EQ1',25,GREEN,bold=True)
    d.text(1030,160,'Combine the two comparisons',29,bold=True)
    d.rect(1190,440,180,135)
    d.text(1280,486,'AND',29,bold=True,anchor='mt')
    for label,yy,col in [('EQ1',475,GREEN),('LT0',540,PURPLE)]:
        d.text(1020,yy-21,label,26,col,bold=True)
        d.line([(1110,yy),(1190,yy)],col)
    d.rect(1510,280,170,145)
    d.text(1595,332,'OR',30,bold=True,anchor='mt')
    d.text(1280,299,'LT1',26,PURPLE,bold=True)
    d.line([(1360,320),(1510,320)],PURPLE)
    d.line([(1370,507),(1440,507),(1440,390),(1510,390)])
    d.line([(1680,350),(1810,350)],PURPLE)
    d.arrow(1810,350,PURPLE);d.text(1715,304,'S',29,PURPLE,bold=True)
    d.text(1020,635,'S = LT1 OR (EQ1 AND LT0)',27)
    d.text(65,742,'The LOW bit decides only when the HIGH bits are equal. If A=B, S=0.',27)
    selectors(d)
    d.save('prep-018-n2-recursive.png')

def subtractor():
    d=Drawing('N=2: extended subtraction + selection',
              'Unsigned A=A1A0 and B=B1B0 (0..3). Prepend ZERO to each input before subtraction.',1310)
    d.rect(570,255,670,350)
    d.text(905,280,'3-bit subtractor',36,bold=True,anchor='mt')
    d.text(905,345,'D[2:0] = {0,A1,A0} - {0,B1,B0}',29,anchor='mt')
    d.text(905,425,'Exact difference: -3 through +3',28,anchor='mt')
    d.text(905,490,'D2=1 iff the difference is negative',27,anchor='mt')
    for label,yy in [('Aext = 0 A1 A0',390),('Bext = 0 B1 B0',525)]:
        d.text(90,yy-45,label,29,BLUE,bold=True)
        d.line([(90,yy),(570,yy)],BLUE,4)
        d.text(450,yy+10,'/3',24,BLUE)
    d.line([(1240,340),(1750,340)],PURPLE)
    d.arrow(1750,340,PURPLE)
    d.text(1340,293,'D2 = S = (A < B)',28,PURPLE,bold=True)
    for label,yy in [('D1',455),('D0',540)]:
        d.line([(1240,yy),(1440,yy)])
        d.text(1280,yy-40,label,25)
        d.text(1480,yy-20,'unused',26)
    d.text(65,665,'Example: A=01 (1), B=10 (2): 001 - 010 = 111 (-1). D2=1 -> select B.',28)
    d.text(65,715,'Only D2 is needed. A synthesis tool may remove the unused difference-bit logic.',26)
    selectors(d)
    d.save('prep-018-n2-subtractor.png')

if __name__=='__main__':
    recursive()
    subtractor()
