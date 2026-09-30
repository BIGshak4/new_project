"""Draw the complete Q-only divide-by-three schematic as a reusable PNG.

Repeated clk/rst_n labels are connected nets, as in a conventional schematic.
Signal wiring matches prep_010_divide_by_three.sv exactly.
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
S = 2
im = Image.new('RGB', (2000*S, 1400*S), 'white')
d = ImageDraw.Draw(im)
INK, BLUE, PURPLE, GREEN = '#26374a', '#1267b1', '#8054ad', '#087f70'
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
COMPLEMENTED = '--and' in sys.argv


def text(x, y, label, size=26, color=INK, bold=False, anchor=None):
    d.text((x*S, y*S), label, fill=color,
           font=ImageFont.truetype(BOLD if bold else FONT, size*S), anchor=anchor)


def line(points, color=INK, width=3):
    d.line([(x*S,y*S) for x,y in points], fill=color, width=width*S,
           joint='curve')


def circle(x, y, r, fill='white', color=INK):
    d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S), fill=fill,
              outline=color, width=3*S)


def dot(x, y):
    circle(x, y, 6, INK)


def arrow(x, y, color=INK):
    d.polygon([(x*S,y*S),((x-12)*S,(y-7)*S),((x-12)*S,(y+7)*S)], fill=color)


def bezier(points):
    a,b,c,e = points
    result = []
    for i in range(101):
        t = i/100
        result.append(tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]
                            +3*(1-t)*t*t*c[k]+t**3*e[k] for k in (0,1)))
    return result


def or_gate(x,y,w=180,h=140,inverted=False):
    # OR outline, including the curved input side.
    line(bezier([(x,y),(x+w*.58,y),(x+w*.86,y+h*.18),(x+w,y+h/2)]))
    line(bezier([(x+w,y+h/2),(x+w*.86,y+h*.82),(x+w*.58,y+h),(x,y+h)]))
    line(bezier([(x,y+h),(x+w*.30,y+h*.67),(x+w*.30,y+h*.33),(x,y)]))
    # At quarter height the curved back reaches x + 0.16875*w.
    for iy in (y+h*.25,y+h*.75):
        line([(x-25,iy),(x+w*.17,iy)])
    if inverted:
        circle(x+w+8,y+h/2,8)
    return x+w+(16 if inverted else 0),y+h/2


def and_gate(x,y,w=180,h=140):
    line([(x,y+h),(x,y),(x+w-h/2,y)])
    d.arc(((x+w-h)*S,y*S,(x+w)*S,(y+h)*S),-90,90,fill=INK,width=3*S)
    line([(x+w-h/2,y+h),(x,y+h)])
    for iy in (y+h*.25,y+h*.75):
        line([(x-25,iy),(x,iy)])


def ff(x,y,name,edge,q_name):
    w,h=250,240
    d.rectangle((x*S,y*S,(x+w)*S,(y+h)*S), fill='#f6f9fc',outline=INK,width=3*S)
    text(x+w/2,y+15,name,29,bold=True,anchor='mt')
    text(x+14,y+48,'D',27)
    has_qn = COMPLEMENTED and name in ('FF1','FF0')
    text(x+w-55,y+48,'Q_N' if has_qn else 'Q',23)
    if has_qn:
        circle(x+w+8,y+60,8)
        text(x+w-35,y+98,'Q',27)
    text(x+w/2,y+98,'D flip-flop',24,anchor='mt')
    text(x+w/2,y+130,edge+' edge',23,BLUE,anchor='mt')
    cy=y+180
    line([(x,cy-12),(x+18,cy),(x,cy+12)],BLUE)
    if edge == 'Falling':
        circle(x-8,cy,8,color=BLUE)
        line([(x-68,cy),(x-16,cy)],BLUE)
    else:
        line([(x-68,cy),(x,cy)],BLUE)
    text(x-68,cy-32,'clk',23,BLUE)
    rx=x+160
    text(rx,y+h-34,'CLR',22,PURPLE,anchor='mt')
    circle(rx,y+h+8,8,color=PURPLE)
    line([(rx,y+h+16),(rx,y+h+58)],PURPLE)
    text(rx,y+h+63,'rst_n',23,PURPLE,anchor='mt')
    text(x+w+18,y+20,name.lower().replace('ff','q')+'_N' if has_qn else q_name,27,GREEN,bold=True)
    if has_qn:
        text(x+w+12,y+78,q_name,27,GREEN,bold=True)


text(70,30,'Divide by 3 — '+('AND + complementary Q outputs' if COMPLEMENTED else 'complete circuit'),44,bold=True)
text(70,91,'Input: clk with 50% duty   |   Output: f_in / 3, 50% duty in the ideal timing model',27)

# The counter outputs return to the NOR inputs by separate, uncrossed wires.
line([(1316 if COMPLEMENTED else 1300,440),(1390,440),(1390,175),(125,175),(125,475),(275,475)])
text(680,140,'q0_N feedback' if COMPLEMENTED else 'q0 feedback',24)
line([(900,440),(900,250),(185,250),(185,405),(275,405)])
text(420,214,'q1_N feedback' if COMPLEMENTED else 'q1 feedback',24)
if COMPLEMENTED:
    line([(866,440),(900,440)])
    and_gate(300,370)
else:
    or_gate(300,370,inverted=True)
text(390,325,'AND' if COMPLEMENTED else 'NOR',27,bold=True,anchor='mt')
line([(480 if COMPLEMENTED else 496,440),(600,440)])
arrow(589,440)

ff(600,380,'FF1','Rising','q1 = p')
ff(1050,380,'FF0','Rising','q0')
ff(1050,820,'FF_DELAY','Falling','delayed')

# p drives FF0.D, FF_DELAY.D and OR.in1, plus the NOR feedback.
line([(850,490),(990,490),(990,440),(1050,440)] if COMPLEMENTED else [(850,440),(1050,440)])
arrow(1038,440)
if not COMPLEMENTED:
    dot(900,440)
else:
    line([(1300,490),(1350,490)])
dot(940,490 if COMPLEMENTED else 440)
line([(940,490 if COMPLEMENTED else 440),(940,880),(1050,880)])
arrow(1038,880)
dot(940,740)
line([(940,740),(1510,740),(1510,705),(1555,705)])
text(1160,702,'p',26,GREEN,bold=True)

# OR.in2 is the delayed copy of p, not the other counter bit.
line([(1300,880),(1460,880),(1460,775),(1555,775)])
or_gate(1580,670)
text(1670,625,'OR',27,bold=True,anchor='mt')
line([(1760,740),(1900,740)],GREEN,4)
arrow(1900,740,GREEN)
text(1860,675,'out',32,GREEN,bold=True,anchor='mt')
text(1830,793,'p OR delayed',25,GREEN,anchor='mt')

text(80,810,'Counter connections',29,bold=True)
text(80,860,'D1 = q1_N AND q0_N' if COMPLEMENTED else 'D1 = NOT(q1 OR q0)',27)
text(80,906,'D0 = q1',27)
text(80,952,'State (q1,q0): 00 > 10 > 01 > 00',26)
text(80,1020,'Delayed copy',29,bold=True)
text(80,1070,'D_DELAY = q1',27)
if COMPLEMENTED:
    text(80,1120,'Q_N means NOT Q; it is an FF output.',26)

line([(70,1200),(1930,1200)],'#d8e0e8',2)
text(70,1230,'NET LABELS',23,bold=True)
text(310,1230,'All clk labels connect to the SAME input clock.',25,BLUE)
text(310,1270,'All rst_n labels connect to the SAME active-low reset; reset all Q outputs to 0.',25,PURPLE)
text(310,1310,'Clock triangle + bubble = falling edge. Filled dots = connected branches.',24)

im.resize((2000,1400),Image.Resampling.LANCZOS).save(ROOT/('diagrams/prep-010-circuit-and.png' if COMPLEMENTED else 'diagrams/prep-010-circuit.png'))
