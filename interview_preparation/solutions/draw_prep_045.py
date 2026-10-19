"""Rebuild the first-finisher schematic and Moore graph as clean PNG assets."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
INK, WIRE, GREEN = "#26334a", "#56699c", "#267665"


class Canvas:
    def __init__(self, width, height):
        self.image = Image.new("RGB", (width * SCALE, height * SCALE), "white")
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, text, size=27, color=INK):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * SCALE)
        self.draw.text((x * SCALE, y * SCALE), text, font=font, fill=color, anchor="mm")

    def line(self, points, arrow=False, color=WIRE, width=3):
        self.draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=color,
                       width=width * SCALE, joint="curve")
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            theta = math.atan2(y - py, x - px)
            triangle = [(x, y)] + [(x - 16 * math.cos(theta + a), y - 16 * math.sin(theta + a))
                                   for a in (-0.43, 0.43)]
            self.draw.polygon([(a * SCALE, b * SCALE) for a, b in triangle], fill=color)

    def dot(self, x, y):
        self.draw.ellipse(((x - 5) * SCALE, (y - 5) * SCALE,
                           (x + 5) * SCALE, (y + 5) * SCALE), fill=WIRE)

    def box(self, x, y, w, h, name, sub=""):
        self.draw.rounded_rectangle((x * SCALE, y * SCALE, (x + w) * SCALE, (y + h) * SCALE),
                                    radius=14 * SCALE, fill="#f4f6fb", outline=WIRE, width=3 * SCALE)
        self.text(x + w / 2, y + h * .38, name, 32)
        if sub:
            self.text(x + w / 2, y + h * .67, sub, 26)

    def label(self, x, y, text, color=WIRE):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 27 * SCALE)
        bounds = self.draw.textbbox((0, 0), text, font=font)
        width = (bounds[2] - bounds[0]) / SCALE + 24
        self.draw.rounded_rectangle(((x - width / 2) * SCALE, (y - 22) * SCALE,
                                    (x + width / 2) * SCALE, (y + 22) * SCALE),
                                    radius=10 * SCALE, fill="white")
        self.text(x, y, text, 27, color)

    def curve(self, points, label, xy, color=WIRE):
        route = []
        for step in range(121):
            t = step / 120
            route.append(tuple((1 - t) ** 3 * points[0][j]
                               + 3 * (1 - t) ** 2 * t * points[1][j]
                               + 3 * (1 - t) * t ** 2 * points[2][j]
                               + t ** 3 * points[3][j] for j in (0, 1)))
        self.line(route, arrow=True, color=color)
        self.label(*xy, label, color)

    def save(self, name):
        target = ROOT / "diagrams" / name
        self.image.save(target)
        print(target)


def schematic():
    c = Canvas(1660, 920)
    c.text(830, 60, "winner_next = rst ? 00 : (winner == 00 ? candidate : winner)", 31)
    c.box(260, 180, 300, 230, "ENC", "1 > 2 > 3")
    c.box(1040, 200, 140, 230, "MUX")
    c.box(1280, 200, 200, 230, "D-FF", "[1:0]")
    for pin, y in ((1, 225), (2, 295), (3, 365)):
        c.text(100, y, f"p{pin}", 31)
        c.line([(145, y), (260, y)], arrow=True)
    c.line([(560, 270), (1040, 270)], arrow=True)
    c.label(790, 240, "candidate[1:0]")
    c.text(1065, 270, "1", 23)
    c.text(1065, 360, "0", 23)
    c.line([(1180, 315), (1280, 315)], arrow=True)
    c.line([(1480, 315), (1595, 315)], arrow=True)
    c.text(1540, 255, "winner", 28)
    c.dot(1520, 315)
    c.line([(1520, 315), (1520, 545), (820, 545), (820, 360), (1040, 360)], arrow=True)
    c.label(1240, 545, "winner[1:0]")
    c.dot(820, 545)
    c.line([(820, 545), (820, 650)], arrow=True)
    c.box(670, 650, 300, 120, "== 00")
    c.line([(970, 710), (1005, 710), (1005, 480), (1110, 480), (1110, 430)], arrow=True)
    c.label(1125, 655, "unlocked")
    c.line([(1380, 495), (1380, 430)], arrow=True)
    c.text(1380, 525, "clk", 26)
    c.text(1380, 615, "rst = 1  =>  00", 26)
    c.text(830, 835, "00 : WAIT     01 : W1     10 : W2     11 : W3", 27)
    c.text(830, 885, "posedge clk; rst=1 => winner_next=00", 25)
    c.save("prep-045-first-finisher-circuit.png")


def state_graph():
    c = Canvas(1600, 1100)
    c.text(800, 50, "rst=0; p1 > p2 > p3", 33)
    c.curve(((738, 305), (650, 350), (350, 450), (355, 688)), "p1 = 1", (455, 460), GREEN)
    c.curve(((800, 330), (800, 450), (800, 560), (800, 668)), "p1=0, p2=1", (895, 490), GREEN)
    c.curve(((862, 305), (950, 350), (1250, 450), (1245, 688)),
            "p1=0, p2=0, p3=1", (1150, 460), GREEN)
    c.curve(((745, 173), (590, 70), (1020, 70), (855, 173)), "000", (800, 130))
    for x in (300, 800, 1300):
        c.curve(((x - 65, 820), (x - 230, 1030), (x + 230, 1030), (x + 65, 820)),
                "***", (x, 960))
    c.line([(500, 240), (710, 240)], arrow=True)
    c.label(555, 205, "rst=1")
    for x, y, title, output in ((800, 240, "WAIT", "00"),
                                (300, 760, "W1", "01"),
                                (800, 760, "W2", "10"),
                                (1300, 760, "W3", "11")):
        c.draw.ellipse(((x - 90) * SCALE, (y - 90) * SCALE,
                        (x + 90) * SCALE, (y + 90) * SCALE),
                       fill="#f4f6fb", outline=WIRE, width=3 * SCALE)
        c.text(x, y - 20, title, 32)
        c.text(x, y + 29, output, 31, GREEN)
    c.text(800, 1030, "p=(p1,p2,p3); ***={000,001,010,011,100,101,110,111}", 26)
    c.text(800, 1070, "rst=1 => Q_next=00", 26)
    c.save("prep-045-first-finisher-fsm.png")


if __name__ == "__main__":
    schematic()
    state_graph()
