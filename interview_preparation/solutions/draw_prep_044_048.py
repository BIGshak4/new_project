"""Reusable raster schematics: Fibonacci datapath and modulo-three pulse FSM."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
S = 2
INK, BLUE, GREEN, LIGHT = "#27364c", "#566999", "#287d70", "#f3f6fb"


class Canvas:
    def __init__(self, width, height):
        self.im = Image.new("RGB", (width * S, height * S), "white")
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, value, size=26, color=INK):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * S)
        self.d.text((x * S, y * S), str(value), fill=color, font=font, anchor="mm")

    def line(self, points, color=BLUE, width=3, arrow=False):
        self.d.line([(x * S, y * S) for x, y in points], fill=color, width=width * S, joint="curve")
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            a = math.atan2(y - py, x - px)
            tri = [(x, y)] + [(x - 15 * math.cos(a + t), y - 15 * math.sin(a + t)) for t in (-0.45, 0.45)]
            self.d.polygon([(x * S, y * S) for x, y in tri], fill=color)

    def box(self, x, y, w, h, title, subtitle):
        self.d.rounded_rectangle((x * S, y * S, (x + w) * S, (y + h) * S), radius=14 * S,
                                 fill=LIGHT, outline=BLUE, width=3 * S)
        self.text(x + w / 2, y + h * 0.35, title, 32)
        self.text(x + w / 2, y + h * 0.69, subtitle, 23)

    def curve(self, pts, color=BLUE):
        p, q, r, s = pts
        route = []
        for i in range(101):
            t = i / 100
            route.append(tuple((1-t)**3*p[k] + 3*(1-t)**2*t*q[k] + 3*(1-t)*t*t*r[k] + t**3*s[k] for k in (0, 1)))
        self.line(route, color, arrow=True)

    def label(self, x, y, value, color=INK):
        self.d.rounded_rectangle(((x-22)*S, (y-24)*S, (x+22)*S, (y+24)*S), radius=8*S, fill="white")
        self.text(x, y, value, 32, color)

    def save(self, name):
        target = ROOT / "diagrams" / name
        self.im.save(target)
        print(target)


def fibonacci():
    c = Canvas(1500, 1130)
    c.text(750, 55, "F(k+2) = F(k+1) + F(k)", 38)
    c.text(750, 108, "a_next = b       b_next = (a + b) mod 2^W", 28)
    c.box(230, 225, 300, 175, "a [W-1:0]", "D-FF; a(0) = 0")
    c.box(960, 225, 300, 175, "b [W-1:0]", "D-FF; b(0) = 1")
    c.line([(80, 310), (230, 310)], arrow=True)
    c.text(140, 270, "b", 30, GREEN)
    c.line([(530, 310), (710, 310)], arrow=True)
    c.text(610, 270, "a = F(k)", 28, GREEN)
    c.line([(795, 310), (960, 310)], arrow=True)
    c.text(860, 270, "sum", 28, GREEN)
    c.line([(1260, 310), (1430, 310)], arrow=True)
    c.text(1345, 270, "b = F(k+1)", 25, GREEN)
    for center in (380, 1110):
        c.line([(center, 470), (center, 400)], arrow=True)
        c.text(center, 500, "clk", 24)
    c.box(605, 570, 300, 170, "+", "sum [W-1:0]")
    c.line([(395, 615), (605, 615)], arrow=True)
    c.text(440, 580, "a", 30, GREEN)
    c.line([(395, 695), (605, 695)], arrow=True)
    c.text(440, 660, "b", 30, GREEN)
    c.line([(905, 655), (1140, 655)], arrow=True)
    c.text(1035, 615, "sum = (a+b) mod 2^W", 24, GREEN)
    c.text(750, 790, "a_next = b       b_next = sum       value = a", 27)
    labels = ["k", "a", "b"]
    values = [list(range(11)), [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
              [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]]
    for row in range(3):
        y = 900 + row * 60
        c.text(120, y, labels[row], 28)
        for i, value in enumerate(values[row]):
            c.text(250 + i * 112, y, value, 27)
        c.line([(180, y + 30), (1425, y + 30)], color="#d9e0ed", width=1)
    c.text(750, 1090, "k = 0..10; W >= 7", 26)
    c.save("prep-044-fibonacci-datapath.png")


def divider():
    c = Canvas(1500, 1150)
    c.text(750, 55, "f(pulse) = f(clk) / 3", 38)
    c.text(750, 108, "count: 0 -> 1 -> 2 -> 0       pulse_next = (count == 2)", 27)
    centers = [(330, 310), (1170, 310), (750, 640)]
    radius = 90
    for i, (x, y) in enumerate(centers):
        c.d.ellipse(((x-radius)*S, (y-radius)*S, (x+radius)*S, (y+radius)*S), fill=LIGHT, outline=BLUE, width=3*S)
        c.text(x, y-15, f"S{i}", 36)
        c.text(x, y+32, f"count = {i}", 24)
    c.curve(((420, 290), (630, 205), (870, 205), (1080, 290)))
    c.label(750, 218, "0")
    c.curve(((1130, 390), (1080, 530), (945, 615), (840, 635)))
    c.label(1040, 535, "0")
    c.curve(((660, 635), (530, 610), (405, 510), (365, 395)), GREEN)
    c.label(455, 535, "1", GREEN)
    c.text(750, 770, "clk ^ / pulse_next", 27)
    c.text(750, 815, "rst = 1: count = 0, pulse = 0", 27)
    rows = [("edge", list(range(1, 13))),
            ("count", [1, 2, 0] * 4),
            ("pulse", [0, 0, 1] * 4)]
    for row, (label, vals) in enumerate(rows):
        y = 885 + row*65
        c.text(100, y, label, 26)
        for i, value in enumerate(vals):
            x = 220 + i*105
            if label == "pulse" and value:
                c.d.rounded_rectangle(((x-35)*S, (y-26)*S, (x+35)*S, (y+26)*S), radius=10*S, fill="#e0f2e9")
            c.text(x, y, value, 27, GREEN if label == "pulse" and value else INK)
        c.line([(165, y+33), (1440, y+33)], color="#d9e0ed", width=1)
    c.text(750, 1105, "T(high) = T(clk)       T(pulse) = 3T(clk)       D = 1/3", 27)
    c.save("prep-048-third-clock-fsm-timing.png")


if __name__ == "__main__":
    fibonacci()
    divider()
