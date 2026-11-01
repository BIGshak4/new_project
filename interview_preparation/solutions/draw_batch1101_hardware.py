"""Deterministic bilingual engineering redraws for the November intake."""
from pathlib import Path

from draw_batch21_hardware import GREEN, PALE, PURPLE, canvas, label, table
from draw_prep_016_064 import phrase, wire

OUT = Path(__file__).resolve().parents[1] / 'diagrams'


def box(d, rect, lines):
    d.rounded_rectangle(rect, 22, fill=PALE, outline=PURPLE, width=5)
    x1,y1,x2,y2=rect
    for i,line in enumerate(lines,1):
        label(d,((x1+x2)/2,y1+i*(y2-y1)/(len(lines)+1)),line,37)


def dot(d,x,y):
    d.ellipse((x-7,y-7,x+7,y+7),fill=PURPLE)


def ir_drop(lg):
    im,d=canvas('מתח העומס כולל גם את נתיב החזרה','Load voltage includes the return-path drop',lg,1450)
    box(d,(150,330,520,900),['Vs = 1.0 V'])
    box(d,(1660,330,2150,900),['I = 2 A','Vload = 0.96 V'])
    label(d,(485,430),'+',32);label(d,(485,800),'-',32)
    label(d,(1695,430),'+',32);label(d,(1695,800),'-',32)
    for y,res,caption in [(430,'Rs = 15 mOhm','30 mV'),(800,'Rg = 5 mOhm','10 mV')]:
        wire(d,[(520,y),(900,y)],PURPLE,arrow=False)
        box(d,(900,y-55,1280,y+55),[res])
        wire(d,[(1280,y),(1660,y)],PURPLE,arrow=False)
        label(d,(1090,y-135),caption,41)
    wire(d,[(590,320),(780,320)],GREEN,5);label(d,(680,255),'I',42)
    wire(d,[(1550,950),(1360,950)],GREEN,5);label(d,(1460,1000),'I',42)
    phrase(d,(335,1010),'מקור','Source',lg,40)
    phrase(d,(1905,1010),'עומס','Load',lg,40)
    label(d,(1200,1120),'Vload = Vs - I(Rs+Rg)     P_loss = I^2(Rs+Rg)',45)
    phrase(d,(1200,1230),'קבל תומך במעבר ואינו מבטל נפילת מתח קבועה','A capacitor supports a transient; it does not remove steady DC drop',lg,39)
    label(d,(1200,1340),'C_ideal >= delta_I * delta_t / delta_V',46)
    return im


def predicates(lg):
    im,d=canvas('ארבע בדיקות נפרדות ובחירה מפורשת','Four separate predicates and explicit selection',lg,1530)
    forms=['NOT(a AND b AND c AND d)','abc OR abd OR acd OR bcd','a XOR b XOR c XOR d','NOT(F10)']
    for i,form in enumerate(forms):
        y=330+i*230
        box(d,(350,y-70,1390,y+85),[f'F{i//2}{i%2} = {form}'])
        label(d,(180,y),'x[3:0]',34)
        wire(d,[(250,y),(350,y)],PURPLE,4)
        wire(d,[(1390,y),(1650,y)],GREEN,5)
        label(d,(1515,y-40),f'{i:02b}',32)
    box(d,(1650,240,2070,1120),['MUX 4:1','AB','y = F[AB]'])
    wire(d,[(2070,700),(2310,700)],GREEN,6);label(d,(2250,625),'y',50)
    wire(d,[(1970,1180),(1970,1120)],PURPLE,5)
    label(d,(2110,1240),'A=mode[1]',36);label(d,(2110,1340),'B=mode[0]',36)
    table(d,[[('קלט','input'),'00','01','10','11'],['0101','1','0','0','1'],['1111','0','1','0','1']],180,1200,[800,220,220,220,220],lg,80,36)
    return im


def mux(lg):
    im,d=canvas('ענף קצר לקלט מאוחר ומחיר מפורש לבקרה','A short late-data branch with explicit control cost',lg,1660)
    # Seven-cell optimized design, with distinct data and select pins.
    for y,pair,name in [(520,'D2, D3','P23'),(900,'D4, D5','P45'),(1180,'D6, D7','P67')]:
        box(d,(380,y-80,690,y+80),['MUX S0',name]);label(d,(170,y),pair,36)
        wire(d,[(260,y),(380,y)],PURPLE,4)
    box(d,(950,360,1270,650),['MUX S1','LOW'])
    wire(d,[(690,520),(830,520),(830,570),(950,570)],PURPLE,4)
    label(d,(685,300),'D1',40);wire(d,[(730,300),(830,300),(830,440),(950,440)],PURPLE,4)
    box(d,(950,930,1270,1210),['MUX S1','HIGH'])
    wire(d,[(690,900),(820,900),(820,1000),(950,1000)],PURPLE,4)
    wire(d,[(690,1180),(820,1180),(820,1140),(950,1140)],PURPLE,4)
    box(d,(1490,650,1810,950),['MUX S2','REST'])
    wire(d,[(1270,505),(1370,505),(1370,730),(1490,730)],PURPLE,4)
    wire(d,[(1270,1070),(1370,1070),(1370,875),(1490,875)],PURPLE,4)
    box(d,(2030,570,2310,950),['MUX C','Y'])
    wire(d,[(1810,800),(1920,800),(1920,850),(2030,850)],PURPLE,4)
    label(d,(660,195),'D0',50,GREEN)
    wire(d,[(730,195),(1900,195),(1900,670),(2030,670)],GREEN,7)
    label(d,(1950,620),'1',34);label(d,(1950,890),'0',34)
    box(d,(1510,1170,2240,1330),['C = NOT(S2 OR S1 OR S0)'])
    wire(d,[(2180,1170),(2180,950)],GREEN,4)
    phrase(d,(1200,1440),'שבעה מרבבים ועוד פענוח; הבקרה מתייצבת מראש','Seven MUXes plus predecode; control settles in advance',lg,40)
    phrase(d,(1200,1520),'עומק נתונים','Data depth',lg,37)
    label(d,(1200,1600),'D0 = 1; D1 = 3; D2..D7 = 4',45)
    return im


def decoder(lg):
    im,d=canvas('פענוח אינדקס ומיסוך הנתון המתאים','Decode the index and mask the corresponding data',lg,1390)
    box(d,(260,330,760,1050),['DECODER','n = 2','E[j] = [S=j]'])
    label(d,(140,650),'S[1:0]',37);wire(d,[(190,700),(260,700)],PURPLE,4)
    for i in range(4):
        y=370+i*210
        wire(d,[(760,y),(1130,y)],PURPLE,4);label(d,(900,y-55),f'E{i}',37)
        box(d,(1130,y-55,1390,y+65),['AND'])
        wire(d,[(1430,y-95),(1260,y-95),(1260,y-55)],GREEN,4);label(d,(1500,y-95),f'D{i}',39)
        wire(d,[(1390,y),(1640,y)],GREEN,4)
    box(d,(1640,290,2040,1070),['OR','3 x OR','n = 2'])
    wire(d,[(2040,700),(2290,700)],GREEN,5);label(d,(2260,620),'Y',47)
    label(d,(1200,1180),'S = 10  =>  E3..E0 = 0100  =>  Y = D2',47)
    phrase(d,(1200,1290),'נתוני הקלט אינם חייבים להיות בעלי אחד יחיד','The data inputs need not be one-hot',lg,39)
    return im


def polarities(lg):
    im,d=canvas('נתון חי מול דגימה אחרונה: שלוש יציאות','Live data versus the last sample: three outputs',lg,1840)
    box(d,(450,300,870,710),['DFF','D=d','Q=q'])
    label(d,(200,400),'d',49);wire(d,[(250,400),(450,400)],PURPLE,4)
    dot(d,300,400)
    wire(d,[(300,400),(300,190),(2300,190),(2300,750)],PURPLE,4,arrow=False)
    label(d,(200,620),'clk',45);wire(d,[(280,620),(450,620)],PURPLE,4)
    for i,formula in enumerate(['R = d AND NOT q','F = q AND NOT d','B = d XOR q']):
        y=330+i*180
        wire(d,[(870,500),(1040,500),(1040,y),(1230,y)],GREEN,4)
        box(d,(1230,y-65,2190,y+65),[formula])
        wire(d,[(2300,y+25),(2190,y+25)],PURPLE,4);dot(d,2300,y+25)
    dot(d,1040,500)
    phrase(d,(1200,840),'לא משתמשים בנתון כשעון; הדגימה מתעדכנת בעלייה','Data is not the clock; the snapshot updates on rising clk',lg,39)
    times=[0,1,2.2,3,4.2,4.6,5,6.4,7,8.2,9,10]
    signals={name:[] for name in ['clk','d','q','R','F','B']}
    rises={1,3,5,7,9};changes={2.2:1,4.2:0,4.6:1,6.4:0,8.2:1}
    all_times=sorted(set(times+[2,4,6,8]))
    data=saved=0
    for row,name in enumerate(signals):
        y=1030+row*115;label(d,(140,y-25),name,39)
        previous=None;points=[];data=saved=0
        for t in all_times:
            if t in changes:data=changes[t]
            if t in rises:saved=data
            value={'clk':int(int(t)%2==1),'d':data,'q':saved,'R':data&(1-saved),'F':saved&(1-data),'B':data^saved}[name]
            xp=300+t*190;yp=y-55*value
            if previous is not None:points.append((xp,previous))
            points.append((xp,yp));previous=yp
        wire(d,points,PURPLE if row<3 else GREEN,5,arrow=False)
        d.line((300,y+12,2200,y+12),fill=PALE,width=2)
    for tick in range(11):label(d,(300+190*tick,1750),str(tick),30)
    label(d,(2310,1750),'t',34)
    return im


if __name__=='__main__':
    for number,stem,fn in [(233,'ir-drop-20261101',ir_drop),(234,'controlled-predicates-20261101',predicates),
                           (235,'late-mux-20261101',mux),(236,'decoder-mux-20261101',decoder),
                           (91,'polarity-batch1101',polarities)]:
        for lg in ('he','en'):
            fn(lg).save(OUT/f'prep-{number:03d}-{stem}-{lg}.png',optimize=True)
