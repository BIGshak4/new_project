"""Localized deterministic diagrams for priority hierarchy and gate-only counter."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
INK, BLUE, GREEN, ORANGE, PURPLE = '#23334b', '#2a62a0', '#257b67', '#b26522', '#7854a2'


def text(d, point, value, size=48, *, color=INK, bold=False, hebrew=False, anchor='mm'):
    # Only pure Hebrew phrases are reversed; formulas/net names remain LTR.
    if hebrew:
        value = value[::-1]
    d.text(point,value,font=ImageFont.truetype(BOLD if bold else FONT,size),fill=color,anchor=anchor)


def wire(d, points, color=BLUE, width=8, arrow=True):
    d.line(points,fill=color,width=width,joint='curve')
    if arrow:
        x,y=points[-1];px,py=points[-2];angle=math.atan2(y-py,x-px)
        d.polygon([(x,y),(x-28*math.cos(angle-.45),y-28*math.sin(angle-.45)),
                   (x-28*math.cos(angle+.45),y-28*math.sin(angle+.45))],fill=color)


def box(d, rect, color=BLUE):
    d.rounded_rectangle(rect,radius=30,fill='#f5f8fd',outline=color,width=7)


def phrase(d, point, he, en, language, size=48, **kwargs):
    text(d,point,he if language=='he' else en,size,hebrew=language=='he',**kwargs)


def priority(language, fifth):
    im=Image.new('RGB',(4700,2650),'white');d=ImageDraw.Draw(im)
    phrase(d,(2350,100),'מקודד עדיפות היררכי לשש עשרה כניסות','Hierarchical sixteen-input priority encoder',language,70,bold=True)
    text(d,(2350,205),'In15 > In14 > ... > In0      |      K,G,L: /2      |      V,Y: /1',48)
    for g in range(4):
        y=350+g*470
        box(d,(500,y,1130,y+300))
        text(d,(815,y+65),f'C{g}: PE4',58,bold=True)
        text(d,(815,y+145),'In[3:0]',46)
        wire(d,[(170,y+150),(500,y+150)]);text(d,(180,y+80),f'In{4*g+3}..In{4*g}',45,anchor='lm')
        text(d,(375,y+190),'/4',38)
        wire(d,[(1130,y+110),(1500,y+110)],GREEN);text(d,(1370,y+60),f'V{g}',45,color=GREEN,bold=True)
        wire(d,[(1130,y+235),(1500,y+235)],BLUE);text(d,(1370,y+185),f'K{g}[1:0]',45,color=BLUE,bold=True)
    group=(2050,360,3080,980)
    box(d,group,GREEN)
    phrase(d,(2565,425),'בחירת הקבוצה הזוכה','Choose the winning group',language,49,bold=True,color=GREEN)
    for g in range(4):
        yy=535+110*g
        text(d,(1780,yy),f'V{g}',47,color=GREEN,bold=True)
        wire(d,[(1840,yy),(2050,yy)],GREEN)
    if fifth:
        text(d,(2565,545),'C4: PE4',55,bold=True)
        text(d,(2565,665),'(V3,V2,V1,V0)',47)
        text(d,(2565,790),'Y = C4.valid',45,color=GREEN)
        text(d,(2565,885),'G = C4.index[1:0]',45,color=PURPLE)
    else:
        text(d,(2565,555),'Y = V3 OR V2 OR V1 OR V0',43,color=GREEN)
        text(d,(2565,690),'G1 = V3 OR V2',46,color=PURPLE)
        text(d,(2565,820),'G0 = V3 OR (V1 AND NOT V2)',40,color=PURPLE)
    wire(d,[(3080,565),(3600,565)],GREEN);text(d,(3380,500),'Y',54,color=GREEN,bold=True)
    wire(d,[(3080,840),(3310,840),(3310,1130),(2565,1130),(2565,1320)],PURPLE)
    text(d,(3190,780),'G[1:0]',48,color=PURPLE,bold=True)
    box(d,(2050,1320,3080,2010),BLUE)
    text(d,(2565,1390),'MUX 4:1 x 2',55,bold=True)
    text(d,(2600,1290),'S = G[1:0]',46,color=PURPLE)
    for g in range(4):
        yy=1505+125*g
        text(d,(1760,yy),f'K{g}[1:0]',46,color=BLUE,bold=True)
        wire(d,[(1880,yy),(2050,yy)],BLUE)
        text(d,(2110,yy),f'D{g}',40,color=BLUE)
    wire(d,[(3080,1640),(3490,1640),(3490,1945),(3700,1945)],BLUE)
    text(d,(3300,1575),'L[1:0]',49,color=BLUE,bold=True)
    box(d,(3700,1640,4510,2270),PURPLE)
    phrase(d,(4105,1710),'שרשור וחסימה','Concatenate and qualify',language,45,bold=True)
    for label,yy,color in [('G[1:0]',1830,PURPLE),('Y',2130,GREEN)]:
        wire(d,[(3510,yy),(3700,yy)],color)
        text(d,(3480,yy),label,44,color=color,anchor='rm')
    text(d,(4105,1850),'raw = {G,L}',49,bold=True)
    text(d,(4105,1990),'P = raw AND {4{Y}}',44,bold=True)
    text(d,(4105,2190),'P[3:0]',49,color=PURPLE,bold=True)
    wire(d,[(4105,2270),(4105,2390)],PURPLE)
    phrase(d,(2350,2420),'שמות חוטים זהים מסמנים את אותו חיבור','Matching net names identify the same connection',language,48)
    phrase(d,(2350,2520),'ללא שעון וללא דלגלגים','No clock or flip-flops',language,46)
    im.save(OUT/f'prep-016-hierarchy-{"five" if fifth else "four"}-{language}.png')


def counter(language):
    im=Image.new('RGB',(4300,3350),'white');d=ImageDraw.Draw(im)
    phrase(d,(2150,100),'מונה שלושה ביטים באמצעות שערים ודלגלגים','Three-bit counter using gates and flip-flops',language,68,bold=True)
    text(d,(2150,215),'U = inc AND NOT dec       D = dec AND NOT inc',53,bold=True)
    phrase(d,(2150,325),'איפוס סינכרוני משותף גובר על פקודות הספירה','Common synchronous reset overrides counting',language,49)
    equations=[['T0 = U OR D'],['T1 = (U AND q0)','OR (D AND NOT q0)'],
               ['T2 = (U AND q1 AND q0)','OR (D AND NOT q1 AND NOT q0)']]
    for bit in range(3):
        y=640+bit*850;cy=y+215
        box(d,(480,y,1990,y+430))
        phrase(d,(1235,y+75),'לוגיקת היפוך בשערים','Gate-only toggle logic',language,49,bold=True)
        for line_number,value in enumerate(equations[bit]):
            text(d,(1235,y+210+line_number*100),value,45,bold=True)
        text(d,(270,y+180),'U,D',46,color=BLUE)
        wire(d,[(330,y+215),(480,y+215)])
        if bit:
            text(d,(260,y+335),'q0' if bit==1 else 'q1,q0',44,color=PURPLE)
            wire(d,[(330,y+355),(480,y+355)],PURPLE)
        wire(d,[(1990,cy),(2300,cy)],BLUE);text(d,(2155,cy-65),f'T{bit}',48,color=BLUE,bold=True)
        d.ellipse((2300,cy-100,2500,cy+100),outline=BLUE,width=8,fill='#f5f8fd')
        text(d,(2400,cy),'XOR',42,bold=True)
        box(d,(2810,y,3410,y+430),GREEN)
        text(d,(3110,y+75),f'DFF {bit}',53,color=GREEN,bold=True)
        text(d,(2865,cy),'D',43,color=GREEN);text(d,(3355,cy),'Q',43,color=GREEN)
        wire(d,[(2500,cy),(2810,cy)],BLUE);text(d,(2650,cy-65),f'D{bit}',47,color=BLUE)
        wire(d,[(3410,cy),(4050,cy)],PURPLE);text(d,(3870,cy-65),f'q{bit}',53,color=PURPLE,bold=True)
        branch=(3650,cy);d.ellipse((3640,cy-10,3660,cy+10),fill=PURPLE)
        wire(d,[branch,(3650,y-170),(2400,y-170),(2400,cy-100)],PURPLE)
        text(d,(3100,y-220),f'q{bit}',45,color=PURPLE)
        for x,label in [(2980,'clk'),(3240,'rst')]:
            wire(d,[(x,y+575),(x,y+430)],ORANGE)
            text(d,(x,y+620),label,44,color=ORANGE,bold=True)
    phrase(d,(2150,3160),'כל הדלגלגים משתמשים באותו שעון ובאותו איפוס','All flip-flops share the same clock and reset',language,48)
    text(d,(2150,3260),'Di = qi XOR Ti      |      rst=1 -> q=000      |      q mod 8',47,bold=True)
    im.save(OUT/f'prep-064-gate-counter-{language}.png')


def table(language):
    im=Image.new('RGB',(3000,1900),'white');d=ImageDraw.Draw(im)
    phrase(d,(1500,100),'טבלת מעברי המונה','Counter transition table',language,67,bold=True)
    text(d,(1500,210),'q(next)     |     rst=0',48)
    headers=['q[2:0]','inc=0, dec=0','inc=0, dec=1','inc=1, dec=0','inc=1, dec=1']
    xs=[300,900,1500,2100,2700]
    for x,h in zip(xs,headers,strict=True):text(d,(x,350),h,43,bold=True)
    for q in range(8):
        y=520+q*145
        if q%2==0:d.rectangle((30,y-62,2970,y+62),fill='#f0f5fb')
        vals=[q,q,(q-1)%8,(q+1)%8,q]
        for x,val in zip(xs,vals,strict=True):text(d,(x,y),f'{val:03b}',52,bold=True)
    text(d,(1500,1770),'rst=1 -> 000',55,color=ORANGE,bold=True)
    im.save(OUT/f'prep-064-transition-table-{language}.png')


if __name__=='__main__':
    for language in ('he','en'):
        priority(language,True)
        priority(language,False)
        counter(language)
        table(language)
