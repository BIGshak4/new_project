"""Rebuild the supplied hill/dip sketch as paired readable learning diagrams."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, MUTED = "#35234f", "#73558d", "#6e607c"


def diagram(language, solution=False):
    im = Image.new("RGB", (1600, 1260 if solution else 1180), "#fffdf8")
    draw = ImageDraw.Draw(im)

    def text(point, value, size=43, he=False, color=INK, bold=False):
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
        draw.text(point, value[::-1] if he else value, font=font, fill=color, anchor="mm")

    def localized(point, he, en, size=43, color=INK, bold=False):
        text(point, he if language == "he" else en, size, language == "he", color, bold)

    def arrow(a, b, color=PURPLE, both=False):
        draw.line((a, b), fill=color, width=5)
        angle = math.atan2(b[1] - a[1], b[0] - a[0])
        for tip, direction in ((b, angle), (a, angle + math.pi)) if both else ((b, angle),):
            draw.polygon([tip] + [(tip[0] - 17 * math.cos(direction + t), tip[1] - 17 * math.sin(direction + t)) for t in (-.45, .45)], fill=color)

    localized((800, 62), "גבעה ובור במסלולים סימטריים", "Mirrored hill and dip tracks", 54, bold=True)
    localized((800, 127), "גוף נקודתי מונחה ללא חיכוך", "Ideal guided point mass; no friction", 37, MUTED)
    for index, dip in enumerate((False, True)):
        baseline = 440 + index * 510
        start_y = baseline - 220
        points = [(365 - 220 * math.cos(t * math.pi / 2 / 120), start_y + 220 * math.sin(t * math.pi / 2 / 120)) for t in range(121)]
        points += [(760, baseline)]
        # The idealized semicircle has the same arc length in either track.
        points += [(860 - 100 * math.cos(t * math.pi / 120), baseline + (1 if dip else -1) * 100 * math.sin(t * math.pi / 120)) for t in range(121)]
        points += [(1430, baseline)]
        draw.line(points, fill=INK, width=7, joint="curve")
        draw.ellipse((127, start_y - 18, 163, start_y + 18), fill=PURPLE, outline=INK, width=3)
        for x in range(365, 1431, 24):
            draw.line((x, baseline, x + 10, baseline), fill="#c9bfd1", width=2)
        arrow((95, start_y), (95, baseline), both=True)
        text((47, (start_y + baseline) / 2), "R1", 37)
        endpoint_y = baseline + (100 if dip else -100)
        arrow((860, baseline), (860, endpoint_y), both=True)
        text((860, baseline + (-65 if dip else 65)), "R2", 39)
        localized((1130, baseline - 210), "מסלול עם בור" if dip else "מסלול עם גבעה", "Dip track" if dip else "Hill track", 43, bold=True)
        localized((1430, baseline + 55), "סוף", "End", 34)
        text((520, baseline + 55), "y = 0", 36, color=MUTED)
    if solution:
        text((800, 1125), "v_dip(s) > v_hill(s)   for   h(s) > 0", 44, color=PURPLE, bold=True)
        localized((800, 1195), "אותו אורך מקומי, פחות זמן בכל זוג קטעים", "Same paired arc length, less time in the dip", 40)
    else:
        text((800, 1125), "H = R1 > R2 > 0", 42, color=PURPLE)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"prep-082-{'comparison' if solution else 'tracks'}-{language}.png"
    im.save(path)
    print(path.name)


if __name__ == "__main__":
    for lang in ("he", "en"):
        diagram(lang)
        diagram(lang, solution=True)
