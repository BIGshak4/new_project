"""Draw the exact digit graph; language-neutral labels work in either UI language."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCALE = 2
IMAGE = Image.new("RGB", (1500 * SCALE, 700 * SCALE), "white")
DRAW = ImageDraw.Draw(IMAGE)
BLUE, GREEN, INK = "#515d9a", "#287b68", "#27304c"
POSITIONS = {3: (130, 285), 4: (415, 285), 6: (700, 285), 9: (985, 285),
             2: (1270, 285), 8: (700, 500), 5: (930, 500), 1: (1160, 500), 7: (1390, 500)}


def text(point, value, size, color=INK):
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size * SCALE)
    DRAW.text(tuple(v * SCALE for v in point), value, font=font, fill=color, anchor="mm")


def arrow(points, color):
    DRAW.line([(x * SCALE, y * SCALE) for x, y in points], fill=color, width=4 * SCALE)
    x, y = points[-1]
    px, py = points[-3]
    angle = math.atan2(y - py, x - px)
    head = [(x, y)] + [(x - 19 * math.cos(angle + delta), y - 19 * math.sin(angle + delta))
                       for delta in (-0.45, 0.45)]
    DRAW.polygon([(a * SCALE, b * SCALE) for a, b in head], fill=color)


def straight(a, b, pair, color):
    ax, ay = POSITIONS[a]
    bx, by = POSITIONS[b]
    angle = math.atan2(by - ay, bx - ax)
    start = (ax + 53 * math.cos(angle), ay + 53 * math.sin(angle))
    end = (bx - 56 * math.cos(angle), by - 56 * math.sin(angle))
    arrow([(start[0] + (end[0] - start[0]) * t / 20,
            start[1] + (end[1] - start[1]) * t / 20) for t in range(21)], color)
    label = ((ax + bx) / 2, (ay + by) / 2 - 30) if ay == by else (ax - 42, (ay + by) / 2)
    text(label, str(pair), 25, color)


def main():
    text((750, 50), "10a + b = 17k  /  23k", 34)
    for a, b, pair in ((3, 4, 34), (4, 6, 46), (6, 9, 69), (9, 2, 92)):
        straight(a, b, pair, BLUE)
    # Curved return from 2 to 3, outside the forward edges.
    points = []
    for i in range(121):
        t = i / 120
        points.append(((1 - t) ** 3 * 1270 + 3 * (1 - t) ** 2 * t * 1270
                       + 3 * (1 - t) * t * t * 130 + t ** 3 * 130,
                       (1 - t) ** 3 * 231 + 3 * (1 - t) ** 2 * t * 110
                       + 3 * (1 - t) * t * t * 110 + t ** 3 * 227))
    arrow(points, BLUE)
    text((700, 115), "23", 25, BLUE)
    for a, b, pair in ((6, 8, 68), (8, 5, 85), (5, 1, 51), (1, 7, 17)):
        straight(a, b, pair, GREEN)
    for digit, (x, y) in POSITIONS.items():
        color = BLUE if digit in (3, 4, 6, 9, 2) else GREEN
        bounds = ((x - 51) * SCALE, (y - 51) * SCALE, (x + 51) * SCALE, (y + 51) * SCALE)
        DRAW.ellipse(bounds, fill="#f5f4fa" if color == BLUE else "#f0f8f5", outline=color, width=3 * SCALE)
        text((x, y), str(digit), 40, color)
    text((750, 625), "17, 23, 34, 46, 51, 68, 69, 85, 92", 28)
    target = ROOT / "diagrams/prep-038-adjacent-digit-graph.png"
    IMAGE.save(target)
    print(target)


if __name__ == "__main__":
    main()
