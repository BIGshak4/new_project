"""Render the verified PREP-007 transition table as a circular-state diagram."""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
W, H = 1200, 1100
im = Image.new("RGB", (W * SCALE, H * SCALE), "#ffffff")
draw = ImageDraw.Draw(im)
CW, CCW, GRAY, INK = "#2463cf", "#c76b15", "#8190a5", "#17263d"
font_dir = Path("C:/Windows/Fonts")


def font(size, bold=False):
    return ImageFont.truetype(str(font_dir / ("arialbd.ttf" if bold else "arial.ttf")), round(size * SCALE))


def text(x, y, value, size=26, fill=INK, bold=False):
    draw.text((x * SCALE, y * SCALE), value, font=font(size, bold), fill=fill, anchor="mm")


def arrow(points, color, width=4):
    scaled = [(round(x * SCALE), round(y * SCALE)) for x, y in points]
    draw.line(scaled, fill=color, width=width * SCALE, joint="curve")
    x, y = points[-1]
    px, py = points[-2]
    angle = math.atan2(y - py, x - px)
    length, half_width = 15, 7
    polygon = [(x, y),
               (x - length * math.cos(angle) + half_width * math.sin(angle),
                y - length * math.sin(angle) - half_width * math.cos(angle)),
               (x - length * math.cos(angle) - half_width * math.sin(angle),
                y - length * math.sin(angle) + half_width * math.cos(angle))]
    draw.polygon([(round(a * SCALE), round(b * SCALE)) for a, b in polygon], fill=color)


def curve(p0, p1, p2, p3, color):
    points = []
    for i in range(101):
        t = i / 100
        u = 1 - t
        points.append(tuple(u**3 * p0[k] + 3*u*u*t*p1[k] + 3*u*t*t*p2[k] + t**3*p3[k] for k in (0, 1)))
    arrow(points, color, 3)


text(600, 35, "ROTATION DIRECTION — STATE MACHINE", 30, bold=True)
text(600, 78, "Arrow label: new AB / output     |     State: previous AB", 23, GRAY)

# CW: 00 -> 01 -> 11 -> 10 -> 00. CCW uses the reverse edges.
arrow([(395, 220), (805, 220)], CW)
text(600, 194, "01 / CW", 27, CW, True)
arrow([(805, 280), (395, 280)], CCW)
text(600, 310, "00 / CCW", 27, CCW, True)

arrow([(910, 325), (910, 675)], CW)
text(1020, 480, "11 / CW", 27, CW, True)
arrow([(850, 675), (850, 325)], CCW)
text(746, 520, "01 / CCW", 27, CCW, True)

arrow([(805, 780), (395, 780)], CW)
text(600, 815, "10 / CW", 27, CW, True)
arrow([(395, 720), (805, 720)], CCW)
text(600, 687, "11 / CCW", 27, CCW, True)

arrow([(290, 675), (290, 325)], CW)
text(170, 480, "00 / CW", 27, CW, True)
arrow([(350, 325), (350, 675)], CCW)
text(457, 520, "10 / CCW", 27, CCW, True)

# Self-loops: identical reading yields no new direction event.
for x, bits in ((320, "00"), (880, "01")):
    curve((x - 50, 187), (x - 165, 100), (x + 165, 100), (x + 50, 187), GRAY)
    text(x, 145, f"{bits} / -", 23, GRAY)
for x, bits in ((320, "10"), (880, "11")):
    curve((x + 50, 813), (x + 165, 905), (x - 165, 905), (x - 50, 813), GRAY)
    text(x, 862, f"{bits} / -", 23, GRAY)

for x, y, state in ((320, 250, "00"), (880, 250, "01"), (880, 750, "11"), (320, 750, "10")):
    draw.ellipse(((x-80)*SCALE, (y-80)*SCALE, (x+80)*SCALE, (y+80)*SCALE), fill="#f1f5fb", outline=INK, width=3*SCALE)
    text(x, y-13, "S" + state, 34, bold=True)
    text(x, y+28, "AB = " + state, 22, GRAY)

text(600, 970, "CW = clockwise     |     CCW = counterclockwise     |     - = no new event", 23)
text(600, 1010, "Two-bit jumps (00 <-> 11, 01 <-> 10): INVALID; omitted for clarity.", 22, GRAY)
text(600, 1046, "Initialize from the first AB reading. Direction convention follows the supplied sensor drawing.", 21, GRAY)

output = ROOT / "diagrams" / "prep-007-fsm.png"
output.parent.mkdir(parents=True, exist_ok=True)
im.save(output)
print(output)
