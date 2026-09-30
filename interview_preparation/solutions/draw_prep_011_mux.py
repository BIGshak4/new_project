"""Render two full MUX-only networks; I0 selected for S=0, I1 for S=1."""
from draw_prep_010_mod3_counters import Drawing, INK, GREEN, BLUE


def cell(d,x,y,name,select):
    d.d.polygon([(x*2,y*2),((x+200)*2,(y+35)*2),((x+200)*2,(y+225)*2),(x*2,(y+260)*2)],fill='#f6f9fc',outline=INK,width=6)
    d.text(x+100,y-55,name,29,bold=True,anchor='mt')
    d.text(x+15,y+53,'0',27)
    d.text(x+15,y+173,'1',27)
    d.text(x+165,y+111,'Q',27)
    d.text(x+100,y+212,'S',26,BLUE,anchor='mt')
    d.line([(x+100,y+242.5),(x+100,y+320)],BLUE)
    d.text(x+100,y+330,select,30,BLUE,bold=True,anchor='mt')


def input_wire(d,x,y,label):
    d.line([(x-130,y),(x,y)])
    d.text(x-115,y-42,label,30,GREEN,bold=True)


def draw_a():
    d=Drawing('Part (a) — a valid implementation with 3 MUXes','f = NOT(a AND b AND NOT c)   |   Only input signals, constants and ordinary 2:1 MUXes',1000)
    cell(d,280,330,'MUX 1','b')
    cell(d,810,400,'MUX 2','a')
    cell(d,1400,350,'MUX 3','c')
    input_wire(d,280,400,'1')
    input_wire(d,280,520,'0')
    input_wire(d,810,470,'1')
    d.line([(480,460),(650,460),(650,590),(810,590)])
    d.arrow(798,590)
    d.text(510,418,'NOT b',25,GREEN)
    d.line([(1010,530),(1195,530),(1195,420),(1400,420)])
    d.arrow(1388,420)
    d.text(1018,490,'NOT(a AND b)',25,GREEN)
    input_wire(d,1400,540,'1')
    d.line([(1600,480),(1780,480)],GREEN,4)
    d.arrow(1780,480,GREEN)
    d.text(1700,430,'f',33,GREEN,bold=True)
    d.text(65,820,'MUX 1 inverts b. MUX 2 forms NOT(a AND b). MUX 3 forces f=1 when c=1.',27)
    d.text(65,880,'For every MUX: S=0 selects input 0; S=1 selects input 1. No clock or storage.',26,BLUE)
    d.save('prep-011-three-mux.png')


def draw_b():
    d=Drawing('Part (b) — optimal implementation with 2 MUXes','f = NOT(a AND b AND NOT c)   |   No extra NOT, AND or OR gates',1000)
    cell(d,400,340,'MUX 1','b')
    cell(d,1090,390,'MUX 2','a')
    input_wire(d,400,410,'1')
    input_wire(d,400,530,'c')
    input_wire(d,1090,460,'1')
    d.line([(600,470),(810,470),(810,580),(1090,580)])
    d.arrow(1078,580)
    d.text(650,422,'t = (NOT b) OR c',27,GREEN)
    d.line([(1290,520),(1640,520)],GREEN,4)
    d.arrow(1640,520,GREEN)
    d.text(1490,467,'f',33,GREEN,bold=True)
    d.text(65,790,'a=0: output 1.    a=1, b=0: output 1.    a=1, b=1: output c.',28)
    d.text(65,850,'Only a=1, b=1, c=0 produces f=0. All other input combinations produce f=1.',26)
    d.text(65,912,'For every MUX: S=0 selects input 0; S=1 selects input 1. No clock or storage.',26,BLUE)
    d.save('prep-011-two-mux.png')


if __name__=='__main__':
    draw_a()
    draw_b()
