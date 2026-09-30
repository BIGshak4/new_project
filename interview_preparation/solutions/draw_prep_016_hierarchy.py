"""Complete net-labelled block schematics for the five-/four-controller options."""
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, PURPLE

def draw(use_fifth):
    title=('16-input priority encoder: 5 controllers + a 2-bit-wide MUX' if use_fifth else
           '16-input priority encoder: 4 controllers + group logic + MUX')
    d=Drawing(title,'Priority: In15 highest, In0 lowest. Matching net names connect; /2 and /4 mark bus widths.',1550)
    d.text(65,160,'1. Four local winners',29,bold=True)
    d.text(975,160,'2. Select the highest active GROUP',29,bold=True)
    for g in range(4):
        y=250+g*210
        d.rect(260,y,330,145)
        d.text(425,y+20,'Controller C'+str(g),27,bold=True,anchor='mt')
        d.text(425,y+68,'local inputs 0..3',25,anchor='mt')
        d.text(425,y+105,'group '+str(g),23,anchor='mt')
        d.text(65,y+37,f'In{4*g}..In{4*g+3}',23,BLUE,bold=True)
        d.line([(65,y+80),(260,y+80)],BLUE,4)
        d.text(180,y+85,'/4',23,BLUE)
        d.line([(590,y+48),(755,y+48)],GREEN)
        d.arrow(755,y+48,GREEN)
        d.text(625,y+10,'V'+str(g)+' (Y)',23,GREEN,bold=True)
        d.line([(590,y+110),(755,y+110)],BLUE,4)
        d.arrow(755,y+110,BLUE)
        d.text(620,y+119,'K'+str(g)+'[1:0]',23,BLUE,bold=True)
    d.rect(1120,255,410,290)
    if use_fifth:
        d.text(1325,275,'Controller C4',29,bold=True,anchor='mt')
        for g in range(4):
            yy=335+g*53
            d.text(990,yy-19,'V'+str(g),26,GREEN,bold=True)
            d.line([(1050,yy),(1120,yy)],GREEN)
            d.text(1134,yy-15,'In'+str(g),23)
        d.text(1440,329,'Y',24)
        d.text(1410,416,'Z[1:0]',23)
    else:
        d.text(1325,275,'Group selection logic',26,bold=True,anchor='mt')
        for g in range(4):
            yy=335+g*53
            d.text(990,yy-19,'V'+str(g),26,GREEN,bold=True)
            d.line([(1050,yy),(1120,yy)],GREEN)
        d.text(1140,330,'Y = V0 OR V1 OR V2 OR V3',21)
        d.text(1140,390,'G1 = V3 OR V2',23)
        d.text(1140,444,'G0 = V3 OR (V1 AND NOT V2)',21)
    d.line([(1530,350),(1745,350)],GREEN)
    d.arrow(1745,350,GREEN)
    d.text(1645,310,'Y',29,GREEN,bold=True)
    d.line([(1530,435),(1745,435)],PURPLE,4)
    d.arrow(1745,435,PURPLE)
    d.text(1570,454,'G[1:0] = group',24,PURPLE,bold=True)

    d.text(975,620,'3. Route that group\'s LOCAL code',29,bold=True)
    d.rect(1160,750,330,300)
    d.text(1325,770,'MUX 4:1',30,bold=True,anchor='mt')
    d.text(1325,811,'2-bit data',25,anchor='mt')
    for g in range(4):
        yy=863+g*48
        d.text(950,yy-20,'K'+str(g)+'[1:0]',25,BLUE,bold=True)
        d.line([(1090,yy),(1160,yy)],BLUE,4)
        d.text(1175,yy-17,'D'+str(g),23)
    d.line([(1325,675),(1325,750)],PURPLE,4)
    d.text(1350,700,'Select = G[1:0]',25,PURPLE,bold=True)
    d.line([(1490,900),(1745,900)],BLUE,4)
    d.arrow(1745,900,BLUE)
    d.text(1555,862,'L[1:0]',26,BLUE,bold=True)

    d.text(65,1130,'4. Combine GROUP and LOCAL position',29,bold=True)
    d.rect(410,1210,1080,190)
    d.text(950,1233,'Raw index = { G[1:0], L[1:0] }',34,bold=True,anchor='mt')
    d.text(950,1285,'P[3:0] = Y ? Raw index : 0000',29,anchor='mt')
    d.text(950,1340,'Concatenation is wiring. Zeroing when Y=0 can use four AND gates.',25,anchor='mt')
    for label,yy,col in [('G[1:0]',1250,PURPLE),('L[1:0]',1300,BLUE),('Y',1350,GREEN)]:
        d.text(190,yy-17,label,25,col,bold=True)
        d.line([(320,yy),(410,yy)],col,3)
    d.line([(1490,1290),(1725,1290)],BLUE,4)
    d.arrow(1725,1290,BLUE)
    d.text(1580,1250,'P[3:0]',27,BLUE,bold=True)
    d.text(65,1465,'Example: requests 2, 6, 13 -> V[3:0]=1011 -> G=11, L=01 -> P=1101 (13), Y=1.',27)
    d.save('prep-016-'+('five-controllers' if use_fifth else 'four-controllers')+'.png')

if __name__=='__main__':
    draw(True)
    draw(False)
