"""Four-stage vector datapath; all fixed shifts are wiring, not storage."""
from draw_prep_010_mod3_counters import Drawing, INK, GREEN, BLUE

d=Drawing('Keep only the highest set bit','8-bit combinational datapath: spread the leading 1 downward, then isolate the boundary',950)
d.text(65,185,'Example: x = 10000000',30,bold=True)
stages=[(180,'s1','x OR (x >> 1)','11000000'),
        (600,'s2','s1 OR (s1 >> 2)','11110000'),
        (1020,'s3','s2 OR (s2 >> 4)','11111111'),
        (1440,'y','s3 XOR (s3 >> 1)','10000000')]
for i,(x,name,formula,value) in enumerate(stages):
    d.rect(x,340,280,210)
    d.text(x+140,365,name,34,bold=True,anchor='mt')
    d.text(x+140,438,formula,25,anchor='mt')
    d.text(x+140,486,'8-bit vector logic',22,BLUE,anchor='mt')
    d.line([(x-90,445),(x,445)],width=4)
    d.arrow(x-12,445)
    if i>0:
        d.line([(stages[i-1][0]+280,445),(x-90,445)],width=4)
    d.text(x+140,598,value,30,GREEN,bold=True,anchor='mt')
d.text(88,400,'x',29,GREEN,bold=True)
d.line([(1720,445),(1830,445)],GREEN,4)
d.arrow(1830,445,GREEN)
d.text(1780,400,'y',29,GREEN,bold=True)
d.text(65,725,'Each shift is a FIXED, zero-filled rewiring. Each vector OR/XOR acts separately on the eight bits.',25)
d.text(65,775,'No clock, flip-flop, variable shifter or encoded bit index is needed. Input 00000000 gives output 00000000.',25)
d.text(65,835,'Source example: 00101011  ->  00100000. The output is an 8-bit mask, not the index 5.',27,GREEN)
d.save('prep-014-isolate-msb.png')
