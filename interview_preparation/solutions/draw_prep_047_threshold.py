"""Draw a clean pin-explicit four-A threshold schematic; no raster editing."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
INK = "#22364d"
BLUE = "#476b9c"
GREEN = "#227e6d"


def main():
    image = Image.new("RGB", (2200 * SCALE, 1080 * SCALE), "white")
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size=28, color=INK):
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * SCALE)
        draw.text((x*SCALE, y*SCALE), value, fill=color, font=font, anchor="mm")

    def line(points, arrow=True, color=BLUE):
        draw.line([(x*SCALE, y*SCALE) for x, y in points], fill=color, width=4*SCALE, joint="curve")
        if arrow:
            x, y = points[-1]
            px, py = points[-2]
            angle = math.atan2(y-py, x-px)
            vertices = [(x, y)] + [(x-18*math.cos(angle+d), y-18*math.sin(angle+d)) for d in (-0.42, 0.42)]
            draw.polygon([(x*SCALE, y*SCALE) for x, y in vertices], fill=color)

    def gate(x, y, name):
        draw.rounded_rectangle((x*SCALE, y*SCALE, (x+280)*SCALE, (y+300)*SCALE), radius=18*SCALE, fill="#f3f6fc", outline=BLUE, width=4*SCALE)
        text(x+140, y+112, name, 43)
        text(x+140, y+168, "A", 29)
        text(x+140, y+214, ">= 2 / 4", 26)

    def input_wire(x, y, label):
        text(x-80, y, label, 33)
        line([(x-45, y), (x, y)])

    text(1100, 64, "y = [a+b+c+d >= 3]", 46)
    text(1100, 120, "A(u,v,w,z) = [u+v+w+z >= 2]", 30)
    for x, y, name in ((360,170,"G1"),(360,650,"G2"),(1020,160,"G3"),(1580,435,"G4")):
        gate(x, y, name)
    for y, label in zip((225,285,345,405),("c","d","0","0")):
        input_wire(360,y,label)
    for y, label in zip((705,765,825,885),("c","d","1","0")):
        input_wire(360,y,label)
    input_wire(1020,215,"a")
    input_wire(1020,275,"b")
    input_wire(1020,395,"0")
    line([(640,320),(820,320),(820,335),(1020,335)])
    text(790,278,"p = c & d",29)
    line([(1300,310),(1430,310),(1430,490),(1580,490)])
    text(1380,263,"r",34)
    line([(640,800),(1400,800),(1400,550),(1580,550)])
    text(1000,758,"q = c | d",30)
    input_wire(1580,610,"0")
    input_wire(1580,670,"0")
    line([(1860,585),(2100,585)],color=GREEN)
    text(1990,530,"y",40,GREEN)
    text(1990,638,">= 3 / 4",30,GREEN)
    text(1100,1010,"#A = 4",36)
    path = ROOT / "diagrams/prep-047-four-threshold-boxes.png"
    image.save(path)
    print(path)


if __name__ == "__main__":
    main()
