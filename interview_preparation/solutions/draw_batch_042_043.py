"""Language-neutral component schematic and complete ABCD Mealy state graph."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
INK, BLUE, GREEN = "#28354c", "#566599", "#2b7d70"


class Canvas:
    def __init__(self, width, height):
        self.image = Image.new("RGB", (width * SCALE, height * SCALE), "white")
        self.draw = ImageDraw.Draw(self.image)

    def text(self, x, y, value, size=27, color=INK):
        font_path = "C:/Windows/Fonts/seguisym.ttf" if "∉" in value else "C:/Windows/Fonts/arial.ttf"
        font = ImageFont.truetype(font_path, size * SCALE)
        self.draw.text((x * SCALE, y * SCALE), value, font=font, fill=color, anchor="mm")

    def line(self, points, color=BLUE, width=3, arrow=False):
        self.draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=color, width=width * SCALE, joint="curve")
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            angle = math.atan2(y - py, x - px)
            triangle = [(x, y)] + [(x - 17 * math.cos(angle + d), y - 17 * math.sin(angle + d)) for d in (-0.44, 0.44)]
            self.draw.polygon([(a * SCALE, b * SCALE) for a, b in triangle], fill=color)

    def curve(self, points, label, label_at, color=BLUE):
        p0, p1, p2, p3 = points
        route = []
        for step in range(101):
            t = step / 100
            route.append(tuple((1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * p1[j]
                               + 3 * (1 - t) * t * t * p2[j] + t ** 3 * p3[j] for j in (0, 1)))
        self.line(route, color=color, arrow=True)
        self.label(*label_at, label, color)

    def label(self, x, y, value, color=BLUE):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26 * SCALE)
        box = self.draw.textbbox((0, 0), value, font=font)
        w = (box[2] - box[0]) / SCALE + 20
        self.draw.rounded_rectangle(((x - w / 2) * SCALE, (y - 20) * SCALE, (x + w / 2) * SCALE, (y + 20) * SCALE), radius=9 * SCALE, fill="white")
        self.text(x, y, value, 26, color)

    def box(self, x, y, width, height, title, sub=None):
        self.draw.rounded_rectangle((x * SCALE, y * SCALE, (x + width) * SCALE, (y + height) * SCALE), radius=12 * SCALE, fill="#f6f7fb", outline=BLUE, width=3 * SCALE)
        self.text(x + width / 2, y + height * 0.38, title, 32)
        if sub:
            self.text(x + width / 2, y + height * 0.65, sub, 24)

    def save(self, filename):
        target = ROOT / "diagrams" / filename
        self.image.save(target)
        print(target)


def rising_diagram():
    c = Canvas(1650, 680)
    c.text(825, 55, "pulse[n] = x[n] & ~x[n-1]", 36)
    c.box(410, 140, 210, 180, "D-FF", "previous")
    c.box(760, 145, 160, 120, "NOT")
    c.box(995, 375, 160, 170, "AND")
    c.box(1250, 375, 210, 170, "D-FF", "pulse")
    c.text(70, 495, "x", 32)
    c.line([(100, 495), (250, 495), (995, 495)], arrow=True)
    c.draw.ellipse((245 * SCALE, 490 * SCALE, 255 * SCALE, 500 * SCALE), fill=BLUE)
    c.line([(250, 495), (250, 205), (410, 205)], arrow=True)
    c.line([(620, 205), (760, 205)], arrow=True)
    c.line([(920, 205), (970, 205), (970, 430), (995, 430)], arrow=True)
    c.line([(1155, 460), (1250, 460)], arrow=True)
    c.line([(1460, 460), (1580, 460)], arrow=True)
    c.text(1555, 420, "pulse", 29)
    for center, bottom in ((515, 320), (1355, 545)):
        c.line([(center, bottom + 58), (center, bottom)], arrow=True)
        c.text(center, bottom + 86, "clk", 23)
    c.text(515, 113, "Q(0)=0", 23)
    c.text(1355, 349, "Q(0)=0", 23)
    c.text(825, 645, "rst=1: previous=0, pulse=0", 25)
    c.save("prep-042-rising-edge-registered.png")


def sequence_diagram():
    c = Canvas(1500, 1120)
    c.text(750, 48, "ABCD", 42)
    c.text(750, 1090, "* : x ∉ {A, B, C, D}", 26)
    centers = {0: (350, 275), 1: (1120, 275), 2: (1120, 790), 3: (350, 790)}
    c.curve(((435, 275), (630, 275), (840, 275), (1030, 275)), "A / 0", (735, 242))
    c.curve(((1120, 365), (1120, 490), (1120, 570), (1120, 698)), "B / 0", (1175, 535))
    c.curve(((1030, 790), (830, 790), (635, 790), (442, 790)), "C / 0", (735, 826))
    c.curve(((350, 700), (350, 570), (350, 490), (350, 368)), "D / 1", (405, 535), GREEN)
    c.curve(((1055, 215), (920, 100), (560, 100), (413, 209)), "C,D,* / 0", (735, 150))
    c.curve(((1168, 711), (1390, 590), (1390, 468), (1180, 350)), "A / 0", (1320, 535))
    c.curve(((410, 724), (580, 670), (860, 450), (1055, 336)), "A / 0", (790, 533))
    c.curve(((1045, 742), (890, 650), (570, 520), (420, 340)), "B,D,* / 0", (655, 560))
    c.curve(((290, 723), (100, 610), (100, 455), (288, 344)), "B,C,* / 0", (140, 535))
    c.curve(((290, 210), (120, 25), (150, 400), (264, 290)), "B,C,D,* / 0", (150, 190))
    c.curve(((1165, 195), (1320, 40), (1360, 370), (1208, 285)), "A / 0", (1320, 190))
    for state, (x, y) in centers.items():
        c.draw.ellipse(((x - 88) * SCALE, (y - 88) * SCALE, (x + 88) * SCALE, (y + 88) * SCALE), fill="#f6f7fb", outline=BLUE, width=3 * SCALE)
        c.text(x, y - 18, f"S{state}", 36)
        c.text(x, y + 31, '""' if state == 0 else '"' + "ABCD"[:state] + '"', 27)
    c.line([(105, 275), (258, 275)], arrow=True)
    c.save("prep-043-abcd-mealy.png")


if __name__ == "__main__":
    rising_diagram()
    sequence_diagram()
