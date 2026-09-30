"""Seven specified A/B cells, with each output-joining net explicit."""
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN
d=Drawing('XOR using seven A/B components',
          'A(u,v): drives 1 only on 00.  B(u,v): drives 0 only on 11.  Otherwise the output is Z.',1210)
d.text(70,170,'Stage 1: fully driven n = NOT(x OR y)',29,bold=True)
d.text(990,170,'Stage 2: fully driven f = x XOR y',29,bold=True)

def cell(x,y,name,a,b,kind):
    d.rect(x,y,200,100)
    d.text(x+100,y+19,name,31,bold=True,anchor='mt')
    d.text(x+100,y+61,kind,20,anchor='mt')
    for dy,label in [(25,a),(75,b)]:
        d.text(x-100,y+dy-18,label,27,BLUE,bold=True)
        d.line([(x-50,y+dy),(x,y+dy)])

for row,(name,a,b,kind) in enumerate([
    ('A1','x','y','00 -> 1'),('B1','x','x','11 -> 0'),('B2','y','y','11 -> 0')]):
    y=285+row*230
    cell(250,y,name,a,b,kind)
    d.line([(450,y+50),(720,y+50)])
    d.d.ellipse((715*2,(y+45)*2,725*2,(y+55)*2),fill=INK)
d.line([(720,335),(720,795)])
d.line([(720,565),(845,565)],GREEN)
d.arrow(845,565,GREEN); d.text(864,543,'n',31,GREEN,bold=True)

for row,(name,a,b,kind) in enumerate([
    ('A2','x','n','00 -> 1'),('A3','y','n','00 -> 1'),
    ('B3','x','y','11 -> 0'),('B4','n','n','11 -> 0')]):
    y=260+row*220
    cell(1220,y,name,a,b,kind)
    d.line([(1420,y+50),(1650,y+50)])
    d.d.ellipse((1645*2,(y+45)*2,1655*2,(y+55)*2),fill=INK)
d.line([(1650,310),(1650,970)])
d.line([(1650,640),(1775,640)],GREEN)
d.arrow(1775,640,GREEN); d.text(1795,620,'f',31,GREEN,bold=True)
d.line([(70,1065),(1830,1065)],'#d8e0e8',2)
d.text(70,1100,'Identical labels denote the same net. Each n input is connected to the RESOLVED stage-1 output.',25)
d.text(70,1145,'The vertical lines join outputs; they are wires, not OR gates. No floating or conflicting net in any stable input case.',24)
d.save('prep-015-tristate-xor.png')
