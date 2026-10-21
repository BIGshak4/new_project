"""Reproducible localized technical figures for the 21 October intake."""
from pathlib import Path
from math import atan2, cos, sin, pi
import importlib.util
import sys
from PIL import Image, ImageDraw, ImageFont

BANK = Path(__file__).resolve().parents[1]
OUT = BANK / "diagrams"
INK, BLUE, GREEN, RED, GRAY, ORANGE = "#24314a", "#355fa0", "#267660", "#aa4545", "#738096", "#a16b1e"


def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/" + ("segoeuib.ttf" if bold else "segoeui.ttf"), size)


def label(d, xy, text, size=42, fill=INK, bold=False, he=False):
    d.text(xy, text[::-1] if he else text, font=font(size,bold), fill=fill, anchor="mm")


def arrow(d, points, color=BLUE, width=7):
    d.line(points, fill=color, width=width, joint="curve")
    a,b = points[-2:]
    angle = atan2(b[1]-a[1],b[0]-a[0])
    d.polygon([b,(b[0]-28*cos(angle-pi/7),b[1]-28*sin(angle-pi/7)),
                 (b[0]-28*cos(angle+pi/7),b[1]-28*sin(angle+pi/7))],fill=color)


def box(d, rect, color=BLUE, bg="#f2f6fd"):
    d.rounded_rectangle(rect,28,fill=bg,outline=color,width=6)


def trajectories(lang):
    he = lang == "he"
    spec = importlib.util.spec_from_file_location("rendezvous_draw_model", BANK/"solutions/prep_062_identical_agents.py")
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    im=Image.new("RGB",(3400,2100),"white");d=ImageDraw.Draw(im)
    label(d,(1700,110),"אותה תוכנית ומהירויות התקדמות שונות" if he else "Same program, different average progress rates",65,bold=True,he=he)
    label(d,(1700,225),"D=4    |    t_meet=6D-1=23",48,GRAY)
    x0,x1,y0,y1=330,3100,1600,410
    xy=lambda t,p:(x0+t*(x1-x0)/23,y0-p*(y0-y1)/12)
    for p in range(0,13,2):
        d.line([xy(0,p),xy(23,p)],fill="#e6eaf0",width=3)
        label(d,(250,xy(0,p)[1]),str(p),37,GRAY)
    for t in (0,5,10,15,20,23):
        d.line([xy(t,0),xy(t,12)],fill="#e6eaf0",width=3)
        label(d,(xy(t,0)[0],1680),str(t),37,GRAY)
    arrow(d,[(x0,y0),(x1+80,y0)],INK,5);arrow(d,[(x0,y0),(x0,y1-60)],INK,5)
    label(d,(180,440),"x",51,INK,bold=True);label(d,(3200,1660),"t",51,INK,bold=True)
    cpus=[module.LocalCPU(),module.LocalCPU()];positions=[0,4];points=[[xy(0,0)],[xy(0,4)]]
    for t in range(1,24):
        visible=[p in (0,4) for p in positions]
        moves=[cpus[i].tick(visible[i]) for i in (0,1)]
        positions=[positions[i]+moves[i] for i in (0,1)]
        for i in (0,1):points[i].append(xy(t,positions[i]))
    for pts,color in zip(points,(BLUE,GREEN)):
        d.line(pts,fill=color,width=10,joint="curve")
    for t,p,color in ((10,4,BLUE),(23,12,GREEN)):
        x,y=xy(t,p);d.ellipse((x-15,y-15,x+15,y+15),fill=color)
    label(d,(xy(11,4)[0]+300,xy(11,4)[1]+100),"P=1, t=11",39,BLUE,bold=True)
    label(d,(xy(23,12)[0]-220,xy(23,12)[1]-80),"x=12, t=23",42,GREEN,bold=True)
    label(d,(850,1810),"הסוכן שהתחיל מאחור" if he else "Initially trailing agent",47,BLUE,bold=True,he=he)
    label(d,(2460,1810),"הסוכן שהתחיל מלפנים" if he else "Initially leading agent",47,GREEN,bold=True,he=he)
    label(d,(1700,1920),"כל הוראה מבוצעת אורכת יחידת זמן כולל בדיקה וקפיצה" if he else "Every executed primitive costs one tick, including test and jump",43,he=he)
    label(d,(1700,2020),"v_slow=1/3    |    v_fast=2/3    |    MF: dx=+1",43,GRAY)
    im.save(OUT/f"prep-062-trajectories-{lang}.png")


def program(lang):
    he=lang=="he";im=Image.new("RGB",(3600,2200),"white");d=ImageDraw.Draw(im)
    label(d,(1800,100),"תוכנית מקומית ללא ידיעת המרחק או מיקום האחר" if he else "Local program: no distance or other-agent position",63,bold=True,he=he)
    label(d,(650,250),"SLOW",55,BLUE,bold=True);label(d,(2900,250),"FAST",55,GREEN,bold=True)
    for rect,text,color in (((350,350,950,550),"MF",BLUE),((350,1250,950,1450),"GOTO SLOW",BLUE),
                            ((1580,750,2220,950),"GOTO FAST",ORANGE),((2500,350,3300,550),"MF",GREEN),
                            ((2500,950,3300,1150),"MF",GREEN),((2500,1550,3300,1750),"GOTO FAST",GREEN)):
        box(d,rect,color,"#f2f6fd" if color==BLUE else "#eff8f3" if color==GREEN else "#fffaed")
        label(d,((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),text,52,color,bold=True)
    d.polygon([(650,650),(1000,850),(650,1050),(300,850)],fill="#fffaed",outline=ORANGE,width=6)
    label(d,(650,850),"if P",55,ORANGE,bold=True)
    arrow(d,[(650,555),(650,645)],BLUE)
    arrow(d,[(650,1055),(650,1245)],BLUE);label(d,(800,1150),"P=0",43,BLUE,bold=True)
    arrow(d,[(350,1350),(140,1350),(140,450),(345,450)],BLUE)
    arrow(d,[(1005,850),(1575,850)],ORANGE);label(d,(1280,770),"P=1",43,ORANGE,bold=True)
    arrow(d,[(2225,850),(2350,850),(2350,450),(2495,450)],ORANGE)
    arrow(d,[(2900,555),(2900,945)],GREEN)
    arrow(d,[(2900,1155),(2900,1545)],GREEN)
    arrow(d,[(3305,1650),(3460,1650),(3460,450),(3305,450)],GREEN)
    label(d,(1800,1870),"בדיקה שקרית מדלגת על הקפיצה המותנית בלי לבצע אותה" if he else "A false test skips its guarded GOTO without executing it",45,he=he)
    label(d,(1800,1970),"אין צורך בסעיף אחר ואין צורך בתנועה לאחור" if he else "No ELSE branch and no backward movement are needed",45,he=he)
    label(d,(1800,2080),"MF / if P / GOTO : T=1",46,GRAY)
    im.save(OUT/f"prep-062-local-program-{lang}.png")


def duck(lang):
    he=lang=="he";im=Image.new("RGB",(3600,2200),"white");d=ImageDraw.Draw(im)
    label(d,(1800,110),"בריחה באמצעות יתרון במהירות הזוויתית" if he else "Escape by gaining an angular-speed advantage",65,bold=True,he=he)
    cx,cy,R=1120,1100,730;r=R*6/25
    d.ellipse((cx-R,cy-R,cx+R,cy+R),fill="#f0f7ff",outline=BLUE,width=7)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=GRAY,width=5)
    # Dashed diameter and a clean final sprint, duck opposite fox at departure.
    d.line((cx-R,cy,cx+R,cy),fill="#c2cbd9",width=4)
    arrow(d,[(cx-r-20,cy),(cx-R+20,cy)],GREEN,11)
    d.ellipse((cx-r-22,cy-22,cx-r+22,cy+22),fill=BLUE)
    d.ellipse((cx+R-23,cy-23,cx+R+23,cy+23),fill=RED)
    d.ellipse((cx-R-23,cy-23,cx-R+23,cy+23),fill=GREEN)
    label(d,(cx-r,cy+80),"D",54,BLUE,bold=True)
    label(d,(cx+R+70,cy),"F",54,RED,bold=True)
    label(d,(cx-R-70,cy),"Q",54,GREEN,bold=True)
    label(d,(cx+45,cy+65),"O",45,GRAY)
    label(d,(cx-r/2,cy-70),"r",45,GRAY,bold=True)
    label(d,(cx-r-(R-r)/2,cy+90),"R-r=0.76R",44,GREEN,bold=True)
    arc=[(cx+R*cos(a),cy-R*sin(a)) for a in [pi*i/120 for i in range(121)]]
    arrow(d,arc,RED,10)
    label(d,(cx,cy-R-75),"pi*R",51,RED,bold=True)
    # Orbit arrow shows motion is inside the pond, not on the shore.
    orbit=[(cx+r*cos(a),cy-r*sin(a)) for a in [pi*.15+pi*1.25*i/80 for i in range(81)]]
    arrow(d,orbit,BLUE,7)
    for y,n,heading,formula in (
        (430,"1","לשחות למעגל פנימי" if he else "Reach the inner circle","r=6R/25=0.24R < R/4"),
        (950,"2","להגיע מול השועל" if he else "Become opposite the fox","v/r > 4v/R"),
        (1470,"3","לברוח בקו ישר החוצה" if he else "Sprint straight to the shore","(R-r)/v < pi*R/(4v)")):
        box(d,(2140,y-90,3460,y+260),GREEN if n=="3" else BLUE)
        label(d,(2270,y+20),n,65,GREEN if n=="3" else BLUE,bold=True)
        label(d,(2850,y+10),heading,48,bold=True,he=he)
        label(d,(2800,y+150),formula,43,GREEN if n=="3" else BLUE,bold=True)
    label(d,(1800,1930),"השועל נשאר על הגדה והברווז יכול לשחות בכל כיוון בתוך האגם" if he else "The fox stays on the shore; the duck may swim in any direction inside",44,he=he)
    label(d,(1800,2050),"0.76 R/v < 0.785398... R/v     |     margin > 0",47,GREEN,bold=True)
    im.save(OUT/f"prep-063-duck-fox-escape-{lang}.png")


def prisoners(lang):
    he=lang=="he";im=Image.new("RGB",(3400,2000),"white");d=ImageDraw.Draw(im)
    label(d,(1700,110),"מאה ואחד אסירים עם שתי נורות" if he else "101 prisoners with two lights",65,bold=True,he=he)
    label(d,(1700,230),"N=101    |    m=100",46,GRAY)
    for x,known in ((180,True),(1780,False)):
        box(d,(x,400,x+1440,1200),BLUE if known else GREEN,"#f2f6fd" if known else "#eff8f3")
        heading="מצב התחלתי כבוי ידוע" if he and known else "מצב התחלתי לא ידוע" if he else "Initially BOTH OFF" if known else "Unknown initial lights"
        label(d,(x+720,510),heading,50,bold=True,he=he)
        label(d,(x+720,700),"sent <= 1" if known else "sent <= 2",58,BLUE if known else GREEN,bold=True)
        label(d,(x+720,880),"C_target=100" if known else "C_target=200",57,BLUE if known else GREEN,bold=True)
        label(d,(x+720,1020),"אם מדווח אחד טרם ביקר" if he else "If one contributor has not visited",39,GRAY,he=he)
        label(d,(x+720,1110),"C<=99" if known else "C<=199",43,GRAY)
    box(d,(180,1330,3220,1680),ORANGE,"#fffaed")
    label(d,(1700,1420),"נורה אחת שומרת אות ונורה שנייה מאפשרת פעולת דמה" if he else "One light stores a token; the other permits a dummy action",48,ORANGE,bold=True,he=he)
    label(d,(1700,1550),"אם לא משנים את נורת האות הופכים את נורת הדמה" if he else "If no signal action applies, toggle the dummy light",47,he=he)
    label(d,(1700,1790),"משנים בדיוק נורה אחת ולכן מקיימים גם היתר לשנות אחת או שתיים" if he else "Exactly one changed light also satisfies permission to change one OR both",43,he=he)
    label(d,(1700,1900),"אין חסם זמן קבוע ונדרשת הוגנות בביקורים" if he else "Fair repeated visits are required; no fixed visit bound",44,GRAY,he=he)
    im.save(OUT/f"prep-054-101-prisoners-{lang}.png")


if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    for language in ("he","en"):
        trajectories(language);program(language);duck(language);prisoners(language)
