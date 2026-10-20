"""Deterministic bilingual solution figures; Pillow only, editable generator.

Formula/signal labels use LTR. Pure Hebrew labels are reversed separately for
the bundled non-RAQM Pillow runtime; mixed expressions are never reversed.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BLUE, GREEN, INK, MUTED, ORANGE = "#365da5", "#277969", "#17243c", "#65758b", "#af671b"
FONT = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"


class Canvas:
    def __init__(self, title, subtitle):
        self.im = Image.new("RGB", (3000, 1900), "#fcfdff")
        self.d = ImageDraw.Draw(self.im)
        self.text((1500, 100), title, 66, bold=True)
        self.text((1500, 200), subtitle, 40, color=MUTED)

    def text(self, point, text, size=42, color=INK, bold=False, he=False):
        if he:
            text = text[::-1]
        self.d.text(point, text, font=ImageFont.truetype(BOLD if bold else FONT, size), fill=color, anchor="mm")

    def box(self, coords, fill="#eef3ff", outline=BLUE, width=5, radius=25):
        self.d.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)

    def wire(self, points, color=BLUE, width=7, arrow=True):
        self.d.line(points, fill=color, width=width, joint="curve")
        if arrow:
            a, b = points[-2], points[-1]
            theta = math.atan2(b[1]-a[1], b[0]-a[0])
            pts = [b]
            for delta in (-0.45, 0.45):
                pts.append((b[0]-30*math.cos(theta+delta), b[1]-30*math.sin(theta+delta)))
            self.d.polygon(pts, fill=color)

    def dot(self, p, color=BLUE):
        self.d.ellipse((p[0]-10,p[1]-10,p[0]+10,p[1]+10),fill=color)

    def save(self, stem, lang):
        OUT.mkdir(parents=True, exist_ok=True)
        self.im.save(OUT / f"{stem}-{lang}.png")


def caption(c, lang, y, he, en, size=42):
    c.text((1500,y), he if lang=="he" else en, size, he=lang=="he")


def lists(lang):
    c = Canvas("PREP-032", "p: A -> B       q: B -> A       p is q")
    caption(c,lang,320,"אותו צומת בזיכרון ולא ערכים שווים","Shared node identity, not equal stored values",52)
    centers = {"A1":(400,650),"A2":(900,650),"B1":(900,1130),"C1":(1550,880),"C2":(2200,880)}
    for name,(x,y) in centers.items():
        common = name.startswith("C")
        c.box((x-130,y-100,x+130,y+100),fill="#e9f7f0" if common else "#eef3ff",outline=GREEN if common else BLUE)
        c.text((x,y-20),name,52,bold=True)
        c.text((x,y+48),"7",31,color=MUTED)
    c.wire([(530,650),(770,650)])
    c.wire([(1030,650),(1250,650),(1250,880),(1420,880)])
    c.wire([(1030,1130),(1250,1130),(1250,880)],arrow=False)
    c.dot((1250,880))
    c.wire([(1680,880),(2070,880)],color=GREEN)
    c.wire([(2330,880),(2680,880)],color=GREEN)
    c.text((2770,880),"None",45)
    c.text((180,650),"head_a",36)
    c.text((660,1130),"head_b",36)
    caption(c,lang,1390,"שני החצים מתחברים לאותו זנב משותף","Both paths join the SAME physical suffix",44)
    c.text((1500,1530),"p = head_b if p is None else p.next",43)
    c.text((1500,1620),"q = head_a if q is None else q.next",43)
    c.text((1500,1750),"T = O(m+n)     |     S = O(1)",42,color=GREEN)
    c.save("prep-032-head-switch",lang)


def enable(lang):
    c=Canvas("PREP-056", "D_next = (en AND data) OR ((NOT en) AND Q)")
    caption(c,lang,330,"בוחרים נתון חדש או מחזירים את המצב השמור","Select new data or feed back the stored value",50)
    c.d.polygon([(1100,600),(1400,720),(1400,1180),(1100,1300)],fill="#eef3ff",outline=BLUE,width=6)
    c.text((1250,950),"MUX",52,bold=True)
    c.text((1140,760),"1",48)
    c.text((1140,1140),"0",48)
    c.box((1830,700,2250,1210),fill="#e9f7f0",outline=GREEN)
    c.text((2040,880),"DFF",55,bold=True)
    c.text((1870,950),"D",42)
    c.text((2200,950),"Q",42)
    c.d.line([(1990,1210),(2020,1160),(2050,1210)],fill=GREEN,width=5)
    c.wire([(450,760),(1100,760)])
    c.text((350,760),"data",45)
    c.wire([(1400,950),(1830,950)])
    c.text((1615,875),"D_next",40,color=BLUE)
    c.wire([(2250,950),(2710,950)],color=GREEN)
    c.text((2780,950),"Q",50,color=GREEN,bold=True)
    c.dot((2500,950),GREEN)
    c.wire([(2500,950),(2500,1460),(820,1460),(820,1140),(1100,1140)],color=GREEN)
    c.wire([(1250,490),(1250,660)],color=ORANGE)
    c.text((1250,445),"en",50,color=ORANGE,bold=True)
    c.wire([(2020,1380),(2020,1210)],color=MUTED)
    c.text((2120,1325),"clk",38,color=MUTED)
    c.text((1500,1600),"en = 1: Q_next = data      |      en = 0: Q_next = Q",43)
    caption(c,lang,1740,"אותו שעון לדלגלג ללא שער על קו השעון","The DFF keeps the original clock; do not gate clk",42)
    c.save("prep-056-enable-feedback-mux",lang)


def average(lang):
    c=Canvas("PREP-058", "N >= 2     |     b = a + 2     |     0 <= a,b < 2^N")
    caption(c,lang,320,"בחירה בין הביטים העליונים לפי הביט הנמוך","Select the upper bits using the low input bit",50)
    c.box((1190,530,1680,1160))
    c.text((1435,710),"N-1",55,bold=True)
    c.text((1435,785),"MUX 2:1",45,bold=True)
    c.text((1235,650),"0",48)
    c.text((1235,1030),"1",48)
    c.wire([(610,650),(1190,650)])
    c.text((390,650),"a[N-1:1]",45)
    c.wire([(610,1030),(1190,1030)])
    c.text((390,1030),"b[N-1:1]",45)
    c.wire([(1680,845),(2330,845)],color=GREEN)
    c.text((2580,845),"y[N-1:1]",45,color=GREEN)
    c.wire([(1435,380),(1435,530)],color=ORANGE)
    c.text((1190,420),"s = a[0]",43,color=ORANGE)
    c.wire([(610,1370),(1190,1370)],color=ORANGE)
    c.text((390,1370),"a[0]",45,color=ORANGE)
    c.d.polygon([(1190,1270),(1190,1470),(1400,1370)],outline=BLUE,fill="#eef3ff",width=5)
    c.d.ellipse((1400,1355,1430,1385),fill="white",outline=BLUE,width=5)
    c.wire([(1430,1370),(2330,1370)],color=GREEN)
    c.text((2540,1370),"y[0]",45,color=GREEN)
    c.text((1500,1580),"y_i = ((NOT s) AND a_i) OR (s AND b_i),   i >= 1",43)
    caption(c,lang,1740,"כל בורר ממומש בשערי וגם או ולא בלבד","Each selector uses only AND / OR / NOT gates",42)
    c.save("prep-058-average-gate-select",lang)


def coins(lang):
    c=Canvas("PREP-059", "k > 10       |       T_total = 10")
    caption(c,lang,320,"בוחרים עשרה מטבעות בלי לראות והופכים רק אותם","Choose any ten unseen coins; flip only those ten",50)
    c.box((220,500,1370,1150))
    c.box((1630,500,2780,1150),fill="#e9f7f0",outline=GREEN)
    c.text((795,610),"|A| = 10",50,bold=True)
    c.text((2205,610),"|B| = k - 10",50,bold=True,color=GREEN)
    c.text((795,780),"T = x",58)
    c.text((795,900),"H = 10 - x",58)
    c.text((2205,840),"T = 10 - x",58)
    c.wire([(795,1150),(795,1350)],color=ORANGE)
    c.wire([(2205,1150),(2205,1350)],color=GREEN)
    c.text((1080,1250),"הופכים את כולם" if lang=="he" else "FLIP ALL A",36,color=ORANGE,bold=True,he=lang=="he")
    c.text((2450,1250),"לא הופכים" if lang=="he" else "NO FLIPS",36,color=GREEN,bold=True,he=lang=="he")
    c.box((220,1360,1370,1550),fill="#fff5e8",outline=ORANGE)
    c.box((1630,1360,2780,1550),fill="#e9f7f0",outline=GREEN)
    c.text((795,1455),"T' = 10 - x",53,color=ORANGE)
    c.text((2205,1455),"T' = 10 - x",53,color=GREEN)
    caption(c,lang,1710,"הסימון אלגברי בלבד ואינו מידע שאפשר לראות בחדר","The algebra is explanatory; orientations remain hidden",40)
    c.save("prep-059-blind-ten-coin-flip",lang)


if __name__ == "__main__":
    for lang in ("he","en"):
        for draw in (lists,enable,average,coins):
            draw(lang)
    print("Created 8 bilingual PNG figures.")
