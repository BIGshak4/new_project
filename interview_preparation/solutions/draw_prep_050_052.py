"""Deterministic technical diagrams. Run with the bundled Python/Pillow runtime.

No natural-language diagram prose: state/signal labels and formulas are shared
between the Hebrew and English explanations. PNG assets are learner diagrams,
not replacements for the archived source screenshots.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
FONT = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
INK = "#20314a"
BLUE = "#2762a5"
ORANGE = "#b3641d"
GREEN = "#238069"


def text(draw, xy, value, size=48, fill=INK, anchor="mm", bold=False):
    draw.text(xy, value, fill=fill, font=ImageFont.truetype(BOLD if bold else FONT, size), anchor=anchor)


def line(draw, points, color=BLUE, width=8, arrow=True):
    draw.line(points, fill=color, width=width, joint="curve")
    if arrow:
        x, y = points[-1]
        px, py = points[-2]
        angle = math.atan2(y - py, x - px)
        draw.polygon([(x, y), (x - 28 * math.cos(angle - 0.48), y - 28 * math.sin(angle - 0.48)),
                      (x - 28 * math.cos(angle + 0.48), y - 28 * math.sin(angle + 0.48))], fill=color)


def label(draw, xy, value, size=46, fill=INK):
    font = ImageFont.truetype(BOLD, size)
    box = draw.textbbox(xy, value, font=font, anchor="mm")
    draw.rounded_rectangle((box[0] - 16, box[1] - 10, box[2] + 16, box[3] + 10), radius=10, fill="white")
    draw.text(xy, value, font=font, fill=fill, anchor="mm")


def mux(draw, x, y, name, color=BLUE):
    w, h = 330, 350
    draw.rounded_rectangle((x, y, x+w, y+h), radius=28, fill="#f0f6ff", outline=color, width=7)
    text(draw, (x+w/2, y+80), name, 54, bold=True)
    text(draw, (x+w/2, y+145), "MUX", 49, bold=True)
    text(draw, (x+43, y+110), "0", 40, fill=color)
    text(draw, (x+43, y+245), "1", 40, fill=color)
    text(draw, (x+w/2+32, y+h-38), "S", 39, fill=ORANGE)
    return {"d0": (x,y+110), "d1": (x,y+245), "s": (x+w/2,y+h), "out": (x+w,y+178)}


def raw(draw, pin, value, direction="left", color=BLUE):
    x,y = pin
    if direction == "left":
        line(draw, [(x-190,y),(x,y)],color)
        label(draw,(x-225,y),value,42,color)
    else:
        line(draw, [(x,y+170),(x,y)],ORANGE)
        label(draw,(x,y+215),value,43,ORANGE)


def xor_diagram():
    im=Image.new("RGB",(4400,1800),"white");d=ImageDraw.Draw(im)
    text(d,(2200,100),"F = A XOR B XOR C",72,bold=True)
    text(d,(2200,205),"MUX(S,D0,D1): S=0 -> D0; S=1 -> D1",50)
    for rect in [(350,360,2010,1110),(2120,360,3950,1110)]:
        d.rounded_rectangle(rect,radius=35,fill="#f8fafc",outline="#dce5ef",width=4)
    p1=mux(d,650,520,"M1");p2=mux(d,1500,520,"M2")
    p3=mux(d,2450,520,"M3");p4=mux(d,3400,520,"M4")
    raw(d,p1['d0'],'A');raw(d,p1['d1'],'0');raw(d,p1['s'],'B','bottom')
    raw(d,p2['d0'],'B');raw(d,p2['s'],'A','bottom')
    line(d,[p1['out'],(1190,p1['out'][1]),(1190,p2['d1'][1]),p2['d1']]);label(d,(1150,650),'t')
    branch=(2070,p2['out'][1])
    line(d,[p2['out'],branch,(2070,p3['d0'][1]),p3['d0']]);label(d,(2180,570),'P')
    d.ellipse((branch[0]-11,branch[1]-11,branch[0]+11,branch[1]+11),fill=BLUE)
    raw(d,p3['d1'],'0');raw(d,p3['s'],'C','bottom')
    raw(d,p4['d0'],'C')
    line(d,[p3['out'],(3100,p3['out'][1]),(3100,p4['d1'][1]),p4['d1']]);label(d,(3070,650),'u')
    line(d,[branch,(2070,1250),(p4['s'][0],1250),p4['s']],ORANGE);label(d,(3000,1250),'P',fill=ORANGE)
    line(d,[p4['out'],(4160,p4['out'][1])],GREEN);label(d,(4070,620),'F',fill=GREEN)
    text(d,(1175,430),'P = A XOR B',49,bold=True)
    text(d,(3035,430),'F = P XOR C',49,bold=True)
    text(d,(2200,1450),'M1(B,A,0) -> t      M2(A,B,t) -> P',49)
    text(d,(2200,1530),'M3(C,P,0) -> u      M4(P,C,u) -> F',49)
    text(d,(2200,1650),'4 x MUX2:1     |     const = {0}     |     gates = {MUX}',47,bold=True)
    im.save(OUT/'prep-051-xor-three-four-mux.png')


def adder_diagram():
    im=Image.new("RGB",(4400,2380),"white");d=ImageDraw.Draw(im)
    text(d,(2200,100),'A + B + Cin = S + 2*Cout',70,bold=True)
    text(d,(2200,205),'MUX(S,D0,D1): S=0 -> D0; S=1 -> D1',49)
    m1=mux(d,600,500,'M1');m2=mux(d,1600,500,'M2')
    m3=mux(d,1600,1400,'M3');m4=mux(d,3100,500,'M4');m5=mux(d,3100,1400,'M5')
    raw(d,m1['d0'],'1');raw(d,m1['d1'],'0');raw(d,m1['s'],'B','bottom')
    raw(d,m2['d0'],'B');raw(d,m2['s'],'A','bottom')
    line(d,[m1['out'],(1240,m1['out'][1]),(1240,m2['d1'][1]),m2['d1']]);label(d,(1200,620),'nB')
    raw(d,m3['d0'],'1');raw(d,m3['d1'],'0');raw(d,m3['s'],'Cin','bottom')
    raw(d,m4['d0'],'Cin')
    branch=(2240,m2['out'][1])
    line(d,[m2['out'],branch,(2240,1110),(m4['s'][0],1110),m4['s']],ORANGE)
    d.ellipse((branch[0]-11,branch[1]-11,branch[0]+11,branch[1]+11),fill=ORANGE)
    label(d,(2230,620),'P',fill=ORANGE)
    line(d,[branch,(2240,2050),(m5['s'][0],2050),m5['s']],ORANGE)
    d.ellipse((2230,1100,2250,1120),fill=ORANGE)
    # The blue nCin wire crosses two orange P wires WITHOUT joining them.
    # Explicit white-bordered wire bridges distinguish these crossings from dots.
    line(d,[m3['out'],(2195,m3['out'][1])],arrow=False)
    for horizontal,x,y in [(True,2240,m3['out'][1]),(False,2540,1110)]:
        pts=[]
        for step in range(81):
            t=step/80
            if horizontal:
                pts.append((x-45+90*t,y-35*math.sin(math.pi*t)))
            else:
                pts.append((x+35*math.sin(math.pi*t),y+45-90*t))
        d.line(pts,fill='white',width=22)
        d.line(pts,fill=BLUE,width=8)
    line(d,[(2285,m3['out'][1]),(2540,m3['out'][1]),(2540,1155)],arrow=False)
    line(d,[(2540,1065),(2540,m4['d1'][1]),m4['d1']]);label(d,(2620,950),'nCin')
    raw(d,m5['d0'],'A');raw(d,m5['d1'],'Cin')
    line(d,[m4['out'],(4100,m4['out'][1])],GREEN);label(d,(4000,620),'S',fill=GREEN)
    line(d,[m5['out'],(4100,m5['out'][1])],GREEN);label(d,(4000,1520),'Cout',fill=GREEN)
    text(d,(2200,2220),'5 x MUX2:1     |     const = {0,1}     |     P = A XOR B',49,bold=True)
    im.save(OUT/'prep-052-full-adder-five-mux.png')


def curve(draw, start, control, end, value, position, color):
    points=[]
    for k in range(101):
        t=k/100
        points.append(((1-t)**2*start[0]+2*t*(1-t)*control[0]+t*t*end[0],
                       (1-t)**2*start[1]+2*t*(1-t)*control[1]+t*t*end[1]))
    line(draw,points,color,7)
    label(draw,position,value,52,color)


def fsm_diagram():
    im=Image.new('RGB',(4200,3000),'white');d=ImageDraw.Draw(im)
    text(d,(2100,100),'LSB -> MSB     |     s(next) = 3*(s + b) mod 5',66,bold=True)
    text(d,(2100,210),'S0: z=1          S1,S2,S3,S4: z=0',49)
    nodes={0:(2100,630),3:(3400,1200),1:(2900,2400),2:(1300,2400),4:(800,1200)}
    radius=160
    def attach(n, toward):
        x,y=nodes[n];a=math.atan2(toward[1]-y,toward[0]-x)
        return (x+radius*math.cos(a),y+radius*math.sin(a))
    edges=[
        (0,3,(3000,550),'1',(2820,680),ORANGE),
        (1,3,(3450,2100),'0',(3360,1900),BLUE),
        (2,1,(2100,2690),'0',(2100,2550),BLUE),
        (3,4,(2100,1000),'0',(2100,1100),BLUE),
        (4,2,(800,2100),'0',(900,1940),BLUE),
        (2,4,(1440,1700),'1',(1290,1800),ORANGE),
        (3,2,(2500,1760),'1',(2440,1800),ORANGE),
        (4,0,(1100,550),'1',(1390,680),ORANGE),
    ]
    for a,b,ctrl,value,pos,color in edges:
        curve(d,attach(a,ctrl),ctrl,attach(b,ctrl),value,pos,color)
    # Self loops drawn above S0 and to the right of S1.
    curve(d,(2010,500),(2100,240),(2190,500),'0',(2100,350),BLUE)
    curve(d,(3040,2340),(3500,2390),(3010,2510),'1',(3290,2440),ORANGE)
    line(d,[(1750,630),(1930,630)],INK,7);label(d,(1740,570),'rst',42)
    for state,(x,y) in nodes.items():
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill='#f4f8fd',outline=BLUE,width=7)
        if state==0:d.ellipse((x-radius+18,y-radius+18,x+radius-18,y+radius-18),outline=GREEN,width=6)
        text(d,(x,y-22),f'S{state}',68,bold=True)
        text(d,(x,y+62),f'z={int(state==0)}',42,fill=GREEN if state==0 else INK)
    text(d,(2100,2830),'b=0',50,fill=BLUE,bold=True)
    text(d,(2500,2830),'b=1',50,fill=ORANGE,bold=True)
    im.save(OUT/'prep-050-lsb-five-state-fsm.png')


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    xor_diagram();adder_diagram();fsm_diagram()
