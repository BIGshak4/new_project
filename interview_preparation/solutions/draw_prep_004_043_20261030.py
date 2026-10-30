"""Authored bilingual timing and encoded-symbol FSM illustrations."""
from pathlib import Path

from draw_prep_016_064 import box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, GREEN = "#fffdf8", "#302344", "#71558c", "#33786d"


def wave(draw, values, y, color, start=400, step=180):
    points = []
    for i, value in enumerate(values):
        level = y - value * 80
        points.extend([(start + i * step, level), (start + (i + 1) * step, level)])
    draw.line(points, fill=color, width=6)


def timing(lang):
    image = Image.new("RGB", (2200, 1270), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 80), "השהיה מפורשת ומחזור עבודה", "Explicit latency and duty cycle", lang, 54, bold=True)
    text(draw, (1100, 165), "z[k] = x[k] XOR x[k-1]     y[k] = z[k-1]", 43)
    values = [0, 0, 1, 1, 0, 0, 1, 1]
    z = [0, 0, 1, 0, 1, 0, 1, 0]
    delayed = [0] + z[:-1]
    for i in range(9):
        x = 400 + i * 180
        draw.line((x, 260, x, 900), fill="#ded7e3", width=2)
        if i < 8:
            text(draw, (x + 90, 280), str(i), 34)
    for name, samples, y, color in [("x[k]", values, 480, INK), ("z[k]", z, 670, PURPLE), ("y[k]", delayed, 860, GREEN)]:
        text(draw, (220, y - 40), name, 44, bold=True, color=color)
        wave(draw, samples, y, color)
    phrase(draw, (1100, 1010), "הדוגמה המחזורית מתייצבת לאחר מילוי הצינור", "Periodic illustration settles after pipeline fill", lang, 39)
    text(draw, (1100, 1100), "P = 4 sampled cycles       steady duty = 2 / P = 50%", 42, color=GREEN, bold=True)
    phrase(draw, (1100, 1190), "השהיה נוספת מזיזה מופע ואינה מסנכרנת אות אסינכרוני", "Extra latency shifts phase; it does not provide CDC synchronization", lang, 35)
    return image


def symbols(lang):
    image = Image.new("RGB", (2300, 1600), BG)
    d = ImageDraw.Draw(image)
    phrase(d, (1150, 80), "דוגמת תבנית עם חפיפה", "Example target with overlap", lang, 54, bold=True)
    text(d, (1150, 165), "T = (1, 2, 1, 2)       symbol: 3 bits       Moore Y = (q == 4)", 41)
    # Four main progress edges and rounded prefix nodes.
    xs = [260, 700, 1140, 1580, 2020]
    for i in range(4):
        wire(d, [(xs[i] + 93, 415), (xs[i + 1] - 93, 415)], PURPLE, 6)
        text(d, ((xs[i] + xs[i + 1]) // 2, 355), str([1, 2, 1, 2][i]), 42, bold=True)
    for i, x in enumerate(xs):
        d.ellipse((x - 92, 323, x + 92, 507), fill="#ecf5ef" if i == 4 else "white", outline=GREEN if i == 4 else PURPLE, width=6)
        text(d, (x, 393), f"Q{i}", 46, bold=True)
        text(d, (x, 455), f"Y={int(i == 4)}", 29)
    # One particularly important fallback curve; all transitions are in the table.
    arc = [(2020, 510), (2020, 620), (1580, 620), (1580, 510)]
    d.line(arc, fill=GREEN, width=6, joint="curve")
    wire(d, [(1580, 590), (1580, 510)], GREEN, 6)
    text(d, (1800, 670), "1", 40, bold=True, color=GREEN)
    phrase(d, (1150, 760), "טבלת מעברים מלאה לדוגמה", "Complete transition table for this example", lang, 40, bold=True)
    cols = [350, 750, 1150, 1550, 1950]
    headers = ["state", "input 1", "input 2", "other", "Y"]
    rows = [["Q0", "Q1", "Q0", "Q0", "0"], ["Q1", "Q1", "Q2", "Q0", "0"], ["Q2", "Q3", "Q0", "Q0", "0"], ["Q3", "Q1", "Q4", "Q0", "0"], ["Q4", "Q3", "Q0", "Q0", "1"]]
    box(d, (120, 820, 2180, 1390), PURPLE)
    for c, value in zip(cols, headers, strict=True):
        text(d, (c, 880), value, 37, bold=True)
    for r, row in enumerate(rows):
        for c, value in zip(cols, row, strict=True):
            text(d, (c, 980 + r * 83), value, 39, color=GREEN if r == 4 else INK)
    phrase(d, (1150, 1470), "החץ התחתון משמר התחלה של הזיהוי הבא", "The lower edge retains a prefix for the next detection", lang, 37)
    return image


if __name__ == "__main__":
    for lang in ("he", "en"):
        timing(lang).save(OUT / f"prep-004-delayed-edge-duty-{lang}.png")
        symbols(lang).save(OUT / f"prep-043-three-bit-symbols-{lang}.png")
