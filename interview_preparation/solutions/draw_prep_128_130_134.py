"""Clean bilingual FSM, lower-clamp and constant-multiplier diagrams (Pillow)."""
from math import atan2, cos, sin
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, GREEN, PALE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0"


def canvas(he, en, lang, height=1600, width=2200):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (width // 2, 78), he, en, lang, 50, bold=True)
    return image, draw


def label(draw, point, value, size=39, color=INK):
    text(draw, point, value, size, bold=True, color=color)


def panel(draw, rect):
    draw.rounded_rectangle(rect, 20, fill=PALE, outline=PURPLE, width=5)


def curve(draw, points, value, at, color=PURPLE):
    path = []
    for step in range(81):
        t = step / 80
        u = 1 - t
        path.append((u**3 * points[0][0] + 3 * u*u*t * points[1][0] + 3*u*t*t * points[2][0] + t**3 * points[3][0],
                     u**3 * points[0][1] + 3 * u*u*t * points[1][1] + 3*u*t*t * points[2][1] + t**3 * points[3][1]))
    # Halo makes crossing graph edges visibly separate, never extra states.
    draw.line(path, fill=BG, width=15)
    draw.line(path, fill=color, width=5)
    a, b = path[-4], path[-1]
    angle = atan2(b[1] - a[1], b[0] - a[0])
    draw.polygon((b, (b[0]-25*cos(angle-0.4), b[1]-25*sin(angle-0.4)),
                  (b[0]-25*cos(angle+0.4), b[1]-25*sin(angle+0.4))), fill=color)
    draw.rounded_rectangle((at[0]-28, at[1]-29, at[0]+28, at[1]+29), 8, fill=BG)
    label(draw, at, value, 39, color)


def state_graph(lang):
    image, d = canvas("מכונת מור לזיהוי הרצף הנתון", "Moore machine for the specified serial pattern", lang, 1710)
    phrase(d, (1100, 168), "כל חץ מסומן בביט הקלט; רק מצב הזיהוי מוציא אחד", "Edges show input bits; only the detection state outputs one", lang, 36)
    # Forward progress clockwise around the perimeter.
    curve(d, [(455,600),(600,600),(800,600),(945,600)], "0", (700,550))
    curve(d, [(1155,600),(1300,600),(1500,600),(1645,600)], "1", (1400,550))
    curve(d, [(1750,705),(1750,820),(1750,1020),(1750,1145)], "0", (1830,925))
    curve(d, [(1645,1250),(1500,1250),(1300,1250),(1155,1250)], "1", (1400,1310))
    curve(d, [(945,1250),(800,1250),(600,1250),(455,1250)], "1", (700,1310))
    # All seven fallback/self-loop cases.
    curve(d, [(290,515),(190,345),(510,345),(410,515)], "1", (350,370))
    curve(d, [(990,515),(890,345),(1210,345),(1110,515)], "0", (1050,370))
    curve(d, [(1690,515),(1650,215),(450,215),(410,515)], "1", (1050,260))
    curve(d, [(1680,1170),(1590,950),(1310,800),(1120,680)], "0", (1430,900))
    curve(d, [(1140,1190),(1280,1010),(1520,1010),(1660,1190)], "0", (1400,1060))
    curve(d, [(420,1170),(510,950),(790,800),(980,680)], "0", (700,900))
    curve(d, [(290,1165),(110,1020),(110,850),(290,685)], "1", (165,925))
    locations = {0:(350,600),1:(1050,600),2:(1750,600),3:(1750,1250),4:(1050,1250),5:(350,1250)}
    prefixes = ("empty", "0", "01", "010", "0101", "01011")
    for state, (x,y) in locations.items():
        d.ellipse((x-108,y-108,x+108,y+108), fill="#edf5ef" if state==5 else BG, outline=GREEN if state==5 else PURPLE, width=5)
        if state==5:
            d.ellipse((x-120,y-120,x+120,y+120), outline=GREEN, width=4)
        label(d, (x,y-42), f"Q{state}", 43)
        if state==0:
            phrase(d,(x,y+9),"ריקה","empty",lang,29)
        else:
            label(d,(x,y+9),prefixes[state],34)
        label(d,(x,y+61),f"Y={int(state==5)}",29,GREEN if state==5 else INK)
    wire(d, [(65,600),(235,600)], INK)
    label(d,(130,540),"reset",29)
    phrase(d,(1100,1490),"איפוס סינכרוני מכל מצב מחזיר להתחלה", "Synchronous reset from every state returns to Q0",lang,38)
    label(d,(1100,1570),"Q4 + input 0 → Q3     01010 ends in 010",35,PURPLE)
    phrase(d,(1100,1650),"חציות חצים אינן מצבים; המצבים הם העיגולים בלבד", "Crossing edges do not join; only circles denote states",lang,34)
    image.save(OUT/f"prep-128-state-graph-{lang}.png")


def state_datapath(lang):
    image,d=canvas("טבלת המעברים ומימוש מבוסס אוגרי מצב", "Transition table and state-register implementation",lang,1560)
    phrase(d,(1100,170),"ביט אחד בכל חזית; המוצא נקרא אחרי התייצבות המצב החדש", "One bit per edge; observe output after the new state settles",lang,35)
    rows=[("state","0","1","Y"),("Q0","Q1","Q0","0"),("Q1","Q1","Q2","0"),("Q2","Q3","Q0","0"),("Q3","Q1","Q4","0"),("Q4","Q3","Q5","0"),("Q5","Q1","Q0","1")]
    for row,items in enumerate(rows):
        for col,item in enumerate(items):
            left,top=110+col*235,350+row*105
            d.rectangle((left,top,left+235,top+105),fill=PALE if row==0 else BG,outline="#d6cce2",width=2)
            if row==0 and col==0:
                phrase(d,(left+117,top+52),"מצב","state",lang,34,bold=True)
            else:
                label(d,(left+117,top+52),item,37)
    panel(d,(1330,440,1900,700))
    phrase(d,(1615,510),"לוגיקת מצב הבא","Next-state logic",lang,37,bold=True)
    phrase(d,(1615,610),"לפי הטבלה","Use the table",lang,32)
    wire(d,[(1160,490),(1330,490)],INK)
    label(d,(1210,420),"x",43)
    panel(d,(1330,880,1900,1110))
    label(d,(1615,945),"3 DFF",45,PURPLE)
    label(d,(1615,1030),"Q0..Q5 = 000..101",31)
    wire(d,[(1615,700),(1615,880)],GREEN)
    label(d,(1730,785),"D[2:0]",32,GREEN)
    wire(d,[(1900,990),(2100,990)],PURPLE)
    d.ellipse((2092,982,2108,998),fill=PURPLE)
    label(d,(2030,1050),"q[2:0]",31,PURPLE)
    wire(d,[(2100,990),(2100,1300),(1230,1300),(1230,630),(1330,630)],PURPLE)
    panel(d,(1440,260,1910,360))
    label(d,(1675,310),"q2 AND NOT q1 AND q0",27,GREEN)
    wire(d,[(2100,990),(2100,310),(1910,310)],PURPLE)
    wire(d,[(1440,310),(1210,310)],GREEN)
    label(d,(1250,245),"Y",43,GREEN)
    for x,name in ((1480,"clk"),(1760,"rst")):
        wire(d,[(x,1225),(x,1110)],INK)
        label(d,(x,1255),name,32)
    label(d,(1100,1400),"x: 0 1 0 1 0 1 1       Y: 0 0 0 0 0 0 1",36,PURPLE)
    phrase(d,(1100,1500),"ביטי האוגר קטנים באותיות; שמות המצבים מופיעים בטבלה", "Lowercase q denotes encoding bits; table labels Q0..Q5 denote states",lang,34)
    image.save(OUT/f"prep-128-state-table-datapath-{lang}.png")


def threshold(lang):
    image,d=canvas("סף ללא סימן לפי שני הביטים העליונים", "Unsigned threshold from the top two bits",lang,1600)
    phrase(d,(1100,170),"אותו שם מציין אותו אות מפוצל; המערכת צירופית", "Repeated names denote fanout of the same signal; no stored state",lang,35)
    wire(d,[(180,350),(2050,350)],PURPLE)
    label(d,(260,285),"x7",43)
    label(d,(1950,285),"y7",43,PURPLE)
    panel(d,(430,550,740,750))
    label(d,(585,650),"NOT",43)
    wire(d,[(150,650),(430,650)],INK)
    label(d,(240,580),"x7",39)
    wire(d,[(740,650),(1050,650)],GREEN)
    label(d,(875,580),"NOT x7",32,GREEN)
    wire(d,[(150,850),(1050,850)],INK)
    label(d,(240,790),"x6",39)
    panel(d,(1050,550,1470,930))
    label(d,(1260,745),"OR",49)
    wire(d,[(1470,745),(2050,745)],PURPLE)
    label(d,(1920,680),"y6",44,PURPLE)
    panel(d,(430,1070,800,1370))
    label(d,(615,1220),"OR",49)
    for y,name in ((1140,"x7"),(1300,"x6")):
        wire(d,[(150,y),(430,y)],INK)
        label(d,(230,y-55),name,38)
    wire(d,[(800,1220),(1100,1220)],GREEN)
    label(d,(930,1150),"e",45,GREEN)
    panel(d,(1100,1060,1620,1400))
    label(d,(1360,1135),"6 × AND",43)
    label(d,(1360,1305),"yi = xi AND e",34)
    wire(d,[(900,1350),(1100,1350)],INK)
    label(d,(920,1405),"x[5:0]",32)
    wire(d,[(1620,1220),(2050,1220)],PURPLE)
    label(d,(1920,1150),"y[5:0]",39,PURPLE)
    label(d,(1100,1480),"00111111 → 01000000       10000000 → 10000000",37,PURPLE)
    phrase(d,(1100,1560),"שישה שערי וגם, שני שערי או ומהפך אחד במימוש הזה", "This construction: six ANDs, two ORs and one NOT",lang,34)
    image.save(OUT/f"prep-130-gate-network-{lang}.png")


def multiplier(lang):
    image,d=canvas("כפל בקבוע באמצעות שני בלוקי חיבור", "Constant multiplication using two adder blocks",lang,1500,2400)
    phrase(d,(1200,170),"כל ההרחבות וההזזות קבועות ומבוצעות בחיווט", "All extensions and fixed shifts are wiring",lang,36)
    panel(d,(350,500,650,900))
    phrase(d,(500,620),"הרחבת","Zero",lang,34,bold=True)
    phrase(d,(500,685),"אפסים","extension",lang,34,bold=True)
    label(d,(500,790),"N → M",36)
    wire(d,[(80,700),(350,700)],INK)
    label(d,(215,610),"X[N-1:0]",32)
    wire(d,[(650,700),(900,700)],PURPLE)
    label(d,(780,640),"Xext",37,PURPLE)
    for x in (800,850,900):
        d.ellipse((x-7,693,x+7,707),fill=PURPLE)
    wire(d,[(900,700),(900,500),(1150,500)],PURPLE)
    label(d,(1025,420),"Xext << 3",33,PURPLE)
    wire(d,[(850,700),(850,800),(1150,800)],PURPLE)
    label(d,(1000,865),"Xext << 2",33,PURPLE)
    for left in (1150,1750):
        panel(d,(left,400,left+400,900))
        label(d,(left+200,600),"+",85,GREEN)
        label(d,(left+200,770),"M bits",39)
    wire(d,[(1550,500),(1750,500)],GREEN)
    label(d,(1650,420),"T",42,GREEN)
    wire(d,[(800,700),(800,1210),(1650,1210),(1650,800),(1750,800)],PURPLE)
    label(d,(1225,1150),"Xext",38,PURPLE)
    wire(d,[(2150,650),(2340,650)],GREEN)
    label(d,(2245,575),"Y",49,GREEN)
    label(d,(1200,1330),"M = N+4       T = 8X + 4X       Y = T + X = 13X",43,PURPLE)
    phrase(d,(1200,1435),"רוחב מלא גם בתוצאת הביניים; אין שעון או טענת מינימום", "Keep full intermediate width; no clock or minimum-adder claim",lang,36)
    image.save(OUT/f"prep-134-constant-multiplier-datapath-{lang}.png")


if __name__=="__main__":
    for language in ("he","en"):
        state_graph(language)
        state_datapath(language)
        threshold(language)
        multiplier(language)
    print("Wrote eight bilingual solution figures for PREP-128/130/134")
