"""Render the switch subsets in the verified seven-attempt strategy."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
scale = 2
im = Image.new("RGB", (1640 * scale, 460 * scale), "white")
d = ImageDraw.Draw(im)
fonts = Path("C:/Windows/Fonts")


def text(x, y, message, size=22, color="#17263d", bold=False):
    f = ImageFont.truetype(str(fonts / ("arialbd.ttf" if bold else "arial.ttf")), size * scale)
    d.text((x * scale, y * scale), message, font=f, fill=color, anchor="mm")


def line(points, fill="#65758b", width=3):
    d.line([(x * scale, y * scale) for x, y in points], fill=fill, width=width * scale)


text(820, 38, "ROTATING TABLE: 7-ATTEMPT GUARANTEED STRATEGY", 29, bold=True)
masks = [5, 3, 5, 1, 5, 3, 5]
names = {5: "Opposite pair", 3: "Adjacent pair", 1: "Single switch"}
for i, mask in enumerate(masks):
    x, y = 145 + i * 225, 218
    text(x, 112, f"ATTEMPT {i + 1}", 21, bold=True)
    line([(x-66, y-66), (x+66, y-66), (x+66, y+66), (x-66, y+66), (x-66, y-66)])
    for bit, (dx, dy) in enumerate([(-44, -44), (44, -44), (44, 44), (-44, 44)]):
        fill = "#2463cf" if mask & (1 << bit) else "#edf1f7"
        d.ellipse(((x+dx-15)*scale, (y+dy-15)*scale, (x+dx+15)*scale, (y+dy+15)*scale), fill=fill, outline="#65758b", width=2*scale)
    d.ellipse(((x-13)*scale, (y-13)*scale, (x+13)*scale, (y+13)*scale), fill="#fff5cc", outline="#9f853a", width=2*scale)
    text(x, 320, names[mask], 21, bold=True)
    if i < 6:
        line([(x+82,y), (x+135,y)])
        d.polygon([(u*scale,v*scale) for u,v in [(x+143,y),(x+131,y-6),(x+131,y+6)]], fill="#65758b")
text(820, 382, "Press the blue switches together. Stop immediately when the lamp lights.", 24, bold=True)
text(820, 424, "Each picture refers to the table as you see it now; no switch identity is tracked across rotations.", 22, color="#65758b")
output = root / "diagrams" / "prep-008-strategy.png"
output.parent.mkdir(parents=True, exist_ok=True)
im.save(output)
print(output)
