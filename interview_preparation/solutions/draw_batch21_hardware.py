"""Clean bilingual engineering diagrams for the 31 October hardware intake."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, PALE, GREEN, GRAY = "#fffdf8", "#302344", "#624883", "#eee7f5", "#30766a", "#ddd6e4"


def canvas(he, en, language, height=1500):
    image = Image.new("RGB", (2400, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 90), he, en, language, 54, bold=True, color=INK)
    return image, draw


def label(draw, xy, value, size=39, color=INK):
    text(draw, xy, value, size, bold=True, color=color)


def box(draw, rect, lines):
    draw.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=6)
    x1, y1, x2, y2 = rect
    for index, line in enumerate(lines, 1):
        label(draw, ((x1+x2)/2, y1+index*(y2-y1)/(len(lines)+1)), line)


def table(draw, rows, x, y, widths, language, height=83, size=35):
    for row_index, row in enumerate(rows):
        left = x
        for value, width in zip(row, widths, strict=True):
            draw.rectangle((left, y+row_index*height, left+width, y+(row_index+1)*height),
                           fill=PALE if row_index == 0 else BG, outline=GRAY, width=3)
            xy = (left+width/2, y+(row_index+.5)*height)
            if isinstance(value, tuple):
                phrase(draw, xy, *value, language, size, bold=True, color=INK)
            else:
                label(draw, xy, str(value), size)
            left += width


def curve(draw, start, control1, control2, end, value=None, caption=None):
    points = []
    for i in range(65):
        t = i/64
        points.append(tuple((1-t)**3*start[a]+3*(1-t)**2*t*control1[a]
                            +3*(1-t)*t*t*control2[a]+t**3*end[a] for a in (0, 1)))
    wire(draw, points, GREEN, 5)
    if value is not None:
        xy = caption or points[32]
        draw.rectangle((xy[0]-55,xy[1]-23,xy[0]+55,xy[1]+23),fill=BG)
        label(draw, xy, value, 34, GREEN)


def rotation(language):
    image, draw = canvas("סיבוב ימינה בשכבות של אחד, שניים וארבעה", "Rotate right in stages of one, two and four", language, 1420)
    for stage in range(3):
        x = 280+730*stage
        box(draw, (x, 380, x+520, 780), ["8 x MUX 2:1", f"S = s[{stage}]", f"d = {1 << stage}"])
        if stage:
            wire(draw, [(x-210, 580), (x, 580)], PURPLE)
    wire(draw, [(70, 580), (280, 580)], PURPLE)
    label(draw, (175, 490), "x[7:0]", 34)
    wire(draw, [(2260, 580), (2370, 580)], GREEN)
    label(draw, (2295, 875), "y[7:0]", 34)
    label(draw, (1200, 1030), "v_next[i] = MUX(s[j], v[i], v[(i+2^j) mod 8])", 42)
    label(draw, (1200, 1150), "10010110  -- s=3 -->  11010010", 48)
    phrase(draw, (1200, 1290), "כמות קבועה: חיווט בלבד; כמות משתנה: עשרים וארבעה מוקסים", "Fixed amount: wiring only; variable amount: twenty-four MUXes", language, 37)
    return image


def mux_switches(language):
    image, draw = canvas("שני ענפים נבחרים ומניין רכיבים מפורש", "Two selected branches with explicit device counting", language, 1960)
    phrase(draw, (1200, 230), "שערי תמסורת: שישה טרנזיסטורים כולל יצירת הבקרה ההפוכה", "Transmission gates: six transistors including select inversion", language, 41)
    # Four pass devices are drawn as distinct boxes in two parallel pairs.
    for base, source, ngate, pgate in [(400, "A", "nS", "S"), (1000, "B", "S", "nS")]:
        label(draw, (160, base+90), source, 52)
        wire(draw, [(210, base+90), (370, base+90)], PURPLE, arrow=False)
        wire(draw, [(370, base+90), (370, base), (710, base)], PURPLE)
        wire(draw, [(370, base+90), (370, base+180), (710, base+180)], PURPLE)
        draw.ellipse((361, base+81, 379, base+99), fill=PURPLE)
        box(draw, (710, base-65, 1320, base+65), [f"nMOS: G={ngate}"])
        box(draw, (710, base+115, 1320, base+245), [f"pMOS: G={pgate}"])
        wire(draw, [(1320, base), (1570, base), (1570, base+90)], GREEN, arrow=False)
        wire(draw, [(1320, base+180), (1570, base+180), (1570, base+90)], GREEN, arrow=False)
        draw.ellipse((1561, base+81, 1579, base+99), fill=GREEN)
        wire(draw, [(1570, base+90), (1840, base+90)], GREEN, arrow=False)
    wire(draw, [(1840, 490), (1840, 1090)], GREEN, arrow=False)
    wire(draw, [(1840, 790), (2260, 790)], GREEN)
    draw.ellipse((1831, 781, 1849, 799), fill=GREEN)
    label(draw, (2260, 700), "Y", 53)
    box(draw, (1860, 290, 2280, 470), ["nS = NOT S", "INV: 2T"])
    label(draw, (1200, 1390), "3 NAND2 + INV = 14T;    2 TG + INV = 6T", 47)
    label(draw, (1200, 1510), "2 nMOS + INV = 4T;    nS_ext: 2T", 45)
    label(draw, (1200, 1630), "nMOS: Vout_high <= VDD - Vtn", 43)
    phrase(draw, (1200, 1770), "פחות טרנזיסטורים אינם מבטיחים אותן רמות רעש והנעה", "Fewer devices do not guarantee the same noise margins or drive", language, 39)
    phrase(draw, (1200, 1870), "שער תמסורת עדיין משתמש בטרנזיסטורים משלימים", "A transmission gate still uses complementary devices", language, 39)
    return image


def counter(language):
    image, draw = canvas("שישה מצבים חוקיים ושלוש סיביות מצב", "Six legal states and three state bits", language, 1470)
    centers = [220+390*i for i in range(6)]
    for state, xx in enumerate(centers):
        draw.ellipse((xx-88, 420, xx+88, 596), fill=PALE, outline=PURPLE, width=6)
        label(draw, (xx, 507), str(state), 60)
        curve(draw, (xx-60, 445), (xx-145, 225), (xx+145, 225), (xx+60, 445), "e=0", (xx, 300))
        if state<5:
            wire(draw, [(xx+88, 507), (centers[state+1]-88, 507)], GREEN, 6)
            label(draw, (xx+195, 445), "e=1", 33, GREEN)
    curve(draw, (centers[5], 596), (centers[5], 900), (centers[0], 900), (centers[0], 596), "e=1", (1200, 825))
    box(draw, (500, 1020, 1900, 1230), ["rst=1: next=0", "count>=6: next=0; e=0|1"])
    phrase(draw, (1200, 1350), "איפוס סינכרוני גובר על התאוששות ועל אפשור", "Synchronous reset overrides recovery and enable", language, 43)
    return image


def fsm(language, pattern):
    image, draw = canvas("זיהוי רצף ושימור חפיפות", f"Detect {pattern} while retaining overlaps", language, 2280 if pattern == "0101" else 1820)
    label(draw, (1200, 195), f"pattern = {pattern}; Moore z = (state == Q4)", 44)
    xs, y, radius = [300, 750, 1200, 1650, 2100], 565, 95
    for state, xx in enumerate(xs):
        draw.ellipse((xx-radius, y-radius, xx+radius, y+radius), fill=PALE, outline=PURPLE, width=6)
        if state==4:
            draw.ellipse((xx-radius+13, y-radius+13, xx+radius-13, y+radius-13), outline=GREEN, width=5)
        label(draw, (xx, y-25), f"Q{state}", 44)
        prefix = "--" if state==0 else pattern[:state]
        label(draw, (xx, y+35), prefix, 33)
        if state<4:
            wire(draw, [(xx+radius, y), (xs[state+1]-radius, y)], GREEN, 6)
            label(draw, ((xx+xs[state+1])/2, y-55), pattern[state], 36, GREEN)
    wire(draw, [(45, y), (xs[0]-radius, y)], PURPLE)
    if pattern == "1101":
        transitions = ((0,1),(0,2),(3,2),(0,4),(0,2))
        loops = [(0,"0"),(2,"1")]
        arcs = [(1,0,"0",310),(4,2,"1",220),(3,0,"0",925),(4,0,"0",1110)]
    else:
        transitions = ((1,0),(1,2),(3,0),(1,4),(3,0))
        loops = [(0,"1"),(1,"0")]
        arcs = [(4,3,"0",300),(2,0,"1",920),(3,1,"0",1080),(4,0,"1",1250)]
    for state, bit in loops:
        xx=xs[state]
        curve(draw,(xx-60,y-74),(xx-160,y-280),(xx+160,y-280),(xx+60,y-74),bit,(xx,y-230))
    for source,target,bit,level in arcs:
        offset=-85 if level<y else 85
        label_y = .25*(y+offset)+.75*level+(-45 if level<y else 45)
        curve(draw,(xs[source],y+offset),(xs[source],level),(xs[target],level),(xs[target],y+offset),bit,((xs[source]+xs[target])/2,label_y))
    top = 1300 if pattern=="0101" else 1160
    rows = [[("מצב", "state"), "x=0", "x=1", "z"]]
    rows += [[f"Q{i}",f"Q{t[0]}",f"Q{t[1]}",int(i==4)]for i,t in enumerate(transitions)]
    table(draw, rows, 540, top, [330]*4, language, 69, 34)
    if pattern == "0101":
        box(draw, (220, 1855, 1200, 2095), ["FIFO[4 x 1]", "DIN=x; rst: full=0", "POP(if full) + PUSH"])
        box(draw, (1510, 1855, 2270, 2095), ["w[3:0]", "full AND (w=0101)"])
        wire(draw, [(1200, 1975), (1510, 1975)], GREEN)
        phrase(draw,(1200,2200),"חלופת התור כוללת זיכרון וצפייה בארבעה איברים", "FIFO alternative includes storage and four-entry peek",language,39)
    else:
        phrase(draw,(1200,1710),"פלט לאחר החזית: חמישה מצבים בקידוד של שלושה דלגלגים", "Post-edge output: five states encoded by three FFs",language,40)
    return image


def mos(draw, x, y, pmos=False):
    draw.line((x, y-80, x, y+80), fill=PURPLE, width=7)
    draw.line((x-38, y-65, x-38, y+65), fill=PURPLE, width=6)
    if pmos:
        draw.ellipse((x-78,y-15,x-48,y+15),outline=PURPLE,width=4,fill=BG)
        draw.line((x-155,y,x-78,y),fill=PURPLE,width=6)
    else:
        draw.line((x-155,y,x-38,y),fill=PURPLE,width=6)
    draw.line((x,y-80,x+90,y-80),fill=PURPLE,width=6)
    draw.line((x,y+80,x+90,y+80),fill=PURPLE,width=6)


def inverter(language):
    image, draw = canvas("מהפך משלים עם שמות ההדקים", "CMOS inverter with terminal names", language, 1570)
    x=1020
    mos(draw,x,500,True);mos(draw,x,970,False)
    wire(draw,[(x+90,420),(x+90,250)],PURPLE,arrow=False)
    label(draw,(x+90,205),"VDD",48)
    wire(draw,[(x+90,580),(x+90,890)],GREEN,arrow=False)
    wire(draw,[(x+90,1050),(x+90,1210)],PURPLE,arrow=False)
    label(draw,(x+90,1265),"GND",48)
    wire(draw,[(x-155,500),(650,500),(650,970),(x-155,970)],PURPLE,arrow=False)
    wire(draw,[(300,735),(650,735)],PURPLE,arrow=False)
    draw.ellipse((641,726,659,744),fill=PURPLE)
    label(draw,(300,665),"Vin",50)
    wire(draw,[(x+90,735),(2020,735)],GREEN)
    draw.ellipse((x+81,726,x+99,744),fill=GREEN)
    label(draw,(2020,665),"Vout",50)
    for yy,device,source,drain,body in [(500,"PMOS","S: VDD","D: Vout","B/well: VDD"),(970,"NMOS","S: GND","D: Vout","B: GND")]:
        label(draw,(1600,yy-70),device,47)
        label(draw,(1640,yy+5),source+"; "+drain,35)
        label(draw,(1640,yy+78),"G: Vin; "+body,35)
    table(draw,[["Vin","PMOS","NMOS","Vout"],["0","ON","OFF","VDD"],["VDD","OFF","ON","0"]],300,1340,[450]*4,language,65,33)
    return image


def allocation(language):
    image, draw = canvas("תפוסה ובחירת כתובת אחרי שחרור", "Occupancy and address selection after release", language, 1550)
    box(draw,(150,340,750,680),["used[31:0]","pop_success","effective_used"])
    box(draw,(1010,340,1610,680),["free = NOT effective_used","PE32","free_valid, addr[4:0]"])
    box(draw,(1840,340,2300,680),["push & free_valid","RAM[addr] <= data","used_next[addr]=1"])
    wire(draw,[(750,510),(1010,510)],PURPLE)
    wire(draw,[(1610,510),(1840,510)],GREEN)
    label(draw,(1200,900),"payload[31:0][31:0] + used[31:0]",46)
    table(draw,[[('תפוסה לפני החזית','used before'),"pop","push","push_success / addr"],["FFFF_FFFF","7","1","1 / 7"],["FFFF_FFFF","--","1","0 / --"]],200,1030,[600,300,300,800],language,92,37)
    phrase(draw,(1200,1430),"איפוס מנקה תפוסה, לא מוחק פיזית את הנתונים", "Reset clears occupancy; it does not physically scrub payload",language,40)
    return image


def prime_scope(language):
    image, draw = canvas("שתי פונקציות שונות בגלל תחום השלילה", "Negation scope gives two different functions", language, 1570)
    for y, names in [(430,["S=b, D0=1, D1=c","q = NOT b OR c","S=a, D0=1, D1=q"]),
                     (1030,["S=c, D0=b, D1=0","r = b AND NOT c","S=a, D0=0, D1=r"])]:
        box(draw,(250,y-140,1020,y+140),["MUX 2:1",names[0]])
        box(draw,(1450,y-140,2220,y+140),["MUX 2:1",names[2]])
        wire(draw,[(1020,y),(1450,y)],GREEN)
        label(draw,(1235,y-90),"q"if y==430 else "r",47)
        label(draw,(1200,y+225),names[1],43)
    label(draw,(1200,210),"F = NOT(a AND b AND NOT c)",46)
    label(draw,(1200,810),"P = a AND b AND NOT c",46)
    label(draw,(1200,1405),"a=1, b=1, c=0  =>  F=0, P=1",48)
    return image


def matrix(language):
    image, draw = canvas("היפוך עמודות שומר על סדר השורות", "Column reversal preserves row order", language, 1470)
    first=["011101","001111","101100"];second=["101110","111100","001101"]
    for side,rows in [(210,first),(1490,second)]:
        for row,word in enumerate(rows):
            label(draw,(side-85,480+175*row),f"r={row}",34)
            for col,bit in enumerate(word):
                xx=side+col*118;yy=430+row*175
                draw.rectangle((xx,yy,xx+100,yy+100),fill=PALE,outline=PURPLE,width=4)
                label(draw,(xx+50,yy+50),bit,51)
    wire(draw,[(1030,655),(1340,655)],GREEN)
    label(draw,(1200,1050),"y[r][c] = x[r][C-1-c]",54)
    label(draw,(1200,1170),"flat_source = r*C + (C-1-c)",47)
    phrase(draw,(1200,1320),"חיווט מקביל קבוע; לא טרנספוזיציה ולא היפוך כל האפיק", "Fixed parallel wiring; neither transpose nor reversal of the full bus",language,38)
    return image


if __name__ == "__main__":
    renderers=[(199,"barrel-rotation",rotation),(200,"mux-switch-topologies",mux_switches),
               (202,"enabled-mod6",counter),(204,"1101-moore",lambda lg:fsm(lg,"1101")),
               (205,"cmos-inverter",inverter),(207,"0101-overlap-storage",lambda lg:fsm(lg,"0101")),
               (102,"push-pop-address",allocation),(11,"prime-scope",prime_scope),(94,"matrix-axis",matrix)]
    for number,stem,render in renderers:
        for language in ("he","en"):
            render(language).save(OUT/f"prep-{number:03d}-{stem}-batch21-{language}.png")
